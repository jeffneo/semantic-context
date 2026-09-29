# Entitlements, phase 3: the JDBC pass-through

Status: phase 3 of [the entitlements plan](2026-09-27-entitlements.md) (option C); built and checked
2026-09-28. See "As built" at the end.

## Why

Phases 1 and 2 made the SQL route exact: it runs as the principal. The Cypher route still reads as
Virtual Graph's single identity (`qlsc-bq`). Option A copes by refusing Cypher wherever that could show
more than the principal may read: any table with a row policy. That has two costs:
- **Over-restriction.** Nine of 60 questions in the oracle run had Cypher refused over `dim_customer`,
  the table under Customer, the graph's hub. Marketing reads every row of it and was refused anyway.
  The graph-shaped questions are where Cypher beats SQL (8 to 5), and most go through Customer.
- **Only the gateway is safe.** A Neo4j user who reaches the virtual graph directly (Browser, an agent's
  own driver) reads everything as `qlsc-bq`. Virtual Graph applies no graph privileges (finding 2), so
  database ACCESS is all or nothing.

The pass-through makes the virtual graph read as the principal. BigQuery then enforces tables, columns,
rows and masking on the Cypher route exactly as on SQL, and an unsigned query is refused.

## What the recon found (2026-09-28)

- **How Virtual Graph connects.** Its BigQuery provider builds `jdbc:bigquery://…;ProjectId=…;…` (plus
  `additionalProperties`) and hands it to a Hikari pool. The pool connects through `DriverManager`.
  Virtual Graph requires an installed driver named `com.google.cloud.bigquery.jdbc.BigQueryDriver`.
  The driver jar is mounted into Neo4j's `lib/`.
- **Parameters reach the SQL.** A Cypher `WHERE $qlsc_principal IS NOT NULL` reaches every statement
  Virtual Graph sends, as `(? /*qlsc_principal*/ IS NOT NULL)`: one-hop, multi-hop, two-step and
  truncating plans alike.
- **Impersonation per connection.** The Google driver impersonates a service account per connection
  (`ServiceAccountImpersonationEmail`), from the application-default credentials it already uses
  (`qlsc-bq`, which may impersonate the test principals). So the pass-through needs no token broker of
  its own.

## The design

**A driver that stands in for the real one**, in `vg-passthrough/` (Java 21, no dependencies but the
JDK):
- **Placement.** Its jar holds `com.google.cloud.bigquery.jdbc.BigQueryDriver`, and is mounted in
  `lib/` in place of the real jar. Virtual Graph finds the driver it requires and connects through it.
- **The real driver** is mounted outside `lib/` and loaded in a child-first class loader for its own
  package. That keeps the two driver classes of one name apart.
- **What it does per statement.** When a statement carrying `? /*qlsc_principal*/` executes, it:
  1. **verifies** the bound value: an HMAC-SHA256 token naming the principal, with an expiry, signed
     with a key only the gateway and the driver hold (`<work>/virtual/passthrough.key`, mounted
     read-only, never committed);
  2. **removes** the predicate and its parameter, so the token never reaches BigQuery;
  3. **runs** the statement on a connection for that principal: the same URL plus
     `ServiceAccountImpersonationEmail=<principal>`, one small pool per principal. A token for the data
     source itself (the estate's own reads) uses the base connection.
- **Refusals:**
  - an unsigned, forged or expired statement is refused with an SQLException that says why;
  - metadata calls (`DatabaseMetaData`) go to the base connection, since Virtual Graph checks its
    schema that way at startup. They return names, not rows.
- **The switch:** `QLSC_PASSTHROUGH=enforce | off`. `off` passes everything to the real driver, as
  today.

**Deployment.** Not a separate service. The driver has to run inside Virtual Graph's JVM, because that's
where Virtual Graph opens JDBC connections. So `docker-compose.yml` changes only the `neo4j-vg` service:
- the pass-through jar mounted in `lib/`;
- the real jar mounted at `/var/lib/neo4j/qlsc/`;
- the key file mounted read-only.

The jar is built locally (`vg-passthrough/build.sh`), and the built jar is gitignored.
Packaging it into a derived image comes later, if the prototype holds.

**The gateway** (`qlsc/entitle.py`, `navigate`):
- **Signing.** Every Cypher query `ask` sends through the virtual graph carries `$qlsc_principal`: a
  token for `--as <principal>`, or for the data source when no one is named. The predicate is added to
  the query's first `WHERE`, or as a `WHERE` of its first `MATCH`.
- **Option A's refusals lifted.** With `virtualize.passthrough: true` (the estate's setting), the
  row-policy refusal no longer applies, since the warehouse filters Virtual Graph's reads as the
  principal. The model restriction (schema) and the probe dry runs stay.

## How it's checked

- **Unit tests** (a self-test the build runs):
  - the token (sign, verify, expired, forged, another key);
  - the rewrite (predicate removed, parameters renumbered, question marks in string literals left
    alone).
- **The oracle** (`eval/entitlements.py`, with the pass-through on):
  - **Rows:** every Cypher answer is checked against BigQuery's own job log. Every job Virtual Graph
    ran for it ran as the principal: `INFORMATION_SCHEMA.JOBS`, by the label Virtual Graph puts on its
    jobs. And risk's customers-by-state answer holds only KS and NE.
  - **Schema:** as before.
- **Probes and negative controls:**
  - a Cypher query with no token, one with a forged token, and one with an expired token are each
    refused by the driver;
  - a broken gateway that signs every query as the data source is caught by the job-log check.
- **Regressions:** the graph-shaped questions and the gold questions on Cypher, without `--as`, score
  as before. The pass-through must be invisible to the estate's own reads.

## Not in this phase

- OIDC or workforce identity: impersonated service accounts still stand in for people.
- A result cache keyed by principal: Virtual Graph has none that we've seen; if it does, it must key by
  principal.
- The composite database (`fennmoor`): its remote alias to the virtual graph carries the same
  parameter, but this phase checks the virtual graph directly.

## As built (2026-09-28)

**The driver** (`vg-passthrough/`, about 450 lines of Java):
- **Built with the JDK alone.** `build.sh` runs `javac`, then the self-test, then `jar`. No Maven, so
  nothing is downloaded. The self-test (`test/qlsc/passthrough/SelfTest.java`) covers:
  - the token: signs and verifies; refuses expired, forged, another key's and malformed tokens;
  - the rewrite: the predicate becomes `TRUE`, later parameters shift down, and a `?` inside quotes or
    backticks is left alone;
  - the key check's pattern.
- **Where it sits.** `BigQueryDriver` (the name Virtual Graph asks for) registers for `jdbc:bigquery:`
  and hands every connection to `Passthrough`.
  - `Passthrough` loads the real driver from `/var/lib/neo4j/qlsc/`, child-first for its package.
  - It wraps each connection. A prepared statement is held until it executes, because the token is a
    parameter bound after `prepareStatement`. Then the token is verified, the predicate becomes `TRUE`,
    and the statement is prepared on the principal's connection. The other bound values are replayed,
    shifted past the token.
  - The token is never sent on.
- **One connection per principal per pooled connection,** not a pool per principal. Hikari lends a
  connection to one thread at a time, so its principal connections need no locking; they close with it.
- **Two unsigned reads are allowed**, and nothing else:
  - **Virtual Graph's startup check that a node key is unique** (`SELECT 1 FROM … GROUP BY … HAVING
    COUNT(*) > 1 LIMIT 1`), matched whole. It returns at most a constant 1. The first deployment
    refused it, and Virtual Graph wouldn't start.
  - **Metadata:** `DatabaseMetaData`, and a prepared statement's column types. These go to the base
    connection and return names, not rows.
- **Deployment:** as planned, `docker-compose.yml` mounts two jars on `neo4j-vg`. The pass-through goes in
  `lib/` (`VG_JDBC_JAR` puts the real one back) and the real driver goes outside it. `QLSC_PASSTHROUGH`
  switches it (enforce by default).
  - The key is `<work>/virtual/passthrough.key`, inside the `/nvg_home` mount the container already
    has. The mount isn't read-only: the Neo4j entrypoint chowns what it's given.
  - `build.sh` rewrites the jar in place, because Docker Desktop's bind mount loses a replaced file.
    After a rebuild: `docker compose --profile vg up -d --force-recreate neo4j-vg`.

**The gateway:**
- `entitle.signing()` signs every Cypher query `ask` sends when the estate has `virtualize.passthrough:
  true`: for `--as <principal>`, or for the data source.
- `entitle.check_cypher` drops the row-policy refusal then. The model restriction and the dry runs as the
  principal stay: they keep the LLM from writing about what the principal can't read, and fail fast.
- `eval/agreement.py` and `eval/diagnose_cypher.py`, which run saved Cypher directly, sign it as the data
  source too.

**Checked** (`eval/entitlements.py`, results/entitlements.md; three principals × 20 questions, both
routes):

| | option A (phases 1–2) | the pass-through |
|---|---|---|
| schema leaks | 0 | 0 |
| row incidents | 0 | 0 |
| Cypher answered | 3 | 12 |
| Cypher refused (row policy) | 9 | 0 |
| routed to Cypher | 1 | 4 |

- **Every Cypher answer ran as its principal.** The check is BigQuery's own job log, read as the owner:
  every job labelled `app=neo4j-virtual-graph` since the question began ran as the principal. It leaves
  out Virtual Graph's `SELECT 1` liveness checks and its key checks, which read no rows.
- **Reached directly, the driver refuses** a query with no token, a forged token (marketing's name,
  risk's signature) and an expired token.
- **Rows, by hand,** for customers by state through the virtual graph:

  | reading as | customers |
  |---|---|
  | the data source | 24,300 |
  | risk | 4,016, only KS and NE |
  | marketing | 24,300 |
  | contact-center | BigQuery refuses it |
- **The negative controls:** five broken gateways, six tries, all caught. The new one: a gateway that
  signs every query as the data source, not the principal. The job-log check caught it on risk.
- **Regressions** (no `--as`: the estate's own reads, signed as the data source):
  - the graph-shaped questions: Cypher 8 of 10 and SQL 5 of 10, as in the last committed run; only
    column aliases differ;
  - the gold questions: SQL 6 of 10 and Cypher 3 of 10, as before. Q05 stays wrong, differently; Q08
    differs by an alias.

  The pass-through is invisible to the estate's own reads.

**Limits:**
- **The key is a file on the host,** readable by anyone who can read the work directory. A deployment
  would keep it in a secret store, shared by the gateway and the container, and rotate it.
- **Impersonated service accounts stand in for people,** as in phases 1 and 2.
- **The composite database** (`fennmoor`) isn't checked. Its remote alias should carry the parameter
  through, but nothing here shows it does.
- **A Neo4j user who reaches the virtual graph directly** can still see its schema: labels and property
  names, from the model. Every row read needs a token signed by the gateway.

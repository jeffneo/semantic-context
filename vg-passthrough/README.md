# vg-passthrough: Virtual Graph reads BigQuery as the person asking

A small JDBC driver (about 450 lines of Java 21, no dependencies but the JDK) that stands in for the BigQuery driver Virtual Graph loads. Without it, everything Virtual Graph reads
is read as one identity, the data source's service account, whoever asked. With it, each statement runs as the principal it is for, so **BigQuery's own tables, columns, row policies
and masking decide what the graph returns**, and a statement that does not say who it is for is refused. The reasons and the checks are in
[plans/2026-09-28-jdbc-passthrough.md](../plans/2026-09-28-jdbc-passthrough.md) (the oracle's results are in
[results/entitlements.md](../examples/fennmoor-bank/results/entitlements.md)); this page is how it is put together and how it is run locally and hosted.

## Why a driver

Virtual Graph is a Neo4j feature: it turns Cypher into SQL and sends it over JDBC. It has no notion of who is asking, and applies no graph privileges to what it reads. The one place
that sees every statement it sends, inside its own process, is the JDBC driver. So the identity is changed there.

- Virtual Graph connects through `DriverManager`, and requires an installed driver named `com.google.cloud.bigquery.jdbc.BigQueryDriver`. This jar contains a class of that name
  ([BigQueryDriver.java](src/com/google/cloud/bigquery/jdbc/BigQueryDriver.java)) and takes its place in Neo4j's `lib/`.
- The real Google driver is mounted outside `lib/` and loaded by [Passthrough.java](src/qlsc/passthrough/Passthrough.java) in a class loader that looks in its own jar first for its own
  package, which keeps the two classes of one name apart.
- The Google driver already impersonates a service account per connection (`ServiceAccountImpersonationEmail`), from the application-default credentials it uses. So no token
  broker is needed: the driver opens a connection with that property set to the principal.

## What happens to a statement

1. **The gateway signs the question.** `qlsc ask` (and the demo server) add `WHERE $qlsc_principal IS NOT NULL` to the Cypher and send a token as that parameter
   (`entitle.py`: `signed()`, `token()`). The token is `base64url("principal\nexpires") . base64url(HMAC-SHA256)`, made with a key only the gateway and this driver hold.
   The empty principal is the data source's own identity, for the estate's own reads.
2. **Virtual Graph carries the parameter into every SQL statement it sends**, as `(? /*qlsc_principal*/ IS NOT NULL)`: the one-hop, multi-hop and truncating plans alike.
3. **The driver holds the prepared statement until it executes** (the token is bound after the statement is prepared) and then:
   - verifies the token ([Token.java](src/qlsc/passthrough/Token.java)): refused if forged (another key), expired or malformed;
   - removes the predicate and its parameter ([Rewrite.java](src/qlsc/passthrough/Rewrite.java): `? IS NOT NULL` becomes `TRUE`, later parameters shift down), so **the token never
     reaches BigQuery**;
   - runs the statement on a connection for that principal: the same URL plus `ServiceAccountImpersonationEmail=<principal>`. One connection per principal per pooled
     connection (the pool lends a connection to one thread at a time, so there is no locking).
4. **BigQuery answers as that person.** Its row policies, column tags and masking apply, and a table the principal may not read is an error from BigQuery, not from us.

What is refused, and what is allowed without a token:

| | |
|---|---|
| a statement with no token, a forged one, an expired one | refused by the driver, with a message that says which |
| a plain (unprepared) statement | refused |
| Virtual Graph's startup check that a node key is unique (`SELECT 1 … GROUP BY … HAVING COUNT(*) > 1 LIMIT 1`) | allowed, matched whole: it returns at most a constant 1 |
| metadata (`DatabaseMetaData`, a statement's column types) | allowed, on the base connection: names, not rows |

Each run writes a line to the container's log, `qlsc-passthrough: ran a statement as <principal>` (or `the data source`), and each refusal one saying why.

## Building it

```bash
vg-passthrough/build.sh     # javac, the self-test, jar: target/qlsc-vg-passthrough.jar
```

The build needs only a JDK. It runs the self-test first (`test/qlsc/passthrough/SelfTest.java`: tokens signed, verified, expired, forged, another key's and malformed; the rewrite,
including a `?` inside quotes; the key check's pattern), and rewrites the jar in place, because Docker Desktop's bind mount loses a replaced file. `scripts/stack up` builds it if it
is not there. After a rebuild: `docker compose --profile vg up -d --force-recreate neo4j-vg`. The jar is gitignored.

## Locally

`docker-compose.yml`'s `neo4j-vg` service mounts two jars:

| Mounted at | What |
|---|---|
| `/var/lib/neo4j/lib/google-cloud-bigquery-jdbc-1.0.0-all.jar` | **this jar** (`VG_JDBC_JAR=…` puts the real driver here instead: everything then reads as the data source, and `qlsc` refuses to read for a principal) |
| `/var/lib/neo4j/qlsc/google-cloud-bigquery-jdbc-1.0.0-all.jar` | the real driver ([docker/nvg/README.md](../docker/nvg/README.md) says where to get it), loaded by this one |

- **The data source's identity** is a credentials file made with `gcloud auth application-default login --impersonate-service-account=<the data-source account>`, in a gcloud directory of
  its own, mounted at `/nvg_home/credentials.json` (`VG_CREDENTIALS`). The datasource sets `OAuthType: 3` (application-default credentials) in
  `virtualize.driver_properties` in the estate's file. That account may impersonate the test principals.
- **The signing key** is `<work>/virtual/passthrough.key`, made by the gateway on first use (`entitle.key()`) and read by the driver at `/nvg_home/passthrough.key` (the work directory's
  `virtual/` is mounted at `/nvg_home`). It is not mounted read-only: the Neo4j entrypoint changes ownership of what it is given.
- The estate turns the gateway's side on with `virtualize.passthrough: true`.

## Hosted

The same jars and the same key, put in place by [deploy/gcp/vm/boot.sh](../deploy/gcp/vm/boot.sh) on the `db-vg` machine, with **no credentials file anywhere**:

- **The jars** are published to the bucket (`scripts/cloud publish`: this jar and the real driver, under `vg/lib/`) and fetched when the machine boots, then mounted exactly as above.
  A running machine fetches only at boot, so a rebuilt jar is deployed by `scripts/cloud down` then `up`.
- **The identity is the machine's.** `db-vg` runs as the data source's service account, and `OAuthType: 3` makes the Google driver find that account through the metadata server. Impersonating
  a principal is the same property as locally, and the same service account needs permission to impersonate the test principals. `credentials.json` exists as an empty file only because
  the datasource's settings name it.
- **The signing key is a secret.** `scripts/cloud secrets` writes the local `passthrough.key` to Secret Manager (`qlsc-demo-passthrough-key`). The Virtual Graph machine reads it at boot to
  `/nvg_home/passthrough.key`; the Cloud Run service (the gateway side, `server.py`) mounts the same secret at `/secrets/passthrough/passthrough.key`, which the image links to where
  `entitle.key()` looks. So the two sides agree without the key being in the image, in Terraform's state or in git. Rotate it by writing a new version and restarting both.
- **The composite database** (`fennmoor`) on that machine has three aliases: the semantic layer and memory, each on its own machine, and `rows`, which points back at the machine's own
  Virtual Graph. A composite query that reads rows (`USE fennmoor.rows MATCH …`) goes through `rows`, a remote hop to Virtual Graph, and the signed parameter has to survive it. It does
  (checked below). The other aliases never reach Virtual Graph, and the page's one composite example reads only the model's schema, so the page cannot show this: the check goes through
  `scripts/cloud tunnel`, which opens bolt to the machines from a workstation while it runs.

## Checking it

Same question, different people, different answers: run "customers in each state" on the page as `admin`, `risk` and `contact-center`. If the driver were not impersonating, all three
would match. The result should be every state, only the states the risk team's row policy allows, and a refusal that does not say whether the data exists.

The proof that does not depend on the answers is BigQuery's own job log. Virtual Graph's jobs carry the label `app=neo4j-virtual-graph` (set in the datasource's `Labels`), and each ran as
the user that impersonated it:

```sql
SELECT creation_time, user_email, LEFT(query, 80) AS query
FROM `<project>`.`region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND (SELECT value FROM UNNEST(labels) WHERE key = 'app') = 'neo4j-virtual-graph'
ORDER BY creation_time DESC
```

`user_email` should be the principal's service account for a question asked as that principal, and the data source's for the estate's own reads. `eval/entitlements.py` does this
check for every answer. The container's log (`docker logs qlsc-neo4j-vg`, or `docker logs neo4j-vg` on the machine) has the `qlsc-passthrough:` lines.

### Checked hosted (2026-10-09)

On the deployed demo, "Customers in each state" (the `rows` target, signed) was run through the service as three principals, and once unsigned. Then the job log above was read for the next
minutes, as the estate's own identity with Resource Viewer on the project, which is enough for `INFORMATION_SCHEMA.JOBS_BY_PROJECT`.

| Asked as | The page got | BigQuery job (from the job log) |
|---|---|---|
| admin | 8 states, 24,300 customers | one job, `user_email` = `qlsc-bq@<project>.iam.gserviceaccount.com` (the data source) |
| risk | 2 states (KS, NE), 4,016 customers | one job, `user_email` = `qlsc-risk@<project>.iam.gserviceaccount.com` |
| contact-center | refused: "the data it needs either does not exist or is not available to you" | no job: BigQuery refused it before one ran |
| admin, signature switched off | refused by the driver: "the query carries no principal token" | no job: the statement never left the driver |

Those were the only jobs Virtual Graph sent in the window apart from its liveness and key checks, which the query leaves out because they read no rows. The numbers are the local
oracle's (24,300; 4,016 in KS and NE; refused for the contact center), so the hosted deployment reads as each principal exactly as the local one does. The page cannot exercise the composite's `rows` alias (its one composite example reads no rows), so that was checked directly, below.

### Checked through the composite (hosted and local, 2026-10-09)

The same question through the composite's `rows` alias: `USE fennmoor.rows MATCH (c:Customer) WHERE $qlsc_principal IS NOT NULL RETURN c.state_code, count(DISTINCT c.customer_key)`, with the
token as the query's `qlsc_principal` parameter. On the hosted `db-vg` (through `scripts/cloud tunnel`, with the signing key of this checkout, which is the one in Secret Manager) and, with
the same results, on the local Virtual Graph instance:

| Token for | Result | BigQuery job's `user_email` |
|---|---|---|
| the data source (admin) | 8 states, 24,300 customers | `qlsc-bq@<project>…` |
| risk | 2 states (KS, NE), 4,016 customers | `qlsc-risk@<project>…` |
| contact-center | refused: BigQuery's error, through the remote hop | no job |
| none | refused: "qlsc pass-through: refused, no principal token" | no job |

So the parameter crosses the remote alias and the driver acts on it: the job log shows two jobs in the window, one per answered question, as the right users.

## Limits

- **Impersonated service accounts stand in for people.** Nothing here is OIDC or workforce identity.
- **A Neo4j user who reaches the virtual graph directly** (Browser, an agent's own driver) can still see its schema: labels and property names, from the model. Every row read needs a token
  signed by the gateway; nothing is returned without one.
- **The key is a shared secret.** Whoever holds it can sign for any principal the data source may impersonate. Locally it is a file on the host; hosted, a secret readable by the two
  service accounts that need it. Hosted, the gateway and the machine run as the same service account, so the boundary is the key and the permission to impersonate, not the account.
- **Written against one driver.** It matches the real driver's class name, its `ServiceAccountImpersonationEmail` property and the shape of Virtual Graph's SQL
  (`? /*qlsc_principal*/`), at `google-cloud-bigquery-jdbc-1.0.0` and a Virtual Graph that is in public preview. A new version of either is a thing to re-check with the self-test and
  `eval/entitlements.py`.
- **BigQuery only.**

# Entitlements: the warehouse's access rules, carried through the semantic layer and the virtual graph

Status: phases 1 and 2 built and checked (2026-09-28); phase 3, the JDBC pass-through, built and checked
the same day ([its plan](2026-09-28-jdbc-passthrough.md)). See "As built" at the end.

## Why

A bank entitles data by line of business, table, column (identifiers, contact details) and row (region,
book, client coverage). `qlsc ask` must answer each person only from what the warehouse lets that person
read. That covers three things:
- **Rows.** An answer holds only rows the person could read in the warehouse. A count is a count of
  *their* rows (the abac kit's point: filter before you aggregate, or every count is the firm's).
- **Schema.** The trace names only tables and columns the person may see. The same goes for joins,
  example queries (their SQL holds literals), filter values (real data values), the principals who ran
  queries, and group names and summaries. A summary written from a hidden table is itself a leak.
- **Copies.** Rows kept in Neo4j (the [memory plan](2026-09-27-agentic-memory.md)) have left the
  warehouse's enforcement, so they must carry it with them.

Without this, no firm with granular entitlements can use either route, the virtual graph least of all.

## What the spikes found (2026-09-27)

1. **Virtual Graph reads as one warehouse identity.** Every Neo4j user's query reaches BigQuery as the
   data source's principal. The documentation says so: the connection's principal is distinct from the
   Neo4j user. So BigQuery's own rules (IAM, column policy tags, row access policies) see one reader
   for everyone.
2. **Virtual Graph ignores Neo4j's graph privileges.** `DENY MATCH` on a label, `DENY READ` on a
   property, `DENY TRAVERSE` on a relationship type, ungranted labels and property-based rules are all
   accepted and none is applied. `db.labels()` shows everything. Only database-level `ACCESS` holds.
   The same privileges on a standard database hold. Written up for the Virtual Graph team in
   `~/Desktop/bugs/neo4j-issue-vg-rbac-ignored/`.
3. **The composite reads as whoever the aliases store.** Our remote aliases carry `USER neo4j PASSWORD
   ...`, so any session on `fennmoor` reads both constituents as the administrator. Neo4j can forward
   the caller's own OIDC token instead (`OIDC CREDENTIAL FORWARDING` on the alias,
   `dbms.security.allow_oidc_credential_forwarding_enabled`), when both instances use OIDC single
   sign-on. Untested here, and untested with a virtual graph.
4. **The BigQuery JDBC driver can carry a per-connection identity:**
   - a pre-issued access token (`OAuthType=2`, `OAuthAccessToken`);
   - service-account impersonation (`ServiceAccountImpersonationEmail`, `...Chain`, `...TokenLifetime`);
   - workforce and workload identity federation (`BYOID_*`);
   - audit tags (`RequestReason`, `Labels`).

   Virtual Graph sets these once, in `datasource.json`, for everyone.
5. **Virtual Graph passes Cypher parameters into its SQL by name.** `WHERE $tok IS NOT NULL` becomes
   `WHERE (? /*tok*/ IS NOT NULL)`, with the value bound through JDBC. So a value the gateway adds to a
   query reaches the JDBC layer, labelled. This makes a JDBC pass-through possible without changing
   Virtual Graph (option C below).

## Can a Neo4j SSO user be guaranteed to be the same warehouse user?

**Not by Neo4j or Virtual Graph today.** Finding 1 rules it out on the virtual graph route. It can be
guaranteed by construction, in one component that holds the person's identity-provider assertion and
derives both identities from the same claim:
- **The Neo4j identity:** the username claim of Neo4j's OIDC single sign-on, or impersonation by a
  gateway service account.
- **The warehouse identity:**
  - **Workforce identity federation:** the same identity provider (Okta, Entra) is a Google Cloud
    workforce pool provider, and Google's STS exchanges the person's token for a Google token acting as
    `principal://.../subject/<sub>`. BigQuery grants roles to that principal.
  - **Google identities** (Cloud Identity, Workspace): the person's own OAuth token is both.

Both mappings read the same claim. They are asserted equal before the query runs, and recorded
together (the abac kit's "bind the two identities").

The coarser, easier variant maps a Neo4j role to a Google service account the gateway impersonates.
The identity is then a role, not a person. BigQuery's audit log still records the delegation chain.

## The design: an entitlement gateway, with the warehouse as the rulebook

**The gateway is the one component every question passes through that knows who is asking.** It
runs `ask`'s steps on the person's behalf:
- it verifies the sign-on;
- it builds the person's allowlist;
- it filters what navigation shows;
- it runs SQL as the person;
- it checks or forwards the Cypher.

At first it's `qlsc ask --as <principal>`, a layer in the tool. Later it's a service (an MCP server)
that an agent talks to, holding no credentials of its own to hand out.

The JDBC pass-through (option C below) is a different component: a driver wrapper inside the virtual
graph's JVM. It is how the gateway's knowledge of the person reaches BigQuery on the Cypher route. The
gateway signs a token naming the person, and the wrapper verifies it and runs the query as that person.

The gateway reuses the abac kit's shape:
- one door;
- the agent holds no credentials;
- the allowlist is enumerated on a privileged connection, and the query executes as the person;
- responses carry records and nothing else;
- an independent oracle checks everything.

One thing differs. **We don't re-implement the warehouse's rules; we ask the warehouse, as the person.**
BigQuery is both the source of the entitlements and the oracle that tests them. Warehouse calls live in
the connector (`src/qlsc/warehouse/`), like every other.

1. **Identity.** The gateway verifies the sign-on token (RS256 against the issuer's keys, as in the kit)
   and gets a warehouse credential for the same person.
2. **The allowlist, per person and session**, from BigQuery as that person:
   - **Tables:** `tables.testIamPermissions` for `bigquery.tables.getData`, over the layer's tables.
     This takes inherited dataset and project roles into account.
   - **Columns:** the policy tags on each column (read on a privileged connection) and whether the
     person may read each tag.
   - **Rows:** which tables carry row access policies (privileged). The gateway needs to know where they
     are, not to evaluate them: the warehouse does that, when it runs as the person.

   The allowlist is cached for the session, with a lifetime no longer than a policy refresh.
3. **Schema, in the semantic layer.** `trace` filters everything it returns through the allowlist:
   - hits, groups, cohort and joins;
   - examples, only those whose every table and column is readable;
   - filter values, only from readable columns, and never from policy-tagged ones;
   - who ran a query, as a kind (production, a person), not a name.

   A group whose tables are only partly readable shows its readable tables, without its summary.
   Direct access to the layer's database (Studio, MCP) bypasses the gateway. There, native Neo4j
   privileges on the layer's own labels are the floor. The layer is a standard database, so they hold.
4. **Rows, on the SQL route:** the SQL runs as the person, so BigQuery enforces tables, columns, rows and
   masking itself. This is exact.
5. **Rows, on the Cypher route:** four options.

| | How | Exact for | Works today |
|---|---|---|---|
| **A. Check, then run** | The gateway checks the query's labels and properties against the allowlist (the `unknown_properties` check already parses them against the model). It then dry-runs Virtual Graph's `EXPLAIN` SQL as the person, and BigQuery refuses an unreadable table or column. | tables, columns | yes |
| **B. Virtual Graph compiles, the gateway runs** | It takes the `External` SQL from `EXPLAIN`, binds the parameters, and runs it as the person. Refused for plans that aren't a single `External` under a projection. | everything | yes, for simple plans |
| **C. JDBC pass-through** (your suggestion) | A driver wrapper in Virtual Graph's JVM replaces the BigQuery jar mount. The gateway adds a signed principal token as a parameter (`WHERE $qlsc_principal IS NOT NULL`), which reaches the wrapper as `? /*qlsc_principal*/` (finding 5). The wrapper verifies the signature, removes the predicate so the token never reaches BigQuery, and runs the statement on a connection for that principal, from a token broker. An unsigned statement is refused, except Virtual Graph's startup schema checks. | everything, any plan | yes, built by us |
| **D. Product asks** | Per-user data source credentials in Virtual Graph (an OIDC token exchanged at STS, or a role mapped to a service account), and enforcement of graph privileges on virtual graphs. | everything | no |

Under A, the virtual graph route is allowed only where no table in the query has a row access policy or
masking. Elsewhere the router sends the question to SQL. That is a deterministic routing signal for the
[router](2026-09-26-router.md).

C is the "exchange entitlements in a JDBC pass-through" idea, and it works without Virtual Graph
changes. It costs Java (JDK 21 and Maven are on this machine), a token broker, one connection pool per
principal, and care that any result cache is keyed by principal. It is also the most concrete way to
show the Virtual Graph team what D should do.

### What the semantic layer adds

The layer is what makes mirroring possible. It holds the mapping from the graph's schema to the
warehouse's objects: each label's table (`Table.graph_label`) and each property's column
(`Column.graph_key`). So the allowlist for labels and properties is computed from the warehouse's
grants, not written by hand.

The log also records who reads what: `(:Principal)-[:RAN]->(:QueryShape)-[:REFERENCES]->(:Table)`. Set
against the grants, that's an access review:
- who holds access they never use;
- whose queries touch identifiers.

This isn't enforcement, but it's a natural thing for a bank to ask of this graph.

## Other ideas considered

- **One virtual graph per entitlement group**, each impersonating a group service account. It works
  today, but it's coarse, and instances multiply with groups (Virtual Graph serves one model per
  instance).
- **Per-role authorized views** (the Snowflake "post-filtered table" pattern in the abac kit's
  `SNOWFLAKE-PARITY.md`): a view dataset per role, and a virtual graph over each. It's exact and
  familiar to review boards, but it's one artifact per role, and as stale as its last refresh.
- **Neo4j attribute-based rules on the layer's database** (the abac assessment's CIP-269
  `abac.native.user_tags()`): tag each Table and Column with its dataset, and each person with the
  datasets they may read. That's the floor for direct access to the layer. It doesn't help the virtual
  graph (finding 2).

## How it is checked: the warehouse as the oracle

Three test principals stand in for people, as service accounts the gateway impersonates:

| principal | may read |
|---|---|
| `qlsc-marketing` | marketing and core customer data, no identifier columns |
| `qlsc-risk` | fraud, lending and core data, with identifiers; customers in two states only (a row access policy on `dw_core.dim_customer`) |
| `qlsc-contact-center` | contact-center data only |

For every gold question, every route, and a set of probes, per principal:
1. **Rows:** each answer is a subset of what the principal's own SQL, run as the principal, returns.
   Counts equal the principal's count, not the firm's.
2. **Schema:** no response names a table, column, filter value or principal outside the allowlist.
   Canary names and values are planted in hidden tables and scanned for in every response.
3. **Negative controls**, as in the abac kit's Phase 8. Deliberately broken gateways (the dry-run check
   skipped, the filter values unfiltered, the token unsigned) must each be caught, by name.
4. **Later:** an adversarial agent (the abac kit's harness) trying to extract hidden schema through
   `ask`.

A leak (an extra row or name) is counted separately from over-restriction (a missing row): a missing row
is a complaint, an extra row is an incident.

## Phases

1. **Identity, allowlist, schema hiding, SQL as the person** (Python: the connector and `navigate`).
   `qlsc ask --as <principal>`. Oracle checks 1 to 3.
2. **The Cypher route under option A**, with the router's entitlement signal.
3. **Option C, the JDBC pass-through**, and the oracle over the virtual graph route with the row policy
   in force.
4. **Later:**
   - single sign-on end to end with a local identity provider;
   - OIDC credential forwarding for the composite;
   - native privileges on the layer's database;
   - the access review.

Unchanged: the build, the layer's model, and every result the build produces. Entitlements filter what
`ask` shows and runs; they don't change what the layer infers.

## Cost

- **BigQuery:** small. Permission checks and dry runs are free; the oracle's queries are counts.
- **GCP changes** (all removable, but removing needs your approval):
  - three service accounts;
  - dataset-level grants;
  - one policy tag taxonomy on the identifier columns;
  - one row access policy.

  A row access policy hides every row from anyone it doesn't name, so it's paired with an all-rows
  policy for the existing principals (you, the estate's service account, and the virtual graph's). A
  policy tag works the same way, with fine-grained read granted to the same three. Nothing else in the
  estate sees a difference.

## Decisions (2026-09-27)

1. **The GCP changes: yes,** as listed under Cost.
2. **Order:** the gateway first (phases 1 and 2), then the JDBC pass-through (phase 3). The pass-through
   is built regardless of how option A does.
3. **Identity for the prototype:** impersonated service accounts standing in for people. A local
   identity provider comes later.
4. **Groups a person can only partly read:** their readable tables are shown, without the summary.

## As built: phases 1 and 2 (2026-09-28)

**In BigQuery** (`examples/fennmoor-bank/entitlements/setup.py`, approved and applied as the owner):
- **APIs and identities:** the IAM, IAM Credentials and Data Catalog APIs enabled; the three service
  accounts; `qlsc-bq` (the connector's and Virtual Graph's identity) may impersonate each.
- **Grants:** each account gets `bigquery.jobUser`, read on its datasets and on `fnb_graph`'s views.
- **Policy tag:** `identifier`, on ten columns of `dim_customer`, `dim_account` and `customer_360`.
  Fine-grained read is granted to you, `qlsc-bq` and risk.
- **Row policies on `dim_customer`:** KS and NE for risk, all rows for you, `qlsc-bq` and marketing.

The script shows what's in place and changes only what isn't. It must be rerun after a fill recreates one
of those tables.

**In the tool:**
- **The connector** (`warehouse/`): `acting_as`, `readable`, `column_tags`, `readable_tags` and
  `row_policies`. A view is readable only if a dry run as the principal passes, because a view reads
  with its reader's own grants.
- **The gateway** (`src/qlsc/entitle.py`): the allowlist, cached per principal;
  `navigate.trace(allow=...)` filters by it; SQL runs as the principal. On the Cypher route, option A:
  refused where a table has a row policy, or where a probe dry run of what Virtual Graph's SQL reads, as
  the principal, fails. `qlsc ask --as <name>`; the router takes SQL when Cypher is refused.
- **Stricter than the plan:** a partly readable group, or Semantic area, is shown without its name as
  well as its summary.

**What building it found:**
- **BigQuery skips column-level checks for a query it can prove returns nothing** (`LIMIT 0`,
  `WHERE FALSE`). Nothing is returned, but a check built on such a dry run checks nothing. The oracle's
  first allowlist used `LIMIT 0` and found no hidden columns. Probes use `LIMIT 1`.
- **Filling Virtual Graph's parameters with NULL doesn't work:** BigQuery rejects a literal NULL in a
  comparison, which would have refused every parameterized Cypher query. The gateway dry-runs one probe
  per table instead, of the columns Virtual Graph's SQL reads there.
- **A metadata query leaked a hidden name.** An example over `INFORMATION_SCHEMA.PARTITIONS` reads no
  layer table, so "every table it reads is readable" held trivially. Its literal named
  `fct_daily_account_balances`, which reached contact-center's prompts. The oracle caught it. An
  example is now shown only if it reads at least one table and its text names nothing hidden.
- **The warehouse shows column names to anyone with metadata access;** policy tags protect values.
  Marketing's own `INFORMATION_SCHEMA.COLUMNS` query lists `tax_id_hash`. That's BigQuery's answer to
  them, not the gateway's, and the oracle scores it so.

**The oracle** (`eval/entitlements.py`, results/entitlements.md): the three principals × the 14 gold
questions and six probes, by both routes and the router.
- **Its own allowlist,** by dry runs as each principal, agrees with the gateway's for all three:
  marketing 19 tables with 10 columns hidden, risk 30, contact-center 21.
- **Schema:** 0 leaks in 60 questions, by either route or in any prompt sent to the LLM. The canaries
  are the names of unreadable tables and hidden columns, the values the log filters them on, and the
  log's principals: 800 to 900 per principal.
- **Rows:** 0 incidents. Every SQL answer is the principal's own read of its query. Risk's five answers
  over `dim_customer` differ from the firm's, as the row policy intends (4,016 of 24,300 customers).
- **Cypher:**
  - it answered 3 times, each through labels with no row policy, checked by the oracle's own allowlist;
  - it was refused 9 times, all for `dim_customer`'s row policy, and the router took SQL each time.

  Marketing's refusals are over-restriction: marketing reads every row, but option A refuses any
  row-policied table. Phase 3 (the pass-through) is what lifts that.
- **The negative controls:** four broken gateways, five tries, every one caught by the check meant for
  it:

  | broken gateway | principal | caught by |
  |---|---|---|
  | navigation unfiltered (the trace shows everything; queries still run as the principal) | marketing, contact-center | schema |
  | hidden columns and their filter values shown | marketing | schema |
  | SQL run as the estate, not the principal | risk | rows |
  | the Cypher gate off (option A skipped) | risk | rows |

- **Over-restriction** is counted apart: no question went unanswered on the SQL route. Some answers are
  empty stand-ins where the principal's tables hold nothing relevant (P4 for marketing: "the average
  handle time by site" with no contact-center data). The writer returns a typed empty query rather than
  declining.

**Next:**
- **Phase 3, the JDBC pass-through:** done. Virtual Graph reads as the principal, and the row-policy
  refusals are gone: Cypher answered 12 times, not 3, with 0 leaks and 0 incidents
  ([as built](2026-09-28-jdbc-passthrough.md#as-built-2026-09-28)).
- **The writer on an empty cohort** should decline rather than return a stand-in query.
- **The oracle** takes about 50 minutes (60 questions, both routes); `--rescore` redoes its schema
  checks from the saved texts.

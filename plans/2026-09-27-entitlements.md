# Entitlements: the warehouse's access rules, carried through the semantic layer and the virtual graph

Status: agreed (2026-09-27), after the accuracy work. The spikes below have run; nothing in `src/`
has changed.

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

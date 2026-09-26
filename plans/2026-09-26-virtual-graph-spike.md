# Virtual Graph spike: a model written from usage, over BigQuery

Status: done (2026-09-26). All tests run, the composite test included, after adding bolt TLS to both Neo4j
instances. Two Virtual Graph bugs are written up for the Virtual Graph team, outside this repo
(`~/Desktop/bugs/neo4j-issue-vg-local-alias/`, `~/Desktop/bugs/neo4j-issue-vg-composite-correlated-subquery/`).

## What was built

- **`qlsc virtualize`** (`src/qlsc/virtualize.py`) writes a Virtual Graph model from the semantic layer:
  - **nodes:** where a Variable's trusted joins converge, or production's MERGE key. When usage cannot
    tell the two sides of a single join apart, the side unique in the data is the key.
  - **relationships:** a column holding the same Variable as another node's key.
  - **names:** from the LLM, with one retry for relationship types that collide.
  - **views:** one per node table, in `fnb_graph`.
  - **report:** the evidence for every node and relationship in `MODEL.md`.
- **`neo4j-vg`** in docker-compose (profile `vg`): Neo4j 2026.09.0 with Virtual Graph, on bolt 7692.

On slice 1 of the data fill (13 tables in scope):
- **11 labels:** Customer, Account, Product, Branch, Merchant, CardTransaction, DepositTransaction,
  Call, Agent, Queue, ContactCenterSite.
- **14 relationship types**, every one a trusted join from the log.
- **Left out:** the suspect join `dim_account.core_account_id = fct_card_transactions.card_account_id`,
  recorded with production's reason. Also `dim_card` (nothing joins it) and `fct_account_closures`
  (no key of its own).

## Findings

1. **Authentication without a key file works.** The documented `configfile` secret accepts only a
   service-account key; an impersonated application-default credentials file is rejected. But
   `additionalProperties: {OAuthType: 3}` reaches the Google JDBC driver unchanged and makes it use
   application-default credentials (`GOOGLE_APPLICATION_CREDENTIALS`), impersonation included. This
   matters for organizations that block service-account keys.
2. **Queries work, in about a second.** Aggregations over two relationships, a customer's neighbourhood,
   and a four-hop pattern (Product, Account, Customer, Call, ContactCenterSite) all ran in 0.8-1.5 s.
   Results matched direct SQL.
3. **Two things in the generated SQL** (`EXPLAIN`):
   - **A redundant self-join.** When a relationship is backed by the node's own table (a foreign-key
     column, the common warehouse case), Virtual Graph joins that table to itself on its key. That is
     harmless on dimensions, but doubles the scan on large facts.
   - **A dropped node in the pattern.** In `(c:Customer)<-[:OWNED_BY]-(a:Account)`, with nothing
     returned from `c`, the join to the customer table is dropped. So rows whose key matches no
     customer still count.
4. **Schema procedures** (for the MCP server):

   | Procedure | Result |
   |---|---|
   | `db.labels()`, `db.relationshipTypes()`, `db.schema.visualization()`, `db.schema.nodeTypeProperties()` | Instant, served from the model; no BigQuery query |
   | `apoc.meta.schema()` (what the MCP server's get-schema calls) | Works, in 36 s: it samples through BigQuery |
   | `apoc.meta.stats()` | Works, in 37 s |
   | `db.stats.retrieve('GRAPH COUNTS')` | Fails: "not supported on virtual graph databases" |

   The MCP server's schema setting worth adding is `db.schema.*`, which is instant and virtual-safe.
   `db.stats` is not.
5. **Composite databases work, through remote aliases only.** `fennmoor` on `neo4j-vg` has two
   constituents:
   - `fennmoor.semantic`: a remote alias to the semantic layer (`neo4j+ssc://neo4j:7687`, database
     `bigquery`);
   - `fennmoor.rows`: a remote alias to the virtual graph on its own instance
     (`neo4j+ssc://localhost:7687`).

   A local alias to the virtual graph is stored but hidden from `SHOW ALIASES`, and never resolves as a
   constituent (bug 1). Remote aliases accept only `neo4j+s`/`neo4j+ssc`, so both instances serve bolt
   TLS, optional (self-signed, `docker/tls/`), and `neo4j-vg` has a keystore for the stored credentials.
   Uncorrelated queries across the two work, in about 1.7 s: tables from the semantic layer beside call
   counts by site from BigQuery.
6. **No `OPTIONAL MATCH`.** A customer's context is several small queries, as planned. A customer with no
   calls simply returns no call rows.
7. **The semantic layer can't drive the virtual graph in one query.** A correlated `CALL (x) { USE
   fennmoor.rows ... }` is rejected. The composite forwards `x` as `WITH $@@x AS x`, and Virtual Graph
   requires a query to start with `MATCH` (bug 2). Dynamic labels and types (`$(...)`) are also
   unsupported. That leaves two routes:
   - an uncorrelated subquery filtered in the outer query, which scans the whole label;
   - two round trips, with the values passed as parameters on the second. This is what `ask --cypher`
     should do anyway.

## Next

- Report the two bugs (`~/Desktop/bugs/`).
- The self-join: try relationship views separate from node views, and compare bytes scanned.
- `ask --cypher` and the router, each with its own plan.

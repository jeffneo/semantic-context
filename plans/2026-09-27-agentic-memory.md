# Agentic memory: a context compiler from the virtual graph into a persistent graph

Status: agreed (2026-09-27), after the accuracy work. The spike below has run; nothing in `src/` has
changed.

## Why

The virtual graph reads warehouse rows on demand and keeps nothing. An agent serving a customer asks
about the same customer again and again: their accounts, cards, recent calls, the campaigns they saw.
Keeping that context in a persistent Neo4j database, after the first fetch, gives:
- **fast, free repeat reads:** 70 ms instead of one to two seconds, and no bytes billed;
- **memory, not only cache:** the agent can add what it learns (a note, a decision, an outcome),
  attached to the facts it's about, and find it again next session;
- **a durable graph that grows with use.** The virtual graph is the on-ramp, and the persistent graph
  is where the context accumulates. That's where the Neo4j revenue is.

It's also a different thing from a Redis context retriever. Redis caches a flattened context per
object. Here the context stays a graph: connected across entities, joined to the semantic layer's
definitions, with provenance on every fact and entitlements carried with it.

## What the spike showed (2026-09-27)

One composite statement read a customer's accounts from the virtual graph and merged them into a
standard database:

```cypher
CALL () { USE memspike.vg
  MATCH (a:Account)-[:OWNED_BY]->(c:Customer) WHERE c.cif_number = $cif
  RETURN c.customer_key AS ck, c.cif_number AS cif, c.segment AS seg, a.account_key AS ak, a.product_code AS pc }
CALL (ck, cif, seg, ak, pc) { USE memspike.mem
  MERGE (m:Customer {customer_key: ck}) SET m.cif_number = cif, m.segment = seg, m.fetched_at = datetime()
  MERGE (x:Account {account_key: ak}) SET x.product_code = pc
  MERGE (x)-[:OWNED_BY]->(m)
  RETURN 1 AS w }
RETURN count(w) AS written
```

| | time |
|---|---|
| the virtual graph alone | 1.0 s |
| fetch and remember, one statement | 1.7 s |
| read back from memory | 0.07 s |

A second run wrote no duplicates.

So the write itself needs no new service: reading the virtual graph and writing a standard constituent
works in one transaction. Only the reverse is blocked (a correlated subquery *into* the virtual graph,
bug 2), and a parameter works around it.

## What the context compiler adds to that statement

The compiler writes such statements for a whole entity, from what the semantic layer knows. Nothing is
written by hand per estate.

1. **What to fetch: a context template per label, from the virtual graph's model.**
   - For `Customer`, the template is its neighbourhood:
     - one hop: accounts, preferred branch, calls, card and deposit transactions;
     - one more hop for their dimensions: product, branch, merchant, queue, agent, site.
   - Facts are windowed (the last N days, capped), so a context stays small. The time column is each
     fact's partition column, which also keeps the warehouse's bill low.
   - The properties are the columns the log's queries actually read, not every column.
   - The virtual graph has no `OPTIONAL MATCH`, so each relationship type is its own uncorrelated read,
     keyed by a parameter.
2. **Same labels, same keys, a source on each.** Memory uses the virtual graph's labels, relationship
   types and node keys (`Column.graph_key`). So repeated fetches merge, memory and the virtual graph agree
   on identity, and **the same Cypher runs on either**: `ask --cypher` can target memory or the virtual
   graph with one generated query.

   Each remembered node also carries its `source`, the virtual graph it came from. Its identity is
   (`source`, key), enforced by a node key constraint per label. This is what keeps collisions apart
   (see "Collisions" below).
3. **Provenance, as links into the semantic layer.** Each fact carries when it was fetched, until when
   it holds, who fetched it and the query that fetched it. It also *links* to where it came from:
   `(:Customer)-[:FROM]->(:Table)`, and to the Computations an answer used (the accuracy plan's
   Phase 2).

   A relationship can't cross databases. So memory holds small **stubs** of the layer's Table, Column
   and Computation nodes: the layer's stable id and a name, nothing else. The links are real
   relationships within memory, so a traversal can ask "which remembered facts come from tables the
   contact center writes". In the composite, a stub's id reaches the full node in the layer, with its
   area, definitions, joins and usage.

   Stubs point only at nodes whose ids survive a rebuild:
   - tables and columns (warehouse names);
   - Computations (ids from their normalized expression).

   Semantic groups are redrawn by each build, so memory reaches them through the table, in the layer.

   The alternative, memory inside the layer's own database, would give direct links. But a rebuild
   rewrites that database, and memory must outlive rebuilds.
4. **Freshness from usage.** How long a fact holds comes from how often production writes its table.
   The log records that (`Table.write_days`). Every table the virtual graph serves is written daily
   (90 or 91 of the log's 91 days), so a customer's context holds until the next load. A table written
   monthly would hold a month. A frozen table holds indefinitely, and is flagged as frozen. A read
   serves memory while fresh, and fetches again when stale (read-through).
5. **Entitlements travel with the rows.** A remembered row has left BigQuery's enforcement. Reads go
   through the [entitlement gateway](2026-09-27-entitlements.md): a fact is shown only if the reader
   may read its source table and columns now, checked at read time, not write time. A table with a row
   access policy is remembered per principal and shown only to the principal who fetched it, because
   whether two people's row filters agree can't be known from outside.
6. **What the agent adds: Neo4j's own agent-memory model.** A single `Note` is too thin. The agent side
   follows Neo4j Labs' `agent-memory`, so what we show is Neo4j's model, fed from the warehouse:
   - **short-term:** `(:Conversation)-[:HAS_MESSAGE]->(:Message)`, messages chained by
     `NEXT_MESSAGE`;
   - **reasoning:** `(:ReasoningTrace)` and `(:ToolCall)`, triggered by messages. An `ask` is a tool
     call. It records the question, the query it ran, the tables and Computations it used (through the
     stubs), and the facts it read or remembered;
   - **long-term:** the entities, preferences and facts the agent learns (`Entity`, typed as its model
     types them), with `(:Message)-[:MENTIONS]->` both to them and to the warehouse facts (a message about a
     customer mentions that `Customer`).

   The warehouse facts are long-term memory with typed labels (`Customer`, `Account`), not generic
   entities. Facts expire and are fetched again. What the agent learns persists, with validity intervals
   in the style of Graphiti: a superseded preference is closed, not deleted. An entity whose facts
   expired keeps its key, so the conversations about it stay attached.

### Collisions

Three kinds, each handled by construction:
- **A virtual graph label that is also an agent-memory label** (a web-analytics `Event`, an
  `Organization`). The agent-memory labels are reserved. `qlsc virtualize` checks its label names
  against them, as it already checks relationship types for uniqueness, and renames a colliding label
  (`WebEvent`).
- **The same label from two virtual graphs** (a core-banking `Customer` and a CRM `Customer`, keyed
  differently). Identity is (`source`, key), so the two never merge by accident. They're linked by
  `SAME_AS` only where the layers show an identity join between the two keys (a Variable spanning
  both). A label used by one source needs no filter in queries. For one used by several, the generated
  Cypher filters on `source`.
- **The same key value in two sources** (customer 1009 in both). Also kept apart by (`source`, key).
## Where it runs

- **The compiler** is Python in the tool, working from the layer and the virtual graph's model:
  - `qlsc remember <label> <key>` fetches and merges;
  - `qlsc recall <label> <key>` reads memory, fetching again if stale;
  - `qlsc converse` records a conversation's messages, the `ask` tool calls in it, and what the agent
    learned, in the agent-memory model.

  Later, the same as MCP tools for an agent.
- **The statements** run on the composite: one transaction per entity, reads from the virtual graph,
  writes to memory. The composite allows writes to one constituent per transaction, which is all this
  needs.
- **Memory** is a new standard database on the main instance, beside the semantic layer, joined to the
  composite as `fennmoor.memory`. The virtual graph instance stays stateless compute.
- **The router** ([plan](2026-09-26-router.md)) gets a third route with a deterministic signal: a
  question about entities whose context is fresh in memory reads memory. A question across all
  customers still goes to the virtual graph or SQL.

Unchanged: the build, the layer's model, and the virtual graph's model. Memory reads the model; it
doesn't change it.

## How it is checked

1. **Correctness:** for 20 customers and a set of context questions, the same Cypher on memory and on
   the virtual graph gives the same rows while the context is fresh.
2. **Economics:** a simulated agent session, about 50 questions over 5 customers, with and without
   memory. Measured: latency (median and 95th percentile) and bytes billed.
3. **Freshness:** with the clock moved past a context's lifetime, a read fetches again, and a stale
   fact is never served as fresh.
4. **Entitlements** (with the entitlement plan's test principals): memory never shows a reader more
   than BigQuery, queried as that reader, would.

## Cost

- **Each customer fetch reads about ten tables.** At BigQuery's 10 MiB minimum per table read, that's
  about 100 to 150 MiB, well under a tenth of a cent.
- **The simulated session** is a few GiB at most.
- **Storage** in Neo4j is negligible at this scale.

## Decisions (2026-09-27)

1. **A `memory` database on the main instance**, in the `fennmoor` composite.
2. **The virtual graph's labels and keys are reused, with a `source` on each.** The agent side follows
   Neo4j Labs' agent-memory model rather than a single `Note` label. Collisions are handled as above.
3. **Freshness** comes from how often production writes each table.
4. **A single-user prototype first.** Sharing across people waits for entitlements phase 1.

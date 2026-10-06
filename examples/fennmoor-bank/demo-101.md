# Demo 101: warehouse context for agents, in 20 minutes

A first-touch tour of the whole architecture on the Fennmoor Bank example (a synthetic bank on BigQuery): what it is,
how it is built, and how an agent uses it, in Neo4j Browser and the terminal. Last rehearsed 2026-10-01; the pieces marked
"live" call an LLM and the warehouse.

## The pitch (draft)

**Ten seconds.** Neo4j infers what your warehouse means from how people actually use it, and gives AI agents live, governed,
remembered context from it without copying a row.

**Thirty seconds.** Your warehouse holds the answers, but nothing in it tells an AI agent what the data means: which table is
current, which join is right, how your business defines "card spend". Teaching it that is a modelling project that is out of
date when it ships. We infer it from the record you already keep, your query log, and build a semantic layer in Neo4j. We
expose the live warehouse rows as a graph without copying them. And we give agents a memory of what they have looked up, with
where it came from, how long it holds, and who may see it, all enforced by the warehouse's own permissions. On our example
estate, an agent using it answered 90% of the business's own questions correctly, against 61 to 66% for the same model given
only the schema, using about a quarter of the tokens that pasting the schema into the prompt takes.

**How the value is delivered.**

| What we do | What the customer gets |
|---|---|
| **Infer the model from usage.** The query log says which columns are joined, which tables are read together, what the business computes. An LLM only names things. | No modelling project to start, and a model that follows the business when usage changes. A rebuild reproduces it exactly. |
| **Virtual Graph over the warehouse.** The inferred model becomes a graph; Cypher is translated to SQL at query time. | Graph questions (neighbourhoods, paths, shared neighbours) on the data where it lives: no pipeline, no copy, nothing to keep in sync. |
| **Memory for agents.** An entity's context is fetched once and kept, with provenance and freshness; answers, corrections and decisions are kept beside it. | Repeated work is free (a repeat costs no tokens and about a tenth of a second), and an agent can say where each fact came from and how fresh it is. |
| **The warehouse stays the rulebook.** Questions run as the asking principal, and every request is measured against token and time targets. | Access rules are not re-implemented or bypassed, and cost and latency are visible per request. |

*Say plainly:* the numbers are from one synthetic estate; the questions are written from its own query log, so about half are
re-asks; and against a schema cached in the prompt, the layer's advantage is accuracy and prompt size, not dollars (the
cached schema is cheaper per right answer at this size, and grows with the estate).

## Before you start (5 minutes)

- `docker compose up -d neo4j` and the Virtual Graph profile are running (`docker ps`: `qlsc-neo4j`, `qlsc-neo4j-vg`).
- `export QLSC_CONFIG=examples/fennmoor-bank/estate.yaml` in the terminal, from the repository root.
- A BigQuery login for the estate's configuration (it lapses): `CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc gcloud auth login`.
- Two Neo4j Browser tabs, signed in as `neo4j` with `NEO4J_PASSWORD` from `.env` (don't paste it anywhere shared):

  | tab | open | connect URL | databases |
  |---|---|---|---|
  | **A, the layer and memory** | http://localhost:7477/browser/ | `bolt://localhost:7690` | `bigquery` (semantic layer), `memory` |
  | **B, Virtual Graph and the composite** | http://localhost:7478/browser/ | `bolt://localhost:7692` | `fennmoor` (composite), `neo4j` (virtual graph) |

- Run every command once beforehand. The LLM steps take 10 to 20 seconds live; talk through them.
- Optional: the same queries in Neo4j Enterprise Studio (Query and Explore, http://localhost:8082) for a more visual tour.
  Studio needs you to sign in yourself.

## Run of show

| min | part | where |
|---|---|---|
| 0:00 | 1. The picture | slide or README |
| 1:00 | 2. The semantic layer | Browser, tab A |
| 5:00 | 3. Ask a question | terminal |
| 9:00 | 4. The virtual graph | terminal, Browser tab B |
| 14:00 | 5. Memory | terminal, Browser tab A |
| 17:00 | 6. Governed, and does it work? | terminal, a table |
| 19:00 | 7. Close | |

### 1. The picture (1 min)

**Show** the first diagram in the [README](../../README.md): three Neo4j shards (the semantic layer, the virtual graph that
maps to the warehouse's rows, and agent memory) joined by a composite database.

**Say.** Two of the three store data: the semantic layer and memory. The virtual graph stores nothing; it is a mapping from
Cypher to SQL over the warehouse. The composite stores nothing either; it lets one Cypher query reach all three.

### 2. The semantic layer (4 min, Browser tab A, `:use bigquery`)

**Show.**

```cypher
MATCH p = (v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(:Table) WHERE v.tables >= 5 RETURN p   // the keys the whole warehouse joins on
```
```cypher
MATCH p = (:Semantic {level: 2})-[:IN_SEMANTIC]->(:Semantic {level: 3}) RETURN p   // the map of the business
```
```cypher
MATCH (c:Computation {kind: 'measure', trusted: true}) RETURN c.name, c.expression, c.jobs ORDER BY c.jobs DESC LIMIT 5   // what the business computes
```

**Say.** None of this was modelled. A **Variable** is a real-world thing that columns share, found from the joins people
actually run (a join that production contradicts is kept as evidence and builds nothing). A **Semantic** is a business area,
found from what is read together. A **Computation** is a measure the business computes again and again, written exactly as
their queries write it. The whole layer comes from the query log and the catalog.

**Land.** The business's own usage is the source of truth, so the model can't drift from how the warehouse is used.

### 3. Ask a question (4 min, terminal)

**Show** (live, about 15 seconds):

```bash
uv run qlsc ask --run "Card spend by customer segment last quarter"
```

**Say**, walking down the output: the closest business areas; the cohort of tables; how the log joins them; the example queries
the business already runs; then the SQL, the dry run, the answer, and the `MEASURED` line at the end. The model picks from
what the layer offers (a typed request, naming the Computation for "card spend"), and code writes the joins and the filters,
so it never invents a join or multiplies rows. The "is purchase" filter in the SQL is not in the question: it is part of how
the business defines card spend.

**Land.** The LLM chooses, deterministic code compiles, and every request reports its tokens and seconds. Where the business has
asked a question before, the router answers with its own query and the new values (86 of 89 right, about 860 tokens).

### 4. The virtual graph (5 min, terminal and Browser tab B)

**Show** a graph question in Cypher (live, about 10 seconds):

```bash
uv run qlsc ask --cypher --run "Which agents handled calls from customer 0001000025, and how many of that customer's calls did each handle?"
```

Point at the SQL it prints: Virtual Graph translated the Cypher into BigQuery SQL, and ran it. Nothing was copied.

**Show the reveal** (tab B, `:use fennmoor`):

```cypher
USE fennmoor.rows CALL db.schema.visualization()   // the virtual graph's schema: 11 labels, 14 relationship types
```

then (tab A, `:use bigquery`):

```cypher
MATCH p = (s:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable)<-[:IS]-(k:Column {graph_key: true})<-[:HAS_COLUMN]-(e:Table)
WHERE c.graph_relationship IS NOT NULL AND s.graph_label IS NOT NULL AND e.graph_label IS NOT NULL AND e <> s
RETURN p   // the 14 paths the model was derived from
```

**Say.** Nobody drew that graph. `qlsc virtualize` wrote its model from the layer: a table is a node where the business's trusted
joins converge on a column; a column that holds another node's key is a relationship. Pick one: `HELD_BY` is
`dim_account.customer_key`, which shares the Customer Key Variable with `dim_customer.customer_key`, where 24 trusted joins
converge. Each relationship on the left has its evidence on the right.

**Show the composite** (live, about 3 seconds):

```bash
uv run examples/fennmoor-bank/demo.py composite
```

**Say.** One Cypher query reads what the layer knows (the business area, the Variable, the source column) beside live rows
counted in BigQuery, in about 2 seconds.

**Land.** A graph over the warehouse that is derived, not drawn, and queryable beside the layer that explains it.

### 5. Memory (3 min, terminal and Browser tab A)

**Show.** First nothing is there (tab A, `:use memory`):

```cypher
MATCH (c:Customer {cif_number: '0001000033'}) RETURN count(c) AS remembered   // 0
```

```bash
uv run qlsc recall Customer cif_number=0001000033   # first time: about 15 reads from BigQuery, 5 to 7 s
uv run qlsc recall Customer cif_number=0001000033   # again: from memory, about 0.05 s
```

then the same query again (1), and what came with it:

```cypher
MATCH (c:Customer {cif_number: '0001000033'})
RETURN c.source, c.fetched_by, c.fetched_at, c.holds_until   // who, when, until when it holds
```
```cypher
MATCH p = (c:Customer {cif_number: '0001000033'})<-[:HELD_BY]-(a:Account)-[:OFFERS]->(pr:Product) RETURN p LIMIT 25   // draw its neighbourhood
```

**Show an agent's exchange** (live, about 40 seconds):

```bash
uv run examples/fennmoor-bank/demo.py exchange
```

**Say.** A customer's neighbourhood is fetched once and kept, with when it was fetched, by whom, and until when it holds
(from how often the table is written). The second read is local. An agent's question is kept the same way: asked again it
costs no tokens; a rejected answer is never given again, and a correction is asked with everything said so far.

**Land.** Agents stop paying twice for the same context, and every fact carries where it came from.

### 6. Governed, and does it work? (2 min)

**Show.**

```bash
uv run qlsc ask --as contact-center "What is the churn risk of our high-balance customers?"
```

**Say.** The first call as a principal takes about 15 seconds (it asks the warehouse what they may read). This principal sees
none of the risk tables, so nothing is offered. Nothing is re-implemented: the warehouse decides, and queries run as that
principal; the virtual graph refuses any query without a signed token naming one.

**Show** the result of the comparison ([eval/comparison/README.md](eval/comparison/README.md)): 176 questions written from
the business's own queries, the same model throughout.

| method | right | tokens per request (median) | seconds (median) |
|---|---|---|---|
| the schema pasted into the prompt | 66% | 43,872 | 4.4 |
| a generic exploring agent | 61% | 50,304 | 22.4 |
| qlsc, one shot | 75% | 6,667 | 4.4 |
| **qlsc, used by an agent** | **90%** | 10,667 | 9.0 |

**Say** the caveats from the pitch: one synthetic estate, about half of the questions are re-asks, and a schema in the prompt
grows with the estate while qlsc's prompt does not.

### 7. Close (1 min)

**Say.** What you saw: a model inferred from usage, a graph over live rows that was derived rather than drawn, memory with
provenance and freshness, and warehouse-enforced access, each measured. Today it reads BigQuery; the warehouse is one
connector module (`src/qlsc/warehouse/`). Virtual Graph is in public preview.

**Next step to offer:** point it at a customer's own query log and catalog. On Fennmoor the whole LLM naming pass costs under
fifty cents with Haiku, and every call is cached, so a rebuild over unchanged evidence is free and reproduces the graph.

## If something goes wrong

- **"gcloud needs a fresh login"**: `CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc gcloud auth login`. The composite and `recall` use the
  Virtual Graph container's own credentials and may still work.
- **A Browser query on the virtual graph says "refused, the query carries no principal token"**: that is the gateway working.
  Use `qlsc ask --cypher` or `demo.py composite`, which sign their queries.
- **`demo.py exchange` says "from memory" on the first line**: that question was asked in the last day. Pass `1` or `2`.
- **No warehouse at all**: show Browser only (parts 2, and 4's two queries, and 5 on a customer already in memory) and the
  comparison table.

## Questions you will get

- **Is this Aura?** Virtual Graph runs on Aura; this rig is self-managed, and the per-principal pass-through and the
  composite here are our own build. The inferred model is the same artifact either way.
- **Other warehouses?** BigQuery today. The tool's warehouse code is one connector; the parser resolves BigQuery SQL only so far.
- **What does the LLM do?** It names Variables, areas and Computations; it fills the typed request for a question; it writes
  the fallback queries. It never writes the joins of a compiled answer.
- **How big a log?** The example has 315,729 jobs over 90 days; the log is aggregated inside the warehouse, so job rows
  never leave it.

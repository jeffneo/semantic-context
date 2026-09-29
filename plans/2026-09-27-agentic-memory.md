# Agentic memory: a context compiler from the virtual graph into a persistent graph

Status: agreed (2026-09-27), after the accuracy work; split into phases (2026-09-28, below). Phases 1 and
2 built and checked (2026-09-28), phase 3 (2026-09-29). On 2026-09-29 the agent side was rebuilt on the
Context Memory model ([its plan](2026-09-29-context-memory-model.md)), and distillation became phase 4.
See each phase's "as built" at the end.

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

## Phases (2026-09-28)

Each phase ends with its checks run and its results written up.

1. **The context compiler, for one reader** (decision 4), reading as the data source. This covers:
   - the `memory` database, and `fennmoor.memory` in the composite;
   - context templates from the virtual graph's model;
   - the same labels and keys, with a `source` on each, and node keys;
   - provenance as properties, plus Table and Column stubs;
   - freshness from `Table.write_days`, with read-through.

   The commands are `qlsc remember` and `qlsc recall`. Checked by:
   - check 1 (correctness), over 20 customers;
   - check 3 (freshness);
   - the fetch and recall latency.
2. **Entitlements over memory:**
   - `--as` on `remember` and `recall`, with `fetched_by` recorded;
   - read-time checks against the principal's allowlist (tables and columns);
   - a row-policied table's facts remembered per principal.

   Checked by check 4, with the entitlement oracle.
3. **The agent side:**
   - the agent-memory model (`Conversation`, `Message`, `ReasoningTrace`, `ToolCall`, `Entity`) and
     `qlsc converse`;
   - an `ask` recorded as a tool call, with Computation stubs;
   - the reserved labels checked in `qlsc virtualize` (collisions).
4. **Distillation** (added 2026-09-29, with the Context Memory model): skills from the agents'
   experience ([its plan](2026-09-29-context-memory-model.md)).
5. **The memory route and the economics:**
   - the router's third route: a fresh context reads memory;
   - `ask --cypher` on memory;
   - check 2, the simulated session (latency and bytes billed).

   MCP tools come after.

**How phase 1 writes (a change from "Where it runs"):** the reads and the write are two steps from
Python, not one composite statement. The reads go to the virtual graph, each signed for the
pass-through; the write is one transaction on memory. Three reasons:
- the second hop's reads are keyed by the first hop's results, and a correlated subquery into the
  virtual graph is bug 2;
- the reads run concurrently;
- the pass-through signs each read on its own.

The composite still joins memory for reading (`fennmoor.memory`).

## Phase 1, as built (2026-09-28)

**The context compiler** (`src/qlsc/memory.py`, `qlsc remember | recall <label> <key | property=value>`):
- **The template is generic.** It's derived from the virtual graph's model:
  - hop 0 is the node;
  - hop 1 is every relationship touching it. The many side is windowed by its table's partition
    column (`memory.window_days`, 90) and capped at the most recent `memory.cap` (200);
  - hop 2 is the to-one relationships out of what hop 1 fetched, each relationship read once.

  For Customer that's 15 reads: the plan's list exactly. Hop 0 and hop 1 run concurrently, and then
  hop 2, keyed on hop 1's nodes (`IN $keys`). Each read is signed for the pass-through.
- **Properties:** the columns the log's queries read or filter on, plus keys and partition columns.
  That's 14 of Customer's 23 columns (`memory.properties: all` keeps every one).
- **Memory:**
  - the `memory` database on the semantic layer's instance, made on first use;
  - `fennmoor.memory` in the composite (made by hand, like the other aliases: docker/nvg/README.md);
  - a node key (source, key) per label, where `source` is the virtual graph's dataset;
  - Table and Column stubs, with `FROM` from every node.
- **Provenance:** `fetched_at`, `holds_until`, `fetched_by` (the data source, in this phase) and
  `fetched_with` (the read's Cypher) on every node and relationship. The anchor also records the
  context: `context_fetched_at`, `context_holds_until`, `context_template` (a digest of the template,
  window and cap) and `context_capped`.
- **Freshness:** the median gap between the table's write days in the log, which is a day for every
  table here. A context holds until its first fact expires.
  - A refetch removes the relationships a read no longer returns, only around the nodes that read was
    keyed on.
  - Nodes stay, and every read from memory requires `holds_until > $now` on each node and relationship.

**Checked** (`eval/memory.py`, results/memory.md; 20 customers: the two the graph questions name, and 18
who called in the window):

| check | result |
|---|---|
| contexts read back from memory exactly as fetched (nodes, properties, relationships) | 20 of 20 |
| the same Cypher, six context questions, same rows on memory and on the virtual graph | 110 of 110 (10 left out: over a capped relationship) |
| remembering again changes nothing | 5,296 nodes, 15,863 relationships, before and after (6,610 and 19,143 on the phase 2 rerun, with its contexts in memory too) |
| within its lifetime, recall reads memory | ok |
| past it, recall fetches again | ok |
| a planted stale fact is never read | ok |
| a refetch removes it | ok |
| a changed template (30-day window) is fetched again | ok |

Latency, per customer:

| | median | p95 |
|---|---|---|
| fetch and remember (15 reads, one write) | 3.6 s | 5.7 s |
| recall from memory | 0.05 s | 0.12 s |
| a context question on the virtual graph | 1.37 s | 2.55 s |
| the same question on memory | 0.006 s | 0.05 s |

The composite reads across memory and the layer in one query: remembered accounts, their table's stub,
and the same table's write days from `fennmoor.semantic`.

**Worth knowing:**
- **Seven of 20 customers hit the cap** on card or deposit transactions (200 in 90 days). Their contexts
  hold the most recent 200, flagged on the anchor. A question over all of them belongs to the virtual
  graph or SQL, which is phase 4's router.
- **Virtual Graph's inner joins show in the counts.** 45 calls, but 30 with an agent: a call with no
  agent has no `HANDLED_BY`. Memory is the same, because it reads the same way.
- **`holds_until` is an upper bound.** The log gives write days, not times, so a fact fetched just before
  the day's load holds until the next day's.
- **Not in this phase:** `--as`, and anything shared between people (phase 2). A context is written as
  the data source only.

## Phase 2, as built (2026-09-28)

**`--as <principal>`** on `remember` and `recall`, as for `ask` (`src/qlsc/memory.py`):
- **The fetch is theirs:**
  - the template comes from the virtual graph's model as the gateway restricts it for them
    (`entitle.model`: readable tables only, no hidden columns);
  - each read is signed for them, so the pass-through runs it as them and BigQuery applies their tables,
    columns and rows;
  - a lookup by a property they can't read (marketing's `cif_number`) is refused before it's sent.
- **Facts that depend on who reads them:**
  - **Which ones:** a node of a table with a row access policy (`dim_customer`), and a relationship
    whose table or either end has one. Which tables have a policy comes from the warehouse, cached as
    the allowlists are.
  - **The mark:** each such fact carries a mark per principal who fetched it
    (`seen_until:<principal>`, as long as the fact holds), and a read of memory needs the reader's own
    mark.
  - **On refetch:** a refetch takes the reader's mark off what it no longer returns. A relationship with
    no mark left is removed.

  Nodes aren't split per principal: one row stays one node, so identity is still (source, key).
- **Other facts** are the same whoever reads them, and are shared: a call, an account, a branch.
- **Contexts are recorded per principal** on the anchor (`context_until:<principal>`, `context_template:…`).
  A recall reads memory only for a context the principal fetched, with their template as it is now. A
  table or column they lost changes the template, so the context is fetched again.
- **An anchor whose table they can't read** is refused (`the warehouse doesn't let … read Customer's
  table`).

**Checked** (`eval/memory_entitlements.py`, results/memory_entitlements.md):
- **The setup.** The anchors are four customers (two in KS, inside risk's row policy, and the two the
  graph questions name, outside it), branch 101 (Topeka, KS) and the busiest agent. The data source
  remembers them all first, so memory holds every row. Then each principal remembers and recalls them as
  themselves.
- **The oracle** is BigQuery, read as the principal directly: not through the gateway, the virtual graph
  or the pass-through. Every node must be a row they may read, with the same values. Every relationship
  must be the foreign key in that row. No property may be a column hidden from them, by the oracle's own
  dry-run allowlist.

| | result |
|---|---|
| recalls checked | 18 (marketing 5, risk 6 with 2 empty, contact-center 1, and 10 refusals) |
| incidents | 0 |
| each read of memory the same as the principal's own fetch | all |
| risk reads memory for a customer others remembered | nothing |
| risk's recall of it | fetched (as nothing), not served |
| contact-center's recall of a customer | refused: it can't read `dim_customer` |

The row policy shows in the counts. Branch 101's context is 931 nodes for marketing (every row) and 636
for risk (KS and NE customers only).

Negative controls, reads of memory broken on purpose, all caught by the oracle:

| broken read | caught by |
|---|---|
| row marks ignored (risk) | rows risk can't read (295 of 353 customers around branch 101) |
| columns unrestricted (marketing) | hidden columns shown: `cif_number`, `full_name`, `primary_email` |
| another's context (risk read with marketing's marks) | a row risk can't read |

**Found on the way:**
- **Phase 1's refetch removed a relationship outright,** even one that depends on the reader. As risk,
  it would have deleted the accounts-to-customers relationships marketing had fetched around branch 101,
  a loss of marketing's facts. Such a relationship now loses only the reader's mark. A relationship with
  no marks at all, such as one left from phase 1, is removed on the next refetch around it.
- **Virtual Graph returns a `TIMESTAMP` without its zone** (the value is UTC). Memory keeps it as
  returned, the same as the virtual graph. The oracle first compared it as local time, and flagged
  every call.

Phase 1's checks, rerun after these changes, all pass: 20 of 20 contexts, 110 of 110 questions, and
freshness.

**Not in this phase:**
- **Sharing a context between principals.** A principal reads memory only for their own contexts. A
  context whose template reads no row-policied table could be shared when two principals' templates
  are identical, but at two hops every template here reaches Customer.
- **Arbitrary Cypher over memory as a principal** (`ask --cypher` on memory, phase 4). It needs the
  same restriction as the virtual graph (the model), and the marks in its `WHERE`.
- **The stubs** (Table, Column) are names only, and anyone reading memory raw sees them. BigQuery shows
  column names to metadata readers too.

## Phase 3, the design (2026-09-29)

**The model is Neo4j Labs' agent-memory, as its source writes it** (`neo4j_agent_memory/graph/queries.py`):
- **Short-term:** `(:Conversation)-[:HAS_MESSAGE]->(:Message)`, `-[:FIRST_MESSAGE]->` the first, and
  `(:Message)-[:NEXT_MESSAGE]->` the next.
- **Reasoning:**
  - one `(:ReasoningTrace)` per user message that calls tools, `-[:INITIATED_BY]->` it, and
    `(:Conversation)-[:HAS_TRACE]->` it;
  - a step per tool call: `(:ReasoningTrace)-[:HAS_STEP {order}]->(:ReasoningStep)-[:USES_TOOL]->(:ToolCall)-[:INSTANCE_OF]->(:Tool)`,
    and `(:ToolCall)-[:TRIGGERED_BY]->(message)`;
  - `(:ReasoningStep)-[:TOUCHED]->` what the step read.
- **Long-term:**
  - the warehouse facts `remember` keeps, with their own labels: a message `-[:MENTIONS]->` them, and
    a step `-[:TOUCHED]->` them;
  - what the agent learns: `(:Preference {category, preference})` and `(:Fact {subject, predicate, object})`,
    each `-[:ABOUT]->` a warehouse fact and `-[:EXTRACTED_FROM]->` the message. People and things
    outside the warehouse are `(:Entity:<POLE+O type>)`, `-[:RELATED_TO {relation_type}]->` what they
    relate to.

**qlsc's tools** are `recall` (an entity's context; the step touches its anchor) and `ask` (a question).
An ask's `ToolCall` records:
- the route, the query and the first rows;
- `-[:USED]->` the stubs of the Tables its query reads and the Computations its request used.

**Validity (Graphiti's style, beyond agent-memory's):**
- **Supersession.** A new preference in the same category, or a fact with the same predicate, about the
  same thing closes the old one (`valid_until`) and `-[:SUPERSEDES]->` it. Nothing is deleted.
- **Expired facts keep their conversations.** A warehouse fact that expires keeps its node (source, key),
  so its conversations stay attached across refetches.

**Entitlements:**
- **Private to its principal.** Everything the agent side records carries `recorded_by`: the principal,
  or the data source. It's read back only by them, because a conversation about a customer holds what
  its principal could read.
- **A mention or `ABOUT` needs a visible fact:** the warehouse fact must be in memory as that principal
  fetched it.

**`qlsc recall` shows what was noted:** the current preferences and facts about the anchor, and the
conversations that mentioned it, the reader's own only.

**`qlsc converse <conversation.yaml> [--as]`** records a conversation. The file gives its messages, the
tools each message called (run as they're recorded) and what the agent learned. The same functions
(`qlsc/converse.py`) are what an agent, or later an MCP server, calls directly.

**No LLM in this phase.** A message mentions what its tools touched and what it names explicitly. Entity
extraction from free text (agent-memory's extractors) comes later, if a demo needs it.

**Collisions:**
- `qlsc virtualize` renames a label that is one of agent-memory's labels, a POLE+O type label, or a
  memory stub label (`Table`, `Column`, `Computation`), falling back to the table's own name.
- None of today's labels collides, so the model doesn't change.

**How it's checked** (`eval/converse.py`): two sessions, a day apart, of a banker with one customer, as
marketing, and one of risk with another. It checks:
- the chain and the traces;
- each tool call's links;
- mentions landing on the warehouse nodes themselves;
- session 2 finding session 1's notes;
- supersession;
- what each principal sees of the others' conversations (nothing);
- that a refetch leaves the conversations attached.

## Phase 3, as built (2026-09-29)

**As designed above** (`src/qlsc/converse.py`, `qlsc converse <file> [--as]`, and `qlsc recall` showing
what was noted):
- **The agent-memory model:** labels, relationship types and properties as agent-memory's own Cypher
  writes them, so its tooling reads this memory.
- **Beyond agent-memory:**
  - `recorded_by`;
  - `valid_from` and `valid_until` on Preference as well as Fact;
  - `SUPERSEDES`;
  - `USED` from an ask's ToolCall to the Table and Computation stubs.
- **Three example conversations** in `examples/fennmoor-bank/conversations/`: marketing-1 and marketing-2
  (a banker and customer 0001000025, a session apart), and risk-1 (a Kansas customer).

**Checked** (`eval/converse.py`, results/converse.md): 16 of 16.

| check | result |
|---|---|
| each conversation's chain: FIRST_MESSAGE, then NEXT_MESSAGE through every message in order | 3 of 3 |
| each tool call: TRIGGERED_BY its user message, in a trace INITIATED_BY it, HAS_TRACE, INSTANCE_OF its Tool | 4 of 4 |
| a recall's step TOUCHED the warehouse Customer | yes |
| the ask (compiled SQL, 10 rows) USED `fct_card_transactions`, `dim_merchant` and one Computation | yes |
| mentions are the warehouse's own Customer nodes (source, fetched_at, FROM a Table stub) | yes |
| marketing-2's recall finds marketing-1's preference, fact, person and conversation | yes |
| marketing-2's preference closes marketing-1's (valid_until, SUPERSEDES); only the new one is noted | yes |
| the data source sees nothing of marketing's notes, and marketing nothing of risk's | yes |
| risk can't note a customer outside its rows | refused |
| remembering the customer again leaves one node and the same notes | yes |

What `qlsc recall --as marketing Customer 8322097816940277129` shows after the two sessions:

    noted: contact channel: phone, mornings (since 2026-09-29)
    noted: interested in: a travel rewards card (since 2026-09-29)
    noted: Ana (person), DAUGHTER_OF
    in 2 conversations, the last 2026-09-29: Travel card follow-up for customer 8322097816940277129

**Collisions:** `qlsc virtualize` renames a label memory reserves (`memory.RESERVED_LABELS`), falling back
to the table's name, then with its dataset's (`dw_web.events` becomes `DwWebEvent`). Today's labels are
unchanged.

**Found on the way: the permission checks failed open.** The owner's gcloud login lapsed overnight, and
every warehouse call failed.
- **What happened:**
  - the connector's permission checks read any error as "no";
  - risk's allowlist was rebuilt with no tables (a misleading refusal);
  - worse, the row-policy cache was rewritten as "no table has a row policy". For 15 minutes memory
    would have treated customers as shared facts.
- **No harm done.** Risk's empty allowlist refused its recall first, and nothing else read or wrote
  memory in those minutes. The bad caches were deleted.
- **The fix:**
  - only a denial (403) or a missing table (404) now counts as "no";
  - a failed login is `WarehouseUnavailable` (`qlsc/warehouse/__init__.py`): raised, never cached;
  - the CLI shows it as `gcloud needs a fresh login (...)`.

**Not in this phase:**
- **Entity extraction from free text.** A message mentions what its tools touched and what it names.
  agent-memory's extractors (an LLM, spaCy or GLiNER) could come later.
- **Vector indexes** on messages and preferences, for semantic search over what was said: agent-memory
  has them.
- **An MCP server** exposing recall, ask and the learning calls: after phase 4.

## Phase 3, rebuilt, and phase 4, distillation (2026-09-29)

The agent side was rebuilt on the Context Memory model. Distillation, the model's differentiator, was
built as phase 4. Both are written up in [the Context Memory plan's as-built section](2026-09-29-context-memory-model.md#as-built-2026-09-29).
In short:
- `eval/converse.py`: 26 of 26 checks.
- `eval/distill.py`: 13 of 13. Two skills were distilled from repeated, successful work, none from the
  failing pattern, with no values in either. The approval gate, the offers by permission, and
  measurement and retirement all held.
- **Phases 1 and 2 now use `READ` edges.** Their checks were rerun on them: `eval/memory.py` and
  `eval/memory_entitlements.py`.

Phase 5, the router's memory route and the economics check, followed the same day (below).

## Phase 5, as built (2026-09-29)

**The memory route** (`navigate.answer_memory`, `navigate.memory_route`, `qlsc ask --memory`):
- **The router asks first whether memory holds the whole answer** (`memory.answerable`), from the compiled
  plan alone:
  1. **One entity.** The plan filters one entity by its key, or a fact by its foreign key to one.
  2. **A fresh context.** The reader's own recall of that entity is fresh, with their template.
  3. **Every table in that context.** Everything the plan reads is in the context: the entity, the facts
     pointing at it (as the template reads them), and their dimensions.
  4. **Inside the window.** A windowed fact's period starts inside the window.
  5. **Nothing capped.** No read it relies on was capped.

  If all five hold, the answer comes from memory; if not, it goes to the compiled SQL, as before. The
  request is the same LLM call either way, and cached.
- **The Cypher is the compiler's,** over the virtual graph's model, with memory's guard on every node and
  relationship (`compile.render_cypher(guard=memory.Guard)`): its source, facts that still hold, and a
  row-policied node only if the reader's own step read it.
  - **Outer joins.** The virtual graph has no `OPTIONAL MATCH`, but memory does. So on memory an outer join
    nothing filters on is `OPTIONAL MATCH`, its guard in its own `WHERE`, and it keeps its null group as
    the SQL's `LEFT JOIN` does. The first economics run found this: 6 answers lost a null group (an
    account without a branch, a call without a site).
- **Every answer from memory leaves a Step,** as every read does.
- **`memory.window_days` is now 92,** a full quarter. At 90 days the window began on 2 April, so "last
  quarter" (from 1 April) could never be answered from memory. The phase 1, 2 and 3 checks were rerun
  with it, and all pass.
- **The connector's `run` takes `cache`,** so a measurement can run BigQuery with its result cache off.

**Checked** (`eval/economics.py`, results/economics.md, check 2): a simulated session of 50 questions, 10
about each of 5 customers, as the data source. The customers had no fetch in the day before, so no
fetch job could be answered from BigQuery's result cache, and none was (0 of 142).

| | without memory | with memory |
|---|---|---|
| questions answered | 49 by SQL (1 of 50 didn't compile) | 49 from memory, all 49 the same rows as the SQL |
| latency per question (the query) | median 0.80 s, p95 1.37 s | median 0.027 s, p95 0.072 s |
| the session's query time | 42.5 s | 29.6 s, the 5 context fetches included (3.7 to 8.5 s each) |
| the session's bytes billed | 2,104 MiB | 2,934 MiB: the fetches, a median 606 MiB each |
| compiling a question (the LLM; common to both) | median 7.7 s | the same |

**What it says:**
- **Memory answers exactly and 30 times faster,** once a context is fetched.
- **It costs more bytes than it saves at ten questions per customer.** A fetch bills about what 14 of these
  questions do in SQL, so memory pays in bytes only past that many questions per context while it holds,
  or across sessions within a day.
- **The session's time is the LLM's,** compiling the question: 7.7 s against 0.8 s for the SQL.

**The fetch's bytes, corrected and brought down** (2026-09-29, after phase 5's commit).

- **The first count was wrong.** BigQuery withholds the statistics of any job that reads a table with a
  row access policy: the job is billed, but its bytes aren't reported. Every hop-0 and hop-1 read joined
  `dim_customer`, so about 580 MiB per fetch was missing from the 606. The eval's job windows also ran 5 s
  past each fetch, into the next one's jobs. A fetch really billed about 950 MiB, about 22 questions' SQL.
- **Why a fetch costs more than a question:** BigQuery bills the columns it scans in the partitions it
  can't skip, not the rows returned. In this estate the fact tables hold exactly one quarter, so the
  92-day window skips nothing, and a day's partition (about 3 MiB) is too small for clustering on
  `customer_key` to skip blocks. A read of 199 card transactions scanned 225 MiB, the whole of its 14
  columns. A question reads 3 to 5 columns of one table; a fetch reads every used column of every table
  in the context. The second hop also rescanned each fact table (about 70 MiB a read) just to follow keys
  the first hop's rows already held.
- **Keyed reads** (`memory.keyed`). Virtual Graph writes a traversal as the start's table joined to
  itself and to the end's. A relationship that is a column of its start node's table is now read by that
  column instead:
  - into the anchor, the facts by their own column (`n.customer_key IN $keys`), with no join to
    `dim_customer`: so their bytes are reported too;
  - out of a hop's facts, the dimensions they name, by key, and only those not fetched yet (an account
    the first hop already has isn't read again); the relationships are made from the keys.
  The rows are the same: contexts fetched both ways are identical, for the data source, marketing, risk
  and contact-center, across Customer, Branch and Agent anchors. The anchor's own read still gates the
  context (an anchor the reader can't see gives an empty one), and every check was rerun: memory,
  memory_entitlements, converse and distill pass.
- **The eval, fixed:** each fetch has the job log to itself (5 s apart, 1 s margins); a job whose bytes
  are withheld, or that the result cache answered, is counted at BigQuery's minimum, 10 MiB per table it
  references. The connector's `run` says when a job's bytes were withheld (`bytes_hidden`).

| | before (corrected) | keyed |
|---|---|---|
| a fetch's bytes billed (median) | about 950 MiB | 557 MiB |
| break-even: questions' SQL a fetch bills | about 22 | 12.5 |
| a fetch's latency (median) | 5.3 s | 4.3 s |
| the session's query time, with memory | | 22.1 s, against 47.3 s without |
| answers from memory, the same as the SQL | 49 of 49 | 49 of 49 |

What's left of a fetch is mostly the first hop's facts at full width (card and deposit transactions,
about 225 MiB each). Here, only a narrower fetch or a batch of entities in one fetch brings that down:
the scan costs the same for one customer or many. In a warehouse with years of history and large
clustered partitions, a customer's reads would prune to a few blocks, both sides would sit near the
per-table minimum, and a fetch's cost would be its count of table references. The next step, batching
many entities per fetch, waits for a decision.

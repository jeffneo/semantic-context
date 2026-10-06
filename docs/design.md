# Design

What qlsc builds, from what, and why each choice was made. The code's module docstrings say how.

## Principle: usage is the ground truth

qlsc infers what a warehouse means (which columns are the same thing, which tables belong together,
what the business areas are) from what the business actually runs: the query log. A designed model
(an ERD, declared keys, catalog descriptions, an ontology) is one author's opinion. qlsc never builds
from one; it aligns them afterwards and reports where design and usage agree and disagree.

Two refinements, still inside that principle:

1. **Count authors, not executions.** A BI join that runs 8,000 times is one modeller's decision
   replayed by its viewers; a dbt join is one engineer's decision replayed nightly. Evidence strength
   is independent convergence: how many distinct people or processes arrived at the same join.
   Executions measure importance, not correctness.
2. **Usage shows how the business operates, not whether it is right.** A join can be heavily used and
   wrong. qlsc prunes nothing on "correctness": it keeps every observed edge with a confidence, and the
   confidence comes from contradictions between usages (a person's join that conflicts with how
   production keys the same columns), not from a designed model.

### Admissible inputs

| Input | Used? | Why |
|---|---|---|
| The query log: text, principal, references, bytes, errors, timing | **Yes, primary** | Executed usage |
| View definitions | Yes | Executed code, and a view's joins are otherwise invisible in the log |
| Catalog names, columns, types, partitioning | Yes, for parsing only | Resolve aliases, `*` and CTEs; asserts no relationships |
| Declared keys, descriptions, ERDs, glossaries, ontologies | Never as input | Designed opinion: aligned and diffed afterwards (`qlsc align`) |
| Row counts, data profiling | No, with one exception | Says nothing about how the data is used. The exception is a safety check, not a source of meaning: `qlsc virtualize` confirms that a key usage proposed is unique (`COUNT(DISTINCT)`) before a Virtual Graph model relies on it |

The boundary is structural: `src/qlsc` never refers to an example, and `tests/test_boundary.py` fails if
it does. An example's spec and answer key are read only by that example's evaluations.

### Which statements build structure

The graph is built from **consumption**: the read side of every statement, not only SELECTs. A MERGE,
CTAS or view body is a read by a production process. On the example's log, 56 of the 65 join
predicates in write statements never appear in any SELECT, and renames (`CIF_NO` -> `cif_number`) exist
only in view and model definitions, so a SELECT-only graph would lose most production join evidence and
disconnect the raw layer from the modelled one. Excluded from structure (kept only as table liveness):
ingestion MERGEs and LOAD jobs, which consume nothing in the warehouse. Failed queries never create
structure; they are kept as error evidence.

## The graph

**Bottom layer**: seven labels, only what the log and the catalog show directly (`qlsc load`).

```
(:Project)<-[:IN_PROJECT]-(:Dataset)<-[:IN_DATASET]-(:Table)-[:HAS_COLUMN]->(:Column)
(:Principal)-[:RAN]->(:QueryShape)-[:READS|FILTERS]->(:Column)
(:QueryShape)-[:USES_JOIN]->(:JoinKey)-[:ON {side}]->(:Column)
(:QueryShape)-[:REFERENCES|WRITES]->(:Table)      (:Column)-[:FLOWS]->(:Column)
```

A QueryShape is one distinct query with its literals taken out, with its run counts as properties (no
Job nodes). Literal values live on `FILTERS` (values, value_jobs, first and last seen); names the
parser could not place are a `QueryShape.unresolved` list.

**Above it**, everything inferred:

| | What | Built by |
|---|---|---|
| `Variable` | The real-world thing a set of joined columns holds; `(:Column)-[:IS]->(:Variable)`. Columns never joined are `:Unjoined` | `qlsc variables` |
| `Computation {kind}` | What the business computes from its columns, again and again: a `measure` (an aggregate, with the filters that come with it), a derived `dimension` (a CASE bucket, a date truncation), a `population` (filters applied together). `(:QueryShape)-[:COMPUTES]->(:Computation)-[:READS]->(:Column)`. Flags: `production`, `trusted`, `health_check` (every query computing it returns one ungrouped row of aggregates) | `qlsc computations` |
| `Request {kind, who, text}` | What the business asks of a query it runs, in its askers' words: two questions by different roles and a task (the step of a business process that ran it), written for each query shape that serves a business consumer (not a load step, a data test, a metadata lookup). `(:Request)-[:FROM]->(:QueryShape)`; shapes link `SUCCEEDS` (the same people started running one as they stopped running another reading alike, a table changed) and `VARIANT_OF` (a table and a trusted Computation in common). Vector index `request_embedding` | `qlsc requests` |
| `Semantic {level}` | A business area. Level 1 groups Variables and Unjoined columns; each level above groups the one below. `-[:IN_SEMANTIC]->` | `qlsc cluster`, `qlsc hierarchy` |
| `K_SIM` | The similarity links a level was grouped from | `qlsc hierarchy` |
| `Concept` | A catalog glossary term, or an ontology class (`:Resource:Class`, `subClassOf`, from rdflib-neo4j) | `qlsc align` |
| `MEANS` | A column's catalog term (exact), or a proposed match of a Variable or Semantic to a Concept (by embedding) | `qlsc align` |

Join confidence is a set of JoinKey properties, not nodes: `confidence` (production, corroborated,
single, suspect, self), `identity`, `production`, `people`, `confidence_reason`.

## The method

1. **Variables.** Columns the business joins hold the same thing. WCC over trusted, identity-preserving
   joins gives one Variable per component. A join is suspect when it equates two id spaces that
   production keeps as separate columns of one table and translates between; suspect joins stay in the
   graph as evidence and build nothing.
2. **Level 1: usage only.** Leiden over Variables and Unjoined columns, linked by how many statements
   read both or derive one from the other. Each group's stability is how much of it comes back over
   reruns with new seeds and resampled statements.
3. **Levels 2 and up: usage fades, language takes over.** Building level L, each pair of nodes scores
   `(1/L) × usage + (1 − 1/L) × text cosine`; each node links to its k best (`K_SIM`); Leiden at
   gamma / (L − 1) groups them. Stop when a level would not shrink. Upper-level names avoid vendor names,
   so two organizations' layers can be matched at the top by embedding.
4. **Navigate (graph RAG).** A question is embedded, vector-searched against every level, walked down
   `IN_SEMANTIC` to level-1 groups (plus the closest level-1 groups directly), then to the tables those
   groups hold, ranked round robin. The log's queries closest to the question (by their SQL's
   embedding) join as examples, skipping any that read a sandbox (a table only people write, never a
   production process) or a frozen table; the tables they read join the cohort. The tables, their joins
   and those queries go to the LLM (`llm.query_model`), which writes one query; the warehouse dry-runs it, and with `--run` runs it, billing at most
   `navigate.maximum_bytes_billed`. With `--cypher` the query is Cypher over the virtual graph
   instead. The LLM gets the cohort's tables that are labels there, plus one hop of relationships
   around them. Before `EXPLAIN`, the query is linted against Virtual Graph's subset (`OPTIONAL MATCH`,
   variable-length paths, `CALL`, `EXISTS`, `UNION`, a `MATCH` after `WITH`, `date()`), each
   relationship's direction is checked against the model, and every label, relationship type and
   property the query names is checked against that part of the model: Virtual Graph runs a pattern over a label it doesn't have
   and returns no rows, so a hallucinated label would otherwise come back as a silently empty answer.
   `EXPLAIN` is then the check, and shows the SQL Virtual Graph sends. Its answer is streamed back and
   capped (`navigate.cypher_max_rows`); the instance caps each transaction's memory and time, so one
   large query fails on its own rather than taking the instance down. When the graph given can't answer
   the question, the writer declines rather than writing a stand-in over the wrong label.
   Both routes get the calendar of the day questions are asked on (`navigate.today`, pinned by an
   estate whose data stops, else the real date) and write periods as literal dates. Virtual Graph
   can't compute dates at all (no `date()`), and a pinned day keeps the answers reproducible from one
   day to the next.
   In both routes each text column carries the values the log's queries filter it on, so code values
   are spelled as the business spells them, not guessed.
5. **Computations and OKF.** The parser's extractor (`qlsc_parse/computations.py`) reads every
   successful shape: in each scope over physical tables, the measures, derived dimensions and
   populations, written over base columns (`fct_card_transactions.amount`) so the same computation in
   two queries is one Computation. A comparison with a date literal or today is the question's period,
   not the definition, and is left out. The LLM names each from its expression and the names queries
   give it. `qlsc okf` writes them as an Open Knowledge Format v0.2 bundle: each Computation an
   `Attested Computation` concept filed under its top business area, the tables it reads as `BigQuery
   Table` concepts, provenance (`sources`, with each query's runs and who ran it) and lifecycle
   (`status`: stable if production computes it, draft if only people do, deprecated on a sandbox or
   frozen table) from the log. Unverified, as inferred definitions are. The closest Computations are the
   compiled request's options (`navigate.compile_computations`). Given to the free writer as
   definitions they didn't help, and that was dropped (see the accuracy plan).
6. **Align.** Catalog bindings are exact; embedding matches are `status: 'proposed'`. The diff lists
   agreement, conflicts (the catalog equating what production keeps apart, or contradicting itself),
   what is designed but unused, and what is used but undesigned.

Every run is deterministic: Leiden and WCC are seeded and single-threaded, and projections are fed in
a fixed order (GDS numbers nodes in arrival order, and Leiden's result depends on that numbering).
Every LLM and embedding call is cached by its full request, so a rebuild over unchanged evidence calls
neither and reproduces the graph exactly.

## Parameters

All of them are in [`src/qlsc/defaults.yaml`](../src/qlsc/defaults.yaml); an estate's config overrides
any. `tests/test_config.py` fails if one is not read by the code. Sensitivity on the Fennmoor example
([results/robustness.md](../examples/fennmoor-bank/results/robustness.md)):

| Parameter | Value | Why | Sensitivity |
|---|---|---|---|
| `variables.joins` | production, corroborated, single | Every join no contradiction rules out | The suspect check catches the planted wrong joins; 50 random wrong merges that slip past it still leave ARI 0.88 vs clean |
| `cluster.seed`, `hierarchy.seed` | 42 | Any fixed seed makes a build repeat | 11 seeds: levels 108 to 110 → 14 to 17 → 4 to 5; NMI vs subjects 0.860 to 0.866 |
| `cluster.gamma` | 4 | Many small, specific groups at level 1 | Flat: gamma 3 to 8 gives NMI vs the spec's subjects 0.85 to 0.87, all seed-stable (ARI 0.96+) |
| `cluster.stability_runs`, `_sample` | 10, 0.8 | Half new seeds, half 80% resamples | Median group stability 0.95 |
| `hierarchy.k` | 5 | Enough neighbours to connect a level, few enough to stay specific | k 3 to 8 at gamma 3: NMI vs spec domains 0.69 to 0.72 |
| `hierarchy.gamma` | 3, divided by L − 1 | High at level 2 (~100 nodes), plain modularity near the top | gamma 1.5 merges too far (NMI 0.64 to 0.68) |
| `align.floor_term`, `floor_class` | 0.52, 0.40 (raw cosine) | Where the best matches turn wrong on inspection | |
| `navigate.examples`, `example_tables` | 3, true | The 3 queries closest to the question by embedding held a question's defining logic for 9 of 10 gold questions (the most-run queries over the cohort, for 4). Their tables found what navigation missed | SQL route, Sonnet 5: 4 of 10 with the most-run examples, 4 with the closest, 6 with the closest and their tables |
| `llm.query_model`, `query_thinking` | claude-sonnet-5-5, between_tools | Writing SQL needs a stronger model than naming. Every model's answers are structured outputs. Sonnet 5.5 can't turn thinking off; between_tools, its lowest, keeps a single answer unthought, as Sonnet 5 ran | Given the answer key's own tables, Haiku 4.5 answered 1 of 10 gold questions, Sonnet 5 answered 4. Full set, compiled: Sonnet 5.5 133 of 176, 128 on a new day's samples (the free writer on Sonnet 5, 129); not yet run free on 5.5, so the model's share is unmeasured |
| `entitlements.allowlist_seconds`, `workers` | 900, 8 | A principal's allowlist (the tables, columns and row policies the warehouse reports for them) is reused for a session, well inside a policy change's reach; its checks run concurrently, one per table | building one over the layer's 177 tables: about 10 s |
| `memory.hops`, `window_quarters`, `cap` | 2, 1, 200 | A context is an entity's relationships and their to-one dimensions (a call's agent, a purchase's merchant). The many side is windowed by its partition column (which also prunes the warehouse's partitions) and capped, so a context stays small. The window starts on last quarter's first day, the period questions ask for most, so "last quarter" can be answered from memory on any day of this one (a count of days did only on some); a capped read is flagged | a customer: 15 reads, 4 to 780 nodes; 7 of 20 customers hit the cap on card or deposit transactions (eval/memory.py) |
| `memory.keys_per_read` | 1000 | A read keyed on more nodes is split: each key is one of the SQL's parameters, and BigQuery takes 10,000 at most. A batch of 50 customers stays within it | eval/economics.py: a batch of 50 |
| `memory.properties` | used | The columns the log's queries read or filter on, with keys and partition columns: what anyone asks of these tables, not every column | Customer: 14 of 23 columns |
| `memory.unknown_hold_days`, `workers` | 1, 6 | A table whose cadence the log doesn't show holds a day, the shortest cadence here; a hop's reads run concurrently | every table the virtual graph serves is written daily |
| `navigate.memory_route` | true | The router answers from memory when memory holds the whole answer: one entity whose context the reader holds fresh, every table in it, the period inside the window, nothing capped. It changes nothing when no context is fresh | 50 questions about 5 customers: 50 from memory, all the same rows as the SQL, a median 0.045 s against 0.71 s; a fetch one at a time bills what 12.7 questions' SQL does, in a batch of 50 a third of one question's per customer (results/economics.md) |
| `memory.tool_result_rows` | 20 | An ask's ToolCall keeps the first rows of its answer, enough for the agent to cite, with the total counted | the example's ask: 10 rows |
| `distill.min_steps`, `min_support`, `min_success` | 2, 3, 0.7 | A procedure is two tool calls or more (one is just using a tool). A skill needs three tasks, most of them successful, as a Computation needs repeated use | the check's failing pattern (0 of 3 successful) and one-offs (1 each) yield no skill |
| `distill.similarity`, `gamma`, `seed` | 0.5, 1.0, 42 | Tasks join when half of what they did and read is shared; seeded Leiden, as the build's. The same threshold decides which skill a task followed | the LLM compiles one kind of question slightly differently each time; half-overlap keeps the variants together |
| `distill.offers`, `offer_similarity` | 3, 0.45 | At most three approved skills offered to a new task, by the raw cosine of its request (masked) to a skill's trigger | see results/distill.md |
| `distill.retire_below`, `negative` | 0.6, [wrong, unhelpful, declined, rejected] | An approved skill whose followers succeed less often is retired; these ratings and outcomes make a task a failure | |
| `entitlements.token_seconds` | 300 | How long a principal token signed for the JDBC pass-through holds: one question's queries, never a session's. Virtual Graph reads within seconds of signing | a Cypher answer takes about 3 to 30 s |
| the compiled request (`navigate.compile_computations`, `compile_hops`, `computation_min_similarity`) | 12, 2, 0.8 | The LLM fills one typed request (measures, possibly from several facts, per-entity two-step measures, derived measures, HAVING, dimensions, filters, period, or a list of rows) from the layer's options: the cohort's tables, the trusted joins, and the closest Computations above the similarity floor (a distant one misleads more than it helps). qlsc/compile.py resolves it into a plan and renders SQL; the memory route renders the same plan as Cypher over the virtual graph's model. Joins along the log's trusted joins with the log's join type, never multiplying the fact's rows; Computations exactly as defined. Free writing for what doesn't fit. Over the virtual graph, compiled Cypher was the compiled SQL's plan with less (one fact only; no OPTIONAL MATCH, so an outer join's null group is lost), so the router never took it, and it was dropped: `--cypher` is free Cypher | SQL, two log samples of 59: free 47, first compiler 48, wider request 45, with the request checks 48; gold 7 each. Full set on Sonnet 5.5: 133 of 176 (compiles 154, 121 correct); after the simplification (a new day, so new samples) 128 (compiles 156, 117 correct); after the build's last round of names, gold 7, graph-shaped 6 (plans/2026-09-28-compiler.md, -compiler-2.md, 2026-09-29-simplification.md) |
| `navigate.compile_checks`, `compile_check_chars` | true, 4 | Before compiling, a Computation's filter on a value the question doesn't say, and a value the question says that the request leaves out (of a table it reads, no word its own tables and columns name), send the request back once with notes; a week grain follows how the log's Computations truncate that column. Advisory, so a false alarm costs one LLM call | quick tests: fire on 5 of 73 questions; SQL 45 → 48 of 59 (three answers regained, none lost); Cypher 11 → 12 of 40 |
| router (`qlsc ask --route`) | a rule | Memory when it holds the whole answer; a precedent (below); compiled SQL when the request compiles; otherwise free Cypher when it answers (not declined, checked, run); otherwise free SQL. Free Cypher reaches the neighbourhood and path questions a request can't express. No decider model is needed for this choice | full set: 128 of 176 (SQL alone 128); gold 7 (SQL 7), graph-shaped 7 (SQL 6, Cypher 8) (plans/2026-09-26-router.md, revised) |
| `requests.sql_chars`, `succeeds_days`, `succeeds_reads` | 6000, 21, 0.4 | The writer reads a query whole up to the longest dashboard query. SUCCEEDS needs the same people, within three weeks, reading alike (the churn v2 to v3 cutover reads 0.5 alike, a day apart) | 364 of 810 candidate shapes serve a business consumer: 1,092 Requests, 2 SUCCEEDS, 550 VARIANT_OF |
| `navigate.precedent_route`, `precedents`, `precedent_pool` | true, 3, 60 | Before writing a request, try the business's own query for a request like this one: the query shapes of the three closest Requests, each read with the question (is it this query with other values? the query with its literal values set), the first still that shape by the parser's fingerprint and passing its dry run answers. The business's own SQL, run as it runs it. A rejected precedent is never offered again in a correction | on 186 questions through an agent (eval/comparison): 89 first answers by precedent, 86 right, median 864 tokens and 3.5 s; the compiled request's 97: 75 right, 10,307 tokens, 8.6 s |
| `service.targets` | tokens 20,000; seconds 30 | What answering one request may cost, from the request to its final answer, corrections included (`qlsc/meter.py`): about three of the layer's one-shot answers, so two answers fit and an open-ended exchange doesn't. A request is delivered when it is right within them | one-shot layer: median 6,700 tokens, 4.4 s |
| `memory.answer_rows` | 1000 | An ask's answer is kept whole up to this many rows, to answer the same request again while its data holds; a longer one is run again | |
| `navigate.today` | null (the real date); the Fennmoor estate pins 2026-07-13 | Relative periods need a day. An estate whose data stops pins it to the data's last day, so "last quarter" has rows, a period to today holds all of them, and a new day doesn't rewrite every query. Fennmoor pinned the day after the log window at first, while its lagged tables (loan decisions, campaign attributions) run twelve days past it; a rule leaving a period that ended today open made up for it, and went with the new day | Unpinned, a new day missed the LLM cache and changed three gold Cypher verdicts |
| `navigate.filter_values` | 8 | Enough for a code list (segments, families, statuses); more adds noise from free-text filters | Q12 and Q14 went from guessed values to the data's |
| `navigate.maximum_bytes_billed`, `rows_shown` | 1 GB, 20 | `ask --run`: the gold questions run so far each bill under 100 MiB at the example's scale; a query over it fails rather than runs | |
| `navigate.mode`, `rank` | combined, round_robin | The direct level-1 search guards against a group filed under the wrong parent; round robin keeps a hub table from crowding out the closest group's core table | [results/navigation.md](../examples/fennmoor-bank/results/navigation.md); over seeds, recall 59% ± 7 ([results/seeds.md](../examples/fennmoor-bank/results/seeds.md)) |

Noise: random cross-estate queries at 100% of the real statement count leave ARI 0.87 against the
clean grouping and barely move NMI against the spec (0.850 vs 0.853).

## Decisions

- **Inputs** as above. A catalog or an ontology is an enhancement layered on the usage graph, never its
  foundation.
- **Granularity:** QueryShape nodes with run counts, no Job nodes.
- **Models:** Claude Haiku 4.5 for naming; Claude Sonnet 5.5 for the queries and the compiler's requests,
  at its lowest thinking setting; Azure OpenAI `text-embedding-3-large` at 512 dimensions. One line each in
  the config.
- **Warehouses:** one connector per warehouse (`src/qlsc/warehouse/`), chosen by `warehouse.type`. The
  log record's field names follow BigQuery's JOBS view; other connectors map onto them. The parser
  resolves BigQuery SQL only so far (`parser/qlsc_parse/catalog.py` DIALECTS); a second dialect is its
  own piece of work.
- **Designed-vs-used diff:** built (`qlsc align`), with every embedding link proposed, not asserted.

- **Entitlements** (plans/2026-09-27-entitlements.md; phase 3, plans/2026-09-28-jdbc-passthrough.md): `qlsc ask --as <principal>` goes
  through a gateway (`src/qlsc/entitle.py`) that asks the warehouse, as the principal, what they may read,
  and never re-implements its rules.
  - **The allowlist:** tables by permission check (a view also by dry run, since a view reads with its
    reader's grants); columns by policy tag and whether the principal may read the tag; where the
    warehouse filters rows per reader. The connector answers all four (`acting_as`, `readable`,
    `column_tags`, `readable_tags`, `row_policies`).
  - **What navigation shows:** only what the allowlist admits. A group or Semantic area that isn't
    wholly readable is shown without its name (stricter than the plan's "without its summary": a name is
    written from the same members). Examples only when they read at least one table, every table and
    column they read is readable, and their text names nothing hidden (a metadata query reads no table
    and may name any in its literals); who ran them, as a kind. Never a tagged column's filter values.
  - **SQL** runs as the principal: the warehouse enforces everything, exactly.
  - **Cypher, through the JDBC pass-through** (`vg-passthrough/`), which is required:
    - **Signing.** The gateway signs every query it sends to the virtual graph with
      `$qlsc_principal`: an HMAC token for the principal, or for the data source when none is named.
    - **Running as the principal.** A driver standing in for BigQuery's, in Virtual Graph's own JVM,
      verifies the token and takes the predicate out. It runs the SQL on a connection impersonating
      that principal, so the warehouse enforces tables, columns and rows exactly as on SQL.
    - **Refusals.** An unsigned, forged or expired statement is refused. The exceptions are metadata,
      and Virtual Graph's startup check that a key is unique.

    - **Failing closed.** Before the virtual graph reads on a principal's behalf, the gateway checks once
      that it refuses an unsigned query. A virtual graph running the plain driver reads everything as its
      own identity, so the gateway refuses it any principal's read: Cypher is refused (the router goes to
      SQL), and so is a principal's recall. The jar mounted as the driver is the one switch.

    The gateway still restricts the model to what the principal may read. A second path without the
    pass-through (option A: Cypher only where no table has a row policy, with dry runs of each table's
    columns) was dropped: memory never consulted it, so a principal's recall would have read a
    row-policied table as the virtual graph's own identity.
  - **Checked by an oracle** built on different mechanisms: the allowlist by dry runs, SQL answers
    rerun as the principal, Cypher answers checked against BigQuery's job log (every job ran as the
    principal), canaries scanned in every response and prompt, the driver probed directly, and four
    broken gateways the checks must catch (`eval/entitlements.py`).
- **Memory** (plans/2026-09-27-agentic-memory.md; the model, plans/2026-09-29-context-memory-model.md):
  `qlsc remember` and `recall` keep an entity's context, fetched from the virtual graph, in a `memory`
  database beside the semantic layer. A rebuild never touches it. `fennmoor.memory` joins it to the
  composite.
  - **What a context is** comes from the virtual graph's model, not per estate:
    - the node itself;
    - every relationship touching it, the many side windowed by its table's partition column and capped
      at the most recent;
    - then, to `memory.hops`, the to-one relationships out of what was fetched (a fact's dimensions).

    Its properties are the columns the log's queries read or filter on.
  - **One read, two targets.** `qlsc virtualize` writes every relationship as a column of its start
    node's table, so every read is the nodes of a label whose property is in `$keys`: the anchor by its
    key, the facts into it by their own `customer_key`, a to-one end by the key the nodes already
    fetched hold (only those not fetched yet). A hop at a time, so hop 0 runs before hop 1. Nothing
    traverses a relationship: Virtual Graph writes a traversal as the start's table joined to itself and
    to the end's, rescanning the fact table and billing the far one. The same read runs on memory, where
    it adds `source` and freshness, so a remembered context can be checked read for read against a fresh
    fetch. The anchor's own read gates the context.
  - **Relationships are derived when a node is written,** from its column: a written node's
    relationships of each type are replaced from it, and it gains those of the nodes already remembered
    that point at it. So a relationship keeps no state of its own. It holds as long as its two nodes do,
    and the memory route traverses it.
  - **Batches** (`qlsc remember LABEL KEY...`). Many anchors' contexts are fetched together, each read
    keyed on what all of them fetched. The warehouse bills the columns it scans, not the rows it returns,
    so a batch costs about what one context does. Each anchor still gets exactly the context it gets
    alone, with its own recall step: checked for 20 customers, and as each principal. The cap stays per
    anchor: a read into the anchors is ordered by anchor, then the most recent, and read in pages of
    (cap + 1) × anchors rows, again for the anchors a page left incomplete. Keys past
    `memory.keys_per_read` split a read. A fetch costs 541 MiB per customer alone, 12 in a batch of 50.
  - **Identity:** the virtual graph's labels, types and keys, with `source` on every node. A node key
    is (source, key) per label.
  - **Provenance:** on every node, `fetched_at`, `holds_until`, `fetched_by` and `fetched_with` (the
    read's Cypher). Every node links `FROM` a stub of its layer Table, and the
    stub links to stubs of the Columns kept. A stub holds an id that survives a rebuild, and a name.
  - **Freshness from usage:** a fact holds for its table's write cadence in the log, and a frozen
    table's facts hold for good.
    - `recall` reads memory while the context holds. It fetches again once it doesn't, or once the
      template changed.
    - A node a fetch no longer returns (it left the window) stays, and a stale one is never read as
      fresh, nor are its relationships. A fact that points elsewhere now is rewritten when it's fetched.
  - **Every recall is a Step its reader owns:** `(:Step {tool: 'recall', owner})-[:READ]->`. Every read
    leaves a record of who read what, and when, from memory too.
  - **Entitlements** (`--as <principal>`): a remembered row has left the warehouse's enforcement.
    - **The fetch is theirs.** The template is the virtual graph's model as the gateway restricts it for
      them, and every read is signed for them. BigQuery applies their tables, columns and rows.
    - **A node of a table with a row access policy** is read from memory only by a principal whose own
      recall step `READ` it, while that read holds, and so is a relationship to it. One row stays one
      node, so identity is still (source, key). A relationship to a node the reader can't see says only
      the key its start node holds, which they read.
    - **Everything else is shared,** since it's the same whoever reads it.
    - **The context record is the reader's own recall step** (its `READ` of the anchor, with the
      template it used). A recall reads memory only for that, with their template as it is now. A table
      or column they lost changes it, so the context is fetched again.
  - **The agent's side** (`qlsc converse`, `src/qlsc/converse.py`) is the Context Memory model. Its eight
    labels are `Conversation`, `Message`, `Task`, `Step`, `Decision`, `Fact`, `Entity` and `Skill`. Its
    ten relationship types are `PART_OF`, `NEXT`, `FROM`, `READ`, `ABOUT`, `MENTIONS`, `BASED_ON`,
    `SUPERSEDES`, `SAME_AS` and `FOLLOWED`.
    - **Tasks.** Each user message starts a Task. Its Steps are qlsc's tools: an `ask`'s step keeps its
      query and `READ`s the Table and Computation stubs it used. A step's fingerprint is its call without
      its values.
    - **Knowledge.** Preferences, relations, outcomes and ratings are all Facts (`predicate`, `value`),
      `ABOUT` their subject. Decisions are `BASED_ON` facts and steps.
    - **Long-term memory.** The warehouse facts are the long-term memory, under their own labels: a
      message `MENTIONS` the `Customer` itself.
    - **Nothing is edited or deleted.** A new fact `SUPERSEDES` the old, `{because: changed}` (it held
      until now) or `corrected` (it never held). A decision based on a superseded fact is flagged to
      revisit.
    - **Private to its principal.** Everything has an `owner`, taken from the gateway and never from
      content, and a `scope`. It's read back only by its owner, and `qlsc recall` shows the reader's
      own notes.
    - **Reserved labels.** A virtual graph label may not take a name memory uses:
      `memory.RESERVED_LABELS`, which `qlsc virtualize` enforces.
  - **Distillation** (`qlsc distill`, `src/qlsc/distill.py`): the method qlsc uses on the query log,
    applied to the agents' own record.
    1. **Cluster.** Tasks of two or more steps are clustered by what they did and read: Jaccard
       similarity, then seeded Leiden.
    2. **Propose.** A cluster that repeats and succeeds becomes a proposed Skill. Its procedure is
       written from the fingerprints, schema only. Its name comes from the LLM, over masked requests,
       and is checked against every literal of its evidence.
    3. **Approve.** A person approves it (`qlsc skills --approve`), and only then is it offered to new
       tasks that fit. It's offered only to readers who may read every table it's about.
    4. **Measure.** Tasks that follow it are recorded with `FOLLOWED` and counted, and it's retired when
       they stop succeeding.
    5. **Keep evidence private.** Others see how many tasks a skill came from, not which.
  - **The memory route** (`navigate.memory_route`, `qlsc ask --memory`): the router answers a compiled
    question from memory when memory holds its whole answer (`memory.answerable`):
    1. **One entity.** The plan filters one entity by its key, or a fact by its foreign key to one.
    2. **A fresh context.** The reader's own recall of that entity is fresh.
    3. **Every table in that context.** Everything the plan reads is in the context: the entity, the
       facts pointing at it, and their dimensions.
    4. **Inside the window.** A windowed fact's period starts inside the window.
    5. **Nothing capped.** No read it relies on was capped.

    The Cypher is the compiler's, over the virtual graph's model, with memory's guard on every node and
    relationship (`compile.render_cypher(guard=memory.Guard)`): its source, facts that still hold, and a
    row-policied node only if the reader's own step read it. Its read leaves a Step, as every read does.
    Otherwise the question goes to the compiled SQL, as before.
  - **Answers are kept** (`converse.Conversation.ask`): an `ask` step keeps its answer whole until the first table
    it read is written again (`holds_until`, the table's write cadence), and the same request (words, day, query
    model, reader's grants: `converse.asked`) is answered from memory, a new step `-[:SAME_AS]->` the one that
    answered, with no LLM or warehouse call. The asker's verdict is a `Fact {predicate: accepted | rejected}`
    about the step. `correct()` asks again in the same Task with everything said so far (`navigate.corrected`:
    navigated again, the previous request beside the correction, `prompts/correction.md`); a rejected answer is
    never reused, and a rejected precedent never offered again. No new labels.
  - **Reads and writes are two steps from Python,** not one composite statement. The second hop is
    keyed on the first's results (a correlated subquery into the virtual graph is Virtual Graph bug
    2), and each read is signed on its own.

- **The process graph, built from text** (plans/2026-10-05-text-graph-construction.md; `src/qlsc/process/`): the unstructured source is a
  path in the config (`process.events`; a path, a `gs://` URI read as the warehouse's gcloud identity, or https), never a table.
  - **Two labels, `State` and `Action`,** and `SELECTS` (State to the Action taken) and `LEADS_TO` (Action to the State left), each with
    `num` and `probability` (`num` over the element's turns, so what is left is the share that ended there, `ends`). A turn is not a node:
    the event-to-element mapping is a file beside the build, and an element keeps a few `examples` (event ids and the conversations they
    are from). An element's id is its kind and a hash of its name.
  - **Annotation is per turn from the conversation so far** (one call per turn; the one-call-per-conversation unit saved $9 but separated
    States worse). An Action begins with a verb from `process.action_verbs`, so reworded questions cannot split one Action in two.
  - **Grouping is nearest neighbours, never all pairs, and deterministic:** GDS kNN over a projection built from a query sorted by id (GDS
    numbers nodes in arrival order, and a native projection takes Neo4j's internal ids, which recreated nodes do not get in the same
    order), seeded Leiden with one thread. Observations are scratch nodes in labels of their own (`ObservationState`), deleted before a
    build ends. Every LLM and embedding call is cached by request, so a rebuild makes none.
  - **The parameters were tuned twice, and the second time mattered:** a cut chosen on 100 conversations fragmented Actions and mixed stages
    at 2,000, so it was chosen again on a different slice and judged on one nobody tuned on (similarity 0.90). A tuned graph is scored on the
    conversations it was not tuned on.
    - **Neighbours are kept, and found by the vector index.** `K_SIM {score, rank, level, transitions}` joins each element to its nearest of the same
    kind at every level, from a cosine vector index per label (`process_state_embedding`, `process_action_embedding`), which is also how a
    query enters the graph by similarity. Against exact neighbours the index is 99.98% recall, GDS kNN 98.5% (and not repeatable with threads);
    GDS stays only for turns, which are not nodes.
  - **Outcomes** (`qlsc process outcomes`): the end of each conversation and the agent's after-call note (read for the outcome and never for a
    State) described by one call, rated 1 to 5, the descriptions grouped into kinds of outcome that are discovered, not given. The rating
    tracks the planted favourability (Spearman 0.75, AUC 0.92 for ended well); the kinds mix what was done with how it ended, and an outcome
    the text cannot show (a fix that did not fix) is not found. The vocabulary is files beside the build (`outcomes.ndjson`, `outcome_types.json`).
  - **Odds on States** (`qlsc process absorb`, `src/qlsc/process/absorb.py`; no calls): a conversation's last State is where it was absorbed into its
    outcome, so each State and Action carries `support` (conversations through it), `end_well` (the share that ended well: rating at least
    `process.absorb.good_rating`) and its likeliest kinds of outcome with their odds, **as properties, not an Outcome label**. Two estimates, scored
    leave-one-conversation-out against the planted favourability: `empirical` (of the conversations through the element) and `chain` (the
    absorbing chain over the lifted transitions, solved by sparse sweeps). On the holdout they are level (Brier 0.201 and 0.200 against the global
    rate's 0.236; the paired difference is zero) and `empirical` is stored, as it needs no assumption and says "thin" honestly. The odds are
    modest (AUC 0.64 at the opening State rising to 0.78 at the last) and an element under `process.min_support` carries none: **66% of the
    checkpoints in a conversation's life sit in a State with enough conversations, and 90% of States are too thin to carry odds**; the rest
    is for nearness to cover (phase 4). A node takes its values from the chain at its own level. The raw counts are stored too (`support_good`,
    `outcome_kinds`/`outcome_counts` on elements, `num_good` on transitions), so the graph alone can pool them.
  - **Outlook** (`qlsc process outlook`, `src/qlsc/process/outlook.py`): a live case's last customer turn is annotated and embedded as the build
    does, looked up in the State vector index, and its 5 nearest States' counts pooled into the odds of ending well and in what, and for each
    Action reps took next how often and how those cases ended (level 2 Actions, pulled toward their own rate). **Nearness covers what coarseness
    could not**: the pooled Brier is 0.185 against 0.201 for the assigned State and 0.236 for the global rate, and coverage goes from 66% to 100%.
    **Ranking the next Actions by how the cases ended beats ranking by how often reps took them, but not the rep who has the real case** (24% of
    recommendations fix the real cause or ask a true unsaid clue, against 26% and 20%), and it fails where a clue is still waiting (16%, below chance:
    it almost never recommends a question, and recommends a remedy that does nothing for the cause 20% of the time against the reps' 3%). The
    payload says it is observational. Three attempts to improve the ranking (the best follow-up instead of the average, a trust threshold, an
    asking mode) were no better and are recorded in `results/process_outlook_ranking.md`: the success of an Action is confounded by the cause the rep
    knew and the State does not say.
  - **Levels above the first** (`src/qlsc/process/abstract.py`; plans/2026-10-06-process-abstraction.md): the same kNN and seeded Leiden over the
    elements' stored vectors, the semantic layer's `gamma / (L - 1)` schedule, a transition-similarity term, parents named by an LLM and
    identified by a hash of their children. A node has a `level`, a child `-[:PART_OF]->` its parent, and a node nobody grouped is carried up; a
    level's transitions carry that `level`. **Actions get levels; States do not**: every coarser State level mixed stages, so States stay at
    the first level (`process.levels.kinds`).
  - **Context at a moment** (`src/qlsc/process/context.py`): memory's reads with a window that ends on the call's day (`as_of`), read and
    never remembered; a table outside the virtual graph's model is read from the warehouse by the column the layer says holds the subject's key;
    the turns' words are matched to the customer's own rows by lookup (a name carried by several merchants is no link by itself; a purchase's
    amount and its merchant's name pick one).

## Known limits

- A permission check that can't reach the warehouse (a lapsed login) is an error, never a "no"
  (`WarehouseUnavailable`). The gateway's and memory's caches (the allowlists, the tables with row
  policies) hold only answers the warehouse gave.

- The example log uses about 150 distinct column-level join predicates and no SELECT has more than 3
  joins; a real log has a long tail of one-off joins and 6 to 10-join queries. Join recovery scores
  flatter qlsc there.
- The process graph's first level is faithful and fine, not coarse: about 800 Action elements for 64 planted actions (completeness 0.65) and
  a quarter of State turns in a State no other turn shares. Its likeliest-next-Action recommendation can only match what reps do. Coarser
  levels, where a case ends and outcome odds are the next plan (plans/2026-10-03-business-process-graph.md). Folding near-duplicate names is
  quadratic in the elements (17 s at 3,000 with a dot product in C; 84 s before), the stage to watch if elements grow into the tens of thousands.
- A call nobody was identified on has no customer, so no context.
- States have no level above the first: grouping States by what they say merges stages (a level that coarsens them keeps 70% to 80% stage
  purity, against 90% for the first). Coverage for the 25% of State turns in a State of their own is to come from nearness at query time, not
  from a coarser State.
- BigQuery skips column-level (policy tag) checks for a query it can prove returns no rows: `LIMIT 0`,
  `WHERE FALSE`, or a literal NULL for a value. Nothing is returned, but a check built on such a dry run
  checks nothing. The gateway's and the oracle's dry runs use `LIMIT 1` and never fill parameters in.
- BigQuery shows column names to anyone who may read a table's metadata; policy tags protect the values.
  A principal's own `INFORMATION_SCHEMA` query lists a hidden column's name. The gateway hides names it
  shows; it doesn't try to hide what the warehouse itself tells the principal.
- A fill that recreates a tagged or row-policied table drops its policy tags and row policies:
  `examples/fennmoor-bank/entitlements/setup.py` restores them, and reports what is in place.
- Navigation depends on which of several equally good level-1 groupings Leiden settles on. Over 11
  seeds ([results/seeds.md](../examples/fennmoor-bank/results/seeds.md)), the grouping's agreement with the
  spec barely moves (NMI vs subjects 0.863 ± 0.002) but cohort recall ranges 50% to 68% (mean 59%, sd
  7), with 13 or 14 of 14 questions hitting an expected table. The configured seed's 54% is one draw;
  compare navigation changes over seeds, not one run.

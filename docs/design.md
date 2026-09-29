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
   frozen table) from the log. Unverified, as inferred definitions are. Offering the closest
   Computations to the query writer (`navigate.computations`) is off by default: in a quick test it
   didn't help (see the accuracy plan).
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
| `hierarchy.k` | 5 | Enough neighbours to connect a level, few enough to stay specific | k 3 to 8 at gamma 3: NMI vs spec domains 0.70 to 0.71 |
| `hierarchy.gamma` | 3, divided by L − 1 | High at level 2 (~100 nodes), plain modularity near the top | gamma 1.5 merges too far (NMI 0.68, less stable) |
| `align.floor_term`, `floor_class` | 0.52, 0.40 (raw cosine) | Where the best matches turn wrong on inspection | |
| `navigate.examples`, `examples_by`, `example_tables` | 3, similarity, true | The most-run queries over the cohort held a question's defining logic for 4 of 10 gold questions; the 3 closest by embedding, for 9. Their tables found what navigation missed | SQL route, Sonnet 5: 4 of 10 with the most-run examples, 4 with the closest, 6 with the closest and their tables |
| `llm.query_model`, `query_thinking` | claude-sonnet-5-5, between_tools | Writing SQL needs a stronger model than naming. Sonnet 5.5 takes no forced tool (answers come as structured outputs) and can't turn thinking off; between_tools, its lowest, keeps a single answer unthought, as Sonnet 5 ran | Given the answer key's own tables, Haiku 4.5 answered 1 of 10 gold questions, Sonnet 5 answered 4. Full set, compiled: Sonnet 5.5 133 of 176 (the free writer on Sonnet 5, 129); not yet run free on 5.5, so the model's share is unmeasured |
| `llm.query_effort` | null | With `query_thinking: adaptive`, how hard the query model reasons. High effort gained nothing on the free writer's quick test, for more latency and tokens | free writer, 69 questions: 55 without, 55 with high effort (5 moved); 3.1 s and 331 output tokens per question without, 3.8 s and 433 with |
| `entitlements.allowlist_seconds`, `workers` | 900, 8 | A principal's allowlist (the tables, columns and row policies the warehouse reports for them) is reused for a session, well inside a policy change's reach; its checks run concurrently, one per table | building one over the layer's 177 tables: about 10 s |
| `memory.hops`, `window_days`, `cap` | 2, 90, 200 | A context is an entity's relationships and their to-one dimensions (a call's agent, a purchase's merchant). The many side is windowed by its partition column (which also prunes the warehouse's partitions) and capped, so a context stays small; a capped read is flagged | a customer: 15 reads, 4 to 780 nodes; 7 of 20 customers hit the cap on card or deposit transactions (eval/memory.py) |
| `memory.properties` | used | The columns the log's queries read or filter on, with keys and partition columns: what anyone asks of these tables, not every column | Customer: 14 of 23 columns |
| `memory.unknown_hold_days`, `workers` | 1, 6 | A table whose cadence the log doesn't show holds a day, the shortest cadence here; a hop's reads run concurrently | every table the virtual graph serves is written daily |
| `entitlements.token_seconds` | 300 | How long a principal token signed for the JDBC pass-through holds: one question's queries, never a session's. Virtual Graph reads within seconds of signing | a Cypher answer takes about 3 to 30 s |
| `navigate.anchors` | question | `parts` breaks the question into measures, groupings, filters and entities, and navigates from each; in a quick test it was about even (gold 7 of 10 both, a log sample 23 of 30 against 22), so the single embedding stays the default | see the accuracy plan, 2026-09-27 |
| `navigate.computations`, `computation_min_similarity` | 0, 0.8 | As first built, the closest Computations misled more than they helped: a close look-alike displaced what a question needed. With a similarity floor, equivalents merged and parameters left out of definitions, they were a wash on the full set: a close definition still gets over-applied. Off | all 176 log questions: 129 without, 130 with 5 definitions (4 gained, 3 lost); gold 7 either way |
| `navigate.writer` | free | `compiled`: the LLM fills one typed request (measures, possibly from several facts, per-entity two-step measures, derived measures, HAVING, dimensions, filters, period, or a list of rows) from the layer's options; qlsc/compile.py resolves it into a plan and renders SQL, or Cypher over the Virtual Graph (one fact only; no OPTIONAL MATCH, so an outer join's null group is lost). Joins along the log's trusted joins with the log's join type, never multiplying the fact's rows; Computations exactly as defined. Free writing for what doesn't fit. Level with the free writer; its misses are now the request's choices, not the SQL | SQL, two log samples of 59: free 47, first compiler 48, wider request 45, with the request checks 48; gold 7 each. Cypher, 40 questions: free 10, compiled and checked 12. Full set on Sonnet 5.5: 133 of 176 (compiles 154, 121 correct), gold 6, graph-shaped 5; Cypher 38, 3, 8 (plans/2026-09-28-compiler.md, -compiler-2.md) |
| `navigate.compile_checks`, `compile_check_chars` | true, 4 | Before compiling, a Computation's filter on a value the question doesn't say, and a value the question says that the request leaves out (of a table it reads, no word its own tables and columns name), send the request back once with notes; a week grain follows the log's truncation of that column; a period ending today that the question doesn't end is left open (the data may run past today). Advisory, so a false alarm costs one LLM call | quick tests: fire on 5 of 73 questions; SQL 45 → 48 of 59 (three answers regained, none lost); Cypher 11 → 12 of 40 |
| router (`qlsc ask --route`) | a rule | Compiled SQL when the request compiles; otherwise free Cypher when it answers (not declined, checked, run); otherwise free SQL. Compiled Cypher is the same plan with less, so it never wins where SQL compiles; free Cypher reaches the neighbourhood and path questions a request can't express. No decider model is needed for this choice | full set: 133 of 176 (SQL alone 133), gold 6 (SQL 6), graph-shaped 8 (SQL 5, Cypher 8) (plans/2026-09-26-router.md, revised) |
| `navigate.concepts` | 0 | Designed models are aligned, not inputs; giving the writer their terms is an experiment | all 176 log questions: 130 without, 133 with 6 terms (5 gained, 2 lost); gold 7 either way |
| `navigate.today` | null (the real date); the Fennmoor estate pins 2026-07-01 | Relative periods need a day. An estate whose data stops pins it, so "last quarter" has rows and a new day doesn't rewrite every query | Unpinned, a new day missed the LLM cache and changed three gold Cypher verdicts |
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
  - **Cypher, through the JDBC pass-through** (`vg-passthrough/`, when the estate sets
    `virtualize.passthrough`):
    - **Signing.** The gateway signs every query it sends to the virtual graph with
      `$qlsc_principal`: an HMAC token for the principal, or for the data source when none is named.
    - **Running as the principal.** A driver standing in for BigQuery's, in Virtual Graph's own JVM,
      verifies the token and takes the predicate out. It runs the SQL on a connection impersonating
      that principal, so the warehouse enforces tables, columns and rows exactly as on SQL.
    - **Refusals.** An unsigned, forged or expired statement is refused. The exceptions are metadata,
      and Virtual Graph's startup check that a key is unique.

    The gateway still restricts the model to what the principal may read, and dry-runs each table's
    columns as them first.
  - **Cypher without it (option A):** Virtual Graph reads as one identity. So the gateway allows Cypher
    only where no table in the query has a row policy, and the same dry runs pass. A refused Cypher
    answer sends the router to SQL.
  - **Checked by an oracle** built on different mechanisms: the allowlist by dry runs, SQL answers
    rerun as the principal, Cypher answers checked against BigQuery's job log (every job ran as the
    principal), canaries scanned in every response and prompt, the driver probed directly, and five
    broken gateways the checks must catch (`eval/entitlements.py`).
- **Memory** (plans/2026-09-27-agentic-memory.md, phases 1 and 2): `qlsc remember` and `recall` keep an
  entity's context, fetched from the virtual graph, in a `memory` database beside the semantic layer. A
  rebuild never touches it. `fennmoor.memory` joins it to the composite.
  - **What a context is** comes from the virtual graph's model, not per estate. It's the node; every
    relationship touching it (the many side windowed by its table's partition column and capped at the
    most recent); then, to `memory.hops`, the to-one relationships out of what was fetched (a fact's
    dimensions). Its properties are the columns the log's queries read or filter on.
  - **One Cypher, two targets.** Each read is written once, for the virtual graph (signed for the
    pass-through) or for memory, where it adds `source` and freshness. So a remembered context can be
    checked read for read against a fresh fetch.
  - **Identity:** the virtual graph's labels, types and keys, with `source` on every node. A node key
    is (source, key) per label.
  - **Provenance:** on every node and relationship, `fetched_at`, `holds_until`, `fetched_by` and
    `fetched_with` (the read's Cypher). Every node links `FROM` a stub of its layer Table, and the
    stub links to stubs of the Columns kept. A stub holds an id that survives a rebuild, and a name.
  - **Freshness from usage:** a fact holds for its table's write cadence in the log. A frozen table's
    facts hold for good. `recall` reads memory while the context holds, and fetches again once it
    doesn't, or once the template changed. A refetch removes the relationships a read no longer
    returns; nodes stay, and a stale one is never read as fresh.
  - **Entitlements** (`--as <principal>`): a remembered row has left the warehouse's enforcement, so memory
    keeps it:
    - **The fetch is theirs.** The template is the virtual graph's model as the gateway restricts it for
      them, and every read is signed for them. BigQuery applies their tables, columns and rows.
    - **A fact that depends on who reads it** is a node of a table with a row access policy, or a
      relationship whose table or either end has one. It carries a mark per principal who fetched it
      (`seen_until:<principal>`), and a read of memory needs the reader's own mark. A refetch removes
      only the reader's mark from what it no longer returns; a relationship no one has a mark on goes.
      One node per row stays one node, so identity is still (source, key).
    - **Any other fact** is the same whoever reads it, and is shared.
    - **A context is recorded per principal** on its anchor. A recall reads memory only for the
      principal's own context, with their template as it is now: a table or column they lost changes it,
      so it is fetched again.
  - **Reads and writes are two steps from Python,** not one composite statement. The second hop is
    keyed on the first's results (a correlated subquery into the virtual graph is Virtual Graph bug
    2), and each read is signed on its own.

## Known limits

- The example log uses about 150 distinct column-level join predicates and no SELECT has more than 3
  joins; a real log has a long tail of one-off joins and 6 to 10-join queries. Join recovery scores
  flatter qlsc there.
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

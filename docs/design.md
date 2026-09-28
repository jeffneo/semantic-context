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
| `llm.query_model` | claude-sonnet-5 | Writing SQL needs a stronger model than naming | Given the answer key's own tables, Haiku 4.5 answered 1 of 10 gold questions, Sonnet 5 answered 4 |
| `navigate.anchors` | question | `parts` breaks the question into measures, groupings, filters and entities, and navigates from each; in a quick test it was about even (gold 7 of 10 both, a log sample 23 of 30 against 22), so the single embedding stays the default | see the accuracy plan, 2026-09-27 |
| `navigate.computations`, `computation_min_similarity` | 0, 0.8 | As first built, the closest Computations misled more than they helped: a close look-alike displaced what a question needed. With a similarity floor, equivalents merged and parameters left out of definitions, they were a wash on the full set: a close definition still gets over-applied. Off | all 176 log questions: 129 without, 130 with 5 definitions (4 gained, 3 lost); gold 7 either way |
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
- **Models:** Claude Haiku 4.5 for naming and SQL, no extended thinking; Azure OpenAI
  `text-embedding-3-large` at 512 dimensions. One line each in the config.
- **Warehouses:** one connector per warehouse (`src/qlsc/warehouse/`), chosen by `warehouse.type`. The
  log record's field names follow BigQuery's JOBS view; other connectors map onto them. The parser
  resolves BigQuery SQL only so far (`parser/qlsc_parse/catalog.py` DIALECTS); a second dialect is its
  own piece of work.
- **Designed-vs-used diff:** built (`qlsc align`), with every embedding link proposed, not asserted.

## Known limits

- The example log uses about 150 distinct column-level join predicates and no SELECT has more than 3
  joins; a real log has a long tail of one-off joins and 6 to 10-join queries. Join recovery scores
  flatter qlsc there.
- Navigation depends on which of several equally good level-1 groupings Leiden settles on. Over 11
  seeds ([results/seeds.md](../examples/fennmoor-bank/results/seeds.md)), the grouping's agreement with the
  spec barely moves (NMI vs subjects 0.863 ± 0.002) but cohort recall ranges 50% to 68% (mean 59%, sd
  7), with 13 or 14 of 14 questions hitting an expected table. The configured seed's 54% is one draw;
  compare navigation changes over seeds, not one run.

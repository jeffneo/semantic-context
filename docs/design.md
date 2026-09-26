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
   groups hold, ranked round robin. The joins and existing queries that connect them go to the LLM,
   which writes one query; the warehouse dry-runs it.
5. **Align.** Catalog bindings are exact; embedding matches are `status: 'proposed'`. The diff lists
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

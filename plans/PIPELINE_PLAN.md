# Pipeline plan: query log → semantic topology

Status: reviewed 2026-09-24 (decisions recorded in §5). M1 design in [M1_PARSER.md](M1_PARSER.md).

Terminology: a **Variable** is one real-world thing measured or identified by one or more
physical columns (the thing two joined columns share). Its `role` comes from use:
`identifier`, `measure`, `category` or `time`. "Concept" is reserved for higher levels of
the hierarchy, to be named when we get there.

## 0. Principle

**Usage is the source of truth.** The pipeline infers the warehouse's topology — what each
column means, which columns are the same thing, how tables connect, which parts are alive —
from what the business actually executes. A designed model (an ERD, declared FK constraints,
catalog descriptions, our own spec) is one author's opinion and is never an input.

Two refinements, both still inside that principle:

1. **Count authors, not executions.** A Looker explore join that runs 8,000 times is one
   LookML author's decision replayed by 166 consumers. A dbt model join is one engineer's
   decision replayed nightly. Evidence strength is *independent convergence*: how many
   distinct authors/processes arrived at the same join. Executions measure importance, not
   correctness.
2. **Usage tells you how the business operates, not whether it is right.** A join can be
   heavily used and wrong (F03, F13). The pipeline never prunes on "correctness"; it keeps
   every observed edge with a confidence, and the confidence comes from *contradictions
   between usages* (a minority join that conflicts with how production processes key the same
   columns), not from a designed model.

### Admissible inputs

| Input | Admissible? | Why |
|---|---|---|
| `INFORMATION_SCHEMA.JOBS` (query text, principals, refs, bytes, errors, timing) | **Yes — primary** | Executed usage |
| `INFORMATION_SCHEMA.VIEWS.view_definition` | **Yes** | Executed code. Needed because `referenced_tables` hides views: a view's joins are invisible in the log unless the view was (re)created in-window |
| `INFORMATION_SCHEMA.COLUMNS` / `TABLES` (names, types, partitioning) | **Yes — for parsing only** | Resolves aliases/`*`/CTEs and gives types for join plausibility. Asserts no relationships |
| Declared PK/FK constraints, column descriptions, policy-tag docs, ERDs | **No** (optional diff only) | Designed opinion. Could be shown as "designed vs. used" |
| `TABLE_STORAGE` row counts, data profiling | **No** | Every deployed table is empty, so these would be misleading here |
| `specs/`, `build/`, `jobs_truth`, answer keys | **Never** | Grading only |

Air gap: pipeline code lives in `pipeline/` and reads only from BigQuery (`fnb_query_log.jobs`
and the `fnb_*` INFORMATION_SCHEMA views). It must not import or open anything under `specs/`.
The only thing that reads both is `specs/tools/score.py`.

One known artifice: the log names logical projects (`fennmoor-raw.core_banking_cdc.X`), while
the catalog lives at `jeffdavis-bq-testproj.fnb_core_banking_cdc.X`. The pipeline gets a
one-line alias map in config. Real multi-project estates need the same thing.

## 1. What the log contains (measured 2026-09-24)

| | Jobs |
|---|---|
| Total jobs | 315,924 |
| LOAD | 5,781 |
| QUERY | 310,143 (1,843 failed) |
| — SELECT (reads) | 206,655 (52,684 cache hits) |
| — MERGE / CTAS / CREATE_VIEW / INSERT / DELETE | 90,508 / 4,334 / 8,460 / 93 / 93 |
| Queries with a table-to-table JOIN | 36,361 (11.7%) |
| — of which SELECTs | 25,857 (12.5% of SELECTs) |
| Distinct SQL strings | 121,187 (all parse with sqlglot) |

Roughly half of the SELECTs are machine chatter with almost no distinct text: Looker
datagroup triggers (60,480 jobs, 4 texts), dbt source freshness (32,400 / 90), Hightouch
syncs (8,640 / 4), elementary-dq monitors (6,930 / 77).

Joins, by workload (successful jobs):

| Workload | Jobs | With JOIN | Distinct SQL |
|---|---|---|---|
| Human ad-hoc SELECT | 49,519 | 14,799 (30%) | 14,862 |
| Looker explore queries | 21,442 | 8,234 (38%) | 21,442 |
| dbt tests (relationship tests) | 22,860 | 2,340 | 254 |
| dbt builds (MERGE + CTAS) | 11,681 | 10,153 | 61 |
| Looker PDT builds | 585 | 135 | 7 |
| Sandbox CTAS | 149 | 109 | 21 |
| Legacy DAG INSERT | 93 | 90 | 93 |
| Tableau, Vertex, Hightouch, monitors, Fivetran | ~200k | ~0 | — |

**Weakness of the test log:** it uses only about 150 distinct column-level join predicates
(an upper bound, with CTE names not yet resolved to base tables), and no SELECT has more
than 3 joins. A real log has a long tail of one-off joins and 6–10-join queries. The
pipeline can be built on this log, but join-recovery scores will flatter it. Widening the
human templates is a separate, cheap task (D5).

## 2. Stages

```
BigQuery ──► 1 extract ──► 2 fingerprint+parse ──► 3 actor model ──► 4 evidence graph (Neo4j)
                                                                          │
     8 score (air-gapped) ◄── 7 answer questions ◄── 6 name/describe ◄── 5 infer
```

### Stage 1 — Extract and normalize
- Pull `fnb_query_log.jobs` once into a local Parquet cache: 301 MiB, about $0.002. Iterate locally.
- Pull catalog columns/types/partitioning and view definitions for the `fnb_*` datasets.
- Map to the warehouse-neutral record from IMPROVEMENTS.md §1, so a Snowflake adapter is a
  config change later.
- Keep failed jobs as evidence. An access-denied error marks a restricted dataset (F08), and
  a typo followed by a fix is a correction pair.

### Stage 2 — Fingerprint and parse
- Fingerprint each query to a **shape**: sqlglot AST with literals replaced, hashed.
  Measured: 121,187 texts collapse to 2,365 shapes. Parse each shape once (see M1_PARSER.md).
- **Keep the literals first.** Build a per-column histogram of filter literals over time;
  new values appearing mid-window are the F17 signal.
- Run `qualify()` against the catalog: resolve aliases, CTE scopes and `*`, expand views from
  their definitions (and tag evidence that comes from views as view-derived).
- Per shape, emit:
  - column reads by role: `project`, `filter`, `group`, `join`, `aggregate(fn)`, `order`;
  - join predicates, `col = col`, recording wrapper functions (`CAST`, `LPAD`, `LOWER`,
    `SHA256`). Wrappers are evidence: they show format translation between id spaces;
  - writes and column-level lineage for MERGE/INSERT/CTAS/views: passthrough, rename,
    transform(fn), aggregate(fn);
  - partition/shard predicates: whether a `_TABLE_SUFFIX` / partition-column filter exists,
    and where (before or after a GROUP BY — F22);
  - `SELECT *` + `LIMIT` markers.
- Anything unresolved becomes `:Unresolved`, never a `Table`. Resolution rate is a health
  metric reported every run.

### Stage 3 — Actor model
Classify each principal by **behavior**, with naming only as a hint:
- periodicity: cron-like inter-arrival times;
- shape entropy: few shapes repeated vs. many unique ones;
- write patterns: MERGE into many tables means ingestion or ELT;
- breadth: one shape family touching nearly every table means a monitor (F19).

Classes: `ingestion`, `transformation`, `bi_service`, `bi_consumer`, `reverse_etl`,
`monitor`, `ml`, `human`. Looker end users come from the Looker context comment in the
query text (user_id, explore); they are consumers of LookML authorship.

Two things fall out of this:
- An **authorship key** per shape: human email, dbt model, LookML explore, and so on. This
  feeds independent-convergence weighting.
- **Monitors are excluded** from co-usage and liveness calculations. Their traffic stays in
  the graph, labelled.

Humans are grouped into inferred teams by the tables they co-access. We don't have an org
chart, and don't need one.

### Stage 4 — Evidence graph (Neo4j database `semanticlayer`)
Nodes:
- `Project`, `Dataset`, `Table`, `View`, `Column`, `Unresolved`
- `Principal {class}`, `Author` (a dbt model, a LookML explore, or a human), `Team` (inferred)
- `QueryShape {fingerprint, sample_sql, jobs (queries per shape), bytes_total, first_seen, last_seen, weekly[]}`
- `JoinKey`: one node per normalized predicate, so `a.x = b.y` across 40 shapes is one object
- `Literal {value}`, filter values per column
- `Variable {role}`, created in Stage 5; `(Column)-[:IS]->(Variable)`

Relationships:
- `(Principal)-[:RAN {jobs, cache_hits, bytes, first, last, weekly[]}]->(QueryShape)`
- `(Author)-[:AUTHORED]->(QueryShape)`
- `(QueryShape)-[:READS {role, fn}]->(Column)`
- `(QueryShape)-[:WRITES]->(Table)`
- `(QueryShape)-[:USES_JOIN]->(JoinKey)` and `(JoinKey)-[:ON {wrapper}]->(Column)` ×2
- `(Column)-[:FLOWS {kind: passthrough|rename|transform|aggregate, fn}]->(Column)`
- `(Table)-[:DERIVED_FROM]->(Table)`; `(View)-[:DEFINED_OVER]->(Table)`
- `(Column)-[:FILTERED_BY {first, last, jobs}]->(Literal)`

Individual jobs are not nodes. Shapes carry the aggregates plus up to 5 sample job ids each.
No Job nodes (D3).

### Stage 5 — Inference (the semantic layer)

**5a. Lineage and layers.** Build table and column lineage from the write statements and
view definitions. Assign each table a layer (`raw`, `staging`, `modeled`, `bi`, `sandbox`,
`legacy`) from the class of its writer and its depth in the lineage, not from dataset
names. Near-identical CTAS chains become copy sprawl (F14).

**5b. Variables: identity by usage.** Two columns belong to the same variable if the business
treats them as interchangeable: it joins them, or passes one through into the other.
- Edge weights:
  - `JoinKey`: weighted by distinct authors, with a bonus when a production author uses it;
  - `FLOWS passthrough/rename`: strong;
  - `transform`: related, but a *different* variable, e.g. `SHA256(tax_id)` → `ssn_hash`;
  - name similarity and co-projection: weak priors that can break ties but never merge
    anything on their own.
- **Hub discounting:** an IDF-style penalty by degree (F15). Weighted Leiden in GDS
  replaces WCC.
- **Homonym split (F03, F04):** when columns that share a name fall into sub-groups that
  production processes never cross, and only low-author ad-hoc joins bridge them, keep them
  as separate variables. Mark the bridging joins as `suspect`.
- **Role per variable**, inferred from how it is used:
  - `key`: joined on;
  - `measure`: under `SUM`/`AVG`;
  - `dimension`: grouped or filtered;
  - `time`: range-filtered or partition column.
- An **identifier variable is an id space.** A table that joins two or more id spaces is a
  crosswalk (F01).
- **Unit hints:** read from names (`_cents`, `_usd`, `_bps`) and from consumer behavior. If
  consumers habitually write `/100` over a column, that column is cents. A lineage path that
  changes the unit without the math flags F12.

**5c. Join confidence.** For each `JoinKey`, compute:
- authors;
- production vs. ad-hoc share;
- type compatibility;
- id-space consistency: does it join two variables that other usage keeps apart? (F13: GA4
  `user_id` is keyed to `online_user` by dbt, and never to `cif` by anyone except one
  sandbox CTAS);
- wrapper translation;
- trend.

The output is a confidence score plus a reason string. Nothing is deleted.

**5d. Table topology and subjects.** Build a bipartite projection of tables and non-hub
variables, then run weighted Leiden to get subject areas. Compute paths between subjects
over high-confidence `JoinKey`s; these are the "how do I get from calls to closures" paths.

**5e. Lifecycle and cost** (pure log statistics, excluding monitors):
- dead tables (F06) and write-only tables with their write cost (F07);
- a writer that stopped while readers continue (F11), and a live legacy chain running
  parallel to a newer table (F05);
- shapes ranked by bytes, with the missing filter named (F09, F20);
- health-check cost (F21);
- bytes growing with history rather than with the increment (F22);
- literal drift (F17).

**Negative controls:** F16 (a column that went null) needs profiling, and F18 needs domain
knowledge. The correct output for both is "not determinable from usage". A pipeline that
claims either is hallucinating, and the scorer counts that as a failure.

### Stage 6 — Naming and description (LLM)
Only now does an LLM see anything, and only to *name* structure the graph already has. It
never invents structure.
- Input per variable or subject:
  - member columns and their tables;
  - usage roles;
  - top literals;
  - two or three sample SQL fragments;
  - neighboring variables;
  - an abbreviation glossary mined from the corpus (for example, `CC_*` tables co-queried
    with call-volume tables means contact center).
- Structured output (`name`, `description`, `confidence`, `evidence[]`). Validation rejects
  boilerplate, bounds length, and requires every referenced column to exist.
- Embeddings: name and description go into separate indexes, with asymmetric task types,
  mean-centered, and recall@k measured on a labelled set.

### Stage 7 — Answer the questions (Q01–Q14)
Question → vector retrieval over variables and subjects → graph traversal for the
highest-confidence join path → generated SQL plus warnings. Examples of warnings:
- Q13: `CC` is ambiguous;
- Q02: two churn models, and which one production uses;
- Q12: PII, and whether consent was checked;
- Q03: route through the `online_user` bridge, not a direct join.

Each generated SQL statement is dry-run against the deployed (empty) tables. That's free,
and it proves the SQL is valid.

### Stage 8 — Scoring (`specs/tools/score.py`, the only code that reads the answer key)
Scoring follows the same principle as §0: **the key is usage truth, not the spec's
design.** Joins are scored against the predicates the simulated processes actually executed
in the window, rebuilt from `jobs_truth` template ids. They are not scored against
`joins.json`, which holds only the 82 dbt model joins.

| Metric | Measure |
|---|---|
| Parse health | % column references resolved; `:Unresolved` count |
| Join recovery | Precision and recall of `JoinKey` vs. executed predicates; plus trap joins flagged |
| Lineage | Precision and recall of column `FLOWS` vs. executed write statements |
| Variables | Pairwise precision/recall and ARI of column→variable (scored against the spec's `concept` tags), over **columns that appear in the log** only |
| Subjects | NMI of table clusters vs. `table.subject` |
| Findings | Pass, partial or fail per F01–F22 with an automated check; F16 and F18 pass only if the pipeline abstains |
| Questions | Per Q: right tables, right join path, right warnings, SQL dry-runs clean |

## 3. Milestones

| # | Build | Scored on |
|---|---|---|
| M1 | Extract, fingerprint, parse, evidence graph in Neo4j | Parse health, join recovery, lineage |
| M2 | Actor model plus lifecycle/cost detectors | F05–F07, F09, F11, F17, F19–F22 |
| M3 | Variables, join confidence, hub identification, identity | F01–F04, F10, F12, F13, F15 (hubs), variable ARI; F16 as a negative control |
| M4 | Layers, subjects (hubs link, D7), copy chains, PII lineage | F05, F08, F14, F15 (subjects), subject NMI |
| M5 | LLM naming, embeddings, retrieval eval | Description validation, recall@k, F04 |
| M6 | Question answering; NES/Bloom views | Q01–Q14; F18 as a negative control |

Every milestone ends with a score report, so each gain can be attributed to a specific step.

## 4. Costs
- BigQuery: one log pull (~$0.002), INFORMATION_SCHEMA reads (10 MiB minimum each), and
  free dry runs. Effectively $0.
- LLM: roughly 500–1,500 naming calls plus embeddings. A few dollars per full run; cache by
  input hash.

## 5. Decisions (2026-09-24)

- **D1 — Inputs:** as in §0. View definitions and catalog column types are admissible.
  Business behavior grounds everything. A manually designed catalog or OWL ontology is
  relevant later as an *enhancement* layered on the usage graph, never as its foundation.
- **D2 — Neo4j target:** a new database, `semanticlayer`. This was changed on 2026-09-24 from
  `querylog`, which keeps the old graph.
- **D3 — Granularity:** `QueryShape` nodes only, with `jobs` (queries per shape) as a property.
  No Job nodes.
- **D4 — Models:** Claude Haiku 5, no extended thinking, for naming. Azure OpenAI
  `text-embedding-3-large` at 512 dimensions for embeddings. Keys are in `.env`.
- **D5 — Widen the human join tail:** after M1.
- **D6 — Designed-vs.-used diff:** deferred. Revisit together with the D1 catalog/ontology
  enhancement.

- **D7 — Hub keys (M3):** customer, account, product and branch are first-class variables and
  are never discounted. In subject clustering they link subjects rather than define them. See
  [M3_VARIABLES.md](M3_VARIABLES.md).
- **D9 — Bottom layer (2026-09-24):** the graph built directly from the log and catalog is seven labels,
  in the Neo4j database `bigquery`: Project, Dataset, Table, Column, Principal, QueryShape, JoinKey. Literal
  values live on `FILTERS` (values, value_jobs, value_first_seen, value_last_seen); unresolved names are a
  `QueryShape.unresolved` list. Everything above it (actors, variables, subjects, findings, naming) is to be
  rebuilt on this layer; the M1-M6 build stays in `semanticlayer` for reference.
- **D8 — Customer identity (M3):** one Entity with several identifier variables (CIF,
  customer_key, OLB login, GA4 user, Salesforce contact...), linked by the crosswalks the
  business joins through.

## 6. Scope of statements used for graph construction

The graph is built from **consumption**: the read side of every statement, not only
`SELECT` statements. A `MERGE`/CTAS/view body is a read, by a production process, and its
target is where the consumed result lands. Measured on the current log (successful jobs,
qualified with sqlglot):

- Distinct base-table join predicates: 56 in SELECTs and 65 in write statements. **56 of the
  65 write predicates never appear in any SELECT.** A SELECT-only graph would lose most
  production join evidence, including every dbt model join.
- Renames (`CIF_NO` → `cif_number`) exist only in view and model definitions. Nobody joins a
  raw column to its staging rename, so without write statements the raw and modeled layers
  would be disconnected islands.
- Identifier variables come from joins. Measures and categories are almost never joined;
  their identity evidence (a passthrough of `amount` from staging to mart) exists only in
  write statements.

Excluded from structure (kept only as table liveness: last written, write cost):
ingestion `MERGE`s (Fivetran), `LOAD` jobs and schema-only DDL, which consume nothing in the
warehouse. Failed queries never create structure; they are kept as error evidence only.

# Fennmoor Bank: a worked example

Fennmoor Bank is a fictional US regional retail bank with a BigQuery estate. It has 324 tables across 43
datasets in three projects, dbt and Looker models, legacy and sandbox mess, and planted traps. A
simulator produces a realistic 90-day `INFORMATION_SCHEMA.JOBS` log (315,729 jobs) from its spec. qlsc
reads only that log and BigQuery's catalog, and this folder's evaluations grade what it builds against
the spec.

This tutorial goes from an empty BigQuery project to a question answered from the semantic layer. Run
every command from the repository root.

| Path | What |
|---|---|
| `estate.yaml` | qlsc's config for this estate: the BigQuery connector, name rules, the Neo4j database, the designed models |
| `spec/` | The answer key: every table and column, what it means, and what is wrong with it on purpose ([spec/README.md](spec/README.md)) |
| `generate/` | Builds the estate from the spec, deploys it empty to BigQuery, simulates the log, writes the synthetic catalog |
| `designed/` | Designed models to align: a catalog export and a small bank ontology ([designed/README.md](designed/README.md)) |
| `eval/` | Grades what qlsc built against the spec; writes `results/` |
| `results/` | The latest scores, in git |
| `demo.cypher` | Queries that draw each layer in Neo4j Browser or Explore |
| `build/`, `work/` | Generated (not in git): the spec's build and the log; qlsc's extracts, reports and caches |

## 1. Set up

Follow the root [README](../../README.md#use-it) for Neo4j, the parse service and `.env`. Point `.env`
at this estate:

```
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml
QLSC_WORK=./examples/fennmoor-bank/work
```

Create the database the config names, once, in Neo4j Browser (`CREATE DATABASE bigquery`). For
BigQuery, set up a project and a gcloud configuration as in [gcp-setup.md](gcp-setup.md), and put the
project in `estate.yaml` (`warehouse.project`). Everything BigQuery does here is free: the tables are
empty, the models are validated by dry run, and the log is pulled once, aggregated.

## 2. Build the estate and its query log

```bash
uv run examples/fennmoor-bank/generate/build.py                          # expand and validate the spec -> build/
uv run examples/fennmoor-bank/generate/deploy.py --project <project>     # create the estate empty, dry-run every model
uv run examples/fennmoor-bank/generate/templates.py --project <project>  # every query template, each dry-run
uv run examples/fennmoor-bank/generate/simulate.py --project <project> --validate 400 --load
uv run examples/fennmoor-bank/generate/make_catalog.py                   # the synthetic catalog -> designed/catalog.json
```

The simulator writes the log and its per-job truth to `build/log/` and loads the log (not the truth)
into `fnb_query_log.jobs`. Everything is seeded: the same spec gives the same log, byte for byte.

## 3. Build the semantic layer

```bash
uv run qlsc extract     # aggregate the log inside BigQuery, snapshot the catalog -> work/
uv run qlsc build       # about a minute with the caches warm
```

What `build` prints, stage by stage:

- **parse**: 121,093 distinct query texts (and the catalog's view definitions) fingerprinted into 2,387
  shapes, one per distinct query with its literals taken out; every successful shape resolved
  (`work/PARSE_HEALTH.md`, with a cross-check against BigQuery's own `referenced_tables`).
- **load**: the bottom layer, about 7,100 nodes and 21,000 relationships.
- **variables**: join confidence for all 156 join keys (5 suspect: the planted wrong joins), then 50
  variables over 177 columns; the other 3,948 columns are `:Unjoined`.
- **cluster**: 109 level-1 groups, median stability 0.95.
- **hierarchy**: 109 → 16 → 5.
- **align**: 79 glossary terms and 58 ontology classes; the catalog's term agrees with the embedding
  match for 24 of 30 bound variables, and the diff (`work/ALIGNMENT.md`) surfaces all three planted wrong
  bindings.

## 4. Look at it

Open Neo4j Browser on the `bigquery` database and paste queries from [demo.cypher](demo.cypher). Each
returns a graph, and its size is noted. A good path through it:

| | Shows |
|---|---|
| 1.1, 1.3 | The estate, and where one table's data comes from |
| 2.2, 2.3 | The keys the warehouse joins on, and the join predicates behind one variable |
| 2.5 | The joins kept out of the variables, and why (`k.confidence_reason`) |
| 3.2, 3.3 | The top of the semantic layer, then one area top to bottom |
| 3.6 | From meaning down to data: one group, its tables and the queries that read them |
| 4.1, 4.2, 4.5 | The ontology as imported, the semantic layer read through it, and the catalog contradicting itself |

## 5. Ask it

```bash
uv run qlsc ask "How many customers use the mobile app each week?"
uv run qlsc ask "Which contact centers see the most account closures, and what do they cost to run?"
uv run qlsc ask --no-sql "Loan delinquency rate by product and branch"
```

Each answer shows the walk: the closest Semantic nodes, the level-1 groups under them, the cohort of
tables, the joins and existing queries that connect them, and one query written from that cohort and
dry-run in BigQuery.

With data in the tables (`generate/fill.py`, [the fill plan](../../plans/2026-09-26-fill-the-estate.md)),
the walk goes on to the answer. There are two routes: SQL in BigQuery, or Cypher over the virtual
graph (`qlsc virtualize`, then `docker compose --profile vg up -d neo4j-vg`).

```bash
uv run qlsc ask --run "Account closures by reason, deposits versus cards."
uv run qlsc ask --cypher --run "Card spend by merchant category and customer segment, last quarter."
```

The Cypher route prints the SQL Virtual Graph sends to BigQuery. On the card-spend question it returns
45 rows (segment by merchant category, April to June 2026) that match a hand-written SQL query to the
cent.

## 6. Grade it

```bash
uv run examples/fennmoor-bank/eval/bottom_layer.py   # parse health, join recovery, lineage
uv run examples/fennmoor-bank/eval/navigation.py     # the 14 gold questions: tables reached and in the cohort
uv run examples/fennmoor-bank/eval/robustness.py     # noise injection and parameter sweeps
uv run examples/fennmoor-bank/eval/seeds.py          # the layer and navigation over 10 Leiden seeds
```

`eval/fingerprint.py` prints a fingerprint of the graph (counts, and hashes of every layer's ids and
names); diff two of them around a refactor to prove it changed nothing.

| | Latest |
|---|---|
| [Bottom layer](results/bottom_layer.md) | joins: recall 100% (123 of 123), precision 79% (the 33 extras are joins through CTEs and subqueries the reference extractor cannot see); lineage 100% / 100% |
| [Navigation](results/navigation.md) | 13 of 14 questions hit an expected table; expected-table recall 54% in the 8-table cohort, 72% reached under the opened groups |
| [Seeds](results/seeds.md) | over 11 Leiden seeds: recall 59% ± 7 (50% to 68%), 13 or 14 of 14 hit; NMI vs the spec's subjects 0.863 ± 0.002 |
| [Robustness](results/robustness.md) | random noise at 100% of the real statements: ARI 0.87 vs clean; level-1 gamma 3 to 8 and level-2 k 3 to 8 all give the same quality |

## Adapting it

For another organization, copy `estate.yaml`: set `business` (how the prompts refer to it), the
`warehouse` connector and its settings, the name rules, and the designed models (for an insurer, its
catalog export and ACORD or its enterprise data model). `spec/`, `generate/` and `eval/` are this
example's alone; a real estate has no answer key.

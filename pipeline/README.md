# pipeline/

The query-log → semantic-topology pipeline. Plan: [plans/PIPELINE_PLAN.md](../plans/PIPELINE_PLAN.md);
M1 design: [plans/M1_PARSER.md](../plans/M1_PARSER.md); M2: [plans/M2_ACTORS_LIFECYCLE.md](../plans/M2_ACTORS_LIFECYCLE.md); M3: [plans/M3_VARIABLES.md](../plans/M3_VARIABLES.md); M4: [plans/M4_TOPOLOGY.md](../plans/M4_TOPOLOGY.md); M5: [plans/M5_SEMANTICS.md](../plans/M5_SEMANTICS.md); M6: [plans/M6_QUESTIONS.md](../plans/M6_QUESTIONS.md).

Reads only BigQuery (the log table and INFORMATION_SCHEMA) — never `specs/`. Every LLM prompt is a file in
[`prompts/`](../prompts/).

| Path | What |
|---|---|
| `estate.yaml` | Where to read, and name-canonicalization rules. No meaning, no relationships. |
| `extract.py` | T0: aggregates the log inside BigQuery; writes the catalog snapshot |
| `parser/` | `qlsc-parse`: library, HTTP service, batch CLI, golden tests, Dockerfile |
| `parse_log.py` | T1 + T2 through the service; writes shapes, texts, health report, review sample |
| `load_graph.py` | Stage 4: the bottom layer into Neo4j `bigquery`: Project, Dataset, Table, Column, Principal, QueryShape, JoinKey (`--reset` reloads from scratch) |
| `actors.py` | Stage 3: principal classes, shape purposes, authors, BI end users, consumption, teams (GDS) |
| `detect.py` | Stage 5e: lifecycle and cost findings -> `(:Finding)` nodes + `work/FINDINGS.md` |
| `variables.py` | Stage 5a (new model): GDS WCC over columns joined by a JoinKey -> `(:Variable)`, `(:Column)-[:IS]->(:Variable)`, LLM-named; other columns `:Unjoined` |
| `cluster.py` | Stage 5b (new model): Leiden (gamma 4) over Variable/Unjoined units read by the same queries or linked by lineage (ingestion plumbing excluded) -> level-1 `(:Semantic)`, `-[:IN_SEMANTIC]->`, LLM-named; `Semantic.stability` from 10 reruns (new seeds, 80% resamples of the statements) |
| `hierarchy.py` | Stage 5c (new model): per level, embed each Semantic (512-d); building level L, score pairs by (1/L) usage + (1 - 1/L) text cosine; `K_SIM` to the k=5 best; Leiden with gamma 3/(L-1) -> next level; stops when a level would not shrink, has 3 or fewer nodes, or k would cover it; vector index `semantic_embedding` |
| `joins.py` | Join confidence on each JoinKey (production / corroborated / single / suspect / self, identity-preserving or not); `variables.py` builds only from trusted, identity-preserving joins |
| `navigate.py` | Demo: question -> embedding -> closest Semantic nodes -> level-1 groups beneath (plus the closest level-1 groups directly) -> the tables and columns they hold (ranked by use) -> the joins and queries in the log that connect them -> SQL written from that cohort, dry-run in BigQuery (`--no-sql` to skip) |
| `align.py` | Stage 6 (new model): the ontology imported with rdflib-neo4j (`Resource:Class`, `subClassOf`) and the catalog's glossary, both as `(:Concept)`; catalog bindings and proposed embedding links as `MEANS`; the designed-vs-used diff -> `work/ALIGNMENT.md` |
| `llm.py` | Shared: `prompt(name, **values)` loads `prompts/<name>.md`; cached, tool-forced Claude calls; batch naming with validation and retry; Azure embeddings |
| `legacy/` | The M3 `variables.py` (join confidence, identity, units), kept for reference while the stages are rebuilt |
| `topology.py` | Stages 5a/5d: layers, subjects (hubs link, D7), copy families, sensitive-data exposure -> `work/TOPOLOGY.md` |
| `semantics.py` | Stage 6: LLM names and descriptions (tables, variables, subjects), proposed domains, embeddings |
| `retrieve.py` | Question -> tables (vector indexes + usage prior), with the reason for each |
| `guide.py` | Stage 7a: table status (current / caution / avoid) with reasons, freshness, `USE_INSTEAD`, table-level `JOINS` -> `work/GUIDE.md` |
| `tools.py` | Stage 7b: the semantic layer as agent tools (search, describe, join path, example queries, sensitive data, dry run); plus the catalog-only baseline |
| `answer.py` | Stage 7c: question -> tables, joins, SQL, warnings (LLM agent over `tools.py`; `--baseline` for catalog only) |
| `views.py` | Stage 7d: Enterprise Studio perspective (`views/`) and `cypher/views.cypher`; every search phrase is tested |
| `run.sh` | Rebuild the graph from `work/` end to end and score (about 40 s) |
| `graphdb.py` | Shared Neo4j access |
| `health.py` | Parse-health report (incl. cross-check vs BigQuery `referenced_tables`) and review sample |
| `work/` | Outputs (gitignored) |

```bash
uv run pipeline/extract.py                       # T0 groups + catalog snapshot (~$0.01)
docker compose up -d parser                      # the parse service, reads work/catalog.json
uv run pipeline/parse_log.py --sample 0.05       # or without --sample for the full log
uv run pipeline/load_graph.py --reset             # bottom layer -> Neo4j bigquery
uv run pipeline/actors.py                        # actor model (M2)
uv run pipeline/detect.py                        # lifecycle and cost findings (M2)
uv run pipeline/variables.py                     # WCC variables from joins, named by Haiku (D9)
uv run pipeline/cluster.py --gamma 4             # Leiden semantic groups over co-reads, named by Haiku
uv run pipeline/hierarchy.py                     # the levels above (--k 5 --gamma 3)
uv run pipeline/topology.py                      # layers, subjects, copies, sensitive data (M4)
uv run pipeline/semantics.py                     # names, descriptions, embeddings (M5; cached)
uv run pipeline/guide.py                         # table status and alternatives (M6)
uv run pipeline/views.py                         # Enterprise Studio perspective (M6)
uv run pipeline/answer.py "Loan delinquency rate by product and branch."   # ask a question (M6)
uv run pipeline/navigate.py "How many customers use the mobile app each week?"   # question -> data cohort
pipeline/run.sh                                  # all of the above from work/, then score
uv run specs/tools/score.py                      # scorer (spec side; reads the answer key)
uv run specs/tools/score.py --only-m6            # just the 14 questions, 3 runs per mode
uv run --no-project --with 'sqlglot[c]==30.19.0' --with pytest pytest pipeline/parser/tests -q
```

**Status (2026-09-24, D9):** the bottom layer is the 7-label model in `bigquery`. The stages from
`actors.py` on still read the previous model (Literal, Unresolved, Author, ...) and are being rebuilt on it;
their M1-M6 output is in the `semanticlayer` database, and `run.sh` stops after the M1 score until then.

Stage order matters: `topology.py` rebuilds the Subject nodes, which drops the names, embeddings and
domain links `semantics.py` put on them. Rerun `semantics.py` after it (cached, so free); `run.sh` does.

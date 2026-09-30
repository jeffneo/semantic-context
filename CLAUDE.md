# CLAUDE.md

qlsc infers a semantic layer for a data warehouse from its query log, in Neo4j. `src/qlsc/` is the tool;
`examples/fennmoor-bank/` is a synthetic bank that exercises it, with an answer key. Read
[README.md](README.md) and [docs/design.md](docs/design.md) before changing anything that affects results.

## Principles

- **Usage is the ground truth.** The pipeline builds only from the query log and the catalog's physical
  facts. Designed models (catalogs, ontologies, ERDs, an example's spec) are aligned afterwards, never
  inputs.
- **The tool knows nothing about any example.** Nothing in `src/qlsc/` or `prompts/` names an estate, reads
  a spec, or assumes a warehouse; `tests/test_boundary.py` enforces it. An example may import the tool,
  never the other way round. Estate specifics go in the estate's config.
- **Warehouse code lives in a connector** (`src/qlsc/warehouse/`), nowhere else.
- **Every parameter lives in `src/qlsc/defaults.yaml`,** with why it has its value. No magic numbers in
  code, no settings that nothing reads (`tests/test_config.py`).
- **Builds are deterministic.** Seeded, single-threaded GDS; projections fed in sorted order
  (`Graph.project_pairs`); LLM and embedding calls cached by request. Keep it that way.

## How the user works

- Keep the graph model small and natural: few labels, each meaning something to a business reader. No
  plumbing or styling labels; put evidence on properties rather than new node types.
- A **Variable** is the real-world thing joined columns share; a **Semantic** is a business area;
  **Concept** is a designed-model term. Use these words.
- Every LLM prompt is a file in `prompts/`, loaded with `prompt(name, **values)`, listed in
  `prompts/README.md`. Never write prompt text in Python.
- Plans go in `plans/YYYY-MM-DD-topic.md` before larger work (see `plans/README.md`); durable decisions
  then move into `docs/design.md`.
- Ask before design decisions that change the model or the method; say plainly when a result got worse.

## Commands

```bash
uv sync
uv run qlsc --help                       # extract, build, one command per stage, ask
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc build        # ends with `qlsc requests`, the request bank
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc ask "question"   # the router's query; --run, --sql, --cypher, --memory, --as <principal>
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc computations   # then: qlsc okf (the OKF bundle, <work>/okf)
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc recall Customer cif_number=0001000025   # a context, kept in memory; remember fetches again (KEY... in one batch); --as <principal>
uv run pytest                            # needs Neo4j up for the demo-query tests
uv run ruff check . && uv run ruff format .
uv run --no-project --with 'sqlglot[c]==30.19.0' --with pytest pytest parser/tests -q
uv run examples/fennmoor-bank/eval/{bottom_layer,navigation,robustness,seeds}.py   # -> results/
uv run examples/fennmoor-bank/eval/answers.py         # the gold questions' reference answers, from the filled data
uv run examples/fennmoor-bank/eval/execution.py [param=value ...]  # ask's answers to the gold questions, by SQL, Cypher and the router (match.py's ruler)
uv run examples/fennmoor-bank/eval/log_questions.py write|run   # 176 questions written from the log's own queries
uv run examples/fennmoor-bank/eval/log_accuracy.py [param=value ...]  # ask's answers to them (about an hour, about $6 of LLM calls)
uv run examples/fennmoor-bank/eval/qdd.py <name> [--route=cypher] [param=value ...]   # a quick A/B of one setting: 40 questions, minutes; an experiment, in <work>/qdd/
uv run examples/fennmoor-bank/eval/graph_accuracy.py [param=value ...]  # ten graph-shaped questions, both routes
uv run examples/fennmoor-bank/eval/comparison/run.py prep|layer|agent|naive-schema|naive-agent|report   # qlsc against naive approaches, 186 questions, measured (~$25, 15 min); README beside it
uv run examples/fennmoor-bank/eval/entitlements.py [--controls-only]  # the gateway, with the warehouse as the oracle (about an hour)
uv run examples/fennmoor-bank/eval/memory.py            # remembered contexts against the virtual graph; freshness (minutes)
uv run examples/fennmoor-bank/eval/memory_entitlements.py   # memory as each principal, with BigQuery as the oracle (minutes)
uv run examples/fennmoor-bank/eval/converse.py          # the agent side: the example conversations recorded, then checked
uv run examples/fennmoor-bank/eval/distill.py           # skills from simulated experience: distill, approve, offer, retire (~10 min)
uv run examples/fennmoor-bank/eval/economics.py         # 50 questions, with and without memory: latency and bytes billed (~10 min)
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc distill   # then: qlsc skills [--approve ID --as PRINCIPAL]
QLSC_CONFIG=examples/fennmoor-bank/estate.yaml uv run qlsc converse examples/fennmoor-bank/conversations/marketing-1.yaml
uv run examples/fennmoor-bank/entitlements/setup.py [--apply]   # the test principals' grants, tags and row policies in BigQuery (as the owner)
uv run examples/fennmoor-bank/generate/fill.py --slice 2   # fill BigQuery with rows (plans/2026-09-26-fill-*.md)
```

Services: `docker compose up -d neo4j` (bolt 7690 per the example config). The parser (`parser/`,
`qlsc_parse`) runs in-process: `qlsc parse` pools it over `parse.workers` processes. Virtual Graph:
`vg-passthrough/build.sh`, then `docker compose --profile vg up -d --force-recreate neo4j-vg` (bolt 7692);
every Cypher query it runs must be signed (`entitle.signing`), or the pass-through refuses it.

## Changing code

- Match the surrounding style: module docstrings say what a stage does and why; Cypher sits as named
  constants in the module that uses it, with `$parameters`, never string-built values.
- A refactor must not change results. Before and after, run
  `uv run examples/fennmoor-bank/eval/fingerprint.py` around `qlsc build` and diff the two.
- A change that is meant to change results: rerun the example's evaluations, update `results/`, and
  update the numbers quoted in README.md, the example's README and docs/design.md.
- Navigation scores depend on the Leiden draw; compare changes over seeds (`eval/seeds.py`), not one run.
- `examples/*/work/` and `examples/*/build/` are generated and gitignored; the example's generators
  reproduce `build/` byte for byte.

## Safety

- Secrets are in `.env` (NEO4J_PASSWORD, NES_TOOLS_PASSWORD, ANTHROPIC_API_KEY, AZURE_OPENAI_*). Never print
  or commit them.
- BigQuery: always select the estate's named gcloud configuration (`CLOUDSDK_ACTIVE_CONFIG_NAME=` its
  `warehouse.gcloud_config`); never change the user's default gcloud configuration or project. Never
  delete anything in a GCP project without asking.
- License files (`*.license`) are referenced, never copied or committed.
- Enterprise Studio (localhost:8082) needs the user to sign in; don't enter passwords.

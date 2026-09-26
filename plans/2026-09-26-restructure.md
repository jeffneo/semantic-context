# Restructure: one tool, one worked example

Status: done (2026-09-26). The M1-M6 build is the history up to commit 80dd3e9.

## Why

The repository held two generations of the pipeline (the M1-M6 model and the seven-label rebuild) and
mixed the tool with the Fennmoor example. The rule "the pipeline never reads the spec" was kept by
discipline, not structure; parameters were scattered across CLI defaults and constants; helpers were
written several times; twenty standalone scripts each declared their own dependencies.

## What changed

- Retired the M1-M6 stages (actors, detect, topology, semantics, retrieve, guide, tools, answer, views),
  their prompts, Studio perspective and scores; `plans/M1-M6` and `IMPROVEMENTS.md`.
- `src/qlsc/`: a package with a `qlsc` command (`extract`, `build`, one command per stage, `ask`) in
  place of `run.sh` and per-script entry points; one `pyproject.toml`.
- Warehouse connectors (`src/qlsc/warehouse/`), chosen by `warehouse.type`; BigQuery is the first. The
  prompts take the organization and the warehouse from config.
- Every method parameter in `src/qlsc/defaults.yaml`; unused settings dropped (`llm.provider`,
  `embeddings.provider`, `qa`).
- Shared helpers defined once: `names.py` (canonical table names, now the parser's own rules),
  GDS projection and Leiden on `Graph`, `write_names`, one LLM client, one BigQuery client.
- `examples/fennmoor-bank/`: config, spec, generators, designed models, evaluations, results, demo
  queries, tutorial. Generated `build/` and `work/` are out of git.
- `tests/`: the tool/example boundary, prompts, config, the method's pure parts, the demo queries.
- Style: ruff (lint and format); nested closures lifted into named functions (joins, load); results
  computed before they are rendered (align, bottom-layer scoring).

## Found on the way

Leiden was seeded but not reproducible across rebuilds: GDS numbers nodes in the order rows arrive, and
that order changed after a reset. Projections are now fed sorted, and two rebuilds from scratch give
the same graph. The deterministic grouping is 109 → 16 → 5 (was one draw of 107 → 15 → 4); navigation
recall on the gold questions is 54% (was 65% on the earlier draw), with equal agreement with the spec.
A sweep over 11 seeds (`eval/seeds.py`) puts recall at 59% ± 7, range 50% to 68%: both earlier numbers
are draws from that range.

## How it was checked

- The restructured `qlsc build` produced a graph identical to the pre-restructure code (same ordering
  fix): every label and relationship count, and hashes of ids, names, levels, memberships, K_SIM,
  MEANS, READS, FILTERS and FLOWS. ALIGNMENT.md identical below its header.
- The bottom-layer scores and the navigation evaluation identical under old and new code.
- The generators reproduce `build/`, the log and the catalog export byte for byte.
- `qlsc extract` against BigQuery (into a scratch directory): the same catalog version
  (`cat-0d09e3192339`); the log groups identical once summed per text, principal and week (the old
  extract also split groups by BigQuery's query hash, which the simulated log varies for 4,635 texts
  and nothing downstream reads); principal profiles identical but for `daily_cv` in the 16th digit.
- Dry runs through the connector: a valid query and a planner error, both reported correctly.
- `uv run pytest`, the parser's golden tests, `ruff check`.

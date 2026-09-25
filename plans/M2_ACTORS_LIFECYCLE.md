# M2: actor model, lifecycle and cost findings

Status: complete, 2026-09-24. Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Stage 3 and Stage 5e).
Code: `pipeline/actors.py`, `pipeline/detect.py`, `pipeline/graphdb.py`. Scorer: `specs/tools/score.py` (M2 section).

```bash
uv run pipeline/actors.py          # Stage 3: classes, purposes, authors, end users, consumption, teams
uv run pipeline/detect.py          # Stage 5e: findings -> graph + work/FINDINGS.md
uv run specs/tools/score.py        # M1 + M2 scores -> specs/build/score/
```

## What was added to earlier stages

Each of these is a measured fact, not an inference:

- **Parser**
  - `family_id`: the structure of a query with every identifier and literal blanked. One
    monitor query stamped across 70 tables is one family.
  - `output`: the column count, whether the output is aggregate-only, whether it is grouped,
    and the root FROM table. A single row of aggregates is how health checks look.
- **Extract (T0).** A per-principal time profile, aggregated in BigQuery with one row per
  principal. It holds:
  - business-hours and weekend share, in the estate's time zone;
  - same-slot share: how much of the work recurs at the same hour:minute on most days;
  - day-to-day variation.
- **Extract (T0 bug fix).** Load jobs now group by destination table. Before, one arbitrary
  destination per (principal, week) was kept, which misdated every multi-table loader. For
  example, Vertex writes churn scores v2 and v3.
- **Loader**
  - `RAN.days` and `LOADED.days` (distinct active dates).
  - `Table.write_days`.
  - Weekly bytes per shape.

## Stage 3: the actor model (behavior first; names only as hints)

| Class | Decided by |
|---|---|
| `human` | user account |
| `ingestion` | only loads files, or 80% or more of its writes merge from per-run staging tables |
| `ml` | reads warehouse tables *and* loads results back (out and back) |
| `bi_service` | end-user ids in its query context (3 or more), or a service account keeping human hours (business hours at least 40%, weekend at most 25%) |
| `transformation` | writes from warehouse sources |
| `monitor` | 80% or more of its reads are single-row checks |
| `scheduled_reader` | reads on a schedule and writes nothing (covers reverse ETL: the log cannot see where it sends data) |

- **Shape purpose.** Each shape gets one of `adhoc`, `bi`, `extract`, `ml_read`, `build`,
  `ingest`, `probe`, `view_definition`, `metadata` or `failed`.
- **Consumption.** Defined as `adhoc`, `bi`, `extract`, `ml_read` and `build` reads, with
  views expanded to their sources. Probes are not consumption: tests, freshness checks, BI
  cache triggers and monitor checks. Neither are view definitions (a `CREATE VIEW` reads no
  data) or failed jobs.
- **Authors** (`:Author`). A dbt model (from its query comment), a BI model rooted at one
  table, the first person to run a shape, or a service. This is the input to M3's
  "count authors, not executions".
- **End users** (`:Consumer`). There are 166, recovered from Looker's query-context comment.
- **Teams.** People are grouped by what they consume: weighted Jaccard over
  `(:Principal)-[:CONSUMES]->(:Table)` (GDS node similarity), then Leiden. This was not
  tuned against the key.

## Stage 5e: findings

The graph now holds `(:Finding {kind, title, summary, cost_bytes, evidence})-[:ABOUT {role}]->(...)`.
Current counts:

| Kind | Found |
|---|---|
| `monitor` | 1 |
| `dead` | 64 (including a stale Looker PDT generation) |
| `write_only` | 29 |
| `straggler` | 2 |
| `superseded_live` | 1 |
| `unpruned_scan` | 19 |
| `star_limit` | 10 |
| `probe_cost` | 16 |
| `incremental_rescan` | 8 |
| `literal_drift` | 1 |

Rules that took more than one attempt:

- **Straggler.** A table written on a cadence (4 or more write days) that has gone quiet for
  longer than `max(7 days, 3 × its median interval)` while consumers keep reading. One-off
  sandbox CTAS tables and monthly refreshes are excluded. The rule also names the stopped
  upstream source and a likely successor (a table first written within 2 days of the stop,
  sharing its columns).
- **Superseded, still live.** Two pipeline-built tables with different writers, neither
  upstream of the other, that share 60% or more of their root source columns. Roots are
  traced through `FLOWS` and views. The candidate is the one with the smaller audience, and
  it is reported only if its downstream chain still reaches a consumer. A candidate already
  inside another candidate's chain is folded into it.
- **Unpruned scan.** A view is prunable only when the query filters a view column that
  passes straight through from the base partition column. Otherwise the view "cannot pass a
  pruning filter down". Reading all shards of a sharded table is always reported. Partitioned
  tables are reported by cost. The finding names the filter the query used instead.
- **Literal drift.** Applies to string columns with an established vocabulary. A value
  qualifies if it first appears more than 21 days into the window, with at least 10 jobs
  since, and is not a period label (`APR-26`, `2026-Q2`, `FY26`).

## Score (2026-09-24)

| | Result |
|---|---|
| Principal classes | **36 / 36** |
| Shape purposes | **1,100 / 1,100** (a person's `INFORMATION_SCHEMA` lookup labeled `metadata` counts as ad hoc) |
| Teams | ARI **0.73**, pairwise precision 61%, recall 100% |
| Unused tables vs. usage truth | **93/93** flagged are really unconsumed; **92/92** unconsumed are flagged |
| F05, F06, F07, F09, F11, F17, F19, F21, F22 | **pass** |
| F20 | partial: 2 of 3 (see below) |

The teams result comes from two merges: data science with customer analytics, and digital
product with marketing. In both cases the two groups consume the same tables.

## Issues in the spec and simulator found by M2 (not fixed; the pipeline follows the log)

- **F20.** The key says cx_ops's `SELECT * … LIMIT 1000` on `fct_calls` is among the
  costliest human queries. In the log it filters on the partition column and bills
  0.93 GiB across 137 jobs.
- **F06.** `card_account_hist_2019` and `consumer_attributes_2019_archive` are status `dead`
  in the spec, but the simulated file loader reloads them daily or monthly. The pipeline
  calls them write-only, which is still "unused". An archive table should not be reloaded.
- **Usage key.** The scorer's first usage key counted dbt's `CREATE VIEW` as consumption of
  the view's sources. It isn't: the view defines, it reads nothing. This is fixed in
  `score.py`.

## Beyond the key

These are true in the log but not planted:
- The churn PDT froze on 05-15 because its source stopped. Looker's datagroup trigger polls
  `MAX(score_date)` on v2, which stopped changing, so Looker has served six-week-old churn
  scores since.
- Six more incremental dbt models apply their date filter after the scan.
- A risk analyst's reconciliation sandbox hangs off the legacy balance chain.

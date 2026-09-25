# M1 design: the SQL parse service

Status: M1 complete 2026-09-24 (see §10-11). Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md).
Code: `pipeline/parser/` (library, service, tests), `pipeline/extract.py`, `pipeline/parse_log.py`, `pipeline/health.py`.

## 1. What was wrong with the old routine (`old/KnowledgeLayer.ipynb`, `extract_query_info`)

| Problem | Effect in the old graph |
|---|---|
| `parse_one(sql)` with no dialect | BigQuery syntax (backticked `project-with-dashes`, `QUALIFY`, `SAFE.`, `_TABLE_SUFFIX`) is parsed as generic SQL |
| Tables keyed by `.name` only | Project and dataset are dropped; same-named tables in different datasets merge |
| Every `Table` node counted as a table | CTE names and derived-table aliases became `Table` nodes |
| One alias map for the whole query | Scopes collide: `a` in a CTE and `a` in the outer query are treated as the same table |
| Unqualified columns dropped unless the query has exactly one table | Most columns in multi-table queries disappear |
| Join criteria stored as a string | No column pairs, so joins cannot become graph edges without re-parsing |
| Bare `except: return None` | Failures vanish without a count |
| One Cypher round trip per query, `MERGE` on the full SQL string | Load time grows with the log, not with the number of shapes |

All of these share one root cause: the routine walks the raw AST instead of resolving names
against a catalog. sqlglot can do that resolution (`qualify` plus scope traversal); the old
code never called it.

## 2. Measurements (this log, Apple Silicon, one core)

| Step | Unit | Pure-Python sqlglot 30.19 | Compiled (`sqlglot[c]`) |
|---|---|---|---|
| Tokenize | per distinct text | 0.19 ms | 0.05 ms |
| Parse | per distinct text | 0.82 ms | 0.35 ms |
| Parse + `qualify` (name resolution) | per shape | 7.4 ms | 4.7 ms |

Deduplication, measured:

- 310,143 query jobs;
- 121,187 distinct texts;
- 84,709 BigQuery-style shapes (literals and comments stripped);
- **2,365 canonical shapes** once volatile table names are normalized: Fivetran staging
  suffixes, Looker `LR_` PDT ids, date shards and anonymous result tables.

Resolution: 100% of texts parse. Of 4,000 shapes, 51 (1.3%) fail `qualify`. Most of those
are the simulator's injected typos (`cif_numbr`, `evnt_time`), which also failed in
BigQuery, so failing is correct. The rest are catalog gaps to close in M1:
- `INFORMATION_SCHEMA` queries;
- a GA4 wildcard column;
- one sandbox column.

**BigQuery already fingerprints every job, for free.** I checked with twelve zero-byte probe
queries. `query_info.query_hashes.normalized_literals` ignores:
- literals, including typed ones such as `DATE '…'`;
- whole array literals;
- comments;
- whitespace;
- keyword case.

It keeps the length of `IN (…)` lists. So the warehouse does the per-job deduplication
itself.

## 3. Recommendation: separate service, yes; Rust, no (not now)

Your architectural instinct is right. The parser should be a separate, stateless service
with a versioned contract, packaged to run as a compose service, a Cloud Run job or
function, or a Lambda. I would not write it in Rust, for three reasons.

1. **The scale lever is deduplication, not parser speed.** The per-job work is grouping by
   fingerprint, and that runs inside the warehouse, which is built for billions of rows. The
   parser only ever sees distinct shapes. On this log that is 131 jobs per shape, and the full
   resolution pass is about 11 CPU-seconds.
2. **Rust would speed up the wrong 7%.** Parsing is 0.35 ms of the 4.7 ms per shape; name
   resolution is the other 93%. The fast Rust parser (`sqlparser-rs`) gives an AST with no
   resolution: no CTE or alias scoping, no `*` expansion, no struct-versus-table
   disambiguation, no correlated subqueries, no `USING` coalescing, no wildcard tables. We
   would have to write the resolver ourselves, which is months of work. It is also exactly
   the part that broke v1.
3. **The contract makes the language swappable later.** If a hot spot ever shows up, port
   that tier alone. The likely candidate is the per-text literal pass, which is simple and
   well specified. For BigQuery-exact resolution, the stronger upgrade would be Google's own
   GoogleSQL (ZetaSQL) analyzer behind the same contract, not a hand-written Rust resolver.

The scale pitch is honest this way: aggregation happens in your warehouse; parsing is
embarrassingly parallel over distinct shapes; results are cached by shape, so a daily run
parses only the shapes that are new.

Illustrative arithmetic, not a measurement: a log of a billion jobs that reduces to 50M
distinct texts and 1M shapes needs about 1.5 CPU-hours for the per-text literal pass and
about 1.5 CPU-hours for resolution. Across 100 workers, that is a couple of minutes.

## 4. Architecture: three tiers, each sized to what it needs

```
BigQuery                      parse service (stateless, fan-out)                  loader
──────────                    ──────────────────────────────────                  ──────
JOBS ─► T0 SQL aggregate ──►  T1 fingerprint (per BQ hash, 0.35 ms) ─► T2 resolve  ──► Neo4j
        by BQ hash, text,        canonical shape id, literal list        (per shape,
        principal, week          per distinct text                        ~5 ms)
```

- **T0 — in-warehouse aggregation (SQL).** Group by
  `(normalized_literals hash, query text, principal, week)`, with counts, bytes, slot-ms,
  cache hits, errors, first and last seen, and `referenced_tables`. Billions of jobs become
  distinct texts with statistics, and job rows never leave the warehouse. Here that is one
  scan of a 301 MiB table (about $0.002).
- **T1 — fingerprint (service, cheap).** One parse per distinct text. It strips comments,
  replaces literals with slots, canonicalizes volatile identifiers, and hashes the result to
  a `shape_id`. The literal values, in slot order, are returned per text; this is what keeps
  F17 (literal drift) possible after deduplication. Slot order is stable because the
  fingerprint is taken over the AST: the same shape means the same tree and the same walk
  order.
- **T2 — resolve and extract (service, expensive).** Runs on one representative text per
  `shape_id`. It qualifies against the catalog and makes a single pass over the scopes to
  emit a parse record (§5). It must not call `sqlglot.lineage()` per column, because that
  re-qualifies the whole query for every column.
- **Loader.** Batched `UNWIND` writes of shapes, statistics and parse records into
  `semanticlayer`: one transaction per batch, keyed on `shape_id`, never on SQL text.

### Canonical identifiers (T1)

| Pattern | Canonical |
|---|---|
| `fivetran_staging.<table>_<12+ hex>` | `<table>_{hex}` |
| `LR_<15 alnum>_<name>` (Looker PDT) | `LR_{id}_<name>` |
| `<table>_YYYYMMDD`, `<table>_YYYYMM` (shards) | `<table>_*` (same as the wildcard table) |
| `_<40 hex>.anon…` (anonymous results) | `{anon}` |

These rules also decide **graph identity**. A sharded table or a rotating PDT is one `Table`
node, with the physical names kept as a property. The rules are configuration, not code:
each customer estate will need a few of its own.

## 5. Contract

The parse record, one per shape, NDJSON:

```json
{
  "shape_id": "sha256…", "parser": "qlsc-parse/0.1 sqlglot/30.19", "catalog": "cat-2026-09-24",
  "dialect": "bigquery", "statement_type": "MERGE", "status": "ok|partial|error",
  "tables":  [{"id": "fennmoor-dw.dw_core.fct_calls", "kind": "table|view|wildcard",
               "via_view": null}],
  "reads":   [{"table": "…", "column": "wrapup_code_name",
               "roles": ["filter", "group"], "agg": null, "scope": "cte:closures"}],
  "joins":   [{"left":  {"table": "…", "column": "cif_number", "wrap": []},
               "right": {"table": "…", "column": "bank_customer_ref", "wrap": ["LPAD"]},
               "type": "LEFT", "op": "=", "scope": "main"}],
  "filters": [{"table": "…", "column": "wrapup_code_name", "op": "IN",
               "slots": [4, 5], "partition": false}],
  "writes":  {"table": "…", "mode": "MERGE|CTAS|INSERT|VIEW",
              "columns": [{"target": "cif_number",
                           "from": [{"table": "…", "column": "CIF_NO"}],
                           "kind": "passthrough|rename|transform|aggregate", "fn": null}]},
  "scan":    {"select_star": false, "limit": null,
              "partition_filter": {"fennmoor-dw.dw_core.fct_calls": "pushed|after_agg|none"},
              "suffix_filter":    {}},
  "unresolved": [{"name": "cif_numbr", "kind": "column", "reason": "not in catalog"}]
}
```

`status: partial` means the record is still emitted with whatever resolved. Nothing is
silently dropped, and the unresolved share is a reported health metric.

**Catalog snapshot.** Built from `INFORMATION_SCHEMA.COLUMNS` and `VIEWS` into one JSON
file, versioned by content hash and loaded once per cold start: a mounted volume locally,
GCS in the cloud. Ours is 324 tables and tiny. For estates with 100k+ tables, the interface
allows sending a catalog slice per batch, using T0's `referenced_tables` plus view expansion.

**Cache key.** `(shape_id, parser version, catalog version)`. A new parser or catalog version
re-parses only what it affects.

## 6. Packaging

- One image, `qlsc-parse`: Python 3.12 with `sqlglot[c]` and a thin HTTP layer.
  - `POST /v1/fingerprint` (T1) and `POST /v1/resolve` (T2) take NDJSON batches of about
    500 items, so per-request overhead is negligible.
  - `batch` mode reads and writes files (local or `gs://`) for Cloud Run jobs.
- **docker-compose:** a `parser` service with N worker processes (one per core) next to
  Neo4j. The pipeline driver calls it over HTTP, the same way it would call Cloud Run.
- **Cloud:** the same image runs unchanged on Cloud Run (service or job), on Cloud Run
  functions, or as a Lambda container image. No local state.
- The library is importable too, so unit tests and notebooks can call it in-process.

## 7. Correctness before speed: tests

- **Golden records.** About 40 hand-checked shapes covering:
  - nested CTEs with shadowed aliases, `USING`, and `SELECT * EXCEPT/REPLACE`;
  - `UNNEST` of structs (GA4 `event_params`), wildcard tables with `_TABLE_SUFFIX`, and
    correlated subqueries;
  - `QUALIFY`, `PIVOT`, `MERGE` with `UPDATE SET`, and CTAS through views;
  - Looker's generated SQL, dbt incremental `MERGE`, and a staging view rename;
  - the three trap joins.
- **Invariants on every run:**
  - every resolved table and column exists in the catalog;
  - no CTE name ever appears as a table;
  - every join side resolves or is listed as unresolved.
- **A benchmark in the test suite,** so regressions in ms per shape are visible.

## 8. One realism fix needed first (simulator)

`simulate.py` computes `normalized_literals` with a regex that keeps comments, whitespace
and case. Real BigQuery ignores all three. As a result, every Looker query (each carries a
context comment) gets its own hash, and T0 would under-deduplicate compared with a real log.
The fix: compute the hash from the AST, the way T1 does, matching the probe results in §2.
Then re-run the simulator and **replace `fnb_query_log.jobs`**. The load is free, and only
this one field changes.

## 9. M1 steps (original plan)

1. Fix the simulator hash, regenerate, and reload the log table (needs your OK to replace it).
2. Build the `qlsc-parse` library, with golden tests and invariants.
3. Wrap it in the service and add it to `docker-compose.yml`.
4. Extract: the T0 aggregate query and the catalog snapshot from BigQuery.
5. Dry-run the pipeline on a 5% sample. Review the parse-health report and 20 records by
   hand together **before** the full run.
6. Full run, load into `querylog`, and a score report: parse health, join recovery, lineage.

## 10. Build log and measured results (2026-09-24)

**Done.** Steps 1–5. The simulator hash now mimics BigQuery exactly: the twelve probe
groupings match. Along the way I fixed two `hash()` calls that were salted per process, so
the log is byte-for-byte reproducible. The log was reloaded (315,729 jobs). Also built:
- the parser library with 43 golden tests;
- the service, `qlsc-parser` in docker-compose, running compiled sqlglot;
- T0 and catalog extraction;
- the 5% sample run with its health report and review sample.

**Correction to §2.** The 4.7 ms/shape figure was a benchmark artefact: it passed the schema
as a dict, and sqlglot rebuilt it on every call. With a prebuilt schema, resolution costs
**~0.6–0.9 ms per shape**. As a result, T1 (~0.7–0.8 ms per distinct text) is now the
larger cost. The T1 optimisation, if it's ever needed, is to fingerprint once per BigQuery
hash and take literals with the tokenizer. That still needs no Rust.

**Full-log check** (in-process, no outputs written). All of these hold:
- 121,093 texts collapse to 2,293 shapes.
- All 1,100 shapes that succeeded in BigQuery resolve with status `ok`.
- All 94 catalog view definitions resolve.
- Table resolution agrees with BigQuery's `referenced_tables` on 1,100 of 1,100 shapes.

**Design changes made during the build:**
- **Shard families come from the catalog,** not from a regex, so a one-off
  `CUST_MSTR_BKP_20250211` keeps its name.
- **Canonicalization rules ship inside the catalog snapshot.** A worker needs exactly one
  artifact.
- **The catalog comes from per-dataset INFORMATION_SCHEMA views,** UNIONed. The
  region-level views need project-wide list rights, which the service account doesn't have.
  Cost: about 1.3 GiB billed (roughly $0.008), because each INFORMATION_SCHEMA view bills a
  10 MiB minimum.
- **A dataset never referenced in the log** (`sbx_tom_okafor`) is placed in the logical
  project of its sibling datasets (`sbx_*`).
- **Unqualified columns follow BigQuery's own rule** (the one visible source that has the
  name). `qualify` leaves some unqualified, for example in the copy it makes of a correlated
  subquery when expanding `GROUP BY <alias>`.
- **Lineage from a transient source** (Fivetran staging) keeps its column names as written.

**Bugs the golden tests and the hand review caught.** Parse health never showed any of
these as failures:
- a bare-column projection dropped from lineage and CTE traces;
- `UNION ALL` branches matched by name rather than position;
- `NOT` ignored (`IS NOT NULL` recorded as `IS NULL`);
- a parenthesized CTAS body losing its lineage;
- dbt `INSERT ROW` losing its lineage;
- `GROUP BY ALL` keys not marked;
- the Looker PDT id length;
- duplicated GA4 filters;
- `COUNT(*)` recorded as a constant;
- function spellings (`LPAD`, `COUNTIF`).

## 11. Full run, load and first score (2026-09-24)

`parse_log.py` parses the full log in 16 seconds of wall time on 6 workers: 121,187 texts
and 2,387 shapes. `load_graph.py --reset` loads the Neo4j `semanticlayer` database in
under 3 seconds: 9,839 nodes and 24,031 relationships. Graph invariants hold:
- every table is either in the catalog, or labeled transient or system;
- no CTE name became a table;
- every join key touches exactly two columns;
- no structure was created from queries that failed in BigQuery.

`specs/tools/score.py` is the only code that reads both the answer key and the graph. It
uses usage truth: only statements that ran successfully in the window count.

| | graph | key | matched | precision | recall |
|---|---|---|---|---|---|
| Join pairs | 156 | 123 | 123 | 78.8% vs. key; **100% after hand review** | **100%** |
| Lineage edges | 1,887 | 1,887 | 1,887 | **100%** | **100%** |
| Parse health | 1,194 of 1,194 successful shapes (log + views) resolved ok | | | | |

The join key has three sources: declared model joins, declared Looker explore joins, and
a regex extractor over every successful statement. The regex extractor only sees
directly named tables. The 33 graph pairs outside the key are joins it cannot see:
- through CTEs or subqueries;
- `IN (SELECT …)` semi-joins;
- transformed keys such as `archive_month = DATE_TRUNC(score_date, MONTH)`.

I read all 33 by hand, and all are correct. Three are the same column joined to itself,
for example two aggregates of `dim_account` joined on `branch_id`. They are correct but
say nothing about identity, and M3 should treat them that way.

Scoring found three more resolver bugs, now covered by tests (46 in total):
- `UNION ALL` branches left as `SELECT *` over CTEs whose outputs collide were not traced by
  position. This cost 19 lineage edges in `int_accounts_unioned`.
- Columns that only steer a value were used as join sides: the `ORDER BY` of
  `ARRAY_AGG(x ORDER BY t)` and CASE/IF conditions. That produced two false join pairs.
  These columns now carry `control`; lineage keeps them and joins don't.
- The scorer's own reference extractor missed unquoted `dataset.table` names. That was a
  bug in the key, not in the pipeline.

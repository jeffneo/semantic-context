#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "google-cloud-bigquery>=3.25"]
# ///
"""Stage 1 / T0: pull the aggregated log and the catalog snapshot from BigQuery.

Reads only BigQuery (the log table and INFORMATION_SCHEMA). Never reads specs/.

  work/t0_groups.ndjson.gz  one row per (bq hash, query text, principal, statement,
                            project, week) with counts, bytes, time range, refs
  work/catalog.json         tables, columns, types, partitioning, view SQL, shard
                            families and physical->logical dataset aliases

Job rows never leave the warehouse: grouping happens in BigQuery. On a real estate
this is the step that turns billions of jobs into distinct texts.

Usage: uv run pipeline/extract.py [--log-only | --catalog-only]

Also: work/t0_principals.ndjson.gz - per-principal time profile (schedule vs. people).
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import google.auth.credentials
import yaml
from google.cloud import bigquery

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"


class GcloudCredentials(google.auth.credentials.Credentials):
    """Token from `gcloud auth print-access-token` under a named configuration."""

    def __init__(self, config: str):
        super().__init__()
        self.config = config

    def refresh(self, request):
        env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": self.config}
        out = subprocess.run(["gcloud", "auth", "print-access-token"], env=env,
                             capture_output=True, text=True, check=True)
        self.token = out.stdout.strip()
        self.expiry = dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(minutes=45)


# One row per distinct (text, principal, week). Everything the later stages need
# about individual jobs is aggregated here, inside the warehouse.
T0_SQL = """
SELECT
  query_info.query_hashes.normalized_literals AS bq_hash,
  query,
  job_type,
  statement_type,
  project_id,
  user_email,
  DATE_TRUNC(DATE(creation_time), WEEK(MONDAY)) AS week,
  COUNT(*) AS jobs,
  COUNTIF(cache_hit) AS cache_hits,
  COUNTIF(error_result IS NOT NULL) AS errors,
  ANY_VALUE(error_result.reason) AS error_reason,
  ANY_VALUE(error_result.message) AS error_message,
  SUM(IFNULL(total_bytes_processed, 0)) AS bytes_processed,
  SUM(IFNULL(total_bytes_billed, 0)) AS bytes_billed,
  SUM(IFNULL(total_slot_ms, 0)) AS slot_ms,
  MIN(creation_time) AS first_seen,
  MAX(creation_time) AS last_seen,
  ARRAY_AGG(DISTINCT DATE(creation_time)) AS days,
  ANY_VALUE(TO_JSON_STRING(referenced_tables)) AS referenced_tables,
  -- a load job has no SQL: its destination is what it did, so it is part of the key
  IF(destination_table.dataset_id LIKE '\\\\_%', NULL,
    FORMAT('%s.%s.%s', destination_table.project_id, destination_table.dataset_id,
           destination_table.table_id)) AS destination_table,
  ANY_VALUE(TO_JSON_STRING(labels)) AS labels
FROM `{project}.{log_table}`
GROUP BY bq_hash, query, job_type, statement_type, project_id, user_email, week, destination_table
"""

# How each principal behaves in time, aggregated in the warehouse (one row per principal):
# working-hours and weekend share, and how much of its work lands on the same
# (hour, minute) slot day after day - the signature of a schedule.
PRINCIPALS_SQL = """
WITH j AS (
  SELECT user_email, DATETIME(creation_time, @tz) AS t
  FROM `{project}.{log_table}`
),
a AS (
  SELECT user_email, COUNT(*) AS jobs, COUNT(DISTINCT DATE(t)) AS active_days,
         COUNTIF(EXTRACT(DAYOFWEEK FROM t) IN (1, 7)) AS weekend_jobs,
         COUNTIF(EXTRACT(DAYOFWEEK FROM t) BETWEEN 2 AND 6 AND EXTRACT(HOUR FROM t) BETWEEN 8 AND 17)
           AS business_hours_jobs,
         COUNT(DISTINCT EXTRACT(HOUR FROM t)) AS distinct_hours,
         MIN(t) AS first_job, MAX(t) AS last_job
  FROM j GROUP BY 1
),
slots AS (
  SELECT user_email, EXTRACT(HOUR FROM t) AS h, EXTRACT(MINUTE FROM t) AS m,
         COUNT(DISTINCT DATE(t)) AS slot_days, COUNT(*) AS n
  FROM j GROUP BY 1, 2, 3
),
rs AS (
  SELECT s.user_email, SUM(IF(s.slot_days >= 0.5 * a.active_days, s.n, 0)) AS recurring_jobs,
         COUNT(*) AS distinct_slots
  FROM slots s JOIN a USING (user_email) GROUP BY 1
),
dc AS (
  SELECT user_email, SAFE_DIVIDE(STDDEV(n), AVG(n)) AS daily_cv
  FROM (SELECT user_email, DATE(t) AS d, COUNT(*) AS n FROM j GROUP BY 1, 2) GROUP BY 1
)
SELECT a.*, rs.recurring_jobs / a.jobs AS recurring_slot_share, rs.distinct_slots, dc.daily_cv
FROM a JOIN rs USING (user_email) JOIN dc USING (user_email)
"""

# Where each dataset lives, as the log itself reports it.
DATASET_HOME_SQL = """
SELECT r.project_id, r.dataset_id, COUNT(*) AS n
FROM `{project}.{log_table}`, UNNEST(referenced_tables) AS r
GROUP BY 1, 2
UNION ALL
SELECT destination_table.project_id, destination_table.dataset_id, COUNT(*)
FROM `{project}.{log_table}`
WHERE destination_table.dataset_id IS NOT NULL
GROUP BY 1, 2
"""

# Physical facts only: names, types, partitioning, view SQL. Descriptions, labels
# and constraints are deliberately not selected (plans/PIPELINE_PLAN.md §0).
# Per-dataset views, UNIONed: the region-level views need project-wide list rights.
COLUMNS_SQL = """
SELECT c.table_schema, c.table_name, t.table_type, c.column_name, c.ordinal_position,
       c.data_type, c.is_partitioning_column = 'YES' AS is_partition,
       c.clustering_ordinal_position
FROM `{project}.{ds}.INFORMATION_SCHEMA.COLUMNS` c
JOIN `{project}.{ds}.INFORMATION_SCHEMA.TABLES` t USING (table_schema, table_name)
"""
VIEWS_SQL = """
SELECT table_schema, table_name, view_definition
FROM `{project}.{ds}.INFORMATION_SCHEMA.VIEWS`
"""


def union(template: str, project: str, datasets: list[str]) -> str:
    return "\nUNION ALL\n".join(template.format(project=project, ds=d) for d in datasets)


SHARD = re.compile(r"^(.*_)(20\d{6}|20\d{4})$")


def client(cfg) -> bigquery.Client:
    bq = cfg["bigquery"]
    return bigquery.Client(project=bq["project"], credentials=GcloudCredentials(bq["gcloud_config"]),
                           location=bq["location"])


def run(c: bigquery.Client, sql: str, params=()) -> tuple[list, bigquery.QueryJob]:
    job = c.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=list(params)))
    return list(job.result()), job


def jsonable(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if isinstance(v, list):
        return [jsonable(x) for x in v]
    return v


def extract_log(c, cfg) -> dict:
    bq = cfg["bigquery"]
    rows, job = run(c, T0_SQL.format(project=bq["project"], log_table=bq["log_table"]))
    WORK.mkdir(exist_ok=True)
    with gzip.open(WORK / "t0_groups.ndjson.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps({k: jsonable(v) for k, v in r.items()}) + "\n")
    jobs = sum(r["jobs"] for r in rows)
    texts = len({r["query"] for r in rows if r["query"]})
    print(f"T0: {jobs:,} jobs -> {len(rows):,} groups, {texts:,} distinct texts "
          f"({job.total_bytes_billed / 2**20:,.0f} MiB billed)")
    prows, pjob = run(c, PRINCIPALS_SQL.format(project=bq["project"], log_table=bq["log_table"]),
                      [bigquery.ScalarQueryParameter("tz", "STRING", bq.get("timezone", "UTC"))])
    with gzip.open(WORK / "t0_principals.ndjson.gz", "wt") as f:
        for r in prows:
            f.write(json.dumps({k: jsonable(v) for k, v in r.items()}) + "\n")
    print(f"T0: {len(prows)} principal time profiles ({pjob.total_bytes_billed / 2**20:,.0f} MiB billed)")
    return {"jobs": jobs, "groups": len(rows), "texts": texts}


def extract_catalog(c, cfg) -> dict:
    bq = cfg["bigquery"]
    prefix, exclude = bq["dataset_prefix"], bq.get("exclude_datasets", [])
    datasets = sorted(d.dataset_id for d in c.list_datasets()
                      if d.dataset_id.startswith(prefix) and d.dataset_id not in exclude)

    # logical project of each dataset, by majority vote of the log's own references
    home_rows, _ = run(c, DATASET_HOME_SQL.format(project=bq["project"], log_table=bq["log_table"]))
    votes: dict[str, Counter] = defaultdict(Counter)
    for r in home_rows:
        votes[r["dataset_id"]][r["project_id"]] += r["n"]

    col_rows, j1 = run(c, union(COLUMNS_SQL, bq["project"], datasets) + "ORDER BY 1, 2, 5")
    view_rows, j2 = run(c, union(VIEWS_SQL, bq["project"], datasets))
    view_sql = {(r["table_schema"], r["table_name"]): r["view_definition"] for r in view_rows}

    physical: dict[tuple, dict] = {}
    for r in col_rows:
        t = physical.setdefault((r["table_schema"], r["table_name"]), {
            "type": r["table_type"], "columns": {}, "partition": None, "cluster": []})
        t["columns"][r["column_name"]] = r["data_type"]
        if r["is_partition"]:
            t["partition"] = r["column_name"]
        if r["clustering_ordinal_position"]:
            t["cluster"].append(r["column_name"])

    aliases, unhomed = {}, {}
    for ds in sorted({ds for ds, _ in physical}):
        logical_ds = ds[len(prefix):]
        home = votes.get(logical_ds)
        if home:
            aliases[f"{bq['project']}.{ds}"] = f"{home.most_common(1)[0][0]}.{logical_ds}"
            continue
        # Never referenced in the window: place it with the datasets that share its
        # leading name token (sbx_*, dw_*), by the same vote.
        token = logical_ds.split("_")[0] + "_"
        sib = Counter()
        for other, v in votes.items():
            if other.startswith(token):
                sib.update(v)
        unhomed[ds] = sib.most_common(1)[0][0] if sib else bq["project"]
        aliases[f"{bq['project']}.{ds}"] = f"{unhomed[ds]}.{logical_ds}"

    # shard families: 2+ tables sharing a prefix with a date suffix
    fam = defaultdict(list)
    for ds, name in physical:
        m = SHARD.match(name)
        if m:
            fam[(ds, m.group(1))].append(name)
    families = {k: v for k, v in fam.items() if len(v) >= 2}

    rules = [(re.compile(r["pattern"]), r["replace"]) for r in cfg.get("canonical_identifiers", [])]
    tables = {}
    for (ds, name), t in sorted(physical.items()):
        home = aliases.get(f"{bq['project']}.{ds}")
        if not home:
            continue
        m = SHARD.match(name)
        if m and (ds, m.group(1)) in families:
            fqn = f"{home}.{m.group(1)}*"
            entry = tables.setdefault(fqn, {"kind": "WILDCARD", "columns": {}, "partition": None,
                                            "cluster": [], "shards": []})
            entry["columns"].update(t["columns"])
            entry["shards"].append(name)
            continue
        entry = {"kind": {"BASE TABLE": "TABLE"}.get(t["type"], t["type"]), "columns": t["columns"],
                 "partition": t["partition"], "cluster": t["cluster"]}
        if (ds, name) in view_sql:
            entry["view_sql"] = view_sql[(ds, name)]
        canon = name
        for rx, rep in rules:
            canon = rx.sub(rep, canon)
        if canon != name:           # e.g. one Looker PDT generation -> LR_{id}_name
            entry["physical"] = [name]
            if f"{home}.{canon}" in tables:
                prev = tables[f"{home}.{canon}"]
                prev["columns"].update(entry["columns"])
                prev["physical"].append(name)
                continue
        tables[f"{home}.{canon}"] = entry
    for e in tables.values():
        if e["kind"] == "WILDCARD":
            e["columns"]["_TABLE_SUFFIX"] = "STRING"
            e["shards"].sort()

    body = {"rules": cfg.get("canonical_identifiers", []), "aliases": aliases, "shard_families": sorted(f"{aliases[f'{bq['project']}.{ds}']}.{p}"
                                                         for ds, p in families if f"{bq['project']}.{ds}" in aliases),
            "tables": tables}
    version = "cat-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    cat = {"version": version, "extracted_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
           "source": f"{bq['project']} INFORMATION_SCHEMA, {len(datasets)} datasets", **body}
    WORK.mkdir(exist_ok=True)
    (WORK / "catalog.json").write_text(json.dumps(cat, indent=1))
    kinds = Counter(e["kind"] for e in tables.values())
    billed = (j1.total_bytes_billed + j2.total_bytes_billed) / 2**20
    print(f"catalog {version} ({billed:,.0f} MiB billed): {len(tables)} tables {dict(kinds)}, "
          f"{sum(len(e['columns']) for e in tables.values()):,} columns, {len(families)} shard families")
    if unhomed:
        print(f"  never referenced in the log, placed by sibling datasets: {unhomed}")
    return cat


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-only", action="store_true")
    ap.add_argument("--catalog-only", action="store_true")
    a = ap.parse_args()
    cfg = yaml.safe_load((HERE / "estate.yaml").read_text())
    c = client(cfg)
    if not a.catalog_only:
        extract_log(c, cfg)
    if not a.log_only:
        extract_catalog(c, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())

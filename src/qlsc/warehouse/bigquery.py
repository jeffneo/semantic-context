"""BigQuery: the log from INFORMATION_SCHEMA.JOBS (or a table with its schema), the catalog from
INFORMATION_SCHEMA.COLUMNS / TABLES / VIEWS, and free dry runs.

Settings (config `warehouse:`): project, gcloud_config, location, log_table, dataset_prefix,
exclude_datasets, timezone. Job rows never leave the warehouse: grouping happens in BigQuery.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterator

import google.auth.credentials
from google.cloud import bigquery

from qlsc.warehouse import Warehouse


class GcloudCredentials(google.auth.credentials.Credentials):
    """A token from `gcloud auth print-access-token` under a named gcloud configuration."""

    def __init__(self, config: str):
        super().__init__()
        self.config = config

    def refresh(self, request):
        env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": self.config}
        out = subprocess.run(
            ["gcloud", "auth", "print-access-token"], env=env, capture_output=True, text=True, check=True
        )
        self.token = out.stdout.strip()
        self.expiry = dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(minutes=45)


def client(project: str, gcloud_config: str, location: str) -> bigquery.Client:
    return bigquery.Client(project=project, credentials=GcloudCredentials(gcloud_config), location=location)


# One row per distinct (text, principal, week): everything later stages need about jobs, aggregated here.
LOG_SQL = """
SELECT
  query, job_type, statement_type, project_id, user_email,
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
GROUP BY query, job_type, statement_type, project_id, user_email, week, destination_table
"""

# How each principal behaves in time: working-hours and weekend share, and how much of its work lands
# on the same (hour, minute) slot day after day - the signature of a schedule.
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

# Physical facts only: names, types, partitioning, view SQL. Descriptions, labels and constraints are
# deliberately not selected (docs/design.md: designed models are not inputs). Per-dataset views,
# UNIONed: the region-level views need project-wide list rights.
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


class BigQuery(Warehouse):
    name = "BigQuery"
    sql = "BigQuery Standard SQL"
    dialect = "bigquery"

    def __init__(self, settings):
        super().__init__(settings)
        self._client = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            self._client = client(self.cfg["project"], self.cfg["gcloud_config"], self.cfg["location"])
        return self._client

    def _query(self, sql: str, params=()) -> list:
        job = self.client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=list(params)))
        rows = list(job.result())
        print(f"  BigQuery: {len(rows):,} rows, {job.total_bytes_billed / 2**20:,.0f} MiB billed")
        return rows

    def _log_sql(self, template: str) -> str:
        return template.format(project=self.cfg["project"], log_table=self.cfg["log_table"])

    def log_groups(self) -> Iterator[dict]:
        for r in self._query(self._log_sql(LOG_SQL)):
            yield dict(r.items())

    def principal_profiles(self) -> Iterator[dict]:
        tz = bigquery.ScalarQueryParameter("tz", "STRING", self.cfg.get("timezone", "UTC"))
        for r in self._query(self._log_sql(PRINCIPALS_SQL), [tz]):
            yield dict(r.items())

    def catalog(self) -> dict:
        project, prefix = self.cfg["project"], self.cfg["dataset_prefix"]
        exclude = set(self.cfg.get("exclude_datasets", []))
        datasets = sorted(
            d.dataset_id
            for d in self.client.list_datasets()
            if d.dataset_id.startswith(prefix) and d.dataset_id not in exclude
        )
        union = lambda template: "\nUNION ALL\n".join(
            template.format(project=project, ds=d) for d in datasets
        )
        tables: dict[tuple, dict] = {}
        for r in self._query(union(COLUMNS_SQL) + "ORDER BY 1, 2, 5"):
            t = tables.setdefault(
                (r["table_schema"], r["table_name"]),
                {"type": r["table_type"], "columns": {}, "partition": None, "cluster": []},
            )
            t["columns"][r["column_name"]] = r["data_type"]
            if r["is_partition"]:
                t["partition"] = r["column_name"]
            if r["clustering_ordinal_position"]:
                t["cluster"].append(r["column_name"])
        for r in self._query(union(VIEWS_SQL)):
            if (r["table_schema"], r["table_name"]) in tables:
                tables[(r["table_schema"], r["table_name"])]["view_sql"] = r["view_definition"]
        return {
            "source": f"{project} INFORMATION_SCHEMA, {len(datasets)} datasets",
            "project": project,
            "tables": tables,
            "aliases": self._aliases(sorted({ds for ds, _ in tables})),
        }

    def _aliases(self, datasets: list[str]) -> dict[str, str]:
        """The estate is deployed as <prefix><dataset> in one project; the logical project of each
        dataset is the one the log's own references name most often."""
        project, prefix = self.cfg["project"], self.cfg["dataset_prefix"]
        votes: dict[str, Counter] = defaultdict(Counter)
        for r in self._query(self._log_sql(DATASET_HOME_SQL)):
            votes[r["dataset_id"]][r["project_id"]] += r["n"]
        aliases, unhomed = {}, {}
        for ds in datasets:
            logical = ds[len(prefix) :]
            home = votes.get(logical)
            if not home:
                # never referenced in the window: place it with the datasets sharing its leading
                # name token (sbx_*, dw_*), by the same vote
                token = logical.split("_")[0] + "_"
                siblings = Counter()
                for other, v in votes.items():
                    if other.startswith(token):
                        siblings.update(v)
                home = unhomed[ds] = siblings or Counter({project: 1})
            aliases[f"{project}.{ds}"] = f"{home.most_common(1)[0][0]}.{logical}"
        if unhomed:
            print(f"  never referenced in the log, placed by sibling datasets: {sorted(unhomed)}")
        return aliases

    def is_service_account(self, principal: str) -> bool:
        return principal.endswith("gserviceaccount.com")

    def _dry_run(self, sql: str) -> dict:
        try:
            config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            job = self.client.query(sql, job_config=config)
            return {"ok": True, "bytes_processed": job.total_bytes_processed}
        except subprocess.CalledProcessError:
            login = f"CLOUDSDK_ACTIVE_CONFIG_NAME={self.cfg['gcloud_config']} gcloud auth login"
            return {"ok": None, "error": f"gcloud needs a fresh login ({login})"}
        except Exception as e:  # the planner's message is the useful part
            msg = getattr(e, "message", None) or str(e)
            deployed = re.escape(self.cfg["project"]) + "[:.]" + re.escape(self.cfg["dataset_prefix"])
            msg = re.sub(r"^POST https://\S+: ", "", re.sub(deployed, "", msg)).split("\n")[0]
            return {"ok": False, "error": msg if len(msg) <= 400 else msg[:397] + "..."}

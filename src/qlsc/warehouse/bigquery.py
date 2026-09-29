"""BigQuery: the log from INFORMATION_SCHEMA.JOBS (or a table with its schema), the catalog from
INFORMATION_SCHEMA.COLUMNS / TABLES / VIEWS, and free dry runs.

Settings (config `warehouse:`): project, gcloud_config, location, log_table, dataset_prefix,
exclude_datasets, timezone. Job rows never leave the warehouse: grouping happens in BigQuery.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

import google.auth.credentials
from google.api_core import exceptions as api_exceptions
from google.auth import impersonated_credentials
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery

from qlsc.warehouse import Warehouse, WarehouseUnavailable


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


SCOPE = "https://www.googleapis.com/auth/cloud-platform"


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
    dialect = "bigquery"  # sqlglot's name for it: the compiler renders its SQL in this dialect
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

    # ---- entitlements: BigQuery answers, as the principal, what the principal may read

    def acting_as(self, principal: str) -> BigQuery:
        """This connector as a principal: the estate's identity impersonates it (it holds the
        principal's token-creator grant), so BigQuery enforces the principal's own grants, column
        policy tags and row access policies on every query and check."""
        other = BigQuery(self.settings)
        creds = impersonated_credentials.Credentials(
            source_credentials=GcloudCredentials(self.cfg["gcloud_config"]),
            target_principal=principal,
            target_scopes=[SCOPE],
            lifetime=3600,
        )
        other._client = bigquery.Client(
            project=self.cfg["project"], credentials=creds, location=self.cfg["location"]
        )
        other.principal = principal
        return other

    def _each(self, items: list, f) -> list:
        """f over items concurrently (the permission checks). A failed login is the warehouse unavailable,
        raised, never read as a denial."""
        try:
            with ThreadPoolExecutor(self.settings["entitlements"]["workers"]) as pool:
                return list(pool.map(f, items))
        except subprocess.CalledProcessError as e:
            raise WarehouseUnavailable(self._login_needed()["error"]) from e

    def _physical_ref(self, table: str) -> bigquery.TableReference | None:
        """A logical table's physical reference; a wildcard (shard family) by its first shard."""
        cat = json.loads((self.settings.work / "catalog.json").read_text())
        entry = cat["tables"].get(table) or {}
        if entry.get("kind") == "WILDCARD":
            if not entry.get("shards"):
                return None
            table = table[:-1] + entry["shards"][0][len(table.rsplit(".", 1)[-1]) - 1 :]
        elif not entry:
            return None  # not deployed: nobody can read it
        return bigquery.TableReference.from_string(self._physical_table(table).strip("`"))

    def readable(self, tables: list[str]) -> set[str]:
        def check(t):
            ref = self._physical_ref(t)
            if ref is None:
                return False
            try:
                got = self.client._connection.api_request(
                    method="POST",
                    path=f"/projects/{ref.project}/datasets/{ref.dataset_id}/tables/{ref.table_id}:testIamPermissions",
                    data={"permissions": ["bigquery.tables.getData"]},
                )
            except (api_exceptions.Forbidden, api_exceptions.NotFound):
                return False  # no such table, or not even allowed to ask; any other failure is raised
            if "bigquery.tables.getData" not in got.get("permissions", []):
                return False
            if kinds.get(t) != "VIEW":
                return True
            # A view runs with its reader's own grants on what it reads (unless it is authorized): the grant on
            # the view alone doesn't make it readable. A dry run says (LIMIT 1: an empty query checks nothing).
            return (
                self._dry_run(f"SELECT 1 FROM `{ref.project}.{ref.dataset_id}.{ref.table_id}` LIMIT 1")["ok"]
                is True
            )

        kinds = {
            k: v.get("kind")
            for k, v in json.loads((self.settings.work / "catalog.json").read_text())["tables"].items()
        }
        return {t for t, ok in zip(tables, self._each(tables, check)) if ok}

    def column_tags(self, tables: list[str]) -> dict[tuple[str, str], str]:
        def tags(t):
            ref = self._physical_ref(t)
            if ref is None:
                return []
            try:
                schema = self.client.get_table(ref).schema
            except Exception:
                return []
            return [
                (t, f.name, f.policy_tags.names[0]) for f in schema if f.policy_tags and f.policy_tags.names
            ]

        return {(t, c): tag for found in self._each(tables, tags) for t, c, tag in found}

    def readable_tags(self, tags: list[str]) -> set[str]:
        session = AuthorizedSession(self.client._credentials)

        def check(tag):
            r = session.post(
                f"https://datacatalog.googleapis.com/v1/{tag}:testIamPermissions",
                json={"permissions": ["datacatalog.categories.fineGrainedGet"]},
            )
            if r.status_code == 401:
                raise WarehouseUnavailable(f"the warehouse couldn't be asked about {tag}: {r.status_code}")
            return r.ok and "datacatalog.categories.fineGrainedGet" in r.json().get("permissions", [])

        return {t for t, ok in zip(tags, self._each(tags, check)) if ok}

    def row_policies(self, tables: list[str]) -> set[str]:
        def has(t):
            ref = self._physical_ref(t)
            if ref is None:
                return False
            try:
                got = self.client._connection.api_request(
                    method="GET",
                    path=f"/projects/{ref.project}/datasets/{ref.dataset_id}/tables/{ref.table_id}/rowAccessPolicies",
                )
            except api_exceptions.NotFound:
                return False  # no such table. Any other failure is raised: "no policy" is never a guess

            return bool(got.get("rowAccessPolicies"))

        return {t for t, ok in zip(tables, self._each(tables, has)) if ok}

    # ---- Virtual Graph

    def _physical_table(self, table: str) -> str:
        return self.physical_sql(f"SELECT 1 FROM `{table}`").split("FROM ", 1)[1].strip()

    def is_unique(self, table: str, columns: list[str]) -> bool:
        key = f"TO_JSON_STRING(STRUCT({', '.join(f'`{c}`' for c in columns)}))"
        n, distinct = next(
            iter(self._query(f"SELECT COUNT(*), COUNT(DISTINCT {key}) FROM {self._physical_table(table)}"))
        )
        return n > 0 and n == distinct

    def create_views(self, dataset: str, views: dict[str, str]) -> None:
        full = f"{self.cfg['project']}.{dataset}"
        self.client.create_dataset(bigquery.Dataset(full), exists_ok=True)
        for name, sql in views.items():
            self.client.query(f"CREATE OR REPLACE VIEW `{full}.{name}` AS\n{self.physical_sql(sql)}").result()

    def virtual_graph(self, dataset: str) -> tuple[dict, dict]:
        vg = self.settings.get("virtualize", {})
        datasource = {
            "type": "bigquery",
            "projectId": self.cfg["project"],
            "datasetName": dataset,
            "enableHighThroughputAPI": False,
            "maximumBytesBilled": vg.get("maximum_bytes_billed", 10**9),
        }
        # Anything in additionalProperties goes to the Google BigQuery JDBC driver as is. OAuthType 3 makes it
        # use application-default credentials (GOOGLE_APPLICATION_CREDENTIALS), which accept an impersonated
        # service account; the documented `configfile` secret alone accepts only a service-account key.
        if vg.get("driver_properties"):
            datasource["additionalProperties"] = {k: str(v) for k, v in vg["driver_properties"].items()}
        secret = {"type": "configfile", "filename": vg.get("credentials_file", "/nvg_home/credentials.json")}
        return datasource, secret

    def is_service_account(self, principal: str) -> bool:
        return principal.endswith("gserviceaccount.com")

    def _dry_run(self, sql: str) -> dict:
        try:
            config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            job = self.client.query(sql, job_config=config)
            return {"ok": True, "bytes_processed": job.total_bytes_processed}
        except subprocess.CalledProcessError:
            return self._login_needed()
        except Exception as e:
            return {"ok": False, "error": self._message(e)}

    def _run(self, sql: str, maximum_bytes_billed: int, rows: int, cache: bool = True) -> dict:
        try:
            config = bigquery.QueryJobConfig(maximum_bytes_billed=maximum_bytes_billed, use_query_cache=cache)
            job = self.client.query(sql, job_config=config)
            result = job.result(max_results=rows)
            return {
                "ok": True,
                "columns": [f.name for f in result.schema],
                "rows": [dict(r.items()) for r in result],
                "total": result.total_rows,
                "bytes_billed": job.total_bytes_billed or 0,
            }
        except subprocess.CalledProcessError:
            return self._login_needed()
        except Exception as e:
            return {"ok": False, "error": self._message(e)}

    def _login_needed(self) -> dict:
        login = f"CLOUDSDK_ACTIVE_CONFIG_NAME={self.cfg['gcloud_config']} gcloud auth login"
        return {"ok": None, "error": f"gcloud needs a fresh login ({login})"}

    def _message(self, e: Exception) -> str:
        """The planner's message, in logical names: the useful part of a BigQuery error."""
        msg = getattr(e, "message", None) or str(e)
        deployed = re.escape(self.cfg["project"]) + "[:.]" + re.escape(self.cfg["dataset_prefix"])
        msg = re.sub(r"^POST https://\S+: ", "", re.sub(deployed, "", msg)).split("\n")[0]
        return msg if len(msg) <= 400 else msg[:397] + "..."

"""Warehouse connectors: the only code that talks to a warehouse.

The config's `warehouse.type` picks one; the rest of `warehouse:` is that connector's own settings.
A connector supplies five things, and the pipeline never asks a warehouse for anything else:

  log_groups()           the query log, aggregated inside the warehouse: one record per distinct
                         (query text, principal, statement type, project, week) - see LOG_GROUP
  principal_profiles()   per principal, when it works: hours, weekends, recurring time slots
  catalog()              physical facts about tables: names, columns, types, partitioning, view SQL,
                         and where each physical dataset sits in the estate's logical names
  is_service_account()   whether a principal is a process rather than a person
  dry_run(sql)           the warehouse's verdict on a query, without running it

For `qlsc ask --run`, a connector may also run a query, billing at most a cap:

  run(sql, cap, rows)    the answer: its columns, the first rows, and what it billed

For `qlsc virtualize` (a Neo4j Virtual Graph over the warehouse's rows), a connector may also supply:

  is_unique(table, cols) whether columns identify a table's rows (Virtual Graph needs unique keys)
  create_views(dataset, views)   the views the virtual graph reads, in one dataset of their own
  virtual_graph(dataset) Virtual Graph's datasource.json and secret.json for this warehouse

To add a warehouse: subclass Warehouse in a module here and list it in CONNECTORS.
"""

from __future__ import annotations

import importlib
import json
from abc import ABC, abstractmethod
from collections.abc import Iterator

import sqlglot
from sqlglot import exp

from qlsc.config import ConfigError, Settings

CONNECTORS = {"bigquery": "qlsc.warehouse.bigquery:BigQuery"}

# The log-group record. Field names follow BigQuery's INFORMATION_SCHEMA.JOBS; other connectors map
# their log (Snowflake QUERY_HISTORY, Databricks system.query.history) onto the same names.
LOG_GROUP = [
    "query",
    "job_type",
    "statement_type",
    "project_id",
    "user_email",
    "week",
    "jobs",
    "cache_hits",
    "errors",
    "error_reason",
    "error_message",
    "bytes_processed",
    "bytes_billed",
    "slot_ms",
    "first_seen",
    "last_seen",
    "days",
    "referenced_tables",
    "destination_table",
    "labels",
]


class Warehouse(ABC):
    name: str  # as people call it: "BigQuery"
    sql: str  # the SQL it runs, as the prompts say it: "BigQuery Standard SQL"
    dialect: str  # sqlglot's name for that dialect

    def __init__(self, settings: Settings):
        self.settings = settings
        self.cfg = settings["warehouse"]

    @abstractmethod
    def log_groups(self) -> Iterator[dict]:
        """One LOG_GROUP record per distinct (query, principal, statement type, project, week)."""

    @abstractmethod
    def principal_profiles(self) -> Iterator[dict]:
        """Per principal: user_email, jobs, active_days, weekend_jobs, business_hours_jobs,
        distinct_hours, first_job, last_job, recurring_slot_share, distinct_slots, daily_cv."""

    @abstractmethod
    def catalog(self) -> dict:
        """{"source": str, "project": the physical project,
        "tables": {(dataset, table): {"type", "columns": {name: type}, "partition", "cluster", "view_sql"?}},
        "aliases": {"<project>.<dataset>": "<logical project>.<logical dataset>"}}"""

    @abstractmethod
    def is_service_account(self, principal: str) -> bool: ...

    @abstractmethod
    def _dry_run(self, sql: str) -> dict:
        """Dry-run SQL in physical names -> {ok: True, bytes_processed} | {ok: False, error}, or
        {ok: None, error} when the warehouse could not be asked (credentials)."""

    # ---- Virtual Graph (optional)

    def is_unique(self, table: str, columns: list[str]) -> bool:
        raise NotImplementedError(f"{self.name}: no Virtual Graph support")

    def create_views(self, dataset: str, views: dict[str, str]) -> None:
        """Create or replace one view per entry {view name: SELECT in logical table names}."""
        raise NotImplementedError(f"{self.name}: no Virtual Graph support")

    def virtual_graph(self, dataset: str) -> tuple[dict, dict]:
        """(datasource.json, secret.json) for a virtual graph reading `dataset`."""
        raise NotImplementedError(f"{self.name}: no Virtual Graph support")

    # ---- running queries (optional; qlsc ask --run)

    def _run(self, sql: str, maximum_bytes_billed: int, rows: int) -> dict:
        """Run SQL in physical names -> {ok: True, columns, rows: the first `rows` as dicts, total,
        bytes_billed} | {ok: False, error}."""
        raise NotImplementedError(f"{self.name}: cannot run queries")

    def dry_run(self, sql: str) -> dict:
        """Dry-run SQL written in the graph's (logical) table names."""
        try:
            physical = self.physical_sql(sql)
        except sqlglot.errors.ParseError as e:
            return {"ok": False, "error": str(e)[:300]}
        return self._dry_run(physical)

    def run(self, sql: str, maximum_bytes_billed: int, rows: int) -> dict:
        """Run SQL written in logical table names, billing at most `maximum_bytes_billed`."""
        try:
            physical = self.physical_sql(sql)
        except sqlglot.errors.ParseError as e:
            return {"ok": False, "error": str(e)[:300]}
        return self._run(physical, maximum_bytes_billed, rows)

    def physical_sql(self, sql: str) -> str:
        """Logical table names (the log's, the graph's) -> the deployed tables, from the catalog snapshot."""
        cat = json.loads((self.settings.work / "catalog.json").read_text())
        dataset = {logical: phys for phys, logical in cat["aliases"].items()}
        by_name = {logical.split(".", 1)[1]: logical for logical in dataset}
        table = {
            fqn: sorted(t["physical"])[-1]  # a Looker PDT: its newest generation
            for fqn, t in cat["tables"].items()
            if t.get("physical") and t["kind"] != "WILDCARD"
        }
        tree = sqlglot.parse_one(sql, read=self.dialect)
        for t in tree.find_all(exp.Table):
            if not t.db:
                continue
            logical = f"{t.catalog}.{t.db}" if t.catalog else by_name.get(t.db)
            if logical not in dataset:
                continue
            project, ds = dataset[logical].split(".", 1)
            t.set("catalog", exp.to_identifier(project))
            t.set("db", exp.to_identifier(ds))
            t.set("this", exp.to_identifier(table.get(f"{logical}.{t.name}", t.name)))
        return tree.sql(dialect=self.dialect)


def connect(settings: Settings) -> Warehouse:
    kind = settings["warehouse"]["type"]
    if kind not in CONNECTORS:
        raise ConfigError(f"no connector for warehouse type {kind!r} (known: {', '.join(CONNECTORS)})")
    module, cls = CONNECTORS[kind].split(":")
    return getattr(importlib.import_module(module), cls)(settings)

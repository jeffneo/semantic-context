"""Catalog snapshot: physical facts about tables, plus name canonicalization.

The snapshot is produced by qlsc extract through a warehouse connector. It holds names,
types, partitioning and view SQL - never descriptions or constraints - and the SQL dialect.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from sqlglot import exp
from sqlglot.schema import MappingSchema

SYSTEM_PARTS = {"INFORMATION_SCHEMA"}
# Name resolution (project.dataset.table, wildcard shards, _TABLE_SUFFIX) is BigQuery's so far.
DIALECTS = {"bigquery"}
SHARD_SUFFIX = re.compile(r"^(20\d{6}|20\d{4}|\d*\*)$")


class Catalog:
    def __init__(self, data: dict, rules: list[dict] | None = None):
        self.version: str = data["version"]
        self.dialect: str = data.get("dialect", "bigquery")
        if self.dialect not in DIALECTS:
            raise ValueError(
                f"qlsc-parse resolves {', '.join(sorted(DIALECTS))} SQL; the catalog is {self.dialect}"
            )
        self.tables: dict[str, dict] = data["tables"]
        self.aliases: dict[str, str] = data.get("aliases", {})
        self.shard_families: set[str] = set(data.get("shard_families", []))
        self.rules = [(re.compile(r["pattern"]), r["replace"]) for r in (rules or data.get("rules", []))]
        # key every table by its canonical name (a Looker PDT generation -> LR_{id}_name)
        canon: dict[str, dict] = {}
        for fqn, t in self.tables.items():
            key = ".".join(self.canonical(*fqn.split(".", 2)))
            if key in canon:
                canon[key] = {**canon[key], "columns": {**canon[key]["columns"], **t["columns"]}}
            else:
                canon[key] = t
        self.tables = canon
        nested: dict = {}
        self.colcase: dict[str, dict[str, str]] = {}
        for fqn, t in self.tables.items():
            if not t["columns"]:
                continue
            p, d, n = fqn.split(".", 2)
            nested.setdefault(p, {}).setdefault(d, {})[n] = t["columns"]
            self.colcase[fqn] = {c.lower(): c for c in t["columns"]}
        self.schema = MappingSchema(nested, dialect=self.dialect)

    @classmethod
    def load(cls, path: str | Path, rules: list[dict] | None = None) -> Catalog:
        return cls(json.loads(Path(path).read_text()), rules)

    # ------------------------------------------------------------------ names

    def canonical(self, project: str, dataset: str, name: str) -> tuple[str, str, str]:
        """Physical -> logical dataset, volatile identifiers, shards -> wildcard table."""
        home = self.aliases.get(f"{project}.{dataset}")
        if home:
            project, dataset = home.split(".", 1)
        for rx, rep in self.rules:
            name = rx.sub(rep, name)
        if "_" in name:
            head, _, tail = name.rpartition("_")
            if SHARD_SUFFIX.match(tail) and f"{project}.{dataset}.{head}_" in self.shard_families:
                name = f"{head}_*"
        return project, dataset, name

    def canonicalize_tables(self, tree: exp.Expression, default_project: str | None = None) -> None:
        """Rewrite every qualified table reference in place to its canonical name."""
        for t in tree.find_all(exp.Table):
            if not t.args.get("db") or is_system(t):
                continue
            project = t.catalog or default_project
            if not project:
                continue
            p, d, n = self.canonical(project, t.db, t.name)
            t.set("catalog", exp.to_identifier(p, quoted=True))
            t.set("db", exp.to_identifier(d, quoted=True))
            t.set("this", exp.to_identifier(n, quoted=True))

    # ---------------------------------------------------------------- lookups

    def get(self, fqn: str) -> dict | None:
        return self.tables.get(fqn)

    def column(self, fqn: str, name: str) -> str | None:
        """Catalog spelling of a column, or None if the table lacks it."""
        cc = self.colcase.get(fqn)
        return cc.get(name.lower()) if cc is not None else None


def is_system(t: exp.Table) -> bool:
    return any(s in p.upper() for p in (t.catalog, t.db, t.name) if p for s in SYSTEM_PARTS)


def fqn(t: exp.Table) -> str:
    return ".".join(p for p in (t.catalog, t.db, t.name) if p)

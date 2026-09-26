"""Building the catalog snapshot: the connector's physical tables -> logical names, shard families,
canonical identifiers. The example's snapshot came from the pre-connector extract, so rebuilding it
from its own physical tables must give the same version hash."""

from __future__ import annotations

import json

import pytest
from conftest import EXAMPLE

from qlsc.extract import build_catalog


def physical_from(cat: dict) -> dict:
    """Invert a snapshot back to what a connector returns."""
    deployed = {logical: phys for phys, logical in cat["aliases"].items()}
    project = next(iter(cat["aliases"])).split(".", 1)[0]
    tables = {}
    for fqn, t in cat["tables"].items():
        ds = deployed[fqn.rsplit(".", 1)[0]].split(".", 1)[1]
        columns = {
            c: typ for c, typ in t["columns"].items() if c != "_TABLE_SUFFIX" or t["kind"] != "WILDCARD"
        }
        entry = {
            "type": {"TABLE": "BASE TABLE"}.get(t["kind"], t["kind"]),
            "columns": columns,
            "partition": t["partition"],
            "cluster": t["cluster"],
        }
        if t.get("view_sql"):
            entry["view_sql"] = t["view_sql"]
        for name in t.get("shards") or t.get("physical") or [fqn.rsplit(".", 1)[1]]:
            tables[(ds, name)] = (
                {**entry, "partition": None, "cluster": []} if t["kind"] == "WILDCARD" else entry
            )
    return {"source": cat["source"], "project": project, "tables": tables, "aliases": cat["aliases"]}


def test_rebuilding_the_example_snapshot_gives_the_same_version():
    path = EXAMPLE / "work" / "catalog.json"
    if not path.exists():
        pytest.skip("no extracted catalog in the example's work directory")
    cat = json.loads(path.read_text())
    rebuilt = build_catalog(physical_from(cat), cat["rules"], "BigQuery", "bigquery")
    assert rebuilt["version"] == cat["version"]
    assert rebuilt["tables"] == cat["tables"]


def test_shards_and_volatile_names():
    physical = {
        "source": "test",
        "project": "p",
        "aliases": {"p.fnb_raw": "bank-raw.raw"},
        "tables": {
            ("fnb_raw", "events_20260101"): {
                "type": "BASE TABLE",
                "columns": {"a": "INT64"},
                "partition": None,
                "cluster": [],
            },
            ("fnb_raw", "events_20260102"): {
                "type": "BASE TABLE",
                "columns": {"b": "INT64"},
                "partition": None,
                "cluster": [],
            },
            ("fnb_raw", "backup_20250211"): {
                "type": "BASE TABLE",
                "columns": {"a": "INT64"},
                "partition": None,
                "cluster": [],
            },
            ("fnb_raw", "LR_6ABCDEF12345_orders"): {
                "type": "BASE TABLE",
                "columns": {},
                "partition": None,
                "cluster": [],
            },
        },
    }
    rules = [{"pattern": "^LR_[0-9A-Z]{10,30}_", "replace": "LR_{id}_"}]
    cat = build_catalog(physical, rules, "BigQuery", "bigquery")
    assert set(cat["tables"]) == {
        "bank-raw.raw.events_*",
        "bank-raw.raw.backup_20250211",
        "bank-raw.raw.LR_{id}_orders",
    }
    assert cat["tables"]["bank-raw.raw.events_*"]["shards"] == ["events_20260101", "events_20260102"]
    assert cat["tables"]["bank-raw.raw.LR_{id}_orders"]["physical"] == ["LR_6ABCDEF12345_orders"]
    assert cat["dialect"] == "bigquery"

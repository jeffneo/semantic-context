"""Building the catalog snapshot: the connector's physical tables -> logical names, shard families,
canonical identifiers."""

from __future__ import annotations

from qlsc.extract import build_catalog


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


def test_a_pdts_generations_are_ordered_by_when_they_were_made():
    """physical_sql reads a Looker PDT's newest generation: the last made, whatever its id says."""
    table = lambda created: {"type": "BASE TABLE", "columns": {"a": "INT64"}, "partition": None,
                             "cluster": [], "created": created}  # fmt: skip
    physical = {
        "source": "test",
        "project": "p",
        "aliases": {"p.fnb_scratch": "bank-an.scratch"},
        "tables": {
            ("fnb_scratch", "LR_ZZZZZZZZZZ12_daily"): table("2026-06-01T00:00:00"),  # the older, sorts last
            ("fnb_scratch", "LR_AAAAAAAAAA12_daily"): table("2026-06-02T00:00:00"),
        },
    }
    rules = [{"pattern": "^LR_[0-9A-Z]{10,30}_", "replace": "LR_{id}_"}]
    cat = build_catalog(physical, rules, "BigQuery", "bigquery")
    assert cat["tables"]["bank-an.scratch.LR_{id}_daily"]["physical"][-1] == "LR_AAAAAAAAAA12_daily"

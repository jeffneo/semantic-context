"""The pure pieces of the method: identity-preserving joins and lineage, naming, table ranking, and
what ask --cypher gives the LLM and reads back from Virtual Graph."""

from __future__ import annotations

import datetime as dt

from qlsc.joins import DSU, joins_identity, keeps_identity
from qlsc.names import canonical_table, short
from qlsc.navigate import calendar, external_sql, model_slice, round_robin
from qlsc_parse.catalog import Catalog


def test_identity_joins():
    assert joins_identity([{"wraps": [], "vias": ["direct", "direct"]}])
    assert joins_identity([{"wraps": ["CAST<STRING>", "LPAD"], "vias": ["direct", "rename"]}])
    assert joins_identity([{"wraps": ["ARRAY_AGG", "OFFSET"], "vias": ["aggregate", "direct"]}])
    assert not joins_identity([{"wraps": ["DATE_TRUNC"], "vias": ["direct", "direct"]}])
    assert not joins_identity([{"wraps": [], "vias": ["expression", "direct"]}])


def test_identity_lineage():
    cols = {"a.id": {"type": "STRING"}, "a.amount": {"type": "NUMERIC"}}
    assert keeps_identity({"a": "a.id", "kinds": ["rename"], "fns": []}, cols)
    assert keeps_identity(
        {"a": "a.id", "kinds": ["expression"], "fns": ["MAX"]}, cols
    )  # MAX(user_id) is a user id
    assert not keeps_identity(
        {"a": "a.amount", "kinds": ["expression"], "fns": ["MAX"]}, cols
    )  # a new measure
    assert not keeps_identity({"a": "a.id", "kinds": ["passthrough"], "fns": [], "control": True}, cols)


def test_disjoint_sets():
    d = DSU()
    d.union("b", "a")
    d.union("c", "b")
    assert d.find("c") == d.find("a") == "a"
    assert d.find("z") == "z"


def test_canonical_names():
    cat = Catalog(
        {
            "version": "t",
            "tables": {},
            "aliases": {"phys.fnb_raw": "bank-raw.raw"},
            "shard_families": ["bank-raw.raw.events_"],
            "rules": [{"pattern": "^LR_[0-9A-Z]{10,30}_", "replace": "LR_{id}_"}],
        }
    )
    assert canonical_table(cat, "phys.fnb_raw.accounts") == "bank-raw.raw.accounts"
    assert canonical_table(cat, "bank-raw.raw.events_20260105") == "bank-raw.raw.events_*"
    assert canonical_table(cat, "bank-raw.raw.LR_6ABCDEF12345_orders") == "bank-raw.raw.LR_{id}_orders"
    assert short("bank-dw.dw_core.dim_account") == "dw_core.dim_account"


def test_round_robin_gives_every_group_a_turn():
    t = lambda groups, used, frozen=False: {
        "groups": set(groups),
        "used": used,
        "frozen": frozen,
        "cols": {"c"},
    }
    tables = {"hub": t("AB", 30), "a2": t("A", 10), "b1": t("B", 5), "old": t("A", 50, frozen=True)}
    # usage alone would take hub, a2, b1 before old; round robin: A's best, then B's best not yet taken
    assert round_robin(["A", "B"], tables, 2) == ["hub", "b1"]
    assert round_robin(["A", "B"], tables, 4)[-1] == "old"  # frozen tables go last


def test_model_slice_is_the_labels_and_one_hop():
    node = lambda label: {"label": label, "table": label.lower(), "properties": [], "key": [{"column": "id"}]}
    rel = lambda ty, a, b: {"label": ty, "start": {"targetEntity": a}, "end": {"targetEntity": b}}
    schema = {
        "entities": {
            "nodes": [node(x) for x in ("Account", "Call", "Customer", "Site")],
            "relationships": [
                rel("OWNED_BY", "Account", "Customer"),
                rel("RECEIVED_FROM", "Call", "Customer"),
                rel("SERVICED_AT", "Call", "Site"),
            ],
        }
    }
    nodes, rels = model_slice(schema, ["Call"])
    assert [n["label"] for n in nodes] == ["Call", "Customer", "Site"]  # the cohort's first, then one hop
    assert [r["label"] for r in rels] == ["RECEIVED_FROM", "SERVICED_AT"]  # not Account's, two hops away


def test_external_sql_reads_every_external_operator():
    op = lambda kind, details="", children=(): {
        "operatorType": kind,
        "args": {"Details": details},
        "children": list(children),
    }
    plan = op("ProduceResults@neo4j", "n", [op("Projection@neo4j", "n", [op("External@neo4j", "SELECT 1")])])
    assert external_sql(plan) == ["SELECT 1"]


def test_calendar_periods():
    c = calendar(dt.date(2026, 9, 26))
    assert "last quarter: 2026-04-01 to 2026-06-30" in c
    assert "last month: 2026-08-01 to 2026-08-31" in c.lower()
    assert "last year: 2025-01-01 to 2025-12-31" in c
    assert "last quarter: 2025-10-01 to 2025-12-31" in calendar(dt.date(2026, 1, 15))

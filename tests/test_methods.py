"""The pure pieces of the method: identity-preserving joins and lineage, naming, table ranking."""

from __future__ import annotations

from qlsc.joins import DSU, joins_identity, keeps_identity
from qlsc.names import canonical_table, short
from qlsc.navigate import round_robin
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

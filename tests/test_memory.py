"""Memory's context compiler, without a database (plans/2026-09-27-agentic-memory.md, phase 1)."""

from __future__ import annotations

import datetime as dt

from qlsc import entitle, memory

NODES = {
    "Customer": {"table": "dim_customer", "key": "customer_key", "partition": None,
                 "props": {"customer_key": "INTEGER", "segment": "STRING"}},
    "Account": {"table": "dim_account", "key": "account_key", "partition": None,
                "props": {"account_key": "INTEGER", "product_code": "STRING"}},
    "Product": {"table": "dim_product", "key": "product_code", "partition": None,
                "props": {"product_code": "STRING"}},
    "Txn": {"table": "fct_txn", "key": "txn_id", "partition": "post_date",
            "props": {"txn_id": "STRING", "post_date": "DATE", "amount": "FLOAT"}},
    "Merchant": {"table": "dim_merchant", "key": "merchant_id", "partition": None,
                 "props": {"merchant_id": "STRING"}},
}  # fmt: skip
RELS = [
    {"type": "OWNED_BY", "start": "Account", "end": "Customer"},
    {"type": "CONTAINS", "start": "Account", "end": "Product"},
    {"type": "MADE_BY", "start": "Txn", "end": "Customer"},
    {"type": "AT", "start": "Txn", "end": "Merchant"},
    {"type": "CHARGED_TO", "start": "Txn", "end": "Account"},
]
M = memory.Model("p.graph", NODES, RELS, {})


def test_the_template_is_the_neighbourhood_then_its_dimensions():
    reads = memory.template(M, "Customer", hops=2)
    assert [(r.hop, r.name) for r in reads] == [
        (0, "Customer"),
        (1, "Customer<-MADE_BY-Txn"),
        (1, "Customer<-OWNED_BY-Account"),
        (2, "Txn-AT->Merchant"),
        (2, "Txn-CHARGED_TO->Account"),
        (2, "Account-CONTAINS->Product"),
    ]
    txn = reads[1]
    assert txn.inward and txn.window == "post_date"  # the many side, windowed by its partition
    assert reads[3].via_window == "post_date"  # keyed on windowed facts: their partitions only
    assert [r.name for r in memory.template(M, "Customer", hops=1)][-1] == "Customer<-OWNED_BY-Account"


def test_each_relationship_is_read_once():
    reads = memory.template(M, "Account", hops=3)
    types = [r.type for r in reads if r.type]
    assert len(types) == len(set(types))
    # from an account: its customer, product and charges; then the charges' merchants
    assert {r.name for r in reads if r.hop == 2} == {"Txn-AT->Merchant", "Txn-MADE_BY->Customer"}


def test_the_same_read_over_either_target():
    r = memory.template(M, "Customer", hops=2)[1]
    vg, mem = memory.cypher(M, r), memory.cypher(M, r, memory=True)
    assert "n.`post_date` >= $since" in vg and "LIMIT $limit" in vg and "$source" not in vg
    assert mem.startswith("MATCH (n:`Txn` {source: $source})-[x:`MADE_BY`]->(v:`Customer` {source: $source})")
    assert "x.holds_until > $now" in mem and "n.holds_until > $now" in mem
    # the rest is the same read: same filter, order and limit
    assert vg.split("RETURN")[1] == mem.split("RETURN")[1]
    # signed for the pass-through, the predicate goes in its WHERE, over all of it
    assert "WHERE $qlsc_principal IS NOT NULL AND (v.`customer_key` IN $keys" in entitle.signed(vg)


def test_freshness_from_the_write_cadence():
    daily = [f"2026-04-{d:02d}" for d in range(1, 31)]
    monthly = ["2026-04-01", "2026-05-01", "2026-06-01"]
    assert memory.cadence_days(daily) == 1 and memory.cadence_days(monthly) == 30.5
    assert memory.cadence_days(["2026-04-01"]) is None and memory.cadence_days(None) is None
    at = dt.datetime(2026, 9, 28, 12, tzinfo=dt.UTC)
    s = {"memory": {"unknown_hold_days": 1}}
    assert memory.holds_until(s, {"write_days": daily}, at) == at + dt.timedelta(days=1)
    assert memory.holds_until(s, {"write_days": monthly}, at) == at + dt.timedelta(days=30.5)
    assert memory.holds_until(s, {"write_days": None, "frozen": True}, at) is None  # holds for good
    assert memory.holds_until(s, {"write_days": None}, at) == at + dt.timedelta(days=1)


def test_a_changed_template_is_a_different_context():
    p = {"window_days": 90, "cap": 200, "properties": "used"}
    reads = memory.template(M, "Customer", hops=2)
    assert memory.digest(M, reads, p) == memory.digest(M, reads, dict(p))
    assert memory.digest(M, reads, p) != memory.digest(M, reads, p | {"window_days": 30})
    assert memory.digest(M, reads, p) != memory.digest(M, reads[:-1], p)


def test_identifiers_only():
    try:
        memory.ident("Customer`) DETACH DELETE (n")
    except memory.Unsupported:
        pass
    else:
        raise AssertionError("expected Unsupported")

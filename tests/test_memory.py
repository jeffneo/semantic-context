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


def test_on_the_virtual_graph_a_relationship_is_read_by_its_key_column():
    rels = [r | {"fk": {"MADE_BY": "customer_key", "AT": "merchant_id"}.get(r["type"])} for r in RELS]
    m = memory.Model("p.graph", NODES, rels, {})
    reads = {r.name: r for r in memory.template(m, "Customer", hops=2)}
    into, out = reads["Customer<-MADE_BY-Txn"], reads["Txn-AT->Merchant"]
    # into the anchor: the facts by their own column, windowed and capped; no traversal to join
    vg = memory.cypher(m, into)
    assert vg.startswith("MATCH (n:`Txn`)\nWHERE n.`customer_key` IN $keys\n  AND n.`post_date` >= $since")
    assert "RETURN n.`customer_key` AS _via" in vg and vg.endswith("LIMIT $limit") and "-[x:" not in vg
    # out of the facts: the dimensions by key (the keys the facts hold)
    assert (
        memory.cypher(m, out)
        == "MATCH (n:`Merchant`)\nWHERE n.`merchant_id` IN $keys\nRETURN n.`merchant_id` AS `merchant_id`"
    )
    # memory has the relationships, and traverses them; a read without a key column traverses everywhere
    assert "-[x:`MADE_BY`]->" in memory.cypher(m, into, memory=True)
    assert "-[x:`CHARGED_TO`]->" in memory.cypher(m, reads["Txn-CHARGED_TO->Account"])


def test_a_key_column_is_one_of_the_start_nodes_own_table():
    nodes = {
        "Txn": {"key": "txn_id", "columns": {"txn_id": "txn_id", "cust": "customer_key"}, "readable": {"txn_id": 1, "cust": 1}},
        "Customer": {"key": "customer_key", "columns": {"customer_key": "customer_key"}, "readable": {"customer_key": 1}},
    }  # fmt: skip
    r = {"table": "fct_txn", "start": {"targetEntity": "Txn", "keys": [{"nodeColumn": "txn_id", "relationshipColumn": "txn_id"}]},
         "end": {"targetEntity": "Customer", "keys": [{"nodeColumn": "customer_key", "relationshipColumn": "customer_key"}]}}  # fmt: skip
    views = {"fct_txn": "Txn", "link": "Link"}
    assert memory.foreign_key(r, nodes, views) == "cust"  # the property, by its column
    assert memory.foreign_key(r | {"table": "link"}, nodes, views) is None  # held in another table
    hidden = nodes | {"Txn": nodes["Txn"] | {"readable": {"txn_id": 1}}}
    assert memory.foreign_key(r, hidden, views) is None  # a column the reader may not read


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


def test_a_row_policied_node_needs_the_readers_own_read():
    """Customer's table has a row policy: a customer is read from memory only if the reader's own step READ
    it and that read still holds, and so is a relationship to one; a purchase's merchant is anyone's."""
    import dataclasses

    m = dataclasses.replace(M, reader="p@x", policied={"Customer"})
    reads = {r.name: r for r in memory.template(m, "Customer", hops=2)}
    mine = "(:Step {owner: $by})-[r:READ]->"
    assert f"EXISTS {{ {mine}(n) WHERE r.holds_until > $now }}" in memory.cypher(
        m, reads["Customer"], memory=True
    )
    made_by = memory.cypher(m, reads["Customer<-MADE_BY-Txn"], memory=True)
    assert f"{mine}(v)" in made_by and f"{mine}(n)" not in made_by
    assert "Step" not in memory.cypher(m, reads["Txn-AT->Merchant"], memory=True)
    # the virtual graph's read is the same whoever reads: the warehouse applies their rules
    assert memory.cypher(m, reads["Customer<-MADE_BY-Txn"]) == memory.cypher(
        M, reads["Customer<-MADE_BY-Txn"]
    )


def test_an_asks_fingerprint_has_no_values():
    from qlsc.converse import fingerprint

    request = {
        "fits": True,
        "reason": "…",
        "measures": [{"alias": "spend", "aggregate": "SUM", "column": "dw.fct_txn.amount"}],
        "filters": [{"column": "dw.fct_txn.customer_key", "op": "=", "value": "8322097816940277129"}],
        "period": {"column": "dw.fct_txn.post_date", "from": "2026-04-01", "to": "2026-06-30"},
        "limit": 10,
    }
    a = {"request": request, "writer": "compiled", "route": "sql"}
    other = request | {"filters": [{"column": "dw.fct_txn.customer_key", "op": "=", "value": "42"}],
                       "period": {"column": "dw.fct_txn.post_date", "from": "2025-01-01", "to": "2025-03-31"}}  # fmt: skip
    f = fingerprint(a, [])
    assert "8322097816940277129" not in f and "2026" not in f and "spend" not in f
    assert f == fingerprint(a | {"request": other}, [])  # the same kind of ask, whoever it was for
    assert fingerprint({"route": "cypher", "writer": "free"}, ["b", "a"]) == "ask cypher over a, b"


def test_a_virtual_graph_label_never_takes_one_memory_reserves():
    from qlsc.virtualize import fallback_label

    assert fallback_label("p.dw_web.fct_web_events") == "WebEvent"
    assert fallback_label("p.dw_ops.tasks") == "DwOpsTask"  # Task is memory's own
    assert fallback_label("p.dw_core.dim_customer") == "Customer"
    assert {"Message", "Decision", "Skill", "Table"} <= memory.RESERVED_LABELS


def test_the_computations_a_request_used():
    from qlsc.converse import computation_ids

    request = {
        "measures": [{"computation": "c1"}, {"computation": ""}],
        "blocks": [{"filters": [{"computation": "c2"}]}],
    }
    assert computation_ids(request) == ["c1", "c2"]


def test_the_memory_route_guards_every_node_and_relationship():
    """Phase 5: the compiler's Cypher, run on memory, carries memory's conditions: its source, facts that
    still hold, and a row-policied node only if the reader's own step read it."""
    import dataclasses

    import sqlglot

    m = dataclasses.replace(M, reader="p@x", policied={"Customer"})
    g = memory.Guard(m)
    assert g.node("c", "Customer")[-1] == (
        "EXISTS { (:Step {owner: $by})-[seen:READ]->(c) WHERE seen.holds_until > $now }"
    )
    assert len(g.node("t", "Txn")) == 2 and g.relationship("r0") == [
        "(r0.holds_until IS NULL OR r0.holds_until > $now)"
    ]
    value = lambda sql: memory.literal_value(sqlglot.parse_one(sql, read="bigquery").expression)
    assert value("x.k = -9222608688654483010") == "-9222608688654483010"
    assert value("x.d >= DATE '2026-04-01'") == "2026-04-01" and value("x.s = 'KS'") == "KS"

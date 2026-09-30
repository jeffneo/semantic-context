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
RELS = [  # each a column of its start node's table (fk), as qlsc virtualize writes them
    {"type": "OWNED_BY", "start": "Account", "end": "Customer", "fk": "customer_key"},
    {"type": "CONTAINS", "start": "Account", "end": "Product", "fk": "product_code"},
    {"type": "MADE_BY", "start": "Txn", "end": "Customer", "fk": "customer_key"},
    {"type": "AT", "start": "Txn", "end": "Merchant", "fk": "merchant_id"},
    {"type": "CHARGED_TO", "start": "Txn", "end": "Account", "fk": "account_key"},
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
    by = {r.name: r for r in reads}
    txn = by["Customer<-MADE_BY-Txn"]
    assert txn.inward and txn.window == "post_date"  # the many side, windowed by its partition
    assert not by["Txn-AT->Merchant"].inward and by["Txn-AT->Merchant"].window is None  # to-one
    assert [r.name for r in memory.template(M, "Customer", hops=1)][-1] == "Customer<-OWNED_BY-Account"


def test_each_relationship_is_read_once():
    reads = memory.template(M, "Account", hops=3)
    types = [r.type for r in reads if r.type]
    assert len(types) == len(set(types))
    # from an account: its customer, product and charges; then the charges' merchants
    assert {r.name for r in reads if r.hop == 2} == {"Txn-AT->Merchant", "Txn-MADE_BY->Customer"}


def guarded(q: str, g: memory.Guard, v: str, label: str) -> bool:
    return all(c in q for c in g.node(v, label))


def test_the_same_read_over_either_target():
    r = memory.template(M, "Customer", hops=2)[1]
    vg, mem = memory.cypher(M, r), memory.cypher(M, r, memory=True)
    g = memory.Guard(M)
    # over memory, the read is guarded; the virtual graph's is not
    assert guarded(mem, g, "n", "Txn") and "$source" not in vg and "$now" not in vg
    # the rest is the same read: same filter, order and limit
    assert vg.split("RETURN")[1] == mem.split("RETURN")[1]
    assert mem.startswith(vg.split("\nRETURN")[0])
    # signed for the pass-through, the predicate goes in its WHERE, over all of it
    assert "WHERE $qlsc_principal IS NOT NULL AND (n.`customer_key` IN $keys" in entitle.signed(vg)


def test_every_read_is_a_labels_nodes_by_a_property():
    reads = {r.name: r for r in memory.template(M, "Customer", hops=2)}
    into, out = reads["Customer<-MADE_BY-Txn"], reads["Txn-AT->Merchant"]
    # the anchor by its key
    assert memory.cypher(M, reads["Customer"]).startswith(
        "MATCH (n:`Customer`)\nWHERE n.`customer_key` IN $keys"
    )
    # into the anchor: the facts by their own column, windowed and capped; no traversal to join
    vg = memory.cypher(M, into)
    assert vg.startswith("MATCH (n:`Txn`)\nWHERE n.`customer_key` IN $keys\n  AND n.`post_date` >= $since")
    assert "RETURN n.`customer_key` AS _via" in vg and vg.endswith("LIMIT $limit")
    # out of the facts: the dimensions by key (the keys the facts hold)
    assert (
        memory.cypher(M, out)
        == "MATCH (n:`Merchant`)\nWHERE n.`merchant_id` IN $keys\nRETURN n.`merchant_id` AS `merchant_id`"
    )
    assert not any("-[" in memory.cypher(M, r, mem) for r in reads.values() for mem in (False, True))


def test_a_read_into_the_anchors_is_ordered_by_anchor_then_the_most_recent():
    r = memory.template(M, "Customer", hops=2)[1]
    for q in (memory.cypher(M, r), memory.cypher(M, r, memory=True)):  # so a batch's is read in pages
        assert q.endswith("ORDER BY n.`customer_key`, n.`post_date` DESC, n.`txn_id`\nLIMIT $limit")


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
    p = {"window_quarters": 1, "cap": 200, "properties": "used"}
    reads = memory.template(M, "Customer", hops=2)
    assert memory.digest(M, reads, p) == memory.digest(M, reads, dict(p))
    assert memory.digest(M, reads, p) != memory.digest(M, reads, p | {"window_quarters": 0})
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
    it and that read still holds; a purchase's merchant is anyone's."""
    import dataclasses

    m = dataclasses.replace(M, reader="p@x", policied={"Customer"})
    g = memory.Guard(m)
    assert any("Step {owner: $by}" in c for c in g.node("n", "Customer"))
    assert not any("Step" in c for c in g.node("n", "Merchant"))
    reads = {r.name: r for r in memory.template(m, "Customer", hops=2)}
    assert guarded(memory.cypher(m, reads["Customer"], memory=True), g, "n", "Customer")
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


def test_the_memory_route_guards_every_node():
    """Phase 5: the compiler's Cypher, run on memory, carries memory's conditions on every node: its source,
    facts that still hold, and a row-policied node only if the reader's own step read it. A relationship
    holds as long as its nodes do."""
    import dataclasses

    import sqlglot

    m = dataclasses.replace(M, reader="p@x", policied={"Customer"})
    g = memory.Guard(m)
    assert g.node("c", "Customer")[-1] == (
        "EXISTS { (:Step {owner: $by})-[seen:READ]->(c) WHERE seen.holds_until > $now }"
    )
    assert len(g.node("t", "Txn")) == 2
    value = lambda sql: memory.literal_value(sqlglot.parse_one(sql, read="bigquery").expression)
    assert value("x.k = -9222608688654483010") == "-9222608688654483010"
    assert value("x.d >= DATE '2026-04-01'") == "2026-04-01" and value("x.s = 'KS'") == "KS"


class FakeVirtualGraph:
    """A virtual graph over a few rows: it answers the reads memory.cypher writes (a label's nodes by a
    property), ordered and limited as they ask."""

    def __init__(self, m: memory.Model, rows: dict[str, list[dict]]):
        self.m, self.data = m, rows
        self.queries = 0

    def rows(self, q: str, keys: list, since, limit: int, **_) -> list[dict]:
        import re

        self.queries += 1
        q = q.replace("$qlsc_principal IS NOT NULL AND (", "")  # signed for the pass-through
        window = re.search(r"n\.`(\w+)` >= \$since", q)
        inside = lambda r: not window or r[window.group(1)] >= since
        label, prop = re.match(r"MATCH \(n:`(\w+)`\)\nWHERE n\.`(\w+)` IN \$keys", q).groups()
        got = [dict(r) for r in self.data[label] if r[prop] in keys and inside(r)]
        if "_via" not in q:
            return got
        key, w = self.m.key(label), window.group(1) if window else None
        got.sort(key=lambda r: (r[prop], *([-r[w].toordinal()] if w else []), r[key]))
        return [r | {"_via": r[prop]} for r in got][:limit]


def test_a_batch_gives_each_anchor_the_context_it_gets_alone(tmp_path):
    import datetime as dt

    d = lambda day: dt.date(2026, 6, day)
    nodes = {k: v | {"props": dict(v["props"])} for k, v in NODES.items()}
    nodes["Txn"]["props"] |= {"customer_key": "INTEGER", "merchant_id": "STRING", "account_key": "INTEGER"}
    nodes["Account"]["props"] |= {"customer_key": "INTEGER"}
    m = memory.Model("p.graph", nodes, RELS, {})
    data = {
        "Customer": [{"customer_key": k, "segment": "mass"} for k in (1, 2, 3)],
        "Account": [{"account_key": 10, "customer_key": 1, "product_code": "CHK"},
                    {"account_key": 20, "customer_key": 2, "product_code": "SAV"}],
        "Product": [{"product_code": "CHK"}, {"product_code": "SAV"}],
        "Merchant": [{"merchant_id": "m1"}, {"merchant_id": "m2"}],
        "Txn": [  # customer 1 has three purchases (over the cap of two), customer 2 one, customer 3 none
            {"txn_id": "a", "customer_key": 1, "post_date": d(1), "amount": 1.0, "merchant_id": "m1", "account_key": 10},
            {"txn_id": "b", "customer_key": 1, "post_date": d(3), "amount": 2.0, "merchant_id": "m2", "account_key": 10},
            {"txn_id": "c", "customer_key": 1, "post_date": d(2), "amount": 3.0, "merchant_id": "m1", "account_key": 10},
            {"txn_id": "e", "customer_key": 2, "post_date": d(2), "amount": 4.0, "merchant_id": "m2", "account_key": 20},
        ],
    }  # fmt: skip

    class Settings(dict):
        work = tmp_path  # the pass-through's key

    s = Settings(memory={"cap": 2, "keys_per_read": 1000, "workers": 2, "window_quarters": 1},
                 navigate={"today": "2026-07-01"}, entitlements={"token_seconds": 300})  # fmt: skip
    reads, now = memory.template(m, "Customer", hops=2), dt.datetime(2026, 7, 1, tzinfo=dt.UTC)
    vg = FakeVirtualGraph(m, data)
    batch = memory.run_batch(s, m, reads, [1, 2, 3, 99], vg, False, now)
    in_batch = vg.queries
    for k in (1, 2, 3, 99):
        alone = memory.run_reads(s, m, reads, k, FakeVirtualGraph(m, data), False, now)
        assert batch[k].nodes == alone.nodes and batch[k].edges == alone.edges, k
        assert [(x["read"], x["rows"], x["capped"]) for x in batch[k].reads] == [
            (x["read"], x["rows"], x["capped"]) for x in alone.reads
        ]
    one = batch[1]
    assert one.capped() == ["Customer<-MADE_BY-Txn"]  # the cap is the customer's own
    assert {k for lb, k in one.nodes if lb == "Txn"} == {"b", "c"}  # its two most recent
    assert batch[2].capped() == [] and ("Txn", "e") in batch[2].nodes
    assert not batch[99].nodes  # no such customer: an empty context
    assert in_batch < 4 * len(reads)  # read together, not once per customer

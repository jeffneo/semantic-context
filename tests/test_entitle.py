"""The entitlement gateway's rules, without a warehouse (plans/2026-09-27-entitlements.md)."""

from __future__ import annotations

from qlsc import entitle

ALLOW = entitle.Allowlist(
    principal="qlsc-marketing@p.iam.gserviceaccount.com",
    tables={"p.dw.dim_customer", "p.dw.fct_txn"},
    hidden={("p.dw.dim_customer", "full_name")},
    tagged={("p.dw.dim_customer", "full_name"), ("p.dw.fct_txn", "card_token")},
    rows={"p.dw.dim_customer"},
)


def test_columns_tables_and_values():
    assert ALLOW.column("p.dw.dim_customer", "segment")
    assert not ALLOW.column("p.dw.dim_customer", "full_name")  # its policy tag isn't theirs
    assert not ALLOW.column("p.dw.fct_calls", "call_id")  # the table isn't theirs
    assert ALLOW.column("p.dw.fct_txn", "card_token") and not ALLOW.shown("p.dw.fct_txn", "card_token")


def test_a_computation_only_over_what_they_read():
    ok = {"tables": ["p.dw.fct_txn"], "expression": "SUM(fct_txn.amount)", "filters": []}
    other = {"tables": ["p.dw.fct_calls"], "expression": "COUNT(*)", "filters": []}
    hidden = {
        "tables": ["p.dw.dim_customer"],
        "expression": "COUNT(DISTINCT dim_customer.full_name)",
        "filters": [],
    }
    assert entitle.computation_ok(ALLOW, ok)
    assert not entitle.computation_ok(ALLOW, other) and not entitle.computation_ok(ALLOW, hidden)


def test_the_virtual_graph_as_they_may_see_it():
    labels = {"p.dw.dim_customer": "Customer", "p.dw.fct_txn": "Txn", "p.dw.fct_calls": "Call"}
    prop = lambda *cols: [{"name": c, "column": c, "type": "STRING"} for c in cols]
    rel = lambda label, a, b, col: {
        "label": label,
        "start": {"targetEntity": a},
        "end": {"targetEntity": b, "keys": [{"relationshipColumn": col, "nodeColumn": col}]},
    }
    entities = {
        "nodes": [
            {"label": "Customer", "properties": prop("customer_key", "segment", "full_name")},
            {"label": "Txn", "properties": prop("customer_key", "amount")},
            {"label": "Call", "properties": prop("customer_key")},
        ],
        "relationships": [
            rel("MADE_BY", "Txn", "Customer", "customer_key"),
            rel("FROM", "Call", "Customer", "customer_key"),
        ],
    }
    m = entitle.model(ALLOW, entities, labels)
    assert [n["label"] for n in m["nodes"]] == ["Customer", "Txn"]
    assert [x["name"] for x in m["nodes"][0]["properties"]] == ["customer_key", "segment"]
    assert [r["label"] for r in m["relationships"]] == ["MADE_BY"]


def test_a_virtual_graph_that_runs_unsigned_queries_is_refused_a_principal(tmp_path):
    """Without the pass-through, the virtual graph reads as its own identity: nothing is sent on a
    principal's behalf. The estate's own reads still go."""
    from neo4j.exceptions import Neo4jError

    (tmp_path / "virtual").mkdir()
    (tmp_path / "virtual" / "schema.json").write_text('{"entities": {"nodes": [{"label": "Customer"}]}}')

    class Settings(dict):
        work = tmp_path

    class VirtualGraph:
        def __init__(self, enforcing):
            self.enforcing = enforcing

        def rows(self, q, **_):
            if self.enforcing:
                raise Neo4jError._hydrate_neo4j(
                    code="Neo.DatabaseError.General.UnknownError",
                    message="qlsc pass-through: refused, the query carries no principal token",
                )
            return [{"n": 1}]

    for uri, enforcing in (("bolt://plain", False), ("bolt://passthrough", True)):
        s = Settings(virtualize={"neo4j": {"uri": uri}}, entitlements={"token_seconds": 300})
        V = VirtualGraph(enforcing)
        sent, params = entitle.signing(s, None, "MATCH (c:Customer) RETURN c", V)
        assert "$qlsc_principal IS NOT NULL" in sent and params["qlsc_principal"]
        if enforcing:
            assert entitle.signing(s, ALLOW, "MATCH (c:Customer) RETURN c", V)[1]["qlsc_principal"]
        else:
            try:
                entitle.signing(s, ALLOW, "MATCH (c:Customer) RETURN c", V)
            except entitle.Unenforced:
                pass
            else:
                raise AssertionError("signed for a principal on a virtual graph that doesn't enforce it")

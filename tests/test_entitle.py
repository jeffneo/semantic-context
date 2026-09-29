"""The entitlement gateway's rules, without a warehouse (plans/2026-09-27-entitlements.md)."""

from __future__ import annotations

from qlsc import entitle
from qlsc.navigate import answered, pick

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


def test_probes_of_what_virtual_graphs_sql_reads():
    sql = (
        "SELECT `c`.`segment` AS `seg`, count(distinct `c`.`customer_key`) AS `n` "
        "FROM `p`.`fnb_graph`.`fct_card_transactions` AS `unnamed0` "
        "JOIN `p`.`fnb_graph`.`dim_customer` AS `c` ON `c`.`customer_key` = `unnamed0`.`customer_key` "
        "WHERE `c`.`state_code` IN unnest([? /*param_0*/, ?]) GROUP BY `seg` LIMIT ? /*param_1*/"
    )
    assert entitle.probes(sql) == [
        "SELECT `customer_key`, `segment`, `state_code` FROM `p`.`fnb_graph`.`dim_customer` LIMIT 1",
        "SELECT `customer_key` FROM `p`.`fnb_graph`.`fct_card_transactions` LIMIT 1",
    ]


def test_a_refused_cypher_answer_sends_the_router_to_sql():
    cypher = {"writer": "compiled", "cypher": "MATCH (c:Customer) RETURN count(*)", "check": {"sql": []}}
    free_sql = {"writer": "free", "sql": "SELECT 1", "result": {"ok": True}}
    assert answered(cypher) and pick(free_sql, cypher) == "cypher"
    refused = cypher | {"refused": "the warehouse filters the rows of dim_customer per reader"}
    assert not answered(refused) and pick(free_sql, refused) == "sql"

"""The compiler: a typed request -> SQL, deterministically (plans/2026-09-28-compiler.md)."""

from __future__ import annotations

import pytest

from qlsc.compile import Catalogue, Unfit, compile_sql, within

TABLES = {
    "p.dw.fct_txn": {
        "txn_id": "STRING",
        "customer_key": "INT64",
        "amount": "NUMERIC",
        "is_purchase": "BOOL",
        "post_date": "DATE",
        "posted_at": "TIMESTAMP",
    },
    "p.dw.dim_customer": {"customer_key": "INT64", "segment": "STRING", "branch_id": "INT64"},
    "p.dw.dim_branch": {"branch_id": "INT64", "region": "STRING"},
    "p.dw.fct_calls": {"call_id": "STRING", "customer_key": "INT64"},
}
JOINS = [
    {"a": "p.dw.dim_customer", "ac": "customer_key", "b": "p.dw.fct_txn", "bc": "customer_key"},
    {"a": "p.dw.dim_branch", "ac": "branch_id", "b": "p.dw.dim_customer", "bc": "branch_id"},
    {"a": "p.dw.dim_customer", "ac": "customer_key", "b": "p.dw.fct_calls", "bc": "customer_key"},
]
SPEND = {
    "id": "c1",
    "kind": "measure",
    "name": "Card Purchase Spend",
    "expression": "SUM(fct_txn.amount)",
    "filters": ["fct_txn.is_purchase"],
    "tables": ["p.dw.fct_txn"],
}
AFFLUENT = {
    "id": "c2",
    "kind": "population",
    "name": "Affluent",
    "expression": "dim_customer.segment = 'affluent'",
    "filters": [],
    "tables": ["p.dw.dim_customer"],
}
CAT = Catalogue(TABLES, JOINS, {"c1": SPEND, "c2": AFFLUENT})
UNIQUE = {("p.dw.dim_customer", "customer_key"), ("p.dw.dim_branch", "branch_id")}
unique = lambda t, c: (t, c) in UNIQUE


def req(**kw):
    return {
        "fits": True,
        "reason": "",
        "measures": [],
        "dimensions": [],
        "filters": [],
        "period": {},
        "order": [],
        "limit": 0,
    } | kw


def flat(sql: str) -> str:
    return " ".join(sql.split()).replace("( ", "(").replace(" )", ")")


def test_computation_joined_two_hops_with_period():
    sql = flat(
        compile_sql(
            req(
                measures=[{"alias": "spend", "computation": "c1"}],
                dimensions=[
                    {"alias": "region", "column": "dw.dim_branch.region"},
                    {"alias": "month", "column": "dw.fct_txn.post_date", "grain": "month"},
                ],
                filters=[{"computation": "c2"}],
                period={"column": "dw.fct_txn.posted_at", "from": "2026-04-01", "to": "2026-06-30"},
            ),
            CAT,
            unique,
        )
    )
    assert "SUM(fct_txn.amount) AS spend" in sql
    assert (
        "JOIN `p.dw.dim_customer` AS dim_customer ON dim_customer.customer_key = fct_txn.customer_key" in sql
    )
    assert "JOIN `p.dw.dim_branch` AS dim_branch ON dim_branch.branch_id = dim_customer.branch_id" in sql
    assert "DATE_TRUNC(fct_txn.post_date, MONTH) AS month" in sql
    assert "(fct_txn.is_purchase)" in sql and "(dim_customer.segment = 'affluent')" in sql
    assert "DATE(fct_txn.posted_at) >= CAST('2026-04-01' AS DATE)" in sql
    assert "GROUP BY 1, 2" in sql


def test_measures_with_different_filters_share_one_query():
    sql = flat(
        compile_sql(
            req(
                measures=[
                    {"alias": "spend", "computation": "c1"},
                    {"alias": "txns", "aggregate": "COUNT"},
                    {"alias": "share", "ratio_of": ["spend", "txns"]},
                ],
            ),
            CAT,
            unique,
        )
    )
    assert (
        "SUM(CASE WHEN (fct_txn.is_purchase) THEN fct_txn.amount ELSE NULL END) AS spend" in sql
        or "SUM(IF(" in sql
    )
    assert "COUNT(*) AS txns" in sql
    assert "SAFE_DIVIDE(" in sql and "WHERE" not in sql  # the purchase filter belongs to spend only


def test_conditions_are_typed_from_the_column():
    sql = flat(
        compile_sql(
            req(
                measures=[
                    {
                        "alias": "n",
                        "aggregate": "COUNT_DISTINCT",
                        "column": "dw.fct_txn.customer_key",
                        "where": [{"column": "dw.fct_txn.is_purchase", "op": "IS TRUE", "values": []}],
                    }
                ],
                filters=[
                    {"column": "dw.dim_customer.segment", "op": "IN", "values": ["affluent", "private"]},
                    {"column": "dw.fct_txn.amount", "op": ">=", "values": ["100"]},
                ],
            ),
            CAT,
            unique,
        )
    )
    assert "dim_customer.segment IN ('affluent', 'private')" in sql
    assert "fct_txn.amount >= 100" in sql


def test_what_cannot_compile_falls_back():
    with pytest.raises(Unfit, match="doesn't fit|list"):
        compile_sql(req(fits=False, reason="a list of rows"), CAT, unique)
    with pytest.raises(Unfit, match="no column"):
        compile_sql(
            req(measures=[{"alias": "x", "aggregate": "SUM", "column": "dw.fct_txn.nope"}]), CAT, unique
        )
    with pytest.raises(Unfit, match="multiply"):  # calls per customer joined to transactions: a fan-out
        compile_sql(
            req(
                measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_txn.txn_id"}],
                dimensions=[{"alias": "c", "column": "dw.fct_calls.call_id"}],
            ),
            CAT,
            unique,
        )


def test_within_wraps_each_aggregate():
    assert within("COUNT(*)", ["t.a"]) == "COUNT(IF(t.a, 1, NULL))"
    assert within("SAFE_DIVIDE(COUNTIF(t.x), COUNT(*))", ["t.a"]).count("IF(t.a") == 2


def test_an_open_ended_period_and_a_count_of_rows():
    cat = Catalogue(TABLES, JOINS, {})
    sql = flat(
        compile_sql(
            req(
                measures=[{"alias": "calls", "aggregate": "COUNT"}],
                dimensions=[{"alias": "cust", "column": "dw.fct_calls.customer_key"}],
            ),
            cat,
            unique,
        )
    )
    assert "COUNT(*) AS calls FROM `p.dw.fct_calls` AS fct_calls" in sql  # the fact, from the dimension
    sql = flat(
        compile_sql(
            req(
                measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_txn.txn_id"}],
                period={"column": "dw.fct_txn.post_date", "from": "2026-04-15", "to": ""},
            ),
            cat,
            unique,
        )
    )
    assert "fct_txn.post_date >= CAST('2026-04-15' AS DATE)" in sql and "<=" not in sql


def test_conditions_inside_a_measure_stay_inside_it():
    sql = flat(
        compile_sql(
            req(
                measures=[
                    {
                        "alias": "clicks",
                        "aggregate": "COUNT",
                        "where": [{"column": "dw.fct_txn.is_purchase", "op": "IS TRUE", "values": []}],
                    }
                ],
                dimensions=[{"alias": "cust", "column": "dw.fct_txn.customer_key"}],
            ),
            CAT,
            unique,
        )
    )
    assert (
        "COUNT(IF(fct_txn.is_purchase IS TRUE, 1, NULL)) AS clicks" in sql and "WHERE" not in sql
    )  # zeros stay
    assert within("COUNT(DISTINCT t.x)", ["t.a"]) == "COUNT(DISTINCT IF(t.a, t.x, NULL))"

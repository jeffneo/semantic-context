"""The compiler: a typed request -> SQL, deterministically (plans/2026-09-28-compiler.md)."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlglot.executor import env, execute

from qlsc.compile import (
    Catalogue,
    Unfit,
    check,
    compile_cypher,
    compile_sql,
    open_period,
    week_usage,
    weeks,
)

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


# ---- the SQL, run: the compiled queries over a few rows (sqlglot's executor, with BigQuery's functions
# the compiler writes), so the tests say what the answer is, not how the SQL is spelled

D = dt.date
ROWS_ = {
    "fct_txn": [  # customer 3 has no customer row; customer 4 never buys
        {"txn_id": "t1", "customer_key": 1, "amount": 10.0, "is_purchase": True, "post_date": D(2026, 4, 2)},
        {"txn_id": "t2", "customer_key": 1, "amount": 5.0, "is_purchase": False, "post_date": D(2026, 5, 3)},
        {"txn_id": "t3", "customer_key": 2, "amount": 20.0, "is_purchase": True, "post_date": D(2026, 5, 10)},
        {"txn_id": "t4", "customer_key": 3, "amount": 7.0, "is_purchase": True, "post_date": D(2026, 6, 1)},
        {
            "txn_id": "t5",
            "customer_key": 2,
            "amount": 100.0,
            "is_purchase": True,
            "post_date": D(2026, 3, 15),
        },
        {"txn_id": "t6", "customer_key": 4, "amount": 1.0, "is_purchase": False, "post_date": D(2026, 4, 20)},
    ],
    "dim_customer": [
        {"customer_key": 1, "segment": "affluent", "branch_id": 10},
        {"customer_key": 2, "segment": "mass", "branch_id": 20},
        {"customer_key": 4, "segment": "mass", "branch_id": 20},
    ],
    "dim_branch": [{"branch_id": 10, "region": "North"}, {"branch_id": 20, "region": "South"}],
    "fct_calls": [{"call_id": "k1", "customer_key": 1}, {"call_id": "k2", "customer_key": 1}],
    "fct_costs": [
        {"branch_id": 10, "month_start": D(2026, 4, 1), "cost": 50.0},
        {"branch_id": 20, "month_start": D(2026, 4, 1), "cost": 40.0},
    ],  # fmt: skip
}
for r in ROWS_["fct_txn"]:
    r["posted_at"] = dt.datetime.combine(r["post_date"], dt.time(10))


def _trunc(unit, v):
    return {"MONTH": v.replace(day=1), "YEAR": v.replace(month=1, day=1), "DAY": v}[str(unit).upper()]


env.ENV.update(
    SAFEDIVIDE=lambda a, b: None if a is None or not b else a / b,
    DATETRUNC=_trunc,
    DATE=lambda v: v.date() if isinstance(v, dt.datetime) else v,
)


def run(sql: str) -> list[tuple]:
    """The compiled SQL's answer over ROWS_, sorted."""
    got = execute(sql, dialect="bigquery", tables={"p": {"dw": ROWS_}})
    return sorted(got.rows, key=lambda r: tuple((x is None, x) for x in r))


def test_computation_joined_two_hops_with_period():
    """A Computation's measure and population, a dimension two joins away, a month grain, a period on a
    timestamp: the affluent customer's purchases in the quarter, by region and month."""
    sql = compile_sql(
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
    assert run(sql) == [("North", D(2026, 4, 1), 10.0)]


def test_measures_with_different_filters_share_one_query():
    """Spend counts purchases only; the count of transactions counts every one; the share divides them."""
    sql = compile_sql(
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
    assert run(sql) == [(137.0, 6, 137.0 / 6)]


def test_conditions_are_typed_from_the_column():
    sql = compile_sql(
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
                {"column": "dw.fct_txn.amount", "op": ">=", "values": ["10"]},  # a number, as text
            ],
        ),
        CAT,
        unique,
    )
    assert run(sql) == [(1,)]


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


def test_an_open_ended_period_and_a_count_of_rows():
    cat = Catalogue(TABLES, JOINS, {})
    calls = compile_sql(
        req(
            measures=[{"alias": "calls", "aggregate": "COUNT"}],
            dimensions=[{"alias": "cust", "column": "dw.fct_calls.customer_key"}],
        ),
        cat,
        unique,
    )
    assert run(calls) == [(1, 2)]  # a count of rows is of the table the dimension names
    since = compile_sql(
        req(
            measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_txn.txn_id"}],
            period={"column": "dw.fct_txn.post_date", "from": "2026-04-15", "to": ""},
        ),
        cat,
        unique,
    )
    assert run(since) == [(4,)]  # "since April 15": no end


def test_conditions_inside_a_measure_stay_inside_it():
    """ "Count only purchases": a customer with none still shows, with zero."""
    sql = compile_sql(
        req(
            measures=[
                {
                    "alias": "purchases",
                    "aggregate": "COUNT",
                    "where": [{"column": "dw.fct_txn.is_purchase", "op": "IS TRUE", "values": []}],
                }
            ],
            dimensions=[{"alias": "cust", "column": "dw.fct_txn.customer_key"}],
        ),
        CAT,
        unique,
    )
    assert run(sql) == [(1, 1), (2, 2), (3, 1), (4, 0)]


# ---- the wider request, and Cypher from the same plan (plans/2026-09-28-compiler-2.md)

WIDE = TABLES | {
    "p.dw.fct_costs": {"branch_id": "INT64", "month_start": "DATE", "cost": "NUMERIC"},
    "p.dw.fct_balance": {
        "account_key": "INT64",
        "customer_key": "INT64",
        "as_of": "DATE",
        "balance": "NUMERIC",
    },
    "p.lk.LR_{id}_facts": {"customer_key": "INT64", "score": "FLOAT64"},
}
WIDE_JOINS = [
    *JOINS,
    {"a": "p.dw.dim_branch", "ac": "branch_id", "b": "p.dw.fct_costs", "bc": "branch_id"},
    {"a": "p.dw.dim_customer", "ac": "customer_key", "b": "p.dw.fct_balance", "bc": "customer_key"},
    {"a": "p.dw.dim_customer", "ac": "customer_key", "b": "p.lk.LR_{id}_facts", "bc": "customer_key"},
]
LATEST_BAL = {
    "id": "c3",
    "kind": "measure",
    "name": "Latest Balance",
    "expression": "ARRAY_AGG(fct_balance.balance ORDER BY fct_balance.as_of DESC LIMIT 1)[SAFE_OFFSET(0)]",
    "filters": [],
    "grain": ["fct_balance.account_key"],
    "tables": ["p.dw.fct_balance"],
}
SCORE = {
    "id": "c4",
    "kind": "measure",
    "name": "Mean Score",
    "expression": "AVG(`LR_{id}_facts`.score)",
    "filters": [],
    "tables": ["p.lk.LR_{id}_facts"],
}
WIDE_CAT = Catalogue(WIDE, WIDE_JOINS, {"c1": SPEND, "c2": AFFLUENT, "c3": LATEST_BAL, "c4": SCORE})
WIDE_UNIQUE = UNIQUE | {("p.lk.LR_{id}_facts", "customer_key")}
wide_unique = lambda t, c: (t, c) in WIDE_UNIQUE


def test_two_facts_are_two_blocks_joined_on_the_dimensions():
    """Spend (through customers to branches) and cost (by branch) are two facts: each aggregated on its
    own, then joined on the branch, so neither multiplies the other."""
    request = req(
        measures=[
            {"alias": "spend", "computation": "c1"},
            {"alias": "cost", "aggregate": "SUM", "column": "dw.fct_costs.cost"},
            {"alias": "spend_per_cost", "ratio_of": ["spend", "cost"]},
        ],
        dimensions=[{"alias": "branch", "column": "dw.fct_costs.branch_id"}],
        filters=[{"column": "dw.dim_customer.segment", "op": "=", "values": ["affluent"]}],
    )
    with pytest.raises(Unfit, match="filter|multiply"):  # the segment filter can't apply to costs
        compile_sql(request, WIDE_CAT, wide_unique)
    sql = compile_sql(request | {"filters": []}, WIDE_CAT, wide_unique)
    assert run(sql) == [(10, 10.0, 50.0, 0.2), (20, 120.0, 40.0, 3.0)]


def test_a_distinct_count_moves_the_fact_to_the_finer_table():
    sql = flat(
        compile_sql(
            req(
                measures=[
                    {"alias": "n", "aggregate": "COUNT_DISTINCT", "column": "dw.dim_customer.customer_key"}
                ],
                dimensions=[{"alias": "m", "column": "dw.fct_txn.post_date", "grain": "month"}],
            ),
            WIDE_CAT,
            wide_unique,
        )
    )
    assert "FROM `p.dw.fct_txn` AS fct_txn" in sql and "COUNT(DISTINCT dim_customer.customer_key)" in sql
    with pytest.raises(Unfit):  # a SUM over the customers would be multiplied by their transactions
        compile_sql(
            req(
                measures=[{"alias": "n", "aggregate": "SUM", "column": "dw.dim_customer.branch_id"}],
                dimensions=[{"alias": "m", "column": "dw.fct_txn.post_date", "grain": "month"}],
            ),
            WIDE_CAT,
            wide_unique,
        )


def test_a_latest_value_is_summed_per_entity_in_two_steps():
    sql = flat(
        compile_sql(
            req(
                measures=[{"alias": "balance", "computation": "c3"}],
                dimensions=[{"alias": "segment", "column": "dw.dim_customer.segment"}],
            ),
            WIDE_CAT,
            wide_unique,
        )
    )
    assert "per_fct_balance_account_key" in sql and "GROUP BY 1, 2" in sql
    assert "SUM(balance) AS balance" in sql and sql.count("GROUP BY") == 2


def test_having_difference_and_a_list():
    before = {"column": "dw.fct_txn.post_date", "op": "<", "values": ["2026-04-01"]}
    after = {"column": "dw.fct_txn.post_date", "op": ">=", "values": ["2026-04-01"]}
    sql = compile_sql(
        req(
            measures=[
                {"alias": "q1", "aggregate": "SUM", "column": "dw.fct_txn.amount", "where": [before]},
                {"alias": "q2", "aggregate": "SUM", "column": "dw.fct_txn.amount", "where": [after]},
                {"alias": "change", "difference_of": ["q2", "q1"]},
            ],
            dimensions=[{"alias": "cust", "column": "dw.fct_txn.customer_key"}],
            having=[{"alias": "q2", "op": ">", "value": 15}],
        ),
        WIDE_CAT,
        wide_unique,
    )
    assert run(sql) == [(2, 100.0, 20.0, -80.0)]  # only customer 2 bought more than 15 from April
    listing = compile_sql(
        req(
            dimensions=[{"alias": "k", "column": "dw.dim_customer.customer_key"}],
            filters=[{"column": "dw.dim_customer.segment", "op": "=", "values": ["mass"]}],
            order=[{"alias": "k", "desc": False}],
            limit=1,
        ),
        WIDE_CAT,
        wide_unique,
    )
    assert run(listing) == [(2,)]


def test_a_computation_on_a_looker_table_drops_in_under_its_alias():
    """A Looker PDT's name (LR_{id}_facts) isn't an identifier: its alias is, and the Computation's
    expression is rewritten to it."""
    sql = flat(compile_sql(req(measures=[{"alias": "s", "computation": "c4"}]), WIDE_CAT, wide_unique))
    assert "AVG(LR_id_facts.score)" in sql and "AS LR_id_facts" in sql


# The Virtual Graph model over the first catalogue: transactions -> customers -> branches.
LABELS = {"p.dw.fct_txn": "Txn", "p.dw.dim_customer": "Customer", "p.dw.dim_branch": "Branch"}
node = lambda label, table, cols: {
    "label": label,
    "table": table,
    "key": [{"column": cols[0]}],
    "properties": [{"name": c, "column": c, "type": t} for c, t in TABLES[f"p.dw.{table}"].items()],
}
MODEL = {
    "nodes": [
        node("Txn", "fct_txn", ["txn_id"]),
        node("Customer", "dim_customer", ["customer_key"]),
        node("Branch", "dim_branch", ["branch_id"]),
    ],
    "relationships": [
        {
            "label": "MADE_BY",
            "table": "fct_txn",
            "start": {
                "targetEntity": "Txn",
                "keys": [{"nodeColumn": "txn_id", "relationshipColumn": "txn_id"}],
            },
            "end": {
                "targetEntity": "Customer",
                "keys": [{"nodeColumn": "customer_key", "relationshipColumn": "customer_key"}],
            },
        },
        {
            "label": "PREFERS",
            "table": "dim_customer",
            "start": {
                "targetEntity": "Customer",
                "keys": [{"nodeColumn": "customer_key", "relationshipColumn": "customer_key"}],
            },
            "end": {
                "targetEntity": "Branch",
                "keys": [{"nodeColumn": "branch_id", "relationshipColumn": "branch_id"}],
            },
        },
    ],
}


def test_cypher_from_the_same_request():
    cypher = flat(
        compile_cypher(
            req(
                measures=[
                    {"alias": "spend", "computation": "c1"},
                    {"alias": "txns", "aggregate": "COUNT"},
                    {"alias": "share", "ratio_of": ["spend", "txns"]},
                ],
                dimensions=[
                    {"alias": "region", "column": "dw.dim_branch.region"},
                    {"alias": "month", "column": "dw.fct_txn.post_date", "grain": "week_monday"},
                ],
                filters=[{"computation": "c2"}],
                period={"column": "dw.fct_txn.posted_at", "from": "2026-04-01", "to": "2026-06-30"},
                order=[{"alias": "spend", "desc": True}],
                limit=3,
            ),
            CAT,
            unique,
            LABELS,
            MODEL,
        )
    )
    assert cypher.startswith("MATCH (fct_txn:Txn) MATCH (fct_txn)-[:MADE_BY]->(dim_customer:Customer)")
    assert "MATCH (dim_customer)-[:PREFERS]->(dim_branch:Branch)" in cypher
    x = "CASE WHEN fct_txn.is_purchase THEN fct_txn.amount ELSE null END"
    # SQL's SUM of no values is NULL, not Cypher's 0
    assert f"CASE WHEN count({x}) = 0 THEN null ELSE sum({x}) END AS spend" in cypher
    assert "date.truncate('week', fct_txn.post_date) AS month" in cypher
    assert "fct_txn.posted_at >= datetime('2026-04-01T00:00:00Z')" in cypher
    assert "fct_txn.posted_at < datetime('2026-07-01T00:00:00Z')" in cypher
    assert "CASE WHEN txns = 0 THEN null ELSE toFloat(spend) / txns END AS share" in cypher
    assert cypher.endswith("ORDER BY spend DESC LIMIT 3")


def test_cypher_what_the_graph_cant_express():
    with pytest.raises(Unfit, match="not in the virtual graph"):
        compile_cypher(
            req(measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_calls.call_id"}]),
            CAT,
            unique,
            LABELS,
            MODEL,
        )
    with pytest.raises(Unfit, match="truncation"):  # BigQuery's weeks start on Sunday, Cypher's on Monday
        compile_cypher(
            req(
                measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_txn.txn_id"}],
                dimensions=[{"alias": "w", "column": "dw.fct_txn.post_date", "grain": "week"}],
            ),
            CAT,
            unique,
            LABELS,
            MODEL,
        )


def test_cypher_reads_an_outer_joins_key_on_the_fact():
    cat = Catalogue(TABLES, [j | {"type": "LEFT"} for j in JOINS], {})
    cypher = flat(
        compile_cypher(
            req(
                measures=[{"alias": "n", "aggregate": "COUNT", "column": "dw.fct_txn.txn_id"}],
                dimensions=[{"alias": "c", "column": "dw.dim_customer.customer_key"}],
            ),
            cat,
            unique,
            LABELS,
            MODEL,
        )
    )
    # the customer is read on the transaction itself: no relationship walked, so a transaction with no
    # customer keeps its (null) group, as the SQL's LEFT JOIN does
    assert "MADE_BY" not in cypher and "fct_txn.customer_key AS c" in cypher


# ---- checks on the request (plans/2026-09-28-compiler-2.md, next)


def test_checks_find_an_unstated_restriction_and_a_stated_value_left_out():
    voice = {
        "id": "v1",
        "kind": "measure",
        "name": "Voice Call Transfers",
        "expression": "COUNTIF(fct_calls.was_transferred)",
        "filters": ["fct_calls.media_type = 'voice'"],
        "tables": ["p.dw.fct_calls"],
    }
    tables = TABLES | {
        "p.dw.fct_calls": TABLES["p.dw.fct_calls"] | {"media_type": "STRING", "was_transferred": "BOOL"}
    }
    cat = Catalogue(tables, JOINS, {"v1": voice})
    values = {("p.dw.fct_calls", "media_type"): ["voice", "chat"]}
    transfers = req(measures=[{"alias": "t", "computation": "v1"}])
    notes = check(transfers, cat, "How many calls were transferred, by media type?", values, 4)
    assert (
        len(notes) == 1 and "'voice'" in notes[0]
    )  # the Computation's restriction the question didn't state
    assert check(transfers, cat, "How many voice calls were transferred?", values, 4) == []
    count = req(measures=[{"alias": "n", "aggregate": "COUNT_DISTINCT", "column": "dw.fct_calls.call_id"}])
    notes = check(count, cat, "How many voice calls did we take?", values, 4)
    assert len(notes) == 1 and "'voice'" in notes[0]  # the value the question states, left out
    grouped = count | {"dimensions": [{"alias": "m", "column": "dw.fct_calls.media_type"}]}
    assert check(grouped, cat, "Voice and chat calls by media type", values, 4) == []


def test_a_week_grain_follows_the_log():
    texts = [
        "select date_trunc(post_date, week) as wk, count(*) from t group by 1",
        "SELECT DATE_TRUNC(t.post_date, WEEK) FROM t",
        "select date_trunc(post_date, week(monday)) from t",
    ]
    assert week_usage(texts, "post_date") == "week" and week_usage(texts, "other") == ""
    assert week_usage(["select date_trunc(date(ts), isoweek) from t"], "ts") == "week_monday"
    request = req(dimensions=[{"alias": "w", "column": "dw.fct_txn.post_date", "grain": "week_monday"}])
    usage = lambda t, c: week_usage(texts, c)
    assert weeks(request, CAT, usage, "Spend by week") and request["dimensions"][0]["grain"] == "week"
    request["dimensions"][0]["grain"] = "week_monday"
    assert weeks(request, CAT, usage, "Spend by week starting Monday") == []


def test_a_period_ending_today_that_the_question_doesnt_end_is_open():
    request = req(period={"column": "dw.fct_txn.post_date", "from": "2026-04-22", "to": "2026-07-01"})
    assert (
        open_period(request, "2026-07-01", "Decisions on or after 2026-04-22")
        and request["period"]["to"] == ""
    )
    request = req(period={"column": "dw.fct_txn.post_date", "from": "2026-04-22", "to": "2026-07-01"})
    assert open_period(request, "2026-07-01", "Decisions from 2026-04-22 to 2026-07-01") == []


def test_on_memory_an_outer_join_keeps_its_null_group():
    """With a guard (memory: a standard database), an outer join nothing filters on is OPTIONAL MATCH, its
    guard in its own WHERE; over the virtual graph (no OPTIONAL MATCH) it stays a MATCH."""
    from qlsc.compile import Block, Plan, render_cypher

    class Guard:
        node = staticmethod(lambda v, label: [f"{v}.ok"])
        relationship = staticmethod(lambda r: [f"{r}.ok"])

    b = Block(fact="p.dw.acct", joins=[("p.dw.acct", "branch_id", "p.dw.branch", "branch_id", True)],
              where=["acct.owner = 7"], dims=[("branch", "branch.name")], measures=[("n", "COUNT(acct.id)")])  # fmt: skip
    p = Plan(
        blocks=[b], dims=["branch"], outputs=["n"], derived={}, having=[], order=[], limit=0, listing=False
    )
    labels = {"p.dw.acct": "Account", "p.dw.branch": "Branch"}
    prop = lambda *cs: [{"name": c, "column": c, "type": "STRING"} for c in cs]
    model = {
        "nodes": [{"label": "Account", "properties": prop("id", "owner", "branch_id")},
                  {"label": "Branch", "properties": prop("branch_id", "name")}],
        "relationships": [{"label": "AT", "start": {"targetEntity": "Account"},
                           "end": {"targetEntity": "Branch", "keys": [{"relationshipColumn": "branch_id", "nodeColumn": "branch_id"}]}}],
    }  # fmt: skip
    virtual = render_cypher(p, labels, model)
    assert "MATCH (acct)-[:AT]->(branch:Branch)" in virtual and "OPTIONAL" not in virtual
    mem = render_cypher(p, labels, model, guard=Guard())
    assert "OPTIONAL MATCH (acct)-[r0:AT]->(branch:Branch)\nWHERE (branch.ok) AND (r0.ok)" in mem
    assert mem.index("(acct.ok)") < mem.index(
        "OPTIONAL MATCH"
    )  # the main WHERE before it, the fact's guard in it

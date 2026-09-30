"""The router's rule (navigate.route): memory, else compiled SQL, else free Cypher when it answers, else free
SQL. The live router and the evaluations' `pick` are the same rule."""

from __future__ import annotations

from qlsc.navigate import answered, pick, route

MEMORY = {"writer": "compiled", "route": "memory", "cypher": "MATCH (n) RETURN n"}
NOT_MEMORY = {"fallback": "no fresh context"}
COMPILED = {"writer": "compiled", "sql": "SELECT 1", "result": {"ok": True}}
UNFIT = {"fallback": "a list of rows"}
FREE_SQL = {"writer": "free", "sql": "SELECT 1", "result": {"ok": True}}
CYPHER = {"writer": "free", "cypher": "MATCH (n) RETURN n", "check": {"sql": []}, "result": {"ok": True}}


def test_the_order():
    assert route({"memory": MEMORY, "sql": COMPILED, "cypher": CYPHER, "free": FREE_SQL})[0] == "memory"
    assert route({"memory": NOT_MEMORY, "sql": COMPILED, "cypher": CYPHER, "free": FREE_SQL})[0] == "sql"
    assert route({"memory": NOT_MEMORY, "sql": UNFIT, "cypher": CYPHER, "free": FREE_SQL})[0] == "cypher"
    assert route({"sql": UNFIT, "cypher": {"declined": "no fees"}, "free": FREE_SQL})[0] == "free"


def test_the_router_runs_only_what_it_needs():
    ran = []
    step = lambda name, a: lambda: ran.append(name) or a
    route(
        {"memory": step("memory", NOT_MEMORY), "sql": step("sql", COMPILED), "cypher": step("cypher", CYPHER)}
    )
    assert ran == ["memory", "sql"]


def test_cypher_that_does_not_answer_sends_the_router_to_sql():
    for bad in (
        {"declined": "the graph has no fees"},
        {"skipped": "not in the virtual graph"},
        {"refused": "the warehouse filters the rows of dim_customer per reader"},
        CYPHER | {"check": {"error": "unsupported"}},
        CYPHER | {"result": {"ok": False, "error": "timeout"}},
        None,
    ):
        assert pick(FREE_SQL, bad) == "sql"
    assert pick(FREE_SQL, CYPHER) == "cypher" and pick(COMPILED, CYPHER) == "sql"
    assert not answered({"error": "the Virtual Graph instance is not running"})

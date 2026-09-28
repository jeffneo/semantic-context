"""The router's rule (navigate.pick): compiled SQL, else free Cypher when it answers, else free SQL."""

from __future__ import annotations

from qlsc.navigate import answered, pick

COMPILED = {"writer": "compiled", "sql": "SELECT 1", "result": {"ok": True}}
FREE_SQL = {"writer": "free", "sql": "SELECT 1", "fallback": "a list of rows", "result": {"ok": True}}
CYPHER = {"writer": "free", "cypher": "MATCH (n) RETURN n", "check": {"sql": []}, "result": {"ok": True}}


def test_compiled_sql_wins():
    assert pick(COMPILED, CYPHER) == "sql"


def test_free_cypher_when_the_question_does_not_compile_and_cypher_answers():
    assert pick(FREE_SQL, CYPHER) == "cypher"


def test_free_sql_when_cypher_does_not_answer():
    assert pick(FREE_SQL, {"declined": "the graph has no fees"}) == "sql"
    assert pick(FREE_SQL, {"skipped": "not in the virtual graph"}) == "sql"
    assert pick(FREE_SQL, CYPHER | {"check": {"error": "unsupported"}}) == "sql"
    assert pick(FREE_SQL, CYPHER | {"result": {"ok": False, "error": "timeout"}}) == "sql"
    assert pick(FREE_SQL, None) == "sql"
    assert not answered({"error": "the Virtual Graph instance is not running"})

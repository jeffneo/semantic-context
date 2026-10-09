"""Retention (plans/2026-10-08-memory-retention.md): what `qlsc memory sweep` deletes and keeps, on a scratch memory database of rows and conversations of known ages."""

from __future__ import annotations

import datetime as dt

import pytest

from qlsc import memory

NOW = dt.datetime(2026, 10, 8, 12, 0, tzinfo=dt.UTC)
DB = "memory-sweep-scratch"


def ago(**kw) -> dt.datetime:
    return NOW - dt.timedelta(**kw)


@pytest.fixture
def scratch(graph, example_settings):
    """A memory database of its own, so nothing real is touched, with a settings object that points memory at it."""
    from qlsc.graph import Graph

    with Graph(example_settings, {"database": "system"}) as system:
        system.run(f"CREATE DATABASE `{DB}` IF NOT EXISTS WAIT")
    s = example_settings
    old = dict(s["memory"])
    s["memory"] = {**old, "database": DB, "retain": {"fetched_days": 0.25, "audit_days": None}}
    with memory.memory_graph(s) as M:
        M.run("MATCH (n) DETACH DELETE n")
        # fetched rows: old, young, of two labels (one of them a dimension a young context still holds)
        M.run(
            """
            CREATE (:Customer {cif_number: 'old', fetched_at: $old, holds_until: $old})
            CREATE (:Customer {cif_number: 'young', fetched_at: $young, holds_until: $young})
            CREATE (:CardTransaction {id: 1, fetched_at: $old, holds_until: $old})
            CREATE (:Merchant {id: 'm', fetched_at: $young, holds_until: $young})
            CREATE (:Table {id: 't', name: 'a stub of the layer'})
            """,
            old=ago(days=2),
            young=ago(hours=1),
        )
        # a recall outside any conversation, old and young; an old conversation, whole, and a young one
        M.run(
            """
            MATCH (c:Customer {cif_number: 'young'})
            CREATE (:Step {id: 's-old', tool: 'recall', owner: 'x', recorded_at: $old})
            CREATE (:Step {id: 's-young', tool: 'recall', owner: 'x', recorded_at: $young})-[:READ]->(c)
            CREATE (c1:Conversation {id: 'c-old', recorded_at: $old})
            CREATE (m1:Message {id: 'm-old', recorded_at: $old})-[:PART_OF]->(c1)
            CREATE (t1:Task {id: 't-old', recorded_at: $old})-[:PART_OF]->(c1)
            CREATE (t1)-[:FROM]->(m1)
            CREATE (st1:Step {id: 'st-old', tool: 'ask', recorded_at: $old})-[:PART_OF]->(t1)
            CREATE (d1:Decision {id: 'd-old', recorded_at: $old})-[:PART_OF]->(t1)
            CREATE (f1:Fact {id: 'f-old', recorded_at: $old})-[:FROM]->(m1)
            CREATE (f1)-[:ABOUT]->(st1)
            CREATE (c2:Conversation {id: 'c-young', recorded_at: $young})
            CREATE (m2:Message {id: 'm-young', recorded_at: $young})-[:PART_OF]->(c2)
            CREATE (t2:Task {id: 't-young', recorded_at: $young})-[:PART_OF]->(c2)
            CREATE (:Step {id: 'st-young', tool: 'ask', recorded_at: $young})-[:PART_OF]->(t2)
            """,
            old=ago(days=90),
            young=ago(hours=1),
        )
    yield s
    s["memory"] = old
    with Graph(s, {"database": "system"}) as system:
        system.run(f"DROP DATABASE `{DB}` IF EXISTS WAIT")


def ids(s, label: str) -> set[str]:
    with memory.memory_graph(s) as M:
        return {r["i"] for r in M.rows(f"MATCH (n:{label}) RETURN coalesce(n.id, n.cif_number) AS i")}


def test_fetched_rows_expire_and_the_audit_record_is_kept(scratch):
    found = memory.sweep(scratch, NOW)
    assert found == {"fetched rows": {"Customer": 1, "CardTransaction": 1}}
    assert ids(scratch, "Customer") == {"young"} and ids(scratch, "Merchant") == {"m"}
    assert ids(scratch, "Table") == {"t"}  # a stub of the layer has no age
    # every conversation and step is still there, the 90-day-old ones too
    assert ids(scratch, "Conversation") == {"c-old", "c-young"}
    assert {"s-old", "s-young", "st-old", "st-young"} <= ids(scratch, "Step")


def test_the_sweep_leaves_a_step_of_its_own(scratch):
    memory.sweep(scratch, NOW)
    with memory.memory_graph(scratch) as M:
        (row,) = M.rows("MATCH (s:Step {tool: 'sweep'}) RETURN s.result AS result, s.owner AS owner")
    assert row["owner"] == "qlsc" and '"fetched rows": 2' in row["result"]


def test_a_dry_run_deletes_nothing(scratch):
    found = memory.sweep(scratch, NOW, dry_run=True)
    assert found["fetched rows"] == {"Customer": 1, "CardTransaction": 1}
    assert ids(scratch, "Customer") == {"old", "young"}
    assert "sweep" not in {r for r in ids(scratch, "Step")}


def test_a_second_sweep_finds_nothing(scratch):
    memory.sweep(scratch, NOW)
    assert memory.sweep(scratch, NOW)["fetched rows"] == {}


def test_a_conversation_goes_whole_when_the_audit_record_has_an_age(scratch):
    scratch["memory"]["retain"]["audit_days"] = 30
    found = memory.sweep(scratch, NOW)
    assert found["conversations"] == {"Conversation": 1}
    assert ids(scratch, "Conversation") == {"c-young"}
    assert ids(scratch, "Message") == {"m-young"} and ids(scratch, "Task") == {"t-young"}
    assert ids(scratch, "Decision") == set() and ids(scratch, "Fact") == set()  # theirs, with it
    steps = ids(scratch, "Step") - {
        r for r in ids(scratch, "Step") if len(r) == 36
    }  # the sweep's own step has a uuid
    assert steps == {"s-young", "st-young"}  # the old conversation's step and the old standalone one are gone

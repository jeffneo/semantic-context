"""The levels above the first (src/qlsc/process/abstract.py), the parts that need no database: what makes two elements alike by their
transitions, a parent's vector and id. The grouping itself (GDS) and the write are checked by building."""

from __future__ import annotations

import pytest

from qlsc.process import abstract
from qlsc.process.abstract import Node


def turn(event, conversation, seq, kind):
    return {"event": event, "conversation": conversation, "seq": seq, "kind": kind}


TURNS = [
    turn("a1", "c1", 0, "action"), turn("s1", "c1", 1, "state"), turn("a2", "c1", 2, "action"),
    turn("a3", "c2", 0, "action"), turn("s2", "c2", 1, "state"), turn("a4", "c2", 2, "action"),
]  # fmt: skip
OF = {"a1": "greet", "a2": "ask", "a3": "greet", "a4": "ask", "s1": "S-open", "s2": "S-open"}


def test_two_elements_in_the_same_places_are_alike_by_their_transitions():
    v = abstract.transition_vectors(TURNS, OF)
    assert abstract.sparse_cosine(v["greet"], v["greet"]) == pytest.approx(1.0)
    assert (
        abstract.sparse_cosine(v["greet"], v["ask"]) < 0.5
    )  # one comes before the State, the other after it
    # two Actions that follow the same State and are followed by the same one are alike, whatever their words
    more = [turn("a5", "c3", 0, "action"), turn("s3", "c3", 1, "state"), turn("a6", "c3", 2, "action")]
    of = {**OF, "a5": "hello", "a6": "ask", "s3": "S-open"}
    v = abstract.transition_vectors(TURNS + more, of)
    assert abstract.sparse_cosine(v["greet"], v["hello"]) == pytest.approx(1.0)


def test_a_turn_of_the_same_kind_in_a_row_is_no_transition():
    rows = [turn("x", "c", 0, "state"), turn("y", "c", 1, "state")]
    assert abstract.transition_vectors(rows, {"x": "A", "y": "B"}) == {}


def test_a_parents_vector_is_the_turn_weighted_mean_of_its_children_at_unit_length():
    kids = [Node("a", [1.0, 0.0], count=3, ends=0), Node("b", [0.0, 1.0], count=1, ends=0)]
    v = abstract.centroid(kids)
    assert sum(x * x for x in v) == pytest.approx(1.0) and v[0] > v[1]  # the larger child pulls it


def test_a_parents_id_is_its_children_not_their_order_and_not_its_name():
    one = abstract.parent_id("action", 2, ["b", "a"])
    assert one == abstract.parent_id("action", 2, ["a", "b"])
    assert one != abstract.parent_id("action", 3, ["a", "b"]) and one != abstract.parent_id(
        "state", 2, ["a", "b"]
    )
    assert one.startswith("action:L2:")

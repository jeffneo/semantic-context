"""Absorb (src/qlsc/process/absorb.py): the odds a State carries of a case ending well, by the two estimates. Counts and sweeps only: no model,
no database."""

from __future__ import annotations

import pytest

from qlsc.process import absorb

P = {"prior": 0.0, "tolerance": 1e-9, "sweeps": 500}


def turns(conversation: str, elements: list[str]) -> list[dict]:
    """A conversation as the build records it: an Action first, then a State, alternating (the elements' ids say which)."""
    return [
        {
            "conversation": conversation,
            "seq": i,
            "kind": "state" if e.startswith("state:") else "action",
            "element": e,
        }
        for i, e in enumerate(elements)
    ]


def outcomes(**kw: tuple[str, int]) -> dict[str, dict]:
    return {c: {"type": t, "good": g} for c, (t, g) in kw.items()}


def counts_of(rows: list[dict], found: dict[str, dict]) -> absorb.Counts:
    c = absorb.Counts()
    for p in absorb.paths(rows, found):
        c.add(p)
    return c


def test_a_conversation_taken_out_of_the_counts_and_put_back_changes_nothing():
    rows = turns("c1", ["action:a", "state:s", "action:b", "state:t"]) + turns(
        "c2", ["action:a", "state:s", "action:b", "state:u"]
    )
    found = outcomes(c1=("fixed", 1), c2=("lost", 0))
    c = counts_of(rows, found)
    before = (c.n, c.good, dict(c.through), {k: dict(v) for k, v in c.out.items()}, dict(c.fin))
    p = next(x for x in absorb.paths(rows, found) if x.conversation == "c1")
    c.add(p, -1)
    assert (c.n, c.good, c.through["state:s"], c.through["state:t"]) == (1, 0, 1, 0)
    c.add(p)
    after = (c.n, c.good, dict(c.through), {k: dict(v) for k, v in c.out.items()}, dict(c.fin))
    assert before == after


def test_a_turn_followed_by_one_of_its_own_kind_is_no_transition_and_a_case_without_an_outcome_is_not_counted():
    rows = turns("c1", ["action:a", "action:b", "state:s"]) + turns("c2", ["action:a", "state:s"])
    (p,) = absorb.paths(rows, outcomes(c1=("fixed", 1)))
    assert p.pairs == [("action:b", "state:s")]  # a then b are both Actions: the graph has no such transition
    assert p.last == "state:s" and p.touched == {"action:a", "action:b", "state:s"}


def test_the_empirical_odds_are_the_share_of_the_conversations_through_the_state_and_a_prior_pulls_a_thin_state_to_the_global_rate():
    rows = []
    found = {}
    for i in range(4):
        rows += turns(f"g{i}", ["action:a", "state:s"])
        found[f"g{i}"] = {"type": "fixed", "good": 1}
    rows += turns("b", ["action:a", "state:r"])
    found["b"] = {"type": "lost", "good": 0}
    c = counts_of(rows, found)
    assert absorb.empirical(c, "state:s", 0.0) == 1.0
    assert absorb.empirical(c, "state:r", 0.0) == 0.0
    # one case that went badly is not the State's fate: with 2 pseudo-conversations at the global rate (0.8) it is 1.6 / 3
    assert absorb.empirical(c, "state:r", 2.0) == pytest.approx(0.8 * 2 / 3)
    assert absorb.empirical(c, "state:unseen", 0.0) == pytest.approx(0.8)  # nothing seen: the global rate


def test_the_chain_weights_each_next_element_by_how_often_it_follows():
    # s -> (a) -> good ending or bad ending, half and half; and an element that always leads to s
    rows = []
    found = {}
    for i in range(3):
        rows += turns(f"g{i}", ["action:a", "state:s", "action:x", "state:good"])
        found[f"g{i}"] = {"type": "fixed", "good": 1}
        rows += turns(f"b{i}", ["action:a", "state:s", "action:x", "state:bad"])
        found[f"b{i}"] = {"type": "lost", "good": 0}
    c = counts_of(rows, found)
    h = absorb.chain(c, P)
    assert h["state:good"] == pytest.approx(1.0) and h["state:bad"] == pytest.approx(0.0)
    assert h["action:x"] == pytest.approx(0.5)
    assert h["state:s"] == pytest.approx(0.5)
    assert h["action:a"] == pytest.approx(0.5)


def test_the_chain_reaches_an_element_through_a_loop_to_where_cases_end():
    # s -> x -> s again half the time, otherwise ends in a good outcome: every case is eventually absorbed good
    rows = []
    found = {}
    for i in range(2):
        rows += turns(f"l{i}", ["action:a", "state:s", "action:x", "state:s", "action:x", "state:s"])
        found[f"l{i}"] = {"type": "fixed", "good": 1}
    rows += turns("e", ["action:a", "state:s"])
    found["e"] = {"type": "fixed", "good": 1}
    c = counts_of(rows, found)
    h = absorb.chain(c, P)
    assert h["state:s"] == pytest.approx(1.0)


def test_a_chain_solve_that_starts_from_the_full_solution_ends_where_a_cold_one_does():
    rows = turns("c1", ["action:a", "state:s", "action:b", "state:t"]) + turns(
        "c2", ["action:a", "state:s", "action:b", "state:u"]
    )
    rows += turns("c3", ["action:a", "state:s", "action:b", "state:t"])
    found = outcomes(c1=("fixed", 1), c2=("lost", 0), c3=("fixed", 1))
    c = counts_of(rows, found)
    warm = absorb.chain(c, P)
    p = next(x for x in absorb.paths(rows, found) if x.conversation == "c2")
    c.add(p, -1)
    cold = absorb.chain(c, P)
    start = absorb.chain(c, P, start=warm)
    assert all(start[e] == pytest.approx(cold[e]) for e in cold)
    assert cold["state:s"] == pytest.approx(1.0)  # without c2, every case through s ended well


def test_an_element_is_standing_for_its_highest_ancestor_no_higher_than_the_level_asked():
    levels = {"action:a": 1, "action:b": 1, "action:L2": 2, "action:L3": 3, "action:solo": 1}
    parent = {"action:a": "action:L2", "action:b": "action:L2", "action:L2": "action:L3"}
    assert absorb.ancestor_at("action:a", 1, levels, parent) == "action:a"
    assert absorb.ancestor_at("action:a", 2, levels, parent) == "action:L2"
    assert absorb.ancestor_at("action:a", 3, levels, parent) == "action:L3"
    assert absorb.ancestor_at("action:solo", 3, levels, parent) == "action:solo"  # nobody grouped it


def test_the_likeliest_outcomes_are_listed_most_likely_first_and_from_the_estimate_that_is_stored():
    rows = []
    found = {}
    for i, t in enumerate(["fixed", "fixed", "fixed", "lost"]):
        rows += turns(f"c{i}", ["action:a", "state:s"])
        found[f"c{i}"] = {"type": t, "good": int(t == "fixed")}
    c = counts_of(rows, found)
    assert absorb.likely(c, "empirical", {}, "state:s", 1) == [("fixed", 0.75)]
    assert [k for k, _ in absorb.likely(c, "empirical", {}, "state:s", 5)] == ["fixed", "lost"]
    kinds = absorb.chain_kinds(c, P)
    assert absorb.likely(c, "chain", kinds, "state:s", 2)[0] == ("fixed", pytest.approx(0.75))

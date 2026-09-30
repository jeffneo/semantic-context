"""The ruler every accuracy number is measured with (examples/fennmoor-bank/eval/match.py): an answer
matches its reference on the compared columns, whatever the answer calls them."""

from __future__ import annotations

import sys

from conftest import EXAMPLE

sys.path.insert(0, str(EXAMPLE / "eval"))
from match import compare, verdict  # noqa: E402

REF = {"columns": ["segment", "share"], "rows": [{"segment": "affluent", "share": 0.25}, {"segment": "mass", "share": 0.75}]}  # fmt: skip
ITEMS = [["segment"], ["share"]]
answer = lambda cols, rows: {"columns": cols, "rows": [dict(zip(cols, r)) for r in rows], "total": len(rows), "ok": True}  # fmt: skip


def test_the_same_values_under_other_names_in_another_order():
    got = answer(["pct", "grp"], [(0.75, "MASS"), (0.2501, "Affluent")])
    assert compare(REF, got, ITEMS)[0] == "correct"


def test_a_share_as_a_percentage():
    assert (
        compare(REF, answer(["segment", "pct"], [("affluent", 25.0), ("mass", 75.0)]), ITEMS)[0] == "correct"
    )


def test_wrong_values_or_rows_are_wrong_and_none_is_empty():
    assert compare(REF, answer(["segment", "share"], [("affluent", 0.3), ("mass", 0.7)]), ITEMS)[0] == "wrong"
    assert compare(REF, answer(["segment", "share"], [("affluent", 0.25)]), ITEMS)[0] == "wrong"
    assert compare(REF, answer(["segment", "share"], []), ITEMS)[0] == "empty"


def test_alternatives_either_identifies_the_thing():
    ref = {"columns": ["branch_id", "n"], "rows": [{"branch_id": 10, "n": 3}, {"branch_id": 20, "n": 4}]}
    got = answer(["branch_id", "calls"], [(10, 3), (20, 4)])
    assert compare(ref, got, [["branch_id", "branch_name"], ["n"]])[0] == "correct"


def test_a_pivoted_answer_is_melted_back_to_rows():
    ref = {"columns": ["segment", "month", "n"], "rows": [
        {"segment": "affluent", "month": "apr", "n": 1}, {"segment": "affluent", "month": "may", "n": 2},
        {"segment": "mass", "month": "apr", "n": 3}, {"segment": "mass", "month": "may", "n": 4}]}  # fmt: skip
    got = answer(["segment", "apr", "may"], [("affluent", 1, 2), ("mass", 3, 4)])
    assert compare(ref, got, [["segment"], ["month"], ["n"]])[0] == "correct"


def test_a_route_that_did_not_answer_is_not_scored_as_wrong():
    refs = [{"name": "Q1", "items": ITEMS, "result": REF}]
    assert verdict({"skipped": "not in the virtual graph"}, refs)[0] == "not covered"
    assert verdict({"declined": "no fees here"}, refs)[0] == "declined"
    assert verdict({"sql": "x", "result": {"ok": False, "error": "timeout"}}, refs)[0] == "failed"
    assert (
        verdict({"sql": "x", "result": answer(["a"], [(1,)])}, [refs[0] | {"items": []}])[0] == "not scored"
    )

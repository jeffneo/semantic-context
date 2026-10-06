"""The statistics under the process graph's scorer (examples/fennmoor-bank/eval/process_graph.py): V-measure, Wilson intervals, ranks."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "eval"
sys.path.insert(0, str(EVAL))

import process_graph as pg  # noqa: E402


def test_a_perfect_grouping_scores_one_and_one_cluster_is_complete_but_not_homogeneous():
    classes = {"a": "x", "b": "x", "c": "y", "d": "y"}
    assert pg.v_measure(classes, {"a": "1", "b": "1", "c": "2", "d": "2"}) == (1.0, 1.0, 1.0)
    h, c, v = pg.v_measure(classes, {k: "all" for k in classes})
    assert (h, c) == (0.0, 1.0) and v == 0.0
    h, c, _ = pg.v_measure(classes, {k: k for k in classes})  # every turn alone: homogeneous, not complete
    assert (h, c) == (1.0, pytest.approx(0.5))


def test_the_scorer_only_counts_events_both_sides_name():
    assert pg.v_measure({"a": "x", "b": "y"}, {"a": "1"})[2] == 1.0


def test_a_wilson_interval_holds_the_rate_and_narrows_with_more_points():
    lo, hi = pg.wilson(7, 100)
    assert lo < 0.07 < hi
    lo2, hi2 = pg.wilson(70, 1000)
    assert hi2 - lo2 < hi - lo
    assert pg.wilson(0, 0) == (0.0, 0.0)


def test_ranks_average_ties_and_pearson_of_ranks_is_spearman():
    assert pg.ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]
    a, b = [1, 2, 3, 4], [10, 20, 30, 41]
    assert pg.pearson(pg.ranks(a), pg.ranks(b)) == pytest.approx(1.0)
    assert pg.pearson([1, 1, 1], [1, 2, 3]) != pg.pearson([1, 1, 1], [1, 2, 3])  # nan: no variance

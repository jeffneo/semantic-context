"""The request bank's links between query shapes (qlsc/requests.py), without a database."""

from __future__ import annotations

from qlsc import requests


def shape(id, first, last, principals, reads, tables, computes=()):
    return {"id": id, "first_seen": first, "last_seen": last, "principals": principals, "reads": reads,
            "tables": tables, "computes": list(computes)}  # fmt: skip


V2 = shape(
    "v2", "2026-04-01T00:00:00", "2026-05-01T00:00:00", ["ana", "raj"], ["a", "b", "c"], ["churn_v2"], ["m"]
)
V3 = shape(
    "v3", "2026-05-02T00:00:00", "2026-06-30T00:00:00", ["ana", "raj"], ["a", "b", "d"], ["churn_v3"], ["m"]
)


def test_a_query_that_replaced_another_succeeds_it():
    succ, _ = requests.edges([V2, V3], days=21, reads=0.4)
    assert succ == [{"a": "v3", "b": "v2", "props": {"gap_days": 1}}]  # v3 replaced v2 a day after it stopped


def test_no_succession_without_the_same_people_or_reads_alike_or_a_table_changed():
    other_people = V3 | {"principals": ["kim"]}
    unlike = V3 | {"reads": ["x", "y", "z"]}
    same_table = V3 | {"tables": ["churn_v2"]}
    late = V3 | {"first_seen": "2026-09-01T00:00:00"}
    for b in (other_people, unlike, same_table, late):
        assert requests.edges([V2, b], days=21, reads=0.4)[0] == []


def test_variants_share_a_table_and_a_computation():
    a, b = V2 | {"tables": ["t"]}, V3 | {"tables": ["t"]}
    assert requests.edges([a, b], days=21, reads=0.4)[1] == [{"a": "v2", "b": "v3", "props": {}}]
    assert requests.edges([a, b | {"computes": ["other"]}], days=21, reads=0.4)[1] == []

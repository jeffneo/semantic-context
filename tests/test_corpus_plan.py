"""The process corpus's phase A (examples/fennmoor-bank/generate/corpus_plan.py): plans are reproducible, the world's
structures show up in them, and plans are matched to rows that agree with them. No warehouse: the matcher runs on a pool built
here."""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from pathlib import Path

import pytest

GENERATE = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "generate"
sys.path.insert(0, str(GENERATE))

import corpus_plan  # noqa: E402
import corpus_report  # noqa: E402
import corpus_world  # noqa: E402


@pytest.fixture(scope="module")
def world():
    return corpus_world.load_world()


@pytest.fixture(scope="module")
def plans(world):
    sampler = corpus_plan.Sampler(world)
    return [sampler.plan(7, i) for i in range(3000)]


def test_a_plan_is_the_same_whatever_else_is_generated(world):
    a, b = corpus_plan.Sampler(world), corpus_plan.Sampler(world)
    assert a.plan(7, 5) == b.plan(7, 5)
    assert a.plan(7, 5) != a.plan(8, 5)
    assert [a.plan(7, i) for i in range(10)] == [b.plan(7, i) for i in range(10)]


def test_every_outcome_is_reachable(world, plans):
    reached = {p["outcome"] for p in plans}
    unreached = [o["id"] for o in world.outcomes if o["requires"] and o["id"] not in reached]
    # Retention with a skipped authentication that still saves is rare by construction; it is the only one allowed to be missing.
    assert set(unreached) <= {"OUT-RETAINED-WITH-BREACH"}


def test_the_control_family_has_nothing_to_find(plans):
    control = [p for p in plans if p["domain"] == "DOM-SERVICING" and p["steps"][0]["kind"] != "queue"]
    assert sum(p["outcome"] == "OUT-RESOLVED-FIRST-CONTACT" for p in control) / len(control) > 0.9
    assert not any(p["misdiagnosed"] for p in control)


def test_asking_has_value(world, plans):
    savable = [
        p
        for p in plans
        if p["procedure"] == "PROC-RETENTION"
        and p["steps"][0]["kind"] != "queue"
        and world.effect("ACT-PROCESS-CLOSURE", p["cause"]) != "fixes"
    ]
    learned = [p for p in savable if any(s.get("reveals") for s in p["steps"])]
    not_learned = [p for p in savable if p not in learned]
    rate = lambda ps: sum(p["retained"] for p in ps) / len(ps)  # noqa: E731
    assert rate(learned) > rate(not_learned) + 0.1


def test_reps_differ_without_dictating(plans):
    worked = [p for p in plans if p["steps"][0]["kind"] != "queue" and p["procedure"] != "PROC-SERVICING"]
    wrong = {r: [p["misdiagnosed"] for p in worked if p["rep"] == r] for r in {p["rep"] for p in worked}}
    rate = {r: sum(v) / len(v) for r, v in wrong.items()}
    assert rate["REP-METHODICAL"] < rate["REP-RUSHED"]
    assert all(0.02 < v < 0.7 for v in rate.values())


def test_the_site_effect_is_planted(plans):
    hung = {s: [p["steps"][0]["kind"] == "queue" for p in plans if p["site"] == s] for s in ("TUL", "MNL")}
    assert sum(hung["MNL"]) / len(hung["MNL"]) > 1.5 * sum(hung["TUL"]) / len(hung["TUL"])


def test_a_breach_is_recorded_only_where_a_gate_applies(world, plans):
    for p in plans:
        for b in p["breaches"]:
            if world.policies[b["policy"]].get("applies_when", {}).get("is_authenticated") == [False]:
                assert not p["authenticated"]


def synthetic_pool(world) -> list[dict]:
    """Rows for every combination a plan can ask for, so matching can be checked without the warehouse."""
    agents: dict[str, str] = {}
    for i in itertools.count():
        agents.setdefault(world.rep_of(f"agent-{i}"), f"agent-{i}")
        if len(agents) == len(world.rep_archetypes):
            break
    rows, n = [], 0
    for intent, site, auth, transferred in itertools.product(
        sorted(corpus_world.INTENTS), sorted(corpus_world.SITES), (True, False), (True, False)
    ):
        for agent in agents.values():
            for _ in range(3):
                n += 1
                rows.append(
                    {
                        "conversation_id": f"c{n}",
                        "conversation_start": "2026-01-01T10:00:00",
                        "media_type": "voice",
                        "ivr_intent": intent,
                        "agent_user_id": agent,
                        "site_id": site,
                        "queue_site_id": site,
                        "cif_number": f"{n:010d}",
                        "is_authenticated": auth,
                        "was_transferred": transferred,
                        "is_abandoned": False,
                        "is_account_closure_call": intent == "CLOSE_ACCOUNT",
                        "handle_sec": 3000,
                        "wrapup_code_name": "X",
                        "fees": [
                            {
                                "fee_id": "f",
                                "fee_type": "MAINT",
                                "fee_amount": 12.5,
                                "assessed_date": "2026-01-01",
                                "product_code": "X",
                            }
                        ],
                        "purchases": [
                            {
                                "settlement_id": "s",
                                "merchant_id": "m",
                                "merchant_name": "ShopRiver",
                                "mcc_category_group": "RETAIL",
                                "amount": 20.0,
                                "post_date": "2026-01-02",
                            }
                        ],
                        "next_id": None,
                        "next_gap_days": None,
                        "next_answered": None,
                    }
                )
    for intent, site in itertools.product(sorted(corpus_world.INTENTS), sorted(corpus_world.SITES)):
        for _ in range(30):
            n += 1
            rows.append(
                {
                    **rows[0],
                    "conversation_id": f"c{n}",
                    "ivr_intent": intent,
                    "agent_user_id": None,
                    "site_id": None,
                    "queue_site_id": site,
                    "is_abandoned": True,
                    "is_account_closure_call": False,
                    "was_transferred": False,
                    "fees": None,
                    "purchases": None,
                }
            )
    return rows


def test_plans_are_matched_to_rows_that_agree_with_them(world):
    pool = synthetic_pool(world)
    plans, stats = corpus_plan.generate(world, pool, 7, 150)
    assert stats["plans"] >= 150 and not stats.get("given_up")
    assert corpus_report.verify(world, plans, pool) == []
    assert len({p["conversation_id"] for p in plans}) == len(plans)  # no row twice


def test_a_row_is_used_once(world):
    pool = synthetic_pool(world)
    plans, _ = corpus_plan.generate(world, pool, 3, 200)
    assert max(Counter(p["conversation_id"] for p in plans).values()) == 1

"""The process corpus's phase B (examples/fennmoor-bank/generate/corpus_text.py and corpus_check.py): the skeleton, the checks that
keep the text agreeing with the plan, and the event objects. No model: the stub writes placeholder text, and the checks are tried
on text written here."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from test_corpus_plan import synthetic_pool

GENERATE = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "generate"
sys.path.insert(0, str(GENERATE))

import corpus_check  # noqa: E402
import corpus_plan  # noqa: E402
import corpus_text  # noqa: E402
import corpus_world  # noqa: E402

IDENTITY = {"ACT-VERIFY-IDENTITY", "ACT-STEPUP-VERIFY"}


@pytest.fixture(scope="module")
def world():
    return corpus_world.load_world()


@pytest.fixture(scope="module")
def plans(world):
    out, _ = corpus_plan.generate(world, synthetic_pool(world), 7, 300)
    return out


def rendered(world, plan):
    text, meta = corpus_text.request_for(world, plan, 7, None, None)
    turns = {t["slot"]: t["text"] for t in corpus_text.stub_turns(meta["skeleton"])}
    return text, meta, turns


def problems(world, plan, meta, turns):
    raw = [{"slot": k, "text": v} for k, v in turns.items()]
    return corpus_check.check(world, plan, meta, raw, turns, corpus_text.STYLES)


def worked(plans):
    return [p for p in plans if p["steps"][0]["kind"] != "queue"]


def test_the_skeleton_follows_the_plan_step_for_step(world, plans):
    for p in worked(plans)[:60]:
        _, meta, _ = rendered(world, p)
        sk = meta["skeleton"]
        assert [s["slot"] for s in sk] == list(range(len(sk)))
        assert (
            sk[0]["role"] == "rep_greeting"
            and sk[1]["role"] == "cust_opening"
            and sk[-1]["role"] == "case_note"
        )
        rep_actions = [s["action"] for s in p["steps"] if s.get("action")]
        # every action the rep took is a slot, and nothing else is
        said = [
            s for s in sk if s["role"].startswith("rep_") and s["role"] not in {"rep_greeting", "rep_closing"}
        ]
        assert len(said) == len(rep_actions)


def test_a_conversation_that_never_reached_an_agent_is_a_system_line(world, plans):
    queue = [p for p in plans if p["steps"][0]["kind"] == "queue"]
    assert queue
    ev = corpus_text.scripted_events(queue[0], 7)
    assert len(ev) == 1 and ev[0]["role"] == "system" and corpus_check.event_problems(ev, queue[0]) == []


def test_the_stub_writes_events_that_agree_with_their_rows(world, plans, tmp_path):
    summary = corpus_text.realise(world, None, plans, 7, None, True, tmp_path)
    results = summary.pop("results")
    assert summary["written"] > 0
    for r in results:
        if r["events"]:
            assert corpus_check.event_problems(r["events"], r["plan"]) == []
    assert (tmp_path / "events.ndjson.gz").is_file() and (tmp_path / "truth.ndjson.gz").is_file()


def test_every_slot_must_come_back_once_and_in_order(world, plans):
    p = next(p for p in worked(plans) if p["procedure"] == "PROC-SERVICING")
    _, meta, turns = rendered(world, p)
    drop = {k: v for k, v in turns.items() if k != 2}
    assert any("slots are wrong" in x for x in problems(world, p, meta, drop))
    # a model that kept writing past the last slot is forgiven; one that rewrote the middle is not
    extra = {**turns, len(turns): "and then some", len(turns) + 1: "more"}
    raw = [{"slot": k, "text": v} for k, v in extra.items()]
    assert not any(
        "slots are wrong" in x for x in corpus_check.check(world, p, meta, raw, extra, corpus_text.STYLES)
    )


def test_an_identifier_or_the_plans_vocabulary_is_rejected(world, plans):
    p = worked(plans)[0]
    _, meta, turns = rendered(world, p)
    assert any(
        "identifier" in x for x in problems(world, p, meta, {**turns, 1: "my number is 5551234567890"})
    )
    assert any("vocabulary" in x for x in problems(world, p, meta, {**turns, 1: "this is CAU-RET-FEE-SHOCK"}))


def test_a_verification_nobody_took_is_rejected(world, plans):
    # the breach is a skipped verification: the text must not quietly make it
    p = next(
        p
        for p in worked(plans)
        if not p["authenticated"] and not {s["action"] for s in p["steps"] if s.get("action")} & IDENTITY
    )
    _, meta, turns = rendered(world, p)
    agent_slot = next(s["slot"] for s in meta["skeleton"] if s["role"] == "rep_greeting")
    bad = {**turns, agent_slot: "Hi, can I get the last four of your card and your date of birth?"}
    assert any("verifies the caller" in x for x in problems(world, p, meta, bad))


def test_checking_the_account_is_not_verifying_the_caller(world, plans):
    # running a check (the dispute window, the waiver history) must not license verification talk
    p = next(
        p
        for p in worked(plans)
        if not p["authenticated"]
        and not {s["action"] for s in p["steps"] if s.get("action")} & IDENTITY
        and any(world.actions[s["action"]]["type"] == "check" for s in p["steps"] if s.get("action"))
    )
    _, meta, turns = rendered(world, p)
    agent_slot = next(s["slot"] for s in meta["skeleton"] if s["role"] == "rep_greeting")
    bad = {**turns, agent_slot: "Before we go on, I just need to verify who you are."}
    assert any("verifies the caller" in x for x in problems(world, p, meta, bad))


def test_a_clue_nobody_surfaced_is_rejected(world, plans):
    for p in worked(plans):
        _, meta, turns = rendered(world, p)
        asked = {
            world.actions[s["action"]]["elicits"]
            for s in p["steps"]
            if s.get("action") and world.actions[s["action"]].get("elicits")
        }
        unsaid = [
            m
            for m in p["world"]["present"]
            if world.manifestations[m].get("discriminating") and m not in meta["surfaced"] and m not in asked
        ]
        if unsaid and len(corpus_check.keywords(world.manifestations[unsaid[0]]["label"])) >= 2:
            slot = next(s["slot"] for s in meta["skeleton"] if s["role"] == "cust_opening")
            bad = {**turns, slot: world.manifestations[unsaid[0]]["label"]}
            assert any("brings up something nobody did" in x for x in problems(world, p, meta, bad))
            return
    pytest.skip("no plan in the sample had an unsaid clue with distinctive words")


def test_an_email_must_finish_its_sentences():
    assert not corpus_check.email_complete("Hello,\n\nThat sounds good, and\n\n[REDACTED]")
    assert corpus_check.email_complete("Hello,\n\nAll set.\n\nRegards,\n[REDACTED]")
    assert corpus_check.email_complete("Hi,\n\nThanks.\n\nThanks,\n[REDACTED]")
    assert not corpus_check.email_complete("Hi,\n\nAll good")


def test_the_customers_last_line_raises_nothing_new(world, plans):
    for p in worked(plans):
        _, meta, turns = rendered(world, p)
        closing = [s["slot"] for s in meta["skeleton"] if s["role"] == "cust_closing"]
        if closing:
            bad = {**turns, closing[0]: "Actually, are you open on Saturdays?"}
            assert any("asks something new" in x for x in problems(world, p, meta, bad))
            return
    pytest.skip("no conversation with a closing in the sample")

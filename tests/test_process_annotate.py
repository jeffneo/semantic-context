"""Annotation (src/qlsc/process/annotate.py): the prompts' inputs, the checks on an answer, one retry, and a failed turn recorded
and not fatal. No model: the LLM is a fake that answers from a script."""

from __future__ import annotations

import pytest

from qlsc import config
from qlsc.process import annotate
from qlsc.process.source import Source, Turn

CONVERSATION = [
    Turn("e0", "c", 0, "t0", "voice_turn", "agent", "action", "Thanks for calling."),
    Turn("e1", "c", 1, "t1", "voice_turn", "customer", "state", "I was charged a fee."),
    Turn("e2", "c", 2, "t2", "voice_turn", "agent", "action", "I'll check that."),
]


@pytest.fixture()
def s(tmp_path):
    f = tmp_path / "estate.yaml"
    f.write_text("business: {name: a bank, kind: bank}\nwarehouse: {gcloud_config: x}\n")
    return config.load(f)


class Fake:
    """An LLM that answers from a queue, and keeps what it was asked."""

    def __init__(self, system, settings, model=None):
        self.system, self.model = system, model or "fake"
        self.asked: list[str] = []
        self.calls = self.cached = 0
        self.seconds = 0.0
        self.tokens = {"in": 0, "out": 0}

    def call(self, user, schema, max_tokens=0):
        self.asked.append(user)
        self.calls += 1
        return Fake.next(schema)

    def cost(self):
        return 0.0


Fake.queue = []


def answers(*items):
    Fake.queue = list(items)
    Fake.next = lambda schema: Fake.queue.pop(0)


@pytest.fixture()
def annotator(s, monkeypatch):
    monkeypatch.setattr(annotate, "LLM", Fake)
    return annotate.Annotator(s)


def test_the_transcript_stops_at_the_turn_being_described():
    text = annotate.transcript(CONVERSATION, 1)
    assert "[2] Customer: I was charged a fee." in text
    assert "I'll check that." not in text  # the future is not in the prompt
    assert annotate.transcript(CONVERSATION).count("\n") == 2


def test_a_state_is_the_latest_turn_then_what_is_known():
    assert (
        annotate.state_text({"latest_turn": "A fee.  ", "established": " Not verified."})
        == "A fee. Not verified."
    )


def test_an_action_must_begin_with_a_listed_verb(s):
    assert annotate.problems(s, "action", {"action": "Check the waiver history"}) == []
    assert "must begin with" in annotate.problems(s, "action", {"action": "Request the account number"})[0]
    assert annotate.problems(s, "action", {"action": " "}) == ["the action is empty"]
    assert annotate.problems(s, "state", {"latest_turn": "x", "established": ""}) == ["established is empty"]


def test_a_bad_answer_is_asked_again_with_the_reason_and_then_accepted(annotator):
    answers({"action": "Request the account number"}, {"action": "Ask for the account number"})
    r = annotator.turn(CONVERSATION, 2)
    assert (r["attempts"], r["problems"], r["description"]) == (2, [], "Ask for the account number")
    assert "rejected" in annotator.action.asked[1] and "rejected" not in annotator.action.asked[0]


def test_a_turn_that_fails_twice_is_recorded_with_its_problem_and_does_not_stop_the_pass(annotator):
    answers({"action": "Request x"}, {"action": "Request y"}, {"latest_turn": "ok", "established": "fine"})
    rows = [annotator.turn(CONVERSATION, 2), annotator.turn(CONVERSATION, 1)]
    assert rows[0]["problems"] and rows[0]["attempts"] == 2
    assert rows[1]["problems"] == [] and rows[1]["description"] == "ok fine"


def test_a_conversation_call_must_number_every_turn_in_order(annotator):
    good = {
        "turns": [
            {"turn": 1, "latest_turn": "", "established": "", "action": "Greet the customer"},
            {"turn": 2, "latest_turn": "A fee.", "established": "Not verified.", "action": ""},
            {"turn": 3, "latest_turn": "", "established": "", "action": "Check the fee"},
        ]
    }
    answers(good)
    rows = annotator.by_conversation(CONVERSATION)
    assert [r["kind"] for r in rows] == ["action", "state", "action"] and not any(r["problems"] for r in rows)
    # a wrong numbering is asked again, and if it stays wrong every turn carries the problem
    answers({"turns": good["turns"][:2]}, {"turns": good["turns"][:2]})
    rows = annotator.by_conversation(CONVERSATION)
    assert all(r["problems"] for r in rows) and all(r["attempts"] == 2 for r in rows)


def test_the_same_limit_is_the_same_sample():
    src = Source("x", {"b": [], "a": [], "c": []}, {})
    assert (
        annotate.select(src, 2) == annotate.select(src, 2) == ["b", "a"]
    )  # the source's own order (read() sorts it)


def test_a_request_the_api_refuses_fails_that_turn_and_not_the_pass(annotator):
    import anthropic

    def refuse(schema):
        raise anthropic.APIError("content filter", request=None, body=None)

    Fake.next = refuse
    r = annotator.turn(CONVERSATION, 2)
    assert r["problems"] and "no answer" in r["problems"][0] and r["attempts"] == 2

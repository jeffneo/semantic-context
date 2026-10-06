"""Outcomes (src/qlsc/process/outcomes.py): what the outcome call is shown and what it may answer, and the after-call note the turns leave out.
No model and no database."""

from __future__ import annotations

import json

import pytest

from qlsc import config
from qlsc.process import outcomes, source
from qlsc.process.source import Turn


@pytest.fixture()
def s(tmp_path):
    f = tmp_path / "estate.yaml"
    f.write_text(
        "business: {name: a bank, kind: bank}\nwarehouse: {gcloud_config: x}\nprocess:\n  events: events.ndjson\n"
    )
    return config.load(f)


def turn(seq, role, text):
    return Turn(
        f"e{seq}", "c", seq, "t", "voice_turn", role, "state" if role == "customer" else "action", text
    )


def test_the_call_is_shown_the_end_of_the_conversation_not_the_whole_of_it():
    turns = [turn(i, "customer" if i % 2 else "agent", f"line {i}") for i in range(10)]
    shown = outcomes.ending(turns, 3)
    assert shown.splitlines() == ["Customer: line 7", "Agent: line 8", "Customer: line 9"]


def test_an_answer_needs_a_description_and_a_rating_from_one_to_five():
    assert outcomes.problems({"outcome": "Fee waived.", "rating": 4}) == []
    assert outcomes.problems({"outcome": " ", "rating": 4}) == ["outcome is empty"]
    assert "rating" in outcomes.problems({"outcome": "x", "rating": 9})[0]


class Fake:
    def __init__(self, answers):
        self.answers, self.asked = list(answers), []

    def call(self, user, schema, max_tokens=0):
        self.asked.append(user)
        return self.answers.pop(0)


def test_a_bad_answer_is_asked_again_with_the_reason_and_a_second_failure_is_recorded_not_fatal(s):
    turns = [turn(0, "agent", "bye")]
    good = outcomes.describe_one(
        Fake([{"outcome": "x", "rating": 9}, {"outcome": "Settled.", "rating": 5}]), s, "c", turns, "note"
    )
    assert (good["attempts"], good["problems"], good["rating"]) == (2, [], 5)
    bad = outcomes.describe_one(
        Fake([{"outcome": "", "rating": 3}, {"outcome": "", "rating": 3}]), s, "c", turns, "note"
    )
    assert bad["problems"] == ["outcome is empty"] and bad["attempts"] == 2


def test_the_note_is_read_from_its_channel_and_never_made_a_turn(tmp_path, s):
    rows = [
        {
            "event_id": "a",
            "conversation_id": "c1",
            "seq": 0,
            "ts": "t",
            "channel": "voice_turn",
            "role": "agent",
            "text": "hi",
        },
        {
            "event_id": "b",
            "conversation_id": "c1",
            "seq": 5,
            "ts": "t",
            "channel": "case_note",
            "role": "agent",
            "text": "Waived the fee.",
        },
    ]
    (tmp_path / "events.ndjson").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert source.notes(s) == {"c1": "Waived the fee."}
    assert [t.event for t in source.read(s).conversations["c1"]] == ["a"]  # the turn reader leaves it out

"""Outlook (src/qlsc/process/outlook.py): locating a case, pooling the nearest States' counts, and listing the Actions open from there. Counts only: no
model, no database."""

from __future__ import annotations

import pytest

from qlsc.process import absorb, outlook
from qlsc.process.build import BuildError
from qlsc.process.source import Turn

P = {
    "states": 5,
    "temperature": 0.0,
    "level": 1,
    "prior": 0.0,
    "outcomes_shown": 3,
    "actions_shown": 5,
}


def turn(seq: int, kind: str) -> Turn:
    return Turn(
        f"e{seq}",
        "c",
        seq,
        "t",
        "voice_turn",
        "customer" if kind == "state" else "agent",
        kind,
        f"line {seq}",
    )


def stats() -> outlook.Stats:
    """Two States: s1 (10 conversations, 8 ended well) and s2 (10, 2 well); s1's cases took x (8 of them, 7 ended well) or y (2, 1 well)."""
    return outlook.Stats(
        state={
            "state:s1": {"name": "one", "n": 10, "good": 8, "kinds": {"fixed": 8, "lost": 2}},
            "state:s2": {"name": "two", "n": 10, "good": 2, "kinds": {"lost": 8, "fixed": 2}},
        },
        nexts={"state:s1": {"action:x": (8, 7), "action:y": (2, 1)}, "state:s2": {"action:y": (10, 1)}},
        action={
            "action:x": {"name": "do x", "n": 8, "good": 7},
            "action:y": {"name": "do y", "n": 12, "good": 2},
        },
        base=0.5,
    )


def test_the_nearest_state_counts_most_and_a_zero_temperature_counts_only_it():
    assert outlook.weights([0.9, 0.8], 0.0) == [1.0, 0.0]
    w = outlook.weights([0.9, 0.8, 0.9], 0.1)
    assert w[0] == w[2] == 1.0 and w[1] == pytest.approx(0.3678794)
    assert outlook.weights([0.9, 0.5], 1000.0) == pytest.approx(
        [1.0, 1.0], abs=1e-3
    )  # a high temperature: nearly uniform
    assert outlook.weights([], 0.1) == []


def test_counts_are_pooled_not_rates_so_a_big_state_weighs_what_it_has():
    got = outlook.pool(
        stats(), [("state:s1", 0.9), ("state:s2", 0.9)], {**P, "temperature": 1.0}, floor=3, prior=0.0
    )
    assert got["support"] == 20
    assert got["end_well"] == pytest.approx((8 + 2) / 20)
    assert got["outcomes"] == [("fixed", 0.5), ("lost", 0.5)]
    only = outlook.pool(stats(), [("state:s1", 0.9), ("state:s2", 0.5)], P, floor=3, prior=0.0)
    assert only["end_well"] == pytest.approx(0.8)  # the nearest only, at temperature 0


def test_a_pool_under_the_floor_carries_no_odds_and_says_so():
    thin = outlook.Stats({"state:t": {"name": "t", "n": 2, "good": 2, "kinds": {"fixed": 2}}}, {}, {}, 0.5)
    got = outlook.pool(thin, [("state:t", 0.9)], P, floor=3, prior=0.0)
    assert got["end_well"] is None and got["outcomes"] == [] and got["support"] == 2


def test_a_prior_pulls_a_thin_pool_toward_the_base_rate():
    thin = outlook.Stats({"state:t": {"name": "t", "n": 4, "good": 4, "kinds": {"fixed": 4}}}, {}, {}, 0.5)
    assert outlook.pool(thin, [("state:t", 0.9)], P, 3, 0.0)["end_well"] == 1.0
    assert outlook.pool(thin, [("state:t", 0.9)], P, 3, 4.0)["end_well"] == pytest.approx(0.75)


def test_the_actions_are_listed_by_how_often_reps_took_them_with_how_those_cases_ended():
    got = outlook.pool(
        stats(), [("state:s1", 0.9), ("state:s2", 0.9)], {**P, "temperature": 1.0}, floor=3, prior=0.0
    )
    names = [a["name"] for a in got["actions"]]
    assert names == ["do y", "do x"]  # y was taken 12 times, x 8
    y = got["actions"][0]
    assert y["probability"] == pytest.approx(12 / 20) and y["support"] == 12
    assert y["end_well_after"] == pytest.approx(2 / 12)  # no prior of its own: the pooled cases
    assert got["most_common"]["name"] == "do y"
    assert got["recommended"]["name"] == "do x"  # 7 of 8 ended well after it


def test_an_action_seen_a_few_times_is_pulled_toward_its_own_overall_rate_and_one_seen_under_the_floor_is_not_recommended():
    s = stats()
    s.nexts["state:s1"]["action:z"] = (1, 1)  # one case, which ended well
    s.action["action:z"] = {"name": "do z", "n": 1, "good": 1}
    got = outlook.pool(s, [("state:s1", 0.9)], {**P, "prior": 10.0}, floor=3, prior=0.0)
    z = next(a for a in got["actions"] if a["name"] == "do z")
    assert z["end_well_after"] == pytest.approx(
        (1 + 10 * 1.0) / 11
    )  # its own rate is 1 of 1: the pull is toward that, with the Action's own prior of 0
    assert got["recommended"]["name"] != "do z"  # one case is under the floor of 3


def test_the_counts_of_an_evaluation_give_the_same_pool_as_the_graphs_properties_would():
    rows = []
    found = {}
    for i, (end, good) in enumerate([("fixed", 1)] * 3 + [("lost", 0)]):
        c = f"c{i}"
        rows += [
            {"conversation": c, "seq": 0, "kind": "action", "element": "action:a"},
            {"conversation": c, "seq": 1, "kind": "state", "element": "state:s"},
            {"conversation": c, "seq": 2, "kind": "action", "element": "action:b"},
            {"conversation": c, "seq": 3, "kind": "state", "element": "state:t"},
        ]
        found[c] = {"type": end, "good": good}
    counts = absorb.Counts()
    for p in absorb.paths(rows, found):
        counts.add(p)
    s = outlook.stats_from_counts(counts, ["state:s"])
    assert s.state["state:s"] == {"name": "state:s", "n": 4, "good": 3, "kinds": {"fixed": 3, "lost": 1}}
    assert s.nexts["state:s"] == {"action:b": (4, 3)}
    assert s.action["action:b"]["n"] == 4 and s.base == pytest.approx(outlook.base_of(counts))
    got = outlook.pool(s, [("state:s", 0.99)], P, floor=3, prior=0.0)
    assert got["end_well"] == pytest.approx(0.75) and got["actions"][0]["probability"] == 1.0


def test_a_live_case_is_located_by_the_customers_latest_turn_up_to_where_it_has_got():
    turns = [turn(0, "action"), turn(1, "state"), turn(2, "action"), turn(3, "state"), turn(4, "action")]
    assert outlook.last_state(turns, None) == 3
    assert outlook.last_state(turns, 2) == 1
    with pytest.raises(BuildError):
        outlook.last_state(turns, 0)


# ----------------------------------------------------------------------------------------------------------------------- the tool


@pytest.fixture()
def s(tmp_path):
    from qlsc import config

    f = tmp_path / "estate.yaml"
    f.write_text(
        "business: {name: a bank, kind: bank}\nwarehouse: {gcloud_config: x}\nprocess:\n  events: events.ndjson\n"
        "  readers: [contact-center]\n"
    )
    return config.load(f)


def canned_outlook() -> dict:
    out = outlook.pool(
        stats(), [("state:s1", 0.9), ("state:s2", 0.9)], {**P, "temperature": 1.0}, floor=3, prior=0.0
    )
    out.pop("recommended")  # as `at` does
    return {
        "turn": 3,
        "state": "closing over a fee",
        "located": [{"id": "state:s1", "name": "one", "similarity": 0.9, "support": 10}],
        "outlook": out,
        "measured": {"seconds": 1.0},
    }


def test_a_live_conversation_is_turns_by_the_configs_roles_and_a_role_it_does_not_know_is_refused(s):
    from qlsc.process import source

    turns = source.live(s, [{"role": "agent", "text": "Hello"}, {"role": "customer", "text": "Hi, a fee"}])
    assert [(t.seq, t.kind) for t in turns] == [(0, "action"), (1, "state")]
    with pytest.raises(source.SourceError):
        source.live(s, [{"role": "robot", "text": "x"}])
    with pytest.raises(source.SourceError):
        source.live(s, [{"role": "customer", "text": "  "}])


def test_what_an_agent_is_shown_is_small_has_the_support_and_the_caution_and_no_recommendation():
    v = outlook.view(canned_outlook(), 5)
    assert "recommended" not in v and "recommended" not in str(v)
    assert v["caution"].startswith("Observational") and v["support"] == 20
    assert [a["action"] for a in v["next_actions"]] == ["do y", "do x"]
    assert set(v["next_actions"][0]) == {"action", "share", "cases", "ended_well_after"}


def test_only_the_readers_the_config_names_may_use_the_outlook(s):
    assert outlook.allowed(s, "contact-center") and not outlook.allowed(s, "marketing")


def test_the_outlook_tool_records_a_refusal_an_error_and_an_answer_as_steps(s, monkeypatch):
    from types import SimpleNamespace

    from qlsc import converse

    steps = []
    me = SimpleNamespace(
        s=s,
        m=SimpleNamespace(reader="marketing"),
        _new_step=lambda tool: "step-1",
        _attach=lambda step, arguments, result, status, error, seconds, fp: steps.append(
            (status, result, error)
        ),
    )
    lines = [{"role": "customer", "text": "I want to close my account"}]
    assert converse.Conversation.outlook(me, lines) is None
    assert steps[-1][0] == "refused" and "process.readers" in steps[-1][2]

    me.m = SimpleNamespace(reader="contact-center")
    assert converse.Conversation.outlook(me, [{"role": "robot", "text": "x"}]) is None
    assert steps[-1][0] == "error"

    monkeypatch.setattr(outlook, "at", lambda s_, turns, turn: canned_outlook())
    got = converse.Conversation.outlook(me, lines)
    assert got["end_well"] == pytest.approx(0.5) and steps[-1][0] == "ok" and steps[-1][1] == got

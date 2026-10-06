"""The build's pure parts (src/qlsc/process/build.py): the annotations it reads, the middle of an element, naming checks, folding by
name vectors, ids, and the lift of consecutive turns into counted transitions. The GDS grouping and the write need Neo4j and are
checked by building."""

from __future__ import annotations

import json

import pytest

from qlsc import config
from qlsc.process import build


@pytest.fixture()
def s(tmp_path):
    f = tmp_path / "estate.yaml"
    f.write_text("business: {name: a bank, kind: bank}\nwarehouse: {gcloud_config: x}\n")
    return config.load(f)


def turn(event, conversation, seq, kind, description="d", answer=None, problems=()):
    return {
        "event": event,
        "conversation": conversation,
        "seq": seq,
        "kind": kind,
        "description": description,
        "answer": answer or {},
        "problems": list(problems),
    }


def test_a_turn_with_no_description_or_a_problem_is_not_read(s):
    path = s.work / "process"
    path.mkdir()
    rows = [
        turn("a", "c", 0, "action"),
        turn("b", "c", 1, "state", description=""),
        turn("c", "c", 2, "action", problems=["x"]),
    ]
    (path / "annotations-turn.ndjson").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert [r["event"] for r in build.load(s)] == ["a"]
    (path / "annotations-turn.ndjson").unlink()
    with pytest.raises(build.BuildError, match="annotate"):
        build.load(s)


def test_what_is_embedded_for_a_state_is_a_parameter(s):
    r = turn(
        "a", "c", 0, "state", "line. established.", {"latest_turn": "line.", "established": " established. "}
    )
    assert build.text_to_embed(s, r) == "line. established."
    s["process"]["state_embeds"] = "established"
    assert build.text_to_embed(s, r) == "established."
    assert build.text_to_embed(s, turn("b", "c", 1, "action", "Greet the customer")) == "Greet the customer"


def test_the_middle_of_an_element_is_its_mean_and_the_closest_come_first():
    vec = {"a": [1.0, 0.0], "b": [0.9, 0.1], "c": [0.0, 1.0]}
    assert build.closest(["a", "b", "c"], {k: build.unit(v) for k, v in vec.items()}, 2) == ["b", "a"]
    assert [round(x, 3) for x in build.centre(["a"], {"a": [3.0, 4.0]})] == [0.6, 0.8]
    assert round(sum(x * x for x in build.centre(["a", "b"], vec)), 6) == 1.0  # a unit vector


def test_an_actions_name_must_begin_with_a_listed_verb_and_a_states_need_not(s):
    action, state = build.name_check(s, "action"), build.name_check(s, "state")
    good = {"name": "Verify the customer's identity", "description": "The agent verifies who is calling."}
    assert action(good) is None
    assert "must begin with" in action({**good, "name": "Request the account number"})
    assert (
        state(
            {
                "name": "Fee dispute, caller not verified",
                "description": "A fee is disputed before verification.",
            }
        )
        is None
    )
    assert state({"name": "Fee", "description": "A fee is disputed before verification."})  # too short a name


class Names:
    """Name vectors from a table, in place of the embedder."""

    def __init__(self, vectors):
        self.vectors = vectors

    def embed(self, texts):
        return [self.vectors[t] for t in texts]


def test_folding_is_greedy_largest_first_and_never_a_chain(s):
    s["process"]["fold_similarity"] = 0.9
    # a~b and b~c but not a~c: c must not join a through b
    vectors = {
        "A": build.unit([1.0, 0.0, 0.0]),
        "B": build.unit([1.0, 0.45, 0.0]),
        "C": build.unit([1.0, 0.9, 0.0]),
    }
    groups = {"a": ["a1", "a2", "a3"], "b": ["b1", "b2"], "c": ["c1"]}
    named = {"a": {"name": "A"}, "b": {"name": "B"}, "c": {"name": "C"}}
    out = build.fold(s, groups, named, Names(vectors))
    assert out == {"a": ["a1", "a2", "a3", "b1", "b2"], "c": ["c1"]}


def test_an_element_id_is_its_kind_and_a_hash_of_its_name():
    assert build.element_id("state", "Fee dispute") == build.element_id("state", "Fee dispute")
    assert build.element_id("state", "Fee dispute") != build.element_id("action", "Fee dispute")
    assert build.element_id("state", "x").startswith("state:")


def test_consecutive_turns_become_counted_transitions_and_the_last_turn_ends():
    rows = [
        turn("1", "c1", 0, "action"),
        turn("2", "c1", 1, "state"),
        turn("3", "c1", 2, "action"),
        turn("4", "c2", 0, "action"),
        turn("5", "c2", 1, "state"),
        turn("6", "c2", 2, "state"),  # two States in a row: no transition between them
    ]
    of = {"1": "A1", "2": "S1", "3": "A2", "4": "A1", "5": "S1", "6": "S2"}
    count, ends, num = build.lift(rows, of)
    assert num == {("A1", "S1"): 2, ("S1", "A2"): 1}
    assert count == {"A1": 2, "S1": 2, "A2": 1, "S2": 1}
    assert ends == {
        "A2": 1,
        "S1": 1,
        "S2": 1,
    }  # a turn with no valid successor ends; a probability is num / count
    # lifting again over the same turns gives the same counts: by assignment, never added to
    assert build.lift(rows, of)[2] == num


def test_a_composite_alias_is_a_plain_name_or_it_is_refused(s):
    s["process"]["composite"] = {"database": "fennmoor; DROP DATABASE x", "url": "neo4j+ssc://x:7687"}
    s["virtualize"] = {"neo4j": {"uri": "bolt://localhost:1", "database": "neo4j"}}
    with pytest.raises(build.BuildError, match="plain composite alias"):
        build.join_composite(s)
    s["process"]["composite"] = None
    assert build.join_composite(s) is None  # none configured, nothing done

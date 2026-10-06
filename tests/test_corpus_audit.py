"""The audit of a written corpus (examples/fennmoor-bank/generate/corpus_audit.py): it must pass a corpus that agrees with its
plans and its rows, and say which check failed when one does not. No model and no warehouse: a stub corpus on the synthetic pool."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest
from test_corpus_plan import synthetic_pool

GENERATE = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "generate"
sys.path.insert(0, str(GENERATE))

import corpus_audit  # noqa: E402
import corpus_plan  # noqa: E402
import corpus_text  # noqa: E402
import corpus_world  # noqa: E402


@pytest.fixture(scope="module")
def world():
    return corpus_world.load_world()


@pytest.fixture()
def written(world, tmp_path):
    pool = synthetic_pool(world)
    plans, _ = corpus_plan.generate(world, pool, 7, 150)
    with gzip.open(tmp_path / "plans.ndjson.gz", "wt") as out:
        for p in plans:
            out.write(json.dumps(p, sort_keys=True, default=str) + "\n")
    corpus_text.realise(world, None, plans, 7, None, True, tmp_path)
    return world, pool, tmp_path


def lines(world, pool, folder):
    text, _ = corpus_audit.audit(world, folder, folder / "plans.ndjson.gz", pool)
    return [x for x in text.splitlines() if x.strip().startswith("FAIL")]


def rewrite(path: Path, edit) -> None:
    with gzip.open(path, "rt") as handle:
        rows = [json.loads(line) for line in handle]
    edit(rows)
    with gzip.open(path, "wt") as out:
        for r in rows:
            out.write(json.dumps(r, sort_keys=True) + "\n")


def test_a_corpus_that_agrees_with_its_rows_passes_the_warehouse_checks(written):
    world, pool, folder = written
    failed = lines(world, pool, folder)
    # the stub's placeholder text is not meant to pass the gates or the wording checks, only the checks against the rows
    assert not [x for x in failed if "warehouse" in x or "row" in x or "event ids" in x or "callback" in x]


def test_an_event_by_the_wrong_agent_is_found(written):
    world, pool, folder = written

    def edit(events):
        next(e for e in events if e["role"] == "agent")["agent_user_id"] = "someone-else"

    rewrite(folder / "events.ndjson.gz", edit)
    assert any("the row's own agent" in x for x in lines(world, pool, folder))


def test_a_conversation_the_warehouse_does_not_have_is_found(written):
    world, pool, folder = written
    rewrite(folder / "events.ndjson.gz", lambda events: events[0].update(conversation_id="nowhere"))
    assert any("in the warehouse" in x for x in lines(world, pool, folder))


def test_an_identifier_in_the_text_is_found(written):
    world, pool, folder = written
    rewrite(folder / "events.ndjson.gz", lambda events: events[0].update(text="my number is 123456789012"))
    assert any("identifier" in x for x in lines(world, pool, folder))


def test_a_plan_row_that_drifted_from_the_warehouse_is_found(written):
    world, pool, folder = written
    rewrite(folder / "truth.ndjson.gz", lambda truth: truth[0]["row"].update(ivr_intent="DRIFTED"))
    assert any("field for field" in x for x in lines(world, pool, folder))


def test_a_mention_of_a_fee_the_customer_never_had_is_found(written):
    world, pool, folder = written

    def edit(truth):
        t = next(t for t in truth if t["events"])
        t["events"][0]["mentions"] = [{"type": "Fee", "key": "no-such-fee"}]

    rewrite(folder / "truth.ndjson.gz", edit)
    assert any("fee and merchant" in x for x in lines(world, pool, folder))

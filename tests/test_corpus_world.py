"""The process corpus's world validator (examples/fennmoor-bank/generate/corpus_world.py): the shipped world is clean,
and each kind of authoring error it exists to catch is caught."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
import yaml

GENERATE = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "generate"
spec = importlib.util.spec_from_file_location("corpus_world", GENERATE / "corpus_world.py")
cw = importlib.util.module_from_spec(spec)
sys.modules["corpus_world"] = cw
spec.loader.exec_module(cw)


@pytest.fixture
def world(tmp_path):
    """A copy of the shipped world to break."""
    dest = tmp_path / "corpus"
    shutil.copytree(cw.WORLD, dest, ignore=shutil.ignore_patterns("README.md"))
    return dest


def edit(path: Path, change):
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data))


def errors(path: Path) -> list[str]:
    return cw.validate(path)[0].errors


def test_shipped_world_is_clean():
    report, counts = cw.validate()
    assert report.errors == [] and report.warnings == []
    assert counts["procedures"] == 5 and counts["causes"] >= 30


def test_every_intent_has_exactly_one_procedure():
    w = cw.load_world()
    assert set(w.intent_procedure) == cw.INTENTS


def test_servicing_is_the_control(world):
    # A discriminating manifestation in the control family would be a pipeline's invention made real.
    edit(
        world / "causes.yaml",
        lambda d: next(c for c in d if c["id"] == "CAU-SRV-BALANCE")["manifestations"].append(
            {"id": "MAN-RET-FEE-ON-STATEMENT", "probability": 0.5}
        ),
    )
    assert any("nothing discriminating" in e for e in errors(world))


def test_a_cause_nothing_fixes_is_an_error(world):
    edit(
        world / "efficacy.yaml",
        lambda d: d.__setitem__(
            slice(None), [e for e in d if e["action"] != "ACT-WARN-SCAM-AND-RECALL-PAYMENT"]
        ),
    )
    assert any("CAU-FRD-SCAM-VICTIM" in e and "fixes" in e for e in errors(world))


def test_a_cause_no_procedure_holds_is_an_error(world):
    def drop(d):
        next(p for p in d if p["id"] == "PROC-PAYMENT-FEES")["hypotheses"].remove("CAU-PAY-HOW-TO")

    edit(world / "procedures.yaml", drop)
    assert any("CAU-PAY-HOW-TO" in e and "held by 0" in e for e in errors(world))


def test_a_discriminator_no_action_elicits_is_an_error(world):
    edit(
        world / "actions.yaml",
        lambda d: d.__setitem__(slice(None), [a for a in d if a["id"] != "ACT-ASK-COMPETING-OFFER"]),
    )
    assert any("MAN-RET-COMPETING-RATE" in e for e in errors(world))


def test_a_gate_nothing_can_satisfy_is_an_error(world):
    def break_gate(d):
        next(p for p in d if p["id"] == "POL-DISPUTE-WINDOW-CHECKED")["satisfied_by"] = ["ACT-GIVE-BALANCE"]

    edit(world / "policies.yaml", break_gate)
    assert any("POL-DISPUTE-WINDOW-CHECKED" in e and "cannot be satisfied" in e for e in errors(world))


def test_shares_must_sum(world):
    edit(world / "domains.yaml", lambda d: d[0].__setitem__("share", 0.5))
    assert any("domains: shares sum" in e for e in errors(world))


def test_a_rep_archetype_cannot_dictate(world):
    edit(world / "reps.yaml", lambda d: d["archetypes"][0].__setitem__("policy_compliance", 1.0))
    assert any("strictly between" in e for e in errors(world))


def test_the_last_outcome_is_the_fallback(world):
    edit(world / "outcomes.yaml", lambda d: d["outcomes"].pop())
    assert any("fallback" in e for e in errors(world))

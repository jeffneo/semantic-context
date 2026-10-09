"""Write the demo UI's picture of the accuracy comparison -> ui/src/examples/fennmoor/accuracy/accuracy.json.

The comparison (eval/comparison/README.md) has four methods answer the same 186 questions: 10 hand-written gold questions and 176 written from
queries the business ran. This keeps what a page needs to show it: the totals per method (results/comparison.json), and for every question its text and
each method's verdict, tokens, seconds, cost and query (work/comparison/<method>.json). The log questions carry the business's own query, the
reference they were scored against. The gold questions' answer key (the tables a good answer should use) is not written.

Run `eval/comparison/run.py report` first. Deterministic. Usage: uv run examples/fennmoor-bank/generate/ui_accuracy.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import yaml

from qlsc import config

EXAMPLE = Path(__file__).resolve().parents[1]
PROJECT = config.load(EXAMPLE / "estate.yaml")["warehouse"][
    "project"
]  # the physical project: never in what is written
ROOT = EXAMPLE.parents[1]
RESULT = EXAMPLE / "results" / "comparison.json"
WORK = EXAMPLE / "work" / "comparison"
GOLD = EXAMPLE / "spec" / "questions.yaml"
LOG = EXAMPLE / "eval" / "log_questions.yaml"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "accuracy" / "accuracy.json"

METHODS = [
    (
        "naive-schema",
        "The schema in the prompt",
        "Every table and column in the prompt: one query, one fix after a failed dry run.",
    ),
    (
        "naive-agent",
        "A generic agent",
        "Tools to list tables, describe them and run SQL over the same schema.",
    ),
    ("layer", "The layer, one shot", "The compiled request from the semantic layer, with no agent."),
    (
        "agent",
        "An agent using the layer",
        "The agent holds its process's state, writes its request, checks each answer and corrects it; the layer answers by precedent first.",
    ),
]
IDS = [m[0] for m in METHODS]


def clean(text: str) -> str:
    """Nothing here may name the physical project the estate is deployed to."""
    assert PROJECT not in text and "fnb_" not in text, "a query names the physical project"
    return text


def main() -> None:
    totals = json.loads(RESULT.read_text())
    runs = {
        m: {k: v for k, v in json.loads((WORK / f"{m}.json").read_text()).items() if k != "_run"} for m in IDS
    }
    gold = yaml.safe_load(GOLD.read_text())["questions"]
    log = yaml.safe_load(LOG.read_text())

    questions = []
    for qid in sorted(runs["agent"], key=lambda q: (q[0] != "Q", q)):  # the gold questions, then the log's
        is_gold = qid in gold
        q = {
            "id": qid,
            "group": "gold" if is_gold else "log",
            "text": (gold if is_gold else log)[qid]["question"],
            "r": {},
        }
        if not is_gold:
            q["who"] = log[qid].get("who")
            q["ref"] = clean(log[qid]["sql"])
        for m in IDS:
            r = runs[m][qid]
            q["r"][m] = {
                "v": r["verdict"],
                "why": "" if r["verdict"] == "correct" else r["why"],
                "d": bool(r["delivered"]),
                "t": r["measure"]["tokens"],
                "s": r["measure"]["seconds"],
                "c": r["measure"]["cost"],
                "sql": clean(r.get("sql") or ""),
            }
        a = runs["agent"][qid]
        q["agent"] = {"route": a["turns"][0]["route"], "outcome": a["outcome"], "turns": len(a["turns"])}
        questions.append(q)

    # What a first answer was, and how those did: a precedent (the business's own query for a request like this) or a compiled request.
    firsts = {"precedent": [], "compiled": []}
    for r in runs["agent"].values():
        t = r["turns"][0]
        firsts["precedent" if t["route"] == "precedent" else "compiled"].append(t)
    routes = {
        name: {
            "n": len(ts),
            "right": sum(t["verdict"] == "correct" for t in ts),
            "tokens_p50": statistics.median(t["tokens"] for t in ts),
            "seconds_p50": statistics.median(t["seconds"] for t in ts),
        }
        for name, ts in firsts.items()
    }

    out = {
        "targets": json.loads((WORK / "agent.json").read_text())["_run"]["targets"],
        "methods": [
            {"id": i, "name": n, "blurb": b, "log": totals[i]["log"], "gold": totals[i]["gold"]}
            for i, n, b in METHODS
        ],
        "outcomes": totals["agent"]["outcomes"],
        "routes": routes,
        "questions": questions,
    }
    for m in out["methods"]:  # the totals carry the run's commit and replay flags: not what the page shows
        for g in ("log", "gold"):
            m[g] = {k: v for k, v in m[g].items() if k not in ("commit", "replayed")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"{OUT.relative_to(ROOT)}: {len(questions)} questions, {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

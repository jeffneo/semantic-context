"""Write the demo UI's picture of the router -> ui/src/examples/fennmoor/router/router.json.

The router (qlsc/navigate.py `route`) is a rule, not a model: the first of memory, a precedent, compiled SQL, free Cypher and free SQL whose answer
stands. Each rung has been measured by the evaluation that exercised it, and this keeps those figures, each from its own results file:
  memory      results/economics.json: 50 questions about 5 customers, answered from memory against the same SQL in BigQuery
  precedent   work/comparison/agent.json: the agent's first answers (eval/comparison): a precedent, or a compiled or free SQL request
  compiled    results/log_accuracy.json: 176 questions from the log, one shot, both routes scored; the router's pick
  cypher      results/graph_accuracy.json: ten questions natural over a graph, both routes scored, and the same on the 176
  graph       how many tables the Virtual Graph models (work/virtual/schema.json), and the graph-shaped questions: both routes scored
  trace       the ten graph-shaped questions as they fell down the ladder: compiled SQL declined (and why), Cypher answered or declined, free SQL
Nothing is tuned for the page. The evaluations did not all exercise every rung (the comparison's agent had precedent, compiled and free SQL; the graph
questions had compiled, Cypher and free), and `sets` says which did.

Run the evaluations first (results/ is committed; work/comparison needs `eval/comparison/run.py agent`). Deterministic.
Usage: uv run examples/fennmoor-bank/generate/ui_router.py
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path

from qlsc import config

EXAMPLE = Path(__file__).resolve().parents[1]
PROJECT = config.load(EXAMPLE / "estate.yaml")["warehouse"][
    "project"
]  # the physical project: never in what is written
ROOT = EXAMPLE.parents[1]
RESULTS = EXAMPLE / "results"
AGENT = EXAMPLE / "work" / "comparison" / "agent.json"
SCHEMA = EXAMPLE / "work" / "virtual" / "schema.json"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "router" / "router.json"

MIB = 1024 * 1024


def memory() -> dict:
    s = json.loads((RESULTS / "economics.json").read_text())["summary"]
    return {
        "questions": s["questions"],
        "fromMemory": s["from memory"],
        "sameRows": s["same answer"],
        "memoryMedian": s["memory latency"]["median"],
        "sqlMedian": s["sql latency"]["median"],
        "compileMedian": s["compile latency"]["median"],
        "sessionSecondsWithout": round(s["without memory"]["seconds"], 1),
        "sessionSecondsWith": round(s["with memory"]["seconds"], 1),
        "sessionMibWithout": round(s["without memory"]["billed"] / MIB),
        "sessionMibWith": round(s["with memory"]["billed"] / MIB),
    }


def agent() -> dict:
    """The comparison's agent: what its first answers were, and how those did."""
    runs = {k: v for k, v in json.loads(AGENT.read_text()).items() if k != "_run"}
    firsts: dict[str, list] = {"precedent": [], "sql": []}
    for r in runs.values():
        t = r["turns"][0]
        firsts["precedent" if t["route"] == "precedent" else "sql"].append(t)
    return {
        name: {
            "n": len(ts),
            "right": sum(t["verdict"] == "correct" for t in ts),
            "tokensMedian": statistics.median(t["tokens"] for t in ts),
            "secondsMedian": statistics.median(t["seconds"] for t in ts),
        }
        for name, ts in firsts.items()
    }


def log() -> dict:
    """The 176 log questions through both routes and the router: what it picked, how each route did on its own."""
    qs = json.loads((RESULTS / "log_accuracy.json").read_text())
    by_pick = {"sql": {"n": 0, "right": 0}, "cypher": {"n": 0, "right": 0}}
    rungs = {"compiled": {"n": 0, "right": 0}, "cypher": {"n": 0, "right": 0}, "free": {"n": 0, "right": 0}}
    for q in qs.values():
        pick = q["routed"]["route"]
        rung = (
            "compiled" if q["sql"]["writer"] == "compiled" else "cypher" if pick == "cypher" else "free"
        )  # compiled SQL stands when it compiled
        for c in (by_pick[pick], rungs[rung]):
            c["n"] += 1
            c["right"] += q["routed"]["verdict"] == "correct"
    writers = Counter(q["sql"]["writer"] for q in qs.values())
    compiled_right = sum(
        q["sql"]["verdict"] == "correct" for q in qs.values() if q["sql"]["writer"] == "compiled"
    )
    free_right = sum(q["sql"]["verdict"] == "correct" for q in qs.values() if q["sql"]["writer"] == "free")
    cypher = Counter(q["cypher"]["verdict"] for q in qs.values())
    return {
        "n": len(qs),
        "picked": by_pick,
        "rungs": rungs,
        "compiled": {"n": writers["compiled"], "right": compiled_right},
        "free": {"n": writers["free"], "right": free_right},
        "sqlRight": sum(q["sql"]["verdict"] == "correct" for q in qs.values()),
        "cypher": {k: cypher[k] for k in ("correct", "wrong", "empty", "failed", "declined", "not covered")},
        "eitherRight": sum("correct" in (q["sql"]["verdict"], q["cypher"]["verdict"]) for q in qs.values()),
    }


def graph() -> tuple[dict, list]:
    """The ten graph-shaped questions: how the router picked, and each question's fall down the ladder."""
    qs = {
        k: v
        for k, v in json.loads((RESULTS / "graph_accuracy.json").read_text()).items()
        if re.fullmatch(r"G\d+", k)
    }
    by_pick = {"sql": {"n": 0, "right": 0}, "cypher": {"n": 0, "right": 0}}
    trace = []
    for k, q in sorted(qs.items()):
        pick = q["routed"]["route"]
        by_pick[pick]["n"] += 1
        by_pick[pick]["right"] += q["routed"]["verdict"] == "correct"
        compiled = q["sql"]["writer"] == "compiled"
        cypher_declined = q["cypher"]["verdict"] in ("declined", "not covered", "failed")
        trace.append(
            {
                "id": k,
                "text": q["question"],
                "rows": q["reference_rows"],
                # each rung the router reached: served, or why not
                "compiled": {
                    "state": "served" if compiled else "declined",
                    "why": "" if compiled else q["sql"]["fallback"],
                },
                "cypher": (
                    {"state": "not reached", "why": ""}
                    if compiled
                    else {"state": "declined", "why": q["cypher"]["why"]}
                    if cypher_declined
                    else {"state": "served", "why": ""}
                ),
                "free": {"state": "served" if pick == "sql" and not compiled else "not reached", "why": ""},
                "routed": "compiled" if compiled else pick if pick == "cypher" else "free",
                "verdict": q["routed"]["verdict"],
                "verdictWhy": q[pick]["why"],
                "query": q[pick]["query"],
                "queryKind": "cypher" if pick == "cypher" else "sql",
            }
        )
    alone = {r: sum(q[r]["verdict"] == "correct" for q in qs.values()) for r in ("sql", "cypher")}
    return {"picked": by_pick, "sqlRight": alone["sql"], "cypherRight": alone["cypher"]}, trace


def main() -> None:
    graph_stats, trace = graph()
    out = {
        "memory": memory(),
        "agent": agent(),
        "log": log(),
        "graph": {
            "n": len(trace),
            "tables": len(json.loads(SCHEMA.read_text())["entities"]["nodes"]),
            **graph_stats,
        },
        "trace": trace,
    }
    text = json.dumps(out, separators=(",", ":"), sort_keys=True)
    assert PROJECT not in text and "fnb_" not in text, "the physical project or its dataset prefix is named"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n")
    print(f"{OUT.relative_to(ROOT)}: {len(trace)} traced questions, {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

"""A quick, directional A/B of one navigation setting, on the SQL route: minutes, not an hour.

The ten gold questions scored by value, and every STEP-th question written from the log (leave-one-out
as in log_accuracy.py), answered with the navigation parameters as configured plus the overrides given.
Run it twice, once per setting, and compare the two result files.

Writes results/qdd_<name>.md and .json. Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/qdd.py <name> [--all] [param=value ...]   (--all: every log question)
  e.g. qdd.py base computations=0     qdd.py definitions computations=5
"""

from __future__ import annotations

import json
import sys

import yaml
from common import RESULTS, SPEC, settings, write_result
from execution import ROWS, judge, references
from log_accuracy import verdict_of
from log_questions import QUESTIONS, answers_dir

from qlsc.graph import Graph
from qlsc.navigate import answer_sql, trace
from qlsc.warehouse import connect

STEP = 6  # every sixth log question: about 30


def main() -> int:
    every = "--all" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--all"]
    name, overrides = args[0], dict(a.split("=", 1) for a in args[1:])
    step = 1 if every else STEP
    s = settings()
    for k, v in overrides.items():
        s.params["navigate"][k] = yaml.safe_load(v)
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    logq = yaml.safe_load(QUESTIONS.read_text())
    kept = [
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    ]
    wh, res = connect(s), {}
    todo = [("gold", q) for q in sorted(gold)] + [("log", q) for q in kept[::step]]
    with Graph(s) as G:
        for i, (src, qid) in enumerate(todo, 1):
            if src == "gold":
                refs = references(wh, qid)
                if not refs[0]["items"]:
                    continue
                tr = trace(G, s, gold[qid]["question"])
            else:
                q = logq[qid]
                ref = json.loads((answers_dir(s) / f"{qid}.json").read_text())
                tr = trace(G, s, q["question"], exclude=frozenset({q["shape"]}))
            a = answer_sql(G, s, tr, execute=True, rows=ROWS)
            if src == "gold":
                got = a.get("result")
                ok = got is not None and got.get("ok", True)
                v, why = judge(refs, got) if ok else ("failed", str((got or {}).get("error"))[:100])
            else:
                v, why = verdict_of(a, ref, [[c] for c in q["compare"]])
            res[qid] = {
                "source": src,
                "verdict": v,
                "why": why,
                "sql": a.get("sql"),
                "definitions": [d["name"] for d in tr.get("definitions", [])],
            }
            print(f"{i}/{len(todo)} {qid} {v:10} {why[:90]}", flush=True)
    n = lambda src: (
        sum(1 for r in res.values() if r["source"] == src and r["verdict"] == "correct"),
        sum(1 for r in res.values() if r["source"] == src),
    )
    (g, gn), (lg, ln) = n("gold"), n("log")
    L = [f"# Quick A/B: {name}", "", f"Overrides: {overrides or 'none'}. SQL route.", ""]
    which = "all" if every else f"every {STEP}th"
    L += [f"Gold questions: {g} of {gn} correct. Log questions ({which}): {lg} of {ln}.", ""]
    L += ["| question | verdict |", "|---|---|"]
    L += [f"| {q} | {r['verdict']}: {r['why']}".replace("\n", " ")[:200] + " |" for q, r in res.items()]
    print(f"gold {g}/{gn}, log {lg}/{ln} -> {write_result(f'qdd_{name}', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

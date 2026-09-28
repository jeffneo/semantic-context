"""A quick, directional A/B of one navigation setting, on the SQL route: minutes, not an hour.

The ten gold questions scored by value, and every STEP-th question written from the log (leave-one-out
as in log_accuracy.py), answered with the navigation parameters as configured plus the overrides given.
Run it twice, once per setting, and compare the two result files.

Writes results/qdd_<name>.md and .json. Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/qdd.py <name> [--all | --offset=N] [--route=cypher] [param=value ...]
  (--all: every log question; --offset: which of each STEP questions to take, for a second sample;
   --route=cypher: the Cypher route over the Virtual Graph instead of SQL)
  e.g. qdd.py base computations=0     qdd.py definitions computations=5
"""

from __future__ import annotations

import json
import sys
from collections import Counter

import yaml
from common import RESULTS, SPEC, settings, write_result
from execution import ROWS, judge, references
from log_accuracy import verdict_of
from log_questions import QUESTIONS, answers_dir

from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, trace
from qlsc.warehouse import connect

STEP = 6  # every sixth log question: about 30


def main() -> int:
    every = "--all" in sys.argv
    offset = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--offset=")), 0)
    route = next((a.split("=")[1] for a in sys.argv if a.startswith("--route=")), "sql")
    answer = {"sql": answer_sql, "cypher": answer_cypher}[route]
    args = [a for a in sys.argv[1:] if a != "--all" and not a.startswith(("--offset=", "--route="))]
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
    if (probe := wh.dry_run("SELECT 1"))["ok"] is not True:  # fail now, not after an hour of failed queries
        raise SystemExit(f"the warehouse isn't reachable: {probe.get('error')}")
    todo = [("gold", q) for q in sorted(gold)] + [("log", q) for q in kept[offset::step]]
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
            a = answer(G, s, tr, execute=True, rows=ROWS)
            if src == "gold" and ("skipped" in a or "declined" in a):
                v, why = ("not covered", a["skipped"]) if "skipped" in a else ("declined", a["declined"])
            elif src == "gold":
                got = a.get("result")
                ok = got is not None and got.get("ok", True)
                failure = (got or {}).get("error") or a.get("error") or a.get("check", {}).get("error")
                v, why = judge(refs, got) if ok else ("failed", str(failure)[:100])
            else:
                v, why = verdict_of(a, ref, [[c] for c in q["compare"]])
            res[qid] = {
                "source": src,
                "verdict": v,
                "why": why,
                "sql": a.get("sql") or a.get("cypher"),
                "definitions": [d["name"] for d in tr.get("definitions", [])],
                "writer": a.get("writer"),
                "fallback": a.get("fallback"),
            }
            print(f"{i}/{len(todo)} {qid} {v:10} {(a.get('writer') or '')[:8]:8} {why[:80]}", flush=True)
            if "fresh login" in why:  # the credentials expired mid-run: every answer from here would fail
                raise SystemExit(f"stopped at {qid}: {why}")
    n = lambda src: (
        sum(1 for r in res.values() if r["source"] == src and r["verdict"] == "correct"),
        sum(1 for r in res.values() if r["source"] == src),
    )
    (g, gn), (lg, ln) = n("gold"), n("log")
    L = [
        f"# Quick A/B: {name}",
        "",
        f"Overrides: {overrides or 'none'}. {route.upper() if route == 'sql' else 'Cypher'} route.",
        "",
    ]
    which = "all" if every else f"every {STEP}th"
    L += [f"Gold questions: {g} of {gn} correct. Log questions ({which}): {lg} of {ln}.", ""]
    writers = Counter(r["writer"] for r in res.values())
    if writers.get("compiled"):
        fits = sum(1 for r in res.values() if r["writer"] == "compiled" and r["verdict"] == "correct")
        L += [
            f"Compiled {writers['compiled']} of {len(res)} ({fits} correct); fell back to free writing for {writers.get('free', 0)}.",
            "",
        ]
    L += ["| question | verdict |", "|---|---|"]
    L += [f"| {q} | {r['verdict']}: {r['why']}".replace("\n", " ")[:200] + " |" for q, r in res.items()]
    print(
        f"gold {g}/{gn}, log {lg}/{ln}, writers {dict(Counter(r['writer'] for r in res.values()))} -> {write_result(f'qdd_{name}', L, res)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

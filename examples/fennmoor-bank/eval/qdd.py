"""A quick, directional A/B of one setting, on one route: minutes, not an hour.

The ten gold questions scored by value, and every STEP-th question written from the log (leave-one-out
as in log_accuracy.py), answered with the parameters as configured plus the overrides given. Run it
twice, once per setting, and compare the two result files. An experiment, not a result the docs quote:
it writes to <work>/qdd/, with the commit it ran at and the overrides.

Writes <work>/qdd/<name>.md and .json. Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/qdd.py <name> [--all | --offset=N] [--route=cypher] [param=value ...]
  (--all: every log question; --offset: which of each STEP questions to take, for a second sample;
   --route=cypher: the Cypher route over the Virtual Graph instead of SQL)
  e.g. qdd.py base     qdd.py free writer=free     qdd.py effort llm.query_effort=high
Each question records the query model's uncached calls: their API seconds and tokens.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

import yaml
from common import RESULTS, SPEC, commit, overrides, settings, write_result
from log_questions import QUESTIONS, answers_dir
from match import ROWS, LLMUsage, references, verdict

from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, trace
from qlsc.warehouse import connect

STEP = 6  # every sixth log question: about 30


def main() -> int:
    every = "--all" in sys.argv
    offset = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--offset=")), 0)
    route = next((a.split("=")[1] for a in sys.argv if a.startswith("--route=")), "sql")
    answer = {"sql": answer_sql, "cypher": answer_cypher}[route]
    s = settings()
    args, _ = overrides(
        s, [a for a in sys.argv[1:] if a != "--all" and not a.startswith(("--offset=", "--route="))]
    )
    name, sets = args[0], [a for a in sys.argv[1:] if "=" in a and not a.startswith("--")]
    usage = LLMUsage()
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    logq = yaml.safe_load(QUESTIONS.read_text())
    kept = [
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    ]
    wh, res = connect(s), {}
    if (probe := wh.dry_run("SELECT 1"))["ok"] is not True:  # fail now, not after an hour of failed queries
        raise SystemExit(f"the warehouse isn't reachable: {probe.get('error')}")
    todo = [("gold", q) for q in sorted(gold)] + [("log", q) for q in kept[offset :: 1 if every else STEP]]
    with Graph(s) as G:
        for i, (src, qid) in enumerate(todo, 1):
            if src == "gold":
                refs = references(wh, qid)
                if not refs[0]["items"]:
                    continue
                tr = trace(G, s, gold[qid]["question"])
            else:
                q = logq[qid]
                refs = [{"name": qid, "items": [[c] for c in q["compare"]],
                         "result": json.loads((answers_dir(s) / f"{qid}.json").read_text())}]  # fmt: skip
                tr = trace(G, s, q["question"], exclude=frozenset({q["shape"]}))
            usage.made.clear()
            a = answer(G, s, tr, execute=True, rows=ROWS)
            v, why = verdict(a, refs)
            res[qid] = {
                "source": src,
                "verdict": v,
                "why": why,
                "sql": a.get("sql") or a.get("cypher"),
                "writer": a.get("writer"),
                "fallback": a.get("fallback"),
                "llm": usage.spent(),
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
        f"At {commit()}. Overrides: {', '.join(sets) or 'none'}. {'SQL' if route == 'sql' else 'Cypher'} route.",
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
    spent = [r["llm"] for r in res.values() if r["llm"]["calls"]]
    if spent:
        L += [
            f"Query model, over the {len(spent)} questions it wasn't cached for ({sum(x['calls'] for x in spent)} calls): "
            f"{sum(x['seconds'] for x in spent) / len(spent):.1f} s per question in the API, "
            f"{sum(x['tokens_in'] for x in spent) / len(spent):,.0f} tokens in and "
            f"{sum(x['tokens_out'] for x in spent) / len(spent):,.0f} out per question.",
            "",
        ]
    L += ["| question | verdict |", "|---|---|"]
    L += [f"| {q} | {r['verdict']}: {r['why']}".replace("\n", " ")[:200] + " |" for q, r in res.items()]
    out = write_result(
        name, L, res | {"_run": {"commit": commit(), "overrides": sets, "route": route}}, s.work / "qdd"
    )
    print(f"gold {g}/{gn}, log {lg}/{ln}, writers {dict(writers)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

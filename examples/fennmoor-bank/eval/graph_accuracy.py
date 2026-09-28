"""Graph-shaped questions (eval/graph_questions.yaml) through `qlsc ask`, by both routes.

The log's questions are what is easy in SQL. These are written by hand to show questions natural over
the virtual graph: an entity's neighbourhood, several hops, shared neighbours, a cycle. A quick,
directional check (ten questions, a few minutes), scored like the others (execution.py's matcher).

Writes results/graph_accuracy.md and .json. Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/graph_accuracy.py [G01 ...] [param=value ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from common import settings, write_result
from execution import MAXIMUM_BYTES_BILLED, ROUTES, ROWS
from log_accuracy import verdict_of

from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, trace
from qlsc.warehouse import connect

QUESTIONS = Path(__file__).resolve().parent / "graph_questions.yaml"


def main() -> int:
    s = settings()
    overrides = [a for a in sys.argv[1:] if "=" in a]
    for a in overrides:  # navigate overrides: writer=compiled
        k, v = a.split("=", 1)
        s.params["navigate"][k] = yaml.safe_load(v)
    qs = yaml.safe_load(QUESTIONS.read_text())
    wanted = [a for a in sys.argv[1:] if "=" not in a] or list(qs)
    wh, res = connect(s), {}
    with Graph(s) as G:
        for i, qid in enumerate(wanted, 1):
            q = qs[qid]
            ref = wh.run(q["sql"], MAXIMUM_BYTES_BILLED, ROWS)
            items = [[c] for c in q["compare"]]
            tr = trace(G, s, q["question"])
            out = {"question": q["question"], "reference_rows": ref.get("total"), "cohort": tr["top"]}
            for route, answer in (("sql", answer_sql), ("cypher", answer_cypher)):
                a = answer(G, s, tr, execute=True, rows=ROWS)
                v, why = verdict_of(a, ref, items) if ref["ok"] else ("no reference", ref["error"][:100])
                out[route] = {
                    "verdict": v,
                    "why": why,
                    "query": a.get("sql") or a.get("cypher"),
                    "writer": a.get("writer"),
                    "fallback": a.get("fallback"),
                }
                print(f"{i}/{len(wanted)} {qid} {route:6} {v:12} {why[:90]}", flush=True)
            res[qid] = out
    n = lambda route, v: sum(1 for r in res.values() if r[route]["verdict"] == v)
    L = ["# Graph-shaped questions", ""]
    L.append(
        f"{len(res)} hand-written questions natural over the virtual graph (`eval/graph_questions.yaml`), "
        "through `qlsc ask` by both routes. Directional: ten questions."
    )
    L += [
        "",
        "| route | correct | wrong | empty | failed | declined | not covered |",
        "|---|---|---|---|---|---|---|",
    ]
    for route in ROUTES:
        L.append(
            f"| {route} | {n(route, 'correct')} | {n(route, 'wrong')} | {n(route, 'empty')} | "
            f"{n(route, 'failed')} | {n(route, 'declined')} | {n(route, 'not covered')} |"
        )
    L += ["", "| question | sql | cypher |", "|---|---|---|"]
    cell = lambda x: f"{x['verdict']}: {x['why']}".replace("|", "/")[:140]
    L += [f"| {q}. {r['question']} | {cell(r['sql'])} | {cell(r['cypher'])} |" for q, r in res.items()]
    out = "_".join(["graph_accuracy", *(re.sub(r"\W+", "_", a) for a in overrides)])  # one file per setting
    print(f"-> {write_result(out, L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

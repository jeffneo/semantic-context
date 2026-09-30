"""Graph-shaped questions (eval/graph_questions.yaml) through `qlsc ask`, by both routes.

The log's questions are what is easy in SQL. These are written by hand to show questions natural over
the virtual graph: an entity's neighbourhood, several hops, shared neighbours, a cycle. A quick,
directional check (ten questions, a few minutes), scored by match.py's ruler.

Writes results/graph_accuracy.md and .json (with overrides that differ from the defaults, a file named
after them). Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/graph_accuracy.py [G01 ...] [param=value ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from common import overrides, settings, write_result
from match import MAXIMUM_BYTES_BILLED, ROWS, both_routes, cell, route_table

from qlsc.graph import Graph
from qlsc.navigate import trace
from qlsc.warehouse import connect

QUESTIONS = Path(__file__).resolve().parent / "graph_questions.yaml"


def main() -> int:
    s = settings()
    argv, suffix = overrides(s, sys.argv[1:])
    qs = yaml.safe_load(QUESTIONS.read_text())
    wanted = argv or list(qs)
    wh, res = connect(s), {}
    with Graph(s) as G:
        for i, qid in enumerate(wanted, 1):
            q = qs[qid]
            ref = {
                "name": qid,
                "items": [[c] for c in q["compare"]],
                "result": wh.run(q["sql"], MAXIMUM_BYTES_BILLED, ROWS),
            }
            if not ref["result"]["ok"]:
                raise SystemExit(f"{qid}'s reference failed: {ref['result']['error'][:200]}")
            tr = trace(G, s, q["question"])
            res[qid] = {
                "question": q["question"],
                "reference_rows": ref["result"]["total"],
                "cohort": tr["top"],
            }
            res[qid] |= both_routes(G, s, tr, [ref], f"{i}/{len(wanted)} {qid}")
    L = ["# Graph-shaped questions", ""]
    L.append(
        f"{len(res)} hand-written questions natural over the virtual graph (`eval/graph_questions.yaml`), "
        "through `qlsc ask` by both routes. Directional: ten questions."
    )
    L += ["", *route_table(res), "", "| question | sql | cypher |", "|---|---|---|"]
    L += [
        f"| {q}. {r['question']} | {cell(r['sql'], 140)} | {cell(r['cypher'], 140)} |" for q, r in res.items()
    ]
    print(f"-> {write_result('graph_accuracy' + suffix, L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

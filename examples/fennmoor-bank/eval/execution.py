"""Execution accuracy: does `qlsc ask` get the right answer, by SQL and by Cypher over the virtual graph?

For each gold question, the question walks down the semantic layer to its cohort (qlsc's navigate),
and both routes write a query and run it:
  sql     SQL from the cohort, run in the warehouse
  cypher  Cypher over the virtual graph, from the cohort's tables that are labels there (plus one hop)
Each answer is compared with the question's reference answer (eval/reference/Qnn.sql, see answers.py),
or an accepted alternative reading of an ambiguous question (Qnn.*.sql), on the columns the reference
declares (`-- compare:`, with alternatives as a|b), by match.py's ruler. Questions whose reference
compares nothing (open-ended or catalog questions) are run and shown, not scored.

Writes results/execution.md and .json (with param=value overrides that differ from the defaults, a
file named after them).
Usage: uv run examples/fennmoor-bank/eval/execution.py [Q04 Q07 ...] [param=value ...]
"""

from __future__ import annotations

import sys

import yaml
from common import SPEC, overrides, settings, write_result
from match import both_routes, cell, references, route_table

from qlsc.graph import Graph
from qlsc.navigate import trace
from qlsc.warehouse import connect


def main() -> int:
    questions = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    s = settings()
    argv, suffix = overrides(s, sys.argv[1:])
    wh, res = connect(s), {}
    with Graph(s) as G:
        for qid in argv or sorted(questions):
            refs = references(wh, qid)
            tr = trace(G, s, questions[qid]["question"])
            res[qid] = {
                "question": questions[qid]["question"],
                "compare": refs[0]["items"],
                "cohort": tr["top"],
            }
            res[qid] |= both_routes(G, s, tr, refs, qid)
    scored = {q: r for q, r in res.items() if r["compare"]}
    L = ["# Execution accuracy", ""]
    L.append(
        "Each gold question through `qlsc ask`, by both routes, against its reference answer "
        "(`results/answers.md`). **correct** = the same rows on the columns the reference compares; "
        "**not covered** = none of the cohort's tables is in the virtual graph. Scored: the questions whose "
        "reference compares columns."
    )
    L += ["", *route_table(scored)]
    either = sum(1 for r in scored.values() if "correct" in (r["sql"]["verdict"], r["cypher"]["verdict"]))
    L += ["", f"Either route correct (an oracle router's score): {either} of {len(scored)}.", ""]
    L += ["| question | sql | cypher |", "|---|---|---|"]
    L += [f"| {q}. {r['question']} | {cell(r['sql'])} | {cell(r['cypher'])} |" for q, r in res.items()]
    print(f"-> {write_result('execution' + suffix, L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

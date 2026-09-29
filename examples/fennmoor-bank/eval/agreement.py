"""When the two routes agree, are they right? Cypher as a second opinion on the SQL route's answer.

For each log question both routes answered with rows (log_accuracy.py's last run), both queries run
again and their results are compared with each other, with no reference: every column of the answer
with fewer columns must appear, with the same values, in the other, row for row (execution.py's
matcher). Set against the reference verdicts, that gives how often an agreement is right, and how
many wrong SQL answers a disagreement flags.

Writes results/agreement.md and .json.
Usage: uv run examples/fennmoor-bank/eval/agreement.py
"""

from __future__ import annotations

import json

from common import RESULTS, settings, write_result
from execution import MAXIMUM_BYTES_BILLED, ROWS, compare
from neo4j.exceptions import Neo4jError

from qlsc import entitle
from qlsc.graph import Graph
from qlsc.warehouse import connect


def main() -> int:
    s = settings()
    runs = json.loads((RESULTS / "log_accuracy.json").read_text())
    answered = lambda r: r["verdict"] in ("correct", "wrong")
    both = [q for q, r in runs.items() if answered(r["sql"]) and answered(r["cypher"])]
    wh, res = connect(s), {}
    with Graph(s, s["virtualize"]["neo4j"]) as V:
        for q in both:
            sql = wh.run(runs[q]["sql"]["query"], MAXIMUM_BYTES_BILLED, ROWS)
            try:
                cypher, params = entitle.signing(s, None, runs[q]["cypher"]["query"])  # the estate's own read
                result = V.run(cypher, **params)
                rows = [x.data() for x in result.records]
                cy = {"ok": True, "columns": list(result.keys), "rows": rows, "total": len(rows)}
            except Neo4jError:
                cy = {"ok": False}
            agree = False
            if sql["ok"] and cy["ok"]:
                a, b = sorted((sql, cy), key=lambda x: len(x["columns"]))
                agree = compare(b, a, [[c] for c in a["columns"]])[0] == "correct"
            res[q] = {
                "agree": agree,
                "sql": runs[q]["sql"]["verdict"],
                "cypher": runs[q]["cypher"]["verdict"],
            }
            print(f"{q} agree={agree!s:5} sql={res[q]['sql']:8} cypher={res[q]['cypher']}")
    n = lambda f: sum(1 for r in res.values() if f(r))
    agree, differ = n(lambda r: r["agree"]), n(lambda r: not r["agree"])
    right = n(lambda r: r["agree"] and r["sql"] == "correct")
    flagged = n(lambda r: not r["agree"] and r["sql"] == "wrong")
    L = ["# When the two routes agree", ""]
    L.append(
        f"{len(res)} log questions both routes answered with rows. The two answers are compared with each "
        "other, not with the reference."
    )
    L += [
        "",
        "| | questions | SQL correct | SQL wrong |",
        "|---|---|---|---|",
        f"| the routes agree | {agree} | {right} | {agree - right} |",
        f"| they differ | {differ} | {differ - flagged} | {flagged} |",
        "",
        f"When they agree, the answer is right {right} times in {agree}. A disagreement flags {flagged} of the "
        f"{n(lambda r: r['sql'] == 'wrong')} wrong SQL answers among these questions.",
    ]
    print(f"-> {write_result('agreement', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

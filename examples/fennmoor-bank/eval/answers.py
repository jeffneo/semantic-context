"""Run the gold questions' reference queries: the answer key for execution accuracy.

Each question in spec/questions.yaml has a hand-written query in eval/reference/Qnn.sql, in the log's
logical table names, written from the spec and checked against the filled data (slice 2 of the fill).
This runs them through the warehouse connector, billing at most MAXIMUM_BYTES_BILLED each, and records
every result. A reference that returns nothing is a finding: either the data does not hold the answer
yet, or the reference is wrong.

Writes results/answers.md and .json.
Usage: uv run examples/fennmoor-bank/eval/answers.py [Q01 Q04 ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from common import SPEC, settings, write_result

from qlsc.warehouse import connect

REFERENCE = Path(__file__).resolve().parent / "reference"
MAXIMUM_BYTES_BILLED = 2 * 10**9  # the largest reference bills well under this at the example's scale
ROWS_KEPT = 50


def cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:,.4g}" if abs(v) < 1 else f"{v:,.2f}"
    return f"{v:,}" if isinstance(v, int) and not isinstance(v, bool) else str(v)


def main() -> int:
    questions = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    wanted = sys.argv[1:] or sorted(questions)
    wh = connect(settings())
    res, L = {}, ["# Reference answers", ""]
    L.append(
        "Each gold question's hand-written reference query (`eval/reference/`), run against the filled "
        "estate. These are the answers execution accuracy scores against."
    )
    for qid in wanted:
        sql = (REFERENCE / f"{qid}.sql").read_text()
        out = wh.run(sql, MAXIMUM_BYTES_BILLED, ROWS_KEPT)
        res[qid] = {"question": questions[qid]["question"], **{k: v for k, v in out.items() if k != "rows"}}
        L += ["", f"## {qid}. {questions[qid]['question']}", ""]
        if not out["ok"]:
            L.append(f"Failed: {out['error']}")
            print(f"{qid}: failed: {out['error']}")
            continue
        rows = [{c: cell(r.get(c)) for c in out["columns"]} for r in out["rows"]]
        res[qid]["rows"] = rows
        L.append("| " + " | ".join(out["columns"]) + " |")
        L.append("|" + "---|" * len(out["columns"]))
        L += ["| " + " | ".join(r[c] for c in out["columns"]) + " |" for r in rows]
        more = f", the first {len(rows)} shown" if out["total"] > len(rows) else ""
        L += ["", f"{out['total']:,} rows{more}; {out['bytes_billed'] / 2**20:,.0f} MiB billed."]
        print(f"{qid}: {out['total']:,} rows, {out['bytes_billed'] / 2**20:,.0f} MiB billed")
    print(f"-> {write_result('answers', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

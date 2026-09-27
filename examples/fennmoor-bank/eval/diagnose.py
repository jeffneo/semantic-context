"""Where do wrong answers come from: finding the tables, or writing the query?

For each gold question scored by value, the SQL route runs twice:
  navigated  the cohort qlsc's navigation finds (what `qlsc ask` does)
  oracle     the answer key's own tables (expected and acceptable), with the joins the log has for them
             and the same example queries: what the SQL writer does when retrieval is perfect
Both are compared with the reference answer (execution.py's matcher). If the oracle is right where
navigation is wrong, retrieval is the problem; if the oracle is wrong too, the query writing is.

Writes results/diagnose.md and .json.
Usage: uv run examples/fennmoor-bank/eval/diagnose.py [Q04 ...]
"""

from __future__ import annotations

import sys

import yaml
from common import SPEC, Names, build, settings, write_result
from execution import ROWS, judge, references

from qlsc import navigate
from qlsc.graph import Graph
from qlsc.navigate import answer_sql, trace
from qlsc.warehouse import connect


def verdict(refs: list[dict], a: dict) -> tuple[str, str]:
    got = a.get("result")
    if got is None or not got.get("ok", True):
        return "failed", str((got or {}).get("error") or a.get("dry_run", {}).get("error"))[:140]
    return judge(refs, got)


def main() -> int:
    questions = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    s = settings()
    wh_spec = build("warehouse.json")
    names, ds_proj = Names(s, wh_spec), {t["dataset"]: t["project"] for t in wh_spec["tables"]}
    canon = lambda x: names.table(x if x.count(".") == 2 else f"{ds_proj[x.split('.')[0]]}.{x}")
    wh = connect(s)
    wanted = sys.argv[1:] or sorted(questions)
    res = {}
    with Graph(s) as G:
        for qid in wanted:
            q = questions[qid]
            refs = references(wh, qid)
            if not refs[0]["items"]:
                continue
            tr = trace(G, s, q["question"])
            key = [canon(t) for t in q.get("expected", [])] + [canon(t) for t in q.get("acceptable") or []]
            oracle = dict(
                tr,
                top=key,
                joins=G.rows(navigate.JOINS, tables=key),
            )
            out = {
                "question": q["question"],
                "missed": sorted(set(key[: len(q["expected"])]) - set(tr["top"])),
            }
            for name, t in (("navigated", tr), ("oracle", oracle)):
                a = answer_sql(G, s, t, execute=True, rows=ROWS)
                v, why = verdict(refs, a)
                out[name] = {"verdict": v, "why": why, "sql": a["sql"], "explanation": a["explanation"]}
                print(f"{qid} {name:9} {v:8} {why[:120]}")
            res[qid] = out
    L = ["# Diagnosis: finding the tables, or writing the query?", ""]
    L.append(
        "The SQL route on each gold question scored by value, with the cohort navigation finds and with "
        "the answer key's own tables (expected and acceptable)."
    )
    n = lambda route: sum(1 for r in res.values() if r[route]["verdict"] == "correct")
    L += [
        "",
        f"Correct: navigated {n('navigated')} of {len(res)}, oracle tables {n('oracle')} of {len(res)}.",
        "",
    ]
    L += ["| question | expected tables navigation missed | navigated | oracle tables |", "|---|---|---|---|"]
    for qid, r in res.items():
        cell = lambda x: f"{x['verdict']}: {x['why']}".replace("|", "/")
        L.append(
            f"| {qid} | {', '.join(r['missed']) or '-'} | {cell(r['navigated'])} | {cell(r['oracle'])} |"
        )
    print(f"-> {write_result('diagnose', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

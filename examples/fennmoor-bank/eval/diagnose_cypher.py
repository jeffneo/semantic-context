"""Is the Cypher route's accuracy a problem of writing Cypher, or of what the virtual graph can run?

Over the log's questions whose every table is a label in the virtual graph (log_questions.py), the
Cypher route runs twice more:
  labels     the reference's own tables as the cohort (retrieval made perfect), from the question
  translate  the same labels, and the reference's SQL given as the SQL to translate: the most the
             route can reach when the question is understood
Each is compared with the reference (execution.py's matcher), and a second time with the reference's
rows that have a null in a compared column left out: a traversal is an inner join, and Virtual Graph
has no OPTIONAL MATCH, so a group for missing keys can't be returned. log_accuracy.py's own run of
both routes over the same questions is shown alongside.

Writes results/diagnose_cypher.md and .json.
Usage: uv run examples/fennmoor-bank/eval/diagnose_cypher.py [--report]   (after log_accuracy.py;
       --report only recomputes the tables, from the last run's answers)
"""

from __future__ import annotations

import json
import sys

import yaml
from common import RESULTS, settings, write_result
from execution import MAXIMUM_BYTES_BILLED, ROWS, compare
from log_accuracy import VIRTUAL, verdict_of
from log_questions import HERE, QUESTIONS, answers_dir

from qlsc import entitle
from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, trace
from qlsc.warehouse import connect

VARIANTS = ("labels", "translate")


def without_nulls(ref: dict, items: list[list[str]]) -> dict:
    keep = [r for r in ref["rows"] if all(r.get(c) is not None for a in items for c in a)]
    return {**ref, "rows": keep}


def judged(a: dict, ref: dict, items: list[list[str]]) -> dict:
    v, why = verdict_of(a, ref, items)
    lenient = v
    if v == "wrong" and a.get("result"):
        lenient = compare(without_nulls(ref, items), a["result"], items)[0]
    return {"verdict": v, "why": why, "lenient": lenient, "query": a.get("cypher")}


def lenient_rerun(s, q: dict, r: dict, route: str) -> str:
    """A wrong answer from log_accuracy's run, run again and compared without the null-key rows."""
    if r["verdict"] != "wrong":
        return r["verdict"]
    ref = json.loads((answers_dir(s) / f"{q['id']}.json").read_text())
    items = [[c] for c in q["compare"]]
    if route == "cypher":
        with Graph(s, s["virtualize"]["neo4j"]) as V:
            cypher, params = entitle.signing(s, None, r["query"])  # the estate's own read
            result = V.run(cypher, **params)
            rows = [x.data() for x in result.records]
            got = {"ok": True, "columns": list(result.keys), "rows": rows, "total": len(rows)}
    else:
        got = connect(s).run(r["query"], MAXIMUM_BYTES_BILLED, ROWS)
    return compare(without_nulls(ref, items), got, items)[0] if got.get("ok") and got["rows"] else "wrong"


def main() -> int:
    s = settings()
    qs = {k: {**v, "id": k} for k, v in yaml.safe_load(QUESTIONS.read_text()).items()}
    kept = {
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    }
    note = (HERE / "prompts" / "translate_note.md").read_text()
    path = RESULTS / "diagnose_cypher.json"
    res = json.loads(path.read_text()) if sys.argv[1:] == ["--report"] else {}
    with Graph(s) as G:
        virtual = {r["t"] for r in G.rows(VIRTUAL)}
        wanted = [q for q in qs if q in kept and set(qs[q]["tables"]) <= virtual]
        for qid in [q for q in wanted if q not in res]:
            q = qs[qid]
            ref = json.loads((answers_dir(s) / f"{qid}.json").read_text())
            items = [[c] for c in q["compare"]]
            tr = trace(G, s, q["question"], exclude=frozenset({q["shape"]}))
            labels = dict(tr, top=q["tables"])
            translate = dict(
                labels, question=note.format(question=q["question"]), examples=[{"sql": q["sql"]}]
            )
            out = {"question": q["question"]}
            for name, t in (("labels", labels), ("translate", translate)):
                out[name] = judged(answer_cypher(G, s, t, execute=True, rows=ROWS), ref, items)
                print(f"{qid} {name:9} {out[name]['verdict']:10} {out[name]['why'][:90]}")
            res[qid] = out
    write_result("diagnose_cypher", [], res)  # the runs, before the report re-executes anything
    runs = json.loads((RESULTS / "log_accuracy.json").read_text())
    for q in res:  # the same lenient reading for the two routes as ask runs them
        for route in ("sql", "cypher"):
            runs[q][route]["lenient"] = lenient_rerun(s, qs[q], runs[q][route], route)
    L = ["# Diagnosis: the Cypher route, question by question", ""]
    L.append(
        f"The {len(res)} log questions whose every table is a label in the virtual graph. **lenient** leaves "
        "out the reference's rows with a null in a compared column (a traversal can't return a group for a "
        "missing key)."
    )
    L += ["", "| run | correct | lenient | declined | failed | of |", "|---|---|---|---|---|---|"]
    n = lambda rows, key, v: sum(1 for r in rows if r[key] == v)
    for name, rows in (
        ("SQL, as ask runs it (log_accuracy)", [runs[q]["sql"] for q in res]),
        ("Cypher, as ask runs it (log_accuracy)", [runs[q]["cypher"] for q in res]),
        ("Cypher, the right labels", [r["labels"] for r in res.values()]),
        ("Cypher, the right labels and the SQL to translate", [r["translate"] for r in res.values()]),
    ):
        lenient = sum(1 for r in rows if r["verdict"] == "correct" or r.get("lenient") == "correct")
        L.append(
            f"| {name} | {n(rows, 'verdict', 'correct')} | {lenient} | {n(rows, 'verdict', 'declined')} | "
            f"{n(rows, 'verdict', 'failed')} | {len(rows)} |"
        )
    L += ["", "| question | labels | translate |", "|---|---|---|"]
    cell = lambda x: f"{x['verdict']}: {x['why']}".replace("|", "/")[:140]
    L += [f"| {q}. {r['question']} | {cell(r['labels'])} | {cell(r['translate'])} |" for q, r in res.items()]
    print(f"-> {write_result('diagnose_cypher', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

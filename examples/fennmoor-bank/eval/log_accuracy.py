"""Execution accuracy over the log's own questions (log_questions.py): the larger answer key.

Each kept question goes through `qlsc ask` by both routes, as execution.py does for the gold
questions, with one difference: navigation never offers the query the question was written from as an
example (`trace(exclude=...)`), or the test would only check that it finds its own reference.

Other queries in the log may still compute the same thing (a Looker explore run with other filters),
and navigation may offer those. That is the log doing its job, and it is how questions resemble past
usage in real life; the results say how often it happened (`sibling`: an example read exactly the
tables the reference reads).

The answers are compared with the reference on its `compare` columns, by match.py's ruler.

Writes results/log_accuracy.md and .json.
Usage: uv run examples/fennmoor-bank/eval/log_accuracy.py [N] [param=value ...]   (N: only the first N questions;
       param=value: an override, e.g. tables=10; one that differs from the defaults is written to
       log_accuracy_<overrides>.*)
       uv run examples/fennmoor-bank/eval/log_accuracy.py --report   (the last run, over the questions kept now)
"""

from __future__ import annotations

import json
import sys
from collections import Counter

import yaml
from common import RESULTS, overrides, scrub, settings, write_result
from log_questions import QUESTIONS, answers_dir
from match import LLMUsage, both_routes, cell, route_table

from qlsc.graph import Graph
from qlsc.navigate import LABELS, trace
from qlsc.warehouse import connect

TOKENS = lambda s: s.work / "log_accuracy_tokens.json"  # the query writer's tokens, from the last full run


def main() -> int:
    usage = LLMUsage()
    s = settings()
    argv, suffix = overrides(s, sys.argv[1:])
    qs = yaml.safe_load(QUESTIONS.read_text())
    kept = {
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    }
    name = "log_accuracy" + suffix
    if argv == ["--report"]:  # the last run's answers, over the questions kept now
        res = {q: r for q, r in json.loads((RESULTS / f"{name}.json").read_text()).items() if q in kept}
        return report(s, res, json.loads(TOKENS(s).read_text()), name)
    wanted = [q for q in qs if q in kept][: int(argv[0]) if argv else None]
    if (probe := connect(s).dry_run("SELECT 1"))["ok"] is not True:  # fail now, not after an hour of failures
        raise SystemExit(f"the warehouse isn't reachable: {probe.get('error')}")
    res = {}
    with Graph(s) as G:
        for i, qid in enumerate(wanted, 1):
            q = qs[qid]
            ref = {"name": qid, "items": [[c] for c in q["compare"]],
                   "result": json.loads((answers_dir(s) / f"{qid}.json").read_text())}  # fmt: skip
            tr = trace(G, s, q["question"], exclude=frozenset({q["shape"]}))
            res[qid] = {
                "question": q["question"],
                "who": q["who"],
                "tables": q["tables"],
                "found": sorted(set(q["tables"]) & set(tr["top"])),
                "sibling": any(set(e.get("tables", [])) == set(q["tables"]) for e in tr["examples"]),
            } | both_routes(G, s, tr, [ref], f"{i}/{len(wanted)} {qid}")
            if i % 10 == 0:  # partial results, so a stopped run still shows where it got to
                (RESULTS / f"{name}.partial.json").write_text(scrub(json.dumps(res, indent=1, default=str)))
    tokens = Counter({"in": usage.spent()["tokens_in"], "out": usage.spent()["tokens_out"]})
    TOKENS(s).write_text(json.dumps(tokens))
    (RESULTS / f"{name}.partial.json").unlink(missing_ok=True)
    return report(s, res, tokens, name)


def report(s, res: dict, tokens: dict, name: str = "log_accuracy") -> int:
    with Graph(s) as G:
        virtual = {r["table"] for r in G.rows(LABELS)}
    L = ["# Execution accuracy over the log's questions", ""]
    L.append(
        f"{len(res)} questions written from the log's own queries (`eval/log_questions.yaml`), each "
        "through `qlsc ask` by both routes, with its own query never offered as an example. Compared "
        "with the query's result on the columns the question asks for (match.py's ruler)."
    )
    n = lambda route, v, sub=res: sum(1 for r in sub.values() if r[route]["verdict"] == v)
    L += ["", *route_table(res)]
    routed = [r["routed"] for r in res.values()]
    compiled = [r for r in res.values() if r["sql"].get("writer") == "compiled"]
    L += [
        "",
        f"Routed: SQL for {sum(r['route'] == 'sql' for r in routed)}, Cypher for "
        f"{sum(r['route'] == 'cypher' for r in routed)} (compiled SQL when the question compiles, else "
        "free Cypher when it answers, else free SQL).",
        f"The SQL compiled for {len(compiled)} of {len(res)}: "
        f"{sum(r['sql']['verdict'] == 'correct' for r in compiled)} correct.",
    ]
    either = sum(1 for r in res.values() if "correct" in (r["sql"]["verdict"], r["cypher"]["verdict"]))
    all_found = [q for q, r in res.items() if set(r["found"]) == set(r["tables"])]
    L += [
        "",
        f"Either route correct: {either} of {len(res)}.",
        f"Navigation's cohort held every table the reference reads for {len(all_found)} of {len(res)}.",
        f"An example read exactly the reference's tables for {sum(r['sibling'] for r in res.values())}.",
        f"Query writing: {tokens['in']:,} tokens in and {tokens['out']:,} out, not counting cached calls.",
        "",
        "| by | questions | sql correct | cypher correct |",
        "|---|---|---|---|",
    ]
    for label, sub in (
        ("the cohort had every reference table", {q: res[q] for q in all_found}),
        ("it missed one or more", {q: r for q, r in res.items() if q not in all_found}),
        ("an example read the reference's tables", {q: r for q, r in res.items() if r["sibling"]}),
        ("no example did", {q: r for q, r in res.items() if not r["sibling"]}),
        ("written from a Looker dashboard", {q: r for q, r in res.items() if "Looker" in r["who"]}),
        ("written from an analyst's query", {q: r for q, r in res.items() if r["who"] == "an analyst"}),
        (
            "every table it reads is in the virtual graph",
            {q: r for q, r in res.items() if set(r["tables"]) <= virtual},
        ),
        ("one table", {q: r for q, r in res.items() if len(r["tables"]) == 1}),
        ("two or more tables", {q: r for q, r in res.items() if len(r["tables"]) > 1}),
    ):
        L.append(f"| {label} | {len(sub)} | {n('sql', 'correct', sub)} | {n('cypher', 'correct', sub)} |")
    L += ["", "| question | sql | cypher |", "|---|---|---|"]
    L += [f"| {q}. {r['question']} | {cell(r['sql'])} | {cell(r['cypher'])} |" for q, r in res.items()]
    print(f"-> {write_result(name, L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

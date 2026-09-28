"""Execution accuracy over the log's own questions (log_questions.py): the larger answer key.

Each kept question goes through `qlsc ask` by both routes, as execution.py does for the gold
questions, with one difference: navigation never offers the query the question was written from as an
example (`trace(exclude=...)`), or the test would only check that it finds its own reference.

Other queries in the log may still compute the same thing (a Looker explore run with other filters),
and navigation may offer those. That is the log doing its job, and it is how questions resemble past
usage in real life; the results say how often it happened (`sibling`: an example read exactly the
tables the reference reads).

The answers are compared with the reference on its `compare` columns, by execution.py's matcher.

Writes results/log_accuracy.md and .json.
Usage: uv run examples/fennmoor-bank/eval/log_accuracy.py [N] [param=value ...]   (N: only the first N questions;
       param=value: a navigation override, e.g. writer=compiled, written to log_accuracy_<overrides>.*)
       uv run examples/fennmoor-bank/eval/log_accuracy.py --report   (the last run, over the questions kept now)
"""

from __future__ import annotations

import json
import sys
from collections import Counter

import yaml
from common import RESULTS, overrides, settings, write_result
from execution import ROUTES, ROWS, compare
from log_questions import QUESTIONS, answers_dir

from qlsc import llm
from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, pick, trace
from qlsc.warehouse import connect

VIRTUAL = "MATCH (t:Table) WHERE t.graph_label IS NOT NULL RETURN t.id AS t"
TOKENS = lambda s: s.work / "log_accuracy_tokens.json"  # the query writer's tokens, from the last full run
MADE: list = []  # every LLM client the routes create, for the token count


def counted(init):
    def wrapper(self, *a, **k):
        init(self, *a, **k)
        MADE.append(self)

    return wrapper


def verdict_of(a: dict, ref: dict, items: list[list[str]]) -> tuple[str, str]:
    got = a.get("result")
    if "skipped" in a:
        return "not covered", a["skipped"]
    if "declined" in a:
        return "declined", a["declined"]
    if got is None or not got.get("ok", True):
        failure = (got or {}).get("error") or a.get("error") or a.get("check", {}).get("error")
        return "failed", str(failure or a.get("dry_run", {}).get("error"))[:160]
    return compare(ref, got, items)


def main() -> int:
    llm.LLM.__init__ = counted(llm.LLM.__init__)
    s = settings()
    argv, suffix = overrides(s, sys.argv[1:])
    qs = yaml.safe_load(QUESTIONS.read_text())
    answers = json.loads((RESULTS / "log_answers.json").read_text())
    kept = {q for q, r in answers.items() if r["verdict"] == "kept"}
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
            ref = json.loads((answers_dir(s) / f"{qid}.json").read_text())
            items = [[c] for c in q["compare"]]
            tr = trace(G, s, q["question"], exclude=frozenset({q["shape"]}))
            sibling = any(set(e.get("tables", [])) == set(q["tables"]) for e in tr["examples"])
            out = {
                "question": q["question"],
                "who": q["who"],
                "tables": q["tables"],
                "found": sorted(set(q["tables"]) & set(tr["top"])),
                "sibling": sibling,
            }
            answers = {}
            for route, answer in (("sql", answer_sql), ("cypher", answer_cypher)):
                a = answers[route] = answer(G, s, tr, execute=True, rows=ROWS)
                v, why = verdict_of(a, ref, items)
                out[route] = {
                    "verdict": v,
                    "why": why,
                    "query": a.get("sql") or a.get("cypher"),
                    "writer": a.get("writer"),
                    "fallback": a.get("fallback"),
                }
                print(
                    f"{i}/{len(wanted)} {qid} {route:6} {v:12} {(a.get('writer') or '')[:8]:8} {why[:90]}",
                    flush=True,
                )
                if "fresh login" in why:  # the credentials expired mid-run: every answer from here would fail
                    raise SystemExit(f"stopped at {qid}: {why}")
            chosen = pick(answers["sql"], answers["cypher"])
            out["routed"] = {"route": chosen, "verdict": out[chosen]["verdict"]}
            res[qid] = out
            if i % 10 == 0:  # partial results, so a stopped run still shows where it got to
                (RESULTS / f"{name}.partial.json").write_text(json.dumps(res, indent=1, default=str))
    tokens = Counter()
    for c in MADE:
        tokens.update(c.tokens)
    TOKENS(s).write_text(json.dumps(tokens))
    (RESULTS / f"{name}.partial.json").unlink(missing_ok=True)
    return report(s, res, tokens, name)


def report(s, res: dict, tokens: dict, name: str = "log_accuracy") -> int:
    with Graph(s) as G:
        virtual = {r["t"] for r in G.rows(VIRTUAL)}
    L = ["# Execution accuracy over the log's questions", ""]
    L.append(
        f"{len(res)} questions written from the log's own queries (`eval/log_questions.yaml`), each "
        "through `qlsc ask` by both routes, with its own query never offered as an example. Compared "
        "with the query's result on the columns the question asks for (execution.py's matcher)."
    )
    n = lambda route, v, sub=res: sum(1 for r in sub.values() if r[route]["verdict"] == v)
    L += [
        "",
        "| route | correct | wrong | empty | failed | declined | not covered | of |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for route in ROUTES:
        L.append(
            f"| {route} | {n(route, 'correct')} | {n(route, 'wrong')} | {n(route, 'empty')} | "
            f"{n(route, 'failed')} | {n(route, 'declined')} | {n(route, 'not covered')} | {len(res)} |"
        )
    routed = [r["routed"] for r in res.values() if "routed" in r]
    if routed:
        L.append(
            f"| routed | {sum(r['verdict'] == 'correct' for r in routed)} | "
            f"{sum(r['verdict'] == 'wrong' for r in routed)} | {sum(r['verdict'] == 'empty' for r in routed)} | "
            f"{sum(r['verdict'] == 'failed' for r in routed)} | | | {len(routed)} |"
        )
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
    cell = lambda x: f"{x['verdict']}: {x['why']}".replace("|", "/")
    L += [f"| {q}. {r['question']} | {cell(r['sql'])} | {cell(r['cypher'])} |" for q, r in res.items()]
    print(f"-> {write_result(name, L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

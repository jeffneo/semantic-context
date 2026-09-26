"""Grade `qlsc ask`'s question -> tables walk on the gold questions.

For each question, each way of choosing the level-1 groups (traversal through the hierarchy, flat
search over level-1 groups, both combined) and each table ranking (round robin over the groups, most
used first), the cohort is compared with the answer key:

  recall     share of the question's expected tables in the cohort
  reached    share of expected tables anywhere under the opened groups (before the cut): what the
             choice of groups allows, independent of ranking
  hit        an expected or acceptable table is in the cohort
  traps      tables the key says to avoid that are in the cohort

Writes results/navigation.md and .json.
Usage: uv run examples/fennmoor-bank/eval/navigation.py
"""

from __future__ import annotations

from common import Names, build, settings, write_result

from qlsc import navigate
from qlsc.graph import Graph
from qlsc.llm import Embedder
from qlsc.names import short

MODES, RANKS = ("traversal", "flat", "combined"), ("usage", "round_robin")


def grade(G: Graph, p: dict, questions: dict, vecs: dict, canon) -> dict:
    res = {}
    for mode in MODES:
        for rank in RANKS:
            rows = {}
            for qid, q in questions.items():
                expected = {canon(t) for t in q.get("expected", [])}
                acceptable = {canon(t) for t in q.get("acceptable") or []}
                avoid = {canon(t) for t in q.get("avoid") or {}}
                _, tables, top = navigate.cohort(G, vecs[qid], p, mode, rank)
                rows[qid] = {
                    "recall": len(expected & set(top)) / len(expected),
                    "reached": len(expected & set(tables)) / len(expected),
                    "hit": bool((expected | acceptable) & set(top)),
                    "traps": sorted(avoid & set(top)),
                    "missed": sorted(expected - set(top)),
                    "top": top,
                }
            n = len(rows)
            res[f"{mode}/{rank}"] = {
                "recall": sum(r["recall"] for r in rows.values()) / n,
                "reached": sum(r["reached"] for r in rows.values()) / n,
                "hit": sum(r["hit"] for r in rows.values()),
                "traps": sum(len(r["traps"]) for r in rows.values()),
                "questions": rows,
            }
    return res


def render(res: dict, n: int, tables: int) -> list[str]:
    L = [
        "# Navigation: question -> tables (qlsc ask)",
        "",
        f"The {n} gold questions, embedded and walked down the semantic layer to a cohort of {tables} tables. "
        "**reached** = expected tables anywhere under the opened level-1 groups (what the choice of groups "
        f"allows); **recall** = expected tables in the final {tables}; **hit** = questions with an expected or "
        f"acceptable table in the {tables}; **traps** = avoid-tables in the {tables}.",
        "",
        "| groups | ranking | reached | recall | hit | traps |",
        "|---|---|---|---|---|---|",
    ]
    for key, r in res.items():
        mode, rank = key.split("/")
        L.append(
            f"| {mode} | {rank} | {r['reached']:.0%} | {r['recall']:.0%} | {r['hit']}/{n} | {r['traps']} |"
        )
    best = max(res, key=lambda x: (res[x]["recall"], res[x]["hit"]))
    L += [
        "",
        f"## Per question ({best})",
        "",
        "| Q | reached | recall | missed | traps |",
        "|---|---|---|---|---|",
    ]
    for qid, r in res[best]["questions"].items():
        L.append(
            f"| {qid} | {r['reached']:.0%} | {r['recall']:.0%} | {', '.join(short(x) for x in r['missed'])} | "
            f"{', '.join(short(x) for x in r['traps'])} |"
        )
    return L


def main() -> int:
    s = settings()
    p = s.params["navigate"]
    wh = build("warehouse.json")
    names = Names(s, wh)
    ds_proj = {t["dataset"]: t["project"] for t in wh["tables"]}
    canon = lambda x: names.table(x if x.count(".") == 2 else f"{ds_proj[x.split('.')[0]]}.{x}")
    questions = build("answer_key.json")["questions"]
    vecs = dict(zip(questions, Embedder(s).embed([q["question"] for q in questions.values()])))
    with Graph(s) as G:
        res = grade(G, p, questions, vecs, canon)
    L = render(res, len(questions), p["tables"])
    path = write_result("navigation", L, res)
    print("\n".join(L[4 : 6 + len(res)]) + f"\n-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

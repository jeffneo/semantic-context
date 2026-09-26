#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Grade pipeline/navigate.py's question -> tables walk on the 14 gold questions (spec side).

For each question and each way of choosing the level-1 groups (traversal through the hierarchy,
flat search over level-1 groups, both combined) and each table ranking (by usage, by group
closeness then usage), the cohort of 8 tables is compared with the answer key:

  recall     share of the question's expected tables in the cohort
  reached    share of expected tables anywhere under the opened groups (before the cut to 8):
             what the choice of groups allows, independent of ranking
  hit        an expected or acceptable table is in the cohort
  traps      tables the key says to avoid that are in the cohort

Writes specs/build/score/NAV_SCORE.md and .json.
Usage: uv run specs/tools/eval_navigate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SPECS = Path(__file__).resolve().parents[1]
ROOT = SPECS.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(SPECS / "tools"))

from graphdb import Graph, config            # noqa: E402
from llm import Embedder                     # noqa: E402
import navigate as N                         # noqa: E402
from score import Names                      # noqa: E402

MODES, RANKS = ("traversal", "flat", "combined"), ("usage", "round_robin")


def main() -> int:
    cfg = config()
    G, emb = Graph(cfg), Embedder(cfg)
    wh = json.loads((SPECS / "build" / "warehouse.json").read_text())
    names = Names(json.loads((ROOT / "pipeline" / "work" / "catalog.json").read_text()), wh)
    ds_proj = {t["dataset"]: t["project"] for t in wh["tables"]}
    canon = lambda x: names.table(x if x.count('.') == 2 else f"{ds_proj[x.split('.')[0]]}.{x}")
    Qs = json.loads((SPECS / "build" / "answer_key.json").read_text())["questions"]
    vecs = dict(zip(Qs, emb.embed([q["question"] for q in Qs.values()])))
    res = {}
    for mode in MODES:
        for rank in RANKS:
            rows = {}
            for qid, q in Qs.items():
                exp = {canon(t) for t in q.get("expected", [])}
                acc = {canon(t) for t in q.get("acceptable") or []}
                av = {canon(t) for t in q.get("avoid") or {}}
                _, tables, top = N.cohort(G, vecs[qid], mode, rank)
                rows[qid] = {"recall": len(exp & set(top)) / len(exp), "reached": len(exp & set(tables)) / len(exp),
                             "hit": bool((exp | acc) & set(top)), "traps": sorted(av & set(top)),
                             "missed": sorted(exp - set(top)), "top": top}
            n = len(rows)
            res[f"{mode}/{rank}"] = {"recall": sum(r["recall"] for r in rows.values()) / n,
                                     "reached": sum(r["reached"] for r in rows.values()) / n,
                                     "hit": sum(r["hit"] for r in rows.values()), "traps": sum(len(r["traps"]) for r in rows.values()),
                                     "questions": rows}
    L = ["# Navigation: question -> tables (pipeline/navigate.py)", "",
         "The 14 gold questions, embedded and walked down the semantic layer to a cohort of 8 tables. "
         "**reached** = expected tables anywhere under the opened level-1 groups (what the choice of groups "
         "allows); **recall** = expected tables in the final 8; **hit** = questions with an expected or "
         "acceptable table in the 8; **traps** = avoid-tables in the 8.", "",
         "| groups | ranking | reached | recall | hit | traps |", "|---|---|---|---|---|---|"]
    for key, r in res.items():
        m, k = key.split("/")
        L.append(f"| {m} | {k} | {r['reached']:.0%} | {r['recall']:.0%} | {r['hit']}/14 | {r['traps']} |")
    best = max(res, key=lambda x: (res[x]["recall"], res[x]["hit"]))
    L += ["", f"## Per question ({best})", "", "| Q | reached | recall | missed | traps |", "|---|---|---|---|---|"]
    for qid, r in res[best]["questions"].items():
        L.append(f"| {qid} | {r['reached']:.0%} | {r['recall']:.0%} | {', '.join(x.split('.', 1)[1] for x in r['missed'])} | "
                 f"{', '.join(x.split('.', 1)[1] for x in r['traps'])} |")
    out = SPECS / "build" / "score"
    (out / "NAV_SCORE.md").write_text("\n".join(L) + "\n")
    (out / "NAV_SCORE.json").write_text(json.dumps(res, indent=1))
    print("\n".join(L[5:5 + 2 + len(res)]))
    print(f"-> {out / 'NAV_SCORE.md'}")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

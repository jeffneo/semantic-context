"""How much of the semantic layer, and of navigation, depends on Leiden's random seed.

Every run is deterministic for a given seed, but a seed is one draw among equally valid groupings. For
each seed, level 1 (qlsc cluster) and the levels above (qlsc hierarchy) are rebuilt with
parameters.cluster.seed and parameters.hierarchy.seed set to it, and graded:

  levels       Semantic groups per level
  stability    median Semantic.stability of the level-1 groups
  NMI          the table partition (each table goes to the group holding most of its columns)
               against the spec's subjects (level 1) and domains (level 2)
  navigation   the gold questions (eval/navigation.py), groups combined, round robin

The graph is rebuilt with the configured seed afterwards (every call is cached, so it comes back
exactly). New groupings are named by the LLM and embedded once, then cached.

Writes results/seeds.md and .json.
Usage: uv run examples/fennmoor-bank/eval/seeds.py [--seeds 1 2 3 ...]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import statistics
from collections import Counter, defaultdict

import navigation
from common import Names, build, nmi, settings, write_result

from qlsc import align, cluster, hierarchy
from qlsc.graph import Graph
from qlsc.llm import Embedder

SEEDS = list(range(1, 11))


def rebuild(s, seed: int) -> None:
    """Level 1 and the levels above with one seed; their output goes to a buffer, not the screen."""
    s = copy.deepcopy(s)
    s["parameters"]["cluster"]["seed"] = s["parameters"]["hierarchy"]["seed"] = seed
    with contextlib.redirect_stdout(io.StringIO()):
        cluster.run(s)
        hierarchy.run(s)


def partition(G: Graph, level: int) -> dict[str, str]:
    """Each table -> the Semantic of `level` holding most of its columns."""
    votes = defaultdict(Counter)
    for r in G.rows(
        """MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(:Semantic {level: 1})
                 -[:IN_SEMANTIC]->{0,}(g:Semantic {level: $l})
           WHERE u:Variable OR u:Unjoined
           RETURN t.id AS t, g.id AS g, count(c) AS n""",
        l=level,
    ):
        votes[r["t"]][r["g"]] += r["n"]
    return {t: c.most_common(1)[0][0] for t, c in votes.items()}


def grade(G: Graph, s, subject: dict, domain: dict, questions: dict, vecs: dict, canon) -> dict:
    levels = {r["l"]: r["n"] for r in G.rows("MATCH (x:Semantic) RETURN x.level AS l, count(*) AS n")}
    stab = sorted(r["v"] for r in G.rows("MATCH (x:Semantic {level: 1}) RETURN x.stability AS v"))
    nav = navigation.grade(G, s.params["navigate"], questions, vecs, canon)["combined/round_robin"]
    return {
        "levels": [levels[k] for k in sorted(levels)],
        "stability": stab[len(stab) // 2],
        "nmi_subjects": nmi(partition(G, 1), subject),
        "nmi_domains": nmi(partition(G, 2), domain) if 2 in levels else None,
        "reached": nav["reached"],
        "recall": nav["recall"],
        "hit": nav["hit"],
        "traps": nav["traps"],
    }


def render(res: dict, configured: int, n: int) -> list[str]:
    rows = list(res.values())
    L = [
        "# Seeds: how much depends on Leiden's random seed",
        "",
        f"Level 1 and the levels above rebuilt with {len(rows)} seeds (both Leiden runs use the same seed); "
        f"the configured seed is {configured}. NMI: the table partition against the spec's subjects (level 1) "
        f"and domains (level 2). Navigation: the {n} gold questions, groups combined, round robin.",
        "",
        "| seed | levels | stability | NMI subjects | NMI domains | reached | recall | hit | traps |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for seed, r in res.items():
        mark = " (configured)" if seed == configured else ""
        L.append(
            f"| {seed}{mark} | {' → '.join(map(str, r['levels']))} | {r['stability']:.2f} | "
            f"{r['nmi_subjects']:.3f} | {r['nmi_domains']:.3f} | {r['reached']:.0%} | {r['recall']:.0%} | "
            f"{r['hit']}/{n} | {r['traps']} |"
        )
    L += ["", "| | mean | sd | min | max |", "|---|---|---|---|---|"]
    for key, fmt in (
        ("nmi_subjects", ".3f"),
        ("nmi_domains", ".3f"),
        ("reached", ".0%"),
        ("recall", ".0%"),
        ("hit", ".1f"),
        ("traps", ".1f"),
    ):
        v = [r[key] for r in rows]
        L.append(
            f"| {key} | {statistics.mean(v):{fmt}} | {statistics.stdev(v):{fmt}} | {min(v):{fmt}} | "
            f"{max(v):{fmt}} |"
        )
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    a = ap.parse_args()
    s = settings()
    configured = s.params["cluster"]["seed"]
    wh = build("warehouse.json")
    names = Names(s, wh)
    subject = {names.table(t["fqn"]): t["subject"] for t in wh["tables"]}
    domain = {names.table(t["fqn"]): t["domain"] for t in wh["tables"]}
    ds_proj = {t["dataset"]: t["project"] for t in wh["tables"]}
    canon = lambda x: names.table(x if x.count(".") == 2 else f"{ds_proj[x.split('.')[0]]}.{x}")
    questions = build("answer_key.json")["questions"]
    vecs = dict(zip(questions, Embedder(s).embed([q["question"] for q in questions.values()])))
    res = {}
    try:
        for seed in sorted(set(a.seeds) | {configured}):
            rebuild(s, seed)
            with Graph(s) as G:
                res[seed] = grade(G, s, subject, domain, questions, vecs, canon)
            r = res[seed]
            print(
                f"seed {seed:3}: levels {r['levels']}, NMI {r['nmi_subjects']:.3f} / {r['nmi_domains']:.3f}, "
                f"recall {r['recall']:.0%}, hit {r['hit']}/{len(questions)}, traps {r['traps']}",
                flush=True,
            )
    finally:  # back to the configured seed, with the alignment on top
        rebuild(s, configured)
        with contextlib.redirect_stdout(io.StringIO()):
            align.run(s)
    path = write_result("seeds", render(res, configured, len(questions)), res)
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

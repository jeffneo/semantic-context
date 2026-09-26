#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Robustness of the semantic layer (spec side): noise injection and parameter sweeps.

Everything runs in memory on the pipeline's own functions (cluster.py, hierarchy.py); nothing is
written to the graph except temporary GDS projections. Agreement with the spec is NMI of the
table partition (each table goes to the group holding most of its columns) against the spec's
subjects (level 1) or domains (level 2). Agreement between two runs is ARI over the units.

  1. Noisy queries: fake statements that read 2-4 random, unrelated units together, added at
     5% to 100% of the real statement count - analysts' one-off queries across the estate.
  2. Wrong joins: random pairs of identifier units merged into one, as a wrong join that got past
     the join-confidence check would do (joins.py flags the kind production contradicts; a random
     one usually has no such evidence).
  3. Level-1 gamma sweep: groups, agreement with the spec, and stability across seeds.
  4. Level-1 -> level-2 sweep: k (neighbours) x gamma, on the same embeddings and usage.

Writes specs/build/score/ROBUSTNESS.md and .json.
Usage: uv run specs/tools/robustness.py
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SPECS = Path(__file__).resolve().parents[1]
ROOT = SPECS.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(SPECS / "tools"))

import cluster as C                          # noqa: E402
import hierarchy as H                        # noqa: E402
from graphdb import Graph, config            # noqa: E402
from llm import Embedder                     # noqa: E402
from score import Names, nmi                 # noqa: E402

GAMMA1 = 4.0
ID_NAME = re.compile(r"(?i)(_id|_key|_number|_nbr|_no|_code|_cd)$")


def ari(a: dict, b: dict) -> float:
    keys = a.keys() & b.keys()
    comb = lambda n: n * (n - 1) / 2
    cont = Counter((a[k], b[k]) for k in keys)
    ra, rb = Counter(a[k] for k in keys), Counter(b[k] for k in keys)
    idx = sum(comb(n) for n in cont.values())
    ea, eb, n = sum(comb(x) for x in ra.values()), sum(comb(x) for x in rb.values()), comb(len(keys))
    exp = ea * eb / n if n else 0
    mx = (ea + eb) / 2
    return (idx - exp) / (mx - exp) if mx != exp else 1.0


def main() -> int:
    cfg = config()
    G = Graph(cfg)
    wh = json.loads((SPECS / "build" / "warehouse.json").read_text())
    names = Names(json.loads((ROOT / "pipeline" / "work" / "catalog.json").read_text()), wh)
    sub = {names.table(t["fqn"]): t["subject"] for t in wh["tables"]}
    dom = {names.table(t["fqn"]): t["domain"] for t in wh["tables"]}
    unit_tables = defaultdict(Counter)           # unit -> table -> columns
    for r in G.rows("""MATCH (u)<-[:IS]-{0,1}(c:Column)<-[:HAS_COLUMN]-(t:Table) WHERE u:Variable OR u:Unjoined
                       RETURN u.id AS u, t.id AS t, count(c) AS n"""):
        unit_tables[r["u"]][r["t"]] += r["n"]
    ident = [r["u"] for r in G.rows("""MATCH (u) WHERE u:Variable OR (u:Unjoined AND u.name =~ $rx) RETURN u.id AS u""",
                                    rx=ID_NAME.pattern.replace("(?i)", "(?i).*"))]

    def table_partition(of: dict) -> dict:
        votes = defaultdict(Counter)
        for u, g in of.items():
            for t, n in unit_tables.get(u, {}).items():
                votes[t][g] += n
        return {t: c.most_common(1)[0][0] for t, c in votes.items() if t in sub}

    def level1(shapes, flows, gamma=GAMMA1, seed=42, merge=None):
        if merge:                                  # wrong joins: relabel b -> a everywhere
            m = lambda u: merge.get(u, u)
            shapes = {s: sorted({m(u) for u in us}) for s, us in shapes.items()}
            flows = [(m(a), m(b), sh) for a, b, sh in flows]
        C.project(G, C.edges_from(shapes, flows))
        groups = C.leiden(G, gamma, seed)
        of = {u: k for k, ms in groups.items() for u in ms}
        if merge:
            for b, a in merge.items():
                if a in of:
                    of[b] = of[a]
        return of, sum(1 for ms in groups.values() if len(ms) >= 2)

    shapes, flows = C.evidence_sets(G)
    base, n_base = level1(shapes, flows)
    base_nmi = nmi(table_partition(base), sub)
    res = {"base": {"groups": n_base, "nmi_subjects": base_nmi}}
    read_units = sorted({u for us in shapes.values() for u in us})
    table_of = {u: max(unit_tables[u], key=unit_tables[u].get) for u in read_units if unit_tables.get(u)}

    # 1. noisy queries
    res["noisy_queries"] = []
    for rate in (0.05, 0.10, 0.25, 0.50, 1.00):
        for seed in (1, 2):
            rnd = random.Random(seed)
            noisy = dict(shapes)
            for i in range(int(rate * len(shapes))):
                picked, seen = [], set()
                while len(picked) < rnd.randint(2, 4):
                    u = rnd.choice(read_units)
                    if table_of.get(u) not in seen:
                        picked.append(u)
                        seen.add(table_of.get(u))
                noisy[f"noise:{i}"] = picked
            of, n = level1(noisy, flows)
            res["noisy_queries"].append({"rate": rate, "seed": seed, "groups": n, "ari_vs_clean": ari(of, base),
                                         "nmi_subjects": nmi(table_partition(of), sub)})
    # 2. wrong joins that get past the confidence check
    res["wrong_joins"] = []
    for m in (5, 10, 25, 50):
        for seed in (1, 2):
            rnd = random.Random(seed)
            merge = {}
            while len(merge) < m:
                a, b = rnd.sample(ident, 2)
                if a not in merge and b not in merge and a not in merge.values() and table_of.get(a) != table_of.get(b):
                    merge[b] = a
            of, n = level1(shapes, flows, merge=merge)
            res["wrong_joins"].append({"merges": m, "seed": seed, "groups": n, "ari_vs_clean": ari(of, base),
                                       "nmi_subjects": nmi(table_partition(of), sub)})
    # 3. level-1 gamma sweep
    res["gamma1"] = []
    for g in (1.0, 2.0, 3.0, 4.0, 6.0, 8.0):
        runs = [level1(shapes, flows, gamma=g, seed=s) for s in (1, 2, 3)]
        tp = table_partition(runs[0][0])
        res["gamma1"].append({"gamma": g, "groups": runs[0][1], "nmi_subjects": nmi(tp, sub), "nmi_domains": nmi(tp, dom),
                              "seed_ari": sum(ari(runs[i][0], runs[j][0]) for i, j in ((0, 1), (0, 2), (1, 2))) / 3})
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=C.GRAPH)
    # 4. level-1 -> level-2 sweep on the stored level-1 groups
    vecs = {r["id"]: r["e"] for r in G.rows("MATCH (s:Semantic {level: 1}) RETURN s.id AS id, s.embedding AS e")}
    use = H.usage(G, 1, C.unit_edges(G))
    eid = {r["id"]: r["e"] for r in G.rows("MATCH (s:Semantic {level: 1}) RETURN s.id AS id, elementId(s) AS e")}
    members = defaultdict(Counter)
    for r in G.rows("""MATCH (s:Semantic {level: 1})<-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       RETURN s.id AS s, t.id AS t, count(c) AS n"""):
        members[r["t"]][r["s"]] += r["n"]
    res["level2"] = []
    for k in (3, 5, 8):
        rows = H.knn(G, 1, k, vecs, use, write=False)
        for g2 in (1.5, 3.0, 4.5):
            parts = []
            for seed in (1, 2, 3):
                G.run("CALL gds.graph.drop('robust', false) YIELD graphName RETURN graphName")
                G.run("""UNWIND $rows AS r MATCH (a) WHERE elementId(a) = r.a MATCH (b) WHERE elementId(b) = r.b
                         WITH gds.graph.project('robust', a, b, {relationshipProperties: {w: r.w}},
                                                {undirectedRelationshipTypes: ['*']}) AS g RETURN g.nodeCount""",
                      rows=[{"a": eid[x["a"]], "b": eid[x["b"]], "w": max(x["score"], 1e-3)} for x in rows])
                parts.append({r["id"]: r["c"] for r in G.rows("""CALL gds.leiden.stream('robust', {gamma: $g,
                    relationshipWeightProperty: 'w', randomSeed: $s, concurrency: 1}) YIELD nodeId, communityId
                    RETURN gds.util.asNode(nodeId).id AS id, communityId AS c""", g=g2, s=seed)})
            tp = {t: parts[0][c.most_common(1)[0][0]] for t, c in members.items() if t in dom and c.most_common(1)[0][0] in parts[0]}
            res["level2"].append({"k": k, "gamma": g2, "groups": len(set(parts[0].values())), "nmi_domains": nmi(tp, dom),
                                  "seed_ari": sum(ari(parts[i], parts[j]) for i, j in ((0, 1), (0, 2), (1, 2))) / 3})
    G.run("CALL gds.graph.drop('robust', false) YIELD graphName RETURN graphName")

    # ------------------------------------------------------------------ report
    def avg(rows, key, by):
        out = defaultdict(list)
        for r in rows:
            out[r[by]].append(r[key])
        return {x: sum(v) / len(v) for x, v in out.items()}
    L = ["# Robustness: noise and parameters", "",
         f"Clean level 1: {n_base} groups, NMI vs spec subjects {base_nmi:.3f} (gamma {GAMMA1}). NMI = agreement of "
         "the table partition with the spec; ARI vs clean = how much of the clean grouping survives (1 = identical). "
         "Noise rows average two seeds.", "",
         "## 1. Noisy queries (random cross-estate co-reads)", "",
         "| noise, share of real statements | groups | ARI vs clean | NMI vs spec subjects |", "|---|---|---|---|"]
    nq = res["noisy_queries"]
    for rate in sorted({r["rate"] for r in nq}):
        rs = [r for r in nq if r["rate"] == rate]
        L.append(f"| {rate:.0%} ({int(rate * len(shapes))}) | {sum(r['groups'] for r in rs) / 2:.0f} | "
                 f"{sum(r['ari_vs_clean'] for r in rs) / 2:.2f} | {sum(r['nmi_subjects'] for r in rs) / 2:.3f} |")
    L += ["", "## 2. Wrong joins that get past the confidence check (random id merges)", "",
          "| merges | groups | ARI vs clean | NMI vs spec subjects |", "|---|---|---|---|"]
    wj = res["wrong_joins"]
    for m in sorted({r["merges"] for r in wj}):
        rs = [r for r in wj if r["merges"] == m]
        L.append(f"| {m} | {sum(r['groups'] for r in rs) / 2:.0f} | {sum(r['ari_vs_clean'] for r in rs) / 2:.2f} | "
                 f"{sum(r['nmi_subjects'] for r in rs) / 2:.3f} |")
    L += ["", "## 3. Level-1 gamma (Leiden over co-reads and lineage)", "",
          "| gamma | groups | NMI vs subjects | NMI vs domains | stability across seeds (ARI) |", "|---|---|---|---|---|"]
    L += [f"| {r['gamma']:g} | {r['groups']} | {r['nmi_subjects']:.3f} | {r['nmi_domains']:.3f} | {r['seed_ari']:.2f} |"
          for r in res["gamma1"]]
    L += ["", "## 4. Level 1 -> level 2 (K_SIM kNN + Leiden)", "",
          "| k | gamma | level-2 groups | NMI vs domains | stability across seeds (ARI) |", "|---|---|---|---|---|"]
    L += [f"| {r['k']} | {r['gamma']:g} | {r['groups']} | {r['nmi_domains']:.3f} | {r['seed_ari']:.2f} |" for r in res["level2"]]
    out = SPECS / "build" / "score"
    (out / "ROBUSTNESS.md").write_text("\n".join(L) + "\n")
    (out / "ROBUSTNESS.json").write_text(json.dumps(res, indent=1))
    print("\n".join(L))
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

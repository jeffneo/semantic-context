#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Stage 5b: semantic groups - Leiden over what the business reads together.

Nodes are the units after variables.py: a Variable (the columns it unifies count as one) or an
:Unjoined column. Two units are related when
  - one query reads both (READS covers every role: select, filter, join, group, order), or
  - column lineage connects them (FLOWS, except control-only origins): the raw, staging and
    mart copies of the same data are one area.
The weight is the number of distinct statements that do either.

  1. GDS Cypher projection, undirected, weight `w`, from those pairs (unit_edges, reused by
     hierarchy.py). Columns of transient ingestion tables (Fivetran's *_{hex} merge sources)
     and lineage out of them are load plumbing, not use, and are left out. Every Variable|Unjoined node is projected, so a column nothing reads or
     derives with anything is an isolated node. --no-lineage drops the FLOWS edges.
  2. Leiden, weighted, gamma > 1 for more and smaller communities (default 4), seeded and
     single-threaded so a rerun gives the same groups.
  3. Materialize every community with 2 or more members as (:Semantic {id, level: 1, size, tables}) with
     (:Variable|Unjoined)-[:IN_SEMANTIC]->(:Semantic). The id is 'sem:' + the smallest member id.
     Isolated nodes (never read together with anything) get no Semantic: there is no evidence
     to group them.
  4. Stability: Leiden is rerun 10 times, 5 with new seeds and 5 on a resample of 80% of the
     statements; Semantic.stability is how much of the group comes back (best Jaccard overlap,
     averaged; 1 = always whole). A low value means the evidence for that group is thin.
  5. Name each Semantic with the LLM (prompts/semantic_*.md).

Usage: uv run pipeline/cluster.py [--gamma 4] [--no-names] [--no-lineage]
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict

from graphdb import Graph, config
from llm import LLM, name_all, prompt

GRAPH = "semantic"
BATCH = 8
SHOW_MEMBERS = 40


def evidence_sets(G: Graph) -> tuple[dict[str, list[str]], list[tuple[str, str, list[str]]]]:
    """The usage evidence per statement: the units each query reads, and each lineage link with the
    statements that make it. Units are a Variable, or an :Unjoined column."""
    shapes = {r["s"]: r["units"] for r in G.rows("""MATCH (s:QueryShape)-[:READS]->(c:Column)
        OPTIONAL MATCH (c)-[:IS]->(v:Variable)
        WITH s, collect(DISTINCT coalesce(v.id, c.id)) AS units WHERE size(units) > 1
        RETURN s.id AS s, units""")}
    # lineage out of transient ingestion tables (Fivetran's *_{hex} merge sources) is load plumbing,
    # not use (PIPELINE_PLAN.md section 6)
    flows = [(r["a"], r["b"], r["shapes"]) for r in G.rows("""
        MATCH (tx:Table)-[:HAS_COLUMN]->(x:Column)-[f:FLOWS]->(y:Column)
        WHERE NOT f.control AND tx.kind <> 'transient'
        OPTIONAL MATCH (x)-[:IS]->(vx:Variable)
        OPTIONAL MATCH (y)-[:IS]->(vy:Variable)
        RETURN coalesce(vx.id, x.id) AS a, coalesce(vy.id, y.id) AS b, f.shapes AS shapes""")]
    return shapes, flows


def edges_from(shapes: dict, flows: list, keep: set | None = None) -> dict[tuple[str, str], dict]:
    """(a, b) with a < b -> {coread, flows}: the number of statements (kept, if `keep` is given)
    that read both, or that derive one from the other."""
    edges: dict[tuple[str, str], dict] = {}

    def add(a, b, kind, w):
        if a != b and w:
            e = edges.setdefault((min(a, b), max(a, b)), {"coread": 0, "flows": 0})
            e[kind] += w
    for sid, units in shapes.items():
        if keep is None or sid in keep:
            for i, a in enumerate(units):
                for b in units[i + 1:]:
                    add(a, b, "coread", 1)
    for a, b, sh in flows:
        add(a, b, "flows", len(sh) if keep is None else sum(1 for x in sh if x in keep))
    return edges


def unit_edges(G: Graph) -> dict[tuple[str, str], dict]:
    """Usage between units: read by the same query, or connected by column lineage."""
    return edges_from(*evidence_sets(G))


def project(G: Graph, edges: dict, lineage: bool = True) -> dict:
    """Every Variable|Unjoined node, and an undirected edge per related pair, weight w."""
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    eid = {r["id"]: r["e"] for r in G.rows("""MATCH (u) WHERE u:Variable OR u:Unjoined
                                               AND NOT EXISTS { (u)<-[:HAS_COLUMN]-(:Table {kind: 'transient'}) }
                                               RETURN u.id AS id, elementId(u) AS e""")}
    rows, linked = [], set()
    for (a, b), e in edges.items():
        w = e["coread"] + (e["flows"] if lineage else 0)
        if w > 0 and a in eid and b in eid:
            rows.append({"a": eid[a], "b": eid[b], "w": float(w)})
            linked |= {a, b}
    rows += [{"a": e, "b": None, "w": None} for u, e in eid.items() if u not in linked]
    return G.rows("""UNWIND $rows AS r
        MATCH (a) WHERE elementId(a) = r.a
        OPTIONAL MATCH (b) WHERE elementId(b) = r.b
        WITH gds.graph.project($g, a, b, {relationshipProperties: CASE WHEN b IS NULL THEN null ELSE {w: r.w} END},
                               {undirectedRelationshipTypes: ['*']}) AS g
        RETURN g.nodeCount AS nodes, g.relationshipCount AS rels""", g=GRAPH, rows=rows)[0]


def leiden(G: Graph, gamma: float, seed: int = 42) -> dict[str, list[str]]:
    comm = defaultdict(list)
    for r in G.rows("""CALL gds.leiden.stream($g, {gamma: $gamma, relationshipWeightProperty: 'w',
                                                   randomSeed: $seed, concurrency: 1})
                       YIELD nodeId, communityId
                       RETURN gds.util.asNode(nodeId).id AS id, communityId AS k""", g=GRAPH, gamma=gamma, seed=seed):
        comm[r["k"]].append(r["id"])
    return {f"sem:{min(ms)}": sorted(ms) for ms in comm.values()}


def stability(G: Graph, groups: dict[str, list[str]], shapes: dict, flows: list, gamma: float,
              lineage: bool, runs: int = 10, share: float = 0.8) -> dict[str, float]:
    """How much of each group comes back when Leiden is rerun: half the runs change only the random
    seed, half also resample the evidence (keep `share` of the statements). For a group, the best
    Jaccard overlap with any community of a run, averaged over the runs: 1 = always comes back whole."""
    import random
    ids = sorted(shapes.keys() | {x for _, _, sh in flows for x in sh})
    score = defaultdict(float)
    for r in range(runs):
        keep = None if r < runs // 2 else set(random.Random(r).sample(ids, int(len(ids) * share)))
        project(G, edges_from(shapes, flows, keep), lineage)
        of = {}
        for k, ms in leiden(G, gamma, seed=r + 1).items():
            for m in ms:
                of[m] = k
        comm = defaultdict(set)
        for m, k in of.items():
            comm[k].add(m)
        for gid, members in groups.items():
            ms = set(members)
            score[gid] += max(len(ms & comm[k]) / len(ms | comm[k]) for k in {of[m] for m in ms if m in of})
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    return {g: v / runs for g, v in score.items()}


def evidence(G: Graph, groups: dict[str, list[str]]) -> dict[str, str]:
    """What the namer sees: tables, variables (named), other columns, and a query that reads many members."""
    unit = {}
    for r in G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       RETURN v.id AS u, v.name AS name, collect(DISTINCT t.id) AS tables, collect(c.id) AS cols"""):
        unit[r["u"]] = {"kind": "variable", "label": r["name"], "tables": r["tables"], "cols": r["cols"]}
    for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Unjoined) RETURN c.id AS u, c.name AS name, c.type AS type,
                       t.id AS t"""):
        unit[r["u"]] = {"kind": "column", "label": f"{r['t'].split('.', 1)[1]}.{r['name']} {r['type'] or ''}".rstrip(),
                        "tables": [r["t"]], "cols": [r["u"]]}
    reads = {r["u"]: r["n"] for r in G.rows("""MATCH (u) WHERE u:Variable OR u:Unjoined
        MATCH (u)<-[:IS]-{0,1}(:Column)<-[:READS]-(s:QueryShape) RETURN u.id AS u, count(DISTINCT s) AS n""")}
    out = {}
    for sid, members in groups.items():
        tables = Counter(t for m in members for t in unit[m]["tables"])
        cols = {c for m in members for c in unit[m]["cols"]}
        best = G.rows("""MATCH (s:QueryShape)-[:READS]->(c:Column) WHERE c.id IN $cols
                         WITH s, count(DISTINCT c) AS n ORDER BY n DESC, s.jobs DESC LIMIT 1
                         RETURN s.sample_sql AS q""", cols=sorted(cols))
        vs = sorted((m for m in members if unit[m]["kind"] == "variable"), key=lambda m: -reads.get(m, 0))
        cs = sorted((m for m in members if unit[m]["kind"] == "column"), key=lambda m: -reads.get(m, 0))
        lines = [f"### semantic group {sid}", f"id: {sid}",
                 f"{len(members)} members from {len(tables)} tables: " +
                 ", ".join(f"{t.split('.', 1)[1]} ({n})" for t, n in tables.most_common(10))
                 + (" ..." if len(tables) > 10 else "")]
        if vs:
            lines.append("variables: " + "; ".join(unit[m]["label"] or m for m in vs[:15]))
        if cs:
            lines.append("columns: " + "; ".join(unit[m]["label"] for m in cs[:SHOW_MEMBERS])
                         + (f"; ... and {len(cs) - SHOW_MEMBERS} more" if len(cs) > SHOW_MEMBERS else ""))
        if best and best[0]["q"]:
            q = best[0]["q"]
            lines.append("a query that reads many of them:\n" + (q if len(q) <= 900 else q[:897] + "..."))
        out[sid] = "\n".join(lines)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gamma", type=float, default=4.0)
    ap.add_argument("--no-names", action="store_true")
    ap.add_argument("--no-lineage", action="store_true", help="co-reads only, without FLOWS edges")
    a = ap.parse_args()
    cfg = config()
    G = Graph(cfg)
    t0 = time.time()
    G.run("CREATE CONSTRAINT semantic_id IF NOT EXISTS FOR (n:Semantic) REQUIRE n.id IS UNIQUE")
    G.auto("MATCH (s:Semantic) CALL (s) { DETACH DELETE s } IN TRANSACTIONS OF 5000 ROWS")

    shapes, flows = evidence_sets(G)
    edges = edges_from(shapes, flows)
    p = project(G, edges, lineage=not a.no_lineage)
    comms = leiden(G, a.gamma)
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    groups = {k: ms for k, ms in comms.items() if len(ms) >= 2}
    alone = sum(1 for ms in comms.values() if len(ms) == 1)
    G.batch("Semantic", """UNWIND $rows AS r CREATE (s:Semantic {id: r.id, level: 1, size: size(r.members), gamma: r.gamma})
                           WITH s, r UNWIND r.members AS mid
                           MATCH (u {id: mid}) WHERE u:Variable OR u:Unjoined CREATE (u)-[:IN_SEMANTIC]->(s)""",
            [{"id": k, "members": ms, "gamma": a.gamma} for k, ms in groups.items()], 200)
    G.run("""MATCH (s:Semantic)<-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)<-[:HAS_COLUMN]-(t:Table)
             WITH s, count(DISTINCT t) AS n SET s.tables = n""")
    sizes = sorted((len(ms) for ms in groups.values()), reverse=True)
    buckets = Counter("2" if n == 2 else "3-5" if n <= 5 else "6-10" if n <= 10 else "11-25" if n <= 25
                      else "26-50" if n <= 50 else "51+" for n in sizes)
    n_flow = sum(1 for e in edges.values() if e["flows"] and not e["coread"])
    print(f"projection: {p['nodes']:,} nodes, {p['rels']:,} relationships ({n_flow:,} pairs linked only by lineage); "
          f"Leiden gamma {a.gamma}: "
          f"{len(comms):,} communities")
    print(f"Semantic: {len(groups):,} groups over {sum(sizes):,} members; {alone:,} nodes alone (no Semantic)")
    print("  sizes: " + ", ".join(f"{b}: {buckets[b]}" for b in ("2", "3-5", "6-10", "11-25", "26-50", "51+"))
          + f"; largest {sizes[:8]}")

    stab = stability(G, groups, shapes, flows, a.gamma, not a.no_lineage)
    G.batch("Semantic.stability", "UNWIND $rows AS r MATCH (s:Semantic {id: r.id}) SET s.stability = r.v",
            [{"id": k, "v": v} for k, v in stab.items()])
    vals = sorted(stab.values())
    print(f"stability (10 reruns: 5 new seeds, 5 with 80% of statements): median {vals[len(vals) // 2]:.2f}, "
          f"{sum(v >= 0.8 for v in vals)} of {len(vals)} groups at 0.8+, {sum(v < 0.5 for v in vals)} below 0.5")

    if not a.no_names:
        llm = LLM(prompt("semantic_system"), cfg)
        named = name_all(llm, evidence(G, groups), "semantic", BATCH, cfg["llm"].get("concurrency", 6))
        G.batch("Semantic.name", """UNWIND $rows AS r MATCH (s:Semantic {id: r.id})
            SET s.name = r.name, s.description = r.description, s.name_status = r.status, s.name_error = r.error,
                s.named_by = r.model""",
                [{"id": k, "name": d.get("name"), "description": d.get("description"), "status": d["status"],
                  "error": d.get("error"), "model": llm.model} for k, d in named.items()])
        print(f"named: {dict(Counter(d['status'] for d in named.values()))}; LLM {llm.model}: {llm.calls} calls, "
              f"{llm.cached} cached, ${llm.cost():.2f}")
    print(f"{time.time() - t0:.0f}s")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

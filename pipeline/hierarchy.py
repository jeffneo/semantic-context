#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Stage 5c: finalize the semantic layer - a hierarchy of Semantic levels.

Level 1 is cluster.py's Leiden groups, built from usage alone: what the business reads together
and derives from one another. Each level above is built from the one below:

  1. Embed every Semantic of the level (text-embedding-3-large, 512 dimensions) from its
     content: name, description and members. Stored as Semantic.embedding, with a cosine vector
     index `semantic_embedding`.
  2. Score every pair of nodes of the level. Building level L:
         score = (1/L) * usage + (1 - 1/L) * text
     text   cosine similarity of the two embeddings
     usage  how much of each node's outside usage (queries reading both, lineage between them)
            goes to the other, 0 to 1
     Usage decides level 1 entirely; its weight falls level by level (1/2 building level 2, 1/3
     building level 3, ...), and language takes over.
  3. Link each node to its k most similar nodes of the level: (:Semantic)-[:K_SIM {score, text,
     usage, rank}]->(:Semantic).
  4. Leiden on that K_SIM graph, seeded and single-threaded. Building level L, gamma = 3 / (L - 1):
     3 building level 2, where there are ~100 nodes and small communities are wanted, down to
     standard modularity (1) near the top, where a high gamma would leave every node alone.
     Each community is a Semantic
     of the next level: (:Semantic {level: L})<-[:IN_SEMANTIC]-(:Semantic {level: L - 1}), named
     by the LLM in general business language (prompts/parent_*.md).
  5. Stop when the next level would not be smaller, or when the level is too small to group:
     3 nodes or fewer, or k neighbours would link every node to every other.

Usage: uv run pipeline/hierarchy.py [--k 5] [--gamma 3]
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from collections import Counter, defaultdict

from graphdb import Graph, config
from cluster import unit_edges
from llm import LLM, Embedder, name_all, prompt

GRAPH = "semantic_ksim"
BATCH = 8
MIN_LEVEL = 3          # a level this small is the top: grouping it would be trivial


def documents(G: Graph, level: int) -> dict[str, str]:
    """The text each Semantic of a level is embedded from."""
    if level == 1:
        rows = G.rows("""MATCH (s:Semantic {level: 1})
            OPTIONAL MATCH (s)<-[:IN_SEMANTIC]-(v:Variable)
            WITH s, collect(v.name) AS vars
            OPTIONAL MATCH (s)<-[:IN_SEMANTIC]-(c:Unjoined)
            WITH s, vars, collect(c.name) AS cols
            OPTIONAL MATCH (s)<-[:IN_SEMANTIC]-()<-[:IS]-{0,1}(:Column)<-[:HAS_COLUMN]-(t:Table)
            RETURN s.id AS id, s.name AS name, s.description AS d, vars, cols, collect(DISTINCT t.name) AS tables""")
        return {r["id"]: f"{r['name']}. {r['d'] or ''}\nTables: {', '.join(sorted(r['tables'])[:15])}"
                         + (f"\nVariables: {', '.join(v for v in r['vars'] if v)}" if r["vars"] else "")
                         + (f"\nColumns: {', '.join(sorted(r['cols'])[:40])}" if r["cols"] else "") for r in rows}
    rows = G.rows("""MATCH (s:Semantic {level: $l})<-[:IN_SEMANTIC]-(c:Semantic)
                     RETURN s.id AS id, s.name AS name, s.description AS d, collect(c.name) AS kids""", l=level)
    return {r["id"]: f"{r['name']}. {r['d'] or ''}\nGroups: {'; '.join(sorted(k for k in r['kids'] if k))}" for r in rows}


def embed(G: Graph, emb: Embedder, level: int) -> dict[str, list[float]]:
    docs = documents(G, level)
    ids = sorted(docs)
    vecs = emb.embed([docs[i] for i in ids])
    G.batch("Semantic.embedding", "UNWIND $rows AS r MATCH (s:Semantic {id: r.id}) SET s.embedding = r.e",
            [{"id": i, "e": v} for i, v in zip(ids, vecs)], 500)
    return dict(zip(ids, vecs))


def usage(G: Graph, level: int, edges: dict) -> dict[tuple[str, str], float]:
    """Cosine of the inter-group usage graph: W(A, B) / sqrt(E(A) * E(B)), E = usage leaving the group."""
    group = {r["u"]: r["g"] for r in G.rows("""MATCH (u)-[:IN_SEMANTIC]->(:Semantic {level: 1})-[:IN_SEMANTIC]->{0,}(g:Semantic {level: $l})
                                               WHERE u:Variable OR u:Unjoined RETURN u.id AS u, g.id AS g""", l=level)}
    W, E = defaultdict(float), defaultdict(float)
    for (a, b), e in edges.items():
        ga, gb = group.get(a), group.get(b)
        if ga and gb and ga != gb:
            w = e["coread"] + e["flows"]
            W[(min(ga, gb), max(ga, gb))] += w
            E[ga] += w
            E[gb] += w
    return {k: w / math.sqrt(E[k[0]] * E[k[1]]) for k, w in W.items()}


def knn(G: Graph, level: int, k: int, vecs: dict, use: dict, write: bool = True) -> list[dict]:
    """Each node's k best neighbours of the same level; building level L = level + 1, usage counts 1/L."""
    w = 1 / (level + 1)
    ids = sorted(vecs)
    rows = []
    for a in ids:
        cand = []
        for b in ids:
            if a != b:
                text = sum(x * y for x, y in zip(vecs[a], vecs[b]))
                u = use.get((min(a, b), max(a, b)), 0.0)
                cand.append((w * u + (1 - w) * text, text, u, b))
        cand.sort(reverse=True)
        rows += [{"a": a, "b": b, "score": sc, "text": t, "usage": u, "rank": i + 1}
                 for i, (sc, t, u, b) in enumerate(cand[:k])]
    if write:
        G.batch("K_SIM", """UNWIND $rows AS r MATCH (a:Semantic {id: r.a}), (b:Semantic {id: r.b})
                            CREATE (a)-[:K_SIM {score: r.score, text: r.text, usage: r.usage, rank: r.rank}]->(b)""", rows)
    return rows


def communities(G: Graph, level: int, gamma: float) -> dict[str, list[str]]:
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    G.run("""MATCH (a:Semantic {level: $l})
             OPTIONAL MATCH (a)-[r:K_SIM]->(b:Semantic {level: $l})
             WITH gds.graph.project($g, a, b, {relationshipProperties: CASE WHEN r IS NULL THEN null
                                                ELSE {score: r.score} END},
                                    {undirectedRelationshipTypes: ['*']}) AS g
             RETURN g.nodeCount AS n""", g=GRAPH, l=level)
    comm = defaultdict(list)
    for r in G.rows("""CALL gds.leiden.stream($g, {gamma: $gamma, relationshipWeightProperty: 'score',
                                                   randomSeed: 42, concurrency: 1})
                       YIELD nodeId, communityId RETURN gds.util.asNode(nodeId).id AS id, communityId AS c""",
                    g=GRAPH, gamma=gamma):
        comm[r["c"]].append(r["id"])
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    return {f"sem:{level + 1}:{min(ms)}": sorted(ms) for ms in comm.values()}


def parent_evidence(G: Graph, groups: dict[str, list[str]]) -> dict[str, str]:
    info = {r["id"]: r for r in G.rows("MATCH (s:Semantic) RETURN s.id AS id, s.name AS name, s.description AS d")}
    return {p: "\n".join([f"### area {p}", f"id: {p}", f"{len(kids)} groups:"] +
                         [f"- {info[c]['name']}: {info[c]['d'] or ''}" for c in kids])
            for p, kids in groups.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--gamma", type=float, default=3.0)
    a = ap.parse_args()
    cfg = config()
    G = Graph(cfg)
    t0 = time.time()
    G.auto("MATCH (s:Semantic) WHERE s.level > 1 CALL (s) { DETACH DELETE s } IN TRANSACTIONS OF 1000 ROWS")
    G.run("MATCH ()-[r:K_SIM]->() DELETE r")
    dims = cfg["embeddings"]["dimensions"]
    G.run(f"""CREATE VECTOR INDEX semantic_embedding IF NOT EXISTS FOR (s:Semantic) ON s.embedding
              OPTIONS {{indexConfig: {{`vector.dimensions`: {dims}, `vector.similarity_function`: 'cosine'}}}}""")
    emb, llm = Embedder(cfg), LLM(prompt("parent_system"), cfg)
    edges = unit_edges(G)
    level = 1
    n = G.rows("MATCH (s:Semantic {level: 1}) RETURN count(s) AS n")[0]["n"]
    print(f"level 1: {n} Semantic nodes (cluster.py)")
    while True:
        vecs = embed(G, emb, level)
        if n <= MIN_LEVEL or a.k >= n - 1:
            print(f"level {level} is the top: {n} nodes" + (f" (k={a.k} would link every node to every other)"
                                                          if n > MIN_LEVEL else ""))
            break
        use = usage(G, level, edges)
        n_edges = len(knn(G, level, a.k, vecs, use))
        gamma = a.gamma / level                  # building level L = level + 1: gamma / (L - 1)
        groups = communities(G, level, gamma)
        sizes = sorted((len(v) for v in groups.values()), reverse=True)
        print(f"level {level}: {n_edges} K_SIM (k={a.k}, usage weight 1/{level + 1}; "
              f"{sum(1 for v in use.values() if v > 0)} node pairs with usage) "
              f"-> Leiden (gamma {gamma:.2f}) {len(groups)} communities {sizes[:12]}")
        if len(groups) >= n:
            print(f"stop: level {level + 1} would have {len(groups)} nodes, not fewer than {n}")
            break
        G.batch("Semantic", """UNWIND $rows AS r CREATE (p:Semantic {id: r.id, level: r.level, size: size(r.kids)})
                               WITH p, r UNWIND r.kids AS kid MATCH (c:Semantic {id: kid}) CREATE (c)-[:IN_SEMANTIC]->(p)""",
                [{"id": p, "level": level + 1, "kids": kids} for p, kids in groups.items()])
        named = name_all(llm, parent_evidence(G, groups), "parent", BATCH, cfg["llm"].get("concurrency", 6))
        G.batch("Semantic.name", """UNWIND $rows AS r MATCH (s:Semantic {id: r.id})
            SET s.name = r.name, s.description = r.description, s.name_status = r.status, s.name_error = r.error,
                s.named_by = r.model""",
                [{"id": p, "name": d.get("name"), "description": d.get("description"), "status": d["status"],
                  "error": d.get("error"), "model": llm.model} for p, d in named.items()])
        G.run("""MATCH (p:Semantic {level: $l})<-[:IN_SEMANTIC]-+(:Semantic {level: 1})
                   <-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)<-[:HAS_COLUMN]-(t:Table)
                 WITH p, count(DISTINCT t) AS n SET p.tables = n""", l=level + 1)
        print(f"  level {level + 1}: {len(groups)} Semantic nodes named {dict(Counter(d['status'] for d in named.values()))}")
        level, n = level + 1, len(groups)
    summary = G.rows("MATCH (s:Semantic) RETURN s.level AS level, count(*) AS n ORDER BY level")
    print("levels: " + ", ".join(f"{r['level']}: {r['n']}" for r in summary)
          + f"; LLM {llm.calls} calls, {llm.cached} cached, ${llm.cost():.2f}; {time.time() - t0:.0f}s")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Semantic levels 2 and up: a hierarchy over the level-1 groups.

Level 1 is qlsc/cluster.py's Leiden groups, built from usage alone. Each level above is built from
the one below:

  1. Embed every Semantic of the level from its content (name, description, members), stored as
     Semantic.embedding with the cosine vector index `semantic_embedding`.
  2. Score every pair of nodes of the level. Building level L:
         score = (1/L) * usage + (1 - 1/L) * text
     text   cosine similarity of the two embeddings
     usage  how much of each node's outside usage (queries reading both, lineage between them) goes
            to the other, 0 to 1
     Usage decides level 1 entirely; its weight falls level by level (1/2 building level 2, 1/3
     building level 3, ...), and language takes over.
  3. Link each node to its k best-scoring nodes of the level:
     (:Semantic)-[:K_SIM {score, text, usage, rank}]->(:Semantic).
  4. Leiden on that K_SIM graph, seeded and single-threaded, at gamma / (L - 1): high building level
     2, where there are ~100 nodes and small communities are wanted, down to standard modularity near
     the top, where a high gamma would leave every node alone. Each community is a Semantic of the
     next level, (:Semantic {level: L})<-[:IN_SEMANTIC]-(:Semantic {level: L - 1}), named by the LLM
     in general business language (prompts/parent_system.md).
  5. Stop when the next level would not be smaller, or the level is too small to group: min_level
     nodes or fewer, or k neighbours would link every node to every other.
"""

from __future__ import annotations

import math
import time
from collections import Counter, defaultdict

from qlsc.cluster import unit_edges
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, cosine, name_all, prompt, write_names

PROJECTION = "semantic_ksim"
BATCH = 8


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
        return {
            r["id"]: f"{r['name']}. {r['d'] or ''}\nTables: {', '.join(sorted(r['tables'])[:15])}"
            + (f"\nVariables: {', '.join(v for v in r['vars'] if v)}" if r["vars"] else "")
            + (f"\nColumns: {', '.join(sorted(r['cols'])[:40])}" if r["cols"] else "")
            for r in rows
        }
    rows = G.rows(
        """MATCH (s:Semantic {level: $l})<-[:IN_SEMANTIC]-(c:Semantic)
                     RETURN s.id AS id, s.name AS name, s.description AS d, collect(c.name) AS kids""",
        l=level,
    )
    return {
        r["id"]: f"{r['name']}. {r['d'] or ''}\nGroups: {'; '.join(sorted(k for k in r['kids'] if k))}"
        for r in rows
    }


def embed(G: Graph, emb: Embedder, level: int) -> dict[str, list[float]]:
    docs = documents(G, level)
    ids = sorted(docs)
    vecs = emb.embed([docs[i] for i in ids])
    G.batch(
        "Semantic.embedding",
        "UNWIND $rows AS r MATCH (s:Semantic {id: r.id}) SET s.embedding = r.e",
        [{"id": i, "e": v} for i, v in zip(ids, vecs)],
        500,
    )
    return dict(zip(ids, vecs))


def usage(G: Graph, level: int, edges: dict) -> dict[tuple[str, str], float]:
    """Cosine of the inter-group usage graph: W(A, B) / sqrt(E(A) * E(B)), E = usage leaving the group."""
    group = {
        r["u"]: r["g"]
        for r in G.rows(
            """MATCH (u)-[:IN_SEMANTIC]->(:Semantic {level: 1})-[:IN_SEMANTIC]->{0,}(g:Semantic {level: $l})
           WHERE u:Variable OR u:Unjoined RETURN u.id AS u, g.id AS g""",
            l=level,
        )
    }
    between, leaving = defaultdict(float), defaultdict(float)
    for (a, b), e in edges.items():
        ga, gb = group.get(a), group.get(b)
        if ga and gb and ga != gb:
            w = e["coread"] + e["flows"]
            between[(min(ga, gb), max(ga, gb))] += w
            leaving[ga] += w
            leaving[gb] += w
    return {k: w / math.sqrt(leaving[k[0]] * leaving[k[1]]) for k, w in between.items()}


def knn(G: Graph, level: int, k: int, vecs: dict, use: dict, write: bool = True) -> list[dict]:
    """Each node's k best neighbours of the same level; building level L = level + 1, usage counts 1/L."""
    w = 1 / (level + 1)
    ids = sorted(vecs)
    rows = []
    for a in ids:
        cand = []
        for b in ids:
            if a != b:
                text = cosine(vecs[a], vecs[b])
                u = use.get((min(a, b), max(a, b)), 0.0)
                cand.append((w * u + (1 - w) * text, text, u, b))
        cand.sort(reverse=True)
        rows += [
            {"a": a, "b": b, "score": sc, "text": t, "usage": u, "rank": i + 1}
            for i, (sc, t, u, b) in enumerate(cand[:k])
        ]
    if write:
        G.batch(
            "K_SIM",
            """UNWIND $rows AS r MATCH (a:Semantic {id: r.a}), (b:Semantic {id: r.b})
                            CREATE (a)-[:K_SIM {score: r.score, text: r.text, usage: r.usage, rank: r.rank}]->(b)""",
            rows,
        )
    return rows


def communities(G: Graph, level: int, rows: list[dict], gamma: float, seed: int) -> dict[str, list[str]]:
    """Leiden over the level's K_SIM links -> the next level's groups."""
    G.project_pairs(PROJECTION, [{"a": r["a"], "b": r["b"], "w": r["score"]} for r in rows])
    groups = G.leiden(PROJECTION, gamma, seed)
    G.drop_projection(PROJECTION)
    return {f"sem:{level + 1}:{k}": ms for k, ms in groups.items()}


def parent_evidence(G: Graph, groups: dict[str, list[str]]) -> dict[str, str]:
    info = {
        r["id"]: r for r in G.rows("MATCH (s:Semantic) RETURN s.id AS id, s.name AS name, s.description AS d")
    }
    return {
        p: "\n".join(
            [f"### area {p}", f"id: {p}", f"{len(kids)} groups:"]
            + [f"- {info[c]['name']}: {info[c]['d'] or ''}" for c in kids]
        )
        for p, kids in groups.items()
    }


def run(s: Settings) -> None:
    p = s.params["hierarchy"]
    t0 = time.time()
    with Graph(s) as G:
        G.delete("(n:Semantic) WHERE n.level > 1", 1000)
        G.run("MATCH ()-[r:K_SIM]->() DELETE r")
        G.run(f"""CREATE VECTOR INDEX semantic_embedding IF NOT EXISTS FOR (s:Semantic) ON s.embedding
                  OPTIONS {{indexConfig: {{`vector.dimensions`: {s["embeddings"]["dimensions"]},
                                           `vector.similarity_function`: 'cosine'}}}}""")
        emb, llm = Embedder(s), LLM(prompt("parent_system", **s.business), s)
        edges = unit_edges(G)
        level, n = 1, G.value("MATCH (s:Semantic {level: 1}) RETURN count(s)")
        print(f"level 1: {n} Semantic nodes (qlsc/cluster.py)")
        while True:
            vecs = embed(G, emb, level)
            if n <= p["min_level"] or p["k"] >= n - 1:
                why = f" (k={p['k']} would link every node to every other)" if n > p["min_level"] else ""
                print(f"level {level} is the top: {n} nodes{why}")
                break
            use = usage(G, level, edges)
            rows = knn(G, level, p["k"], vecs, use)
            gamma = p["gamma"] / level  # building level L = level + 1: gamma / (L - 1)
            groups = communities(G, level, rows, gamma, p["seed"])
            sizes = sorted((len(v) for v in groups.values()), reverse=True)
            print(
                f"level {level}: {len(rows)} K_SIM (k={p['k']}, usage weight 1/{level + 1}; "
                f"{sum(1 for v in use.values() if v > 0)} node pairs with usage) "
                f"-> Leiden (gamma {gamma:.2f}) {len(groups)} communities {sizes[:12]}"
            )
            if len(groups) >= n:
                print(f"stop: level {level + 1} would have {len(groups)} nodes, not fewer than {n}")
                break
            G.batch(
                "Semantic",
                """UNWIND $rows AS r CREATE (p:Semantic {id: r.id, level: r.level, size: size(r.kids)})
                                   WITH p, r UNWIND r.kids AS kid MATCH (c:Semantic {id: kid})
                                   CREATE (c)-[:IN_SEMANTIC]->(p)""",
                [{"id": g, "level": level + 1, "kids": kids} for g, kids in groups.items()],
            )
            named = name_all(llm, parent_evidence(G, groups), ("area", "areas"), BATCH)
            write_names(G, "Semantic", named, llm.model)
            G.run(
                """MATCH (p:Semantic {level: $l})<-[:IN_SEMANTIC]-+(:Semantic {level: 1})
                       <-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)<-[:HAS_COLUMN]-(t:Table)
                     WITH p, count(DISTINCT t) AS n SET p.tables = n""",
                l=level + 1,
            )
            print(
                f"  level {level + 1}: {len(groups)} Semantic nodes named "
                f"{dict(Counter(d['status'] for d in named.values()))}"
            )
            level, n = level + 1, len(groups)
        levels = G.rows("MATCH (s:Semantic) RETURN s.level AS level, count(*) AS n ORDER BY level")
    print(
        "levels: "
        + ", ".join(f"{r['level']}: {r['n']}" for r in levels)
        + f"; {llm.summary()}; {time.time() - t0:.0f}s"
    )

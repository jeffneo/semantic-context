#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Question -> the tables to use, by meaning and by use.

The question is embedded like the stored documents (same model, centered on each label's
mean, normalized) and searched in three vector indexes:
  tables      direct match on what a table holds
  subjects    the area it belongs to (a table inherits its subject's match, discounted)
  variables   a variable the question names (a table inherits its columns' matches, discounted)
plus a small usage prior: tables the business consumes rank above ones nobody uses.
Each result says which of these put it there.

Usage: uv run pipeline/retrieve.py "Which contact centers see the most account closures?"
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict

from graphdb import Graph, config
from semantics import Embedder

WEIGHTS = {"table": 1.0, "subject": 0.8, "variable": 0.7}
USAGE_PRIOR = 0.03


def centered(G: Graph, vec: list[float], label: str) -> list[float]:
    mean = G.rows("MATCH (e:EmbeddingSpace {id: $l}) RETURN e.mean AS m", l=label)[0]["m"]
    c = [x - m for x, m in zip(vec, mean)]
    n = math.sqrt(sum(x * x for x in c)) or 1.0
    return [x / n for x in c]


def search(question: str, k: int = 10, G: Graph | None = None, emb: Embedder | None = None,
           use: tuple = ("table", "subject", "variable"), prior: bool = True) -> list[dict]:
    own = G is None
    G = G or Graph()
    emb = emb or Embedder(config())
    raw = emb.embed([question])[0]
    score, why = defaultdict(float), defaultdict(list)

    def bump(t, s, reason):
        if s > score[t]:
            score[t] = s
        why[t].append(reason)
    if "table" in use:
        for r in G.rows("""CALL db.index.vector.queryNodes('table_embedding', 30, $v) YIELD node, score
                           RETURN node.id AS t, score""", v=centered(G, raw, "Table")):
            bump(r["t"], WEIGHTS["table"] * r["score"], f"table {r['score']:.2f}")
    if "subject" in use:
        for r in G.rows("""CALL db.index.vector.queryNodes('subject_embedding', 6, $v) YIELD node, score
                           MATCH (t:Table)-[:IN_SUBJECT]->(node)
                           RETURN t.id AS t, node.display_name AS s, score""", v=centered(G, raw, "Subject")):
            bump(r["t"], WEIGHTS["subject"] * r["score"], f"subject '{r['s']}' {r['score']:.2f}")
    if "variable" in use:
        for r in G.rows("""CALL db.index.vector.queryNodes('variable_embedding', 20, $v) YIELD node, score
                           MATCH (node)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(t:Table) WHERE t.in_catalog
                           RETURN t.id AS t, node.display_name AS v, score""", v=centered(G, raw, "Variable")):
            bump(r["t"], WEIGHTS["variable"] * r["score"], f"variable '{r['v']}' {r['score']:.2f}")
    usage = {r["t"]: r["n"] or 0 for r in G.rows(
        "MATCH (t:Table) WHERE t.id IN $ts RETURN t.id AS t, t.consumer_count AS n", ts=list(score))}
    out = []
    for t, s in score.items():
        p = USAGE_PRIOR * math.log(1 + usage.get(t, 0)) if prior else 0.0
        out.append({"table": t, "score": s + p, "why": why[t][:3] + ([f"used by {usage.get(t, 0)} principals"] if p else [])})
    out.sort(key=lambda x: -x["score"])
    if own:
        G.close()
    return out[:k]


if __name__ == "__main__":
    for r in search(" ".join(sys.argv[1:]) or "Which contact centers see the most account closures?"):
        print(f"{r['score']:.3f}  {r['table']}  <- {'; '.join(r['why'])}")

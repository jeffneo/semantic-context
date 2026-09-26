"""A fingerprint of the example's graph, to prove a refactor changed nothing it should not.

Counts per label and relationship type, and hashes of the ids and key properties of every layer. Two
builds from the same work/ with the same code and parameters give the same fingerprint.

Usage:
  uv run examples/fennmoor-bank/eval/fingerprint.py > before.json
  ... change the code, uv run qlsc build ...
  uv run examples/fennmoor-bank/eval/fingerprint.py | diff before.json -
"""

from __future__ import annotations

import hashlib
import json
import sys

from common import settings

from qlsc.graph import Graph

NODES = {  # label -> what else to hash besides the id
    "JoinKey": "k.confidence + '|' + toString(k.identity)",
    "Variable": "k.name + '|' + toString(k.size)",
    "Semantic": "k.name + '|' + toString(k.level) + '|' + toString(k.size) + '|' + toString(round(k.stability, 4))",
    "Concept": "k.name",
    "QueryShape": "toString(k.jobs)",
    "Column": "coalesce(k.type, '')",
    "Table": "k.kind",
}
EDGES = {
    "IS": "MATCH (a:Column)-[:IS]->(b:Variable) RETURN a.id AS a, b.id AS b ORDER BY a",
    "IN_SEMANTIC": "MATCH (a)-[:IN_SEMANTIC]->(b) RETURN a.id AS a, b.id AS b ORDER BY a, b",
    "MEANS": """MATCH (a)-[m:MEANS]->(b) RETURN a.id AS a, b.id AS b, m.how AS h, round(coalesce(m.score, 0), 4) AS s
                ORDER BY a, b, h""",
    "K_SIM": "MATCH (a)-[m:K_SIM]->(b) RETURN a.id AS a, b.id AS b, m.rank AS r ORDER BY a, r",
    "FLOWS": "MATCH (a)-[:FLOWS]->(b) RETURN a.id AS a, b.id AS b ORDER BY a, b",
    "READS": "MATCH (s)-[m:READS]->(c) RETURN s.id AS s, c.id AS c, m.roles AS r ORDER BY s, c, r",
    "FILTERS": "MATCH (s)-[m:FILTERS]->(c) RETURN s.id AS s, c.id AS c, m.values AS v ORDER BY s, c, v",
}


def digest(rows) -> str:
    return hashlib.sha1(json.dumps(rows).encode()).hexdigest()[:12]


def fingerprint(G: Graph) -> dict:
    out = {
        f"label {r['l']}": r["n"]
        for r in G.rows("MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS n ORDER BY l")
    }
    out |= {
        f"rel {r['t']}": r["n"]
        for r in G.rows("MATCH ()-[x]->() RETURN type(x) AS t, count(*) AS n ORDER BY t")
    }
    for label, props in NODES.items():
        out[f"hash {label}"] = digest(
            G.rows(f"MATCH (k:{label}) RETURN k.id AS id, {props} AS p ORDER BY id")
        )
    for name, query in EDGES.items():
        out[f"hash {name}"] = digest(G.rows(query))
    for level in G.rows("MATCH (s:Semantic) RETURN DISTINCT s.level AS l ORDER BY l"):
        rows = G.rows(
            """MATCH (u)-[:IN_SEMANTIC]->(s:Semantic {level: $l}) RETURN s.id AS s, u.id AS u
                         ORDER BY s, u""",
            l=level["l"],
        )
        out[f"hash level {level['l']} membership"] = digest(rows)
    return out


def main() -> int:
    with Graph(settings()) as G:
        json.dump(fingerprint(G), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

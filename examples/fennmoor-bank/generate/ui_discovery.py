"""Write the demo UI's picture of the discovered semantic layer -> ui/src/examples/fennmoor/discovery/discovery.json.

What qlsc built from the query log, read from the semantic layer's graph (the `bigquery` database; `qlsc build` first, Neo4j up):
  funnel      how many things there are at each stage, from the log to the groups
  areas       the Semantic nodes: level 3 (the broad areas), 2 and 1 (the groups read together), each with its name, what it is and its parent
  tables      each catalog table's place in the hierarchy: the level-1 group that holds most of its columns, and so its level-2 and level-3
              parents; none for a table no query read, or none of whose columns a group holds
  variables   each Variable (the real-world thing joined columns share): its columns, and the joins between them with who made them and how often
  keptOut     the joins that were not allowed to merge anything: two id spaces production keeps apart, and joins that relate things without
              identifying them
Nothing of the spec's answer key is read. Deterministic. Usage: uv run examples/fennmoor-bank/generate/ui_discovery.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from qlsc import config
from qlsc.graph import Graph

EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "discovery" / "discovery.json"

AREAS = """
MATCH (s:Semantic)
OPTIONAL MATCH (s)-[:IN_SEMANTIC]->(p:Semantic)
RETURN s.id AS id, s.level AS level, s.name AS name, s.description AS description, s.tables AS tables, s.size AS size,
       s.stability AS stability, p.id AS parent
ORDER BY level DESC, tables DESC, id
"""
# every catalog column with the level-1 group that holds it: itself or, when it is joined, its variable
MEMBERSHIP = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog
OPTIONAL MATCH (c)-[:IS]->(v:Variable)
WITH t, coalesce(v, c) AS u
OPTIONAL MATCH (u)-[:IN_SEMANTIC]->(g:Semantic {level: 1})
RETURN t.id AS table, g.id AS group, EXISTS { (:QueryShape)-[:REFERENCES]->(t) } AS read
"""
VARIABLES = """
MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table)
RETURN v.id AS id, v.name AS name, v.description AS description, t.id AS table, c.name AS column
ORDER BY id, table, column
"""
# the joins whose two columns are one variable, with the queries that made them
JOINS = """
MATCH (v:Variable)<-[:IS]-(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)-[:IS]->(v) WHERE a.id < b.id
OPTIONAL MATCH (q:QueryShape)-[:USES_JOIN]->(k)
RETURN v.id AS variable, a.id AS a, b.id AS b, k.confidence AS confidence, k.people AS people, count(DISTINCT q) AS shapes, coalesce(sum(q.jobs), 0) AS jobs
ORDER BY variable, a, b
"""
KEPT_OUT = """
MATCH (ta:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)<-[:HAS_COLUMN]-(tb:Table)
WHERE (k.confidence = 'suspect' OR NOT k.identity) AND a.id < b.id
RETURN ta.id + '.' + a.name AS a, tb.id + '.' + b.name AS b, k.confidence AS confidence, k.identity AS identity, k.confidence_reason AS why
ORDER BY confidence, a, b
"""
COUNTS = """
RETURN count { (:QueryShape) } AS shapes, count { (:QueryShape {origin: 'log'}) } AS logShapes, count { (:JoinKey) } AS joinKeys, count { (:Variable) } AS variables,
       count { (:Column)-[:IS]->(:Variable) } AS joined, count { (:Column) } AS columns
"""


def main() -> None:
    s = config.load(EXAMPLE / "estate.yaml")
    with Graph(s) as G:
        areas = G.rows(AREAS)
        membership = G.rows(MEMBERSHIP)
        variables = G.rows(VARIABLES)
        joins = G.rows(JOINS)
        kept = G.rows(KEPT_OUT)
        counts = G.rows(COUNTS)[0]
        texts = G.value(
            "MATCH (q:QueryShape {origin: 'log'}) RETURN sum(q.texts)"
        )  # distinct query texts the log held (a view's definition has none)

    # The areas, broad first, each pointing at its parent by position.
    index = {a["id"]: i for i, a in enumerate(areas)}
    out_areas = [
        {
            "name": a["name"],
            "description": a["description"],
            "level": a["level"],
            "tables": a["tables"],
            "members": a["size"],
            **({"stability": round(a["stability"], 2)} if a["stability"] is not None else {}),
            **({"parent": index[a["parent"]]} if a["parent"] else {}),
        }
        for a in areas
    ]

    # A table sits in the level-1 group that holds most of its columns (the larger group, then the id, when they tie).
    held = defaultdict(Counter)
    columns = Counter()
    unread = set()  # tables no query referenced
    for r in membership:
        columns[r["table"]] += 1
        if not r["read"]:
            unread.add(r["table"])
        if r["group"]:
            held[r["table"]][r["group"]] += 1
    tables = []
    for table in sorted(columns):
        entry = {"id": table, "columns": columns[table]}
        if table in unread:
            entry["unread"] = True
        if held[table]:
            group = min(held[table], key=lambda g: (-held[table][g], -areas[index[g]]["tables"], g))
            chain = [index[group]]
            while "parent" in out_areas[chain[-1]]:
                chain.append(out_areas[chain[-1]]["parent"])
            entry["groups"] = chain  # level 1, 2, 3
            entry["share"] = round(held[table][group] / columns[table], 2)
        tables.append(entry)

    by_variable: dict[str, dict] = {}
    for r in variables:
        v = by_variable.setdefault(
            r["id"], {"name": r["name"], "description": r["description"], "columns": [], "joins": []}
        )
        v["columns"].append([r["table"], r["column"]])
    where = {}  # a column's position in its variable, for the joins
    for vid, v in by_variable.items():
        for i, (table, column) in enumerate(v["columns"]):
            where[(vid, f"{table}.{column}")] = i
    for r in joins:
        v = by_variable[r["variable"]]
        v["joins"].append(
            [
                where[(r["variable"], r["a"])],
                where[(r["variable"], r["b"])],
                r["confidence"],
                r["jobs"],
                r["people"],
            ]
        )
    out_variables = sorted(
        by_variable.values(), key=lambda v: (-len({t for t, _ in v["columns"]}), v["name"])
    )
    for v in out_variables:
        v["tables"] = len({t for t, _ in v["columns"]})

    out = {
        "funnel": {
            "texts": texts,
            "shapes": counts["shapes"],
            "viewShapes": counts["shapes"] - counts["logShapes"],
            "joinKeys": counts["joinKeys"],
            "variables": counts["variables"],
            "joined": counts["joined"],
            "columns": counts["columns"],
            "groups": dict(sorted(Counter(a["level"] for a in areas).items())),
        },
        "areas": out_areas,
        "tables": tables,
        "variables": out_variables,
        "keptOut": [
            {
                "a": r["a"],
                "b": r["b"],
                "kind": "two id spaces" if r["confidence"] == "suspect" else "relates, does not identify",
                "why": r["why"],
            }
            for r in kept
        ],
    }
    assert "jeffdavis" not in json.dumps(out), "the physical project is named"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n")
    grouped = sum(1 for t in tables if "groups" in t)
    print(
        f"{OUT.relative_to(ROOT)}: {len(out_areas)} areas, {grouped} of {len(tables)} tables placed, {len(out_variables)} variables, "
        f"{len(out['keptOut'])} joins kept out, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()

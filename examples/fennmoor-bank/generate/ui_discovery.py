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

from ui_queries import query

from qlsc import config
from qlsc.graph import Graph

EXAMPLE = Path(__file__).resolve().parents[1]
PROJECT = config.load(EXAMPLE / "estate.yaml")["warehouse"][
    "project"
]  # the physical project: never in what is written
ROOT = EXAMPLE.parents[1]
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "discovery" / "discovery.json"

AREAS = query("discovery", "areas")
MEMBERSHIP = query("discovery", "membership")
VARIABLES = query("discovery", "variables")
JOINS = query("discovery", "joins")
KEPT_OUT = query("discovery", "kept_out")
COUNTS = query("discovery", "counts")
QUERY_TEXTS = query("discovery", "query_texts")


def main() -> None:
    s = config.load(EXAMPLE / "estate.yaml")
    with Graph(s) as G:
        areas = G.rows(AREAS)
        membership = G.rows(MEMBERSHIP)
        variables = G.rows(VARIABLES)
        joins = G.rows(JOINS)
        kept = G.rows(KEPT_OUT)
        counts = G.rows(COUNTS)[0]
        texts = G.value(QUERY_TEXTS)

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
    assert PROJECT not in json.dumps(out), "the physical project is named"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n")
    grouped = sum(1 for t in tables if "groups" in t)
    print(
        f"{OUT.relative_to(ROOT)}: {len(out_areas)} areas, {grouped} of {len(tables)} tables placed, {len(out_variables)} variables, "
        f"{len(out['keptOut'])} joins kept out, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()

"""Write the demo UI's picture of the generated Virtual Graph schema -> ui/src/examples/fennmoor/virtual/virtual.json.

`qlsc virtualize` wrote a model of the warehouse's rows from the semantic layer (work/virtual/): which tables are node labels, which columns point at
which, and a view per node table. This keeps what a page needs to show how:
  nodes          each label, its table, its key and why that column is the key, the Variable it holds, the area the table sits in, its properties
                 and the view's SQL
  relationships  each type, its two labels, the column that points and why it counts (who joined it, how)
  leftOut        what was not made a node, and the joins that were not allowed to become relationships
  questions      the graph-shaped questions answered over the model (results/graph_accuracy.json): the Cypher written, and how both routes scored
The schema, views and evidence are `qlsc virtualize`'s own files (the evidence is MODEL.md's tables, checked against schema.json: a change to either
fails here and not on the page); the Variables and areas come from the layer's graph. Nothing of the spec's answer key is read, and the physical project
the views are deployed to is not written.

Run `qlsc virtualize` first (Neo4j up). Deterministic. Usage: uv run examples/fennmoor-bank/generate/ui_virtual.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from qlsc import config
from qlsc.graph import Graph
from qlsc.virtualize import GROUPS

EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
MODEL = EXAMPLE / "work" / "virtual"
QUESTIONS = EXAMPLE / "results" / "graph_accuracy.json"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "virtual" / "virtual.json"

NODES = """
MATCH (t:Table) WHERE t.graph_label IS NOT NULL
OPTIONAL MATCH (t)-[:HAS_COLUMN]->(k:Column {graph_key: true})
OPTIONAL MATCH (k)-[:IS]->(v:Variable)
RETURN t.id AS table, t.graph_label AS label, k.name AS key, v.name AS variable
"""
POINTERS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE c.graph_relationship IS NOT NULL
OPTIONAL MATCH (c)-[:IS]->(v:Variable)
RETURN c.graph_relationship AS type, t.id AS table, c.name AS column, v.name AS variable
"""


def rows(markdown: str, heading: str) -> list[str]:
    """The lines under a `## heading` of MODEL.md, up to the next."""
    body = markdown.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
    return [line for line in body.splitlines() if line.strip()]


def model_evidence() -> tuple[dict, dict, list]:
    """MODEL.md: why each node is a node, why each relationship is one, and what was left out."""
    text = (MODEL / "MODEL.md").read_text()
    nodes, rels, left = {}, {}, []
    for line in rows(text, "Nodes")[2:]:  # past the table's header and its rule
        m = re.fullmatch(r"\| (\w+) \| (\S+) \| (\S+) \| (.+) \|", line)
        if m:
            nodes[m[1]] = {"why": m[4]}
    for line in rows(text, "Relationships")[2:]:
        m = re.fullmatch(r"\| \(:(\w+)\)-\[:(\w+)\]->\(:(\w+)\) \| (\S+) \| (.+) \|", line)
        if m:
            rels[m[2]] = {"why": m[5]}
    for line in rows(text, "Left out"):
        if m := re.fullmatch(r"- \*\*(\S+)\*\*: not a node, (.+)", line):
            left.append({"what": "table", "name": m[1], "why": m[2]})
        elif m := re.fullmatch(r"- `(.+?)`: (?:suspect, )?(.+)", line):
            left.append({"what": "join", "name": m[1].replace(" = ", " ⇄ "), "why": m[2]})
        elif line.startswith("- "):
            raise SystemExit(f"MODEL.md has a line this does not read: {line}")
    return nodes, rels, left


def view_sql() -> dict[str, str]:
    """views.sql: `-- view` then its SELECT."""
    out = {}
    for block in (MODEL / "views.sql").read_text().strip().split("\n\n"):
        name, sql = block.split("\n", 1)
        out[name.removeprefix("-- ")] = sql.rstrip(";")
    return out


def main() -> None:
    schema = json.loads((MODEL / "schema.json").read_text())["entities"]
    why_node, why_rel, left_out = model_evidence()
    views = view_sql()
    s = config.load(EXAMPLE / "estate.yaml")
    with Graph(s) as G:
        tables = {r["label"]: r for r in G.rows(NODES)}
        pointers = {r["type"]: r for r in G.rows(POINTERS)}
        areas = {r["table"]: r["area"] for r in G.rows(GROUPS, tables=[t["table"] for t in tables.values()])}

    assert set(why_node) == {n["label"] for n in schema["nodes"]}, (
        "MODEL.md and schema.json disagree on the nodes"
    )
    assert set(why_rel) == {r["label"] for r in schema["relationships"]}, (
        "MODEL.md and schema.json disagree on the relationships"
    )
    assert set(tables) == set(why_node), (
        "the graph and schema.json disagree on the nodes: run `qlsc virtualize` again"
    )

    nodes = []
    for n in schema["nodes"]:
        t = tables[n["label"]]
        nodes.append(
            {
                "label": n["label"],
                "table": t["table"],
                "view": n["table"],
                "key": t["key"],
                "variable": t["variable"],
                "why": why_node[n["label"]]["why"],
                "area": areas.get(t["table"]),
                "properties": [[p["column"], p["type"]] for p in n["properties"]],
                "sql": views[n["table"]],
            }
        )
    relationships = []
    for r in schema["relationships"]:
        p = pointers[r["label"]]
        relationships.append(
            {
                "type": r["label"],
                "start": r["start"]["targetEntity"],
                "end": r["end"]["targetEntity"],
                "table": p["table"],
                "column": p["column"],
                "endKey": r["end"]["keys"][0]["nodeColumn"],
                "variable": p["variable"],
                "why": why_rel[r["label"]]["why"],
            }
        )

    graph = json.loads(QUESTIONS.read_text())
    questions = [
        {
            "id": k,
            "text": q["question"],
            "cypher": q["cypher"]["query"],
            "cypher_verdict": q["cypher"]["verdict"],
            "cypher_why": q["cypher"]["why"],
            "sql_verdict": q["sql"]["verdict"],
            "sql_why": q["sql"]["why"],
            "routed": q["routed"]["route"],
            "routed_verdict": q["routed"]["verdict"],
            "rows": q["reference_rows"],
        }
        for k, q in sorted(graph.items())
        if re.fullmatch(r"G\d+", k)
    ]
    out = {
        "inScope": len(why_node) + sum(1 for x in left_out if x["what"] == "table"),
        "nodes": sorted(nodes, key=lambda n: n["label"]),
        "relationships": sorted(relationships, key=lambda r: (r["start"], r["type"])),
        "leftOut": left_out,
        "questions": questions,
    }
    text = json.dumps(out, separators=(",", ":"), sort_keys=True)
    assert "jeffdavis" not in text and "fnb_" not in text, (
        "the physical project or its dataset prefix is named"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n")
    print(
        f"{OUT.relative_to(ROOT)}: {len(nodes)} nodes, {len(relationships)} relationships, {len(left_out)} left out, "
        f"{len(questions)} questions, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()

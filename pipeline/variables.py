#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Stage 5a: variables - one per set of columns the business joins to one another.

Preprocessing for the semantic layer: clustering and naming happen over variables, so
the same real-world thing is represented once across the warehouse.

  1. GDS Cypher projection: every (a:Column)<-[:ON]-(:JoinKey)-[:ON]->(b:Column) becomes an
     undirected a -- b relationship.
  2. WCC over the projection. Each component is one variable.
  3. Materialize: (:Variable {id, size, tables}) and (:Column)-[:IS]->(:Variable).
     The id is 'var:' + the component's smallest column id, so it is stable across runs.
  4. Name each variable with the LLM (prompts/variable_*.md): name, description, and whether the
     columns look like one thing (coherent / note). A failed answer is retried once, then
     recorded as failed rather than dropped.
  5. Every column with no variable gets the label :Unjoined.

Usage: uv run pipeline/variables.py [--no-names]
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict

from graphdb import Graph, config
from llm import LLM, check_name, name_all, prompt

GRAPH = "variables"
BATCH = 20
MAX_COLUMNS_SHOWN = 25
SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
    "type": "object", "required": ["id", "name", "description", "coherent", "note"], "properties": {
        "id": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"},
        "coherent": {"type": "boolean"}, "note": {"type": "string"}}}}}}


def components(G: Graph) -> dict[str, list[str]]:
    """WCC over columns joined by a JoinKey -> component id -> column ids."""
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    p = G.rows("""MATCH (a:Column)<-[:ON]-(:JoinKey)-[:ON]->(b:Column)
                  WHERE elementId(a) <= elementId(b)
                  WITH gds.graph.project($g, a, b, {}, {undirectedRelationshipTypes: ['*']}) AS g
                  RETURN g.nodeCount AS nodes, g.relationshipCount AS rels""", g=GRAPH)[0]
    comp = defaultdict(list)
    for r in G.rows("""CALL gds.wcc.stream($g, {concurrency: 1}) YIELD nodeId, componentId
                       RETURN gds.util.asNode(nodeId).id AS c, componentId AS k""", g=GRAPH):
        comp[r["k"]].append(r["c"])
    G.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAPH)
    print(f"projection: {p['nodes']:,} columns, {p['rels']:,} join relationships -> {len(comp):,} components")
    return {f"var:{min(cs)}": sorted(cs) for cs in comp.values()}


def evidence(G: Graph, variables: dict[str, list[str]]) -> dict[str, str]:
    """What the namer sees for each variable: its columns, how they are joined, values filtered on."""
    col = {r["c"]: r for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(:Variable)
                                        RETURN c.id AS c, t.id AS t, c.name AS name, c.type AS type""")}
    var_of = {c: v for v, cs in variables.items() for c in cs}
    joins = defaultdict(Counter)
    for r in G.rows("""MATCH (s:QueryShape)-[:USES_JOIN]->(k:JoinKey)-[:ON {side: 'left'}]->(a:Column),
                             (k)-[:ON {side: 'right'}]->(b:Column)
                       RETURN a.id AS a, b.id AS b, count(s) AS n"""):
        joins[var_of[r["a"]]][(r["a"], r["b"])] += r["n"]
    values = defaultdict(Counter)
    for r in G.rows("""MATCH (:QueryShape)-[f:FILTERS]->(c:Column)-[:IS]->(:Variable) WHERE size(f.values) > 0
                       UNWIND range(0, size(f.values) - 1) AS i
                       RETURN c.id AS c, f.values[i] AS v, f.value_jobs[i] AS n"""):
        values[var_of[r["c"]]][r["v"]] += r["n"]

    def short(c):
        return c.split(".", 1)[1]
    out = {}
    for v, cs in variables.items():
        tables = {col[c]["t"] for c in cs}
        lines = [f"### variable {v}", f"id: {v}",
                 f"{len(cs)} columns in {len(tables)} tables:"]
        lines += [f"- {short(c)} {col[c]['type'] or ''}".rstrip() for c in cs[:MAX_COLUMNS_SHOWN]]
        if len(cs) > MAX_COLUMNS_SHOWN:
            lines.append(f"- ... and {len(cs) - MAX_COLUMNS_SHOWN} more")
        top = joins[v].most_common(8)
        if top:
            lines.append("joined as: " + "; ".join(f"{short(a)} = {short(b)} ({n} queries)" for (a, b), n in top))
        if values[v]:
            lines.append("values queries filter on: " + ", ".join(repr(x) for x, _ in values[v].most_common(8)))
        out[v] = "\n".join(lines)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-names", action="store_true", help="build the variables, skip the LLM naming")
    a = ap.parse_args()
    cfg = config()
    G = Graph(cfg)
    t0 = time.time()
    G.run("CREATE CONSTRAINT variable_id IF NOT EXISTS FOR (n:Variable) REQUIRE n.id IS UNIQUE")
    G.auto("MATCH (v:Variable) CALL (v) { DETACH DELETE v } IN TRANSACTIONS OF 5000 ROWS")
    G.run("MATCH (c:Unjoined) REMOVE c:Unjoined")

    variables = components(G)
    G.batch("Variable", """UNWIND $rows AS r CREATE (v:Variable {id: r.id, size: size(r.cols)})
                           WITH v, r UNWIND r.cols AS cid MATCH (c:Column {id: cid}) CREATE (c)-[:IS]->(v)""",
            [{"id": v, "cols": cs} for v, cs in variables.items()], 500)
    G.run("""MATCH (v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(t:Table)
             WITH v, count(DISTINCT t) AS n SET v.tables = n""")
    unjoined = G.rows("MATCH (c:Column) WHERE NOT (c)-[:IS]->(:Variable) SET c:Unjoined RETURN count(c) AS n")[0]["n"]

    sizes = Counter(len(cs) for cs in variables.values())
    big = sorted(variables.items(), key=lambda x: -len(x[1]))[:5]
    print(f"variables: {len(variables):,} over {sum(len(c) for c in variables.values()):,} columns; "
          f"{unjoined:,} columns :Unjoined")
    print("  size distribution: " + ", ".join(f"{k} cols x{n}" for k, n in sorted(sizes.items())))
    print("  largest: " + "; ".join(f"{v.split('.')[-1]} ({len(cs)} cols)" for v, cs in big))

    if not a.no_names:
        llm = LLM(prompt("variable_system"), cfg)
        named = name_all(llm, evidence(G, variables), "variable", BATCH, cfg["llm"].get("concurrency", 6), SCHEMA,
                         lambda i: check_name(i, chars=(15, 400)))
        G.batch("Variable.name", """UNWIND $rows AS r MATCH (v:Variable {id: r.id})
            SET v.name = r.name, v.description = r.description, v.coherent = r.coherent, v.note = r.note,
                v.name_status = r.status, v.name_error = r.error, v.named_by = r.model""",
                [{"id": v, "name": d.get("name"), "description": d.get("description"), "coherent": d.get("coherent"),
                  "note": d.get("note") or None, "status": d["status"], "error": d.get("error"), "model": llm.model}
                 for v, d in named.items()])
        st = Counter(d["status"] for d in named.values())
        incoherent = [(v, d) for v, d in named.items() if d.get("coherent") is False]
        print(f"named: {dict(st)}; LLM {llm.model}: {llm.calls} calls, {llm.cached} cached, ${llm.cost():.2f}")
        for v, d in sorted(incoherent, key=lambda x: -len(variables[x[0]])):
            print(f"  not one thing ({len(variables[v])} cols) {d['name']}: {d['note']}")
    print(f"{time.time() - t0:.0f}s")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

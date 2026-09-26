"""Variables: one per set of columns the business joins to one another.

Clustering and naming happen over variables, so the same real-world thing counts once across the
warehouse.

  1. Judge every JoinKey (qlsc/joins.py): does the join say its two columns are the same thing, and
     how far can it be trusted? Stored on the JoinKey (confidence, identity, ...).
  2. GDS Cypher projection: each (a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column) becomes an undirected
     a -- b relationship, if k preserves identity and its confidence is one that builds variables
     (parameters.variables.joins). A suspect join stays in the graph as evidence and builds nothing.
  3. WCC over the projection: each component is one variable, materialized as (:Variable {id, size,
     tables}) with (:Column)-[:IS]->(:Variable). The id is 'var:' + the component's smallest column
     id, so it is stable across runs.
  4. The LLM names each variable (prompts/variable_system.md): name, description, and whether the
     columns look like one thing (coherent, note).
  5. Every column with no variable gets the label :Unjoined.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.joins import judge_joins
from qlsc.llm import LLM, check_name, name_all, prompt, write_names
from qlsc.names import short

PROJECTION = "variables"
BATCH = 20
SHOW_COLUMNS = 25
SCHEMA = {
    "type": "object",
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "description", "coherent", "note"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "coherent": {"type": "boolean"},
                    "note": {"type": "string"},
                },
            },
        }
    },
}


def components(G: Graph, usable: list[str]) -> dict[str, list[str]]:
    """WCC over columns joined by a trusted, identity-preserving JoinKey -> variable id -> column ids."""
    G.drop_projection(PROJECTION)
    p = G.rows(
        """MATCH (a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)
                  WHERE elementId(a) <= elementId(b) AND k.identity AND k.confidence IN $usable
                  WITH gds.graph.project($g, a, b, {}, {undirectedRelationshipTypes: ['*']}) AS g
                  RETURN g.nodeCount AS nodes, g.relationshipCount AS rels""",
        g=PROJECTION,
        usable=usable,
    )[0]
    comp = defaultdict(list)
    for r in G.rows(
        """CALL gds.wcc.stream($g, {concurrency: 1}) YIELD nodeId, componentId
                       RETURN gds.util.asNode(nodeId).id AS c, componentId AS k""",
        g=PROJECTION,
    ):
        comp[r["k"]].append(r["c"])
    G.drop_projection(PROJECTION)
    print(f"projection: {p['nodes']:,} columns, {p['rels']:,} join relationships -> {len(comp):,} components")
    return {f"var:{min(cs)}": sorted(cs) for cs in comp.values()}


def evidence(G: Graph, variables: dict[str, list[str]]) -> dict[str, str]:
    """What the namer sees for each variable: its columns, the joins that built it, values filtered on."""
    col = {
        r["c"]: r
        for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(:Variable)
                                        RETURN c.id AS c, t.id AS t, c.name AS name, c.type AS type""")
    }
    var_of = {c: v for v, cs in variables.items() for c in cs}
    joins = defaultdict(Counter)
    for r in G.rows("""MATCH (s:QueryShape)-[:USES_JOIN]->(k:JoinKey)-[:ON {side: 'left'}]->(a:Column),
                             (k)-[:ON {side: 'right'}]->(b:Column)
                       RETURN a.id AS a, b.id AS b, count(s) AS n"""):
        if r["a"] in var_of and var_of[r["a"]] == var_of.get(r["b"]):
            joins[var_of[r["a"]]][(r["a"], r["b"])] += r["n"]
    values = defaultdict(Counter)
    for r in G.rows("""MATCH (:QueryShape)-[f:FILTERS]->(c:Column)-[:IS]->(:Variable) WHERE size(f.values) > 0
                       UNWIND range(0, size(f.values) - 1) AS i
                       RETURN c.id AS c, f.values[i] AS v, f.value_jobs[i] AS n"""):
        values[var_of[r["c"]]][r["v"]] += r["n"]
    out = {}
    for v, cs in variables.items():
        lines = [
            f"### variable {v}",
            f"id: {v}",
            f"{len(cs)} columns in {len({col[c]['t'] for c in cs})} tables:",
        ]
        lines += [f"- {short(c)} {col[c]['type'] or ''}".rstrip() for c in cs[:SHOW_COLUMNS]]
        if len(cs) > SHOW_COLUMNS:
            lines.append(f"- ... and {len(cs) - SHOW_COLUMNS} more")
        top = joins[v].most_common(8)
        if top:
            lines.append(
                "joined as: " + "; ".join(f"{short(a)} = {short(b)} ({n} queries)" for (a, b), n in top)
            )
        if values[v]:
            lines.append(
                "values queries filter on: " + ", ".join(repr(x) for x, _ in values[v].most_common(8))
            )
        out[v] = "\n".join(lines)
    return out


def run(s: Settings, names: bool = True) -> None:
    t0 = time.time()
    with Graph(s) as G:
        G.run("CREATE CONSTRAINT variable_id IF NOT EXISTS FOR (n:Variable) REQUIRE n.id IS UNIQUE")
        G.delete("(n:Variable)")
        G.run("MATCH (c:Unjoined) REMOVE c:Unjoined")

        print(f"join confidence: {dict(judge_joins(G))}")
        for r in G.rows("""MATCH (k:JoinKey) WHERE k.confidence = 'suspect' OR NOT k.identity
                           RETURN k.id AS id, k.confidence AS c, k.identity AS i"""):
            key = " = ".join(short(x) for x in r["id"].split("="))
            print(f"  not used: {key} ({r['c']}{'' if r['i'] else ', not identity'})")
        variables = components(G, s.params["variables"]["joins"])
        G.batch(
            "Variable",
            """UNWIND $rows AS r CREATE (v:Variable {id: r.id, size: size(r.cols)})
                               WITH v, r UNWIND r.cols AS cid MATCH (c:Column {id: cid}) CREATE (c)-[:IS]->(v)""",
            [{"id": v, "cols": cs} for v, cs in variables.items()],
            500,
        )
        G.run("""MATCH (v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(t:Table)
                 WITH v, count(DISTINCT t) AS n SET v.tables = n""")
        unjoined = G.value("MATCH (c:Column) WHERE NOT (c)-[:IS]->(:Variable) SET c:Unjoined RETURN count(c)")

        sizes = Counter(len(cs) for cs in variables.values())
        largest = sorted(variables.items(), key=lambda x: -len(x[1]))[:5]
        print(
            f"variables: {len(variables):,} over {sum(len(c) for c in variables.values()):,} columns; "
            f"{unjoined:,} columns :Unjoined"
        )
        print("  size distribution: " + ", ".join(f"{k} cols x{n}" for k, n in sorted(sizes.items())))
        print("  largest: " + "; ".join(f"{v.split('.')[-1]} ({len(cs)} cols)" for v, cs in largest))

        if names:
            llm = LLM(prompt("variable_system", **s.business), s)
            named = name_all(
                llm,
                evidence(G, variables),
                ("variable", "variables"),
                BATCH,
                SCHEMA,
                lambda i: check_name(i, chars=(15, 400)),
            )
            write_names(G, "Variable", named, llm.model, extra=("coherent", "note"))
            print(f"named: {dict(Counter(d['status'] for d in named.values()))}; {llm.summary()}")
            for v, d in sorted(named.items(), key=lambda x: -len(variables[x[0]])):
                if d.get("coherent") is False:
                    print(f"  not one thing ({len(variables[v])} cols) {d['name']}: {d['note']}")
    print(f"{time.time() - t0:.0f}s")

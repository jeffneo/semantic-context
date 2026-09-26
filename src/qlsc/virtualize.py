"""Virtualize: a Neo4j Virtual Graph model of the warehouse's rows, written from the semantic layer.

Virtual Graph turns tables into node labels and pointing columns into relationship types, and runs Cypher
as SQL against the warehouse, copying nothing. It needs a model saying which is which; warehouses
rarely declare keys, so this stage writes the model from usage.

  scope          the tables to model: `virtualize.tables` in the config, else every table production
                 builds (written by a service account)
  nodes          a table is a node where a Variable's trusted joins converge on one of its columns (the
                 key everything else points at), or where production's MERGE key identifies its rows.
                 Date variables are properties, never nodes: they would connect everything to everything.
                 Every key is checked unique in the data before it is used.
  relationships  a column of one node table that holds the same Variable as another node's key points
                 at it. Variables are built only from trusted, identity-preserving joins, so a suspect
                 join (one production contradicts) never becomes a relationship; those are listed.
  names          the LLM names labels and types (prompts/virtual_model_*.md); unique, checked
  views          one view per node table in a dataset of its own (Virtual Graph reads one dataset)

Outputs, in <work>/virtual/: schema.json, datasource.json, secret.json (a path, never a secret),
views.sql and MODEL.md (the evidence for every node and relationship, and what was left out). On the
semantic layer: Table.graph_label, Column.graph_key (a node's key), Column.graph_relationship.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, prompt
from qlsc.names import short
from qlsc.warehouse import connect

SCALAR = {
    "STRING": "STRING",
    "INT64": "INTEGER",
    "FLOAT64": "FLOAT",
    "NUMERIC": "FLOAT",
    "BIGNUMERIC": "FLOAT",
    "BOOL": "BOOLEAN",
    "DATE": "DATE",
    "TIMESTAMP": "ZONED_DATE_TIME",
    "DATETIME": "LOCAL_DATE_TIME",
}
TIME_TYPES = {"DATE", "TIMESTAMP", "DATETIME"}
NAMES_SCHEMA = {
    "type": "object",
    "required": ["nodes", "relationships"],
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["table", "label"],
                "properties": {"table": {"type": "string"}, "label": {"type": "string"}},
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type"],
                "properties": {"id": {"type": "string"}, "type": {"type": "string"}},
            },
        },
    },
}

PRODUCTION_TABLES = """
MATCH (p:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape {succeeded: true})-[:WRITES]->(t:Table)
WHERE t.in_catalog AND t.kind = 'table'
RETURN DISTINCT t.id AS id
"""

# Per Variable, its columns in scope ranked by how many of its trusted joins touch them.
HOMES = """
MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table) WHERE t.id IN $scope
OPTIONAL MATCH (c)<-[:ON]-(k:JoinKey)-[:ON]->(o:Column)-[:IS]->(v)
WHERE o <> c AND k.identity AND k.confidence IN $joins
WITH v, t, c, count(DISTINCT k) AS degree, count(DISTINCT CASE WHEN k.production THEN k END) AS production
RETURN v.id AS variable, v.name AS variable_name, t.id AS table, c.name AS column, c.type AS type,
       degree, production
ORDER BY variable, degree DESC, production DESC, table
"""

MERGE_KEYS = """
MATCH (p:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape)-[w:WRITES]->(t:Table)
WHERE t.id IN $scope AND size(w.merge_keys) = 1
RETURN t.id AS table, w.merge_keys[0] AS column, count(*) AS writes
"""

POINTERS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable) WHERE t.id IN $tables
RETURN t.id AS table, c.name AS column, c.type AS type, v.id AS variable
"""

DIRECT = """
MATCH (ta:Table {id: $a})-[:HAS_COLUMN]->(x:Column {name: $ac})<-[:ON]-(k:JoinKey)-[:ON]->(y:Column {name: $bc})<-[:HAS_COLUMN]-(tb:Table {id: $b})
RETURN k.confidence AS confidence, k.people AS people, k.production AS production
"""

SUSPECT = """
MATCH (ta:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)<-[:HAS_COLUMN]-(tb:Table)
WHERE ta.id IN $scope AND tb.id IN $scope AND a.id < b.id AND (k.confidence = 'suspect' OR NOT k.identity)
RETURN ta.id AS a, a.name AS ac, tb.id AS b, b.name AS bc, k.confidence AS confidence, k.identity AS identity,
       k.confidence_reason AS why
"""

GROUPS = """
MATCH (t:Table)-[:HAS_COLUMN]->(:Column)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(g:Semantic {level: 1})
WHERE t.id IN $tables AND (u:Variable OR u:Unjoined)
WITH t, g, count(*) AS n ORDER BY n DESC
RETURN t.id AS table, collect(g.name)[0] AS area
"""

COLUMNS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.id IN $tables AND c.in_catalog
RETURN t.id AS table, collect({name: c.name, type: c.type}) AS columns
"""


def scope(G: Graph, s: Settings) -> list[str]:
    names = s.get("virtualize", {}).get("tables")
    ids = [r["id"] for r in G.rows(PRODUCTION_TABLES)]
    if names:
        ids = [
            r["id"]
            for r in G.rows("MATCH (t:Table) WHERE t.name IN $n AND t.in_catalog RETURN t.id AS id", n=names)
        ]
    return sorted(ids)


def nodes(G: Graph, tables: list[str], p: dict, wh) -> dict[str, dict]:
    """Table -> {key, why}: the column a Variable's trusted joins converge on, else a MERGE key.
    When usage cannot tell the sides apart (a dimension joined by one fact: one join, two columns),
    the side whose values are unique in the data is the key."""
    by_var = defaultdict(list)
    for r in G.rows(HOMES, scope=tables, joins=p["joins"]):
        by_var[r["variable"]].append(r)
    out: dict[str, dict] = {}
    for cols in by_var.values():
        top = cols[0]
        if top["type"] in TIME_TYPES or top["degree"] == 0:
            continue
        tied = [c for c in cols if c["degree"] == top["degree"]]
        if top["degree"] >= p["min_degree"] and len(tied) == 1:
            why = (
                f"{top['variable_name']}: {top['degree']} trusted joins converge on it"
                f" ({top['production']} run by production)"
            )
        else:
            unique = [c for c in tied if wh.is_unique(c["table"], [c["column"]])]
            if len(unique) != 1:
                continue
            top = unique[0]
            why = f"{top['variable_name']}: the unique side of its trusted join"
        if top["table"] not in out or out[top["table"]]["degree"] < top["degree"]:
            out[top["table"]] = {
                "key": top["column"],
                "variable": top["variable"],
                "degree": top["degree"],
                "why": why,
            }
    for r in G.rows(MERGE_KEYS, scope=tables):
        if r["table"] not in out:
            out[r["table"]] = {
                "key": r["column"],
                "variable": None,
                "degree": 0,
                "why": f"production's MERGE key ({r['writes']} writes)",
            }
    return out


def relationships(G: Graph, node: dict[str, dict]) -> list[dict]:
    """A column of a node table holding the Variable another node is keyed by points at that node."""
    home = {n["variable"]: t for t, n in node.items() if n["variable"]}
    rels = []
    for r in G.rows(POINTERS, tables=list(node)):
        end = home.get(r["variable"])
        if not end or end == r["table"] or r["column"] == node[r["table"]]["key"] or r["type"] in TIME_TYPES:
            continue
        direct = G.rows(DIRECT, a=r["table"], ac=r["column"], b=end, bc=node[end]["key"])
        if direct:
            d = max(direct, key=lambda x: (x["production"], x["people"] or 0))
            who = [
                w
                for w in (
                    "production" if d["production"] else "",
                    (f"{d['people']} people" if d["people"] > 1 else "1 person") if d["people"] else "",
                )
                if w
            ]
            why = f"joined directly ({d['confidence']}): by {' and '.join(who) or 'one person'}"
        else:
            why = "the same Variable, through other trusted joins"
        rels.append(
            {
                "id": f"{short(r['table'])}.{r['column']}",
                "start": r["table"],
                "column": r["column"],
                "end": end,
                "why": why,
            }
        )
    return sorted(rels, key=lambda x: x["id"])


def names(s: Settings, node: dict, rels: list[dict], areas: dict, var_names: dict) -> tuple[dict, dict]:
    """Labels and relationship types from the LLM, checked unique; table names as the fallback."""
    lines = [
        f"- {short(t)}: area '{areas.get(t) or '?'}', keyed by {n['key']}"
        + (f" ({var_names.get(n['variable'])})" if n["variable"] else "")
        for t, n in node.items()
    ]
    rel_lines = [f"- {r['id']}: {short(r['start'])} -> {short(r['end'])}" for r in rels]
    llm = LLM(prompt("virtual_model_system", **s.business), s)
    out = llm.call(
        prompt(
            "virtual_model_request",
            n_nodes=len(lines),
            nodes="\n".join(lines),
            n_rels=len(rel_lines),
            relationships="\n".join(rel_lines),
        ),
        NAMES_SCHEMA,
        "record_model",
    )
    by_table = {short(t): t for t in node}
    labels = {by_table.get(x.get("table"), x.get("table")): x.get("label") for x in out.get("nodes", [])}
    types = {x.get("id"): x.get("type") for x in out.get("relationships", [])}
    for t in node:  # fallback: the table name without its prefix, singular
        if (
            not re.fullmatch(r"[A-Z][A-Za-z0-9]{1,40}", labels.get(t) or "")
            or list(labels.values()).count(labels[t]) > 1
        ):
            base = re.sub(r"^(dim|fct|int|agg|stg)_", "", t.rsplit(".", 1)[1])
            labels[t] = "".join(w.capitalize() for w in re.sub(r"s$", "", base).split("_"))
    request = prompt(
        "virtual_model_request",
        n_nodes=len(lines),
        nodes="\n".join(lines),
        n_rels=len(rel_lines),
        relationships="\n".join(rel_lines),
    )
    for attempt in range(2):  # Virtual Graph needs every type unique: ask again for the ones that collide
        bad = type_problems(types, rels)
        if not bad or attempt:
            break
        retry = prompt(
            "virtual_model_retry",
            problems="\n".join(f"- {i}: {why}" for i, why in bad.items()),
            taken=", ".join(sorted(t for i, t in types.items() if i not in bad and t)),
        )
        again = llm.call(request + "\n\n" + retry, NAMES_SCHEMA, "record_model")
        types |= {x.get("id"): x.get("type") for x in again.get("relationships", []) if x.get("id") in bad}
    for i in type_problems(types, rels):  # last resort: the start label and the column
        r = next(r for r in rels if r["id"] == i)
        types[i] = f"{labels[r['start']].upper()}_{r['column'].upper()}"
    return labels, types


def type_problems(types: dict, rels: list[dict]) -> dict[str, str]:
    """Relationship ids whose type is missing, malformed, or used by another relationship."""
    out = {}
    for r in rels:
        ty = types.get(r["id"]) or ""
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,40}", ty):
            out[r["id"]] = f"{ty!r} is not UPPER_SNAKE_CASE"
        elif sum(1 for x in rels if types.get(x["id"]) == ty) > 1:
            out[r["id"]] = f"{ty} is also used by another relationship"
    return out


def schema_json(
    catalog: str,
    dataset: str,
    node: dict,
    rels: list[dict],
    labels: dict,
    types: dict,
    columns: dict,
    views: dict,
) -> dict:
    def props(t):
        return [
            {"name": c["name"], "column": c["name"], "type": SCALAR[c["type"]]}
            for c in columns[t]
            if c["type"] in SCALAR
        ]

    return {
        "catalog": catalog,
        "schema": dataset,
        "entities": {
            "nodes": [
                {"label": labels[t], "table": views[t], "properties": props(t), "key": [{"column": n["key"]}]}
                for t, n in node.items()
            ],
            "relationships": [
                {
                    "label": types[r["id"]],
                    "table": views[r["start"]],
                    "start": {
                        "targetEntity": labels[r["start"]],
                        "keys": [
                            {
                                "nodeColumn": node[r["start"]]["key"],
                                "relationshipColumn": node[r["start"]]["key"],
                            }
                        ],
                    },
                    "end": {
                        "targetEntity": labels[r["end"]],
                        "keys": [{"nodeColumn": node[r["end"]]["key"], "relationshipColumn": r["column"]}],
                    },
                    "properties": [],
                    "key": [{"column": node[r["start"]]["key"]}],
                }
                for r in rels
            ],
        },
    }


def render(
    node: dict,
    rels: list[dict],
    labels: dict,
    types: dict,
    dropped: list,
    excluded: list,
    not_nodes: list,
    dataset: str,
) -> str:
    L = [
        "# Virtual Graph model, written from usage",
        "",
        f"{len(node)} node labels and {len(rels)} relationship types over the views in `{dataset}`. Every node is "
        "keyed where the business's trusted joins converge (or by production's MERGE key), checked unique in the "
        "data; every relationship follows a Variable, which only trusted, identity-preserving joins build.",
        "",
        "## Nodes",
        "",
        "| label | table | key | why |",
        "|---|---|---|---|",
    ]
    L += [
        f"| {labels[t]} | {short(t)} | {n['key']} | {n['why']} |"
        for t, n in sorted(node.items(), key=lambda x: labels[x[0]])
    ]
    L += ["", "## Relationships", "", "| relationship | backed by | evidence |", "|---|---|---|"]
    L += [
        f"| (:{labels[r['start']]})-[:{types[r['id']]}]->(:{labels[r['end']]}) | {short(r['start'])}.{r['column']} | {r['why']} |"
        for r in rels
    ]
    L += ["", "## Left out", ""]
    L += [f"- **{short(t)}**: not a node, {why}" for t, why in not_nodes]
    L += [f"- **{short(t)}.{k}**: key not unique in the data" for t, k in dropped]
    L += [
        f"- `{short(x['a'])}.{x['ac']} = {short(x['b'])}.{x['bc']}`: "
        + (f"suspect, {x['why']}" if x["confidence"] == "suspect" else "does not preserve identity")
        for x in excluded
    ]
    return "\n".join(L) + "\n"


def run(s: Settings, create_views: bool = True) -> None:
    p, cfg = s.params["virtualize"], s.get("virtualize", {})
    dataset = cfg.get("dataset", "graph")
    wh = connect(s)
    out = s.work / "virtual"
    out.mkdir(exist_ok=True)
    with Graph(s) as G:
        tables = scope(G, s)
        node = nodes(G, tables, p, wh)
        dropped = []
        for t, n in list(node.items()):
            if not wh.is_unique(t, [n["key"]]):
                dropped.append((t, n.pop("key")))
                del node[t]
        rels = relationships(G, node)
        excluded = G.rows(SUSPECT, scope=tables)
        not_nodes = [
            (t, "no identifier the business joins on, and no MERGE key") for t in tables if t not in node
        ]
        areas = {r["table"]: r["area"] for r in G.rows(GROUPS, tables=list(node))}
        var_names = {
            r["id"]: r["name"] for r in G.rows("MATCH (v:Variable) RETURN v.id AS id, v.name AS name")
        }
        labels, types = names(s, node, rels, areas, var_names)
        columns = {r["table"]: r["columns"] for r in G.rows(COLUMNS, tables=list(node))}
        taken = defaultdict(int)
        for t in node:
            taken[t.rsplit(".", 1)[1]] += 1
        views = {
            t: t.rsplit(".", 1)[1]
            if taken[t.rsplit(".", 1)[1]] == 1
            else t.split(".", 1)[1].replace(".", "__")
            for t in node
        }
        view_sql = {
            views[t]: "SELECT "
            + ", ".join(f"`{c['name']}`" for c in columns[t] if c["type"] in SCALAR)
            + f" FROM `{t}`"
            for t in node
        }
        if create_views:
            wh.create_views(dataset, view_sql)
        datasource, secret = wh.virtual_graph(dataset)
        schema = schema_json(s["warehouse"]["project"], dataset, node, rels, labels, types, columns, views)
        (out / "schema.json").write_text(json.dumps(schema, indent=2))
        (out / "datasource.json").write_text(json.dumps(datasource, indent=2))
        (out / "secret.json").write_text(json.dumps(secret, indent=2))
        (out / "views.sql").write_text("\n\n".join(f"-- {v}\n{sql};" for v, sql in view_sql.items()) + "\n")
        (out / "MODEL.md").write_text(
            render(node, rels, labels, types, dropped, excluded, not_nodes, dataset)
        )
        G.run("MATCH (t:Table) REMOVE t.graph_label")
        G.run("MATCH (c:Column) REMOVE c.graph_relationship, c.graph_key")
        G.run(
            "UNWIND $rows AS c MATCH (x:Column {id: c}) SET x.graph_key = true",
            rows=[f"{t}.{n['key']}" for t, n in node.items()],
        )
        G.run(
            "UNWIND $rows AS r MATCH (t:Table {id: r.t}) SET t.graph_label = r.l",
            rows=[{"t": t, "l": labels[t]} for t in node],
        )
        G.run(
            "UNWIND $rows AS r MATCH (c:Column {id: r.c}) SET c.graph_relationship = r.ty",
            rows=[{"c": f"{r['start']}.{r['column']}", "ty": types[r["id"]]} for r in rels],
        )
    print(
        f"virtual graph: {len(node)} labels, {len(rels)} relationship types over {len(tables)} tables in scope; "
        f"{len(dropped)} keys not unique, {len(excluded)} joins left out -> {out}"
    )

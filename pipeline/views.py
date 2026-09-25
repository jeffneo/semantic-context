#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stage 7d: views of the semantic layer for Neo4j Enterprise Studio (Explore, i.e. Bloom).

Writes
  views/semantic-layer.perspective.json   import in Explore: Perspective drawer -> Import
  ../cypher/views.cypher                  the same views as plain Cypher, for Query or Browser

The perspective styles what a person exploring needs to see at a glance: tables coloured
by status (avoid red, caution amber, current green, from guide.py's labels), subjects and
domains as the map, variables and entities as the meaning, principals and teams as the
usage, findings as the evidence. Its search phrases are the questions people ask of a
semantic layer:

  Semantic map                        domains, subjects and the variables linking them
  Table <name>                        a table with its joins, sources, subject and alternatives
  Join <a> to <b>                     the shortest path over joins the business runs (no suspect keys)
  Lineage of <name>                   where a table's data comes from
  Who uses <name>                     principals and teams that consume it
  Traps                               tables to avoid and what to use instead
  Variable <name>                     one variable, its columns and tables
  Customer identity                   the entities and their id spaces
  Sensitive data                      where SSNs and tax ids are, raw or hashed
  Suspect joins                       joins production contradicts, with the columns involved
  Copies of <name>                    copy families
  Findings about <name>

Every search phrase is executed against the database with a sample parameter before the
file is written, so a phrase that returns nothing or fails is caught here, not in a demo.

Usage: uv run pipeline/views.py
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "views"

# (category name, labels, colour, size, caption property, properties to hide)
CATEGORIES = [
    ("Avoid", ["Avoid"], "#F16667", 1.0, "display_name"),
    ("Caution", ["Caution"], "#FFC454", 1.0, "display_name"),
    ("Table", ["Table"], "#8DCC93", 1.0, "display_name"),
    ("Subject", ["Subject"], "#4C8EDA", 2.0, "display_name"),
    ("Domain", ["Domain"], "#C990C0", 3.0, "id"),
    ("Variable", ["Variable"], "#57C7E3", 0.75, "display_name"),
    ("Entity", ["Entity"], "#F79767", 2.5, "name"),
    ("Column", ["Column"], "#D9C8AE", 0.5, "name"),
    ("Principal", ["Principal"], "#DA7194", 1.0, "id"),
    ("Team", ["Team"], "#ECB5C9", 2.0, "id"),
    ("Finding", ["Finding"], "#848484", 1.0, "title"),
    ("Dataset", ["Dataset"], "#D9D9D9", 1.5, "name"),
    ("JoinKey", ["JoinKey"], "#569480", 0.5, "confidence"),
]
HIDE = {"embedding", "mean", "write_days", "sample_sql", "week_jobs", "week_bytes", "evidence"}
REL_COLOR = {"USE_INSTEAD": "#F16667", "JOINS": "#569480", "DERIVED_FROM": "#4C8EDA", "LINKED": "#C990C0",
             "CONSUMES": "#DA7194", "ABOUT": "#848484", "IDENTIFIES": "#F79767", "LINKED_VIA": "#F79767",
             "COPY_OF": "#FFC454"}

TABLE_P = {"name": "$name", "dataType": "String", "suggestionLabel": "Table", "suggestionProp": "name"}
PHRASES = [
    ("Semantic map", [], """MATCH (d:Domain)-[c:CONTAINS]->(s:Subject)
OPTIONAL MATCH (s)-[l:LINKED]-(s2:Subject)
RETURN d, c, s, l, s2""", {}),
    ("Table $name", [TABLE_P], """MATCH (t:Table {name: $name})
OPTIONAL MATCH (t)-[j:JOINS]-(o:Table)
OPTIONAL MATCH (t)-[d:DERIVED_FROM]->(src:Table)
OPTIONAL MATCH (t)-[i:IN_SUBJECT]->(s:Subject)
OPTIONAL MATCH (t)-[u:USE_INSTEAD]->(alt:Table)
RETURN t, j, o, d, src, i, s, u, alt""", {"name": "fct_card_transactions"}),
    ("Join $a to $b", [{**TABLE_P, "name": "$a"}, {**TABLE_P, "name": "$b"}], """MATCH (a:Table {name: $a}), (b:Table {name: $b})
MATCH p = shortestPath((a)-[:JOINS*..6]-(b))
WHERE all(r IN relationships(p) WHERE NOT r.suspect)
RETURN p""", {"a": "fct_delinquency_daily", "b": "dim_branch"}),
    ("Lineage of $name", [TABLE_P], """MATCH p = (t:Table {name: $name})-[:DERIVED_FROM*1..6]->(:Table)
RETURN p""", {"name": "fct_contacts_all"}),
    ("Who uses $name", [TABLE_P], """MATCH (t:Table {name: $name})<-[c:CONSUMES]-(p:Principal)
OPTIONAL MATCH (p)-[m:MEMBER_OF]->(tm:Team)
RETURN t, c, p, m, tm""", {"name": "customer_360"}),
    ("Traps", [], """MATCH (t:Avoid)
WHERE coalesce(t.consumer_count, 0) > 0
OPTIONAL MATCH (t)-[u:USE_INSTEAD]->(alt:Table)
RETURN t, u, alt""", {}),
    ("Variable $v", [{"name": "$v", "dataType": "String", "suggestionLabel": "Variable", "suggestionProp": "display_name"}],
     """MATCH (v:Variable {display_name: $v})<-[i:IS]-(c:Column)<-[h:HAS_COLUMN]-(t:Table)
RETURN v, i, c, h, t""", {"v": "Customer Key"}),
    ("Customer identity", [], """MATCH (e:Entity)<-[i:IDENTIFIES]-(v:Variable)
OPTIONAL MATCH (v)-[l:LINKED_VIA]-(v2:Variable)
RETURN e, i, v, l, v2""", {}),
    ("Sensitive data", [], """MATCH (t:Table)-[h:HAS_COLUMN]->(c:Column) WHERE c.sensitive AND t.in_catalog
MATCH (t)-[d:IN_DATASET]->(ds:Dataset)
OPTIONAL MATCH (f:Finding)-[a:ABOUT]->(c)
RETURN t, h, c, d, ds, f, a""", {}),
    ("Suspect joins", [], """MATCH (f:Finding {kind: 'suspect_join'})-[a:ABOUT]->(c:Column)<-[h:HAS_COLUMN]-(t:Table)
RETURN f, a, c, h, t""", {}),
    ("Copies of $name", [TABLE_P], """MATCH (t:Table {name: $name})
MATCH p = (t)-[:COPY_OF*1..4]-(:Table)
RETURN p""", {"name": "customer_360"}),
    ("Findings about $name", [TABLE_P], """MATCH (t:Table {name: $name})
OPTIONAL MATCH (f:Finding)-[a:ABOUT]->(t)
OPTIONAL MATCH (g:Finding)-[b:ABOUT]->(c:Column)<-[h:HAS_COLUMN]-(t)
RETURN t, f, a, g, b, c, h""", {"name": "card_spend_by_segment"}),
]


def dtype(v) -> str:
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "bigint"
    if isinstance(v, float):
        return "number"
    if isinstance(v, list):
        return "array"
    return "string"


def main() -> int:
    G = Graph()
    now = int(time.time() * 1000)
    props = {}
    for lab in {l for c in CATEGORIES for l in c[1]}:
        seen = {}
        for r in G.rows(f"MATCH (n:{lab}) WITH n LIMIT 500 RETURN properties(n) AS p"):
            for k, v in r["p"].items():
                if v is not None and k not in seen:
                    seen[k] = dtype(v)
        props[lab] = seen
    cats = []
    for i, (name, labels, color, size, caption) in enumerate(CATEGORIES, start=1):
        ps = props.get(labels[0], {}) if labels[0] not in ("Avoid", "Caution") else props["Table"]
        cats.append({"id": i, "name": name, "labels": labels, "createdAt": now, "lastEditedAt": now,
                     "properties": [{"name": k, "exclude": k in HIDE, "dataType": t} for k, t in sorted(ps.items())],
                     "color": color, "size": size, "captionKeys": [caption]})
    labels = {lab: [{"propertyKey": k, "type": lab, "dataType": t} for k, t in sorted(ps.items())]
              for lab, ps in props.items()}
    rels = G.rows("""MATCH (a)-[r]->(b) WITH type(r) AS t, labels(a)[0] AS s, labels(b)[0] AS e, count(*) AS n
                     RETURN t, s, e, n""")
    rel_types = sorted({r["t"] for r in rels})
    rel_props = {}
    for t in rel_types:
        seen = {}
        for r in G.rows(f"MATCH ()-[r:{t}]->() WITH r LIMIT 200 RETURN properties(r) AS p"):
            for k, v in r["p"].items():
                if v is not None and k not in seen:
                    seen[k] = dtype(v)
        rel_props[t] = seen
    rtypes = [{"id": t, "name": t, "color": REL_COLOR.get(t, "#D9D9D9"), "size": 2 if t in ("USE_INSTEAD", "JOINS") else 1,
               "properties": [{"propertyKey": k, "type": t, "dataType": d} for k, d in sorted(rel_props[t].items())],
               "captionKeys": ["0_REL_TYPE_CAPTION_KEY"]} for t in rel_types]
    stats = {t: sum(r["n"] for r in rels if r["t"] == t) for t in rel_types}
    indexes = [{"label": r["l"][0], "type": "native", "propertyKeys": r["p"]}
               for r in G.rows("""SHOW INDEXES YIELD labelsOrTypes AS l, properties AS p, entityType AS e, type AS ty
                                  WHERE e = 'NODE' AND ty = 'RANGE' RETURN l, p""")]

    # every search phrase must run and return something before it ships
    templates, report = [], []
    for i, (text, params, cypher, sample) in enumerate(PHRASES):
        rows = G.rows(cypher, **sample)
        n = len(rows)
        report.append(f"{'ok ' if n else 'EMPTY'} {n:5} rows  {text}  {sample or ''}")
        templates.append({"name": text.split(" $")[0], "id": f"tmpl:{now + i}", "createdAt": now + i, "text": text,
                          "cypher": cypher, "isUpdateQuery": None, "hasCypherErrors": False,
                          "params": [{"name": p["name"], "dataType": p["dataType"], "collapsed": False,
                                      "suggestionLabel": p["suggestionLabel"], "suggestionProp": p["suggestionProp"],
                                      "suggestionBoolean": False, "cypher": None} for p in params]})
    persp = {"name": "Semantic layer (from the query log)", "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "qlsc/semantic-layer")),
             "categories": cats, "labels": labels, "relationshipTypes": rtypes,
             "palette": {"colors": ["#FFE081", "#C990C0", "#F79767", "#57C7E3", "#F16667", "#D9C8AE", "#8DCC93",
                                    "#ECB5C9", "#4C8EDA", "#FFC454", "#DA7194", "#569480", "#848484", "#D9D9D9"],
                         "currentIndex": len(cats) % 14},
             "createdAt": now, "lastEditedAt": now, "templates": templates, "sceneActions": [],
             "hiddenRelationshipTypes": [], "hiddenCategories": [], "hideUncategorisedData": False, "isAuto": False,
             "history": [], "parentPerspectiveId": None,
             "metadata": {"pathSegments": [{"source": r["s"], "relationshipType": r["t"], "target": r["e"]} for r in rels],
                          "indexes": indexes, "stats": {"labels": {}, "relationshipTypes": stats}},
             "version": "2.3.0"}
    OUT.mkdir(exist_ok=True)
    (OUT / "semantic-layer.perspective.json").write_text(json.dumps(persp, indent=1))
    lines = ["// Views of the semantic layer (database: semanticlayer). Generated by pipeline/views.py;",
             "// the same queries are the search phrases of views/semantic-layer.perspective.json.", ""]
    for text, params, cypher, sample in PHRASES:
        if sample:
            lines.append(":params " + json.dumps(sample))
        lines += [f"// {text}", cypher + ";", ""]
    (ROOT / "cypher" / "views.cypher").write_text("\n".join(lines))
    print("\n".join(report))
    print(f"-> {OUT / 'semantic-layer.perspective.json'} ({len(cats)} categories, {len(rtypes)} relationship types, "
          f"{len(templates)} search phrases); {ROOT / 'cypher' / 'views.cypher'}")
    G.close()
    return 0 if all(r.startswith("ok") for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())

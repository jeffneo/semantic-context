#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40", "rdflib-neo4j>=1.1"]
# ///
"""Stage 6: align designed models to the semantic layer the log produced - and diff them.

Designed models are inputs like the log, never its foundation (decision D1): a data catalog
export (designed/catalog.json) and an ontology (designed/ontology.ttl).

  ontology   imported as RDF with rdflib-neo4j (Neo4j Labs): every class is a
             (:Resource:Class {uri, label, definition}) and the hierarchy is its
             (:Class)-[:subClassOf]->(:Class), exactly as the triples say (vocabulary URIs
             shortened to local names). The classes are also labelled :Concept {source: 'ontology'}.
  catalog    each glossary term is a (:Concept {source: 'catalog'}).

Links, all (x)-[:MEANS {how, score, status}]->(:Concept):
  catalog    (:Column)-[:MEANS {how: 'catalog'}]  the catalog's own binding of a term to a column:
             exact, not a similarity. Through the column's Variable and Semantic group it places
             the term in the usage structure.
  embedding  (:Variable)-[:MEANS]->(catalog term) and (:Semantic)-[:MEANS]->(ontology class):
             the best match by embedding similarity (text-embedding-3-large, 512), above a floor,
             status 'proposed' for a person to confirm.
Catalog descriptions of tables and columns are properties (catalog_description, catalog_certified).

The diff (work/ALIGNMENT.md):
  agree        a variable's catalog-bound term is also its best match by embedding
  conflicts    the catalog binds one term to columns that production keeps apart (a suspect join
               connects their id spaces); one column bound to several terms (the catalog
               contradicts itself); or one variable's columns are bound to different terms
  designed, unused   terms bound to nothing or to columns nobody reads; certified tables nobody
                     queries; ontology classes nothing matches
  used, undesigned   used, stable semantic groups with no catalog term and no ontology class;
                     tables many principals query with no catalog description

Usage: uv run pipeline/align.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph, config, env
from llm import Embedder
from load_graph import canonical_table

HERE = Path(__file__).resolve().parent
DESIGNED = HERE.parent / "designed"
WORK = HERE / "work"
# Floors on the raw cosine of text-embedding-3-large, set where the matches turn wrong on
# inspection (Neo4j's vector.similarity.cosine reports (1 + cos) / 2; those values are in brackets):
# below 0.52 [0.76] a variable's best term is mostly wrong (Month Start Date -> an Avaya call id);
# the matches the catalog's own bindings confirm are 0.60 [0.80] and up. Below 0.40 [0.70] a group's
# best class is wrong (Salesforce record types -> Credit Bureau Report); above it mostly right, with
# word traps (Online Banking Alert Preferences -> Anti-Money Laundering Alert).
FLOOR_TERM = 0.52        # variable -> catalog term
FLOOR_CLASS = 0.40       # semantic group -> ontology class


def cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def load_catalog(G: Graph) -> tuple[list[dict], list[dict]]:
    cat = json.loads((DESIGNED / "catalog.json").read_text())
    wcat = json.loads((WORK / "catalog.json").read_text())

    def canon_col(fq):
        t, _, c = fq.rpartition(".")
        return f"{canonical_table(wcat, *t.split('.', 2))}.{c}"
    concepts = [{"id": f"catalog:{t['id']}", "source": "catalog", "name": t["name"], "definition": t["definition"],
                 "status": t.get("status")} for t in cat["glossary"]]
    bind = [{"c": canon_col(fq), "k": f"catalog:{t['id']}"} for t in cat["glossary"] for fq in t["columns"]]
    G.batch("Table.catalog", """UNWIND $rows AS r MATCH (t:Table {id: r.t})
        SET t.catalog_description = r.d, t.catalog_certified = r.cert""",
            [{"t": canonical_table(wcat, *a["table"].split(".", 2)), "d": a["description"], "cert": a["certified"]}
             for a in cat["assets"]])
    G.batch("Column.catalog", """UNWIND $rows AS r MATCH (c:Column {id: r.c}) SET c.catalog_description = r.d""",
            [{"c": canon_col(f"{a['table']}.{c}"), "d": d} for a in cat["assets"] for c, d in a["columns"].items()])
    return concepts, bind


def load_ontology(G: Graph, cfg: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """Import the ontology's triples with rdflib-neo4j, then mark its classes as Concepts."""
    from rdflib import Graph as RDFGraph
    from rdflib_neo4j import HANDLE_VOCAB_URI_STRATEGY, Neo4jStore, Neo4jStoreConfig
    n = cfg["neo4j"]
    store = Neo4jStoreConfig(auth_data={"uri": n["uri"], "database": n["database"], "user": n["user"],
                                        "pwd": env()["NEO4J_PASSWORD"]},
                             handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE, batching=True)
    rdf = RDFGraph(store=Neo4jStore(config=store))
    rdf.parse(DESIGNED / "ontology.ttl", format="ttl")
    rdf.close(True)
    G.run("""MATCH (c:Resource:Class)
             SET c:Concept, c.source = 'ontology', c.id = 'ontology:' + split(c.uri, '#')[-1],
                 c.name = coalesce(c.label, split(c.uri, '#')[-1]), c.status = 'approved'""")
    concepts = G.rows("""MATCH (c:Concept {source: 'ontology'})
                         RETURN c.id AS id, 'ontology' AS source, c.name AS name, coalesce(c.definition, '') AS definition""")
    broader = [(r["a"], r["b"]) for r in G.rows("""MATCH (a:Concept {source: 'ontology'})-[:subClassOf]->(b:Concept)
                                                   RETURN a.id AS a, b.id AS b""")]
    return concepts, broader


def main() -> int:
    cfg = config()
    G = Graph(cfg)
    emb = Embedder(cfg)
    G.run("CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE")
    G.run("MATCH (c:Concept) DETACH DELETE c")
    G.run("MATCH (r:Resource) DETACH DELETE r")            # the previous RDF import
    G.run("MATCH (t:Table) REMOVE t.catalog_description, t.catalog_certified")
    G.run("MATCH (c:Column) REMOVE c.catalog_description")

    cat_concepts, bind = load_catalog(G)
    onto_concepts, broader = load_ontology(G, cfg)
    concepts = cat_concepts + onto_concepts
    vecs = emb.embed([f"{c['name']}. {c['definition']}" for c in concepts])
    G.batch("Concept", """UNWIND $rows AS r CREATE (c:Concept) SET c = r""",
            [{**c, "embedding": v} for c, v in zip(concepts, vecs) if c["source"] == "catalog"])
    G.batch("Concept.embedding", """UNWIND $rows AS r MATCH (c:Concept {id: r.id}) SET c.embedding = r.e""",
            [{"id": c["id"], "e": v} for c, v in zip(concepts, vecs) if c["source"] == "ontology"])
    G.batch("MEANS catalog", """UNWIND $rows AS r MATCH (c:Column {id: r.c}), (k:Concept {id: r.k})
        CREATE (c)-[:MEANS {how: 'catalog', status: 'confirmed'}]->(k)""", bind)
    bound = G.rows("MATCH (:Column)-[m:MEANS {how: 'catalog'}]->() RETURN count(m) AS n")[0]["n"]
    print(f"catalog: {len(cat_concepts)} terms, {bound} of {len(bind)} bindings matched a column in the graph; "
          f"ontology (rdflib-neo4j): {len(onto_concepts)} classes, {len(broader)} subClassOf")

    # embed the variables (name, description, column names) to compare with the terms
    V = G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column) RETURN v.id AS id, v.name AS name, v.description AS d,
                  collect(DISTINCT c.name)[..12] AS cols""")
    vv = emb.embed([f"{v['name']}. {v['d'] or ''} Columns: {', '.join(v['cols'])}" for v in V])
    G.batch("Variable.embedding", "UNWIND $rows AS r MATCH (v:Variable {id: r.id}) SET v.embedding = r.e",
            [{"id": v["id"], "e": e} for v, e in zip(V, vv)])
    terms = [(c["id"], v) for c, v in zip(concepts, vecs) if c["source"] == "catalog"]
    classes = [(c["id"], v) for c, v in zip(concepts, vecs) if c["source"] == "ontology"]
    rows = []
    best_term = {}
    for v, e in zip(V, vv):
        k, s = max(((k, cos(e, t)) for k, t in terms), key=lambda x: x[1])
        best_term[v["id"]] = (k, s)
        if s >= FLOOR_TERM:
            rows.append({"x": v["id"], "k": k, "s": s})
    G.batch("MEANS variable", """UNWIND $rows AS r MATCH (v:Variable {id: r.x}), (k:Concept {id: r.k})
        CREATE (v)-[:MEANS {how: 'embedding', score: r.s, status: 'proposed'}]->(k)""", rows)
    S = G.rows("MATCH (s:Semantic) RETURN s.id AS id, s.level AS level, s.name AS name, s.embedding AS e")
    srows = []
    best_class = {}
    for s in S:
        k, sc = max(((k, cos(s["e"], c)) for k, c in classes), key=lambda x: x[1])
        best_class[s["id"]] = (k, sc)
        if sc >= FLOOR_CLASS:
            srows.append({"x": s["id"], "k": k, "s": sc})
    G.batch("MEANS semantic", """UNWIND $rows AS r MATCH (s:Semantic {id: r.x}), (k:Concept {id: r.k})
        CREATE (s)-[:MEANS {how: 'embedding', score: r.s, status: 'proposed'}]->(k)""", srows)
    print(f"proposed: {len(rows)} of {len(V)} variables -> a catalog term (floor {FLOOR_TERM}); "
          f"{len(srows)} of {len(S)} semantic groups -> an ontology class (floor {FLOOR_CLASS})")

    # ------------------------------------------------------------------ the diff
    name = {c["id"]: c["name"] for c in concepts}
    L = ["# Designed vs used: the catalog and the ontology against the semantic layer", "",
         "Designed inputs: `designed/catalog.json` (glossary and descriptions) and `designed/ontology.ttl`. "
         "Catalog bindings are exact; every embedding link is proposed, for a person to confirm.", ""]
    # agree: a variable's bound terms vs its best term by embedding
    vb = defaultdict(Counter)
    for r in G.rows("""MATCH (k:Concept)<-[:MEANS {how: 'catalog'}]-(:Column)-[:IS]->(v:Variable)
                       RETURN v.id AS v, k.id AS k, count(*) AS n"""):
        vb[r["v"]][r["k"]] += r["n"]
    agree = [v for v, c in vb.items() if best_term[v][0] in c]
    L += ["## Agreement", "",
          f"Of {len(vb)} variables with catalog-bound columns, the catalog's term is also the best match by "
          f"embedding for **{len(agree)}** ({len(agree) / max(len(vb), 1):.0%}).", ""]
    # conflicts 1: one term bound to columns that production keeps apart
    L += ["## Conflicts: the catalog equates what production keeps apart", ""]
    # compare id spaces: a bound column stands for its variable (or itself, if unjoined); a suspect
    # join between two of a term's id spaces means production keeps them apart
    unit = {r["c"]: r["v"] for r in G.rows("MATCH (c:Column)-[:IS]->(v:Variable) RETURN c.id AS c, v.id AS v")}
    u = lambda c: unit.get(c, c)
    sus = {}
    for r in G.rows("""MATCH (a:Column)<-[:ON]-(j:JoinKey {confidence: 'suspect'})-[:ON]->(b:Column) WHERE a.id < b.id
                       RETURN a.id AS a, b.id AS b, j.confidence_reason AS why"""):
        sus[frozenset((u(r["a"]), u(r["b"])))] = r
    term_units = defaultdict(set)
    for r in G.rows("MATCH (c:Column)-[:MEANS {how: 'catalog'}]->(k:Concept) RETURN k.id AS k, c.id AS c"):
        term_units[r["k"]].add(u(r["c"]))
    c1 = []
    for k, us in term_units.items():
        for pair, r in sus.items():
            if pair <= us:
                c1.append({"term": name[k], "a": r["a"], "b": r["b"], "why": r["why"]})
    L += [f"- **{r['term']}** is bound to both sides of `{r['a'].split('.', 1)[1]}` = `{r['b'].split('.', 1)[1]}`, but "
          f"that join is suspect: it {r['why']}." for r in c1] or ["- none"]
    # the catalog contradicting itself: one column bound to several terms
    multi = G.rows("""MATCH (c:Column)-[:MEANS {how: 'catalog'}]->(k:Concept)
                      WITH c, collect(k.name) AS terms WHERE size(terms) > 1
                      OPTIONAL MATCH (c)<-[:ON]-(j:JoinKey {confidence: 'suspect'})-[:ON]->(x:Column) WHERE x <> c
                      RETURN c.id AS c, terms, collect(x.id) AS suspect_with""")
    L += ["", "## Conflicts: the catalog contradicts itself", "",
          "Columns bound to more than one glossary term:", ""]
    L += [f"- `{r['c'].split('.', 1)[1]}`: " + " and ".join(f"**{t}**" for t in sorted(r["terms"]))
          + (f". Its join to `{'`, `'.join(x.split('.', 1)[1] for x in r['suspect_with'])}` is one production contradicts, "
             "which points to the binding that follows that join." if r["suspect_with"] else ".") for r in multi] or ["- none"]
    # conflicts 2: one variable, several terms
    c2 = [(v, c) for v, c in vb.items() if len(c) > 1]
    vname = {v["id"]: v["name"] for v in V}
    L += ["", "## Conflicts: usage unifies what the catalog splits", "",
          "Variables whose columns the business joins as one thing, bound to different glossary terms:", ""]
    L += [f"- **{vname[v]}**: " + "; ".join(f"{name[k]} ({n} columns)" for k, n in c.most_common()) for v, c in c2] or ["- none"]
    # designed, unused
    orphan = G.rows("""MATCH (k:Concept {source: 'catalog'}) WHERE NOT (k)<-[:MEANS {how: 'catalog'}]-()
                       RETURN k.name AS n ORDER BY n""")
    unread = G.rows("""MATCH (k:Concept {source: 'catalog'})<-[:MEANS {how: 'catalog'}]-(c:Column)
                       WITH k, collect(c) AS cols WHERE none(c IN cols WHERE (c)<-[:READS]-(:QueryShape))
                       RETURN k.name AS n ORDER BY n""")
    cert = G.rows("""MATCH (t:Table {catalog_certified: true}) WHERE NOT EXISTS {
                       MATCH (p:Principal)-[:RAN]->(s:QueryShape {succeeded: true})-[:REFERENCES]->(t) WHERE s.statement_type <> 'CREATE_VIEW' }
                     RETURN t.id AS t ORDER BY t""")
    matched = {k for k, _ in best_class.values() if _ >= FLOOR_CLASS}
    parent = defaultdict(set)
    for a, b in broader:
        parent[a].add(b)
    for k in list(matched):                  # a class is covered when any of its subclasses is
        stack = [k]
        while stack:
            for p_ in parent[stack.pop()]:
                if p_ not in matched:
                    matched.add(p_)
                    stack.append(p_)
    unmatched = sorted(name[k] for k, _ in classes if k not in matched)
    L += ["", "## Designed, not used", "",
          f"- Glossary terms bound to no column ({len(orphan)}): " + ", ".join(r["n"] for r in orphan),
          f"- Terms bound only to columns no query reads ({len(unread)}): " + ", ".join(r["n"] for r in unread),
          f"- Certified tables nothing queries ({len(cert)}): " + ", ".join(r["t"].split(".", 1)[1] for r in cert),
          f"- Ontology classes that neither a semantic group nor any of their subclasses match ({len(unmatched)}): "
          + ", ".join(unmatched)]
    # used, undesigned
    ud = G.rows("""MATCH (s:Semantic {level: 1}) WHERE s.stability >= 0.8
                   AND NOT EXISTS { (s)<-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)-[:MEANS {how: 'catalog'}]->() }
                   AND NOT (s)-[:MEANS]->()
                   RETURN s.name AS n ORDER BY n""")
    nodesc = G.rows("""MATCH (t:Table) WHERE t.in_catalog AND t.catalog_description IS NULL
                       MATCH (p:Principal)-[:RAN]->(:QueryShape {succeeded: true})-[:REFERENCES]->(t)
                       WITH t, count(DISTINCT p) AS n WHERE n >= 3 RETURN t.id AS t, n ORDER BY n DESC""")
    L += ["", "## Used, not designed", "",
          f"- Stable semantic groups with no catalog term and no ontology class ({len(ud)}): " + ", ".join(r["n"] for r in ud),
          f"- Tables 3+ principals query with no catalog description ({len(nodesc)}): "
          + ", ".join(f"{r['t'].split('.', 1)[1]} ({r['n']})" for r in nodesc[:25])]
    # the ontology's view of the top of the semantic layer
    L += ["", "## The semantic layer, read through the ontology", "", "| level | semantic group | ontology class | score |",
          "|---|---|---|---|"]
    for s in sorted(S, key=lambda x: (-x["level"], x["name"] or "")):
        if s["level"] >= 2:
            k, sc = best_class[s["id"]]
            L.append(f"| {s['level']} | {s['name']} | {name[k] if sc >= FLOOR_CLASS else '(none above floor)'} | {sc:.2f} |")
    (WORK / "ALIGNMENT.md").write_text("\n".join(L) + "\n")
    print(f"agree {len(agree)}/{len(vb)}; conflicts: {len(c1)} catalog-vs-production, {len(multi)} columns with several terms, "
          f"{len(c2)} split variables; "
          f"designed-unused: {len(orphan)} orphan terms, {len(unread)} unread, {len(cert)} certified unqueried, "
          f"{len(unmatched)} unmatched classes; used-undesigned: {len(ud)} groups, {len(nodesc)} tables -> {WORK / 'ALIGNMENT.md'}")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

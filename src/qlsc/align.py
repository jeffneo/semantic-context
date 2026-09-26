"""Align: link designed models to the semantic layer the log produced, and diff them.

Designed models are inputs like the log, never its foundation: a data-catalog export and an ontology
(config `designed.catalog`, `designed.ontology`).

  ontology   imported as RDF with rdflib-neo4j (Neo4j Labs): every class is a
             (:Resource:Class {uri, label, definition}) and the hierarchy is its
             (:Class)-[:subClassOf]->(:Class), exactly as the triples say (vocabulary URIs shortened
             to local names). The classes are also labelled :Concept {source: 'ontology'}.
  catalog    each glossary term is a (:Concept {source: 'catalog'}).

Links, all (x)-[:MEANS {how, score, status}]->(:Concept):
  catalog    (:Column)-[:MEANS {how: 'catalog'}]: the catalog's own binding of a term to a column,
             exact, not a similarity. Through the column's Variable and Semantic group it places the
             term in the usage structure.
  embedding  (:Variable)-[:MEANS]->(catalog term) and (:Semantic)-[:MEANS]->(ontology class): the best
             match by embedding similarity, above a floor (parameters.align), status 'proposed' for a
             person to confirm.
Catalog descriptions of tables and columns are properties (catalog_description, catalog_certified).

The diff (<work>/ALIGNMENT.md):
  agree              a variable's catalog-bound term is also its best match by embedding
  conflicts          the catalog binds one term to columns production keeps apart (a suspect join
                     connects their id spaces); one column bound to several terms (the catalog
                     contradicts itself); one variable's columns bound to different terms
  designed, unused   terms bound to nothing or to columns nobody reads; certified tables nobody
                     queries; ontology classes nothing matches
  used, undesigned   stable semantic groups with no catalog term and no ontology class; tables
                     several principals query with no catalog description
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from qlsc.config import Settings, secret
from qlsc.graph import Graph
from qlsc.llm import Embedder, cosine
from qlsc.names import canonical_column, canonical_table, short
from qlsc_parse.catalog import Catalog


def load_catalog(G: Graph, s: Settings, naming: Catalog) -> tuple[list[dict], list[dict]]:
    """The glossary as Concepts, its column bindings, and table and column descriptions as properties."""
    cat = json.loads(s.resolve(s["designed"]["catalog"]).read_text())
    concepts = [
        {
            "id": f"catalog:{t['id']}",
            "source": "catalog",
            "name": t["name"],
            "definition": t["definition"],
            "status": t.get("status"),
        }
        for t in cat["glossary"]
    ]
    bindings = [
        {"c": canonical_column(naming, fq), "k": f"catalog:{t['id']}"}
        for t in cat["glossary"]
        for fq in t["columns"]
    ]
    G.batch(
        "Table.catalog",
        """UNWIND $rows AS r MATCH (t:Table {id: r.t})
        SET t.catalog_description = r.d, t.catalog_certified = r.cert""",
        [
            {"t": canonical_table(naming, a["table"]), "d": a["description"], "cert": a["certified"]}
            for a in cat["assets"]
        ],
    )
    G.batch(
        "Column.catalog",
        "UNWIND $rows AS r MATCH (c:Column {id: r.c}) SET c.catalog_description = r.d",
        [
            {"c": canonical_column(naming, f"{a['table']}.{c}"), "d": d}
            for a in cat["assets"]
            for c, d in a["columns"].items()
        ],
    )
    return concepts, bindings


def load_ontology(G: Graph, s: Settings) -> tuple[list[dict], list[tuple[str, str]]]:
    """Import the ontology's triples with rdflib-neo4j, then mark its classes as Concepts."""
    from rdflib import Graph as RDFGraph
    from rdflib_neo4j import HANDLE_VOCAB_URI_STRATEGY, Neo4jStore, Neo4jStoreConfig

    n = s["neo4j"]
    store = Neo4jStoreConfig(
        auth_data={
            "uri": n["uri"],
            "database": n["database"],
            "user": n["user"],
            "pwd": secret("NEO4J_PASSWORD"),
        },
        handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
        batching=True,
    )
    rdf = RDFGraph(store=Neo4jStore(config=store))
    rdf.parse(s.resolve(s["designed"]["ontology"]), format="ttl")
    rdf.close(True)
    G.run("""MATCH (c:Resource:Class)
             SET c:Concept, c.source = 'ontology', c.id = 'ontology:' + split(c.uri, '#')[-1],
                 c.name = coalesce(c.label, split(c.uri, '#')[-1]), c.status = 'approved'""")
    concepts = G.rows("""MATCH (c:Concept {source: 'ontology'})
                         RETURN c.id AS id, 'ontology' AS source, c.name AS name, coalesce(c.definition, '') AS definition""")
    broader = [
        (r["a"], r["b"])
        for r in G.rows("""MATCH (a:Concept {source: 'ontology'})-[:subClassOf]->(b:Concept)
                                                   RETURN a.id AS a, b.id AS b""")
    ]
    return concepts, broader


def best(vec, candidates: list[tuple[str, list[float]]]) -> tuple[str, float]:
    return max(((k, cosine(vec, c)) for k, c in candidates), key=lambda x: x[1])


def covered(matched: set, broader: list[tuple[str, str]]) -> set:
    """Classes matched directly or through any of their subclasses."""
    parents = defaultdict(set)
    for a, b in broader:
        parents[a].add(b)
    out, stack = set(matched), list(matched)
    while stack:
        for p in parents[stack.pop()]:
            if p not in out:
                out.add(p)
                stack.append(p)
    return out


def diff(
    G: Graph,
    name: dict,
    best_term: dict,
    best_class: dict,
    classes: list,
    broader: list,
    semantics: list,
    floor_class: float,
) -> dict:
    """Where design and usage agree, conflict, and cover each other's gaps."""
    bound = defaultdict(Counter)  # variable -> the terms its columns are bound to
    for r in G.rows("""MATCH (k:Concept)<-[:MEANS {how: 'catalog'}]-(:Column)-[:IS]->(v:Variable)
                       RETURN v.id AS v, k.id AS k, count(*) AS n"""):
        bound[r["v"]][r["k"]] += r["n"]
    agree = [v for v, c in bound.items() if best_term[v][0] in c]

    # one term bound to both sides of a join production contradicts; a bound column stands for its
    # variable (or itself, if unjoined)
    unit = {
        r["c"]: r["v"] for r in G.rows("MATCH (c:Column)-[:IS]->(v:Variable) RETURN c.id AS c, v.id AS v")
    }
    u = lambda c: unit.get(c, c)
    suspect = {
        frozenset((u(r["a"]), u(r["b"]))): r
        for r in G.rows(
            """MATCH (a:Column)<-[:ON]-(j:JoinKey {confidence: 'suspect'})-[:ON]->(b:Column) WHERE a.id < b.id
           RETURN a.id AS a, b.id AS b, j.confidence_reason AS why"""
        )
    }
    term_units = defaultdict(set)
    for r in G.rows("MATCH (c:Column)-[:MEANS {how: 'catalog'}]->(k:Concept) RETURN k.id AS k, c.id AS c"):
        term_units[r["k"]].add(u(r["c"]))
    kept_apart = [
        {"term": name[k], "a": r["a"], "b": r["b"], "why": r["why"]}
        for k, units in term_units.items()
        for pair, r in suspect.items()
        if pair <= units
    ]

    unqueried = G.rows("""MATCH (t:Table {catalog_certified: true}) WHERE NOT EXISTS {
                              MATCH (:Principal)-[:RAN]->(s:QueryShape {succeeded: true})-[:REFERENCES]->(t)
                              WHERE s.statement_type <> 'CREATE_VIEW' }
                            RETURN t.id AS t ORDER BY t""")
    matched = covered({k for k, score in best_class.values() if score >= floor_class}, broader)
    return {
        "bound": len(bound),
        "agree": agree,
        "kept_apart": kept_apart,
        "several_terms": G.rows("""MATCH (c:Column)-[:MEANS {how: 'catalog'}]->(k:Concept)
                                   WITH c, collect(k.name) AS terms WHERE size(terms) > 1
                                   OPTIONAL MATCH (c)<-[:ON]-(:JoinKey {confidence: 'suspect'})-[:ON]->(x:Column) WHERE x <> c
                                   RETURN c.id AS c, terms, collect(x.id) AS suspect_with"""),
        "split": [(v, c) for v, c in bound.items() if len(c) > 1],
        "orphan": [
            r["n"]
            for r in G.rows("""MATCH (k:Concept {source: 'catalog'}) WHERE NOT (k)<-[:MEANS {how: 'catalog'}]-()
                                             RETURN k.name AS n ORDER BY n""")
        ],
        "unread": [
            r["n"]
            for r in G.rows("""MATCH (k:Concept {source: 'catalog'})<-[:MEANS {how: 'catalog'}]-(c:Column)
                                             WITH k, collect(c) AS cols WHERE none(c IN cols WHERE (c)<-[:READS]-(:QueryShape))
                                             RETURN k.name AS n ORDER BY n""")
        ],
        "certified_unqueried": [r["t"] for r in unqueried],
        "unmatched_classes": sorted(name[k] for k, _ in classes if k not in matched),
        "undesigned_groups": [
            r["n"]
            for r in G.rows("""MATCH (s:Semantic {level: 1}) WHERE s.stability >= 0.8
            AND NOT EXISTS { (s)<-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)-[:MEANS {how: 'catalog'}]->() }
            AND NOT (s)-[:MEANS]->()
            RETURN s.name AS n ORDER BY n""")
        ],
        "undescribed_tables": G.rows("""MATCH (t:Table) WHERE t.in_catalog AND t.catalog_description IS NULL
                                        MATCH (p:Principal)-[:RAN]->(:QueryShape {succeeded: true})-[:REFERENCES]->(t)
                                        WITH t, count(DISTINCT p) AS n WHERE n >= 3 RETURN t.id AS t, n ORDER BY n DESC"""),
        "top": [(x["level"], x["name"], *best_class[x["id"]]) for x in semantics if x["level"] >= 2],
    }


def render(d: dict, name: dict, vname: dict, floor_class: float) -> str:
    L = [
        "# Designed vs used: the catalog and the ontology against the semantic layer",
        "",
        "Catalog bindings are exact; every embedding link is proposed, for a person to confirm.",
        "",
        "## Agreement",
        "",
        f"Of {d['bound']} variables with catalog-bound columns, the catalog's term is also the best match by "
        f"embedding for **{len(d['agree'])}** ({len(d['agree']) / max(d['bound'], 1):.0%}).",
        "",
        "## Conflicts: the catalog equates what production keeps apart",
        "",
    ]
    L += [
        f"- **{r['term']}** is bound to both sides of `{short(r['a'])}` = `{short(r['b'])}`, but "
        f"that join is suspect: it {r['why']}."
        for r in d["kept_apart"]
    ] or ["- none"]
    L += [
        "",
        "## Conflicts: the catalog contradicts itself",
        "",
        "Columns bound to more than one glossary term:",
        "",
    ]
    L += [
        f"- `{short(r['c'])}`: "
        + " and ".join(f"**{t}**" for t in sorted(r["terms"]))
        + (
            f". Its join to `{'`, `'.join(short(x) for x in r['suspect_with'])}` is one production contradicts, "
            "which points to the binding that follows that join."
            if r["suspect_with"]
            else "."
        )
        for r in d["several_terms"]
    ] or ["- none"]
    L += [
        "",
        "## Conflicts: usage unifies what the catalog splits",
        "",
        "Variables whose columns the business joins as one thing, bound to different glossary terms:",
        "",
    ]
    L += [
        f"- **{vname[v]}**: " + "; ".join(f"{name[k]} ({n} columns)" for k, n in c.most_common())
        for v, c in d["split"]
    ] or ["- none"]
    L += [
        "",
        "## Designed, not used",
        "",
        f"- Glossary terms bound to no column ({len(d['orphan'])}): " + ", ".join(d["orphan"]),
        f"- Terms bound only to columns no query reads ({len(d['unread'])}): " + ", ".join(d["unread"]),
        f"- Certified tables nothing queries ({len(d['certified_unqueried'])}): "
        + ", ".join(short(t) for t in d["certified_unqueried"]),
        f"- Ontology classes that neither a semantic group nor any of their subclasses match "
        f"({len(d['unmatched_classes'])}): " + ", ".join(d["unmatched_classes"]),
        "",
        "## Used, not designed",
        "",
        f"- Stable semantic groups with no catalog term and no ontology class ({len(d['undesigned_groups'])}): "
        + ", ".join(d["undesigned_groups"]),
        f"- Tables 3+ principals query with no catalog description ({len(d['undescribed_tables'])}): "
        + ", ".join(f"{short(r['t'])} ({r['n']})" for r in d["undescribed_tables"][:25]),
        "",
        "## The semantic layer, read through the ontology",
        "",
        "| level | semantic group | ontology class | score |",
        "|---|---|---|---|",
    ]
    for level, group, k, score in sorted(d["top"], key=lambda x: (-x[0], x[1] or "")):
        L.append(
            f"| {level} | {group} | {name[k] if score >= floor_class else '(none above floor)'} | {score:.2f} |"
        )
    return "\n".join(L) + "\n"


def run(s: Settings) -> None:
    p = s.params["align"]
    emb = Embedder(s)
    naming = Catalog(json.loads((s.work / "catalog.json").read_text()))
    with Graph(s) as G:
        G.run("CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE")
        G.run("MATCH (c:Concept) DETACH DELETE c")
        G.run("MATCH (r:Resource) DETACH DELETE r")  # the previous RDF import
        G.run("MATCH (t:Table) REMOVE t.catalog_description, t.catalog_certified")
        G.run("MATCH (c:Column) REMOVE c.catalog_description")

        terms_, bindings = load_catalog(G, s, naming)
        classes_, broader = load_ontology(G, s)
        concepts = terms_ + classes_
        vecs = emb.embed([f"{c['name']}. {c['definition']}" for c in concepts])
        G.batch(
            "Concept",
            "UNWIND $rows AS r CREATE (c:Concept) SET c = r",
            [{**c, "embedding": v} for c, v in zip(concepts, vecs) if c["source"] == "catalog"],
        )
        G.batch(
            "Concept.embedding",
            "UNWIND $rows AS r MATCH (c:Concept {id: r.id}) SET c.embedding = r.e",
            [{"id": c["id"], "e": v} for c, v in zip(concepts, vecs) if c["source"] == "ontology"],
        )
        G.batch(
            "MEANS catalog",
            """UNWIND $rows AS r MATCH (c:Column {id: r.c}), (k:Concept {id: r.k})
            CREATE (c)-[:MEANS {how: 'catalog', status: 'confirmed'}]->(k)""",
            bindings,
        )
        matched = G.value("MATCH (:Column)-[m:MEANS {how: 'catalog'}]->() RETURN count(m)")
        print(
            f"catalog: {len(terms_)} terms, {matched} of {len(bindings)} bindings matched a column in the graph; "
            f"ontology (rdflib-neo4j): {len(classes_)} classes, {len(broader)} subClassOf"
        )

        # embed the variables (name, description, column names) to compare with the terms
        variables = G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column) RETURN v.id AS id, v.name AS name,
                              v.description AS d, collect(DISTINCT c.name)[..12] AS cols""")
        vvecs = emb.embed([f"{v['name']}. {v['d'] or ''} Columns: {', '.join(v['cols'])}" for v in variables])
        G.batch(
            "Variable.embedding",
            "UNWIND $rows AS r MATCH (v:Variable {id: r.id}) SET v.embedding = r.e",
            [{"id": v["id"], "e": e} for v, e in zip(variables, vvecs)],
        )
        terms = [(c["id"], v) for c, v in zip(concepts, vecs) if c["source"] == "catalog"]
        classes = [(c["id"], v) for c, v in zip(concepts, vecs) if c["source"] == "ontology"]
        best_term = {v["id"]: best(e, terms) for v, e in zip(variables, vvecs)}
        semantics = G.rows(
            "MATCH (s:Semantic) RETURN s.id AS id, s.level AS level, s.name AS name, s.embedding AS e"
        )
        best_class = {x["id"]: best(x["e"], classes) for x in semantics}
        proposed = {
            "variable": [
                {"x": x, "k": k, "s": sc} for x, (k, sc) in best_term.items() if sc >= p["floor_term"]
            ],
            "semantic": [
                {"x": x, "k": k, "s": sc} for x, (k, sc) in best_class.items() if sc >= p["floor_class"]
            ],
        }
        for label, rows in (("Variable", proposed["variable"]), ("Semantic", proposed["semantic"])):
            G.batch(
                f"MEANS {label.lower()}",
                f"""UNWIND $rows AS r MATCH (x:{label} {{id: r.x}}), (k:Concept {{id: r.k}})
                CREATE (x)-[:MEANS {{how: 'embedding', score: r.s, status: 'proposed'}}]->(k)""",
                rows,
            )
        print(
            f"proposed: {len(proposed['variable'])} of {len(variables)} variables -> a catalog term "
            f"(floor {p['floor_term']}); {len(proposed['semantic'])} of {len(semantics)} semantic groups -> "
            f"an ontology class (floor {p['floor_class']})"
        )

        name = {c["id"]: c["name"] for c in concepts}
        d = diff(G, name, best_term, best_class, classes, broader, semantics, p["floor_class"])
    (s.work / "ALIGNMENT.md").write_text(
        render(d, name, {v["id"]: v["name"] for v in variables}, p["floor_class"])
    )
    print(
        f"agree {len(d['agree'])}/{d['bound']}; conflicts: {len(d['kept_apart'])} catalog-vs-production, "
        f"{len(d['several_terms'])} columns with several terms, {len(d['split'])} split variables; "
        f"designed-unused: {len(d['orphan'])} orphan terms, {len(d['unread'])} unread, "
        f"{len(d['certified_unqueried'])} certified unqueried, {len(d['unmatched_classes'])} unmatched classes; "
        f"used-undesigned: {len(d['undesigned_groups'])} groups, {len(d['undescribed_tables'])} tables "
        f"-> {s.work / 'ALIGNMENT.md'}"
    )

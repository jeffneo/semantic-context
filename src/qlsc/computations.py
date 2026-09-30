"""Computations: what the business computes from its columns, found in the queries it runs.

Every successful query shape is read by the parser's computation extractor (qlsc_parse/computations.py),
which finds, in each scope over physical tables, three kinds, written over base columns:
  measure     an aggregate: SUM(fct_card_transactions.amount), with the scope's non-period filters
  dimension   a derived grouping: DATE_TRUNC(fct_calls.conversation_date, WEEK(MONDAY)), a CASE bucket
  population  the scope's non-period filters together: segment IN ('affluent', 'private') AND ...
The same kind, expression, filters and tables in two queries is one Computation. The LLM names each
(prompts/computation_system.md) from its expression and the names queries give it (their aliases), and
the name and description are embedded for navigation.

  (:QueryShape)-[:COMPUTES]->(:Computation)-[:READS]->(:Column)
  Computation {id, kind, expression, filters, grain, tables, aliases, shapes, jobs, production,
               trusted, name, description, embedding}

Computations that are the same thing written differently (near by embedding, confirmed by the LLM)
keep their most-run member; the others carry `same_as`, its id.

`production`: a service account runs a query that computes it. `trusted`: none of its tables is a
sandbox (only people write it) or frozen (navigate's tests). `health_check`: every query computing it
returns one ungrouped row of aggregates, as data-quality checks do (a row count, the newest load). Computations that are not the same text
but mean the same thing stay separate for now.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict

from qlsc import navigate
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, name_all, prompt, write_names
from qlsc.names import short
from qlsc_parse.catalog import Catalog
from qlsc_parse.computations import computations

SHAPES = """
MATCH (s:QueryShape {succeeded: true}) WHERE s.sample_sql IS NOT NULL
OPTIONAL MATCH (p:Principal)-[r:RAN]->(s)
WITH s, sum(r.jobs) AS jobs, 'service_account' IN collect(p.kind) AS production
OPTIONAL MATCH (s)-[:REFERENCES]->(t:Table)
RETURN s.id AS id, s.sample_sql AS sql, jobs, production, collect(t.id) AS tables
ORDER BY id
"""


def extract(G: Graph, s: Settings) -> dict[str, dict]:
    """id -> Computation, over every successful shape. A filter on a column the shape was run with
    different values for (a parameter: the site, the month, the customer asked about) is the question's,
    not the definition's, and is dropped."""
    catalog = Catalog(json.loads((s.work / "catalog.json").read_text()))
    params = {r["s"]: set(r["cols"]) for r in G.rows(PARAMETERS)}
    found: dict[str, dict] = {}
    aliases: dict[str, Counter] = defaultdict(Counter)
    grains: dict[str, Counter] = defaultdict(Counter)
    shapes = G.rows(SHAPES)
    for i, x in enumerate(shapes, 1):
        project = x["tables"][0].split(".")[0] if x["tables"] else None
        seen = set()
        for c in computations(x["sql"], catalog, project):
            keep = [
                i for i, cols in enumerate(c["filter_columns"]) if not set(cols) & params.get(x["id"], set())
            ]
            c["filters"] = [c["filters"][i] for i in keep]
            if c["kind"] == "population":
                if not keep:
                    continue
                c["columns"] = sorted({col for i in keep for col in c["filter_columns"][i]})
                c["tables"] = sorted({col.rsplit(".", 1)[0] for col in c["columns"]})
                c["expression"] = " AND ".join(c["filters"])
                c["filters"] = []
            key = json.dumps([c["kind"], c["expression"], c["filters"], c["tables"]])
            cid = hashlib.sha256(key.encode()).hexdigest()[:16]
            comp = found.setdefault(
                cid,
                {
                    "id": cid,
                    **{k: c[k] for k in ("kind", "expression", "filters", "tables", "columns")},
                    "shapes": set(),
                    "jobs": 0,
                    "production": False,
                },
            )
            if c["alias"]:
                aliases[cid][c["alias"]] += x["jobs"] or 1
            if c["grain"]:
                grains[cid][json.dumps(c["grain"])] += 1
            if cid not in seen:
                comp["shapes"].add(x["id"])
                comp["jobs"] += x["jobs"] or 0
                comp["production"] |= bool(x["production"])
                seen.add(cid)
        if i % 400 == 0:
            print(f"  {i}/{len(shapes)} shapes read, {len(found)} computations", flush=True)
    for cid, c in found.items():
        c["aliases"] = [a for a, _ in aliases[cid].most_common(5)]
        c["grain"] = json.loads(grains[cid].most_common(1)[0][0]) if grains[cid] else []
        c["shapes"] = sorted(c["shapes"])
    return found


PARAMETERS = """
MATCH (s:QueryShape)-[f:FILTERS]->(c:Column) WHERE size(coalesce(f.values, [])) > 1
RETURN s.id AS s, collect(DISTINCT c.id) AS cols
"""

# Candidates to merge: business Computations of one kind, over the same tables, whose embeddings are
# nearly the same. Over different tables they aren't the same computation (a copy, a stale score).
NEAR = """
MATCH (c:Computation) WHERE NOT c.health_check AND c.embedding IS NOT NULL
CALL db.index.vector.queryNodes('computation_embedding', $k, c.embedding) YIELD node AS d, score
WITH c, d, score WHERE d.id > c.id AND d.kind = c.kind AND d.tables = c.tables AND NOT d.health_check
  AND score >= $min
RETURN c.id AS a, d.id AS b
"""

MERGE_SCHEMA = {
    "type": "object",
    "required": ["sets"],
    "properties": {
        "sets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["set", "same"],
                "properties": {
                    "set": {"type": "string"},
                    "same": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                },
            },
        }
    },
}


def components(pairs: list[tuple[str, str]]) -> list[list[str]]:
    parent: dict[str, str] = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups = defaultdict(list)
    for x in parent:
        groups[find(x)].append(x)
    return sorted(sorted(g) for g in groups.values() if len(g) > 1)


def merge(G: Graph, s: Settings, rows: dict[str, dict], named: dict[str, dict]) -> int:
    """Computations that compute the same thing, written differently: near neighbours by embedding,
    confirmed by the LLM (prompts/computation_merge_system.md). Each confirmed set keeps its most-run
    member; the others point at it (`same_as`) and navigation skips them."""
    p = s["computations"]
    sets = components(
        [(r["a"], r["b"]) for r in G.rows(NEAR, k=p["merge_neighbours"], min=p["merge_similarity"])]
    )
    llm = LLM(prompt("computation_merge_system", **s.business), s)
    show = lambda cid: (
        f"  {cid}: {named.get(cid, {}).get('name', '')} = {evidence(rows[cid]).splitlines()[2]}"
        + (f" with {' AND '.join(rows[cid]['filters'])}" if rows[cid]["filters"] else "")
        + f" on {', '.join(short(t) for t in rows[cid]['tables'])}"
    )
    batches = [sets[i : i + p["merge_batch"]] for i in range(0, len(sets), p["merge_batch"])]
    same_as = {}
    for b in batches:
        text = "\n\n".join(f"set {i}:\n" + "\n".join(show(c) for c in g) for i, g in enumerate(b))
        out = llm.call(prompt("computation_merge", n=len(b), sets=text), MERGE_SCHEMA, 4000)
        for item in out.get("sets", []):
            for group in item.get("same", []):
                group = [c for c in group if c in rows]
                if len(group) > 1:
                    keep = max(group, key=lambda c: (rows[c]["jobs"], c))
                    same_as.update({c: keep for c in group if c != keep})
    G.run("MATCH (c:Computation) REMOVE c.same_as")
    G.batch(
        "Computation.same_as",
        "UNWIND $rows AS r MATCH (c:Computation {id: r.id}) SET c.same_as = r.keep",
        [{"id": c, "keep": k} for c, k in sorted(same_as.items())],
    )
    print(
        f"merged: {len(sets)} candidate sets, {len(same_as)} computations point at another ({llm.calls} LLM calls)"
    )
    return len(same_as)


def evidence(c: dict) -> str:
    lines = [f"id: {c['id']}", f"kind: {c['kind']}", f"expression: {c['expression']}"]
    if c["filters"]:
        lines.append("with the filters: " + " AND ".join(c["filters"]))
    if c["grain"]:
        lines.append("grouped by: " + ", ".join(c["grain"]))
    lines.append("tables: " + ", ".join(short(t) for t in c["tables"]))
    if c["aliases"]:
        lines.append("queries call it: " + ", ".join(c["aliases"]))
    who = "production and people" if c["production"] else "people only"
    lines.append(f"computed by {len(c['shapes'])} queries ({c['jobs']:,} runs), {who}")
    return "\n".join(lines)


def run(s: Settings, names: bool = True) -> None:
    p = s["computations"]
    t0 = time.time()
    with Graph(s) as G:
        G.run("CREATE CONSTRAINT computation_id IF NOT EXISTS FOR (n:Computation) REQUIRE n.id IS UNIQUE")
        G.delete("(n:Computation)")
        found = extract(G, s)
        distrusted = {r["t"] for r in G.rows(navigate.DISTRUSTED)}
        rows = [
            {**c, "trusted": not set(c["tables"]) & distrusted, "shape_count": len(c["shapes"])}
            for c in sorted(found.values(), key=lambda c: c["id"])
        ]
        G.batch(
            "Computation",
            """UNWIND $rows AS r CREATE (c:Computation {id: r.id})
               SET c += r {.kind, .expression, .filters, .tables, .aliases, .jobs, .production, .trusted},
                   c.grain = r.grain, c.shapes = r.shape_count
               WITH c, r UNWIND r.shapes AS sid MATCH (s:QueryShape {id: sid}) CREATE (s)-[:COMPUTES]->(c)""",
            rows,
            500,
        )
        G.batch(
            "Computation.READS",
            """UNWIND $rows AS r MATCH (c:Computation {id: r.id})
               UNWIND r.columns AS col MATCH (k:Column {id: col}) CREATE (c)-[:READS]->(k)""",
            [{"id": r["id"], "columns": r["columns"]} for r in rows],
            500,
        )
        # A health check returns one ungrouped row of aggregates (a row count, a null count, the newest
        # load time): what it computes is about the data's state, not the business.
        G.run("""MATCH (c:Computation)
                 SET c.health_check = all(q IN [(s:QueryShape)-[:COMPUTES]->(c) | s]
                                          WHERE coalesce(q.output_aggregate_only, false)
                                            AND NOT coalesce(q.output_grouped, false))""")
        kinds = Counter(r["kind"] for r in rows)
        print(f"{len(rows)} computations: {dict(kinds)}; {sum(r['trusted'] for r in rows)} trusted")
        if not names:
            return
        llm = LLM(prompt("computation_system", **s.business), s)
        named = name_all(
            llm, {r["id"]: evidence(r) for r in rows}, ("computation", "computations"), p["batch"]
        )
        write_names(G, "Computation", named, llm.model)
        emb = Embedder(s)
        text = lambda r, n: (
            f"{n.get('name', '')}: {n.get('description', '')} ({r['kind']}: {r['expression']})"
        )
        vecs = emb.embed([text(r, named.get(r["id"], {})) for r in rows])
        G.batch(
            "Computation.embedding",
            "UNWIND $rows AS r MATCH (c:Computation {id: r.id}) SET c.embedding = r.e",
            [{"id": r["id"], "e": v} for r, v in zip(rows, vecs)],
            500,
        )
        G.run(f"""CREATE VECTOR INDEX computation_embedding IF NOT EXISTS FOR (c:Computation) ON c.embedding
                  OPTIONS {{indexConfig: {{`vector.dimensions`: {s["embeddings"]["dimensions"]},
                                           `vector.similarity_function`: 'cosine'}}}}""")
        merge(G, s, {r["id"]: r for r in rows}, named)
        failed = sum(1 for n in named.values() if n["status"] == "failed")
        print(
            f"named {len(named)} ({failed} failed); {llm.calls} LLM calls ({llm.cached} cached), "
            f"${llm.cost():.2f}; {time.time() - t0:.0f}s"
        )

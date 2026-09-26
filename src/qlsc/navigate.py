"""Navigate: from a question in plain English down to the data assets that answer it (graph RAG).

  1. Embed the question with the model the Semantic nodes were embedded with.
  2. Vector search the semantic layer (any level) for the closest Semantic nodes.
  3. Walk down IN_SEMANTIC from those hits to the level-1 groups beneath them, add the level-1 groups
     closest to the question directly, and keep the closest of all: the hits say where to look, the
     groups narrow it. The direct search guards against a group filed under the wrong parent.
  4. Down again to the physical layer: the tables whose own columns are in those groups. Ranked round
     robin: each group, closest to the question first, contributes its most-used table (by principals
     querying those columns) in turn, so every relevant group is represented and a hub table from a
     nearby group cannot crowd out the core table of the closest one. Frozen tables (nothing wrote
     them in the log window and no production process reads them) go last. Variables are the links
     between tables, so a table reached only through a shared variable is not part of the cohort.
  5. The log's evidence for that cohort: the joins between those tables, and the queries that already
     read them together, with who ran them.
  6. The SQL: the LLM writes one query from that cohort (prompts/sql_*.md) and the warehouse dry-runs
     it - valid or not, and how many bytes it would scan - at no cost. A failed dry run goes back to
     the LLM once.

Everything is deterministic but the SQL: the same question gives the same cohort.
"""

from __future__ import annotations

import textwrap

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, prompt
from qlsc.names import short
from qlsc.warehouse import connect

SQL_SCHEMA = {
    "type": "object",
    "required": ["sql", "explanation"],
    "properties": {"sql": {"type": "string"}, "explanation": {"type": "string"}},
}

HITS = """
CALL db.index.vector.queryNodes('semantic_embedding', $hits, $v) YIELD node, score
RETURN node.level AS level, node.name AS name, score
"""

# Which level-1 groups to open: under the closest Semantic nodes of any level (the hierarchy), the
# closest level-1 groups directly (flat), or both.
PICK = {
    "traversal": """CALL db.index.vector.queryNodes('semantic_embedding', $hits, $v) YIELD node AS hit
                    MATCH (g:Semantic {level: 1})-[:IN_SEMANTIC]->*(hit)
                    RETURN g, collect(DISTINCT hit.name) AS via""",
    "flat": """MATCH (g:Semantic {level: 1}) WITH g ORDER BY vector.similarity.cosine(g.embedding, $v) DESC
               LIMIT $groups RETURN g, ['(direct)'] AS via""",
}
PICK["combined"] = f"CALL () {{ {PICK['traversal']} UNION {PICK['flat']} }} RETURN g, via"

# The groups opened, closest first, and the columns (with their tables) they hold.
DESCEND = """
CALL () {{ {pick} }}
WITH g, reduce(a = [], x IN collect(via) | a + x) AS via
WITH g, via, vector.similarity.cosine(g.embedding, $v) AS sim
ORDER BY sim DESC LIMIT $groups
MATCH (m)-[:IN_SEMANTIC]->(g)
MATCH (m)<-[:IS]-{{0,1}}(c:Column)<-[:HAS_COLUMN]-(t:Table)
RETURN g.name AS grp, sim, via, t.id AS table, CASE WHEN m:Variable THEN 'Variable' ELSE 'Unjoined' END AS kind,
       CASE WHEN m:Variable THEN m.name ELSE c.name END AS member, c.name AS column
"""

USED = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)<-[:READS]-(:QueryShape)<-[:RAN]-(p:Principal)
WHERE t.id IN $tables AND c.name IN $cols
RETURN t.id AS t, count(DISTINCT p) AS n
"""

# Nothing wrote it in the log window and no production process reads it (directly or through a
# view): people may still query it, but it is not being kept current.
FROZEN = """
MATCH (t:Table) WHERE t.id IN $tables AND t.kind IN ['table', 'wildcard'] AND t.write_days IS NULL
  AND NOT EXISTS { MATCH (:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape {succeeded: true})-[:REFERENCES]->(x:Table)
                   WHERE x = t OR (x.kind = 'view' AND (x)-[:DERIVED_FROM*1..3]->(t)) }
RETURN t.id AS t
"""

JOINS = """
MATCH (a:Table)-[:HAS_COLUMN]->(x:Column)<-[:ON]-(k:JoinKey)-[:ON]->(y:Column)<-[:HAS_COLUMN]-(b:Table)
WHERE a.id IN $tables AND b.id IN $tables AND a.id < b.id
OPTIONAL MATCH (x)-[:IS]->(v:Variable)
RETURN a.id AS a, x.name AS ac, b.id AS b, y.name AS bc, v.name AS variable,
       count{ (:QueryShape)-[:USES_JOIN]->(k) } AS queries
ORDER BY queries DESC LIMIT 8
"""

QUERIES = """
MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table) WHERE t.id IN $tables
WITH s, count(DISTINCT t) AS hit WHERE hit >= 2
MATCH (p:Principal)-[r:RAN]->(s)
WITH s, hit, collect(DISTINCT split(p.id, '@')[0]) AS who, sum(r.jobs) AS jobs
RETURN s.sample_sql AS sql, hit, who, jobs ORDER BY hit DESC, jobs DESC LIMIT 2
"""

COLUMNS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.id IN $tables AND c.in_catalog
RETURN t.id AS t, collect(c.name + ' ' + coalesce(c.type, '')) AS cols
"""


def round_robin(order: list[str], tables: dict, k: int) -> list[str]:
    """Each group in `order`, closest first, contributes its most-used table not yet taken, until k
    tables; frozen tables only once no group has a live one left."""
    by_use = lambda t: (tables[t]["frozen"], -tables[t]["used"], -len(tables[t]["cols"]))
    queues = [sorted((t for t in tables if g in tables[t]["groups"]), key=by_use) for g in order]
    queues = [[t for t in q if not tables[t]["frozen"]] for q in queues] + [[t for q in queues for t in q]]
    top: list[str] = []
    while len(top) < min(k, len(tables)):
        for q in queues:
            nxt = next((t for t in q if t not in top), None)
            if nxt and len(top) < k:
                top.append(nxt)
    return top


def cohort(G: Graph, v: list[float], p: dict, mode: str | None = None, rank: str | None = None):
    """Steps 2-4: the level-1 groups to open, the tables whose own columns they hold, and the top tables.
    rank 'round_robin' (default) or 'usage' (most-queried first) -> (groups, tables, top table ids)."""
    mode, rank = mode or p["mode"], rank or p["rank"]
    rows = G.rows(DESCEND.format(pick=PICK[mode]), hits=p["hits"], groups=p["groups"], v=v)
    groups, tables = {}, {}
    for r in rows:
        g = groups.setdefault(r["grp"], {"sim": r["sim"], "via": r["via"], "members": set()})
        g["members"].add(("var " if r["kind"] == "Variable" else "") + r["member"])
        # a table enters the cohort through its own (unjoined) columns; a variable only links tables
        if r["kind"] == "Unjoined":
            t = tables.setdefault(r["table"], {"cols": set(), "groups": set()})
            t["cols"].add(r["column"])
            t["groups"].add(r["grp"])
    ids = list(tables)
    used = {
        r["t"]: r["n"]
        for r in G.rows(USED, tables=ids, cols=sorted({c for t in tables.values() for c in t["cols"]}))
    }
    frozen = {r["t"] for r in G.rows(FROZEN, tables=ids)}
    for t in tables:
        tables[t]["used"] = used.get(t, 0)
        tables[t]["frozen"] = t in frozen
    if rank == "round_robin":
        top = round_robin(list(groups), tables, p["tables"])  # groups arrive closest first
    else:
        top = sorted(tables, key=lambda t: (tables[t]["frozen"], -tables[t]["used"], -len(tables[t]["cols"])))
        top = top[: p["tables"]]
    return groups, tables, top


def write_sql(
    G: Graph, s: Settings, question: str, top: list[str], joins: list[dict], examples: list[dict]
) -> None:
    """Step 6: the cohort -> one query, dry-run in the warehouse."""
    wh = connect(s)
    cols = G.rows(COLUMNS, tables=top)
    tables = "\n".join(f"`{r['t']}`: {', '.join(r['cols'][:60])}" for r in cols)
    joins_txt = "\n".join(f"{j['a']}.{j['ac']} = {j['b']}.{j['bc']}" for j in joins) or "(none recorded)"
    ex = "\n\n".join(" ".join(q["sql"].split())[:1500] for q in examples) or "(none)"
    llm = LLM(prompt("sql_system", sql=wh.sql, **s.business), s)
    request = prompt(
        "sql_request", question=question, tables=tables, joins=joins_txt, examples=ex, **s.business
    )
    out = llm.call(request, SQL_SCHEMA, "record_sql", max_tokens=3000)
    res = wh.dry_run(out["sql"])
    if res["ok"] is False:
        fix = prompt("sql_fix", error=res["error"], warehouse=wh.name)
        out = llm.call(request + "\n\n" + fix, SQL_SCHEMA, "record_sql", max_tokens=3000)
        res = wh.dry_run(out["sql"])
    print(f"\n5. the SQL (written from the cohort above, dry-run in {wh.name})")
    print(textwrap.indent(out["sql"].strip(), "   "))
    print("\n   " + textwrap.fill(out["explanation"], 100, subsequent_indent="   "))
    if res["ok"]:
        print(f"   dry run: valid; would scan {res.get('bytes_processed') or 0:,} bytes")
    elif res["ok"] is None:
        print(f"   dry run skipped: {res['error']}")
    else:
        print(f"   dry run failed: {res['error']}")


def run(s: Settings, question: str, sql: bool = True) -> None:
    p = s.params["navigate"]
    with Graph(s) as G:
        v = Embedder(s).embed([question])[0]
        print(f"QUESTION  {question}\n")
        print("1. semantic layer: closest Semantic nodes (any level)")
        for h in G.rows(HITS, hits=p["hits"], v=v):
            print(f"   {h['score']:.3f}  L{h['level']}  {h['name']}")

        groups, tables, top = cohort(G, v, p)
        print("\n2. down to the level-1 groups under those hits, closest first")
        for name, g in groups.items():
            print(f"   {g['sim']:.3f}  {name}  (under: {', '.join(g['via'])})")
            print("          " + textwrap.shorten(", ".join(sorted(g["members"])), 150))
        print(
            f"\n3. down to the physical layer: the cohort ({len(top)} of {len(tables)} tables; each group, "
            "closest first, contributes its most-used table in turn; frozen tables last)"
        )
        for t in top:
            cols = textwrap.shorten(", ".join(sorted(tables[t]["cols"])), 80)
            print(
                f"   {short(t):46} {tables[t]['used']:2} principals{' FROZEN' if tables[t]['frozen'] else ''}  {cols}"
            )

        print("\n4. how the log connects them")
        joins, examples = G.rows(JOINS, tables=top), G.rows(QUERIES, tables=top)
        for j in joins:
            print(
                f"   join  {short(j['a'])}.{j['ac']} = {short(j['b'])}.{j['bc']}"
                + (f"  [{j['variable']}]" if j["variable"] else "")
                + f"  ({j['queries']} queries)"
            )
        for q in examples:
            print(
                f"\n   a query that reads {q['hit']} of them, {q['jobs']} runs by {', '.join(q['who'][:4])}:"
            )
            print(textwrap.indent(textwrap.shorten(" ".join(q["sql"].split()), 600), "     "))
        if sql:
            write_sql(G, s, question, top, joins, examples)

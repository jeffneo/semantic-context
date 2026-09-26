#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40", "sqlglot>=30", "google-cloud-bigquery>=3.25"]
# ///
"""Demo: from a natural-language question down to the data assets that answer it.

  1. Embed the question with the model the Semantic nodes were embedded with.
  2. Vector search the semantic layer (any level) for the closest Semantic nodes.
  3. Walk down IN_SEMANTIC from those hits to the level-1 groups beneath them, add the level-1
     groups closest to the question directly, and keep the closest of all: the hits say where
     to look, the groups narrow it. The direct search guards against a group filed under the
     wrong parent (specs/tools/eval_navigate.py: the hierarchy alone reaches 71% of the gold
     questions' tables, with the direct search 78%).
  4. Down again to the physical layer: the tables whose own columns are in those groups.
     Ranked round robin: each group, closest to the question first, contributes its most-used
     table (by principals querying those columns) in turn, so every relevant group is
     represented and a hub table from a nearby group cannot crowd out the core table of the
     closest one. Frozen tables (nothing wrote them in the window and no production process
     reads them) go last. Variables are the links between tables, so a table reached only
     through a shared variable is not part of the cohort.
  5. The log's evidence for that cohort: the joins between those tables, and the queries
     that already read them together, with who ran them.
  6. The SQL: the LLM writes one BigQuery query from that cohort (prompts/sql_*.md), and
     BigQuery dry-runs it - valid or not, and how many bytes it would scan - at no cost. A
     failed dry run goes back to the LLM once. The warehouse tables are empty (the estate is
     deployed for validation only), so the query is validated, not run. --no-sql skips this.

The cohort is ranked by use: how many principals query the tables' columns in play.

Usage: uv run pipeline/navigate.py [--no-sql] "How many customers use the mobile app each week?"
"""
from __future__ import annotations

import math
import sys
import textwrap
from collections import Counter, defaultdict

from graphdb import Graph, config
from llm import LLM, Embedder, prompt

SQL_SCHEMA = {"type": "object", "required": ["sql", "explanation"], "properties": {
    "sql": {"type": "string"}, "explanation": {"type": "string"}}}

HITS, GROUPS, TABLES = 5, 4, 8

# which level-1 groups to open: under the closest Semantic nodes of any level (the hierarchy),
# the closest level-1 groups directly (flat), or both
PICK = {
    "traversal": """CALL db.index.vector.queryNodes('semantic_embedding', $hits, $v) YIELD node AS hit
                    MATCH (g:Semantic {level: 1})-[:IN_SEMANTIC]->*(hit)
                    RETURN g, collect(DISTINCT hit.name) AS via""",
    "flat": """MATCH (g:Semantic {level: 1}) WITH g ORDER BY vector.similarity.cosine(g.embedding, $v) DESC
               LIMIT $groups RETURN g, ['(direct)'] AS via""",
}
PICK["combined"] = f"CALL () {{ {PICK['traversal']} UNION {PICK['flat']} }} RETURN g, via"

DESCEND = """
CALL () { PICK }
WITH g, reduce(a = [], x IN collect(via) | a + x) AS via
WITH g, via, vector.similarity.cosine(g.embedding, $v) AS sim
ORDER BY sim DESC LIMIT $groups
MATCH (m)-[:IN_SEMANTIC]->(g)
MATCH (m)<-[:IS]-{0,1}(c:Column)<-[:HAS_COLUMN]-(t:Table)
RETURN g.name AS grp, sim, via, t.id AS table, CASE WHEN m:Variable THEN 'Variable' ELSE 'Unjoined' END AS kind,
       CASE WHEN m:Variable THEN m.name ELSE c.name END AS member, c.name AS column
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


def short(t: str) -> str:
    return t.split(".", 1)[1]


def write_sql(G: Graph, cfg: dict, question: str, top: list[str], joins: list[dict], examples: list[dict]):
    """Step 6: the cohort -> one BigQuery query, dry-run in BigQuery."""
    from tools import BigQueryDryRun, Physical
    cols = G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.id IN $tables AND c.in_catalog
                     RETURN t.id AS t, collect(c.name + ' ' + coalesce(c.type, '')) AS cols""", tables=top)
    tables = "\n".join(f"`{r['t']}`: {', '.join(r['cols'][:60])}" for r in cols)
    joins_txt = "\n".join(f"{j['a']}.{j['ac']} = {j['b']}.{j['bc']}" for j in joins) or "(none recorded)"
    ex = "\n\n".join(" ".join(s["sql"].split())[:1500] for s in examples) or "(none)"
    llm = LLM(prompt("sql_system"), cfg)
    request = prompt("sql_request", question=question, tables=tables, joins=joins_txt, examples=ex)
    out = llm.call(request, SQL_SCHEMA, "record_sql", max_tokens=3000)
    phys, dry = Physical(G, cfg), BigQueryDryRun(cfg)

    def check(sql):
        try:
            return dry(phys.rewrite(sql))
        except Exception as e:                   # e.g. SQL that does not parse
            return {"ok": False, "error": str(e)[:300]}
    res = check(out["sql"])
    if res.get("ok") is False and "print-access-token" not in (res.get("error") or ""):
        out = llm.call(request + "\n\n" + prompt("sql_fix", error=res["error"]), SQL_SCHEMA, "record_sql", max_tokens=3000)
        res = check(out["sql"])
    print("\n5. the SQL (written from the cohort above, dry-run in BigQuery)")
    print(textwrap.indent(out["sql"].strip(), "   "))
    print("\n   " + textwrap.fill(out["explanation"], 100, subsequent_indent="   "))
    if res.get("ok"):
        print(f"   dry run: valid BigQuery; would scan {res.get('bytes_processed') or 0:,} bytes "
              "(the deployed tables are empty, so it is validated, not run)")
    elif "print-access-token" in (res.get("error") or ""):
        print("   dry run skipped: gcloud needs a fresh login (CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc gcloud auth login)")
    else:
        print(f"   dry run failed: {res.get('error')}")


FROZEN = """
MATCH (t:Table) WHERE t.id IN $tables AND t.kind IN ['table', 'wildcard'] AND t.write_days IS NULL
  AND NOT EXISTS { MATCH (:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape {succeeded: true})-[:REFERENCES]->(x:Table)
                   WHERE x = t OR (x.kind = 'view' AND (x)-[:DERIVED_FROM*1..3]->(t)) }
RETURN t.id AS t
"""


def cohort(G: Graph, v: list[float], mode: str = "combined", rank: str = "round_robin", k: int = TABLES):
    """Steps 2-3: the level-1 groups to open, and the tables whose own columns they hold.
    rank 'usage': by how many principals query those columns; 'group': tables of the closest
    group first, then by usage. -> (groups, tables, ranked table ids)"""
    rows = G.rows(DESCEND.replace("PICK", PICK[mode], 1), hits=HITS, groups=GROUPS, v=v)
    groups, tables = {}, {}
    per_group = defaultdict(Counter)                             # group -> table -> its unjoined columns there
    for r in rows:
        g = groups.setdefault(r["grp"], {"sim": r["sim"], "via": r["via"], "members": set()})
        g["members"].add(("var " if r["kind"] == "Variable" else "") + r["member"])
        # a table enters the cohort through its own (unjoined) columns; a variable only links tables
        if r["kind"] == "Unjoined":
            t = tables.setdefault(r["table"], {"cols": set(), "groups": set()})
            t["cols"].add(r["column"])
            t["groups"].add(r["grp"])
            per_group[r["grp"]][r["table"]] += 1
    used = {r["t"]: r["n"] for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)<-[:READS]-(:QueryShape)<-[:RAN]-(p:Principal)
        WHERE t.id IN $tables AND c.name IN $cols RETURN t.id AS t, count(DISTINCT p) AS n""",
        tables=list(tables), cols=sorted({c for t in tables.values() for c in t["cols"]}))}
    # frozen: nothing wrote it in the log window and no production process reads it (directly or
    # through a view) - people may still query it, but it is not being kept current
    frozen = {r["t"] for r in G.rows(FROZEN, tables=list(tables))}
    order = {name: i for i, name in enumerate(groups)}          # groups arrive closest first
    for t in tables:
        tables[t]["used"] = used.get(t, 0)
        tables[t]["frozen"] = t in frozen
        tables[t]["group_rank"] = min(order[g] for g in tables[t]["groups"])
        # relevance: for each opened group, its closeness to the question times this table's share of it
        tables[t]["relevance"] = sum(groups[g]["sim"] * per_group[g][t] / sum(per_group[g].values())
                                     for g in tables[t]["groups"])
    key = {"usage": lambda t: (tables[t]["frozen"], -tables[t]["used"], -len(tables[t]["cols"])),
           "group": lambda t: (tables[t]["group_rank"], -tables[t]["used"], -len(tables[t]["cols"])),
           "relevance": lambda t: -tables[t]["relevance"],
           "relevance_usage": lambda t: -tables[t]["relevance"] * math.log(2 + tables[t]["used"]),
           "round_robin": None}[rank]
    if rank == "round_robin":
        # each group, closest first, contributes its most-used table not yet taken, until k tables
        queues = [sorted((t for t in tables if g in tables[t]["groups"]),
                         key=lambda t: (tables[t]["frozen"], -tables[t]["used"], -len(tables[t]["cols"]))) for g in groups]
        queues = [[t for t in q if not tables[t]["frozen"]] for q in queues] + [[t for q in queues for t in q]]
        top = []
        while len(top) < min(k, len(tables)):
            for q in queues:
                nxt = next((t for t in q if t not in top), None)
                if nxt and len(top) < k:
                    top.append(nxt)
        return groups, tables, top
    top = sorted(tables, key=key)[:k]
    return groups, tables, top


def main() -> int:
    no_sql = "--no-sql" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--no-sql"]
    question = " ".join(sys.argv[1:]) or "Which contact centers see the most account closures, and what do they cost to run?"
    cfg = config()
    G = Graph(cfg)
    q = Embedder(cfg).embed([question])[0]
    print(f"QUESTION  {question}\n")

    hits = G.rows("""CALL db.index.vector.queryNodes('semantic_embedding', $hits, $v) YIELD node, score
                     RETURN node.level AS level, node.name AS name, score""", hits=HITS, v=q)
    print("1. semantic layer: closest Semantic nodes (any level)")
    for h in hits:
        print(f"   {h['score']:.3f}  L{h['level']}  {h['name']}")

    groups, tables, top = cohort(G, q)
    print("\n2. down to the level-1 groups under those hits, closest first")
    for name, g in groups.items():
        print(f"   {g['sim']:.3f}  {name}  (under: {', '.join(g['via'])})")
        print("          " + textwrap.shorten(", ".join(sorted(g["members"])), 150))
    print(f"\n3. down to the physical layer: the cohort ({len(top)} of {len(tables)} tables; each group, closest first, "
          "contributes its most-used table in turn; frozen tables last)")
    for t in top:
        print(f"   {short(t):46} {tables[t]['used']:2} principals{' FROZEN' if tables[t]['frozen'] else ''}  {textwrap.shorten(', '.join(sorted(tables[t]['cols'])), 80)}")

    print("\n4. how the log connects them")
    joins, examples = G.rows(JOINS, tables=top), G.rows(QUERIES, tables=top)
    for j in joins:
        print(f"   join  {short(j['a'])}.{j['ac']} = {short(j['b'])}.{j['bc']}"
              + (f"  [{j['variable']}]" if j["variable"] else "") + f"  ({j['queries']} queries)")
    for s in examples:
        print(f"\n   a query that reads {s['hit']} of them, {s['jobs']} runs by {', '.join(s['who'][:4])}:")
        print(textwrap.indent(textwrap.shorten(" ".join(s["sql"].split()), 600), "     "))
    if not no_sql:
        write_sql(G, cfg, question, top, joins, examples)
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

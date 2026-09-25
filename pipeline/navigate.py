#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40", "sqlglot>=30", "google-cloud-bigquery>=3.25"]
# ///
"""Demo: from a natural-language question down to the data assets that answer it.

  1. Embed the question with the model the Semantic nodes were embedded with.
  2. Vector search the semantic layer (any level) for the closest Semantic nodes.
  3. Walk down IN_SEMANTIC from those hits to the level-1 groups beneath them, and keep the
     groups closest to the question: the hits say where to look, the groups narrow it.
  4. Down again to the physical layer: the tables whose own columns are in those groups,
     ranked by how many principals query those columns. Variables are the links between
     tables, so a table reached only through a shared variable is not part of the cohort.
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

import sys
import textwrap

from graphdb import Graph, config
from llm import LLM, Embedder, prompt

SQL_SCHEMA = {"type": "object", "required": ["sql", "explanation"], "properties": {
    "sql": {"type": "string"}, "explanation": {"type": "string"}}}

HITS, GROUPS, TABLES = 5, 4, 8

DESCEND = """
CALL db.index.vector.queryNodes('semantic_embedding', $hits, $v) YIELD node AS hit, score
MATCH (g:Semantic {level: 1})-[:IN_SEMANTIC]->*(hit)
WITH g, collect(DISTINCT hit.name) AS via, vector.similarity.cosine(g.embedding, $v) AS sim
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

    rows = G.rows(DESCEND, hits=HITS, groups=GROUPS, v=q)
    groups, tables = {}, {}
    for r in rows:
        g = groups.setdefault(r["grp"], {"sim": r["sim"], "via": r["via"], "members": set()})
        g["members"].add(("var " if r["kind"] == "Variable" else "") + r["member"])
        # a table enters the cohort through its own (unjoined) columns; a variable only links tables
        if r["kind"] == "Unjoined":
            t = tables.setdefault(r["table"], {"cols": set(), "groups": set()})
            t["cols"].add(r["column"])
            t["groups"].add(r["grp"])
    print("\n2. down to the level-1 groups under those hits, closest first")
    for name, g in groups.items():
        print(f"   {g['sim']:.3f}  {name}  (under: {', '.join(g['via'])})")
        print("          " + textwrap.shorten(", ".join(sorted(g["members"])), 150))

    # rank the tables by use: how many principals query the columns in play
    used = {r["t"]: r["n"] for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)<-[:READS]-(:QueryShape)<-[:RAN]-(p:Principal)
        WHERE t.id IN $tables AND c.name IN $cols RETURN t.id AS t, count(DISTINCT p) AS n""",
        tables=list(tables), cols=sorted({c for t in tables.values() for c in t["cols"]}))}
    top = sorted(tables, key=lambda t: (-used.get(t, 0), -len(tables[t]["cols"])))[:TABLES]
    print(f"\n3. down to the physical layer: the cohort ({len(top)} of {len(tables)} tables, by principals querying them)")
    for t in top:
        print(f"   {short(t):46} {used.get(t, 0):2} principals  {textwrap.shorten(', '.join(sorted(tables[t]['cols'])), 80)}")

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

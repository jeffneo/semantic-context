"""OKF: the Computations as an Open Knowledge Format bundle (OKF v0.2, GoogleCloudPlatform/open-knowledge-format).

A directory of markdown files with YAML frontmatter, for any agent or catalog to read:

  index.md                              okf_version 0.2; the areas, and the tables
  computations/<area>/index.md          the area's measures, dimensions and populations
  computations/<area>/<computation>.md  type: Attested Computation
  tables/<dataset>/<table>.md           type: BigQuery Table: schema, joins, the computations over it

A Computation's area is the top Semantic level its columns sit under (most of them). Each concept's
frontmatter carries OKF's provenance and lifecycle families, all from the log:
  sources       the query shapes that compute it, each with its runs (usage_count) and who ran it
                (process: a service account, human: a person), over the log's window (usage_window)
  status        stable if production computes it, draft if only people do, deprecated if every
                table it reads is a sandbox or frozen
  generated     qlsc, at the log's last day (so an unchanged layer writes the same bundle)
No `verified`: a definition inferred from use is unverified until someone confirms it (OKF 5.3).

The bundle is read back at the end: every concept has a type, and every link inside it resolves.
"""

from __future__ import annotations

import re
import shutil
from collections import defaultdict
from pathlib import Path

import yaml

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.names import short

COMPUTATIONS = """
MATCH (c:Computation)
OPTIONAL MATCH (s:QueryShape)-[:COMPUTES]->(c)
OPTIONAL MATCH (p:Principal)-[r:RAN]->(s)
WITH c, s, collect(DISTINCT p.kind) AS kinds, collect(DISTINCT split(p.id, '@')[0]) AS who, sum(r.jobs) AS jobs
ORDER BY jobs DESC, s.id
WITH c, collect({id: s.id, sql: s.sample_sql, kinds: kinds, who: who, jobs: jobs})[..$shapes] AS shapes
RETURN c {.id, .kind, .name, .description, .expression, .filters, .grain, .tables, .aliases, .jobs,
          .production, .trusted, .shapes} AS c, shapes
ORDER BY c.id
"""

# The top Semantic area over each Computation's columns (a count of zero columns: its tables' columns).
AREAS = """
MATCH (c:Computation)
OPTIONAL MATCH (c)-[:READS]->(x:Column)
WITH c, collect(x) AS read
WITH c, CASE WHEN size(read) > 0 THEN read ELSE [(t:Table)-[:HAS_COLUMN]->(y) WHERE t.id IN c.tables | y] END AS cols
CALL (cols) {
  UNWIND cols AS col
  MATCH (col)-[:IS]->{0,1}()-[:IN_SEMANTIC]->(:Semantic {level: 1})-[:IN_SEMANTIC]->*(top:Semantic)
  WHERE NOT (top)-[:IN_SEMANTIC]->()
  RETURN top.name AS area, count(*) AS n ORDER BY n DESC, area LIMIT 1
}
RETURN c.id AS id, area
"""

TABLES = """
MATCH (t:Table)-[:HAS_COLUMN]->(col:Column) WHERE t.id IN $tables
WITH t, col ORDER BY col.name
RETURN t.id AS id, t.kind AS kind, collect({name: col.name, type: col.type}) AS cols
"""

JOINS = """
MATCH (a:Table)-[:HAS_COLUMN]->(x:Column)<-[:ON]-(k:JoinKey)-[:ON]->(y:Column)<-[:HAS_COLUMN]-(b:Table)
WHERE a.id IN $tables AND a.id < b.id
RETURN a.id AS a, x.name AS ac, b.id AS b, y.name AS bc, count{ (:QueryShape)-[:USES_JOIN]->(k) } AS queries
ORDER BY queries DESC, a, b
"""

WINDOW = "MATCH (s:QueryShape) RETURN min(s.first_seen) AS start, max(s.last_seen) AS end"

KINDS = {"measure": "Measures", "dimension": "Derived dimensions", "population": "Populations"}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "unnamed"


def frontmatter(meta: dict, body: str) -> str:
    head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=100).strip()
    return f"---\n{head}\n---\n\n{body.strip()}\n"


def actor(kinds: list[str], who: list[str]) -> str:
    name = sorted(who)[0] if who else "unknown"
    return f"process:{name}" if "service_account" in kinds else f"human:{name}"


def computation_doc(c: dict, shapes: list[dict], area: str, path: dict, window: dict, stamp: str) -> str:
    status = "deprecated" if not c["trusted"] else ("stable" if c["production"] else "draft")
    meta = {
        "type": "Attested Computation",
        "title": c["name"] or c["expression"][:60],
        "description": c["description"] or "",
        "tags": [c["kind"], slug(area)],
        "kind": c["kind"],
        "status": status,
        "runtime": "bigquery",
        "generated": {"by": "qlsc/computations", "at": stamp},
        "sources": [
            {
                "id": f"q{s['id'][:8]}",
                "resource": f"query shape {s['id']} in the warehouse's query log",
                "title": "a production query" if "service_account" in s["kinds"] else "a person's query",
                "author": actor(s["kinds"], s["who"]),
                "usage_count": s["jobs"],
            }
            for s in shapes
            if s["id"]
        ],
        "usage_window": window,
    }
    lines = [
        "# Computation",
        "",
        "```sql",
        runnable(c) if len(c["tables"]) == 1 else c["expression"],
        "```",
        "",
    ]
    if c["filters"] and c["kind"] == "measure":
        lines += ["It comes with these filters, in every query that computes it:", ""]
        lines += [f"- `{f}`" for f in c["filters"]] + [""]
    if c["grain"]:
        lines += ["Most often grouped by " + ", ".join(f"`{g}`" for g in c["grain"]) + ".", ""]
    if c["aliases"]:
        lines += ["Queries call it " + ", ".join(f"`{a}`" for a in c["aliases"]) + ".", ""]
    lines += ["# Tables", ""]
    lines += [f"- [{short(t)}](/{path[t]})" for t in c["tables"]] + [""]
    lines += ["# Examples", ""]
    top = next((s for s in shapes if s["sql"]), None)
    ref = f"[^q{top['id'][:8]}]" if top else ""
    lines += [f"Computed by {c['shapes']} queries in the log, {c['jobs']:,} runs. The most run{ref}:", ""]
    if top:
        lines += ["```sql", " ".join(top["sql"].split())[:1500], "```", ""]
        lines += [f"{ref}: {meta['sources'][0]['title']}"]
    return frontmatter(meta, "\n".join(lines))


def runnable(c: dict) -> str:
    table = c["tables"][0]
    name = table.rsplit(".", 1)[-1]
    what = c["expression"] if c["kind"] != "population" else "COUNT(*)"
    where = (
        c["filters"] if c["kind"] == "measure" else ([c["expression"]] if c["kind"] == "population" else [])
    )
    grain = c["grain"] if c["kind"] == "measure" else ([c["expression"]] if c["kind"] == "dimension" else [])
    sql = "SELECT " + ", ".join([*grain, what]) + f"\nFROM `{table}` AS {name}"
    if where:
        sql += "\nWHERE " + "\n  AND ".join(where)
    if grain:
        sql += "\nGROUP BY " + ", ".join(str(i + 1) for i in range(len(grain)))
    return sql


def table_doc(t: dict, comps: list[dict], cpath: dict, joins: list[dict], tpath: dict) -> str:
    meta = {
        "type": "BigQuery Table",
        "title": short(t["id"]),
        "description": f"{t['kind'] or 'table'} {t['id']}, as the log's queries use it",
        "resource": t["id"],
    }
    lines = ["# Schema", "", "| Column | Type |", "|---|---|"]
    lines += [f"| `{x['name']}` | {x['type'] or ''} |" for x in t["cols"]] + [""]
    if joins:
        lines += ["# Joins", ""]
        for j in joins:
            other = f"[{short(j['b'])}](/{tpath[j['b']]})" if j["b"] in tpath else f"`{short(j['b'])}`"
            lines.append(f"- `{j['ac']}` = {other} `{j['bc']}` ({j['queries']} queries)")
        lines.append("")
    lines += ["# Computations", ""]
    lines += [f"- [{c['name'] or c['expression'][:60]}](/{cpath[c['id']]}) ({c['kind']})" for c in comps]
    return frontmatter(meta, "\n".join(lines))


def check(root: Path) -> dict:
    """OKF conformance (11) and link integrity: every concept has a type; every /link resolves."""
    concepts = [p for p in root.rglob("*.md") if p.name not in ("index.md", "log.md")]
    untyped, broken = [], []
    for p in concepts + list(root.rglob("index.md")):
        text = p.read_text()
        if p.name != "index.md":
            m = re.match(r"---\n(.*?)\n---\n", text, re.S)
            if not m or not (yaml.safe_load(m.group(1)) or {}).get("type"):
                untyped.append(str(p.relative_to(root)))
        for link in re.findall(r"\]\((/[^)#\s]+)\)", text):
            if not (root / link.lstrip("/")).exists():
                broken.append(f"{p.relative_to(root)} -> {link}")
    return {"concepts": len(concepts), "untyped": untyped, "broken": broken}


def run(s: Settings, out: Path | None = None) -> None:
    root = out or s.work / "okf"
    p = s["okf"]
    with Graph(s) as G:
        rows = G.rows(COMPUTATIONS, shapes=p["sources"])
        area_of = defaultdict(lambda: "Unassigned", {r["id"]: r["area"] for r in G.rows(AREAS) if r["area"]})
        w = G.rows(WINDOW)[0]
        tables = sorted({t for r in rows for t in r["c"]["tables"]})
        trows = G.rows(TABLES, tables=tables)
        joins = defaultdict(list)
        for j in G.rows(JOINS, tables=tables):
            joins[j["a"]].append(j)
            joins[j["b"]].append(
                {"a": j["b"], "ac": j["bc"], "b": j["a"], "bc": j["ac"], "queries": j["queries"]}
            )
    window = {"from": w["start"][:10] + "T00:00:00Z", "to": w["end"][:10] + "T00:00:00Z"}
    stamp = window["to"]
    if root.exists():
        shutil.rmtree(root)
    cpath, tpath, used = {}, {}, set()
    for t in trows:
        project, dataset, name = t["id"].split(".", 2)
        tpath[t["id"]] = f"tables/{dataset}/{name}.md"
    for r in rows:
        c = r["c"]
        base = f"computations/{slug(area_of[c['id']])}/{slug(c['name'] or c['expression'])}"
        path = base if base not in used else f"{base}-{c['id'][:6]}"
        used.add(path)
        cpath[c["id"]] = path + ".md"
    by_area, by_table = defaultdict(list), defaultdict(list)
    for r in rows:
        c = r["c"]
        c["tables"] = [t for t in c["tables"] if t in tpath]
        target = root / cpath[c["id"]]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(computation_doc(c, r["shapes"], area_of[c["id"]], tpath, window, stamp))
        by_area[area_of[c["id"]]].append(c)
        for t in c["tables"]:
            by_table[t].append(c)
    for t in trows:
        target = root / tpath[t["id"]]
        target.parent.mkdir(parents=True, exist_ok=True)
        comps = sorted(by_table[t["id"]], key=lambda c: (-c["jobs"], c["id"]))
        target.write_text(table_doc(t, comps, cpath, joins[t["id"]][: p["joins"]], tpath))
    for area, comps in sorted(by_area.items()):
        lines = []
        for kind, heading in KINDS.items():
            ks = sorted((c for c in comps if c["kind"] == kind), key=lambda c: (-c["jobs"], c["id"]))
            if ks:
                lines += [f"# {heading}", ""]
                lines += [
                    f"* [{c['name'] or c['expression'][:60]}](/{cpath[c['id']]}) - {c['description'] or ''}"
                    for c in ks
                ]
                lines.append("")
        (root / f"computations/{slug(area)}/index.md").write_text("\n".join(lines))
    top = ["---", 'okf_version: "0.2"', "---", "", "# Business areas", ""]
    top += [
        f"* [{area}](/computations/{slug(area)}/index.md) - {len(comps)} computations"
        for area, comps in sorted(by_area.items())
    ]
    top += ["", "# Tables", ""]
    top += [f"* [{short(t['id'])}](/{tpath[t['id']]}) - {t['kind'] or 'table'}" for t in trows]
    (root / "index.md").write_text("\n".join(top) + "\n")
    result = check(root)
    print(
        f"OKF bundle: {result['concepts']} concepts ({len(rows)} computations, {len(trows)} tables) in {root}; "
        f"{len(result['untyped'])} without a type, {len(result['broken'])} broken links"
    )
    for x in (result["untyped"] + result["broken"])[:10]:
        print("  ", x)

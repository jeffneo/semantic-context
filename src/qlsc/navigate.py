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
  5. The log's evidence: the queries closest to the question (their SQL's embedding), skipping any
     that read a sandbox (a table only people write) or a frozen table, and the tables they read, which
     join the cohort; then the joins between all of them. (examples_by: runs instead takes the most-run
     queries over the cohort.)
  6. The SQL: the LLM writes one query from that cohort (prompts/sql_*.md) and the warehouse dry-runs
     it - valid or not, and how many bytes it would scan - at no cost. A failed dry run goes back to
     the LLM once.
     Or, with --cypher, a Cypher query over the virtual graph `qlsc virtualize` wrote: the cohort's
     tables that are labels there, and one hop of relationships around them (prompts/cypher_*.md).
     Virtual Graph's EXPLAIN is the check (it rejects what its Cypher subset lacks) and shows the SQL it
     would send.
  7. With --run, the answer: the query runs, billing at most `maximum_bytes_billed`.

Everything is deterministic but the SQL and the Cypher: the same question gives the same cohort.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import textwrap
import time
from decimal import Decimal

from neo4j.exceptions import Neo4jError, ServiceUnavailable

from qlsc import compile as compiler
from qlsc import entitle
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, cosine, prompt
from qlsc.names import short
from qlsc.warehouse import connect

SQL_SCHEMA = {
    "type": "object",
    "required": ["sql", "explanation"],
    "properties": {"sql": {"type": "string"}, "explanation": {"type": "string"}},
}

DECOMPOSE_SCHEMA = {
    "type": "object",
    "required": ["measures", "groupings", "filters", "entities", "period"],
    "properties": {
        "measures": {"type": "array", "items": {"type": "string"}},
        "groupings": {"type": "array", "items": {"type": "string"}},
        "filters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["subject", "value"],
                "properties": {"subject": {"type": "string"}, "value": {"type": "string"}},
            },
        },
        "entities": {"type": "array", "items": {"type": "string"}},
        "period": {"type": "string"},
    },
}

CYPHER_SCHEMA = {
    "type": "object",
    "required": ["answerable", "cypher", "explanation"],
    "properties": {
        "answerable": {
            "type": "boolean",
            "description": "false when the graph given can't answer the question (then cypher is empty)",
        },
        "cypher": {"type": "string"},
        "explanation": {"type": "string"},
    },
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
WITH s, hit, collect(DISTINCT split(p.id, '@')[0]) AS who, collect(DISTINCT p.kind) AS kinds, sum(r.jobs) AS jobs
RETURN s.id AS id, s.sample_sql AS sql, hit, who, kinds, jobs,
       [(s)-[:REFERENCES]->(t:Table) WHERE t.in_catalog | t.id] AS tables
ORDER BY hit DESC, jobs DESC LIMIT $n
"""

# Every query shape that computes something, with who runs it and the tables it reads: the candidates
# for the examples closest to a question.
SHAPES = """
MATCH (s:QueryShape {succeeded: true}) WHERE s.statement_type IN $statements AND s.sample_sql IS NOT NULL
MATCH (p:Principal)-[r:RAN]->(s)
WITH s, collect(DISTINCT split(p.id, '@')[0]) AS who, collect(DISTINCT p.kind) AS kinds, sum(r.jobs) AS jobs
RETURN s.id AS id, s.sample_sql AS sql, who, kinds, jobs, [(s)-[:REFERENCES]->(t:Table) WHERE t.in_catalog | t.id] AS tables
ORDER BY id
"""

# Tables only people write, never a production process (a load or a service account): sandboxes and
# personal copies, which an example query must not lead the writer to.
PERSONAL = """
MATCH (p:Principal)-[:RAN]->(:QueryShape {succeeded: true})-[:WRITES]->(t:Table)
WITH t, collect(DISTINCT p.kind) AS kinds WHERE NOT 'service_account' IN kinds
  AND NOT EXISTS { MATCH (:Principal {kind: 'service_account'})-[:LOADED]->(t) }
RETURN t.id AS t
"""

ALL_TABLES = "MATCH (t:Table) RETURN t.id AS t"

# The Computations closest to the question: what the business computes, as its queries define it.
# Only trusted ones (no sandbox or frozen table), and never one computed only by an excluded shape.
DEFINITIONS = """
CALL db.index.vector.queryNodes('computation_embedding', $pool, $v) YIELD node AS c, score
WHERE score >= $min AND c.trusted AND NOT c.health_check AND c.same_as IS NULL AND c.kind IN $kinds
  AND EXISTS { MATCH (s:QueryShape)-[:COMPUTES]->(c) WHERE NOT s.id IN $exclude }
RETURN c {.id, .name, .kind, .expression, .filters, .grain, .tables, .shapes, .production, .jobs} AS c, score
ORDER BY score DESC LIMIT $k
"""

# The designed models' terms linked to the cohort (qlsc align): catalog glossary terms its columns are
# bound to, and ontology classes its Variables or groups were matched to, closest to the question first.
# An experiment (navigate.concepts): designed models are aligned afterwards, not inputs to the method.
GLOSSARY = """
MATCH (t:Table)-[:HAS_COLUMN]->(col:Column) WHERE t.id IN $tables
OPTIONAL MATCH (col)-[:IS]->(v:Variable)
WITH collect(DISTINCT col) + [x IN collect(DISTINCT v) WHERE x IS NOT NULL]
     + COLLECT { MATCH (g:Semantic {level: 1}) WHERE g.name IN $groups RETURN g } AS xs
UNWIND xs AS x
MATCH (x)-[:MEANS]->(c:Concept) WHERE c.definition IS NOT NULL
WITH c, collect(DISTINCT CASE WHEN x:Column THEN x.id END)[..4] AS columns
RETURN c.name AS name, c.definition AS definition, c.source AS source, columns,
       vector.similarity.cosine(c.embedding, $v) AS sim
ORDER BY sim DESC, name LIMIT $k
"""

COLUMNS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.id IN $tables AND c.in_catalog
RETURN t.id AS t, collect({name: c.name, type: coalesce(c.type, '')}) AS cols
"""

# The values the log's queries filter each text column on, most-used first: the code values the
# business actually uses ('affluent', 'DEPOSIT'), so the LLM spells them as the data does.
FILTER_VALUES = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column {type: 'STRING'})<-[f:FILTERS]-(:QueryShape)
WHERE t.id IN $tables AND f.values IS NOT NULL
UNWIND f.values AS v
WITH t, c, v, count(*) AS shapes ORDER BY shapes DESC, v
RETURN t.id AS t, c.name AS c, collect(v)[..$n] AS vals
"""

# The columns the log's queries filter on a value, most-used first: a question's "affluent" leads to
# the segment column that holds it, whatever the question calls the column.
VALUE_COLUMNS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)<-[f:FILTERS]-(:QueryShape)
WHERE any(x IN f.values WHERE toLower(toString(x)) = toLower($value))
RETURN t.id AS t, c.name AS c, count(*) AS n ORDER BY n DESC, t LIMIT $k
"""

# The log's texts that truncate a column to weeks, for the week its queries mean (Sunday or Monday).
WEEK_TEXTS = """
MATCH (t:Table {id: $table})-[:HAS_COLUMN]->(c:Column {name: $column})<-[:READS]-(q:QueryShape)
WHERE toLower(q.sample_sql) CONTAINS 'week'
RETURN q.sample_sql AS sql
"""

# The trusted joins between some tables: identity-preserving, of a confidence that builds Variables,
# each with the join type most of the log's queries use for it. The compiler's paths run only along these.
TRUSTED_JOINS = """
MATCH (a:Table)-[:HAS_COLUMN]->(x:Column)<-[:ON]-(k:JoinKey)-[:ON]->(y:Column)<-[:HAS_COLUMN]-(b:Table)
WHERE a.id IN $tables AND b.id IN $tables AND a.id < b.id AND k.identity AND k.confidence IN $usable
OPTIONAL MATCH (:QueryShape)-[u:USES_JOIN]->(k)
WITH a.id AS a, x.name AS ac, b.id AS b, y.name AS bc, u.type AS type, count(u) AS n
ORDER BY a, ac, b, bc, n DESC, type
WITH a, ac, b, bc, collect(type)[0] AS type
RETURN a, ac, b, bc, coalesce(type, 'INNER') AS type
"""

# The tables `qlsc virtualize` made node labels.
LABELS = """
MATCH (t:Table) WHERE t.graph_label IS NOT NULL
RETURN t.id AS table, t.graph_label AS label
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


def cohort(
    G: Graph,
    v: list[float],
    p: dict,
    mode: str | None = None,
    rank: str | None = None,
    allow: entitle.Allowlist | None = None,
):
    """Steps 2-4: the level-1 groups to open, the tables whose own columns they hold, and the top tables.
    rank 'round_robin' (default) or 'usage' (most-queried first) -> (groups, tables, top table ids).
    With an allowlist, only the tables and columns it admits: a group partly readable is shown without
    its name, and an area above it that isn't wholly readable likewise."""
    mode, rank = mode or p["mode"], rank or p["rank"]
    rows = G.rows(DESCEND.format(pick=PICK[mode]), hits=p["hits"], groups=p["groups"], v=v)
    if allow is not None:
        kept = [r for r in rows if allow.column(r["table"], r["column"])]
        partly = {r["grp"] for r in rows if not allow.column(r["table"], r["column"])}  # lost a member
        alias = {g: f"(a group you can partly read, {i + 1})" for i, g in enumerate(sorted(partly))}
        rows = [
            r
            | {
                "grp": alias.get(r["grp"], r["grp"]),
                "via": [
                    x if allow.semantics.get(x) == "all" else "(an area you can partly read)"
                    for x in r["via"]
                ],
            }
            for r in kept
        ]
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


def filter_values(G: Graph, tables: list[str], n: int, allow: entitle.Allowlist | None = None) -> dict:
    """{(table, column): the values the log filters it on}; with an allowlist, never a tagged column's."""
    out = {(r["t"], r["c"]): r["vals"] for r in G.rows(FILTER_VALUES, tables=tables, n=n)}
    return out if allow is None else {k: v for k, v in out.items() if allow.shown(*k)}


def columns(G: Graph, tables: list[str], allow: entitle.Allowlist | None = None) -> list[dict]:
    """COLUMNS for some tables; with an allowlist, only readable tables and their readable columns."""
    rows = G.rows(COLUMNS, tables=tables)
    if allow is None:
        return rows
    return [
        r | {"cols": [c for c in r["cols"] if allow.column(r["t"], c["name"])]}
        for r in rows
        if allow.readable(r["t"])
    ]


def column_text(name: str, typ: str, values: list | None) -> str:
    """A column for the prompt: its name and type, and the values the log filters it on."""
    seen = f" (values seen: {', '.join(repr(v) for v in values)})" if values else ""
    return f"{name} {typ}".strip() + seen


def definitions_text(definitions: list[dict], kind: str) -> str:
    """The Computations for the prompt, after the examples; nothing at all when there are none, so a
    request without them is the same text as before they existed."""
    if not definitions:
        return ""
    lines = [
        f"\n\nHow the {kind}'s queries compute some things near this question. Use one only if it computes "
        "exactly what the question asks; otherwise ignore it and write your own:"
    ]
    for d in definitions:
        with_ = f", with {' AND '.join(d['filters'])}" if d["filters"] else ""
        who = "production" if d["production"] else "people"
        lines.append(
            f"- {d['name']} ({d['kind']}): {d['expression']}{with_}; on {', '.join(d['tables'])}; "
            f"{d['shapes']} queries, {who}"
        )
    return "\n".join(lines)


def glossary_text(terms: list[dict]) -> str:
    """The designed models' terms for the prompt; nothing at all when there are none."""
    if not terms:
        return ""
    lines = ["\n\nBusiness terms from the catalog and the ontology, for what the words in the question mean:"]
    for t in terms:
        cols = (
            f" (columns: {', '.join(short(c.rsplit('.', 1)[0]) + '.' + c.rsplit('.', 1)[1] for c in t['columns'])})"
            if t["columns"]
            else ""
        )
        lines.append(f"- {t['name']}: {t['definition']}{cols}")
    return "\n".join(lines)


def example_sql(examples: list[dict]) -> str:
    return "\n\n".join(" ".join(q["sql"].split())[:1500] for q in examples) or "(none)"


def model_slice(schema: dict, labels: list[str]) -> tuple[list[dict], list[dict]]:
    """The part of a Virtual Graph model (schema.json) around some labels: those labels, every
    relationship that starts or ends at one of them, and the labels at its other end."""
    ents = schema["entities"]
    rels = [
        r
        for r in ents["relationships"]
        if r["start"]["targetEntity"] in labels or r["end"]["targetEntity"] in labels
    ]
    near = set(labels) | {r[side]["targetEntity"] for r in rels for side in ("start", "end")}
    nodes = [n for n in ents["nodes"] if n["label"] in near]
    order = {label: i for i, label in enumerate(labels)}  # the cohort's labels first, in its order
    nodes.sort(key=lambda n: (order.get(n["label"], len(order)), n["label"]))
    return nodes, sorted(rels, key=lambda r: r["label"])


def external_sql(plan: dict) -> list[str]:
    """The SQL in a Virtual Graph plan: what its External operators send to the warehouse."""
    out = [plan["args"]["Details"]] if plan["operatorType"].startswith("External") else []
    for child in plan.get("children", []):
        out += external_sql(child)
    return out


def calendar(today: dt.date) -> str:
    """Today and the calendar periods questions name, as dates: Virtual Graph Cypher can't compute them."""

    def month(d: dt.date, back: int) -> dt.date:
        m = d.year * 12 + d.month - 1 - back
        return dt.date(m // 12, m % 12 + 1, 1)

    q = month(today, (today.month - 1) % 3)  # this quarter's first day
    last = lambda start, end: f"{start.isoformat()} to {(end - dt.timedelta(days=1)).isoformat()}"
    y = dt.date(today.year, 1, 1)
    return (
        f"{today.isoformat()}. Last month: {last(month(today, 1), month(today, 0))}; last quarter: "
        f"{last(month(q, 3), q)}; last year: {last(dt.date(today.year - 1, 1, 1), y)}; this year so far: "
        f"{y.isoformat()} to {today.isoformat()}."
    )


def today(s: Settings) -> dt.date:
    """The date questions are asked on: the estate's pinned date, else the real one."""
    pinned = s.params["navigate"]["today"]
    return dt.date.fromisoformat(str(pinned)) if pinned else dt.date.today()


def cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float | Decimal):
        return f"{float(v):,.2f}"
    return str(v)


def show(columns: list[str], rows: list[dict], total: int, where: str) -> None:
    """The answer as a table: the first rows, and how many there are."""
    table = [[cell(r.get(c)) for c in columns] for r in rows]
    width = [min(40, max([len(c)] + [len(x[i]) for x in table])) for i, c in enumerate(columns)]
    print("   " + "  ".join(c[:w].ljust(w) for c, w in zip(columns, width)))
    print("   " + "  ".join("-" * w for w in width))
    for x in table:
        print(
            "   " + "  ".join(v[:w].rjust(w) if v[:1].isdigit() else v[:w].ljust(w) for v, w in zip(x, width))
        )
    print(f"   {total:,} rows{f' (the first {len(rows)} shown)' if total > len(rows) else ''}, {where}")


def shape_text(sql: str, chars: int) -> str:
    """A query's SQL as it is embedded: comments (dbt and Looker headers) removed, whitespace folded."""
    sql = re.sub(r"--[^\n]*", " ", re.sub(r"/\*.*?\*/", " ", sql, flags=re.S))
    return " ".join(sql.split())[:chars]


def similar(
    v: list[float], shapes: list[dict], vecs: list, distrusted: set[str], k: int, keep: set[str] | None = None
) -> list[dict]:
    """The k query shapes closest to the question that read no distrusted table (and, with `keep`, are
    among those), closest first."""
    out = []
    for sh, vec in sorted(zip(shapes, vecs), key=lambda x: (-cosine(v, x[1]), x[0]["id"])):
        if not set(sh["tables"]) & distrusted and (keep is None or sh["id"] in keep):
            out.append({**sh, "similarity": cosine(v, vec)})
            if len(out) == k:
                break
    return out


def decompose(s: Settings, question: str) -> dict:
    """The question's parts: measures, groupings, filters (subject and value), entities, period."""
    llm = LLM(prompt("decompose_system", **s.business), s)
    return llm.call(question, DECOMPOSE_SCHEMA, "record_parts", max_tokens=800)


def merge_cohorts(found: list[tuple[dict, dict, list[str]]], k: int) -> tuple[dict, dict, list[str]]:
    """Several anchors' cohorts as one: groups and tables pooled, the top tables taken from each
    anchor's list in turn, so every part of the question is represented."""
    groups, tables, top = {}, {}, []
    for g, t, _ in found:
        for name, x in g.items():
            groups.setdefault(name, x)
        for tid, x in t.items():
            tables.setdefault(tid, x)
    queues = [list(t) for _, _, t in found]
    while len(top) < k and any(queues):
        for q in queues:
            while q and q[0] in top:
                q.pop(0)
            if q and len(top) < k:
                top.append(q.pop(0))
    return groups, tables, top


def trace(
    G: Graph,
    s: Settings,
    question: str,
    exclude: frozenset[str] = frozenset(),
    allow: entitle.Allowlist | None = None,
) -> dict:
    """Steps 1-4, deterministic: the closest Semantic nodes, the groups opened, the cohort of tables,
    the log's queries closest to the question (and the tables they read), and the joins between them.
    `exclude` names query shapes never to offer as examples (an evaluation leaves out the query a
    question was written from).

    `anchors: parts` breaks the question into its parts first (an LLM call, prompts/decompose_system.md),
    and navigates from each part: every entity, grouping, measure and filter subject opens its own
    groups; every filter value finds the columns the log filters on it; every measure finds the measure
    Computations closest to it.

    `allow` (the entitlement gateway, qlsc/entitle.py) restricts everything to what a principal may read,
    and the answer then runs as them."""
    p = s.params["navigate"]
    emb = Embedder(s)
    v = emb.embed([question])[0]
    parts, value_tables = None, []
    kinds = ["measure", "dimension", "population"]
    definitions = []
    if p["anchors"] == "parts":
        parts = decompose(s, question)
        texts = (
            parts["entities"]
            + parts["groupings"]
            + parts["measures"]
            + [f["subject"] for f in parts["filters"]]
        )
        vecs = emb.embed(texts) if texts else []
        small = {**p, "groups": p["anchor_groups"], "tables": p["anchor_tables"]}
        found = [cohort(G, x, small, allow=allow) for x in vecs] or [cohort(G, v, p, allow=allow)]
        groups, tables, top = merge_cohorts(found, p["tables"])
        for f in parts["filters"]:
            for r in G.rows(VALUE_COLUMNS, value=f["value"], k=p["anchor_values"]):
                if r["t"] not in top + value_tables and (allow is None or allow.readable(r["t"])):
                    value_tables.append(r["t"])
        if p["computations"]:
            per = [(m, "measure") for m in parts["measures"]] + [
                (f["subject"] + " " + f["value"], "population") for f in parts["filters"]
            ]
            pvecs = emb.embed([t for t, _ in per]) if per else []
            for (_, kind), x in zip(per, pvecs):
                for r in G.rows(
                    DEFINITIONS,
                    pool=50,
                    k=p["anchor_computations"],
                    v=x,
                    kinds=[kind],
                    exclude=sorted(exclude),
                    min=p["computation_min_similarity"],
                ):
                    if r["c"]["id"] not in {d["id"] for d in definitions}:
                        definitions.append(r["c"] | {"similarity": r["score"]})
            definitions = definitions[: p["computations"]]
    else:
        groups, tables, top = cohort(G, v, p, allow=allow)
        if p["computations"]:
            definitions = [
                r["c"] | {"similarity": r["score"]}
                for r in G.rows(
                    DEFINITIONS,
                    pool=p["computations"] * 10,
                    k=p["computations"],
                    v=v,
                    kinds=kinds,
                    exclude=sorted(exclude),
                    min=p["computation_min_similarity"],
                )
            ]
    if p["examples_by"] == "similarity":
        shapes = [x for x in G.rows(SHAPES, statements=p["example_statements"]) if x["id"] not in exclude]
        vecs = emb.embed([shape_text(x["sql"], p["example_chars"]) for x in shapes])
        everything = [r["t"] for r in G.rows(ALL_TABLES)]
        distrusted = {r["t"] for r in G.rows(PERSONAL)} | {r["t"] for r in G.rows(FROZEN, tables=everything)}
        keep = entitle.readable_shapes(G, allow, shapes) if allow else None
        examples = similar(v, shapes, vecs, distrusted, p["examples"], keep)
    else:
        examples = G.rows(QUERIES, tables=top, n=p["examples"] * (3 if allow else 1))
        if allow:
            keep = entitle.readable_shapes(G, allow, examples)
            examples = [e for e in examples if e["id"] in keep][: p["examples"]]
    if allow:  # who ran a query, as a kind of principal, never a name
        examples = [e | {"who": e["kinds"]} for e in examples]
        definitions = [d for d in definitions if entitle.computation_ok(allow, d)]
    added = list(value_tables)
    if p["example_tables"]:
        added += [
            t for t in dict.fromkeys(t for e in examples for t in e.get("tables", [])) if t not in top + added
        ]
    if p["computation_tables"]:
        added += [
            t for t in dict.fromkeys(t for d in definitions for t in d["tables"]) if t not in top + added
        ]
    glossary = []
    if p["concepts"]:
        glossary = G.rows(GLOSSARY, tables=top + added, groups=list(groups), v=v, k=p["concepts"])
    hits, joins = G.rows(HITS, hits=p["hits"], v=v), G.rows(JOINS, tables=top + added)
    if allow:
        added = [t for t in added if allow.readable(t)]
        hits = [
            h if allow.semantics.get(h["name"]) == "all" else h | {"name": "(an area you can partly read)"}
            for h in hits
            if allow.semantics.get(h["name"], "none") != "none"
        ]
        joins = [j for j in joins if allow.column(j["a"], j["ac"]) and allow.column(j["b"], j["bc"])]
        glossary = [
            g | {"columns": [c for c in g["columns"] if allow.column(*c.rsplit(".", 1))]} for g in glossary
        ]
    return {
        "question": question,
        "exclude": sorted(exclude),
        "glossary": glossary,
        "parts": parts,
        "hits": hits,
        "groups": groups,
        "tables": tables,
        "cohort": top,
        "added": added,
        "top": top + added,
        "joins": joins,
        "examples": examples,
        "definitions": definitions,
        "allow": allow,
    }


def answer_sql(G: Graph, s: Settings, tr: dict, execute: bool = False, rows: int | None = None) -> dict:
    """Step 6, by the writer configured (navigate.writer): the compiler, falling back to free SQL when
    the question doesn't compile; or free SQL. -> {writer, sql, explanation, dry_run, result?, ...}"""
    if s.params["navigate"]["writer"] == "compiled":
        out = answer_compiled(G, s, tr, execute, rows)
        if "sql" in out:
            return out
        return answer_free(G, s, tr, execute, rows) | {
            "writer": "free",
            "fallback": out["fallback"],
            "request": out.get("request"),
        }
    return answer_free(G, s, tr, execute, rows) | {"writer": "free"}


def unique_check(s: Settings):
    """`unique(table, column)`, from the warehouse, cached in <work>/unique_cache.json."""
    path = s.work / "unique_cache.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    wh = connect(s)

    def unique(table: str, column: str) -> bool:
        key = f"{table}|{column}"
        if key not in cache:
            cache[key] = wh.is_unique(table, [column])
            path.write_text(json.dumps(cache, indent=0, sort_keys=True))
        return cache[key]

    return unique


def compiled_request(G: Graph, s: Settings, tr: dict) -> tuple[dict, compiler.Catalogue, list[str]]:
    """The typed request for a question (qlsc/compile.py), the LLM choosing from the layer's options:
    the cohort's tables, the closest Computations and the tables they read, the trusted joins. One LLM
    call, cached, whichever route it is compiled for; with navigate.compile_checks, a second when the
    checks find something, and a week grain set as the log truncates the column.
    -> (request, catalogue, what the checks found and changed)"""
    p = s.params["navigate"]
    v = Embedder(s).embed([tr["question"]])[0]
    offered = {
        r["c"]["id"]: r["c"]
        for r in G.rows(
            DEFINITIONS,
            pool=p["compile_computations"] * 10,
            k=p["compile_computations"],
            v=v,
            kinds=["measure", "dimension", "population"],
            exclude=tr.get("exclude", []),
            min=p["computation_min_similarity"],
        )
    }
    allow = tr.get("allow")
    if allow:
        offered = {k: c for k, c in offered.items() if entitle.computation_ok(allow, c)}
    ids = list(dict.fromkeys(tr["top"] + [t for c in offered.values() for t in c["tables"]]))
    tables = {r["t"]: {c["name"]: c["type"] for c in r["cols"]} for r in columns(G, ids, allow)}
    offered = {k: c for k, c in offered.items() if set(c["tables"]) <= set(tables)}
    joins = G.rows(TRUSTED_JOINS, tables=list(tables), usable=s.params["variables"]["joins"])
    if allow:
        joins = [j for j in joins if allow.column(j["a"], j["ac"]) and allow.column(j["b"], j["bc"])]
    cat = compiler.Catalogue(tables, joins, offered)
    llm = LLM(prompt("compile_system", **s.business), s, s["llm"]["query_model"])
    values = filter_values(G, list(tables), p["filter_values"], allow)
    text = prompt(
        "compile_request",
        question=tr["question"],
        today=calendar(today(s)),
        tables=compiler.options_text(cat, values, {r["t"] for r in G.rows(FROZEN, tables=list(tables))}),
        joins=compiler.joins_text(joins),
        computations=compiler.computations_text(cat),
        examples=example_sql(tr["examples"]),
        **s.business,
    )
    request = llm.call(text, compiler.SCHEMA, "record_request", max_tokens=3000)
    found: list[str] = []
    if p["compile_checks"]:
        found = compiler.check(request, cat, tr["question"], values, p["compile_check_chars"])
        if found:
            retry = prompt("compile_check", notes="\n".join(f"- {n}" for n in found))
            request = llm.call(text + "\n\n" + retry, compiler.SCHEMA, "record_request", max_tokens=3000)
        usage = lambda t, col: compiler.week_usage(
            [r["sql"] for r in G.rows(WEEK_TEXTS, table=t, column=col)], col
        )
        found += compiler.weeks(request, cat, usage, tr["question"])
        found += compiler.open_period(request, today(s).isoformat(), tr["question"])
    return request, cat, found


def answer_compiled(G: Graph, s: Settings, tr: dict, execute: bool = False, rows: int | None = None) -> dict:
    """The compiler (qlsc/compile.py): the LLM fills a typed request from the layer's options, code
    compiles it. -> {writer: compiled, request, sql, ...} | {fallback: why, request?}"""
    p = s.params["navigate"]
    wh = entitle.warehouse(s, tr.get("allow"))
    request, cat, found = compiled_request(G, s, tr)
    try:
        sql = compiler.compile_sql(request, cat, unique_check(s), dialect=wh.dialect, hops=p["compile_hops"])
    except compiler.Unfit as e:
        return {"fallback": str(e), "request": request, "checks": found}
    res = wh.dry_run(sql)
    if res["ok"] is False:
        return {"fallback": f"the compiled SQL failed its dry run: {res['error'][:200]}", "request": request}
    answer = {
        "writer": "compiled",
        "warehouse": wh.name,
        "request": request,
        "sql": sql,
        "explanation": request.get("reason", ""),
        "checks": found,
        "dry_run": res,
    }
    if execute and res["ok"]:
        t0 = time.time()
        answer["result"] = wh.run(sql, p["maximum_bytes_billed"], rows or p["rows_shown"])
        answer["result"]["seconds"] = time.time() - t0
    return answer


def answer_free(G: Graph, s: Settings, tr: dict, execute: bool = False, rows: int | None = None) -> dict:
    """Step 6: the cohort -> one query, dry-run in the warehouse; step 7, the answer, with `execute`.
    -> {sql, explanation, dry_run, result?}"""
    p = s.params["navigate"]
    wh = entitle.warehouse(s, tr.get("allow"))
    top = tr["top"]
    cols = columns(G, top, tr.get("allow"))
    values = filter_values(G, top, p["filter_values"], tr.get("allow"))
    tables = "\n".join(
        f"`{r['t']}`: "
        + ", ".join(
            column_text(c["name"], c["type"], values.get((r["t"], c["name"]))) for c in r["cols"][:60]
        )
        for r in cols
    )
    joins_txt = (
        "\n".join(f"{j['a']}.{j['ac']} = {j['b']}.{j['bc']}" for j in tr["joins"]) or "(none recorded)"
    )
    llm = LLM(prompt("sql_system", sql=wh.sql, **s.business), s, s["llm"]["query_model"])
    request = prompt(
        "sql_request",
        question=tr["question"],
        tables=tables,
        joins=joins_txt,
        examples=example_sql(tr["examples"]),
        definitions=definitions_text(tr.get("definitions", []), s.business["kind"]),
        glossary=glossary_text(tr.get("glossary", [])),
        today=calendar(today(s)),
        **s.business,
    )
    out = llm.call(request, SQL_SCHEMA, "record_sql", max_tokens=3000)
    res = wh.dry_run(out["sql"])
    if res["ok"] is False:
        fix = prompt("sql_fix", error=res["error"], warehouse=wh.name)
        out = llm.call(request + "\n\n" + fix, SQL_SCHEMA, "record_sql", max_tokens=3000)
        res = wh.dry_run(out["sql"])
    answer = {"warehouse": wh.name, "sql": out["sql"], "explanation": out["explanation"], "dry_run": res}
    if execute and res["ok"]:
        t0 = time.time()
        answer["result"] = wh.run(out["sql"], p["maximum_bytes_billed"], rows or p["rows_shown"])
        answer["result"]["seconds"] = time.time() - t0
    return answer


def refused(s: Settings, tr: dict, cypher: str, check: dict, labels: dict[str, str]) -> str | None:
    """Why the gateway won't let the virtual graph answer this principal (entitle.check_cypher), or None."""
    allow = tr.get("allow")
    if allow is None or "error" in check:
        return None
    table = {label: t for t, label in labels.items()}
    named = {x for x in re.findall(r"\(\s*\w*\s*:\s*(\w+)", cypher) if x in table}
    return entitle.check_cypher(s, allow, sorted(table[x] for x in named), check["sql"])


def answered(a: dict) -> bool:
    """Whether a route gave an answer: not declined, refused or skipped, and its query checked (and ran)."""
    if any(k in a for k in ("skipped", "declined", "refused", "error")) or "error" in a.get("check", {}):
        return False
    return (a.get("result") or {}).get("ok", True) is not False and bool(a.get("sql") or a.get("cypher"))


def pick(sql: dict, cypher: dict | None) -> str:
    """The router's rule (plans/2026-09-26-router.md, as revised): the compiled SQL when the question
    compiles, since compiled Cypher is the same plan with less (no outer join's null group, no HAVING
    pushed down); otherwise free Cypher when it answers, which reaches the neighbourhoods and paths a
    request can't express; otherwise free SQL. -> 'sql' | 'cypher'"""
    if sql.get("writer") == "compiled":
        return "sql"
    return "cypher" if cypher is not None and answered(cypher) else "sql"


def answer_routed(G: Graph, s: Settings, tr: dict, execute: bool = False, rows: int | None = None) -> dict:
    """Step 6 by the router (`pick`), running only what it needs: the compiled SQL; failing that, free
    Cypher; failing that, free SQL. -> the chosen route's answer, with `route`."""
    if s.params["navigate"]["writer"] == "compiled":
        a = answer_compiled(G, s, tr, execute, rows)
        if "sql" in a:
            return a | {"route": "sql"}
        fallback = {"fallback": a["fallback"], "request": a.get("request")}
    else:
        fallback = {}
    c = answer_cypher(G, s, tr, execute, rows, writer="free")
    if pick({}, c) == "cypher":
        return c | fallback | {"route": "cypher"}
    return answer_free(G, s, tr, execute, rows) | {"writer": "free", "route": "sql"} | fallback


def answer_cypher(
    G: Graph, s: Settings, tr: dict, execute: bool = False, rows: int | None = None, writer: str | None = None
) -> dict:
    """Step 6 over the virtual graph, by the writer configured (navigate.writer): the compiler, falling
    back to free Cypher when the question doesn't compile; or free Cypher, from the cohort's labels.
    Checked with Virtual Graph's EXPLAIN; step 7, the answer, with `execute`.
    -> {writer, start, around, cypher, explanation, check, result?} | {skipped: why}
       | {start, around, declined: why}"""
    p, instance = s.params["navigate"], s.get("virtualize", {}).get("neo4j")
    labels = {r["table"]: r["label"] for r in G.rows(LABELS)}
    path = s.work / "virtual" / "schema.json"
    if not (labels and instance and path.exists()):
        return {"skipped": "no virtual graph: run qlsc virtualize, and set virtualize.neo4j in the config"}
    model = json.loads(path.read_text())
    if allow := tr.get("allow"):  # the labels, properties and relationships the principal may read
        labels = {t: label for t, label in labels.items() if allow.readable(t)}
        model = model | {"entities": entitle.model(allow, model["entities"], labels)}
    start = [labels[t] for t in tr["top"] if t in labels]
    if not start:
        return {"skipped": "none of the cohort's tables is in the virtual graph"}
    fallback = {}
    if (writer or p["writer"]) == "compiled":
        out = cypher_compiled(G, s, tr, labels, model["entities"], instance, execute, rows)
        if "fallback" not in out:
            return out
        fallback = {"fallback": out["fallback"], "request": out.get("request")}
    return (
        cypher_free(G, s, tr, labels, model, start, instance, execute, rows) | {"writer": "free"} | fallback
    )


def cypher_compiled(
    G: Graph,
    s: Settings,
    tr: dict,
    labels: dict,
    model: dict,
    instance: dict,
    execute: bool,
    rows: int | None,
) -> dict:
    """The compiler's Cypher: the same request as the SQL route's, over the Virtual Graph model.
    -> {writer: compiled, request, cypher, check, result?} | {fallback: why, request?}"""
    p = s.params["navigate"]
    request, cat, found = compiled_request(G, s, tr)
    try:
        cypher = compiler.compile_cypher(request, cat, unique_check(s), labels, model, hops=p["compile_hops"])
    except compiler.Unfit as e:
        return {"fallback": str(e), "request": request}
    named = re.findall(r"\(\w+:(\w+)\)", cypher)
    table = {label: t for t, label in labels.items()}
    answer = {
        "writer": "compiled",
        "warehouse": connect(s).name,
        "request": request,
        "start": [(x, table[x]) for x in dict.fromkeys(named)],
        "around": [],
        "cypher": cypher,
        "explanation": request.get("reason", ""),
        "checks": found,
    }
    try:
        with Graph(s, instance) as V:
            check = explain(V, cypher, model["nodes"], model["relationships"])
            if "error" in check:
                return {
                    "fallback": f"the compiled Cypher failed its check: {check['error'][:200]}",
                    "request": request,
                }
            answer["check"] = check
            if why := refused(s, tr, cypher, check, labels):
                return answer | {"refused": why}
            if execute:
                answer["result"] = capped_result(V, cypher, p, rows)
    except ServiceUnavailable:
        answer["error"] = f"the Virtual Graph instance is not running at {instance['uri']}"
    except Neo4jError as e:
        answer["error"] = e.message
    return answer


def capped_result(V: Graph, cypher: str, p: dict, rows: int | None) -> dict:
    t0 = time.time()
    columns, data, more = V.capped(cypher, p["cypher_max_rows"])
    return {
        "ok": True,
        "columns": columns,
        "rows": data[: rows or p["rows_shown"]],
        "total": len(data),
        "truncated": more,
        "seconds": time.time() - t0,
    }


def cypher_free(
    G: Graph,
    s: Settings,
    tr: dict,
    labels: dict,
    model: dict,
    start: list[str],
    instance: dict,
    execute: bool,
    rows: int | None,
) -> dict:
    """The LLM writes Cypher from the cohort's labels and one hop around them."""
    p = s.params["navigate"]
    nodes, rels = model_slice(model, start)
    table = {label: t for t, label in labels.items()}
    values = filter_values(
        G, [table[n["label"]] for n in nodes if n["label"] in table], p["filter_values"], tr.get("allow")
    )
    node_txt = "\n".join(
        f"(:{n['label']}) rows of `{table.get(n['label'], n['table'])}`, key {n['key'][0]['column']}: "
        + ", ".join(
            column_text(x["name"], x["type"], values.get((table.get(n["label"]), x["column"])))
            for x in n["properties"][:60]
        )
        for n in nodes
    )
    rel_txt = "\n".join(
        f"(:{r['start']['targetEntity']})-[:{r['label']}]->(:{r['end']['targetEntity']})  "
        f"({r['start']['targetEntity']}.{r['end']['keys'][0]['relationshipColumn']} = "
        f"{r['end']['targetEntity']}.{r['end']['keys'][0]['nodeColumn']})"
        for r in rels
    )
    llm = LLM(prompt("cypher_system", **s.business), s, s["llm"]["query_model"])
    request = prompt(
        "cypher_request",
        question=tr["question"],
        nodes=node_txt,
        relationships=rel_txt or "(none)",
        examples=example_sql(tr["examples"]),
        definitions=definitions_text(tr.get("definitions", []), s.business["kind"]),
        glossary=glossary_text(tr.get("glossary", [])),
        today=calendar(today(s)),  # Virtual Graph has no date(): relative periods need literals
        **s.business,
    )
    answer = {
        "warehouse": connect(s).name,
        "start": [(x, table[x]) for x in start],
        "around": [n["label"] for n in nodes if n["label"] not in start],
    }
    try:
        with Graph(s, instance) as V:
            out = llm.call(request, CYPHER_SCHEMA, "record_cypher", max_tokens=3000)
            if not out["answerable"]:
                return answer | {"declined": out["explanation"]}
            check = explain(V, out["cypher"], nodes, rels)
            if "error" in check:
                fix = prompt("cypher_fix", error=check["error"])
                out = llm.call(request + "\n\n" + fix, CYPHER_SCHEMA, "record_cypher", max_tokens=3000)
                check = explain(V, out["cypher"], nodes, rels)
            answer |= {"cypher": out["cypher"], "explanation": out["explanation"], "check": check}
            if why := refused(s, tr, out["cypher"], check, labels):
                return answer | {"refused": why}
            if execute and "error" not in check:
                answer["result"] = capped_result(V, out["cypher"], p, rows)
    except ServiceUnavailable:
        answer["error"] = f"the Virtual Graph instance is not running at {instance['uri']}"
    except Neo4jError as e:
        answer["error"] = e.message
    return answer


def print_trace(tr: dict) -> None:
    print(f"QUESTION  {tr['question']}\n")
    print("1. semantic layer: closest Semantic nodes (any level)")
    for h in tr["hits"]:
        print(f"   {h['score']:.3f}  L{h['level']}  {h['name']}")
    print("\n2. down to the level-1 groups under those hits, closest first")
    for name, g in tr["groups"].items():
        print(f"   {g['sim']:.3f}  {name}  (under: {', '.join(g['via'])})")
        print("          " + textwrap.shorten(", ".join(sorted(g["members"])), 150))
    tables, top = tr["tables"], tr.get("cohort", tr["top"])
    print(
        f"\n3. down to the physical layer: the cohort ({len(top)} of {len(tables)} tables; each group, "
        "closest first, contributes its most-used table in turn; frozen tables last)"
    )
    for t in top:
        cols = textwrap.shorten(", ".join(sorted(tables[t]["cols"])), 80)
        print(
            f"   {short(t):46} {tables[t]['used']:2} principals{' FROZEN' if tables[t]['frozen'] else ''}  {cols}"
        )
    if tr.get("added"):
        print("   + read by the example queries below: " + ", ".join(short(t) for t in tr["added"]))
    print("\n4. how the log connects them")
    for j in tr["joins"]:
        print(
            f"   join  {short(j['a'])}.{j['ac']} = {short(j['b'])}.{j['bc']}"
            + (f"  [{j['variable']}]" if j["variable"] else "")
            + f"  ({j['queries']} queries)"
        )
    for q in tr["examples"]:
        if "similarity" in q:
            print(
                f"\n   a query {q['similarity']:.2f} like the question, {q['jobs']} runs by "
                f"{', '.join(q['who'][:4])}, reads {', '.join(short(t) for t in q['tables'][:4])}:"
            )
        else:
            print(
                f"\n   a query that reads {q['hit']} of them, {q['jobs']} runs by {', '.join(q['who'][:4])}:"
            )
        print(textwrap.indent(textwrap.shorten(" ".join(q["sql"].split()), 600), "     "))


def print_sql(a: dict) -> None:
    res = a["dry_run"]
    print(f"\n5. the SQL (written from the cohort above, dry-run in {a['warehouse']})")
    print(textwrap.indent(a["sql"].strip(), "   "))
    print("\n   " + textwrap.fill(a["explanation"], 100, subsequent_indent="   "))
    if res["ok"]:
        print(f"   dry run: valid; would scan {res.get('bytes_processed') or 0:,} bytes")
    elif res["ok"] is None:
        print(f"   dry run skipped: {res['error']}")
    else:
        print(f"   dry run failed: {res['error']}")
    if "result" in a:
        out = a["result"]
        print(f"\n6. the answer (run in {a['warehouse']})")
        if out["ok"]:
            where = f"{out['seconds']:.1f} s, {out['bytes_billed'] / 2**20:,.0f} MiB billed"
            show(out["columns"], out["rows"], out["total"], where)
        else:
            print(f"   failed: {out['error']}")


def print_cypher(a: dict) -> None:
    print("\n5. the virtual graph: the cohort's tables that are labels there, and one hop around them")
    if "skipped" in a:
        print(f"   {a['skipped']}")
        return
    print("   " + ", ".join(f"{x} ({short(t)})" for x, t in a["start"]))
    if a["around"]:
        print("   one hop: " + ", ".join(a["around"]))
    if "refused" in a:
        print("\n6. no Cypher for this principal: the gateway refused it (entitlements)")
        print("   " + textwrap.fill(a["refused"], 100, subsequent_indent="   "))
    if "declined" in a:
        print("\n6. no Cypher: the writer found the graph can't answer this")
        print("   " + textwrap.fill(a["declined"], 100, subsequent_indent="   "))
    if "cypher" in a:
        print("\n6. the Cypher (written from the labels above, checked with Virtual Graph's EXPLAIN)")
        print(textwrap.indent(a["cypher"].strip(), "   "))
        print("\n   " + textwrap.fill(a["explanation"], 100, subsequent_indent="   "))
        if "error" in a["check"]:
            print(f"   EXPLAIN failed: {a['check']['error']}")
        else:
            print(
                f"\n   the SQL Virtual Graph sends to {a['warehouse']} (? are the query's literals, as parameters):"
            )
            for q in a["check"]["sql"]:
                print(textwrap.indent(q.strip(), "     "))
    if "result" in a:
        out = a["result"]
        print(f"\n7. the answer (run through Virtual Graph, in {a['warehouse']})")
        show(out["columns"], out["rows"], out["total"], f"{out['seconds']:.1f} s")
    if "error" in a:
        print(f"   failed: {a['error']}")


def unknown_properties(cypher: str, nodes: list[dict]) -> list[str]:
    """Properties a query reads that its variable's label does not have. Cypher returns null for a
    missing property, so Virtual Graph accepts them and the answer silently loses a column."""
    have = {n["label"]: {x["name"] for x in n["properties"]} for n in nodes}
    bound = {v: label for v, label in re.findall(r"\((\w+):(\w+)", cypher) if label in have}
    return sorted(
        {
            f"{v}.{prop} ({bound[v]} has no {prop})"
            for v, prop in re.findall(r"\b(\w+)\.(\w+)\b", cypher)
            if v in bound and prop not in have[bound[v]]
        }
    )


def unknown_names(cypher: str, nodes: list[dict], rels: list[dict]) -> list[str]:
    """Labels and relationship types a query names that the graph given lacks. Virtual Graph runs a
    pattern over a label it doesn't have and returns no rows, so the answer is silently empty."""
    labels, types = {n["label"] for n in nodes}, {r["label"] for r in rels}
    named = {x for g in re.findall(r"\(\s*\w*\s*((?::\s*\w+\s*)+)", cypher) for x in re.findall(r"\w+", g)}
    named |= set(re.findall(r"\b\w+:(\w+)\b(?!\s*[:(])", re.sub(r"\([^()]*\)|\[[^\]]*\]", "", cypher)))
    rel_named = {x for g in re.findall(r"\[\s*\w*\s*:\s*([\w|:\s]+)", cypher) for x in re.findall(r"\w+", g)}
    return sorted(f"label {x}" for x in named - labels) + sorted(
        f"relationship type {x}" for x in rel_named - types
    )


# What Virtual Graph's Cypher subset rejects, found before EXPLAIN so the retry gets a precise reason.
SUBSET = [
    (
        re.compile(r"\bOPTIONAL\s+MATCH\b", re.I),
        "OPTIONAL MATCH is not supported: use MATCH, or group by the pointing column's property on the start node",
    ),
    (
        re.compile(r"\[[^\]]*\*[^\]]*\]"),
        "variable-length relationships (*) are not supported: write each hop out",
    ),
    (re.compile(r"\bCALL\s*(\(|\{)", re.I), "CALL subqueries are not supported"),
    (re.compile(r"\bEXISTS\s*\{", re.I), "EXISTS subqueries are not supported: MATCH the pattern instead"),
    (re.compile(r"\bUNION\b", re.I), "UNION is not supported"),
    (
        re.compile(r"\b(date|datetime|localdatetime|duration)\s*\(\s*\)", re.I),
        "date() and the like have no current date here: use a literal date('YYYY-MM-DD') from the calendar",
    ),
]


def subset_errors(cypher: str) -> list[str]:
    """Constructs Virtual Graph's subset rejects: the table above, and a MATCH after the first WITH."""
    text = re.sub(r"'[^']*'|\"[^\"]*\"|//[^\n]*", "''", cypher)  # never match inside a literal or a comment
    out = [msg for pattern, msg in SUBSET if pattern.search(text)]
    clauses = re.split(r"\b(?=(?:MATCH|WITH|RETURN|WHERE|ORDER\s+BY|UNWIND)\b)", text, flags=re.I)
    seen_with = False
    for c in clauses:
        head = c.strip().split(None, 1)[0].upper() if c.strip() else ""
        if head == "WITH":
            seen_with = True  # an aggregating WITH is left to EXPLAIN: Virtual Graph runs some forms of it
        elif head == "MATCH" and seen_with:
            out.append("every MATCH must come before the first WITH")
    return list(dict.fromkeys(out))


def wrong_directions(cypher: str, nodes: list[dict], rels: list[dict]) -> list[str]:
    """Relationships a query walks against the direction the model gives them. Virtual Graph finds no
    rows for a reversed pattern, so the answer would be silently empty."""
    labels = {n["label"] for n in nodes}
    bound = {v: label for v, label in re.findall(r"\((\w+)\s*:\s*(\w+)", cypher) if label in labels}
    ends = {r["label"]: (r["start"]["targetEntity"], r["end"]["targetEntity"]) for r in rels}
    node = r"\(\s*(\w*)\s*(?::\s*(\w+))?[^()]*\)"
    hop = re.compile(node + r"\s*(<?)-\[\s*\w*\s*:\s*(\w+)[^\]]*\]-(>?)\s*(?=" + node + ")")
    out = []
    for m in hop.finditer(cypher):
        v1, l1, left, rel, right = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        m2 = re.match(node, cypher[m.end() :])
        v2, l2 = m2.group(1), m2.group(2)
        a, b = l1 or bound.get(v1), l2 or bound.get(v2)
        if rel not in ends or not a or not b or bool(left) == bool(right):
            continue
        start, end = (a, b) if right else (b, a)
        if (start, end) != ends[rel] and (end, start) == ends[rel]:
            out.append(f"{rel} goes ({ends[rel][0]})-[:{rel}]->({ends[rel][1]}), not the other way")
    return list(dict.fromkeys(out))


def explain(V: Graph, cypher: str, nodes: list[dict] | None = None, rels: list[dict] | None = None) -> dict:
    """Virtual Graph's verdict on a query without running it: {sql: [...]} | {error}. Checked first,
    without a round trip: the constructs its subset rejects; and, with the model's nodes and
    relationships, a label, relationship type or property the graph lacks, and a relationship walked
    against its direction."""
    unsupported = subset_errors(cypher)
    if unsupported:
        return {"error": "not supported by Virtual Graph: " + "; ".join(unsupported)}
    reversed_ = wrong_directions(cypher, nodes or [], rels or [])
    if reversed_:
        return {"error": "relationship direction: " + "; ".join(reversed_)}
    missing = unknown_names(cypher, nodes, rels or []) if nodes else []
    if missing:
        return {"error": "not in the graph given: " + "; ".join(missing)}
    missing = unknown_properties(cypher, nodes or [])
    if missing:
        return {"error": "unknown properties: " + "; ".join(missing)}
    try:
        return {"sql": external_sql(V.run("EXPLAIN " + cypher).summary.plan)}
    except ServiceUnavailable:
        raise
    except Neo4jError as e:
        return {"error": (e.message or str(e)).split("\n")[0]}


def run(
    s: Settings, question: str, route: str = "auto", execute: bool = False, as_: str | None = None
) -> None:
    """`qlsc ask`: the trace, then the answer by `route`: auto (the router), sql, cypher, or none (the
    cohort only). `as_`: on a principal's behalf, through the entitlement gateway (qlsc/entitle.py)."""
    with Graph(s) as G:
        allow = entitle.allowlist(G, s, as_) if as_ else None
        if allow:
            print(
                f"AS  {allow.principal}: may read {len(allow.tables)} of the layer's tables; "
                f"{len(allow.hidden)} of their columns hidden (policy tags); the warehouse filters the rows of "
                f"{len(allow.rows)} of them per reader\n"
            )
        tr = trace(G, s, question, allow=allow)
        print_trace(tr)
        if route == "auto":
            a = answer_routed(G, s, tr, execute)
            print(
                f"\nrouted to {a['route'].upper()} ({a.get('writer')})"
                + (f"; the request didn't compile: {a['fallback']}" if a.get("fallback") else "")
            )
            (print_cypher if a["route"] == "cypher" else print_sql)(a)
        elif route == "cypher":
            print_cypher(answer_cypher(G, s, tr, execute))
        elif route == "sql":
            print_sql(answer_sql(G, s, tr, execute))

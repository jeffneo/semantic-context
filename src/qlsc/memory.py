"""Memory: an entity's context, fetched from the virtual graph and kept in a persistent Neo4j database
(plans/2026-09-27-agentic-memory.md; phase 1, the context compiler; phase 2, entitlements).

The virtual graph reads warehouse rows on demand and keeps nothing. Memory keeps what a read fetched, so the
next read of the same context is a local graph read, fast and free, and every fact stays tied to the
semantic layer it came from.

  template    what to fetch for a label, from the virtual graph's model:
                hop 0   the node itself;
                hop 1   every relationship touching it. Into it is the many side: windowed by the start
                        table's partition column (the last memory.window_days) and the memory.cap most
                        recent;
                hop 2+  to memory.hops, the relationships out of what was fetched (to-one: a fact's
                        dimensions), keyed by the nodes already fetched.
              Virtual Graph has no OPTIONAL MATCH, so each relationship is its own read. A hop's reads run
              concurrently, each signed for the pass-through.
  properties  the columns the log's queries read or filter on (memory.properties: used), with each node's
              key and partition column; or every column (all)
  identity    the virtual graph's labels, relationship types and keys, with `source` (the virtual graph's
              dataset) on every node: a node key (source, key) per label, so two sources never merge
  provenance  on every node and relationship: fetched_at, holds_until, fetched_by, fetched_with (the read's
              Cypher). Each node -[:FROM]-> a stub of its layer Table, which -[:HAS_COLUMN]-> stubs of the
              Columns remembered: ids that survive a rebuild, and a name
  freshness   a fact holds for its table's write cadence: the median gap between the log's write days. A
              frozen table's facts hold for good. A context holds until its first fact expires; recall
              reads memory while it holds, and fetches again once it doesn't (or once the template changed)
  refetch     a read's relationships that the new fetch didn't return are removed: the fact left the window,
              or points elsewhere now. Nodes stay, stale by their holds_until, and are never read as fresh
  entitlements  `--as <principal>` fetches as them: the template is the virtual graph's model as the gateway
              restricts it for them (entitle.model: readable tables, no hidden columns), and each read is
              signed for them, so the warehouse applies their tables, columns and rows. A remembered row has
              left the warehouse's enforcement, so:
              - a fact that depends on who reads it (a node of a table with a row access policy, or a
                relationship whose table or either end has one) carries `seen_until:<principal>` for each
                principal who fetched it, and is read only by a principal with their own mark still holding.
                A refetch takes the principal's mark off what it no longer returns, and a relationship no one
                has a mark on is removed;
              - any other fact is the same whoever reads it, and is shared;
              - a context is recorded per principal on its anchor (`context_until:<principal>`, ...), and a
                recall reads memory only for a context the principal fetched, with their template as it is
                now: a table or column they lost changes it, and it is fetched again.

Each read's Cypher is written once for either target: the virtual graph, or memory, where the same read adds
`source` and freshness. So a context read back from memory can be compared with the virtual graph's, read for
read.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from neo4j.exceptions import ClientError

from qlsc import entitle
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.warehouse import connect

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Labels memory itself uses, which a virtual graph's labels must not take (qlsc virtualize renames one that
# does): Neo4j Labs agent-memory's (qlsc/converse.py), its POLE+O entity types, and memory's stubs.
RESERVED_LABELS = frozenset(
    {"Conversation", "Message", "Entity", "Preference", "Fact", "ReasoningTrace", "ReasoningStep", "ToolCall",
     "Tool", "Extractor", "Schema", "Person", "Organization", "Location", "Event", "Object", "Table", "Column",
     "Computation"}
)  # fmt: skip
DATA_SOURCE = "data source"  # fetched_by when no principal is named: the estate's own read

# The tables the virtual graph serves: its label, partition column and write days, and the columns memory
# keeps (every column, or those the log's queries read or filter on, with keys and the partition column).
TABLES = """
MATCH (t:Table) WHERE t.graph_label IS NOT NULL
RETURN t.graph_label AS label, t.id AS id, t.name AS name, t.partition_column AS partition,
       t.write_days AS write_days,
       [(t)-[:HAS_COLUMN]->(c:Column)
        WHERE $all OR c.graph_key OR c.name = t.partition_column
           OR EXISTS { (:QueryShape)-[:READS|FILTERS]->(c) } | {id: c.id, name: c.name}] AS columns
"""

# Nothing writes it and no production process reads it (navigate's FROZEN, over every table served).
FROZEN = """
MATCH (t:Table) WHERE t.graph_label IS NOT NULL AND t.write_days IS NULL
  AND NOT EXISTS { MATCH (:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape {succeeded: true})-[:REFERENCES]->(x:Table)
                   WHERE x = t OR (x.kind = 'view' AND (x)-[:DERIVED_FROM*1..3]->(t)) }
RETURN t.graph_label AS label
"""

CREATE_DATABASE = "CREATE DATABASE $name IF NOT EXISTS WAIT"
NODE_KEY = (
    "CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:`{label}`) REQUIRE (n.source, n.`{key}`) IS NODE KEY"
)
STUB_KEYS = (
    "CREATE CONSTRAINT stub_table IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT stub_column IF NOT EXISTS FOR (c:Column) REQUIRE c.id IS UNIQUE",
)

STUBS = """
UNWIND $tables AS t
MERGE (x:Table {id: t.id}) SET x.name = t.name
WITH x, t UNWIND t.columns AS c
MERGE (y:Column {id: c.id}) SET y.name = c.name
MERGE (x)-[:HAS_COLUMN]->(y)
"""

# Per label and relationship type: identifiers from the virtual graph's model (checked), values as parameters.
NODES = """
UNWIND $rows AS r
MERGE (n:`{label}` {{source: $source, `{key}`: r.key}})
SET n += r.props, n.fetched_at = $at, n.holds_until = $until, n.fetched_by = $by, n.fetched_with = r.cypher,
    n[$seen] = CASE WHEN $depends THEN $seen_until ELSE n[$seen] END
WITH n
MATCH (t:Table {{id: $table}})
MERGE (n)-[:FROM]->(t)
"""
EDGES = """
UNWIND $rows AS r
MATCH (a:`{start}` {{source: $source, `{start_key}`: r.start}})
MATCH (b:`{end}` {{source: $source, `{end_key}`: r.end}})
MERGE (a)-[x:`{type}`]->(b)
SET x.fetched_at = $at, x.holds_until = $until, x.fetched_by = $by, x.fetched_with = $cypher,
    x[$seen] = CASE WHEN $depends THEN $seen_until ELSE x[$seen] END
"""
# A read's relationships the new fetch didn't return, around the nodes it was keyed on. One that depends on
# who reads it loses only this reader's mark, and goes when no one's is left (one with no mark, no one reads).
PRUNE_INTO = """
MATCH (:`{start}`)-[x:`{type}`]->(v:`{end}` {{source: $source}})
WHERE v.`{end_key}` IN $keys AND x.fetched_at < $at
DELETE x
"""
PRUNE_OUT_OF = """
MATCH (v:`{start}` {{source: $source}})-[x:`{type}`]->(:`{end}`)
WHERE v.`{start_key}` IN $keys AND x.fetched_at < $at
DELETE x
"""
UNSEE_INTO = """
MATCH (:`{start}`)-[x:`{type}`]->(v:`{end}` {{source: $source}})
WHERE v.`{end_key}` IN $keys
  AND (x[$seen] < $seen_until OR none(k IN keys(x) WHERE k STARTS WITH 'seen_until:'))
SET x[$seen] = null
WITH x WHERE none(k IN keys(x) WHERE k STARTS WITH 'seen_until:')
DELETE x
"""
UNSEE_OUT_OF = """
MATCH (v:`{start}` {{source: $source}})-[x:`{type}`]->(:`{end}`)
WHERE v.`{start_key}` IN $keys
  AND (x[$seen] < $seen_until OR none(k IN keys(x) WHERE k STARTS WITH 'seen_until:'))
SET x[$seen] = null
WITH x WHERE none(k IN keys(x) WHERE k STARTS WITH 'seen_until:')
DELETE x
"""
# The anchor's record of a reader's context: $k_at, $k_until, ... are that reader's property names.
CONTEXT = """
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
SET a[$k_at] = $at, a[$k_until] = $until, a[$k_template] = $template, a[$k_capped] = $capped
"""
FRESH = """
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
WHERE a[$k_template] = $template AND a[$k_at] IS NOT NULL AND (a[$k_until] IS NULL OR a[$k_until] > $now)
RETURN a[$k_at] AS at, a[$k_until] AS until, a[$k_capped] AS capped
"""
FIND_IN_MEMORY = """
MATCH (a:`{label}` {{source: $source}})
WHERE a.`{prop}` = $value AND a[$k_template] = $template AND a[$k_at] IS NOT NULL
  AND (a[$k_until] IS NULL OR a[$k_until] > $now)
RETURN a.`{key}` AS key LIMIT 2
"""
FIND = "MATCH (n:`{label}`) WHERE n.`{prop}` = $value RETURN n.`{key}` AS key LIMIT 2"
# What the reader's agent noted about an anchor (qlsc/converse.py): the preferences and facts that still
# hold, the people and things related to it, and the conversations that mentioned it.
NOTES = """
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
RETURN [(p:Preference)-[:ABOUT]->(a) WHERE p.recorded_by = $by AND (p.valid_until IS NULL OR p.valid_until > $now)
        | p {{.category, .preference, .valid_from}}] AS preferences,
       [(f:Fact)-[:ABOUT]->(a) WHERE f.recorded_by = $by AND (f.valid_until IS NULL OR f.valid_until > $now)
        | f {{.predicate, .object, .valid_from}}] AS facts,
       [(e:Entity)-[r:RELATED_TO]->(a) WHERE e.recorded_by = $by | e {{.name, .type, relation: r.relation_type}}] AS entities,
       [(c:Conversation)-[:HAS_MESSAGE]->(m:Message)-[:MENTIONS]->(a) WHERE m.recorded_by = $by
        | c {{.id, .title, .updated_at}}] AS conversations
"""


DatabaseUnavailable = ClientError  # the memory database doesn't exist yet


class Unsupported(ValueError):
    """The model has something memory doesn't handle yet (a compound key, a name that isn't an identifier)."""


def ident(name: str) -> str:
    if not IDENTIFIER.fullmatch(name):
        raise Unsupported(f"not an identifier: {name!r}")
    return name


@dataclass(frozen=True)
class Read:
    """One read of a template. Hop 0 fetches the anchor itself. A relationship read fetches `label` nodes
    across `type`, keyed on the `via` nodes: inward when the fetched nodes point at them (the many side),
    else outward (to-one)."""

    hop: int
    label: str
    type: str | None = None
    start: str | None = None
    end: str | None = None
    via: str | None = None
    inward: bool = False
    window: str | None = None  # the fetched nodes' partition property (inward reads)
    via_window: str | None = None  # the via nodes' partition property (outward reads: prunes partitions)

    @property
    def name(self) -> str:
        if self.type is None:
            return self.label
        return (
            f"{self.via}<-{self.type}-{self.label}"
            if self.inward
            else f"{self.via}-{self.type}->{self.label}"
        )


@dataclass
class Model:
    """The virtual graph's model (schema.json) as one reader may see it, with the layer's facts about its
    tables."""

    source: str
    nodes: dict[str, dict]  # label -> {table, key, props: {name: type}, partition}
    rels: list[dict]  # {type, start, end}
    tables: dict[str, dict]  # label -> {id, name, columns, write_days, frozen}
    reader: str = DATA_SOURCE  # the principal, or the data source
    allow: entitle.Allowlist | None = None
    policied: set[str] = field(default_factory=set)  # labels whose table has a row access policy
    depends: set[str] = field(default_factory=set)  # relationship types whose facts depend on the reader
    unreadable: set[str] = field(default_factory=set)  # labels the reader may not read

    def key(self, label: str) -> str:
        return self.nodes[label]["key"]

    def seen(self) -> str:
        """The property that marks a fact this reader fetched, until when it holds for them."""
        return f"seen_until:{self.reader}"

    def context_keys(self) -> dict[str, str]:
        return {f"k_{k}": f"context_{k}:{self.reader}" for k in ("at", "until", "template", "capped")}


def row_policied(s: Settings, tables: list[str]) -> set[str]:
    """The tables with a row access policy, from the warehouse (a privileged read); cached in
    <work>/virtual/row_policies.json for entitlements.allowlist_seconds, as the allowlists are."""
    path = s.work / "virtual" / "row_policies.json"
    if path.exists():
        d = json.loads(path.read_text())
        if (
            d["tables"] == sorted(tables)
            and time.time() - d["built"] < s["entitlements"]["allowlist_seconds"]
        ):
            return set(d["policied"])
    policied = connect(s).row_policies(sorted(tables))
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps({"built": time.time(), "tables": sorted(tables), "policied": sorted(policied)})
    )
    return policied


def model(G: Graph, s: Settings, schema: dict | None = None, allow: entitle.Allowlist | None = None) -> Model:
    """The virtual graph's model and the layer's facts about each table it serves: all of it, or (allow)
    what the principal may read."""
    schema = schema or json.loads((s.work / "virtual" / "schema.json").read_text())
    p = s["memory"]
    frozen = {r["label"] for r in G.rows(FROZEN)}
    tables = {
        r["label"]: {**r, "frozen": r["label"] in frozen}
        for r in G.rows(TABLES, all=p["properties"] == "all")
    }
    policied_tables = row_policied(s, sorted(t["id"] for t in tables.values()))
    entities, every = schema["entities"], {n["label"] for n in schema["entities"]["nodes"]}
    if allow is not None:
        entities = entitle.model(allow, entities, {t["id"]: label for label, t in tables.items()})
        tables = {
            label: t | {"columns": [c for c in t["columns"] if allow.column(t["id"], c["name"])]}
            for label, t in tables.items()
        }
    label_of_view = {n["table"]: n["label"] for n in schema["entities"]["nodes"]}
    nodes = {}
    for n in entities["nodes"]:
        label, keys = ident(n["label"]), n.get("key") or []
        if len(keys) != 1:
            raise Unsupported(f"{label}: a key of {len(keys)} columns")
        by_column = {x["column"]: x for x in n["properties"]}
        key = ident(by_column[keys[0]["column"]]["name"])
        t = tables.get(label, {"columns": [], "partition": None})
        kept = {c["name"] for c in t["columns"]} | {keys[0]["column"]}
        partition = by_column.get(t["partition"], {}).get("name") if t["partition"] else None
        nodes[label] = {
            "table": n["table"],
            "key": key,
            "partition": partition,
            "props": {ident(x["name"]): x["type"] for x in n["properties"] if x["column"] in kept},
            "readable": {x["name"]: x["type"] for x in n["properties"]},  # every property the reader may read
        }
    rels = [
        {
            "type": ident(r["label"]),
            "start": r["start"]["targetEntity"],
            "end": r["end"]["targetEntity"],
            "table": label_of_view.get(
                r.get("table"), r["start"]["targetEntity"]
            ),  # the label whose table holds it
        }
        for r in entities["relationships"]
    ]
    policied = {label for label, t in tables.items() if t["id"] in policied_tables}
    depends = {r["type"] for r in rels if {r["table"], r["start"], r["end"]} & policied}
    return Model(
        f"{schema['catalog']}.{schema['schema']}",
        nodes,
        rels,
        tables,
        reader=allow.principal if allow else DATA_SOURCE,
        allow=allow,
        policied=policied,
        depends=depends,
        unreadable=every - set(nodes),
    )


def template(m: Model, anchor: str, hops: int) -> list[Read]:
    """The reads that fetch `anchor`'s context: hop 0 the node, hop 1 every relationship touching it,
    hops 2 and up the to-one relationships out of what was fetched, each relationship read once."""
    if anchor not in m.nodes:
        raise Unsupported(f"no label {anchor} in the virtual graph")
    reads = [Read(0, anchor)]
    for r in sorted(m.rels, key=lambda r: (r["type"], r["start"], r["end"])):
        if r["start"] == anchor:
            reads.append(Read(1, r["end"], r["type"], r["start"], r["end"], via=anchor))
        elif r["end"] == anchor:
            window = m.nodes[r["start"]]["partition"]
            reads.append(
                Read(1, r["start"], r["type"], r["start"], r["end"], via=anchor, inward=True, window=window)
            )
    used = {x.type for x in reads}
    frontier = {x.label for x in reads[1:]}
    for hop in range(2, hops + 1):
        new = [
            Read(
                hop,
                r["end"],
                r["type"],
                r["start"],
                r["end"],
                via=r["start"],
                via_window=m.nodes[r["start"]]["partition"],
            )
            for r in sorted(m.rels, key=lambda r: (r["type"], r["start"], r["end"]))
            if r["type"] not in used and r["start"] in frontier
        ]
        used |= {x.type for x in new}
        frontier = {x.label for x in new}
        reads += new
    return reads


def digest(m: Model, reads: list[Read], p: dict) -> str:
    """What a remembered context was fetched with: a changed template, window or cap fetches it again."""
    what = [[r.name, r.window, sorted(m.nodes[r.label]["props"])] for r in reads] + [
        p["window_days"],
        p["cap"],
        p["properties"],
    ]
    return hashlib.sha256(json.dumps(what).encode()).hexdigest()[:16]


def cypher(m: Model, r: Read, memory: bool = False) -> str:
    """A read's Cypher: over the virtual graph, or (memory) the same read over memory: only its source's
    nodes, only facts that still hold at $now, and a fact that depends on who reads it only with the
    reader's own mark ($seen) still holding."""
    n = m.nodes[r.label]
    src = " {source: $source}" if memory else ""
    fresh = lambda v: f"({v}.holds_until IS NULL OR {v}.holds_until > $now)"
    seen = lambda v: f"{v}[$seen] > $now"
    ret = ", ".join(f"n.`{p}` AS `{p}`" for p in sorted(n["props"]))
    if r.type is None:
        where = [f"n.`{n['key']}` IN $keys"]
        if memory:
            where += [fresh("n")] + ([seen("n")] if r.label in m.policied else [])
        return f"MATCH (n:`{r.label}`{src})\nWHERE " + " AND ".join(where) + f"\nRETURN {ret}"
    vk = m.key(r.via)
    if r.inward:
        match = f"MATCH (n:`{r.label}`{src})-[x:`{r.type}`]->(v:`{r.via}`{src})"
    else:
        match = f"MATCH (v:`{r.via}`{src})-[x:`{r.type}`]->(n:`{r.label}`{src})"
    where = [f"v.`{vk}` IN $keys"]
    if r.window:
        where.append(f"n.`{r.window}` >= $since")
    if r.via_window:
        where.append(f"v.`{r.via_window}` >= $since")
    if memory:
        where += [fresh("x"), fresh("n")]
        where += [seen("x")] * (r.type in m.depends) + [seen("n")] * (r.label in m.policied)
        where += [seen("v")] * (r.via in m.policied)
    order = f"n.`{r.window}` DESC, n.`{n['key']}`" if r.window else f"v.`{vk}`, n.`{n['key']}`"
    limit = "\nLIMIT $limit" if r.inward else ""
    return (
        f"{match}\nWHERE "
        + "\n  AND ".join(where)
        + f"\nRETURN v.`{vk}` AS _via, {ret}\nORDER BY {order}{limit}"
    )


@dataclass
class Context:
    """An anchor's context as read: its nodes (label, key) -> properties, and its relationships."""

    label: str
    key: object
    origin: str  # "virtual graph" | "memory"
    nodes: dict[tuple[str, object], dict] = field(default_factory=dict)
    edges: set[tuple[str, str, object, str, object]] = field(
        default_factory=set
    )  # (type, start, key, end, key)
    reads: list[dict] = field(default_factory=list)  # {read, cypher, keys, rows, capped, seconds}
    fetched_with: dict[tuple[str, object], str] = field(
        default_factory=dict
    )  # node -> the read that fetched it
    fetched_at: dt.datetime | None = None
    holds_until: dt.datetime | None = None
    seconds: float = 0.0

    def capped(self) -> list[str]:
        return [x["read"] for x in self.reads if x["capped"]]

    def summary(self) -> dict:
        return {
            "label": self.label,
            "key": self.key,
            "origin": self.origin,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "reads": {x["read"]: x["rows"] for x in self.reads},
            "capped": self.capped(),
            "seconds": round(self.seconds, 3),
        }


def window_start(s: Settings) -> dt.date:
    today = s.params["navigate"].get("today") or dt.date.today()
    today = today if isinstance(today, dt.date) else dt.date.fromisoformat(str(today))
    return today - dt.timedelta(days=s["memory"]["window_days"])


def run_reads(
    s: Settings, m: Model, reads: list[Read], anchor_key, target: Graph, memory: bool, now: dt.datetime
) -> Context:
    """Every read of the template, a hop at a time (hop 0 with hop 1: both are keyed on the anchor), each
    hop's reads concurrently; the rows become the context's nodes and relationships."""
    p = s["memory"]
    anchor = reads[0].label
    ctx = Context(anchor, anchor_key, "memory" if memory else "virtual graph")
    fetched: dict[str, set] = {anchor: {anchor_key}}
    base = {"since": window_start(s), "limit": p["cap"] + 1}
    if memory:
        base |= {"source": m.source, "now": now, "seen": m.seen()}
    t0 = time.time()

    def one(r: Read) -> tuple[Read, str, list, list[dict], float]:
        q = cypher(m, r, memory)
        keys = sorted(fetched.get(r.via or anchor, set()), key=str)
        sent, extra = (q, {}) if memory else entitle.signing(s, m.allow, q)
        t = time.time()
        rows = target.rows(sent, **base, keys=keys, **extra) if keys else []
        return r, q, keys, rows, time.time() - t

    last = max(r.hop for r in reads)
    groups = [[r for r in reads if r.hop <= 1]] + [
        [r for r in reads if r.hop == h] for h in range(2, last + 1)
    ]
    for group in groups:
        with ThreadPoolExecutor(max_workers=p["workers"]) as pool:
            results = list(pool.map(one, group))
        if group[0].hop == 0 and not results[0][2]:
            ctx.seconds = time.time() - t0
            return ctx  # no such node: an empty context
        for r, q, keys, rows, seconds in results:
            capped = r.inward and len(rows) > p["cap"]
            rows = rows[: p["cap"]] if capped else rows
            key = m.key(r.label)
            for row in rows:
                via = row.pop("_via", None)
                ctx.nodes[(r.label, row[key])] = row
                ctx.fetched_with.setdefault((r.label, row[key]), q)
                fetched.setdefault(r.label, set()).add(row[key])
                if r.type:
                    start, end = (row[key], via) if r.inward else (via, row[key])
                    ctx.edges.add((r.type, r.start, start, r.end, end))
            ctx.reads.append(
                {
                    "read": r.name,
                    "cypher": q,
                    "keys": keys,
                    "rows": len(rows),
                    "capped": capped,
                    "seconds": seconds,
                }
            )
    ctx.seconds = time.time() - t0
    return ctx


def cadence_days(write_days: list | None) -> float | None:
    """The median gap, in days, between a table's write days in the log; None with fewer than two."""
    days = sorted({dt.date.fromisoformat(str(d)) for d in write_days or []})
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    return statistics.median(gaps) if gaps else None


def holds_until(s: Settings, table: dict, at: dt.datetime) -> dt.datetime | None:
    """Until when a fact fetched `at` holds: for its table's write cadence; a frozen table's, for good."""
    if table.get("frozen"):
        return None
    days = cadence_days(table.get("write_days")) or s["memory"]["unknown_hold_days"]
    return at + dt.timedelta(days=days)


def memory_graph(s: Settings) -> Graph:
    return Graph(s, {"database": s["memory"]["database"]})


def ensure(s: Settings, m: Model) -> None:
    """The memory database on the semantic layer's instance, and its keys: (source, key) per label, and the
    stubs' ids."""
    with Graph(s, {"database": "system"}) as system:
        system.run(CREATE_DATABASE, name=s["memory"]["database"])
    with memory_graph(s) as M:
        for label, n in sorted(m.nodes.items()):
            M.run(NODE_KEY.format(name=f"memory_{label}", label=label, key=n["key"]))
        for q in STUB_KEYS:
            M.run(q)


def write(s: Settings, m: Model, ctx: Context, reads: list[Read], template_id: str, at: dt.datetime) -> float:
    """The context into memory, in one transaction: stubs, nodes, relationships, the reads' stale
    relationships removed, and the anchor's context properties. -> seconds"""
    t0 = time.time()
    by, seen = m.reader, m.seen()
    by_label: dict[str, list[dict]] = {}
    done = {x["read"]: x for x in ctx.reads}
    for (label, key), props in ctx.nodes.items():
        by_label.setdefault(label, []).append(
            {"key": key, "props": props, "cypher": ctx.fetched_with[(label, key)]}
        )
    until = {label: holds_until(s, m.tables.get(label, {}), at) for label in m.nodes}
    # a reader's mark holds as long as the fact; a frozen table's, as long as an unknown cadence's: their
    # right to its rows may change though the rows don't
    seen_until = {
        label: u or at + dt.timedelta(days=s["memory"]["unknown_hold_days"]) for label, u in until.items()
    }
    tables = [
        {"id": t["id"], "name": t["name"], "columns": t["columns"]}
        for label, t in sorted(m.tables.items())
        if label in by_label
    ]

    def tx(t):
        t.run(STUBS, tables=tables).consume()
        for label, rows in sorted(by_label.items()):
            q = NODES.format(label=label, key=m.key(label))
            table = m.tables.get(label, {}).get("id")
            t.run(
                q,
                rows=rows,
                source=m.source,
                at=at,
                until=until[label],
                by=by,
                table=table,
                seen=seen,
                depends=label in m.policied,
                seen_until=seen_until[label],
            ).consume()
        for r in reads:
            if r.type is None or r.name not in done:
                continue
            ends = dict(start=r.start, end=r.end, type=r.type, start_key=m.key(r.start), end_key=m.key(r.end))
            rows = [
                {"start": a, "end": b} for (ty, st, a, en, b) in sorted(ctx.edges, key=str) if ty == r.type
            ]
            # a relationship holds as long as the table that holds it: the start node's
            t.run(
                EDGES.format(**ends),
                rows=rows,
                source=m.source,
                at=at,
                until=until[r.start],
                by=by,
                cypher=done[r.name]["cypher"],
                seen=seen,
                depends=r.type in m.depends,
                seen_until=seen_until[r.start],
            ).consume()
            # only around the nodes this read was keyed on: others' relationships are theirs
            if r.type in m.depends:
                prune = UNSEE_INTO if r.inward else UNSEE_OUT_OF
            else:
                prune = PRUNE_INTO if r.inward else PRUNE_OUT_OF
            t.run(
                prune.format(**ends),
                keys=done[r.name]["keys"],
                source=m.source,
                at=at,
                seen=seen,
                seen_until=seen_until[r.start],
            ).consume()
        dates = [until[label] for label in {x[0] for x in ctx.nodes}]
        context_until = min((d for d in dates if d is not None), default=None)
        anchor = ctx.label
        t.run(
            CONTEXT.format(label=anchor, key=m.key(anchor)),
            key=ctx.key,
            source=m.source,
            at=at,
            until=context_until,
            template=template_id,
            capped=ctx.capped(),
            **m.context_keys(),
        ).consume()
        return context_until

    with memory_graph(s) as M, M.driver.session(database=M.db) as session:
        ctx.holds_until = session.execute_write(tx)
    ctx.fetched_at = at
    return time.time() - t0


def virtual_graph(s: Settings) -> Graph:
    instance = s.get("virtualize", {}).get("neo4j")
    if not instance:
        raise Unsupported("no virtual graph: set virtualize.neo4j in the config")
    return Graph(s, instance)


def find(s: Settings, m: Model, label: str, prop: str, value, now: dt.datetime, template_id: str):
    """The key of the one `label` whose `prop` is `value`: from a fresh context in memory, else the virtual
    graph."""
    key = m.key(label)
    if prop not in m.nodes[label]["readable"]:
        raise Unsupported(
            f"{'the ' * (m.allow is None)}{m.reader} may not read {label}.{prop}, or it has none"
        )
    with memory_graph(s) as M:
        q = FIND_IN_MEMORY.format(label=label, prop=ident(prop), key=key)
        try:
            hits = [
                r["key"]
                for r in M.rows(
                    q, source=m.source, value=value, template=template_id, now=now, **m.context_keys()
                )
            ]
        except DatabaseUnavailable:
            hits = []
    if not hits:
        with virtual_graph(s) as V:
            q, extra = entitle.signing(s, m.allow, FIND.format(label=label, prop=prop, key=key))
            hits = [r["key"] for r in V.rows(q, value=value, **extra)]
    if len(hits) != 1:
        raise Unsupported(
            f"{len(hits) or 'no'} {label} with {prop} = {value!r}" + (" (or more)" if hits else "")
        )
    return hits[0]


def typed(m: Model, label: str, prop: str, value: str):
    """A command-line value as the property's type."""
    kind = m.nodes[label]["readable"].get(prop)
    return int(value) if kind == "INTEGER" else float(value) if kind == "FLOAT" else value


def recall(
    s: Settings,
    label: str,
    key,
    now: dt.datetime | None = None,
    force: bool = False,
    m: Model | None = None,
) -> Context:
    """`label` `key`'s context: from memory while it holds, else fetched from the virtual graph and
    remembered (read-through). `force` fetches regardless (remember)."""
    now = now or dt.datetime.now(dt.UTC)
    if m is None:
        with Graph(s) as G:
            m = model(G, s)
    readable(m, label)
    reads = template(m, label, s["memory"]["hops"])
    template_id = digest(m, reads, s["memory"])
    if not force:
        with memory_graph(s) as M:
            try:
                fresh = M.rows(
                    FRESH.format(label=label, key=m.key(label)),
                    key=key,
                    source=m.source,
                    template=template_id,
                    now=now,
                    **m.context_keys(),
                )
            except DatabaseUnavailable:
                fresh = []  # no memory database yet
            if fresh:
                ctx = run_reads(s, m, reads, key, M, memory=True, now=now)
                ctx.fetched_at, ctx.holds_until = fresh[0]["at"], fresh[0]["until"]
                for x in ctx.reads:
                    x["capped"] = x["read"] in (fresh[0]["capped"] or [])
                return ctx
    with virtual_graph(s) as V:
        ctx = run_reads(s, m, reads, key, V, memory=False, now=now)
    if ctx.nodes:
        ensure(s, m)
        ctx.seconds += write(s, m, ctx, reads, template_id, now)
    return ctx


def readable(m: Model, label: str) -> None:
    if label in m.unreadable:
        raise Unsupported(f"the warehouse doesn't let {m.reader} read {label}'s table")
    if label not in m.nodes:
        raise Unsupported(f"no label {label} in the virtual graph (labels: {', '.join(sorted(m.nodes))})")


def resolve(s: Settings, m: Model, label: str, key, now: dt.datetime):
    """A key as given (the label's key, or 'property=value' for the one node with it) as the key's value."""
    if isinstance(key, str) and "=" in key:
        prop, value = key.split("=", 1)
        reads = template(m, label, s["memory"]["hops"])
        return find(s, m, label, prop, typed(m, label, prop, value), now, digest(m, reads, s["memory"]))
    return typed(m, label, m.key(label), key) if isinstance(key, str) else key


def notes(s: Settings, m: Model, label: str, key, now: dt.datetime) -> dict:
    """What the reader's agent noted about `label` `key` (qlsc converse): their own notes only."""
    with memory_graph(s) as M:
        try:
            got = M.rows(
                NOTES.format(label=label, key=m.key(label)), source=m.source, key=key, by=m.reader, now=now
            )
        except DatabaseUnavailable:
            got = []
    if not got:
        return {}
    out = got[0]
    out["conversations"] = sorted(
        {c["id"]: c for c in out["conversations"]}.values(), key=lambda c: c["updated_at"]
    )
    return out


def show_notes(n: dict) -> list[str]:
    day = lambda d: str(d)[:10]
    lines = [
        f"  noted: {p['category']}: {p['preference']} (since {day(p['valid_from'])})"
        for p in n.get("preferences", [])
    ]
    lines += [
        f"  noted: {f['predicate']}: {f['object']} (since {day(f['valid_from'])})" for f in n.get("facts", [])
    ]
    lines += [f"  noted: {e['name']} ({e['type'].lower()}), {e['relation']}" for e in n.get("entities", [])]
    if cs := n.get("conversations"):
        lines.append(
            f"  in {len(cs)} conversation{'s' * (len(cs) > 1)}, the last {day(cs[-1]['updated_at'])}: {cs[-1]['title']}"
        )
    return lines


def show(ctx: Context, m: Model, full: bool = False) -> str:
    """The context, for a person: where it came from, the anchor's properties, and a line per read."""
    if not ctx.nodes:
        mine = "" if m.allow is None else f" that {m.reader} may read"
        return f"no {ctx.label} {ctx.key}{mine} in the virtual graph"
    at = lambda d: (
        d.to_native().strftime("%Y-%m-%d %H:%M UTC")
        if hasattr(d, "to_native")
        else d.strftime("%Y-%m-%d %H:%M UTC")
    )
    holds = at(ctx.holds_until) if ctx.holds_until else "for good (frozen)"
    lines = [
        f"{ctx.label} {ctx.key}: from {ctx.origin} in {ctx.seconds:.2f} s "
        f"({len(ctx.reads)} reads; fetched {at(ctx.fetched_at)} as {'the ' * (m.allow is None)}{m.reader}; "
        f"holds until {holds})"
    ]
    anchor = ctx.nodes[(ctx.label, ctx.key)]
    lines.append("  " + ", ".join(f"{k}={v}" for k, v in sorted(anchor.items()) if v is not None))
    for x in ctx.reads[1:]:
        more = " (capped: the most recent)" if x["capped"] else ""
        lines.append(f"  {x['read']}: {x['rows']}{more}")
    if full:
        for (label, key), props in sorted(ctx.nodes.items(), key=str):
            lines.append(
                f"    {label} {key}: "
                + ", ".join(f"{k}={v}" for k, v in sorted(props.items()) if v is not None)
            )
    return "\n".join(lines)


def reader_model(s: Settings, as_: str | None) -> Model:
    """The model as the principal (a name in entitlements.principals, or as given) may read it, or all of it."""
    with Graph(s) as G:
        return model(G, s, allow=entitle.allowlist(G, s, as_) if as_ else None)


def run(
    s: Settings, label: str, key: str, force: bool = False, full: bool = False, as_: str | None = None
) -> Context:
    """qlsc remember | recall <label> <key | property=value> [--as principal]."""
    now = dt.datetime.now(dt.UTC)
    m = reader_model(s, as_)
    readable(m, label)
    value = resolve(s, m, label, key, now)
    ctx = recall(s, label, value, now=now, force=force, m=m)
    print(show(ctx, m, full))
    if ctx.nodes:
        print("\n".join(show_notes(notes(s, m, label, value, now))))
    return ctx

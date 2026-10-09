"""Memory: an entity's context, fetched from the virtual graph and kept in a persistent Neo4j database
(plans/2026-09-27-agentic-memory.md; phase 1, the context compiler; phase 2, entitlements; the Context Memory
model, plans/2026-09-29-context-memory-model.md).

The virtual graph reads warehouse rows on demand and keeps nothing. Memory keeps what a read fetched, so the
next read of the same context is a local graph read, fast and free, and every fact stays tied to the
semantic layer it came from.

  template    what to fetch for a label, from the virtual graph's model:
                hop 0   the node itself;
                hop 1   every relationship touching it. Into it is the many side: windowed by the start
                        table's partition column (from memory.window_quarters back) and the memory.cap most
                        recent;
                hop 2+  to memory.hops, the relationships out of what was fetched (to-one: a fact's
                        dimensions).
              A hop at a time, its reads concurrently, each signed for the pass-through.
  one read    every relationship is a column of its start node's table (a fact's customer_key: qlsc
              virtualize writes them so), so every read is the nodes of a label whose property is in $keys:
              the anchor by its key; the facts into it by their own column; a to-one end by its key, from the
              column the nodes already fetched hold, and only those not fetched yet. Nothing traverses a
              relationship: Virtual Graph writes a traversal as the start's table joined to itself and to the
              end's, rescanning the fact table and billing the far one (BigQuery bills a minimum per table a
              query references). The anchor's own read gates the context: none, or none the reader may see,
              and the context is empty.
  batch       many anchors' contexts fetched together (qlsc remember LABEL KEY...): each read keyed on
              what all of them fetched, once. A warehouse bills the columns it scans, not the rows it returns,
              so a batch costs about what one context does. Each anchor keeps its own context, exactly the one
              it gets alone: its own rows, capped per anchor (a read into the anchors is paged: each page
              ordered by anchor, the cap and one more per anchor), the dimensions its own facts name, and its
              own recall step.
  properties  the columns the log's queries read or filter on (memory.properties: used), with each node's
              key, partition column and the columns its relationships are; or every column (all)
  identity    the virtual graph's labels, relationship types and keys, with `source` (the virtual graph's
              dataset) on every node: a node key (source, key) per label, so two sources never merge
  relationships  derived when a node is written, from its column: a written node's relationships of each
              type are replaced from it, and a written node gains those of the nodes already remembered that
              point at it. So a relationship has no state of its own: it holds as long as its two nodes do,
              and a fact that points elsewhere now points elsewhere in memory once it is fetched again
  provenance  on every node: fetched_at, holds_until, fetched_by, fetched_with (the read's Cypher). Each node
              -[:FROM]-> a stub of its layer Table, which -[:HAS_COLUMN]-> stubs of the Columns remembered:
              ids that survive a rebuild, and a name
  freshness   a fact holds for its table's write cadence: the median gap between the log's write days. A
              frozen table's facts hold for good. A context holds until its first fact expires; recall
              reads memory while it holds, and fetches again once it doesn't (or once the template changed).
              A node a fetch no longer returns (it left the window) stays, stale by its holds_until, and is
              never read as fresh
  entitlements  `--as <principal>` fetches as them: the template is the virtual graph's model as the gateway
              restricts it for them (entitle.model: readable tables, no hidden columns), and each read is
              signed for them, so the warehouse applies their tables, columns and rows. A remembered row has
              left the warehouse's enforcement, so:
              - every recall is a Step, owned by its reader: (:Step {tool: 'recall', owner})-[:READ]->. A
                fetch's step READ the anchor (the context record: when, with which template, until when it
                holds) and every node of a table with a row access policy it fetched, until it holds for them.
                Such a node is read from memory only by a principal whose own step read it and still holds,
                and so is a relationship to it: a relationship to a node the reader can't see says only the
                key its start node holds, which they read. Any other fact is the same whoever reads it, and is
                shared;
              - a recall reads memory only for a context the reader's own step fetched, with their template
                as it is now: a table or column they lost changes it, and it is fetched again. Every read,
                from memory too, leaves its step: who read what, and when.

  retention   what memory keeps does not stay for ever (plans/2026-10-08-memory-retention.md; `qlsc memory sweep`). Fetched rows are copies that have left the warehouse's
              policies: a node is deleted once it was fetched more than memory.retain.fetched_days ago (a fetch re-stamps every node it touches, so a row a live context still
              uses is as young as that context). The audit record (conversations, steps, decisions, facts) is kept, unless memory.retain.audit_days says otherwise, and then
              a conversation goes whole. Every sweep leaves a Step of its own: deletion is as auditable as reading.

Each read's Cypher is one for either target: the virtual graph, or memory, where the same read adds `source`
and freshness. So a context read back from memory can be compared with the virtual graph's, read for read.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from neo4j.exceptions import ClientError

from qlsc import entitle
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.warehouse import connect

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Labels memory itself uses, which a virtual graph's labels must not take (qlsc virtualize renames one that
# does): the Context Memory model's (qlsc/converse.py) and memory's stubs of the semantic layer.
RESERVED_LABELS = frozenset(
    {"Conversation", "Message", "Task", "Step", "Decision", "Fact", "Entity", "Skill", "Table", "Column",
     "Computation"}
)  # fmt: skip
DATA_SOURCE = "data source"  # fetched_by when no principal is named: the estate's own read

# The tables the virtual graph serves: its label, partition column and write days, and the columns memory
# keeps (every column, or those the log's queries read or filter on, with keys and the partition column).
TABLES = """
MATCH (t:Table) WHERE t.graph_label IS NOT NULL
RETURN t.graph_label AS label, t.id AS id, t.name AS name, t.partition_column AS partition,
       t.write_days AS write_days, t.frozen AS frozen,
       [(t)-[:HAS_COLUMN]->(c:Column)
        WHERE $all OR c.graph_key OR c.name = t.partition_column
           OR EXISTS { (:QueryShape)-[:READS|FILTERS]->(c) } | {id: c.id, name: c.name}] AS columns
"""

CREATE_DATABASE = "CREATE DATABASE $name IF NOT EXISTS WAIT"
NODE_KEY = (
    "CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:`{label}`) REQUIRE (n.source, n.`{key}`) IS NODE KEY"
)
STUB_KEYS = (
    "CREATE CONSTRAINT stub_table IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT stub_column IF NOT EXISTS FOR (c:Column) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT step_id IF NOT EXISTS FOR (s:Step) REQUIRE s.id IS UNIQUE",
    "CREATE INDEX step_owner IF NOT EXISTS FOR (s:Step) ON (s.owner, s.tool)",
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
SET n += r.props, n.fetched_at = $at, n.holds_until = $until, n.fetched_by = $by, n.fetched_with = r.cypher
WITH n
MATCH (t:Table {{id: $table}})
MERGE (n)-[:FROM]->(t)
"""
# A relationship is a column of its start node (qlsc virtualize writes each as its start table's key column),
# so memory derives it when a node is written: a written start node's relationships of the type are replaced
# from its column, and a written end node gains those of the start nodes already remembered that point at it.
# No state of its own: it holds as long as its two nodes do.
OUT_OF = """
UNWIND $keys AS k
MATCH (a:`{start}` {{source: $source, `{start_key}`: k}})
CALL (a) {{ MATCH (a)-[x:`{type}`]->() DELETE x }}
WITH a MATCH (b:`{end}` {{source: $source, `{end_key}`: a.`{fk}`}})
MERGE (a)-[:`{type}`]->(b)
"""
INTO = """
UNWIND $keys AS k
MATCH (b:`{end}` {{source: $source, `{end_key}`: k}})
MATCH (a:`{start}` {{source: $source, `{fk}`: k}})
MERGE (a)-[:`{type}`]->(b)
"""
FK_INDEX = "CREATE INDEX {name} IF NOT EXISTS FOR (n:`{label}`) ON (n.source, n.`{fk}`)"
# The recall itself, as a Step its reader owns. A fetch's step READ the anchor (the context record) and every
# row-policied node it fetched; a read of memory's step READ the anchor only, for the record.
STEP = """
CREATE (s:Step {{id: $id, tool: 'recall', owner: $by, scope: 'private', at: $at, recorded_at: $at, status: 'ok',
                 arguments: $arguments, fingerprint: $fingerprint, template: $template, origin: $origin,
                 capped: $capped}})
WITH s
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
CREATE (s)-[:READ {{context: true, context_until: $until, holds_until: $seen_until}}]->(a)
"""
SEEN = """
MATCH (s:Step {{id: $id}})
UNWIND $keys AS k
MATCH (n:`{label}` {{source: $source, `{key}`: k}})
MERGE (s)-[r:READ]->(n) ON CREATE SET r.holds_until = $seen_until
"""
FRESH = """
MATCH (s:Step {{tool: 'recall', owner: $by, template: $template, origin: 'virtual graph'}})
      -[r:READ {{context: true}}]->(a:`{label}` {{source: $source, `{key}`: $key}})
WHERE s.at <= $now AND (r.context_until IS NULL OR r.context_until > $now)
RETURN s.at AS at, r.context_until AS until, s.capped AS capped
ORDER BY s.at DESC LIMIT 1
"""
FIND_IN_MEMORY = """
MATCH (s:Step {{tool: 'recall', owner: $by, template: $template, origin: 'virtual graph'}})
      -[r:READ {{context: true}}]->(a:`{label}` {{source: $source}})
WHERE a.`{prop}` = $value AND s.at <= $now AND (r.context_until IS NULL OR r.context_until > $now)
RETURN DISTINCT a.`{key}` AS key LIMIT 2
"""
FIND = "MATCH (n:`{label}`) WHERE n.`{prop}` = $value RETURN n.`{key}` AS key LIMIT 2"
# What the reader's own agent side noted about an anchor (qlsc/converse.py): the facts about it that still hold,
# the people and things facts relate to it, its decisions (with their outcomes, and whether a fact one was based
# on has since been superseded), and the conversations that mentioned it.
NOTES = """
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
RETURN [(f:Fact)-[:ABOUT]->(a) WHERE f.owner = $by AND (f.valid_until IS NULL OR f.valid_until > $now)
        | f {{.predicate, .value, .origin, .valid_from}}] AS facts,
       [(e:Entity)<-[:ABOUT]-(f:Fact)-[:MENTIONS]->(a) WHERE f.owner = $by AND (f.valid_until IS NULL OR f.valid_until > $now)
        | {{name: e.name, type: e.type, predicate: f.predicate}}] AS related,
       [(d:Decision)-[:ABOUT]->(a) WHERE d.owner = $by AND (d.valid_until IS NULL OR d.valid_until > $now)
        | d {{.choice, .valid_from,
             outcomes: [(o:Fact {{predicate: 'outcome'}})-[:ABOUT]->(d) WHERE o.owner = $by | o.value],
             revisit: [(d)-[:BASED_ON]->(b:Fact)<-[:SUPERSEDES]-(n:Fact) WHERE n.owner = $by
                       | b.predicate + ': ' + b.value + ' is now ' + n.value]}}] AS decisions,
       [(c:Conversation)<-[:PART_OF]-(m:Message)-[:MENTIONS]->(a) WHERE m.owner = $by
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
    across `type`, from the `via` nodes: inward when the fetched nodes point at them (the many side: the
    nodes whose `fk` is a via node's key), else outward (to-one: the nodes whose key a via node's `fk`
    holds)."""

    hop: int
    label: str
    type: str | None = None
    start: str | None = None
    end: str | None = None
    via: str | None = None
    inward: bool = False
    window: str | None = None  # the fetched nodes' partition property (inward reads)
    fk: str | None = None  # the start node's property holding the end's key

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
    unreadable: set[str] = field(default_factory=set)  # labels the reader may not read

    def key(self, label: str) -> str:
        return self.nodes[label]["key"]


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
    tables = {r["label"]: r for r in G.rows(TABLES, all=p["properties"] == "all")}
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
            "columns": {x["name"]: x["column"] for x in n["properties"]},
        }
    rels = [
        {
            "type": ident(r["label"]),
            "start": r["start"]["targetEntity"],
            "end": r["end"]["targetEntity"],
            "table": label_of_view.get(
                r.get("table"), r["start"]["targetEntity"]
            ),  # the label whose table holds it
            "fk": foreign_key(r, nodes, label_of_view),
        }
        for r in entities["relationships"]
        if r["start"]["targetEntity"] in nodes and r["end"]["targetEntity"] in nodes
    ]
    for r in rels:  # the column a relationship joins on is fetched with its start node: the relationship
        if not r["fk"]:
            raise Unsupported(f"{r['type']}: a relationship that isn't a column of {r['start']}'s own table")
        nodes[r["start"]]["props"][r["fk"]] = nodes[r["start"]]["readable"][r["fk"]]
    policied = {label for label, t in tables.items() if t["id"] in policied_tables}
    return Model(
        f"{schema['catalog']}.{schema['schema']}",
        nodes,
        rels,
        tables,
        reader=allow.principal if allow else DATA_SOURCE,
        allow=allow,
        policied=policied,
        unreadable=every - set(nodes),
    )


def foreign_key(r: dict, nodes: dict, label_of_view: dict) -> str | None:
    """The start node's property that holds the end node's key, when the relationship is a column of the
    start node's own table (a fact's customer_key, an account's branch_id), as qlsc virtualize writes every
    relationship. None otherwise."""
    a, b = r["start"]["targetEntity"], r["end"]["targetEntity"]
    if a not in nodes or b not in nodes or label_of_view.get(r.get("table"), a) != a:
        return None
    if len(r["start"]["keys"]) != 1 or len(r["end"]["keys"]) != 1:
        return None
    (s,), (e,) = r["start"]["keys"], r["end"]["keys"]
    by_column = {c: name for name, c in nodes[a]["columns"].items()}
    fk = by_column.get(e["relationshipColumn"])
    own = (
        by_column.get(s["relationshipColumn"]) == nodes[a]["key"]
        and s["relationshipColumn"] == s["nodeColumn"]
    )
    to_key = {c: name for name, c in nodes[b]["columns"].items()}.get(e["nodeColumn"]) == nodes[b]["key"]
    return fk if fk and own and to_key and fk in nodes[a]["readable"] else None


def template(m: Model, anchor: str, hops: int) -> list[Read]:
    """The reads that fetch `anchor`'s context: hop 0 the node, hop 1 every relationship touching it,
    hops 2 and up the to-one relationships out of what was fetched, each relationship read once."""
    if anchor not in m.nodes:
        raise Unsupported(f"no label {anchor} in the virtual graph")
    reads = [Read(0, anchor)]
    ordered = sorted(m.rels, key=lambda r: (r["type"], r["start"], r["end"]))
    for r in ordered:
        ends = dict(type=r["type"], start=r["start"], end=r["end"], via=anchor, fk=r["fk"])
        if r["start"] == anchor:
            reads.append(Read(1, r["end"], **ends))
        elif r["end"] == anchor:
            reads.append(Read(1, r["start"], **ends, inward=True, window=m.nodes[r["start"]]["partition"]))
    used = {x.type for x in reads}
    frontier = {x.label for x in reads[1:]}
    for hop in range(2, hops + 1):
        new = [
            Read(hop, r["end"], r["type"], r["start"], r["end"], via=r["start"], fk=r["fk"])
            for r in ordered
            if r["type"] not in used and r["start"] in frontier
        ]
        used |= {x.type for x in new}
        frontier = {x.label for x in new}
        reads += new
    return reads


def digest(m: Model, reads: list[Read], p: dict) -> str:
    """What a remembered context was fetched with: a changed template, window or cap fetches it again."""
    what = [[r.name, r.window, sorted(m.nodes[r.label]["props"])] for r in reads] + [
        p["window_quarters"],
        p["cap"],
        p["properties"],
    ]
    return hashlib.sha256(json.dumps(what).encode()).hexdigest()[:16]


def cypher(m: Model, r: Read, memory: bool = False, until: bool = False) -> str:
    """A read's Cypher, the same for either target: the nodes of its label whose property is in $keys. The
    anchor by its key; the facts that point at the via nodes by their own column (a card transaction's
    customer_key), windowed and ordered by via node, then the most recent first, so a batch's is read in
    pages (run_batch); a to-one end by its key, from the column the via nodes hold. On the virtual graph no
    read traverses a relationship: Virtual Graph writes a traversal as the start's table joined to itself and
    to the end's. Over memory, the same read is guarded: its source's nodes, those that still hold at $now,
    and a node of a row-policied table only if the reader's own step ($by) read it and that read still
    holds. `until`: the facts' window also ends at $until (a context as of a day, run_batch's as_of)."""
    n = m.nodes[r.label]
    ret = ", ".join(f"n.`{p}` AS `{p}`" for p in sorted(n["props"]))
    prop = r.fk if r.inward else n["key"]
    where = [f"n.`{prop}` IN $keys"] + ([f"n.`{r.window}` >= $since"] if r.window else [])
    where += [f"n.`{r.window}` <= $until"] if r.window and until else []
    where += Guard(m).node("n", r.label) if memory else []
    match = f"MATCH (n:`{r.label}`)\nWHERE " + "\n  AND ".join(where)
    if not r.inward:
        return f"{match}\nRETURN {ret}"
    recent = f"n.`{r.window}` DESC, " if r.window else ""
    return f"{match}\nRETURN n.`{r.fk}` AS _via, {ret}\nORDER BY n.`{r.fk}`, {recent}n.`{n['key']}`\nLIMIT $limit"


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
    step: str | None = None  # the recall's Step in memory

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


def window_start(s: Settings, day: dt.date | None = None) -> dt.date:
    """The first day of the quarter memory.window_quarters before today's (or before `day`'s)."""
    today = day or s["navigate"].get("today") or dt.date.today()
    today = today if isinstance(today, dt.date) else dt.date.fromisoformat(str(today))
    month = today.year * 12 + (today.month - 1) // 3 * 3 - 3 * s["memory"]["window_quarters"]
    return dt.date(month // 12, month % 12 + 1, 1)


def run_reads(
    s: Settings, m: Model, reads: list[Read], anchor_key, target: Graph, memory: bool, now: dt.datetime
) -> Context:
    """One anchor's context: a batch of one."""
    return run_batch(s, m, reads, [anchor_key], target, memory, now)[anchor_key]


def used(query: str, params: dict) -> dict:
    """The parameters a query's text uses. The virtual graph (preview) answers a query sent with `keys` and three more parameters it never
    reads (a read of one node sent $since, $until and $limit) with a different node's row, whatever `keys` holds: silently wrong. So a read
    is sent what its text names and nothing else."""
    return {k: v for k, v in params.items() if f"${k}" in query}


def run_batch(
    s: Settings,
    m: Model,
    reads: list[Read],
    anchor_keys: list,
    target: Graph,
    memory: bool,
    now: dt.datetime,
    as_of: dt.date | None = None,
) -> dict:
    """Every read of the template for every anchor at once, a hop at a time (hop 0 first: a to-one read out of
    the anchors is keyed on the column they hold), each hop's reads concurrently, each keyed on the union of
    what the anchors fetched. A warehouse bills the columns it scans, not the rows it returns, so a read for
    many anchors costs about what one does. Each anchor keeps its own context: its own rows (capped per
    anchor, the most recent), and the ends its own nodes point at. An anchor with no node, or none the
    reader may see, has an empty context. -> anchor key -> Context"""
    p = s["memory"]
    anchor = reads[0].label
    origin = "memory" if memory else "virtual graph"
    ctxs = {a: Context(anchor, a, origin) for a in anchor_keys}
    live = set(ctxs)  # the anchors found
    fetched: dict = {a: {anchor: {a}} for a in anchor_keys}  # anchor -> label -> its context's keys
    store: dict = {}  # (label, key) -> the row, whichever anchor's read fetched it
    base = {"since": window_start(s, as_of), "limit": p["cap"] + 1}
    if as_of:  # a context as of a day: the facts dated up to it, from the window that ends there. Never written to memory
        base["until"] = as_of
    if memory:
        base |= {"source": m.source, "now": now, "by": m.reader}
    t0 = time.time()

    def one(r: Read) -> tuple[Read, str, dict, list[dict], float]:
        q = cypher(m, r, memory, until=bool(as_of))
        # what each anchor's read is keyed on: a copy, as the hop's other reads add to what was fetched
        keys = {a: set(fetched[a].get(r.via or anchor, ())) for a in live}
        ask = set().union(set(), *keys.values())
        if r.type and not r.inward:  # the ends those nodes point at, not fetched yet
            ask = (
                {store[(r.via, k)].get(r.fk) for k in ask} - {None} - {k for lb, k in store if lb == r.label}
            )
        ask = sorted(ask, key=str)
        sent, extra = (q, {}) if memory else entitle.signing(s, m.allow, q, target)
        t, rows = time.time(), []
        if not r.inward:  # a row per key at most
            for i in range(0, len(ask), p["keys_per_read"]):  # a warehouse limits a query's parameters
                rows += target.rows(sent, **used(sent, base), keys=ask[i : i + p["keys_per_read"]], **extra)
            return r, q, keys, rows, time.time() - t
        # into the anchors, in pages: a page is ordered by anchor, then the most recent first, and holds the
        # cap and one more for each anchor it's keyed on. An anchor is done once the page shows it complete (a
        # later anchor follows it) or past the cap; the rest are read again. So a page completes one anchor
        # at least, and a batch of one is one read, as ever.
        pending = ask
        while pending:
            chunk = pending[: p["keys_per_read"]]
            limit = (p["cap"] + 1) * len(chunk)
            page = target.rows(sent, **used(sent, base | {"limit": limit}), keys=chunk, **extra)
            if len(page) < limit:
                rows += page
                pending = pending[len(chunk) :]
                continue
            count: dict = {}
            for row in page:
                count[row["_via"]] = count.get(row["_via"], 0) + 1
            last = page[-1]["_via"]
            done = {v for v, n in count.items() if v != last or n > p["cap"]}
            rows += [row for row in page if row["_via"] in done]
            pending = [k for k in pending if k not in done]
        return r, q, keys, rows, time.time() - t

    def owned(r: Read, keys: dict, rows: list[dict]) -> dict:
        """Each anchor's rows of a read, in the read's order, with the node each one was reached from."""
        key, got = m.key(r.label), {a: [] for a in live}
        if r.type and not r.inward:  # to-one: the ends the anchor's own nodes point at
            for row in rows:
                store[(r.label, row[key])] = row
            for a in live:
                named = {store[(r.via, k)].get(r.fk) for k in keys[a]} - {None}
                got[a] = [
                    (store[(r.label, f)], None) for f in sorted(named, key=str) if (r.label, f) in store
                ]
            return got
        owners: dict = {}
        for a in live:
            for v in keys[a]:
                owners.setdefault(v, []).append(a)
        for row in rows:
            via = row.pop("_via", None)
            row = store.setdefault((r.label, row[key]), row)
            for a in owners.get(via if r.type else row[key], []):
                got[a].append((row, via))
        return got

    for hop in range(max(r.hop for r in reads) + 1):
        with ThreadPoolExecutor(max_workers=p["workers"]) as pool:
            results = list(pool.map(one, [r for r in reads if r.hop == hop]))
        if hop == 0:
            live &= {row[m.key(anchor)] for row in results[0][3]}
        for r, q, keys, rows, seconds in results:
            key = m.key(r.label)
            for a, got in owned(r, keys, rows).items():
                ctx = ctxs[a]
                capped = r.inward and len(got) > p["cap"]
                got = got[: p["cap"]] if capped else got
                for row, via in got:
                    ctx.nodes[(r.label, row[key])] = row
                    ctx.fetched_with.setdefault((r.label, row[key]), q)
                    fetched[a].setdefault(r.label, set()).add(row[key])
                    if r.inward:
                        ctx.edges.add((r.type, r.start, row[key], r.end, via))
                if r.type and not r.inward:  # each node it was keyed on, to the one it points at
                    for v in keys[a]:
                        f = store[(r.via, v)].get(r.fk)
                        if (r.label, f) in ctx.nodes:
                            ctx.edges.add((r.type, r.start, v, r.end, f))
                ctx.reads.append(
                    {
                        "read": r.name,
                        "cypher": q,
                        "keys": sorted(keys[a], key=str),
                        "rows": len(got),
                        "capped": capped,
                        "seconds": seconds,
                    }
                )
        if not live:
            break
    for ctx in ctxs.values():
        ctx.seconds = time.time() - t0
    return ctxs


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


def memory_instance(s: Settings, database: str | None = None) -> dict:
    """Where memory is: the semantic layer's instance, or the one `memory.neo4j` names. `database`: another database there (`system`)."""
    return {**s["memory"]["neo4j"], "database": database or s["memory"]["database"]}


def memory_graph(s: Settings) -> Graph:
    return Graph(s, memory_instance(s))


def ensure(s: Settings, m: Model) -> None:
    """The memory database on its instance (the semantic layer's unless `memory.neo4j` says otherwise), and its keys: (source, key) per label, (source,
    column) per relationship (to derive it from the end node), and the stubs' ids."""
    with Graph(s, memory_instance(s, "system")) as system:
        system.run(CREATE_DATABASE, name=s["memory"]["database"])
    with memory_graph(s) as M:
        for label, n in sorted(m.nodes.items()):
            M.run(NODE_KEY.format(name=f"memory_{label}", label=label, key=n["key"]))
        for r in sorted(m.rels, key=lambda r: r["type"]):
            M.run(FK_INDEX.format(name=f"memory_{r['start']}_{r['fk']}", label=r["start"], fk=r["fk"]))
        for q in STUB_KEYS:
            M.run(q)


def write(s: Settings, m: Model, ctx: Context, template_id: str, at: dt.datetime) -> float:
    """The context into memory, in one transaction: stubs, nodes, the relationships their columns make, and
    the recall's Step: its READ of the anchor is the context record, and its READ of each row-policied node
    lets the reader see it until it holds for them. -> seconds"""
    t0 = time.time()
    by = m.reader
    by_label: dict[str, list[dict]] = {}
    for (label, key), props in ctx.nodes.items():
        by_label.setdefault(label, []).append(
            {"key": key, "props": props, "cypher": ctx.fetched_with[(label, key)]}
        )
    until = {label: holds_until(s, m.tables.get(label, {}), at) for label in m.nodes}
    # what the reader saw holds for them as long as the fact; a frozen table's, as long as an unknown
    # cadence's: their right to its rows may change though the rows don't
    seen_until = {
        label: u or at + dt.timedelta(days=s["memory"]["unknown_hold_days"]) for label, u in until.items()
    }
    tables = [
        {"id": t["id"], "name": t["name"], "columns": t["columns"]}
        for label, t in sorted(m.tables.items())
        if label in by_label
    ]
    fetched = {label: sorted((k for lb, k in ctx.nodes if lb == label), key=str) for label in by_label}
    dates = [until[label] for label in by_label]
    context_until = min((d for d in dates if d is not None), default=None)
    step = str(uuid.uuid4())

    def tx(t):
        t.run(STUBS, tables=tables).consume()
        for label, rows in sorted(by_label.items()):
            q = NODES.format(label=label, key=m.key(label))
            table = m.tables.get(label, {}).get("id")
            t.run(q, rows=rows, source=m.source, at=at, until=until[label], by=by, table=table).consume()
        for r in sorted(m.rels, key=lambda r: r["type"]):
            ends = dict(start=r["start"], end=r["end"], type=r["type"], fk=r["fk"],
                        start_key=m.key(r["start"]), end_key=m.key(r["end"]))  # fmt: skip
            if r["start"] in fetched:
                t.run(OUT_OF.format(**ends), keys=fetched[r["start"]], source=m.source).consume()
            if r["end"] in fetched:
                t.run(INTO.format(**ends), keys=fetched[r["end"]], source=m.source).consume()
        record(t, m, ctx, template_id, at, step, "virtual graph", context_until, seen_until[ctx.label])
        for label in sorted(m.policied & set(by_label)):
            t.run(
                SEEN.format(label=label, key=m.key(label)),
                id=step,
                keys=fetched[label],
                source=m.source,
                seen_until=seen_until[label],
            ).consume()
        return context_until

    with memory_graph(s) as M, M.driver.session(database=M.db) as session:
        ctx.holds_until = session.execute_write(tx)
    ctx.fetched_at, ctx.step = at, step
    return time.time() - t0


def record(
    t, m: Model, ctx: Context, template_id: str, at, step: str, origin: str, until, seen_until
) -> None:
    """The recall's Step and its READ of the anchor, in transaction `t`."""
    t.run(
        STEP.format(label=ctx.label, key=m.key(ctx.label)),
        id=step,
        by=m.reader,
        at=at,
        arguments=json.dumps({"label": ctx.label, "key": str(ctx.key)}),
        fingerprint=f"recall {ctx.label} ?",
        template=template_id,
        origin=origin,
        capped=ctx.capped(),
        source=m.source,
        key=ctx.key,
        until=until,
        seen_until=seen_until,
    ).consume()


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
                for r in M.rows(q, source=m.source, value=value, template=template_id, now=now, by=m.reader)
            ]
        except DatabaseUnavailable:
            hits = []
    if not hits:
        with virtual_graph(s) as V:
            q, extra = entitle.signing(s, m.allow, FIND.format(label=label, prop=prop, key=key), V)
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
    return recall_batch(s, label, [key], now, force, m)[key]


def recall_batch(
    s: Settings,
    label: str,
    keys: list,
    now: dt.datetime | None = None,
    force: bool = False,
    m: Model | None = None,
) -> dict:
    """Many `label`s' contexts: each read from memory while it holds (unless `force`), the rest fetched from
    the virtual graph together, in one batch (run_batch), and each remembered as its own context, with its
    own recall step. -> key -> Context"""
    now = now or dt.datetime.now(dt.UTC)
    if m is None:
        with Graph(s) as G:
            m = model(G, s)
    readable(m, label)
    reads = template(m, label, s["memory"]["hops"])
    template_id = digest(m, reads, s["memory"])
    out, missing = {}, list(dict.fromkeys(keys))
    if not force:
        with memory_graph(s) as M:
            for key in list(missing):
                try:
                    fresh = M.rows(
                        FRESH.format(label=label, key=m.key(label)),
                        key=key,
                        source=m.source,
                        template=template_id,
                        now=now,
                        by=m.reader,
                    )
                except DatabaseUnavailable:
                    break  # no memory database yet
                if not fresh:
                    continue
                ctx = run_reads(s, m, reads, key, M, memory=True, now=now)
                ctx.fetched_at, ctx.holds_until = fresh[0]["at"], fresh[0]["until"]
                for x in ctx.reads:
                    x["capped"] = x["read"] in (fresh[0]["capped"] or [])
                if ctx.nodes:  # the read of memory leaves its step too: who read what, and when
                    ctx.step = str(uuid.uuid4())
                    with M.driver.session(database=M.db) as session:
                        session.execute_write(
                            lambda t, ctx=ctx: record(
                                t, m, ctx, template_id, now, ctx.step, "memory", None, None
                            )
                        )
                out[key] = ctx
                missing.remove(key)
    if missing:
        with virtual_graph(s) as V:
            fetched = run_batch(s, m, reads, missing, V, memory=False, now=now)
        if any(ctx.nodes for ctx in fetched.values()):
            ensure(s, m)
        for key, ctx in fetched.items():
            if ctx.nodes:
                ctx.seconds += write(s, m, ctx, template_id, now)
            out[key] = ctx
    return {key: out[key] for key in keys}


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
    """What the reader's own agent side noted about `label` `key` (qlsc converse)."""
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
        f"  noted: {f['predicate']}: {f['value']} (since {day(f['valid_from'])})" for f in n.get("facts", [])
    ]
    lines += [f"  noted: {e['name']} ({e['type']}), {e['predicate']}" for e in n.get("related", [])]
    for d in n.get("decisions", []):
        outcome = f"; outcome: {', '.join(d['outcomes'])}" if d["outcomes"] else ""
        revisit = f"; revisit: {'; '.join(d['revisit'])}" if d["revisit"] else ""
        lines.append(f"  decided: {d['choice']} (on {day(d['valid_from'])}{outcome}{revisit})")
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
    s: Settings, label: str, keys: list[str], force: bool = False, full: bool = False, as_: str | None = None
) -> dict:
    """qlsc remember | recall <label> <key | property=value>... [--as principal]: one context, shown with what
    the reader's agent noted; or many, fetched together, one line each. `-` reads keys from stdin."""
    now = dt.datetime.now(dt.UTC)
    m = reader_model(s, as_)
    readable(m, label)
    keys = [k for x in keys for k in (sys.stdin.read().split() if x == "-" else [x])]
    values = [resolve(s, m, label, k, now) for k in keys]
    t0 = time.time()
    ctxs = recall_batch(s, label, values, now=now, force=force, m=m)
    if len(values) == 1:
        ctx = ctxs[values[0]]
        print(show(ctx, m, full))
        if ctx.nodes:
            print("\n".join(show_notes(notes(s, m, label, values[0], now))))
        return ctxs
    for v, ctx in ctxs.items():
        what = f"{len(ctx.nodes)} nodes, {len(ctx.edges)} relationships" if ctx.nodes else "nothing"
        capped = f"; capped: {', '.join(ctx.capped())}" if ctx.capped() else ""
        print(f"{label} {v}: {what}, from {ctx.origin}{capped}")
    fetched = sum(c.origin == "virtual graph" and bool(c.nodes) for c in ctxs.values())
    print(
        f"{len(ctxs)} contexts in {time.time() - t0:.1f} s: {fetched} fetched together, the rest from memory or empty"
    )
    return ctxs


# ---- the memory route (plans/2026-09-27-agentic-memory.md, phase 5): a compiled question about one entity
# whose context the reader holds, answered from memory

ASKED = """
CREATE (s:Step {{id: $id, tool: 'ask', owner: $by, scope: 'private', at: $now, recorded_at: $now, status: 'ok',
                 origin: 'memory', arguments: $arguments, fingerprint: $fingerprint}})
WITH s
MATCH (a:`{label}` {{source: $source, `{key}`: $key}})
CREATE (s)-[:READ {{context: true}}]->(a)
"""


class Guard:
    """Memory's conditions on a query over the virtual graph's model (compile.render_cypher's guard), on every
    node: its source's, still holding at $now, and a row-policied node only if the reader's ($by) own step
    read it and that read still holds. A relationship holds as long as its nodes do. The same as memory's
    own reads (cypher())."""

    def __init__(self, m: Model):
        self.m = m

    def node(self, v: str, label: str) -> list[str]:
        out = [f"{v}.source = $source", f"({v}.holds_until IS NULL OR {v}.holds_until > $now)"]
        if label in self.m.policied:
            out.append(
                f"EXISTS {{ (:Step {{owner: $by}})-[seen:READ]->({v}) WHERE seen.holds_until > $now }}"
            )
        return out


def literal_value(v) -> str | None:
    """A literal's text, as the plan's SQL writes it: 42, -42, 'text', DATE '2026-04-01'; else None."""
    from sqlglot import exp

    if isinstance(v, exp.Literal):
        return v.this
    if isinstance(v, exp.Neg) and isinstance(v.this, exp.Literal):
        return "-" + v.this.this
    if isinstance(v, exp.Cast) and isinstance(v.this, exp.Literal):
        return v.this.this
    return None


def answerable(
    s: Settings, m: Model, block, labels: dict[str, str], entities: dict, now: dt.datetime
) -> dict:
    """Whether memory holds the whole answer to a compiled question (compile.Block), exactly:
      - it is about one entity: a filter on a label's key, or on a fact's foreign key to one;
      - the reader holds a fresh context of that entity (their own recall's step, their template);
      - every table it reads is in that context: the entity, the facts that point at it (the many side,
        which the context windows and caps), and their dimensions (to-one), as the template reads them;
      - on a windowed fact, its period starts inside the window, and the read that fetched it wasn't capped.
    -> {ok, why, label, key}"""
    import sqlglot
    from sqlglot import exp

    from qlsc.compile import alias

    tables = {alias(t): t for t in [block.fact] + [j[2] for j in block.joins]}
    label_of = {v: labels.get(t) for v, t in tables.items()}
    if not all(lb in m.nodes for lb in label_of.values()):
        return {"ok": False, "why": "it reads a table memory doesn't hold for this reader"}
    fk = {}  # (start label, its column) -> (type, end label)
    for r in entities["relationships"]:
        k = r["end"]["keys"][0]
        fk[(r["start"]["targetEntity"], k["relationshipColumn"].lower())] = (
            r["label"],
            r["end"]["targetEntity"],
        )
    column_of = {lb: {p: p.lower() for p in n["readable"]} for lb, n in m.nodes.items()}
    equal, lower = [], {}
    for w in block.where:
        e = sqlglot.parse_one(w, read="bigquery")
        for node in e.find_all(exp.EQ, exp.GTE, exp.GT):
            c, v = node.this, node.expression
            if isinstance(v, exp.Column) and isinstance(c, exp.Literal | exp.Cast | exp.Neg):
                c, v = v, c
            if not isinstance(c, exp.Column):
                continue
            value = literal_value(v)
            if value is None:
                continue
            if isinstance(node, exp.EQ):
                equal.append((c.table, c.name.lower(), value))
            else:
                lower[(c.table, c.name.lower())] = value
    anchors, via = set(), {}
    for v, col, value in equal:
        lb = label_of.get(v)
        if lb is None:
            continue
        if column_of[lb].get(m.key(lb)) == col:
            anchors.add((lb, value))
            via[v] = None
        elif (lb, col) in fk:
            ty, end = fk[(lb, col)]
            anchors.add((end, value))
            via[v] = ty
    if len(anchors) != 1:
        return {"ok": False, "why": f"it isn't about one entity ({len(anchors)} filtered by key)"}
    ((anchor, raw),) = anchors
    key = typed(m, anchor, m.key(anchor), raw)
    reads = template(m, anchor, s["memory"]["hops"])
    by_name = {r.name: r for r in reads}
    with memory_graph(s) as M:
        try:
            fresh = M.rows(FRESH.format(label=anchor, key=m.key(anchor)), key=key, source=m.source,
                           template=digest(m, reads, s["memory"]), now=now, by=m.reader)  # fmt: skip
        except DatabaseUnavailable:
            fresh = []
    if not fresh:
        return {
            "ok": False,
            "why": f"no fresh context of {anchor} {key} for {m.reader} in memory",
            "label": anchor,
            "key": key,
        }
    capped = set(fresh[0]["capped"] or [])
    covered: dict[str, Read | None] = {}
    for v, ty in via.items():
        lb = label_of[v]
        if ty is None and lb == anchor:
            covered[v] = None
        elif (r := by_name.get(f"{anchor}<-{ty}-{lb}")) is not None:
            covered[v] = r
    since = window_start(s).isoformat()
    for v, r in covered.items():
        if r is None:
            continue
        if r.name in capped:
            return {
                "ok": False,
                "why": f"{r.name} was capped in the context: memory holds only the most recent",
            }
        if r.window and not str(lower.get((v, r.window.lower()), "")) >= since:
            return {
                "ok": False,
                "why": f"its period on {label_of[v]}.{r.window} doesn't start inside the window ({since})",
            }
    for a, ac, t, tc, _ in block.joins:
        va, vt = alias(a), alias(t)
        la, lt = label_of[va], label_of[vt]
        out = fk.get((la, ac.lower()))
        back = fk.get((lt, tc.lower()))
        if va in covered and out and out[1] == lt and any(r.type == out[0] and r.via == la for r in reads):
            covered.setdefault(vt, None)
        elif (
            vt in covered and back and back[1] == la and any(r.type == back[0] and r.via == lt for r in reads)
        ):
            covered.setdefault(va, None)
        elif (
            va in covered
            and lt == anchor
            and out
            and out[1] == anchor
            and by_name.get(f"{anchor}<-{out[0]}-{la}")
        ):
            covered.setdefault(vt, None)
    missing = sorted(label_of[v] for v in tables if v not in covered)
    if missing:
        return {"ok": False, "why": f"it reads {', '.join(missing)} outside {anchor} {key}'s context"}
    return {"ok": True, "why": f"{anchor} {key}'s context is fresh in memory", "label": anchor, "key": key}


def answer(s: Settings, m: Model, cypher: str, label: str, key, now: dt.datetime, limit: int) -> dict:
    """The guarded Cypher run on memory, as the reader; its read leaves a Step, as every read does."""
    t0 = time.time()
    with memory_graph(s) as M:
        columns, rows, more = M.capped(cypher, limit, source=m.source, now=now, by=m.reader)
        M.run(ASKED.format(label=label, key=m.key(label)), id=str(uuid.uuid4()), by=m.reader, now=now,
              arguments=json.dumps({"cypher": cypher}), fingerprint="ask memory", source=m.source, key=key)  # fmt: skip
    return {"ok": True, "columns": columns, "rows": rows, "total": len(rows), "truncated": more,
            "seconds": time.time() - t0}  # fmt: skip


# ---------------------------------------------------------------- retention

# One match a class: counted (COUNT), then deleted in batches (DELETE: CALL ... IN TRANSACTIONS, which needs a session of its own, not a managed transaction).
COUNT = "RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC"
DELETE = "CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS"
# The conversation an audit cut-off reaches; what hangs from it is found from there.
SWEEP = {
    "fetched rows": "MATCH (n) WHERE n.fetched_at IS NOT NULL AND n.fetched_at < $cutoff",
    "facts of expired conversations": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Fact)-[:FROM]->(:Message)-[:PART_OF]->(c)""",
    "facts about their work": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Fact)-[:ABOUT]->(x)-[:PART_OF*1..2]->(c) WHERE x:Task OR x:Step OR x:Decision""",
    "decisions": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Decision)-[:PART_OF]->(:Task)-[:PART_OF]->(c)""",
    "steps of expired conversations": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Step)-[:PART_OF]->(:Task)-[:PART_OF]->(c)""",
    "tasks": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Task)-[:PART_OF]->(c)""",
    "messages": """
        MATCH (c:Conversation) WHERE c.recorded_at < $cutoff
        MATCH (n:Message)-[:PART_OF]->(c)""",
    "conversations": "MATCH (n:Conversation) WHERE n.recorded_at < $cutoff",
    "steps outside conversations": "MATCH (n:Step) WHERE NOT (n)-[:PART_OF]->(:Task) AND n.recorded_at < $cutoff",
}
AUDIT = tuple(k for k in SWEEP if k != "fetched rows")  # in the order that leaves nothing dangling
SWEEP_STEP = """
CREATE (s:Step {id: $id, tool: 'sweep', owner: 'qlsc', scope: 'private', at: $at, recorded_at: $at, status: 'ok',
                arguments: $arguments, result: $result})
"""


def sweep(s: Settings, now: dt.datetime | None = None, dry_run: bool = False) -> dict[str, dict[str, int]]:
    """What memory no longer keeps, deleted (or, dry_run, counted): {class: {label: nodes}}. Idempotent; safe beside a recall."""
    now = now or dt.datetime.now(dt.UTC)
    p = s["memory"]["retain"]
    cutoffs = {"fetched rows": now - dt.timedelta(days=p["fetched_days"])}
    if p["audit_days"] is not None:
        cutoffs |= {k: now - dt.timedelta(days=p["audit_days"]) for k in AUDIT}
    found: dict[str, dict[str, int]] = {}
    with memory_graph(s) as M:
        for name, match in SWEEP.items():
            if name not in cutoffs:
                continue
            params = {"cutoff": cutoffs[name]}
            found[name] = {r["label"]: r["n"] for r in M.rows(f"{match} {COUNT}", **params)}
            if found[name] and not dry_run:
                with M.driver.session(database=M.db) as session:
                    session.run(f"{match} WITH DISTINCT n {DELETE}", params).consume()
        if not dry_run:
            M.run(
                SWEEP_STEP,
                id=str(uuid.uuid4()),
                at=now,
                arguments=json.dumps({"fetched_days": p["fetched_days"], "audit_days": p["audit_days"]}),
                result=json.dumps({k: sum(v.values()) for k, v in found.items()}),
            )
    return found


def sweep_report(s: Settings, dry_run: bool = False, as_of: str | None = None) -> None:
    p = s["memory"]["retain"]
    now = dt.datetime.fromisoformat(as_of).replace(tzinfo=dt.UTC) if as_of else None
    found = sweep(s, now, dry_run)
    kept = "kept" if p["audit_days"] is None else f"{p['audit_days']} days"
    print(
        f"memory sweep{' (dry run: nothing deleted)' if dry_run else ''}: fetched rows older than {p['fetched_days']} days; the audit record: {kept}"
    )
    total = 0
    for name, labels in found.items():
        n = sum(labels.values())
        total += n
        print(f"  {name}: {n:,}" + (f"  ({', '.join(f'{k} {v:,}' for k, v in labels.items())})" if n else ""))
    print(f"  {'would delete' if dry_run else 'deleted'} {total:,} nodes")

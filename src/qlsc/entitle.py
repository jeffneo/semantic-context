"""The entitlement gateway: `qlsc ask --as <principal>` answers from only what the warehouse lets that
principal read (plans/2026-09-27-entitlements.md).

The warehouse is the rulebook; nothing here re-implements its rules. For each principal the gateway asks
the warehouse, through the connector, for an allowlist over the layer's tables:
  - tables: which the principal may read, asked as the principal
  - columns: each column's access-policy tag (a privileged read) and which tags the principal may read;
    a column whose tag they can't read is hidden
  - rows: which tables the warehouse filters per reader (row access policies; a privileged read). The
    gateway only needs to know where they are: the warehouse applies them when it runs as the principal
The allowlist is cached per principal for `entitlements.allowlist_seconds`.

Navigation (`navigate.trace(allow=...)`) then shows only what the allowlist admits: the cohort and its
columns, the groups (a partly readable one without its name), the Semantic hits (likewise), the joins,
the examples (only those whose every table and column is readable; who ran them as a kind, not a name),
the Computations, and filter values (never from a tagged column). SQL runs as the principal, so the
warehouse enforces tables, columns and rows exactly. The Cypher route runs as the virtual graph's single
identity, so it is allowed only where that can't show more (option A, `check_cypher`): every table and
column it reads readable by the principal, as a dry run of Virtual Graph's own SQL as the principal
confirms (a probe per table of the columns it reads there), and no table with a row policy.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field

import sqlglot
from sqlglot import exp

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.warehouse import Warehouse, connect

ALL_TABLES = "MATCH (t:Table) WHERE t.in_catalog RETURN t.id AS t ORDER BY t"

# Every Semantic node, with the tables whose columns sit under it: a name or summary is shown only to
# someone who may read all of them.
SEMANTIC_TABLES = """
MATCH (m)-[:IN_SEMANTIC]->(g:Semantic {level: 1})
MATCH (m)<-[:IS]-{0,1}(c:Column)<-[:HAS_COLUMN]-(t:Table)
WITH g, collect(DISTINCT t.id) AS tables
MATCH (g)-[:IN_SEMANTIC]->*(up:Semantic)
WITH up, collect(tables) AS ts
RETURN up.name AS name, reduce(a = [], x IN ts | a + x) AS tables
"""

# The columns each query shape reads: an example is shown only if every one is readable.
SHAPE_COLUMNS = """
MATCH (s:QueryShape)-[:READS]->(c:Column)<-[:HAS_COLUMN]-(t:Table) WHERE s.id IN $ids
RETURN s.id AS id, collect(DISTINCT [t.id, c.name]) AS cols
"""


@dataclass
class Allowlist:
    principal: str
    tables: set[str]  # the layer's tables the principal may read
    hidden: set[tuple[str, str]]  # columns of readable tables whose policy tag the principal can't read
    tagged: set[tuple[str, str]]  # every tagged column: its values are never shown, readable or not
    rows: set[str]  # tables the warehouse filters per reader (row access policies)
    semantics: dict[str, str] = field(default_factory=dict)  # Semantic name -> all | some | none readable
    built: float = 0.0

    def readable(self, table: str) -> bool:
        return table in self.tables

    def column(self, table: str, column: str) -> bool:
        return table in self.tables and (table, column) not in self.hidden

    def shown(self, table: str, column: str) -> bool:
        """Whether a column's filter values may be shown: readable and never tagged."""
        return self.column(table, column) and (table, column) not in self.tagged


def principal(s: Settings, name: str) -> str:
    """A principal by the estate's short name (entitlements.principals), or as given."""
    return (s.get("entitlements", {}).get("principals") or {}).get(name, name)


_CONNECTORS: dict[str, Warehouse] = {}


def warehouse(s: Settings, allow: Allowlist | None) -> Warehouse:
    """The connector a question runs through: the estate's own, or acting as the principal."""
    if allow is None:
        return connect(s)
    if allow.principal not in _CONNECTORS:
        _CONNECTORS[allow.principal] = connect(s).acting_as(allow.principal)
    return _CONNECTORS[allow.principal]


def allowlist(G: Graph, s: Settings, name: str, fresh: bool = False) -> Allowlist:
    """The principal's allowlist over the layer's tables, from the warehouse; cached for
    entitlements.allowlist_seconds in <work>/allowlists/."""
    who = principal(s, name)
    path = s.work / "allowlists" / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', who)}.json"
    if path.exists() and not fresh:
        d = json.loads(path.read_text())
        if time.time() - d["built"] < s["entitlements"]["allowlist_seconds"]:
            return Allowlist(
                d["principal"],
                set(d["tables"]),
                {tuple(x) for x in d["hidden"]},
                {tuple(x) for x in d["tagged"]},
                set(d["rows"]),
                d["semantics"],
                d["built"],
            )
    tables = [r["t"] for r in G.rows(ALL_TABLES)]
    estate = connect(s)
    person = estate.acting_as(who)
    readable = person.readable(tables)
    tags = estate.column_tags(sorted(readable))
    ok_tags = person.readable_tags(sorted(set(tags.values())))
    allow = Allowlist(
        who,
        readable,
        {tc for tc, tag in tags.items() if tag not in ok_tags},
        set(tags),
        estate.row_policies(sorted(readable)),
        built=time.time(),
    )
    for r in G.rows(SEMANTIC_TABLES):
        n = sum(t in readable for t in set(r["tables"]))
        allow.semantics[r["name"]] = "all" if n == len(set(r["tables"])) else "some" if n else "none"
    path.parent.mkdir(exist_ok=True)
    d = asdict(allow)
    d |= {k: sorted(map(list, d[k])) for k in ("hidden", "tagged")}
    d |= {k: sorted(d[k]) for k in ("tables", "rows")}
    path.write_text(json.dumps(d, indent=1))
    return allow


def readable_shapes(G: Graph, allow: Allowlist, shapes: list[dict]) -> set[str]:
    """The query shapes whose every table and column the principal may read, which read at least one table
    (a metadata query reads none, and may name anything in its literals), and whose text names no table
    or column hidden from them."""
    ids = [x["id"] for x in shapes if x.get("tables") and all(allow.readable(t) for t in x["tables"])]
    cols = {r["id"]: r["cols"] for r in G.rows(SHAPE_COLUMNS, ids=ids)}
    names = {t.rsplit(".", 1)[-1] for t in (r["t"] for r in G.rows(ALL_TABLES)) if not allow.readable(t)}
    names = {n for n in names if n not in {t.rsplit(".", 1)[-1] for t in allow.tables}}
    names |= {c for t, c in allow.hidden if not any(allow.column(x, c) for x in allow.tables)}
    unsaid = (
        re.compile(r"(?<!\w)(" + "|".join(sorted(map(re.escape, names))) + r")(?!\w)", re.I)
        if names
        else None
    )
    text = {x["id"]: x.get("sql") or "" for x in shapes}
    return {
        i
        for i in ids
        if all(allow.column(t, c) for t, c in cols.get(i, [])) and not (unsaid and unsaid.search(text[i]))
    }


def computation_ok(allow: Allowlist, c: dict) -> bool:
    """Whether a Computation reads only what the principal may: its tables, and no hidden column
    (named in its expression or filters as table.column)."""
    if not all(allow.readable(t) for t in c["tables"]):
        return False
    text = " ".join([c["expression"], *c.get("filters", [])]).lower()
    return not any(
        re.search(rf"\b{re.escape(t.rsplit('.', 1)[-1].lower())}`?\.{re.escape(col.lower())}\b", text)
        for t, col in allow.hidden
        if t in c["tables"]
    )


def model(allow: Allowlist, entities: dict, labels: dict[str, str]) -> dict:
    """The virtual graph's model as the principal may see it: labels over readable tables, without
    hidden properties; relationships between two such labels, on readable columns."""
    table = {label: t for t, label in labels.items()}
    nodes = []
    for n in entities["nodes"]:
        t = table.get(n["label"])
        if t and allow.readable(t):
            props = [x for x in n["properties"] if allow.column(t, x["column"])]
            nodes.append(n | {"properties": props})
    kept = {n["label"] for n in nodes}
    rels = []
    for r in entities["relationships"]:
        a, b = r["start"]["targetEntity"], r["end"]["targetEntity"]
        key = r["end"]["keys"][0]
        if a in kept and b in kept and allow.column(table[a], key["relationshipColumn"]):
            rels.append(r)
    return {"nodes": nodes, "relationships": rels}


def probes(sql: str, dialect: str = "bigquery") -> list[str]:
    """One query per table Virtual Graph's SQL reads, selecting the columns it reads there: a dry run of
    each, as the principal, is the warehouse's verdict on those columns. Built this way, not by filling
    in the SQL's parameters, because a query the warehouse can prove empty (NULL for a value, LIMIT 0)
    skips its column checks: BigQuery returns nothing, and checks nothing."""
    tree = sqlglot.parse_one(sql, read=dialect)
    tables = {(t.alias or t.name): t for t in tree.find_all(exp.Table)}
    cols: dict[str, set[str]] = {k: set() for k in tables}
    for c in tree.find_all(
        exp.Column
    ):  # Virtual Graph qualifies every column; a bare name is an output alias
        if c.table in cols and c.name:
            cols[c.table].add(c.name)
    out = []
    for key, t in sorted(tables.items()):
        ref = exp.Table(this=t.this.copy(), db=t.args.get("db"), catalog=t.args.get("catalog"))
        select = ", ".join(f"`{c}`" for c in sorted(cols[key])) or "1"
        out.append(f"SELECT {select} FROM {ref.sql(dialect=dialect)} LIMIT 1")
    return list(dict.fromkeys(out))


def check_cypher(s: Settings, allow: Allowlist, tables: list[str], external_sql: list[str]) -> str | None:
    """Option A: why the virtual graph may not answer this principal's query, or None. The virtual graph
    reads as one identity, so it may answer only where that shows nothing more than the principal's own
    read would: no table the warehouse filters per reader, and the principal allowed every table and
    column Virtual Graph's SQL reads (a dry run of it, as the principal)."""
    filtered = sorted(t for t in tables if t in allow.rows)
    if filtered:
        return f"the warehouse filters the rows of {', '.join(filtered)} per reader, and the virtual graph reads them all"
    person = warehouse(s, allow)
    for sql in external_sql:
        try:
            checks = probes(sql)
        except sqlglot.errors.ParseError:
            return "the virtual graph's SQL couldn't be read, so what it reads couldn't be checked"
        for probe in checks:
            res = person._dry_run(probe)
            if res["ok"] is not True:
                return f"{allow.principal} may not read what the virtual graph's SQL reads: {res.get('error', '')[:200]}"
    return None

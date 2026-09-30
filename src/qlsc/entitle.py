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
warehouse enforces tables, columns and rows exactly.

So does Cypher, through the JDBC pass-through (plans/2026-09-28-jdbc-passthrough.md): every query to the
virtual graph carries a signed token naming whom it is for (`signing`), and the driver in Virtual Graph's
JVM verifies it and runs Virtual Graph's SQL as that principal. A query with no token is refused there.
The pass-through is required: before the virtual graph reads on a principal's behalf, the gateway checks
once that it refuses an unsigned query (`enforced`), and refuses the read if it doesn't, so a virtual
graph running the plain driver (reading everything as its own identity) fails closed.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import asdict, dataclass, field

from neo4j.exceptions import Neo4jError

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


# ---- the JDBC pass-through: the gateway's signed statement of whom a query is for


def key(s: Settings) -> bytes:
    """The key the gateway and the pass-through share, in <work>/virtual/passthrough.key (mounted read-only
    into Virtual Graph's container, never committed); made on first use."""
    path = s.work / "virtual" / "passthrough.key"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_hex(32))
        os.chmod(path, 0o644)  # the container reads it as another user; the work directory is the user's
    return bytes.fromhex(path.read_text().strip())


def token(s: Settings, principal: str, now: float | None = None) -> str:
    """base64url("principal\nexpires") . base64url(HMAC-SHA256): vg-passthrough's Token.java verifies it.
    The empty principal is the data source's own identity, for the estate's own reads."""
    expires = int((now or time.time()) + s["entitlements"]["token_seconds"])
    payload = f"{principal}\n{expires}".encode()
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    return b64(payload) + "." + b64(hmac.new(key(s), payload, hashlib.sha256).digest())


CLAUSE = re.compile(r"\b(OPTIONAL\s+MATCH|MATCH|WHERE|WITH|RETURN|UNWIND|ORDER\s+BY|LIMIT)\b", re.I)


def signed(cypher: str) -> str:
    """The query with the gateway's predicate, `$qlsc_principal IS NOT NULL`, in the WHERE of its
    matches (added if there is none): Virtual Graph carries it into every statement it sends, as the
    parameter the pass-through reads. The rest of the WHERE is bracketed, so the predicate holds over all
    of it."""
    masked = re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"", lambda m: " " * len(m.group()), cypher)
    clauses = [(m.start(), m.end(), m.group(1).upper()) for m in CLAUSE.finditer(masked)]
    after = next((a for a, _, k in clauses if k in ("WITH", "RETURN", "UNWIND")), len(cypher))
    where = next(((a, b) for a, b, k in clauses if k == "WHERE" and a < after), None)
    if where is None:
        return cypher[:after].rstrip() + "\nWHERE $qlsc_principal IS NOT NULL\n" + cypher[after:]
    end = next((a for a, _, _ in clauses if a > where[1]), len(cypher))
    body = cypher[where[1] : end].strip()
    return f"{cypher[: where[1]]} $qlsc_principal IS NOT NULL AND ({body})\n{cypher[end:]}"


class Unenforced(Exception):
    """The virtual graph doesn't refuse an unsigned query: it would read as its own identity."""


# A query without the gateway's token: the pass-through refuses it before any SQL runs. (Not a bare 1:
# the pass-through lets Virtual Graph's own key checks through unsigned.)
UNSIGNED = "MATCH (n:`{label}`) RETURN count(n) AS n"
_ENFORCED: dict[str, bool] = {}


def enforced(s: Settings, V: Graph) -> bool:
    """Whether the virtual graph refuses an unsigned query, as the pass-through does: asked once per
    instance."""
    uri = s["virtualize"]["neo4j"]["uri"]
    if uri not in _ENFORCED:
        label = json.loads((s.work / "virtual" / "schema.json").read_text())["entities"]["nodes"][0]["label"]
        try:
            V.rows(UNSIGNED.format(label=label))
            _ENFORCED[uri] = False
        except Neo4jError as e:
            if "pass-through: refused" not in (e.message or ""):
                raise
            _ENFORCED[uri] = True
    return _ENFORCED[uri]


def signing(s: Settings, allow: Allowlist | None, cypher: str, V: Graph | None = None) -> tuple[str, dict]:
    """(the query to send to the virtual graph `V`, its parameters): signed for the principal, or for the
    data source when no one is named. On a principal's behalf only where the pass-through runs: else
    Unenforced."""
    if allow is not None and (V is None or not enforced(s, V)):
        raise Unenforced(
            f"the virtual graph at {s['virtualize']['neo4j']['uri']} runs an unsigned query, so it would read as "
            f"its own identity, not as {allow.principal}: it needs the JDBC pass-through (vg-passthrough/)"
        )
    return signed(cypher), {"qlsc_principal": token(s, allow.principal if allow else "")}

"""The compiler: a question as a typed request, compiled to SQL and to Cypher
(plans/2026-09-28-compiler.md, plans/2026-09-28-compiler-2.md).

The LLM fills a request from the options the semantic layer offers (prompts/compile_*.md): the
measures (a Computation the log defines, an aggregate over a column, or one derived from two others),
the dimensions, the filters, the period, a filter on a measure, and a top N if asked. This module
resolves the request into a plan, deterministically, and renders the plan as SQL, or as Cypher over the
Virtual Graph.

The plan is one or more blocks, each an aggregate over one fact table:
  - the fact is the first measure's table; every other table joins to it along the layer's trusted
    joins, at most two hops, and only to a table unique on its join column (checked in the warehouse,
    cached), so no join multiplies the fact's rows; each is the join type the log mostly uses for it
    (an outer join keeps the fact's rows with no match, as a null group; an inner join drops them)
  - a measure on a table the fact can't join to uniquely starts a block of its own; the blocks are
    joined on the dimensions, each reaching them through the column named, another the request names
    for it, or the column a trusted join equates it to
  - when the fact can't reach what the request groups or filters by, another table the request names
    is the fact, if every measure on another table survives a fan-out (a distinct count, a MIN or a MAX)
  - each table's alias is its name as a plain identifier, so a Computation's expression drops in as
    the log wrote it
  - a Computation's filters that every measure in a block shares go in WHERE with the request's own; a
    measure's other filters, and the conditions a request puts inside a measure ("count only clicked
    rows"), wrap its aggregate's argument, so a group with none still shows zero
  - a measure computed per entity first (`per`, then `then`) is two steps: an inner aggregate grouped by
    the dimensions and the entity, an outer one by the dimensions; a latest-value Computation
    (ARRAY_AGG ... LIMIT 1) asked at a coarser grain than its own is summed over its grain that way
  - literals are typed from the column; a period on a timestamp filters on its date
A request that doesn't fit, names what the layer lacks, or can't be joined raises Unfit, and the route
writes freely instead. The SQL is written in BigQuery's dialect and rendered in the warehouse's through
sqlglot. The Cypher renders the same plan over the Virtual Graph's labels, relationships and properties,
for one block only: Virtual Graph has no CALL subquery to combine two.
"""

from __future__ import annotations

import datetime as dt
import re
from collections import deque
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from qlsc.names import short

OPS = ["=", "!=", "IN", "NOT IN", ">", ">=", "<", "<=", "IS TRUE", "IS FALSE", "IS NULL", "IS NOT NULL"]
AGGREGATES = ["COUNT", "COUNT_DISTINCT", "SUM", "AVG", "MIN", "MAX"]
THEN = ["", "SUM", "AVG", "MIN", "MAX", "COUNT"]
GRAINS = ["", "day", "week", "week_monday", "month", "quarter", "year"]

CONDITION = {
    "type": "object",
    "required": ["column", "op", "values"],
    "properties": {
        "column": {"type": "string", "description": "dataset.table.column"},
        "op": {"type": "string", "enum": OPS},
        "values": {"type": "array", "items": {"type": ["string", "number", "boolean"]}},
    },
}


def strings(description: str) -> dict:
    return {"type": "array", "items": {"type": "string"}, "description": description}


SCHEMA = {
    "type": "object",
    "required": ["fits", "reason", "measures", "dimensions", "filters", "period", "order", "limit"],
    "properties": {
        "fits": {"type": "boolean"},
        "reason": {"type": "string"},
        "measures": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["alias"],
                "properties": {
                    "alias": {"type": "string"},
                    "computation": {"type": "string", "description": "a Computation id, or empty"},
                    "aggregate": {"type": "string", "enum": ["", *AGGREGATES]},
                    "column": {
                        "type": "string",
                        "description": "dataset.table.column; empty for COUNT of rows",
                    },
                    "where": {
                        "type": "array",
                        "items": CONDITION,
                        "description": "count or sum only these rows",
                    },
                    "per": strings("compute the measure per this entity first: dataset.table.column"),
                    "then": {
                        "type": "string",
                        "enum": THEN,
                        "description": "with per: how the values per entity combine",
                    },
                    "ratio_of": strings("two other measures' aliases: numerator, denominator"),
                    "difference_of": strings("two other measures' aliases: the first minus the second"),
                },
            },
        },
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["alias"],
                "properties": {
                    "alias": {"type": "string"},
                    "column": {"type": "string"},
                    "grain": {"type": "string", "enum": GRAINS},
                    "computation": {"type": "string"},
                    "other_columns": strings("the same thing in another fact's table, for a measure there"),
                },
            },
        },
        "filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "computation": {"type": "string", "description": "a population Computation id"},
                    **CONDITION["properties"],
                },
            },
        },
        "period": {
            "type": "object",
            "properties": {
                "column": {"type": "string"},
                "from": {"type": "string"},
                "to": {"type": "string"},
                "other_columns": strings("another fact's date column, for a measure there"),
            },
            "description": "empty fields when the question names no period",
        },
        "having": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["alias", "op", "value"],
                "properties": {
                    "alias": {"type": "string", "description": "a measure's alias"},
                    "op": {"type": "string", "enum": ["=", "!=", ">", ">=", "<", "<="]},
                    "value": {"type": "number"},
                },
            },
            "description": "keep only the rows whose measure passes",
        },
        "order": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["alias", "desc"],
                "properties": {"alias": {"type": "string"}, "desc": {"type": "boolean"}},
            },
        },
        "limit": {"type": "integer"},
    },
}

TRUNC = {
    "day": "DAY",
    "week": "WEEK",
    "week_monday": "WEEK(MONDAY)",
    "month": "MONTH",
    "quarter": "QUARTER",
    "year": "YEAR",
}


# A latest (or any) value rather than an additive aggregate: right only at the grain it was computed at.
LATEST = re.compile(r"\b(ARRAY_AGG|ANY_VALUE|LAST_VALUE|FIRST_VALUE)\s*\(", re.I)


class Unfit(Exception):
    """The request can't be compiled; the route writes freely instead."""


class Catalogue:
    """What a request may name: the tables available (full id -> {column: type}), their trusted joins,
    and the Computations offered (id -> Computation)."""

    def __init__(self, tables: dict[str, dict[str, str]], joins: list[dict], computations: dict[str, dict]):
        self.tables, self.computations = tables, computations
        self.by_short = {short(t): t for t in tables}
        self.edges: dict[str, list[tuple[str, str, str]]] = {t: [] for t in tables}
        self.outer: set[frozenset] = set()  # joins the log mostly writes as outer joins
        for j in joins:  # {a, ac, b, bc, type}
            if j["a"] in tables and j["b"] in tables:
                self.edges[j["a"]].append((j["b"], j["ac"], j["bc"]))
                self.edges[j["b"]].append((j["a"], j["bc"], j["ac"]))
                if (j.get("type") or "INNER").upper() in ("LEFT", "RIGHT", "FULL", "OUTER"):
                    self.outer.add(frozenset([(j["a"], j["ac"]), (j["b"], j["bc"])]))

    def column(self, ref: str) -> tuple[str, str, str]:
        """'dataset.table.column' (or a full id) -> (table id, column, type); Unfit if unknown."""
        table, _, col = (ref or "").rpartition(".")
        if not table:
            raise Unfit(f"{ref!r} names no table")
        t = self.by_short.get(table) or (table if table in self.tables else None)
        if not t:
            raise Unfit(f"no table {table!r} among those offered")
        cols = {c.lower(): (c, typ) for c, typ in self.tables[t].items()}
        if col.lower() not in cols:
            raise Unfit(f"{short(t)} has no column {col!r}")
        c, typ = cols[col.lower()]
        return t, c, typ

    def route(self, start: str, goal: str, hops: int, unique) -> list[tuple[str, str, str, str]] | None:
        """The shortest join path that never multiplies `start`'s rows (each step to a table unique on
        its join column), as (from table, its column, to table, its column) steps; None if none."""
        if start == goal:
            return []
        seen, queue = {start}, deque([(start, [])])
        while queue:
            t, steps = queue.popleft()
            if len(steps) == hops:
                continue
            for other, mine, theirs in sorted(self.edges.get(t, [])):
                if other in seen or not unique(other, theirs):
                    continue
                route = [*steps, (t, mine, other, theirs)]
                if other == goal:
                    return route
                seen.add(other)
                queue.append((other, route))
        return None

    def equivalents(self, table: str, col: str) -> list[tuple[str, str]]:
        """The columns a trusted join equates (table, col) to: the same values in another table."""
        return sorted((other, theirs) for other, mine, theirs in self.edges.get(table, []) if mine == col)


def alias(table: str) -> str:
    """A table's alias: its own name, made a plain identifier if it isn't one (a Looker PDT's LR_{id}_x
    -> LR_id_x)."""
    raw = table.rsplit(".", 1)[-1]
    return raw if re.fullmatch(r"[A-Za-z_]\w*", raw) else re.sub("_+", "_", name(raw))


def name(text: str) -> str:
    """An output column's name as a plain identifier (the LLM may write spaces or symbols)."""
    out = re.sub(r"\W+", "_", str(text)).strip("_") or "value"
    return f"_{out}" if out[0].isdigit() else out


def aliased(expression: str, tables: list[str]) -> str:
    """A Computation's expression with its tables named by their aliases here."""
    for t in tables:
        raw = t.rsplit(".", 1)[-1]
        if raw != alias(t):
            expression = expression.replace(f"`{raw}`.", f"{alias(t)}.").replace(f"{raw}.", f"{alias(t)}.")
    return expression


def literal(value, typ: str) -> str:
    typ = (typ or "").upper()
    if value is None:
        return "NULL"
    if typ in ("BOOL", "BOOLEAN"):
        return "TRUE" if str(value).lower() in ("true", "1", "yes") else "FALSE"
    if typ in ("INT64", "INTEGER", "FLOAT64", "NUMERIC", "BIGNUMERIC", "FLOAT"):
        try:
            float(value)
            return str(value)
        except (TypeError, ValueError):
            raise Unfit(f"{value!r} is not a number") from None
    if typ == "DATE":
        return f"DATE '{value}'"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def condition(cat: Catalogue, c: dict, used: set[str]) -> str:
    t, col, typ = cat.column(c["column"])
    used.add(t)
    ref, op, vals = f"{alias(t)}.{col}", c["op"].upper(), c.get("values") or []
    if op in ("IS TRUE", "IS FALSE", "IS NULL", "IS NOT NULL"):
        return f"{ref} {op}"
    if op in ("IN", "NOT IN"):
        if not vals:
            raise Unfit(f"{op} on {col} with no values")
        return f"{ref} {op} ({', '.join(literal(v, typ) for v in vals)})"
    if len(vals) != 1:
        raise Unfit(f"{op} on {col} needs one value")
    other = column_ref(cat, vals[0], used)  # agent site != queue site: a value naming a column is that column
    return f"{ref} {op} {other or literal(vals[0], typ)}"


def column_ref(cat: Catalogue, value, used: set[str]) -> str | None:
    if not isinstance(value, str) or "." not in value:
        return None
    try:
        t, col, _ = cat.column(value)
    except Unfit:
        return None
    used.add(t)
    return f"{alias(t)}.{col}"


def within(expression: str, filters: list[str]) -> str:
    """An aggregate expression over only the rows its filters keep: each aggregate's argument
    becomes IF(filters, argument, NULL)."""
    if not filters:
        return expression
    text = filters[0] if len(filters) == 1 else " AND ".join(f"({f})" for f in filters)
    cond = sqlglot.parse_one(text, read="bigquery")
    tree = sqlglot.parse_one(expression, read="bigquery")
    wrap = lambda arg: exp.If(this=cond.copy(), true=arg, false=exp.Null())
    for agg in list(tree.find_all(exp.AggFunc)):
        arg = agg.this
        if isinstance(arg, exp.Distinct):  # COUNT(DISTINCT x) -> COUNT(DISTINCT IF(cond, x, NULL))
            arg.set("expressions", [wrap(x) for x in arg.expressions])
            continue
        if arg is None or isinstance(arg, exp.Star):
            arg = exp.Literal.number(1)
        agg.set("this", wrap(arg))
    return tree.sql(dialect="bigquery")


def fanout_safe(expression: str) -> bool:
    """Whether an aggregate is the same over a fact's rows repeated: distinct counts, MIN and MAX."""
    try:
        aggs = list(sqlglot.parse_one(expression, read="bigquery").find_all(exp.AggFunc))
    except sqlglot.errors.ParseError:
        return False
    return bool(aggs) and all(
        isinstance(a, (exp.Min, exp.Max)) or (isinstance(a, exp.Count) and isinstance(a.this, exp.Distinct))
        for a in aggs
    )


def same_grain(c: dict, request: dict, cat: Catalogue) -> bool:
    """Whether the request groups by every column of the Computation's grain (its most common GROUP BY)."""
    grouped = set()
    for d in request.get("dimensions") or []:
        if d.get("column"):
            try:
                t, col, _ = cat.column(d["column"])
                grouped.add(f"{alias(t)}.{col}".lower())
            except Unfit:
                pass
    return all(aliased(g, c["tables"]).lower() in grouped for g in c.get("grain") or [])


# ---- checks on the request, before it is compiled


def said(value: str, question: str) -> bool:
    """Whether the question says a value: its words start words of the question ('PURCH' in
    'purchases', 'ACCT_MAINT' in 'ACCT_MAINT')."""
    norm = lambda x: re.sub(r"[^a-z0-9]+", " ", str(x).lower()).strip()
    v = norm(value)
    return bool(v) and f" {v}" in f" {norm(question)} "


def literals(sql: str) -> list[str]:
    try:
        tree = sqlglot.parse_one(sql, read="bigquery")
    except sqlglot.errors.ParseError:
        return []
    return [x.name for x in tree.find_all(exp.Literal) if x.is_string]


def request_tables(request: dict, cat: Catalogue) -> set[str]:
    """The tables a request names, directly or through its Computations."""
    refs = [d.get("column") for d in request.get("dimensions") or []]
    refs += [f.get("column") for f in request.get("filters") or []]
    refs += [(request.get("period") or {}).get("column")]
    out = set()
    for m in request.get("measures") or []:
        refs += [m.get("column"), *(w.get("column") for w in m.get("where") or [])]
    for x in [
        *(request.get("measures") or []),
        *(request.get("dimensions") or []),
        *(request.get("filters") or []),
    ]:
        out |= set((cat.computations.get(x.get("computation") or "") or {}).get("tables") or [])
    for ref in refs:
        if ref:
            try:
                out.add(cat.column(ref)[0])
            except Unfit:
                pass
    return out


def check(request: dict, cat: Catalogue, question: str, values: dict, chars: int) -> list[str]:
    """What the request does that the question doesn't say, and what the question says that the
    request leaves out, as notes for the LLM to reconsider. Checked:
      - a Computation's filter on a value the question doesn't say ('voice' in Voice Call Transfers,
        for a question about all calls): a definition brought from someone else's query
      - a value the log filters a column on that the question says ("voice calls") on a column the
        request neither filters nor groups by
    Values shorter than `chars` are not checked: codes like 'A' match too much."""
    notes = []
    for m in request.get("measures") or []:
        c = cat.computations.get(m.get("computation") or "")
        for f in (c or {}).get("filters") or []:
            unsaid = [v for v in literals(f) if len(v) >= chars and not said(v, question)]
            if unsaid:
                notes.append(
                    f"measure {m.get('alias')!r} uses {c['name']!r}, which keeps only rows where {f}; the "
                    f"question doesn't say {unsaid[0]!r}. Keep it only if the question means that restriction."
                )
    grouped, filtered = set(), set()  # the answer's groupings, and what restricts the whole answer
    for d in request.get("dimensions") or []:
        grouped |= {x for x in [d.get("column"), *(d.get("other_columns") or [])] if x}
    for f in request.get("filters") or []:
        c = cat.computations.get(f.get("computation") or "")
        filtered |= {f.get("column") or "", (c or {}).get("expression") or ""}
    each = []  # what restricts each measure
    for m in request.get("measures") or []:
        if m.get("ratio_of") or m.get("difference_of"):
            continue
        c = cat.computations.get(m.get("computation") or "") or {}
        own = {w.get("column") or "" for w in m.get("where") or []} | set(c.get("filters") or [])
        each.append(" ".join(own).lower())
    has = lambda texts, col: re.search(rf"\b{re.escape(col.lower())}\b", " ".join(texts).lower()) is not None
    reads = request_tables(request, cat)
    # A word the request's own tables and columns name ("card" in fct_card_transactions, "purchase" in
    # is_purchase) is accounted for by them, not a value to filter on.
    words = {
        w
        for t in reads
        for x in [t.rsplit(".", 1)[-1], *cat.tables[t]]
        for w in re.split(r"[^a-z0-9]+", x.lower())
        if w
    }
    norm = lambda v: re.sub(r"[^a-z0-9]+", " ", v.lower()).strip()
    for (t, col), vals in sorted(values.items()):
        if t not in reads:
            continue
        stated = [
            v
            for v in vals
            if isinstance(v, str)
            and len(v) >= chars
            and "%" not in v
            and said(v, question)
            and not any(w.startswith(norm(v)) for w in words)
        ]
        if not stated or has(filtered, col) or (each and all(has([x], col) for x in each)):
            continue
        if has(grouped, col) and len(stated) > 1:
            continue  # "voice and chat calls, by media type": the grouping shows each
        notes.append(
            f"the question says {stated[0]!r}, a value of {short(t)}.{col}, but the request doesn't "
            f"filter the answer on {col}" + (" (it only groups by it)." if has(grouped, col) else ".")
        )
    return notes


WEEK_TRUNC = (
    r"DATE_TRUNC\s*\(\s*(?:DATE\s*\(\s*)?[\w.`]*\b{col}\b[^,]*,\s*(ISOWEEK|WEEK\s*\(\s*(\w+)\s*\)|WEEK)\b"
)


def week_usage(texts: list[str], column: str) -> str:
    """How the log's queries truncate a column to weeks: 'week' (BigQuery's, from Sunday),
    'week_monday', or '' when they don't, or split evenly."""
    rx = re.compile(WEEK_TRUNC.format(col=re.escape(column)), re.I)
    monday = sunday = 0
    for text in texts:
        for unit, day in rx.findall(text or ""):
            if unit.upper() == "ISOWEEK" or day.upper() == "MONDAY":
                monday += 1
            elif not day or day.upper() == "SUNDAY":
                sunday += 1
    return "week_monday" if monday > sunday else "week" if sunday > monday else ""


def weeks(request: dict, cat: Catalogue, usage, question: str) -> list[str]:
    """A week grain as the log's queries truncate that column (usage(table, column) -> week_usage),
    unless the question names the day weeks start on. Changes the request; returns what changed."""
    if re.search(r"\b(monday|sunday|iso)\b", question, re.I):
        return []
    out = []
    for d in request.get("dimensions") or []:
        if d.get("grain") in ("week", "week_monday") and d.get("column"):
            try:
                t, col, _ = cat.column(d["column"])
            except Unfit:
                continue
            logged = usage(t, col)
            if logged and logged != d["grain"]:
                out.append(f"{d['alias']}: {d['grain']} -> {logged}, as the log truncates {short(t)}.{col}")
                d["grain"] = logged
    return out


def open_period(request: dict, today: str, question: str) -> list[str]:
    """A period that ends today, in a question that names no end ("on or after April 22"), is open:
    the data may run past today, and the question asked for all of it. Changes the request; returns
    what changed."""
    period = request.get("period") or {}
    end = str(period.get("to") or "").strip()
    if end != today or today in question:
        return []
    period["to"] = ""
    return [f"period: the end {today} is today, which the question doesn't name: left open"]


# ---- the plan


@dataclass
class Measure:
    alias: str
    expr: str  # the aggregate, with the conditions the request puts inside it
    filters: list[str]  # its Computation's filters: those every measure in its block shares go in WHERE
    table: str | None  # the table it aggregates; None for a COUNT(*) of the fact's rows
    tables: set[str]  # every table it reads
    safe: bool  # the same over a fan-out
    per: tuple[str, ...] = ()  # computed per these first (expressions over aliases)...
    then: str = ""  # ...then combined so


@dataclass
class Block:
    fact: str
    joins: list[tuple[str, str, str, str, bool]]  # (from table, its column, to table, its column, outer)
    where: list[str]
    dims: list[tuple[str, str]]  # (alias, expression)
    measures: list[tuple[str, str]]
    per: list[tuple[str, str]] = field(default_factory=list)
    then: dict[str, str] = field(default_factory=dict)


@dataclass
class Plan:
    blocks: list[Block]
    dims: list[str]
    outputs: list[str]  # the measures' aliases in the request's order, derived ones included
    derived: dict[str, tuple[str, str, str]]  # alias -> (ratio | difference, first, second)
    having: list[tuple[str, str, float]]
    order: list[tuple[str, bool]]
    limit: int
    listing: bool  # no measures: a list of rows


def measure(cat: Catalogue, m: dict, request: dict) -> Measure:
    per, tables, then = [], set(), (m.get("then") or "").upper()
    for p in m.get("per") or []:
        if p:
            t, col, _ = cat.column(p)
            per.append(f"{alias(t)}.{col}")
            tables.add(t)
    if m.get("computation"):
        c = cat.computations.get(m["computation"])
        if not c or c["kind"] != "measure":
            raise Unfit(f"no measure Computation {m['computation']!r}")
        reads = [t for t in c["tables"] if t in cat.tables]
        if len(reads) != len(c["tables"]):
            raise Unfit(f"Computation {c['name']!r} reads a table not offered")
        expr = aliased(c["expression"], reads)
        if LATEST.search(expr) and not per and not same_grain(c, request, cat):
            if not c.get("grain"):
                raise Unfit(f"{c['name']!r} is a latest value with no grain")
            per, then = [aliased(g, reads) for g in c["grain"]], then or "SUM"  # each entity's, summed
        if per and then not in THEN[1:]:
            raise Unfit(f"measure {m['alias']!r} is per entity with no way to combine it")
        return Measure(
            m["alias"],
            expr,
            [aliased(f, reads) for f in c["filters"]],
            reads[0],
            tables | set(reads),
            fanout_safe(expr),
            tuple(per),
            then if per else "",
        )
    agg = (m.get("aggregate") or "").upper()
    if agg not in AGGREGATES:
        raise Unfit(f"measure {m['alias']!r} has neither a Computation nor an aggregate")
    inline = [condition(cat, w, tables) for w in m.get("where") or []]
    table = None
    if m.get("column"):
        t, col, _ = cat.column(m["column"])
        table, ref = t, f"{alias(t)}.{col}"
        tables.add(t)
    elif agg == "COUNT":
        ref = "*"  # of the fact's rows: the fact comes from a column the request names
    else:
        raise Unfit(f"{agg} needs a column")
    if per and then not in THEN[1:]:
        raise Unfit(f"measure {m['alias']!r} is per entity with no way to combine it")
    expr = f"COUNT(DISTINCT {ref})" if agg == "COUNT_DISTINCT" else f"{agg}({ref})"
    return Measure(
        m["alias"],
        within(expr, inline),  # "count only these rows": a zero stays a zero
        [],
        table,
        tables,
        agg in ("COUNT_DISTINCT", "MIN", "MAX"),
        tuple(per),
        then if per else "",
    )


def plan(request: dict, cat: Catalogue, unique, hops: int = 2) -> Plan:
    """The request resolved into blocks. `unique(table, column) -> bool` says whether a join target is
    unique on its key. Raises Unfit when it can't be compiled."""
    if not request.get("fits"):
        raise Unfit(request.get("reason") or "the request says it doesn't fit")
    asked = request.get("measures") or []
    pair = lambda m: m.get("ratio_of") or m.get("difference_of")
    base = [measure(cat, m, request) for m in asked if not pair(m)]
    derived: dict[str, tuple[str, str, str]] = {}
    pending = [m for m in asked if pair(m)]
    while pending:  # a derived measure may come before the two it derives from
        known = {x.alias for x in base} | set(derived)
        ready = [m for m in pending if len(pair(m)) == 2 and all(x in known for x in pair(m))]
        if not ready:
            raise Unfit(f"derived measure {pending[0]['alias']!r} needs two other measures")
        for m in ready:
            derived[m["alias"]] = ("ratio" if m.get("ratio_of") else "difference", *pair(m))
        pending = [m for m in pending if m not in ready]
    if not base and not request.get("dimensions"):
        raise Unfit("no measure")

    # The measures into blocks: a measure joins the first block whose fact reaches its table without a
    # fan-out, or whose fact it can reach when that block's measures survive one; else it starts its own.
    reach = lambda a, b: cat.route(a, b, hops, unique) is not None
    groups: list[dict] = []
    for m in base:
        for g in groups:
            if (g["per"], bool(g["then"])) != (m.per, bool(m.then)):
                continue
            fact = g["fact"]
            if m.table is None or fact is None or m.table == fact or reach(fact, m.table):
                g["measures"].append(m)
                g["fact"] = fact or m.table
                break
            if all(x.safe or x.table == m.table for x in g["measures"]) and reach(m.table, fact):
                g["measures"].append(m)
                g["fact"] = m.table
                break
        else:
            groups.append({"fact": m.table, "measures": [m], "per": m.per, "then": m.then})
    if not base:
        groups.append({"fact": None, "measures": [], "per": (), "then": ""})
    facts = {g["fact"] for g in groups if g["fact"]}
    blocks = [resolve(g, request, cat, unique, hops, facts, len(groups) > 1) for g in groups]

    outputs = [m["alias"] for m in asked if not pair(m) or m["alias"] in derived]
    if len({name(a) for a in outputs + [d["alias"] for d in request.get("dimensions") or []]}) != len(
        outputs
    ) + len(request.get("dimensions") or []):
        raise Unfit("two outputs with the same name")
    having = []
    for h in request.get("having") or []:
        if h.get("alias") not in outputs:
            raise Unfit(f"a filter on {h.get('alias')!r}, which isn't a measure")
        try:
            having.append((h["alias"], h["op"], float(h["value"])))
        except (KeyError, TypeError, ValueError):
            raise Unfit(f"a filter on {h.get('alias')!r} with no number") from None
    limit = str(request.get("limit") or "").strip()  # the LLM may send 0, null or "null" for none
    return Plan(
        blocks,
        [d["alias"] for d in request.get("dimensions") or []],
        outputs,
        derived,
        having,
        [(o["alias"], bool(o.get("desc"))) for o in request.get("order") or [] if o.get("alias")],
        int(limit) if limit.isdigit() else 0,
        not base,
    )


def named_tables(cat: Catalogue, request: dict) -> set[str]:
    """The tables the request's dimensions and filters name."""
    out = set()
    refs = [
        c for d in request.get("dimensions") or [] for c in [d.get("column"), *(d.get("other_columns") or [])]
    ]
    refs += [f.get("column") for f in request.get("filters") or []]
    for ref in refs:
        if ref:
            try:
                out.add(cat.column(ref)[0])
            except Unfit:
                pass
    return out


def resolve(g: dict, request: dict, cat: Catalogue, unique, hops: int, facts: set, several: bool) -> Block:
    """One block at its fact. A block of row counts (or a list) counts the rows of the first table the
    request names that reaches the rest; other blocks fall back to another table the request names that
    reaches everything, when every measure on another table survives the fan-out."""
    if not g["fact"]:
        period = request.get("period") or {}
        named = [period.get("column") if (period.get("from") or period.get("to")) else None]
        named += [d.get("column") for d in request.get("dimensions") or []]
        named += [f.get("column") for f in request.get("filters") or []]
        candidates = list(dict.fromkeys(cat.column(c)[0] for c in named if c))
        if not candidates:
            raise Unfit("no measure over a table")
    else:
        fact = g["fact"]
        pinned = any(m.table is None for m in g["measures"])  # a count of rows is of its own table's rows
        tables = named_tables(cat, request) | {t for m in g["measures"] for t in m.tables}
        candidates = [fact] + [
            t
            for t in sorted(tables - {fact})
            if not pinned and all(m.safe or m.table == t for m in g["measures"])
        ]
    first = None
    for t in candidates:
        try:
            return resolve_at(t, g, request, cat, unique, hops, facts - {g["fact"]} | {t}, several)
        except Unfit as e:
            first = first or e
    raise first


def resolve_at(
    fact: str, g: dict, request: dict, cat: Catalogue, unique, hops: int, facts: set, several: bool
) -> Block:
    measures: list[Measure] = g["measures"]
    routes: dict[str, list | None] = {fact: []}
    used = {fact}

    def reachable(t: str) -> bool:
        if t not in routes:
            routes[t] = cat.route(fact, t, hops, unique)
        return routes[t] is not None

    def need(tables, what: str) -> None:
        for t in sorted(tables):
            if not reachable(t):
                raise Unfit(
                    f"no join from {short(fact)} to {short(t)} for {what} that doesn't multiply its rows"
                )
            used.add(t)

    for m in measures:
        need(m.tables, f"measure {m.alias!r}")

    dims = []
    for d in request.get("dimensions") or []:
        if d.get("computation"):
            c = cat.computations.get(d["computation"])
            if not c or c["kind"] != "dimension":
                raise Unfit(f"no dimension Computation {d['computation']!r}")
            need(c["tables"], f"dimension {d['alias']!r}")
            dims.append((d["alias"], aliased(c["expression"], c["tables"])))
            continue
        options = [c for c in [d.get("column"), *(d.get("other_columns") or [])] if c]
        if not options:
            raise Unfit(f"dimension {d['alias']!r} has no column")
        found = None
        for ref in options:  # the column named, another named for it, or one a trusted join equates it to
            t, col, typ = cat.column(ref)
            found = next(((t2, c2) for t2, c2 in [(t, col), *cat.equivalents(t, col)] if reachable(t2)), None)
            if found:
                break
        if not found:
            raise Unfit(
                f"no join from {short(fact)} to dimension {d['alias']!r} that doesn't multiply its rows"
            )
        t, col = found
        used.add(t)
        ref, typ = f"{alias(t)}.{col}", cat.tables[t].get(col, "")
        grain = d.get("grain") or ""
        if grain:
            base = f"DATE({ref})" if (typ or "").upper() in ("TIMESTAMP", "DATETIME") else ref
            ref = f"DATE_TRUNC({base}, {TRUNC[grain]})"
        dims.append((d["alias"], ref))

    filter_sets = [m.filters for m in measures]
    shared = set.intersection(*(set(f) for f in filter_sets)) if filter_sets else set()
    where = sorted(shared)
    others = facts - {fact}
    for f in request.get("filters") or []:
        reads: set[str] = set()
        if f.get("computation"):
            c = cat.computations.get(f["computation"])
            if not c or c["kind"] != "population":
                raise Unfit(f"no population Computation {f['computation']!r}")
            text, reads = aliased(c["expression"], c["tables"]), set(c["tables"])
        elif f.get("column"):
            text = condition(cat, f, reads)
        else:
            continue
        if several and reads & others and not all(reachable(t) for t in reads):
            continue  # about another block's fact rows: that block applies it
        need(reads, "a filter")
        where.append(text)
    period = request.get("period") or {}
    start, end = (str(period.get(k) or "").strip() for k in ("from", "to"))
    if period.get("column") and (start or end):  # "since April" has a start and no end
        found = None
        for ref in [period["column"], *(period.get("other_columns") or [])]:
            t, col, typ = cat.column(ref)
            if reachable(t):
                found = (t, col, typ)
                break
        if not found:
            raise Unfit(f"no date column for the period that {short(fact)} reaches")
        t, col, typ = found
        used.add(t)
        ref = f"{alias(t)}.{col}"
        if (typ or "").upper() in ("TIMESTAMP", "DATETIME"):
            ref = f"DATE({ref})"
        if start:
            where.append(f"{ref} >= DATE '{start}'")
        if end:
            where.append(f"{ref} <= DATE '{end}'")

    joins, joined = [], {fact}
    for t in sorted(used - {fact}):
        for a, ac, b, bc in routes[t]:
            if b in joined:
                continue
            joins.append((a, ac, b, bc, frozenset([(a, ac), (b, bc)]) in cat.outer))
            joined.add(b)
    if len({alias(t) for t in joined}) != len(joined):
        raise Unfit("two tables with the same name")
    return Block(
        fact,
        joins,
        where,
        dims,
        [(m.alias, within(m.expr, [f for f in m.filters if f not in shared])) for m in measures],
        [(f"per_{name(p)}", p) for p in g["per"]],
        {m.alias: m.then for m in measures if m.then},
    )


# ---- SQL


def compile_sql(request: dict, cat: Catalogue, unique, dialect: str = "bigquery", hops: int = 2) -> str:
    """The request as SQL. Raises Unfit when it can't be compiled."""
    return render_sql(plan(request, cat, unique, hops), dialect)


def plan_tables(p: Plan) -> list[str]:
    """The tables a plan reads: each block's fact and the tables it joins."""
    return sorted({t for b in p.blocks for t in [b.fact, *(j[2] for j in b.joins)] if t})


def from_sql(b: Block) -> str:
    sql = f"FROM `{b.fact}` AS {alias(b.fact)}"
    for a, ac, t, tc, outer in b.joins:
        sql += (
            f"\n{'LEFT JOIN' if outer else 'JOIN'} `{t}` AS {alias(t)} ON {alias(t)}.{tc} = {alias(a)}.{ac}"
        )
    if b.where:
        sql += "\nWHERE " + "\n  AND ".join(f"({w})" for w in b.where)
    return sql


def group_by(n: int) -> str:
    return f"\nGROUP BY {', '.join(str(i + 1) for i in range(n))}" if n else ""


def block_sql(b: Block) -> str:
    """A block as one row per dimension value: its dimensions and measures, by name."""
    if not b.per:
        cols = [f"{e} AS {name(a)}" for a, e in b.dims + b.measures]
        return "SELECT " + ",\n  ".join(cols) + "\n" + from_sql(b) + group_by(len(b.dims))
    inner = "SELECT " + ", ".join(f"{e} AS {name(a)}" for a, e in b.dims + b.per + b.measures)
    inner += "\n" + from_sql(b) + group_by(len(b.dims) + len(b.per))
    outer = [name(a) for a, _ in b.dims] + [f"{b.then[a]}({name(a)}) AS {name(a)}" for a, _ in b.measures]
    return f"SELECT {', '.join(outer)}\nFROM (\n{inner}\n)" + group_by(len(b.dims))


def outputs_sql(p: Plan, value) -> dict[str, str]:
    """Each output's expression: a measure's, from `value(alias)`, or a derived one's over two others."""
    out: dict[str, str] = {a: value(a) for a in p.outputs if a not in p.derived}
    for a, (op, x, y) in p.derived.items():  # in the order they resolve
        out[a] = f"SAFE_DIVIDE({out[x]}, {out[y]})" if op == "ratio" else f"({out[x]}) - ({out[y]})"
    return out


def render_sql(p: Plan, dialect: str = "bigquery") -> str:
    b = p.blocks[0]
    if p.listing:
        sql = "SELECT DISTINCT " + ",\n  ".join(f"{e} AS {name(a)}" for a, e in b.dims) + "\n" + from_sql(b)
    elif len(p.blocks) == 1 and not b.per:  # one aggregate query
        exprs = outputs_sql(p, dict(b.measures).__getitem__)
        sql = "SELECT " + ",\n  ".join(
            [f"{e} AS {name(a)}" for a, e in b.dims] + [f"{exprs[a]} AS {name(a)}" for a in p.outputs]
        )
        sql += "\n" + from_sql(b) + group_by(len(b.dims))
        if p.having:
            sql += "\nHAVING " + " AND ".join(f"({exprs[a]}) {op} {v:g}" for a, op, v in p.having)
    else:  # each block one row per dimension value, joined on the dimensions
        names = [f"{alias(x.fact)}_{i + 1}" for i, x in enumerate(p.blocks)]
        sql = "WITH " + ",\n".join(f"{n} AS (\n{block_sql(x)}\n)" for n, x in zip(names, p.blocks))
        exprs = outputs_sql(p, name)
        dims = [name(a) for a in p.dims]
        sql += "\nSELECT " + ",\n  ".join(dims + [f"{exprs[a]} AS {name(a)}" for a in p.outputs])
        sql += f"\nFROM {names[0]}"
        for n in names[1:]:
            sql += f"\nFULL JOIN {n} USING ({', '.join(dims)})" if dims else f"\nCROSS JOIN {n}"
        if p.having:
            sql += "\nWHERE " + " AND ".join(f"({exprs[a]}) {op} {v:g}" for a, op, v in p.having)
    if p.order:
        sql += "\nORDER BY " + ", ".join(f"{name(a)}{' DESC' if desc else ''}" for a, desc in p.order)
    if p.limit > 0:
        sql += f"\nLIMIT {p.limit}"
    try:
        tree = sqlglot.parse_one(sql, read="bigquery")
    except sqlglot.errors.ParseError as e:
        raise Unfit(f"compiled SQL doesn't parse: {str(e)[:200]}") from None
    return tree.sql(dialect=dialect, pretty=True)


# ---- Cypher

CYPHER_TRUNC = {"DAY": "day", "MONTH": "month", "QUARTER": "quarter", "YEAR": "year"}
CYPHER_CMP = {exp.EQ: "=", exp.NEQ: "<>", exp.GT: ">", exp.GTE: ">=", exp.LT: "<", exp.LTE: "<="}
CYPHER_AGG = {exp.Avg: "avg", exp.Min: "min", exp.Max: "max"}  # a SUM keeps SQL's NULL (cypher_expr)
CYPHER_ARITH = {exp.Add: "+", exp.Sub: "-", exp.Mul: "*", exp.Mod: "%"}


def compile_cypher(
    request: dict, cat: Catalogue, unique, labels: dict[str, str], model: dict, hops: int = 2
) -> str:
    """The request as Cypher over the Virtual Graph model (schema.json's entities). Raises Unfit."""
    return render_cypher(plan(request, cat, unique, hops), labels, model)


def render_cypher(p: Plan, labels: dict[str, str], model: dict, guard=None) -> str:
    """The plan over the Virtual Graph: each table a label (`labels`: table id -> label), each join a
    relationship, each column a property. Raises Unfit for what the graph can't express. `guard`, for
    another target of the same model (memory: qlsc/memory.py), adds its conditions on every node
    (guard.node(variable, label)) and relationship (guard.relationship(variable)) the query matches."""
    if len(p.blocks) != 1:
        raise Unfit("several fact tables: Virtual Graph has no CALL subquery to combine them")
    b = p.blocks[0]
    nodes = {n["label"]: n for n in model["nodes"]}
    tables = [b.fact] + [j[2] for j in b.joins]
    for t in tables:
        if labels.get(t) not in nodes:
            raise Unfit(f"{short(t)} is not in the virtual graph")
    label = {alias(t): labels[t] for t in tables}
    props = {
        alias(t): {x["column"].lower(): x["name"] for x in nodes[labels[t]]["properties"]} for t in tables
    }
    # A column an outer join equates to its pointing column is read there, so the relationship isn't
    # walked and a fact row with no match keeps its null group (Virtual Graph has no OPTIONAL MATCH).
    same = {(alias(t), tc.lower()): (alias(a), ac) for a, ac, t, tc, outer in b.joins if outer}
    used: set[str] = set()

    def column(c: exp.Column) -> str:
        v, col = c.table, c.name
        while (v, col.lower()) in same:
            v, col = same[(v, col.lower())]
        if v not in props:
            raise Unfit(f"{c.sql()} reads a table not in the query")
        prop = props[v].get(col.lower())
        if not prop:
            raise Unfit(f"{label[v]} has no property for {col}")
        used.add(v)
        return f"{v}.{prop}"

    cy = lambda sql: cypher_expr(sqlglot.parse_one(sql, read="bigquery"), column)
    dims = [(name(a), cy(e)) for a, e in b.dims]
    per = [(name(a), cy(e)) for a, e in b.per]
    meas = [(name(a), cy(e)) for a, e in b.measures]
    where = [cy(w) for w in b.where]

    needed = used | {alias(b.fact)}
    for a, _, t, _, _ in reversed(b.joins):
        if alias(t) in needed:
            needed.add(alias(a))
    lines = [f"MATCH ({alias(b.fact)}:{labels[b.fact]})"]
    walked = [(a, ac, t, tc, outer) for a, ac, t, tc, outer in b.joins if alias(t) in needed]
    rels = [f"r{i}" if guard else "" for i in range(len(walked))]
    # With a guard the target is a standard database (memory), which has OPTIONAL MATCH: an outer join that
    # nothing filters on keeps its null group there, as the SQL's does, and its guard goes in its own WHERE.
    optional: set[str] = set()
    for a, _, t, _, outer in walked:
        if guard and (alias(a) in optional or (outer and not any(f"{alias(t)}." in w for w in where))):
            optional.add(alias(t))
    inner = [(j, r) for j, r in zip(walked, rels) if alias(j[2]) not in optional]
    lines += [f"MATCH {relationship(a, ac, t, tc, labels, model, r)}" for (a, ac, t, tc, _), r in inner]
    if guard:
        matched = [(alias(b.fact), labels[b.fact])] + [(alias(j[2]), labels[j[2]]) for j, _ in inner]
        where += [g for v, lb in matched for g in guard.node(v, lb)] + [
            g for _, r in inner for g in guard.relationship(r)
        ]
    if where:
        lines.append("WHERE " + "\n  AND ".join(f"({w})" for w in where))
    for (a, ac, t, tc, _), r in zip(walked, rels):
        if alias(t) in optional:
            conditions = guard.node(alias(t), labels[t]) + guard.relationship(r)
            lines.append(f"OPTIONAL MATCH {relationship(a, ac, t, tc, labels, model, r)}")
            lines.append("WHERE " + " AND ".join(f"({c})" for c in conditions))
    tail = []
    if p.order:
        tail.append("ORDER BY " + ", ".join(f"{name(a)}{' DESC' if desc else ''}" for a, desc in p.order))
    if p.limit > 0:
        tail.append(f"LIMIT {p.limit}")
    if p.listing:
        return "\n".join([*lines, "RETURN DISTINCT " + ", ".join(f"{e} AS {a}" for a, e in dims), *tail])
    if not (p.derived or p.having or per):
        return "\n".join([*lines, "RETURN " + ", ".join(f"{e} AS {a}" for a, e in dims + meas), *tail])
    keys = [a for a, _ in dims]
    if per:  # each entity's value first, then combined
        lines.append("WITH " + ", ".join(f"{e} AS {a}" for a, e in dims + per + meas))
        dims = [(a, a) for a in keys]
        meas = [(name(a), f"{b.then[a].lower()}({name(a)})") for a, _ in b.measures]
    lines.append("WITH " + ", ".join(f"{e} AS {a}" for a, e in dims + meas))
    exprs = {a: name(a) for a in p.outputs if a not in p.derived}
    for a, (op, x, y) in p.derived.items():
        x, y = exprs[x], exprs[y]
        exprs[a] = (
            f"CASE WHEN {y} = 0 THEN null ELSE toFloat({x}) / {y} END" if op == "ratio" else f"{x} - {y}"
        )
    if p.having:
        lines.append(
            "WHERE " + " AND ".join(f"{exprs[a]} {op.replace('!=', '<>')} {v:g}" for a, op, v in p.having)
        )
    lines.append("RETURN " + ", ".join(keys + [f"{exprs[a]} AS {name(a)}" for a in p.outputs]))
    return "\n".join(lines + tail)


def relationship(a: str, ac: str, t: str, tc: str, labels: dict[str, str], model: dict, var: str = "") -> str:
    """A join step as a relationship: forwards, from the pointing column to the key, or back; `var` names
    it."""
    step = lambda *x: tuple(str(v).lower() for v in x)
    for r in model["relationships"]:
        key = r["end"]["keys"][0]
        have = step(
            r["start"]["targetEntity"], r["end"]["targetEntity"], key["relationshipColumn"], key["nodeColumn"]
        )
        if have == step(labels[a], labels[t], ac, tc):
            return f"({alias(a)})-[{var}:{r['label']}]->({alias(t)}:{labels[t]})"
        if have == step(labels[t], labels[a], tc, ac):
            return f"({alias(a)})<-[{var}:{r['label']}]-({alias(t)}:{labels[t]})"
    raise Unfit(f"no relationship for the join {short(a)}.{ac} = {short(t)}.{tc}")


def date_literal(e: exp.Expression) -> str | None:
    """A DATE literal's day, or None."""
    if isinstance(e, exp.Cast) and e.to.is_type("date") and isinstance(e.this, exp.Literal):
        return e.this.name
    return None


def cypher_expr(e: exp.Expression, column) -> str:
    """A SQL expression (BigQuery's tree) as Cypher, with `column(c)` for a column; Unfit for what has no
    translation here."""
    c = lambda x: cypher_expr(x, column)
    if isinstance(e, exp.Paren):
        return f"({c(e.this)})"
    if isinstance(e, exp.Column):
        return column(e)
    if isinstance(e, exp.Literal):
        return e.name if not e.is_string else "'" + e.name.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if isinstance(e, exp.Boolean):
        return "true" if e.this else "false"
    if isinstance(e, exp.Null):
        return "null"
    if (day := date_literal(e)) is not None:
        return f"date('{day}')"
    if isinstance(e, exp.Count):
        arg = e.this
        if arg is None or isinstance(arg, exp.Star):
            return "count(*)"
        if isinstance(arg, exp.Distinct):
            return f"count(DISTINCT {', '.join(c(x) for x in arg.expressions)})"
        return f"count({c(arg)})"
    if isinstance(e, exp.Sum) and not isinstance(e.this, exp.Distinct):
        # SQL's SUM of no values is NULL, Cypher's sum() 0: a group whose values are all null keeps SQL's NULL
        x = c(e.this)
        return f"CASE WHEN count({x}) = 0 THEN null ELSE sum({x}) END"
    if type(e) in CYPHER_AGG and not isinstance(e.this, exp.Distinct):
        return f"{CYPHER_AGG[type(e)]}({c(e.this)})"
    if isinstance(e, exp.CountIf):
        return f"count(CASE WHEN {c(e.this)} THEN 1 END)"
    if isinstance(e, exp.If):
        other = e.args.get("false")
        orelse = f" ELSE {c(other)}" if other is not None else ""
        return f"CASE WHEN {c(e.this)} THEN {c(e.args['true'])}{orelse} END"
    if isinstance(e, exp.Case):
        out = "CASE" + (f" {c(e.this)}" if e.this else "")
        for w in e.args.get("ifs") or []:
            out += f" WHEN {c(w.this)} THEN {c(w.args['true'])}"
        if e.args.get("default") is not None:
            out += f" ELSE {c(e.args['default'])}"
        return out + " END"
    if isinstance(e, exp.SafeDivide):
        y = c(e.expression)
        return f"CASE WHEN {y} = 0 THEN null ELSE toFloat({c(e.this)}) / {y} END"
    if isinstance(e, exp.Div):
        return f"toFloat({c(e.this)}) / {c(e.expression)}"
    if type(e) in CYPHER_ARITH:
        return f"{c(e.this)} {CYPHER_ARITH[type(e)]} {c(e.expression)}"
    if isinstance(e, exp.Neg):
        return f"-{c(e.this)}"
    if type(e) in CYPHER_CMP:
        if isinstance(e.this, exp.Date) and (day := date_literal(e.expression)) is not None:
            return timestamp_on(c(e.this.this), CYPHER_CMP[type(e)], day)
        return f"{c(e.this)} {CYPHER_CMP[type(e)]} {c(e.expression)}"
    if isinstance(e, exp.And):
        return f"{c(e.this)} AND {c(e.expression)}"
    if isinstance(e, exp.Or):
        return f"{c(e.this)} OR {c(e.expression)}"
    if isinstance(e, exp.Not):
        return f"NOT ({c(e.this)})"
    if isinstance(e, exp.Is) and isinstance(e.expression, exp.Null):
        return f"{c(e.this)} IS NULL"
    if isinstance(e, exp.Is) and isinstance(e.expression, exp.Boolean):
        return f"{c(e.this)} = {c(e.expression)}"
    if isinstance(e, exp.In) and e.expressions:
        return f"{c(e.this)} IN [{', '.join(c(x) for x in e.expressions)}]"
    if isinstance(e, exp.Between):
        return f"{c(e.this)} >= {c(e.args['low'])} AND {c(e.this)} <= {c(e.args['high'])}"
    if isinstance(e, exp.Coalesce):
        return f"coalesce({', '.join(c(x) for x in [e.this, *e.expressions])})"
    if isinstance(e, exp.DateTrunc):
        unit = e.args.get("unit")
        if isinstance(unit, exp.WeekStart) and unit.this.name.upper() == "MONDAY":
            period = "week"  # Cypher's weeks start on Monday; BigQuery's plain WEEK on Sunday
        else:
            period = CYPHER_TRUNC.get(unit.name.upper() if unit is not None else "")
        if not period:
            raise Unfit(f"no Cypher truncation to {unit.sql() if unit is not None else 'no unit'}")
        target = e.this.this if isinstance(e.this, exp.Date) else e.this
        return f"date.truncate('{period}', {c(target)})"
    raise Unfit(f"no Cypher for {type(e).__name__}: {e.sql()[:80]}")


def timestamp_on(prop: str, op: str, day: str) -> str:
    """DATE(timestamp) compared with a day, as the timestamp against midnights: Virtual Graph has no
    date() of a property."""
    d = dt.date.fromisoformat(day)
    nxt = d + dt.timedelta(days=1)
    at = lambda x: f"datetime('{x.isoformat()}T00:00:00Z')"
    on = f"{prop} >= {at(d)} AND {prop} < {at(nxt)}"
    return {
        ">=": f"{prop} >= {at(d)}",
        ">": f"{prop} >= {at(nxt)}",
        "<": f"{prop} < {at(d)}",
        "<=": f"{prop} < {at(nxt)}",
        "=": on,
    }.get(op, f"NOT ({on})")


# ---- the prompt's options


def options_text(cat: Catalogue, values: dict, frozen: set[str] = frozenset()) -> str:
    """The tables, their columns (with the values the log filters them on), and the joins, for the prompt.
    A frozen table (nothing writes it, and no production process reads it) says so: its data has stopped."""
    lines = []
    for t, cols in cat.tables.items():
        parts = []
        for c, typ in list(cols.items())[:60]:
            seen = values.get((t, c))
            parts.append(
                f"{c} {typ}" + (f" (values seen: {', '.join(repr(v) for v in seen)})" if seen else "")
            )
        stale = (
            " (frozen: nothing writes it any more and no production process reads it)" if t in frozen else ""
        )
        lines.append(f"`{short(t)}`{stale}: " + ", ".join(parts))
    return "\n".join(lines)


def computations_text(cat: Catalogue) -> str:
    if not cat.computations:
        return "(none)"
    out = []
    for c in cat.computations.values():
        with_ = f"; with {' AND '.join(c['filters'])}" if c["filters"] else ""
        out.append(
            f"- {c['id']} ({c['kind']}) {c['name']}: {c['expression']}{with_}; on {', '.join(short(t) for t in c['tables'])}"
        )
    return "\n".join(out)


def joins_text(joins: list[dict]) -> str:
    return "\n".join(f"{short(j['a'])}.{j['ac']} = {short(j['b'])}.{j['bc']}" for j in joins) or "(none)"

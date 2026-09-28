"""The compiler: a question as a typed request, compiled to SQL (plans/2026-09-28-compiler.md).

The LLM fills a request from the options the semantic layer offers (prompts/compile_*.md): the
measures (a Computation the log defines, an aggregate over a column, or a ratio), the dimensions, the
filters, the period, and a top N if asked. This module turns the request into SQL, deterministically:
  - the fact is the first measure's table; every other table joins to it along the layer's trusted
    joins, at most two hops, and only to a table unique on its join column (checked in the warehouse,
    cached), so no join multiplies the fact's rows; each is the join type the log mostly uses for it
    (an outer join keeps the fact's rows with no match, as a null group; an inner join drops them)
  - each table's alias is its own name, so a Computation's expression drops in as the log wrote it
  - a Computation's filters that every measure shares go in WHERE with the request's own; a
    measure's other filters, and the conditions a request puts inside a measure ("count only clicked
    rows"), wrap its aggregate's argument, so a group with none still shows zero
  - a latest-value Computation (ARRAY_AGG ... LIMIT 1) compiles only at its own grain; summing it over
    a coarser one needs two steps, and falls back
  - literals are typed from the column; a period on a timestamp filters on its date
A request that doesn't fit, names what the layer lacks, or can't be joined raises Unfit, and the SQL
route falls back to free writing. The SQL is written in BigQuery's dialect and rendered in the
warehouse's through sqlglot.
"""

from __future__ import annotations

import json
import re
from collections import deque

import sqlglot
from sqlglot import exp

from qlsc.names import short

OPS = ["=", "!=", "IN", "NOT IN", ">", ">=", "<", "<=", "IS TRUE", "IS FALSE", "IS NULL", "IS NOT NULL"]
AGGREGATES = ["COUNT", "COUNT_DISTINCT", "SUM", "AVG", "MIN", "MAX"]
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
                    "ratio_of": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "two other measures' aliases: numerator, denominator",
                    },
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
            },
            "description": "empty fields when the question names no period",
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
    return all(g.lower() in grouped for g in c.get("grain") or [])


class Unfit(Exception):
    """The request can't be compiled; the route writes free SQL instead."""


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
        table, _, col = ref.rpartition(".")
        t = self.by_short.get(table) or (table if table in self.tables else None)
        if not t:
            raise Unfit(f"no table {table!r} among those offered")
        cols = {c.lower(): (c, typ) for c, typ in self.tables[t].items()}
        if col.lower() not in cols:
            raise Unfit(f"{short(t)} has no column {col!r}")
        c, typ = cols[col.lower()]
        return t, c, typ

    def path(self, start: str, goal: str, hops: int) -> list[tuple[str, str, str, str]]:
        """The shortest join path, as (from table, its column, to table, its column) steps."""
        if start == goal:
            return []
        seen, queue = {start}, deque([(start, [])])
        while queue:
            t, steps = queue.popleft()
            if len(steps) == hops:
                continue
            for other, mine, theirs in sorted(self.edges.get(t, [])):
                if other in seen:
                    continue
                route = [*steps, (t, mine, other, theirs)]
                if other == goal:
                    return route
                seen.add(other)
                queue.append((other, route))
        raise Unfit(f"no trusted join from {short(start)} to {short(goal)} within {hops} hops")


def alias(table: str) -> str:
    return table.rsplit(".", 1)[-1]


def name(text: str) -> str:
    """An output column's name as a plain identifier (the LLM may write spaces or symbols)."""
    return re.sub(r"\W+", "_", str(text)).strip("_") or "value"


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


def compile_sql(request: dict, cat: Catalogue, unique, dialect: str = "bigquery", hops: int = 2) -> str:
    """The request as SQL. `unique(table, column) -> bool` says whether a join target is unique on its
    key. Raises Unfit when it can't be compiled."""
    if not request.get("fits"):
        raise Unfit(request.get("reason") or "the request says it doesn't fit")
    measures = request.get("measures") or []
    if not measures:
        raise Unfit("no measure")
    used: set[str] = set()
    compiled, filter_sets, fact = [], [], None
    for m in measures:
        if m.get("ratio_of"):
            continue
        if m.get("computation"):
            c = cat.computations.get(m["computation"])
            if not c or c["kind"] != "measure":
                raise Unfit(f"no measure Computation {m['computation']!r}")
            tables = [t for t in c["tables"] if t in cat.tables]
            if len(tables) != len(c["tables"]):
                raise Unfit(f"Computation {c['name']!r} reads a table not offered")
            used.update(tables)
            fact = fact or tables[0]
            expr, own, inline = c["expression"], list(c["filters"]), []
            if LATEST.search(expr) and not same_grain(c, request, cat):
                raise Unfit(
                    f"{c['name']!r} is a latest value per {', '.join(c['grain'])}: summing it needs two steps"
                )
        else:
            agg = (m.get("aggregate") or "").upper()
            if agg not in AGGREGATES:
                raise Unfit(f"measure {m['alias']!r} has neither a Computation nor an aggregate")
            own, inline = [], [condition(cat, w, used) for w in m.get("where") or []]
            if m.get("column"):
                t, col, _ = cat.column(m["column"])
                used.add(t)
                fact = fact or t
                ref = f"{alias(t)}.{col}"
            elif agg == "COUNT":
                ref = "*"  # of the fact's rows: the fact comes from a column the request names
            else:
                raise Unfit(f"{agg} needs a column")
            expr = f"COUNT(DISTINCT {ref})" if agg == "COUNT_DISTINCT" else f"{agg}({ref})"
        compiled.append((m["alias"], within(expr, inline)))  # "count only these rows": a zero stays a zero
        filter_sets.append(own)
    shared = set.intersection(*(set(f) for f in filter_sets)) if filter_sets else set()
    select_measures = [
        (a, within(e, [f for f in fs if f not in shared])) for (a, e), fs in zip(compiled, filter_sets)
    ]
    by_alias = dict(select_measures)
    for m in measures:
        if m.get("ratio_of"):
            if len(m["ratio_of"]) != 2 or any(x not in by_alias for x in m["ratio_of"]):
                raise Unfit(f"ratio {m['alias']!r} needs two measures defined before it")
            num, den = (by_alias[x] for x in m["ratio_of"])
            by_alias[m["alias"]] = f"SAFE_DIVIDE({num}, {den})"
    outputs = [(m["alias"], by_alias[m["alias"]]) for m in measures if not m.get("hidden")]

    dims = []
    for d in request.get("dimensions") or []:
        if d.get("computation"):
            c = cat.computations.get(d["computation"])
            if not c or c["kind"] != "dimension":
                raise Unfit(f"no dimension Computation {d['computation']!r}")
            used.update(c["tables"])
            dims.append((d["alias"], c["expression"]))
            continue
        t, col, typ = cat.column(d["column"])
        used.add(t)
        ref = f"{alias(t)}.{col}"
        grain = d.get("grain") or ""
        if grain:
            base = f"DATE({ref})" if (typ or "").upper() in ("TIMESTAMP", "DATETIME") else ref
            ref = f"DATE_TRUNC({base}, {TRUNC[grain]})"
        dims.append((d["alias"], ref))

    where = sorted(shared)
    for f in request.get("filters") or []:
        if f.get("computation"):
            c = cat.computations.get(f["computation"])
            if not c or c["kind"] != "population":
                raise Unfit(f"no population Computation {f['computation']!r}")
            used.update(c["tables"])
            where.append(c["expression"])
        elif f.get("column"):
            where.append(condition(cat, f, used))
    period = request.get("period") or {}
    start, end = (str(period.get(k) or "").strip() for k in ("from", "to"))
    if period.get("column") and (start or end):  # "since April" has a start and no end
        t, col, typ = cat.column(period["column"])
        used.add(t)
        fact = fact or t
        ref = f"{alias(t)}.{col}"
        if (typ or "").upper() in ("TIMESTAMP", "DATETIME"):
            ref = f"DATE({ref})"
        if start:
            where.append(f"{ref} >= DATE '{start}'")
        if end:
            where.append(f"{ref} <= DATE '{end}'")

    if not fact:  # only COUNT(*) measures: the fact is the first table a dimension or filter names
        named = [d.get("column") for d in request.get("dimensions") or []] + [
            f.get("column") for f in request.get("filters") or []
        ]
        fact = next((cat.column(c)[0] for c in named if c), None)
        if not fact:
            raise Unfit("no measure over a table")
    joins, joined = [], {fact}
    for t in sorted(used - {fact}):
        for a, ac, b, bc in cat.path(fact, t, hops):
            if b in joined:
                continue
            if not unique(b, bc):
                raise Unfit(f"joining {short(b)} on {bc} would multiply {short(a)}'s rows")
            kind = "LEFT JOIN" if frozenset([(a, ac), (b, bc)]) in cat.outer else "JOIN"
            joins.append(f"{kind} `{b}` AS {alias(b)} ON {alias(b)}.{bc} = {alias(a)}.{ac}")
            joined.add(b)
    if len({alias(t) for t in joined}) != len(joined):
        raise Unfit("two tables with the same name")

    sql = "SELECT " + ",\n  ".join(
        [f"{e} AS {name(a)}" for a, e in dims] + [f"{e} AS {name(a)}" for a, e in outputs]
    )
    sql += f"\nFROM `{fact}` AS {alias(fact)}"
    if joins:
        sql += "\n" + "\n".join(joins)
    if where:
        sql += "\nWHERE " + "\n  AND ".join(f"({w})" for w in where)
    if dims:
        sql += "\nGROUP BY " + ", ".join(str(i + 1) for i in range(len(dims)))
    order = [f"{name(o['alias'])}{' DESC' if o.get('desc') else ''}" for o in request.get("order") or []]
    if order:
        sql += "\nORDER BY " + ", ".join(order)
    limit = str(request.get("limit") or "").strip()
    if limit.isdigit() and int(limit) > 0:  # the LLM may send 0, null or "null" for none
        sql += f"\nLIMIT {int(limit)}"
    try:
        tree = sqlglot.parse_one(sql, read="bigquery")
    except sqlglot.errors.ParseError as e:
        raise Unfit(f"compiled SQL doesn't parse: {str(e)[:200]}") from None
    return tree.sql(dialect=dialect, pretty=True)


def options_text(cat: Catalogue, values: dict) -> str:
    """The tables, their columns (with the values the log filters them on), and the joins, for the prompt."""
    lines = []
    for t, cols in cat.tables.items():
        parts = []
        for c, typ in list(cols.items())[:60]:
            seen = values.get((t, c))
            parts.append(
                f"{c} {typ}" + (f" (values seen: {', '.join(repr(v) for v in seen)})" if seen else "")
            )
        lines.append(f"`{short(t)}`: " + ", ".join(parts))
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


def dump(request: dict) -> str:
    return json.dumps(request, indent=1, default=str)

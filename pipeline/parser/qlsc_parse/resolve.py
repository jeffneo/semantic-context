"""T2: resolve one shape against the catalog and extract its parse record.

One `qualify` (alias, CTE, `*` and USING resolution against the catalog), then one
pass over the scopes. Everything is attributed to base columns: a column read
through a CTE, a subquery or an UNNEST is traced back to the table column it came
from, with how it was changed on the way (passthrough, rename, transform,
aggregate). That trace is what turns "c.site = s.site" in an outer query into a
join between two physical columns, and what gives write statements column lineage.

Nothing is dropped silently: anything that does not resolve is listed in
`unresolved`, and the record's status says ok / partial / error.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import Scope, traverse_scope

from . import PARSER_ID
from .catalog import Catalog, fqn, is_system
from .fingerprint import literal_slots

KIND_RANK = {"direct": 0, "passthrough": 1, "rename": 2, "unnest": 3, "transform": 4, "aggregate": 5}
COMPARISONS = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Like, exp.ILike)
COMPARED = tuple(getattr(exp, n) for n in ("Corr", "CovarPop", "CovarSamp", "Sub") if hasattr(exp, n))
EXPECTED_MISSES = {"transient", "system table"}
CLAUSE_ROLE = {"expressions": "project", "where": "filter", "having": "filter", "qualify": "filter",
               "group": "group", "order": "order", "joins": "join", "from_": "from", "from": "from"}


@dataclass(frozen=True)
class Origin:
    """A base column a value came from, and what happened to it on the way."""
    table: str
    column: str
    kind: str = "direct"
    fns: tuple = ()
    path: str | None = None
    control: bool = False       # decides the value (CASE/IF condition, ORDER BY in an aggregate) but is not it

    def via(self, kind: str, fns=(), control: bool = False) -> "Origin":
        k = kind if KIND_RANK[kind] > KIND_RANK[self.kind] else self.kind
        if self.kind == "direct" and kind in ("passthrough", "rename"):
            k = kind
        return Origin(self.table, self.column, k, tuple(fns) + self.fns, self.path, self.control or control)


@dataclass
class Ctx:
    catalog: Catalog
    reads: dict = field(default_factory=dict)
    joins: dict = field(default_factory=dict)
    filters: list = field(default_factory=list)
    tables: dict = field(default_factory=dict)
    unresolved: dict = field(default_factory=dict)
    scan: dict = field(default_factory=lambda: {"select_star": False, "limit": None,
                                                "partition_filter": {}})
    memo: dict = field(default_factory=dict)
    scope_of: dict = field(default_factory=dict)
    comparisons: dict = field(default_factory=dict)

    def miss(self, kind: str, name: str, reason: str):
        self.unresolved.setdefault((kind, name), reason)


# ----------------------------------------------------------------------------- helpers

def statement_type(t: exp.Expression) -> str:
    if isinstance(t, (exp.Select, exp.SetOperation, exp.Subquery)):
        return "SELECT"
    if isinstance(t, exp.Create):
        kind = (t.args.get("kind") or "").upper()
        if kind == "VIEW":
            return "CREATE_VIEW"
        return "CREATE_TABLE_AS_SELECT" if t.expression else f"CREATE_{kind or 'TABLE'}"
    return {exp.Insert: "INSERT", exp.Merge: "MERGE", exp.Delete: "DELETE",
            exp.Update: "UPDATE"}.get(type(t), type(t).__name__.upper())


def fn_name(n: exp.Expression) -> str:
    if isinstance(n, exp.Cast):
        return ("SAFE_CAST" if isinstance(n, exp.TryCast) else "CAST") + f"<{n.to.sql('bigquery')}>"
    if isinstance(n, exp.Func):
        # the dialect's own spelling (sqlglot's class names differ: Pad -> LPAD)
        head = n.sql(dialect="bigquery").split("(", 1)[0].strip().upper()
        return head if head and len(head) <= 40 and " " not in head else n.sql_name()
    return type(n).__name__.upper()


def unwrap(e: exp.Expression) -> tuple[exp.Column | None, list[str]]:
    """A join/filter side that is one column under a chain of functions -> (column, wraps)."""
    if any(isinstance(x, (exp.Select, exp.Subquery)) for x in e.walk()):
        return None, []
    cols = [c for c in e.find_all(exp.Column) if not isinstance(c.this, exp.Star)]
    if len(cols) != 1:
        return None, []
    col, wraps, n = cols[0], [], cols[0].parent
    top = col
    while isinstance(top.parent, exp.Dot):
        top = top.parent
    n = top.parent
    while n is not None and n is not e.parent:
        if not isinstance(n, (exp.Dot, exp.Paren)):
            wraps.append(fn_name(n))
        if n is e:
            break
        n = n.parent
    return col, wraps[::-1]


def is_constant(e: exp.Expression) -> bool:
    return not any(isinstance(x, (exp.Column, exp.Select, exp.Subquery)) for x in e.walk())


def slots_in(e: exp.Expression) -> list[int]:
    return [n.meta["slot"] for n in e.walk() if n.meta and "slot" in n.meta]


def field_path(col: exp.Column) -> str | None:
    parts, n = [], col
    while isinstance(n.parent, exp.Dot) and n.parent.this is n:
        n = n.parent
        parts.append(n.expression.name)
    return ".".join(parts) or None


def clause_of(node: exp.Expression, sel: exp.Expression) -> tuple[str | None, list[exp.Expression]]:
    """Arg key of the Select clause that holds `node`, plus the ancestors on the way."""
    chain, child = [], node
    while child.parent is not None and child.parent is not sel:
        chain.append(child.parent)
        child = child.parent
    return (child.arg_key if child.parent is sel else None), chain


def scope_label(sc: Scope) -> str:
    if sc.is_cte:
        return f"cte:{sc.expression.parent.alias}" if isinstance(sc.expression.parent, exp.CTE) else "cte"
    if sc.is_root:
        return "main"
    if isinstance(sc.expression, exp.SetOperation):
        return "union"
    return "unnest" if isinstance(sc.expression, exp.Unnest) else "subquery"


def find_source(sc: Scope, name: str):
    s = sc
    while s is not None:
        if name in s.sources:
            return s.sources[name], s
        s = s.parent
    return None, None


# ------------------------------------------------------------------------------ tracing

def projection(sel: exp.Expression, name: str):
    if isinstance(sel, exp.Select):
        lname = name.lower()
        for p in sel.expressions:
            if p.alias_or_name.lower() == lname:
                return p
    return None


def trace_expr(ctx: Ctx, sc: Scope, e: exp.Expression) -> list[Origin]:
    """Base-column origins of an expression evaluated in scope `sc`."""
    body = e.this if isinstance(e, exp.Alias) else e
    cols = [c for c in body.find_all(exp.Column) if not isinstance(c.this, exp.Star)]
    # columns inside nested subqueries belong to other scopes
    cols = [c for c in cols if not any(isinstance(a, (exp.Subquery, exp.Select)) and a is not body
                                       for a in _ancestors_until(c, body))]
    if isinstance(body, exp.Column):
        kind, fns = "passthrough", ()
    else:
        agg = [a for a in body.find_all(exp.AggFunc)]
        kind = "aggregate" if agg or isinstance(body, exp.AggFunc) else "transform"
        fns = tuple(dict.fromkeys([fn_name(n) for n in body.walk()
                                   if isinstance(n, (exp.Func, exp.Cast)) and not isinstance(n, exp.Column)]
                                  + arith_tags(body)))
    out = []
    for c in cols:
        ctl = is_control(c, body)
        for o in trace_column(ctx, sc, c):
            out.append(o.via(kind, fns, ctl))
    # subqueries in the expression, e.g. (SELECT value.int_value FROM UNNEST(event_params) ...)
    for sq in body.find_all(exp.Subquery):
        inner = ctx.scope_of.get(id(sq.this))
        if inner is not None and isinstance(sq.this, exp.Select) and sq.this.expressions:
            for o in trace_expr(ctx, inner, sq.this.expressions[0]):
                out.append(o.via("transform", ("SUBQUERY",)))
    return out


def arith_tags(e: exp.Expression) -> list[str]:
    """Scaling by a constant, e.g. '/100' for cents -> dollars. Units hide in these."""
    out = []
    for n in e.walk():
        if isinstance(n, (exp.Div, exp.Mul, exp.SafeDivide)):
            a, b = n.this, n.expression
            k = b if isinstance(b, exp.Literal) and not b.is_string else (
                a if isinstance(a, exp.Literal) and not a.is_string and isinstance(n, exp.Mul) else None)
            if k is not None:
                out.append(("*" if isinstance(n, exp.Mul) else "/") + k.this)
    return out


def is_control(c: exp.Expression, stop: exp.Expression) -> bool:
    """True when c only steers which value is produced: a CASE WHEN / IF condition, the
    ORDER BY of an aggregate (ARRAY_AGG(x ORDER BY t)), or a window's ORDER BY."""
    child = c
    for a in _ancestors_until(c, stop):
        if isinstance(a, exp.If) and child is a.this:
            return True
        # ARRAY_AGG(x ORDER BY t) is Order(this=x, expressions=[t]): only t steers
        if isinstance(a, (exp.Order, exp.Window)) and child is not a.this:
            return True
        child = a
    return False


def _ancestors_until(n: exp.Expression, stop: exp.Expression):
    """Ancestors of n strictly below `stop` (nothing when n is `stop`)."""
    if n is stop:
        return
    p = n.parent
    while p is not None and p is not stop:
        yield p
        p = p.parent


def trace_column(ctx: Ctx, sc: Scope, col: exp.Column) -> list[Origin]:
    key = (id(sc), col.table, col.name.lower(), field_path(col))
    if key in ctx.memo:
        return ctx.memo[key]
    ctx.memo[key] = []          # cycle guard
    src, owner = find_source(sc, col.table) if col.table else (None, None)
    if src is None and not col.table:
        src = unqualified_source(ctx, sc, col.name)
    out: list[Origin] = []
    if src is None:
        if col.name.lower() not in ("_table_suffix",):
            ctx.miss("column", f"{col.table + '.' if col.table else ''}{col.name}", blame(ctx, sc))
    elif isinstance(src, exp.Table):
        out = _base(ctx, src, col)
    elif isinstance(src, Scope):
        out = _derived(ctx, src, col)
    ctx.memo[key] = out
    return out


def has_column(ctx: Ctx, src, name: str) -> bool:
    if isinstance(src, exp.Table):
        return not is_system(src) and ctx.catalog.column(fqn(src), name) is not None
    if isinstance(src, Scope):
        e = src.expression
        if isinstance(e, exp.SetOperation):
            return any(has_column(ctx, b, name) for b in src.set_operation_scopes)
        return isinstance(e, exp.Select) and projection(e, name) is not None
    return False


def unqualified_source(ctx: Ctx, sc: Scope, name: str):
    """BigQuery's rule for an unqualified name: the one visible source that has it,
    innermost scope first. (qualify leaves some unqualified, e.g. in the copy of a
    correlated subquery it makes when expanding GROUP BY <alias>.)"""
    s = sc
    while s is not None:
        hits = [v for v in s.sources.values() if has_column(ctx, v, name)]
        if len(hits) == 1:
            return hits[0]
        if hits:
            return None
        s = s.parent
    return None


def blame(ctx: Ctx, sc: Scope) -> str:
    """Why a column found no source: usually its table is itself unresolved."""
    s = sc
    while s is not None:
        for v in s.sources.values():
            if isinstance(v, exp.Table):
                if is_system(v):
                    return "system table"
                if ctx.catalog.get(fqn(v)) is None:
                    return "table unresolved"
        s = s.parent
    return "no source"


def _base(ctx: Ctx, t: exp.Table, col: exp.Column) -> list[Origin]:
    name = fqn(t)
    if is_system(t):
        return []
    entry = ctx.catalog.get(name)
    if entry is None:
        # A per-run table (Fivetran staging) never has a catalog entry; keep its column
        # names as written. Any other unknown table is already listed as unresolved.
        return [Origin(name, col.name, "direct", (), field_path(col))] if "{" in t.name else []
    spelled = ctx.catalog.column(name, col.name)
    if spelled is None:
        ctx.miss("column", f"{name}.{col.name}", "not in table")
        return []
    return [Origin(name, spelled, "direct", (), field_path(col))]


def _derived(ctx: Ctx, src: Scope, col: exp.Column) -> list[Origin]:
    e = src.expression
    if isinstance(e, exp.Unnest):
        # UNNEST(arr) AS x: x.f is element field f of arr; fields of the element are a path
        out = []
        for arr in e.expressions:
            for o in trace_expr(ctx, src, arr):
                path = ".".join(p for p in (o.path, col.name if col.name.lower() != (e.alias or "").lower() else None,
                                            field_path(col)) if p) or None
                out.append(Origin(o.table, o.column, "unnest" if KIND_RANK[o.kind] < 3 else o.kind, o.fns, path))
        return out
    if isinstance(e, exp.SetOperation):
        # names come from the first branch; every branch contributes by position
        leaves = list(_leaf_branches(src))
        names = [p.alias_or_name.lower() for p in leaves[0].expression.expressions]
        if col.name.lower() not in names:
            ctx.miss("column", f"{scope_label(src)}.{col.name}", "not projected")
            return []
        i, out = names.index(col.name.lower()), []
        for b in leaves:
            out += positional(ctx, b, i)
        return out
    p = projection(e, col.name)
    if p is None:
        star = next((x for x in e.expressions if isinstance(x, exp.Star) or
                     (isinstance(x, exp.Column) and isinstance(x.this, exp.Star))), None) \
            if isinstance(e, exp.Select) else None
        if star is None:
            ctx.miss("column", f"{scope_label(src)}.{col.name}", "not projected")
        return []
    origins = trace_expr(ctx, src, p)
    if isinstance(p, exp.Alias) and isinstance(p.this, exp.Column) and p.this.name.lower() != p.alias.lower():
        origins = [o.via("rename") for o in origins]
    return origins


# ----------------------------------------------------------------------------- analysis

def add_read(ctx: Ctx, o: Origin, role: str, agg: str | None):
    r = ctx.reads.setdefault((o.table, o.column, o.path), {"roles": set(), "derived_roles": set(), "agg": set()})
    (r["roles"] if o.kind in ("direct", "passthrough", "rename", "unnest") else r["derived_roles"]).add(role)
    if agg:
        r["agg"].add(agg)


def side(ctx: Ctx, sc: Scope, e: exp.Expression):
    col, wraps = unwrap(e)
    if col is None:
        return None
    origins = trace_column(ctx, sc, col)
    values = [o for o in origins if not o.control]
    return [(o, wraps) for o in (values or origins)], col


def add_join(ctx: Ctx, sc: Scope, l_expr, r_expr, jtype: str, op: str = "="):
    L, R = side(ctx, sc, l_expr), side(ctx, sc, r_expr)
    if not L or not R:
        return False
    (lo, lcol), (ro, rcol) = L, R
    if lcol.table == rcol.table and lcol.table:
        return False            # same source on both sides: a filter, not a join
    for o1, w1 in lo:
        for o2, w2 in ro:
            a = {"table": o1.table, "column": o1.column, "path": o1.path,
                 "wrap": list(o1.fns[::-1]) + w1, "via": o1.kind}
            b = {"table": o2.table, "column": o2.column, "path": o2.path,
                 "wrap": list(o2.fns[::-1]) + w2, "via": o2.kind}
            if (b["table"], b["column"]) < (a["table"], a["column"]):
                a, b = b, a
            k = (a["table"], a["column"], a["path"], b["table"], b["column"], b["path"], jtype, op)
            ctx.joins.setdefault(k, {"left": a, "right": b, "type": jtype, "op": op,
                                     "scopes": set()})["scopes"].add(scope_label(sc))
    return True


def _add_filter(ctx: Ctx, sc: Scope, col_expr, const_exprs, op: str, clause: str):
    S = side(ctx, sc, col_expr)
    if not S:
        return
    origins, _ = S
    slots = [s for c in const_exprs for s in slots_in(c)]
    for o, wraps in origins:
        ctx.filters.append({"table": o.table, "column": o.column, "path": o.path, "op": op,
                            "wrap": list(o.fns[::-1]) + wraps, "slots": slots, "clause": clause,
                            "scope": scope_label(sc), "via": o.kind, "_scope": id(sc)})


def negated(n: exp.Expression) -> bool:
    p = n.parent
    while isinstance(p, exp.Paren):
        p = p.parent
    return isinstance(p, exp.Not)


def neg_op(op: str) -> str:
    return {"IS NULL": "IS NOT NULL", "=": "!=", "!=": "="}.get(op, "NOT " + op)


def predicates(ctx: Ctx, sc: Scope, clause_node: exp.Expression, clause: str, in_join: bool):
    """Classify comparisons in a WHERE / HAVING / QUALIFY / ON clause."""
    for n in clause_node.walk(bfs=False, prune=lambda x: isinstance(x, (exp.Subquery, exp.Select))
                              and x is not clause_node):
        if isinstance(n, exp.Subquery):
            continue
        neg = negated(n)

        def add_filter(ctx_, sc_, col_expr, consts, op, clause_):
            _add_filter(ctx_, sc_, col_expr, consts, neg_op(op) if neg else op, clause_)
        if isinstance(n, exp.In):
            q = n.args.get("query")
            if q is not None:
                inner = ctx.scope_of.get(id(q.this if isinstance(q, exp.Subquery) else q))
                sel = q.this if isinstance(q, exp.Subquery) else q
                if inner is not None and isinstance(sel, exp.Select) and len(sel.expressions) == 1:
                    L = side(ctx, sc, n.this)
                    R = [o for o in trace_expr(ctx, inner, sel.expressions[0])]
                    if L and R:
                        for o1, w1 in L[0]:
                            for o2 in R:
                                _pair(ctx, sc, o1, w1, o2, [], "IN")
            elif n.expressions and all(is_constant(x) for x in n.expressions):
                add_filter(ctx, sc, n.this, n.expressions, "IN", clause)
        elif isinstance(n, exp.Between):
            if is_constant(n.args["low"]) and is_constant(n.args["high"]):
                add_filter(ctx, sc, n.this, [n.args["low"], n.args["high"]], "BETWEEN", clause)
        elif isinstance(n, exp.Is):
            add_filter(ctx, sc, n.this, [], "IS NULL" if isinstance(n.expression, exp.Null) else "IS", clause)
        elif isinstance(n, COMPARISONS):
            l, r = n.this, n.expression
            op = {exp.EQ: "=", exp.NEQ: "!=", exp.GT: ">", exp.GTE: ">=", exp.LT: "<", exp.LTE: "<=",
                  exp.Like: "LIKE", exp.ILike: "ILIKE"}[type(n)]
            if is_constant(r):
                add_filter(ctx, sc, l, [r], op, clause)
            elif is_constant(l):
                add_filter(ctx, sc, r, [l], {">": "<", "<": ">", ">=": "<=", "<=": ">="}.get(op, op), clause)
            elif isinstance(n, exp.EQ):
                add_join(ctx, sc, l, r, "ON" if in_join else "WHERE")


def _pair(ctx, sc, o1, w1, o2, w2, jtype):
    a = {"table": o1.table, "column": o1.column, "path": o1.path, "wrap": list(o1.fns[::-1]) + w1, "via": o1.kind}
    b = {"table": o2.table, "column": o2.column, "path": o2.path, "wrap": list(o2.fns[::-1]) + w2, "via": o2.kind}
    if (b["table"], b["column"]) < (a["table"], a["column"]):
        a, b = b, a
    k = (a["table"], a["column"], a["path"], b["table"], b["column"], b["path"], jtype, "=")
    ctx.joins.setdefault(k, {"left": a, "right": b, "type": jtype, "op": "=", "scopes": set()})["scopes"].add(
        scope_label(sc))


def analyze_scope(ctx: Ctx, sc: Scope):
    sel = sc.expression
    if not isinstance(sel, exp.Select):
        return
    # tables
    for name, src in sc.sources.items():
        if isinstance(src, exp.Table):
            f = fqn(src)
            entry = None if is_system(src) else ctx.catalog.get(f)
            kind = "system" if is_system(src) else (entry["kind"].lower() if entry else "unknown")
            ctx.tables.setdefault(f, kind)
    # column reads, by clause
    for col in sc.columns:
        if isinstance(col.this, exp.Star):
            continue
        clause, chain = clause_of(col, sel)
        role = CLAUSE_ROLE.get(clause or "", clause or "other")
        if role == "join":
            join = next((a for a in chain if isinstance(a, exp.Join)), None)
            if join is not None and col not in (join.args.get("on") or exp.Null()).find_all(exp.Column):
                role = "from"
        if any(isinstance(a, exp.Window) for a in chain):
            role = "window"
        if any(isinstance(a, exp.Unnest) for a in chain):
            role = "unnest"
        agg = next((fn_name(a) for a in chain if isinstance(a, exp.AggFunc)), None)
        for o in trace_column(ctx, sc, col):
            add_read(ctx, o, role, agg)
    # columns compared with each other: CORR(a.x, b.y), a.x - b.y, a.x > b.y
    for n in sel.walk(prune=lambda x: isinstance(x, (exp.Subquery, exp.Select)) and x is not sel):
        if isinstance(n, COMPARED) or (isinstance(n, (exp.GT, exp.GTE, exp.LT, exp.LTE, exp.NEQ))
                                       and not is_constant(n.this) and not is_constant(n.expression)):
            L, R = side(ctx, sc, n.this), side(ctx, sc, n.expression)
            if not L or not R or (L[1].table == R[1].table and L[1].name == R[1].name):
                continue
            for o1, _ in L[0]:
                for o2, _ in R[0]:
                    if (o1.table, o1.column) != (o2.table, o2.column):
                        a, b = sorted([(o1.table, o1.column), (o2.table, o2.column)])
                        ctx.comparisons.setdefault((a, b), set()).add(type(n).__name__.upper())
    # GROUP BY ALL groups by every projection that is not an aggregate
    g = sel.args.get("group")
    if g is not None and g.args.get("all"):
        for p in sel.expressions:
            if p.find(exp.AggFunc) is None:
                for o in trace_expr(ctx, sc, p):
                    if o.kind in ("direct", "passthrough", "rename", "unnest", "transform"):
                        add_read(ctx, Origin(o.table, o.column, "direct", (), o.path), "group", None)
    # joins and filters
    for j in sel.args.get("joins") or []:
        on = j.args.get("on")
        if on is not None:
            jt = " ".join(p for p in (j.side, j.kind) if p).upper() or "INNER"
            before = len(ctx.joins)
            predicates(ctx, sc, on, "on", True)
            # retag ON equalities with the join type
            for k in list(ctx.joins)[before:]:
                if ctx.joins[k]["type"] == "ON":
                    v = ctx.joins.pop(k)
                    v["type"] = jt
                    nk = k[:6] + (jt, k[7])
                    ctx.joins.setdefault(nk, {**v, "scopes": set()})["scopes"] |= v["scopes"]
    for clause in ("where", "having", "qualify"):
        node = sel.args.get(clause)
        if node is not None:
            predicates(ctx, sc, node, clause, False)
    # partition / shard pruning for each base table read in this scope
    for name, src in sc.sources.items():
        if not isinstance(src, exp.Table) or is_system(src):
            continue
        f = fqn(src)
        entry = ctx.catalog.get(f)
        if not entry:
            continue
        pcol = "_TABLE_SUFFIX" if entry["kind"] == "WILDCARD" else entry.get("partition")
        if entry["kind"] == "VIEW":
            ctx.scan["partition_filter"].setdefault(f, "view")
            continue
        if not pcol:
            continue
        pushed = any(fl["_scope"] == id(sc) and fl["table"] == f and fl["column"].lower() == pcol.lower()
                     and fl["clause"] == "where" for fl in ctx.filters)
        if pcol == "_TABLE_SUFFIX":
            pushed = pushed or any(fl["_scope"] == id(sc) and fl["column"].lower() == "_table_suffix"
                                   for fl in ctx.filters)
        prev = ctx.scan["partition_filter"].get(f)
        state = "pushed" if pushed else "none"
        if prev != "pushed":
            ctx.scan["partition_filter"][f] = state


# ------------------------------------------------------------------------------- writes

def target_of(t: exp.Expression):
    tgt = t.this
    cols = None
    if isinstance(tgt, exp.Schema):
        cols = [c.name for c in tgt.expressions]
        tgt = tgt.this
    return (tgt if isinstance(tgt, exp.Table) else None), cols


def outputs(ctx: Ctx, root_sc: Scope) -> list[tuple[str, list[Origin]]]:
    e = root_sc.expression
    if isinstance(e, exp.SetOperation):
        branches = root_sc.set_operation_scopes
        first = branches[0]
        while isinstance(first.expression, exp.SetOperation):
            first = first.set_operation_scopes[0]
        names = [p.alias_or_name for p in first.expression.expressions]
        return [(n, positional(ctx, root_sc, i), first.expression.expressions[i]) for i, n in enumerate(names)]
    if isinstance(e, exp.Select):
        return [(p.alias_or_name, _renamed(p, trace_expr(ctx, root_sc, p)), p) for p in e.expressions]
    return []


def is_star(p) -> bool:
    return isinstance(p, exp.Star) or (isinstance(p, exp.Column) and isinstance(p.this, exp.Star))


def positional(ctx: Ctx, sc: Scope, i: int) -> list[Origin]:
    """Origins of the i-th output column of a set-operation branch. A branch left as
    `SELECT * FROM x` (qualify does not expand it when x's output names collide, e.g.
    two unaliased CAST(NULL ...)) takes the i-th output of x - BigQuery unions by position."""
    e = sc.expression
    if isinstance(e, exp.SetOperation):
        leaves = list(_leaf_branches(sc))
        return positional(ctx, leaves[0], i) + [o for b in leaves[1:] for o in positional(ctx, b, i)]
    ps = e.expressions if isinstance(e, exp.Select) else []
    if len(ps) == 1 and is_star(ps[0]):
        srcs = [src for _, src in sc.selected_sources.values()]   # its own FROM, not every CTE in scope
        if len(srcs) == 1:
            src = srcs[0]
            if isinstance(src, Scope):
                return positional(ctx, src, i)
            if isinstance(src, exp.Table):
                names = list((ctx.catalog.get(fqn(src)) or {}).get("columns", {}))
                return _base(ctx, src, exp.column(names[i])) if i < len(names) else []
        return []
    return _renamed(ps[i], trace_expr(ctx, sc, ps[i])) if i < len(ps) else []


def _renamed(p, origins):
    if isinstance(p, exp.Alias) and isinstance(p.this, exp.Column) and p.this.name.lower() != p.alias.lower():
        return [o.via("rename") for o in origins]
    return origins


def _leaf_branches(sc: Scope):
    if isinstance(sc.expression, exp.SetOperation):
        for b in sc.set_operation_scopes:
            yield from _leaf_branches(b)
    else:
        yield sc


def lineage_entry(ctx: Ctx, target: str, name: str, origins: list[Origin], expr=None) -> dict:
    spelled = ctx.catalog.column(target, name) or name
    if origins:
        kind = max((o.kind for o in origins), key=KIND_RANK.get)
        fns = list(dict.fromkeys(f for o in origins for f in o.fns))
    else:   # COUNT(*) has no source column but is not a constant
        aggs = [fn_name(a) for a in expr.find_all(exp.AggFunc)] if expr is not None else []
        kind, fns = ("aggregate", aggs) if aggs else ("constant", [])
    return {"target": spelled,
            "from": [{"table": o.table, "column": o.column, "path": o.path, **({"control": True} if o.control else {})}
                     for o in origins],
            "kind": kind, "fn": fns}


def writes_of(ctx: Ctx, t: exp.Expression, root_scopes: dict) -> list[dict]:
    st = statement_type(t)
    if st in ("CREATE_TABLE_AS_SELECT", "CREATE_VIEW", "INSERT"):
        tgt, cols = target_of(t)
        if tgt is None:
            return []
        target = fqn(tgt)
        body = t.expression
        while isinstance(body, (exp.Subquery, exp.Paren)) and not body.alias:
            body = body.this        # CREATE TABLE ... AS ( SELECT ... )
        sc = root_scopes.get(id(body))
        outs = outputs(ctx, sc) if sc else []
        if st == "INSERT":
            cols = cols or list((ctx.catalog.get(target) or {}).get("columns", {}))
            outs = [(cols[i] if i < len(cols) else n, o, e) for i, (n, o, e) in enumerate(outs)]
        mode = {"CREATE_VIEW": "VIEW", "CREATE_TABLE_AS_SELECT": "CTAS"}.get(st, "INSERT")
        return [{"table": target, "mode": mode,
                 "columns": [lineage_entry(ctx, target, n, o, e) for n, o, e in outs]}]
    if st == "MERGE":
        tgt = t.this
        target = fqn(tgt)
        using = t.args.get("using")
        src_alias = using.alias_or_name
        tgt_alias = tgt.alias_or_name
        src_sc = root_scopes.get(id(using.this)) if isinstance(using, exp.Subquery) else None

        def origin_of(v: exp.Expression, target_col: str | None = None) -> list[Origin]:
            out = []
            for c in v.find_all(exp.Column):
                if c.table and c.table.lower() == tgt_alias.lower():
                    continue
                if src_sc is not None:
                    p = projection(src_sc.expression, c.name) if isinstance(src_sc.expression, exp.Select) else None
                    if p is not None:
                        out += _renamed(p, trace_expr(ctx, src_sc, p))
                    else:
                        out += _derived(ctx, src_sc, c)
                elif isinstance(using, exp.Table):
                    out += _base(ctx, using, exp.column(c.name, fqn(using)))
            if isinstance(v, exp.Column):
                same = target_col is None or v.name.lower() == target_col.lower()
                return [o.via("passthrough" if same else "rename") for o in out]
            return [o.via("transform", (fn_name(v),)) for o in out]

        cols: dict[str, list[Origin]] = {}
        for when in (t.args.get("whens").expressions if t.args.get("whens") else []):
            then = when.args.get("then")
            if isinstance(then, exp.Insert) and isinstance(then.this, exp.Var) and then.this.name.upper() == "ROW":
                # INSERT ROW (dbt insert_overwrite): every source column, by name
                names = []
                if src_sc is not None and isinstance(src_sc.expression, exp.Select):
                    names = [p.alias_or_name for p in src_sc.expression.expressions]
                elif isinstance(using, exp.Table):
                    names = list((ctx.catalog.get(fqn(using)) or {}).get("columns", {}))
                for n in names:
                    cols.setdefault(n, []).extend(origin_of(exp.column(n, src_alias), n))
            elif isinstance(then, exp.Update):
                for eq in then.expressions:
                    cols.setdefault(eq.this.name, []).extend(origin_of(eq.expression, eq.this.name))
            elif isinstance(then, exp.Insert):
                names = [c.name for c in then.this.expressions] if isinstance(then.this, exp.Tuple) else []
                vals = then.expression.expressions if isinstance(then.expression, exp.Tuple) else []
                if not names and vals:      # INSERT VALUES (...) with no column list: target order
                    names = list((ctx.catalog.get(target) or {}).get("columns", {}))
                for n, v in zip(names, vals):
                    cols.setdefault(n, []).extend(origin_of(v, n))
        keys = []
        on = t.args.get("on")
        for eq in (on.find_all(exp.EQ) if on is not None else []):
            a, b = eq.this, eq.expression
            if isinstance(a, exp.Column) and isinstance(b, exp.Column):
                tc, sc_ = (a, b) if a.table.lower() == tgt_alias.lower() else (b, a)
                keys.append({"target": ctx.catalog.column(target, tc.name) or tc.name,
                             "from": [{"table": o.table, "column": o.column} for o in origin_of(sc_)]})
        entries = [lineage_entry(ctx, target, n, list(dict.fromkeys(o))) for n, o in cols.items()]
        return [{"table": target, "mode": "MERGE", "columns": entries, "merge_keys": keys}]
    if st in ("DELETE", "UPDATE"):
        tgt = t.this if isinstance(t.this, exp.Table) else None
        return [{"table": fqn(tgt), "mode": st, "columns": []}] if tgt is not None else []
    return []


def dml_filters(ctx: Ctx, t: exp.Expression):
    """DELETE/UPDATE have no Select scope: their WHERE columns belong to the target."""
    tgt = t.this if isinstance(t.this, exp.Table) else None
    where = t.args.get("where")
    if tgt is None or where is None:
        return
    target = fqn(tgt)
    ctx.tables.setdefault(target, (ctx.catalog.get(target) or {}).get("kind", "unknown").lower())
    for n in where.walk():
        if isinstance(n, COMPARISONS + (exp.Between, exp.In)):
            col = n.this if isinstance(n.this, exp.Column) else None
            if col is None:
                continue
            spelled = ctx.catalog.column(target, col.name)
            if spelled is None:
                ctx.miss("column", f"{target}.{col.name}", "not in table")
                continue
            consts = [x for k, x in n.args.items() if k != "this" and isinstance(x, exp.Expression)]
            consts += n.expressions if isinstance(n, exp.In) else []
            ctx.filters.append({"table": target, "column": spelled, "path": None, "op": n.key.upper(),
                                "wrap": [], "slots": [s for c in consts for s in slots_in(c)],
                                "clause": "where", "scope": "main", "via": "direct", "_scope": 0})
            add_read(ctx, Origin(target, spelled), "filter", None)


def dedupe_filters(fs: list[dict]) -> list[dict]:
    """qualify can copy a subquery (GROUP BY <alias>), repeating its predicates."""
    out, seen = [], set()
    for f in fs:
        k = (f["table"], f["column"], f["path"], f["op"], tuple(f["slots"]), f["clause"], f["scope"])
        if k not in seen:
            seen.add(k)
            out.append({k2: v for k2, v in f.items() if k2 != "_scope"})
    return out


def family_id(tree: exp.Expression) -> str:
    """Structure with every identifier and literal blanked: one monitor query stamped
    across 70 tables, or one dbt test type across all models, is one family."""
    import hashlib
    t = tree.copy()
    for n in t.walk():
        n.comments = None
        if isinstance(n, exp.Identifier):
            n.set("this", "_")
            n.set("quoted", False)
    for s_ in literal_slots(t):
        s_.replace(exp.Placeholder())
    return hashlib.sha256(t.sql(dialect="bigquery").encode()).hexdigest()[:16]


def output_summary(t: exp.Expression, scope_of: dict) -> dict | None:
    """Shape of what a query returns: a single row of aggregates is how health checks look."""
    body = t
    while isinstance(body, exp.Subquery):
        body = body.this
    while isinstance(body, exp.SetOperation):
        body = body.this
    if not isinstance(body, exp.Select):
        return None
    ps = body.expressions
    agg_only = bool(ps) and all(p.find(exp.AggFunc) is not None or is_constant(p) for p in ps)
    frm = body.args.get("from_") or body.args.get("from")
    root = frm.this if frm is not None else None
    return {"columns": len(ps), "aggregate_only": agg_only, "grouped": body.args.get("group") is not None,
            "root_from": fqn(root) if isinstance(root, exp.Table) else None}


# --------------------------------------------------------------------------------- main

def resolve(sql: str, catalog: Catalog, default_project: str | None = None,
            shape_id: str | None = None) -> dict:
    rec = {"shape_id": shape_id, "parser": PARSER_ID, "catalog": catalog.version, "dialect": "bigquery"}
    try:
        trees = [t for t in sqlglot.parse(sql, read="bigquery") if t is not None]
    except Exception as e:
        return {**rec, "status": "error", "error": f"parse: {type(e).__name__}: {str(e)[:300]}"}
    if not trees:
        return {**rec, "status": "error", "error": "empty"}

    ctx = Ctx(catalog)
    writes, errors, offset = [], [], 0
    rec["family_id"] = family_id(trees[0])
    for t in trees:
        slots = literal_slots(t)
        for i, s in enumerate(slots):
            s.meta["slot"] = offset + i
        offset += len(slots)
        body = t.expression if isinstance(t, (exp.Create, exp.Insert)) else t
        if isinstance(body, exp.Select) or isinstance(t, exp.Select):
            sel0 = body if isinstance(body, exp.Select) else t
            ctx.scan["select_star"] |= any(isinstance(x, exp.Star) or
                                           (isinstance(x, exp.Column) and isinstance(x.this, exp.Star))
                                           for x in sel0.expressions)
            lim = sel0.args.get("limit")
            if lim is not None and isinstance(lim.expression, exp.Literal):
                ctx.scan["limit"] = int(lim.expression.this)
        catalog.canonicalize_tables(t, default_project)
        for tb in t.find_all(exp.Table):
            if tb.args.get("db") and not is_system(tb) and catalog.get(fqn(tb)) is None:
                # a canonicalized per-run name (staging table, PDT generation) is not
                # expected in a catalog snapshot
                ctx.miss("table", fqn(tb), "transient" if "{" in tb.name else "not in catalog")
                ctx.tables.setdefault(fqn(tb), "transient" if "{" in tb.name else "unknown")
            if is_system(tb):
                ctx.tables.setdefault(fqn(tb), "system")
        try:
            t = qualify(t, schema=catalog.schema, dialect="bigquery", catalog=default_project,
                        validate_qualify_columns=False, quote_identifiers=False)
        except Exception as e:
            errors.append(f"qualify: {type(e).__name__}: {str(e)[:200]}")
            for tb in t.find_all(exp.Table):
                if tb.args.get("db"):
                    entry = catalog.get(fqn(tb))
                    ctx.tables.setdefault(fqn(tb), entry["kind"].lower() if entry else "unknown")
            rec.setdefault("statement_type", statement_type(t))
            continue
        try:
            scopes = traverse_scope(t)
        except Exception as e:
            errors.append(f"scope: {type(e).__name__}: {str(e)[:200]}")
            continue
        ctx.scope_of = {id(s.expression): s for s in scopes}
        if statement_type(t) == "SELECT":
            rec.setdefault("output", output_summary(t, ctx.scope_of))
        for sc in scopes:
            analyze_scope(ctx, sc)
        if isinstance(t, (exp.Delete, exp.Update)):
            dml_filters(ctx, t)
        try:
            writes += writes_of(ctx, t, ctx.scope_of)
        except Exception as e:
            errors.append(f"writes: {type(e).__name__}: {str(e)[:200]}")
        rec.setdefault("statement_type", statement_type(t))

    for w in writes:
        ctx.tables.setdefault(w["table"], (catalog.get(w["table"]) or {}).get("kind", "unknown").lower())
    real_misses = [1 for (k, n), r in ctx.unresolved.items() if r not in EXPECTED_MISSES]
    status = "error" if errors and not ctx.reads and not writes else (
        "partial" if errors or real_misses else "ok")
    rec.update({
        "status": status,
        "statements": len(trees),
        "tables": [{"id": k, "kind": v} for k, v in sorted(ctx.tables.items())],
        "reads": [{"table": t, "column": c, "path": p, "roles": sorted(v["roles"]),
                   "derived_roles": sorted(v["derived_roles"] - v["roles"]), "agg": sorted(v["agg"])}
                  for (t, c, p), v in sorted(ctx.reads.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or ""))],
        "joins": [{**v, "scopes": sorted(v["scopes"])} for v in ctx.joins.values()],
        "filters": dedupe_filters(ctx.filters),
        "comparisons": [{"left": {"table": a[0], "column": a[1]}, "right": {"table": b[0], "column": b[1]},
                         "ops": sorted(ops)} for (a, b), ops in sorted(ctx.comparisons.items())],
        "writes": writes,
        "scan": ctx.scan,
        "unresolved": [{"kind": k, "name": n, "reason": r} for (k, n), r in sorted(ctx.unresolved.items())],
    })
    if errors:
        rec["errors"] = errors
    return rec

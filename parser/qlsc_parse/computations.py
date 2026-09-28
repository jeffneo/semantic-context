"""What a query computes: its measures, the dimensions it derives, and the populations it filters to.

For every SELECT scope whose sources are physical tables, three kinds, each written over base columns
(`table.column`) so the same computation in two queries is the same text:
  measure     an output expression with an aggregate: SUM(fct_card_transactions.amount), with the
              scope's filters that are not a period (they come with the measure: is_purchase)
  dimension   an output expression the scope groups by that derives something: CASE, IF, date
              truncation, arithmetic (a column passed through is not a computation)
  population  the conjunction of the scope's non-period filters: segment IN ('affluent', 'private')
              AND email_opt_in
A period filter is a comparison with a date or timestamp literal, or with the current date: it is the
question's time window, not the definition. Literals are kept (a code value is part of a definition).

Expressions over a CTE's or subquery's columns are left out: their definition lives in the inner scope,
where it is found in its own right.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope

from .catalog import Catalog, fqn, is_system

DERIVING = (exp.Case, exp.If, exp.DateTrunc, exp.TimestampTrunc, exp.Extract, exp.Binary, exp.Func)
DATE_LITERAL = re.compile(r"^\d{4}-\d{2}-\d{2}")
TODAY = (exp.CurrentDate, exp.CurrentTimestamp, exp.CurrentDatetime)


def _bases(scope, catalog: Catalog) -> dict[str, str]:
    """alias -> physical table (canonical name) for the scope's sources that are catalog tables (not a
    per-run table such as a Looker PDT's generation, nor a system view)."""
    return {
        alias: fqn(src)
        for alias, (node, src) in scope.selected_sources.items()
        if isinstance(src, exp.Table) and not is_system(src) and catalog.get(fqn(src)) is not None
    }


def _tidy(e: exp.Expression) -> exp.Expression:
    """One spelling per computation: no parentheses around a lone column, function names upper case."""

    def fix(n):
        if isinstance(n, exp.Paren) and isinstance(n.this, exp.Column):
            return n.this
        if isinstance(n, exp.Anonymous):
            n.set("this", str(n.this).upper())
        return n

    return e.transform(fix)


def _over_bases(e: exp.Expression, bases: dict[str, str], catalog: Catalog) -> tuple[str, list[str]] | None:
    """The expression written over base columns, and those columns; None if any column isn't one."""
    e = exp.Paren(this=e.copy())  # a holder, so a bare column can be replaced too
    cols = []
    for c in list(e.find_all(exp.Column)):
        t = bases.get(c.table)
        if not t or isinstance(c.this, exp.Star):
            return None
        name = catalog.column(t, c.name) or c.name  # the catalog's spelling (the parser lowercases)
        cols.append(f"{t}.{name}")
        c.replace(exp.column(name, table=t.rsplit(".", 1)[-1]))
    if not cols and not e.find(exp.Count):
        return None
    return _tidy(e.this).sql(dialect="bigquery"), sorted(set(cols))


def _is_period(p: exp.Expression) -> bool:
    if p.find(*TODAY):
        return True
    return any(DATE_LITERAL.match(str(lit.this)) for lit in p.find_all(exp.Literal) if lit.is_string)


def _conjuncts(where: exp.Expression | None) -> list[exp.Expression]:
    if where is None:
        return []
    node = where.this
    out, stack = [], [node]
    while stack:
        n = stack.pop()
        if isinstance(n, exp.And):
            stack += [n.right, n.left]
        elif isinstance(n, exp.Paren) and isinstance(n.this, exp.And):
            stack.append(n.this)
        else:
            out.append(n)
    return out


def computations(sql: str, catalog: Catalog, default_project: str | None = None) -> list[dict]:
    """-> [{kind, expression, columns, tables, filters, filter_columns, grain}] for every scope of every
    statement. `filter_columns` lists each filter's columns, so a caller can drop a filter it knows
    to be a parameter (its value varies from run to run)."""
    try:
        trees = [t for t in sqlglot.parse(sql, read="bigquery") if t is not None]
    except Exception:
        return []
    out = []
    for t in trees:
        catalog.canonicalize_tables(t, default_project)
        try:
            t = qualify(
                t,
                schema=catalog.schema,
                dialect="bigquery",
                catalog=default_project,
                validate_qualify_columns=False,
                quote_identifiers=False,
            )
            scopes = traverse_scope(t)
        except Exception:
            continue
        for sc in scopes:
            sel = sc.expression
            if not isinstance(sel, exp.Select):
                continue
            bases = _bases(sc, catalog)
            if not bases:
                continue
            filters = {}
            for p in _conjuncts(sel.args.get("where")):
                w = _over_bases(p, bases, catalog)
                if w and not _is_period(p):
                    filters.setdefault(w[0], w)
            filters = [filters[k] for k in sorted(filters)]
            group = sel.args.get("group")
            grouped = {g.sql(dialect="bigquery") for g in (group.expressions if group else [])}
            grain = sorted(
                {w[0] for g in (group.expressions if group else []) if (w := _over_bases(g, bases, catalog))}
            )
            for proj in sel.expressions:
                e = proj.this if isinstance(proj, exp.Alias) else proj
                w = _over_bases(e, bases, catalog)
                if not w:
                    continue
                name = proj.alias_or_name
                if e.find(exp.AggFunc):
                    kind = "measure"
                elif isinstance(e, DERIVING) and (e.sql(dialect="bigquery") in grouped or name in grouped):
                    kind = "dimension"
                else:
                    kind = None
                if kind:
                    out.append(
                        {
                            "kind": kind,
                            "expression": w[0],
                            "alias": name,
                            "columns": w[1],
                            "tables": sorted(set(bases.values()) & {c.rsplit(".", 1)[0] for c in w[1]})
                            or sorted(set(bases.values())),
                            "filters": [f[0] for f in filters] if kind == "measure" else [],
                            "filter_columns": [f[1] for f in filters] if kind == "measure" else [],
                            "grain": grain if kind == "measure" else [],
                        }
                    )
            if filters:
                out.append(
                    {
                        "kind": "population",
                        "expression": " AND ".join(f[0] for f in filters),
                        "alias": None,
                        "columns": sorted({c for f in filters for c in f[1]}),
                        "tables": sorted({c.rsplit(".", 1)[0] for f in filters for c in f[1]}),
                        "filters": [f[0] for f in filters],  # a population is its filters
                        "filter_columns": [f[1] for f in filters],
                        "grain": [],
                    }
                )
    return out

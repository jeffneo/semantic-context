"""T1: fingerprint one query text into a shape id, its literal values and annotations.

A shape is the query with comments dropped, every literal replaced by a slot, and
volatile table names canonicalized - so the Looker query run by 166 users, or the
Fivetran MERGE from a fresh staging table every sync, is one shape. This mirrors
BigQuery's own `normalized_literals` hash (probed: literals, whole array literals,
comments, whitespace and keyword case are ignored; IN-list length is kept) and adds
the canonical table names on top.

Literal values come back in slot order. Slot order is the pre-order walk of the
parsed tree, so every text of one shape numbers its literals identically, and T2's
filter records ("wrapup_code_name IN slots 4,5") can be joined back to the values.
"""
from __future__ import annotations

import hashlib
import json
import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers

from .catalog import Catalog

JSON_IN_COMMENT = re.compile(r"\{.*\}", re.S)


def is_literal(n: exp.Expression) -> bool:
    return isinstance(n, exp.Literal) or (isinstance(n, exp.Neg) and isinstance(n.this, exp.Literal))


def literal_slots(tree: exp.Expression) -> list[exp.Expression]:
    """Literal slots in pre-order. An array of only literals is one slot, as in BigQuery."""
    out, skip = [], set()
    for n in tree.walk(bfs=False):
        if id(n) in skip:
            continue
        if isinstance(n, exp.Array) and n.expressions and all(is_literal(e) for e in n.expressions):
            out.append(n)
            skip.update(id(x) for e in n.expressions for x in e.walk())
        elif is_literal(n):
            out.append(n)
            skip.update(id(x) for x in n.walk())
    return out


def literal_value(n: exp.Expression):
    if isinstance(n, exp.Array):
        return [literal_value(e) for e in n.expressions]
    if isinstance(n, exp.Neg):
        return "-" + n.this.this
    return n.this


def annotations(tree: exp.Expression) -> list[dict]:
    """JSON objects found in comments: Looker query context, dbt node metadata, ..."""
    out = []
    for n in tree.walk():
        for c in n.comments or ():
            m = JSON_IN_COMMENT.search(c)
            if not m:
                continue
            try:
                obj = json.loads(m.group(0))
            except ValueError:
                continue
            if isinstance(obj, dict):
                head = c[:m.start()].strip().strip("'\"").strip()
                out.append({"source": head or None, **obj})
    return out


def shape_sql(trees: list[exp.Expression], catalog: Catalog | None, default_project: str | None) -> str:
    parts = []
    for t in trees:
        for s in literal_slots(t):
            s.replace(exp.Placeholder())
        for n in t.walk():
            n.comments = None
        if catalog is not None:
            catalog.canonicalize_tables(t, default_project)
        # BigQuery column names are case-insensitive; table names are not
        t = normalize_identifiers(t, dialect="bigquery")
        parts.append(t.sql(dialect="bigquery"))
    return ";\n".join(parts)


def fingerprint(sql: str, catalog: Catalog | None = None, default_project: str | None = None) -> dict:
    try:
        trees = [t for t in sqlglot.parse(sql, read="bigquery") if t is not None]
    except Exception as e:  # sqlglot raises several error types
        return {"shape_id": None, "error": f"{type(e).__name__}: {str(e)[:300]}"}
    if not trees:
        return {"shape_id": None, "error": "empty"}
    lits = [literal_value(s) for t in trees for s in literal_slots(t)]
    notes = [a for t in trees for a in annotations(t)]
    canon = shape_sql(trees, catalog, default_project)
    return {"shape_id": hashlib.sha256(canon.encode()).hexdigest(), "literals": lits,
            "annotations": notes, "statements": len(trees)}

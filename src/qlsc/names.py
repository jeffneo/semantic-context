"""Names every stage shares: canonical table ids, short display names, text ids."""

from __future__ import annotations

import hashlib

from qlsc_parse.catalog import Catalog


def short(fqn: str | None) -> str:
    """An id without its project, for display: bank-dw.dw_core.dim_account -> dw_core.dim_account."""
    if not fqn:
        return "?"
    return fqn.split(".", 1)[1] if fqn.count(".") >= 2 else fqn


def text_id(sql: str) -> str:
    """The id of one distinct query text."""
    return hashlib.sha1(sql.encode()).hexdigest()


def canonical_table(catalog: Catalog, fqn: str) -> str:
    """A table as the log or a designed model spells it -> its id in the graph, by the parser's own
    rules (physical -> logical dataset, volatile identifiers, date shards -> one wildcard table)."""
    return ".".join(catalog.canonical(*fqn.split(".", 2)))


def canonical_column(catalog: Catalog, fqn: str) -> str:
    table, _, column = fqn.rpartition(".")
    return f"{canonical_table(catalog, table)}.{column}"

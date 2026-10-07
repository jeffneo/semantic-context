"""The Cypher the demo page's generators run: one file each in ui/src/examples/fennmoor/queries/<section>/<name>.cypher.

A file starts with comment lines: the database it runs on, its parameters, and what it returns. They go to Neo4j with the query, which ignores them.
The page reads from the same folder when it shows a query, so the query on the page and the one that made its data are one file.
"""

from __future__ import annotations

from pathlib import Path

QUERIES = Path(__file__).resolve().parents[3] / "ui" / "src" / "examples" / "fennmoor" / "queries"


def query(section: str, name: str) -> str:
    return (QUERIES / section / f"{name}.cypher").read_text()

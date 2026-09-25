"""Shared Neo4j access for the pipeline stages (target: estate.yaml `neo4j`)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml
from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def env(path: Path = ROOT / ".env") -> dict:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def config() -> dict:
    return yaml.safe_load((HERE / "estate.yaml").read_text())


class Graph:
    def __init__(self, cfg: dict | None = None):
        n = (cfg or config())["neo4j"]
        self.driver = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]),
                                           notifications_min_severity="OFF")
        self.db = n["database"]
        self.counts = Counter()

    def run(self, q: str, **params):
        return self.driver.execute_query(q, database_=self.db, **params)

    def rows(self, q: str, **params) -> list[dict]:
        return [r.data() for r in self.run(q, **params).records]

    def auto(self, q: str, **params):
        """Auto-commit transaction (needed for CALL ... IN TRANSACTIONS and some GDS calls)."""
        with self.driver.session(database=self.db) as s:
            return [r.data() for r in s.run(q, **params)]

    def batch(self, label: str, q: str, rows: list[dict], size: int = 5000):
        for i in range(0, len(rows), size):
            self.run(q, rows=rows[i:i + size])
        self.counts[label] += len(rows)

    def close(self):
        self.driver.close()

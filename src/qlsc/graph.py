"""Neo4j access for every stage (the config's `neo4j`), and the GDS calls they share."""

from __future__ import annotations

from collections import Counter, defaultdict

from neo4j import GraphDatabase

from qlsc.config import Settings, secret


class Graph:
    def __init__(self, settings: Settings):
        n = settings["neo4j"]
        self.driver = GraphDatabase.driver(
            n["uri"], auth=(n["user"], secret("NEO4J_PASSWORD")), notifications_min_severity="OFF"
        )
        self.db = n["database"]
        self.counts = Counter()

    def __enter__(self) -> Graph:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.driver.close()

    # ------------------------------------------------------------------ Cypher

    def run(self, query: str, **params):
        return self.driver.execute_query(query, database_=self.db, **params)

    def rows(self, query: str, **params) -> list[dict]:
        return [r.data() for r in self.run(query, **params).records]

    def value(self, query: str, **params):
        """The first column of the first row."""
        records = self.run(query, **params).records
        return records[0][0] if records else None

    def auto(self, query: str, **params) -> list[dict]:
        """An auto-commit transaction (needed for CALL ... IN TRANSACTIONS)."""
        with self.driver.session(database=self.db) as s:
            return [r.data() for r in s.run(query, **params)]

    def batch(self, label: str, query: str, rows: list[dict], size: int = 5000) -> None:
        """Run `query` over `rows` (bound as $rows) in chunks; counts rows per label for the summary."""
        for i in range(0, len(rows), size):
            self.run(query, rows=rows[i : i + size])
        self.counts[label] += len(rows)

    def delete(self, match: str, size: int = 5000) -> None:
        """Delete what a pattern binds as `n`, e.g. "(n:Semantic) WHERE n.level > 1"."""
        self.auto(f"MATCH {match} CALL (n) {{ DETACH DELETE n }} IN TRANSACTIONS OF {size} ROWS")

    # ---------------------------------------------------------------------- GDS

    def drop_projection(self, name: str) -> None:
        self.run("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=name)

    def project_pairs(self, name: str, rows: list[dict]) -> dict:
        """An undirected projection from rows {a, b, w} of node ids (b and w may be None for a node
        with no edges). GDS numbers nodes in the order rows arrive and Leiden's result depends on that
        numbering, so rows are sorted: a seeded run repeats on a rebuilt database."""
        self.drop_projection(name)
        ids = sorted({r["a"] for r in rows} | {r["b"] for r in rows if r["b"]})
        eid = dict(
            self.run(
                """MATCH (n) WHERE (n:Variable OR n:Unjoined OR n:Semantic) AND n.id IN $ids
                   RETURN n.id, elementId(n)""",
                ids=ids,
            ).records
        )
        rows = [
            {"a": eid[r["a"]], "b": eid.get(r["b"]), "w": r["w"]}
            for r in sorted(rows, key=lambda r: (r["a"], r["b"] or ""))
        ]
        return self.rows(
            """UNWIND $rows AS r
               MATCH (a) WHERE elementId(a) = r.a
               OPTIONAL MATCH (b) WHERE elementId(b) = r.b
               WITH gds.graph.project($g, a, b,
                      {relationshipProperties: CASE WHEN b IS NULL THEN null ELSE {w: r.w} END},
                      {undirectedRelationshipTypes: ['*']}) AS g
               RETURN g.nodeCount AS nodes, g.relationshipCount AS rels""",
            g=name,
            rows=rows,
        )[0]

    def leiden(self, name: str, gamma: float, seed: int) -> dict[str, list[str]]:
        """Weighted Leiden (property `w`), seeded and single-threaded -> {smallest member id: member ids}."""
        comm = defaultdict(list)
        for r in self.rows(
            """CALL gds.leiden.stream($g, {gamma: $gamma, relationshipWeightProperty: 'w',
                                           randomSeed: $seed, concurrency: 1})
               YIELD nodeId, communityId
               RETURN gds.util.asNode(nodeId).id AS id, communityId AS k""",
            g=name,
            gamma=gamma,
            seed=seed,
        ):
            comm[r["k"]].append(r["id"])
        return {min(ms): sorted(ms) for ms in comm.values()}

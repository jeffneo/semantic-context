"""Semantic level 1: Leiden over what the business reads together.

Nodes are the units after qlsc/variables.py: a Variable (the columns it unifies count once) or an
:Unjoined column. Two units are related when
  - one query reads both (READS covers every role: select, filter, join, group, order), or
  - column lineage connects them (FLOWS, except control-only origins): the raw, staging and mart
    copies of the same data are one area.
The weight is the number of distinct statements that do either.

  1. GDS projection, undirected, weighted. Columns of transient ingestion tables (a loader's per-run
     merge sources) and lineage out of them are load plumbing, not use, and are left out. Every other
     unit is projected; one nothing reads with anything is an isolated node.
  2. Leiden, weighted, seeded and single-threaded (parameters.cluster: gamma above 1 gives more,
     smaller groups).
  3. Every community of 2 or more is a (:Semantic {id, level: 1, size, tables}) with
     (:Variable|Unjoined)-[:IN_SEMANTIC]->(:Semantic); the id is 'sem:' + the smallest member id.
     Isolated units get no Semantic: there is no evidence to group them.
  4. Stability: Leiden reruns, half with new seeds and half on a resample of the statements;
     Semantic.stability is how much of the group comes back (best Jaccard overlap, averaged; 1 =
     always whole). A low value means the evidence for the group is thin.
  5. The LLM names each group (prompts/semantic_system.md).
"""

from __future__ import annotations

import random
import time
from collections import Counter, defaultdict

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, name_all, prompt, write_names
from qlsc.names import short

PROJECTION = "semantic"
BATCH = 8
SHOW_MEMBERS = 40

Shapes = dict[str, list[str]]  # statement -> the units it reads
Flows = list[tuple[str, str, list[str]]]  # (unit, unit, the statements whose lineage links them)


def evidence_sets(G: Graph) -> tuple[Shapes, Flows]:
    """The usage evidence per statement: the units each query reads, and each lineage link with the
    statements that make it."""
    shapes = {
        r["s"]: r["units"]
        for r in G.rows("""MATCH (s:QueryShape)-[:READS]->(c:Column)
        OPTIONAL MATCH (c)-[:IS]->(v:Variable)
        WITH s, collect(DISTINCT coalesce(v.id, c.id)) AS units WHERE size(units) > 1
        RETURN s.id AS s, units""")
    }
    flows = [
        (r["a"], r["b"], r["shapes"])
        for r in G.rows("""
        MATCH (tx:Table)-[:HAS_COLUMN]->(x:Column)-[f:FLOWS]->(y:Column)
        WHERE NOT f.control AND tx.kind <> 'transient'
        OPTIONAL MATCH (x)-[:IS]->(vx:Variable)
        OPTIONAL MATCH (y)-[:IS]->(vy:Variable)
        RETURN coalesce(vx.id, x.id) AS a, coalesce(vy.id, y.id) AS b, f.shapes AS shapes""")
    ]
    return shapes, flows


def edges_from(shapes: Shapes, flows: Flows, keep: set | None = None) -> dict[tuple[str, str], dict]:
    """(a, b) with a < b -> {coread, flows}: how many statements (of `keep`, if given) read both, or
    derive one from the other."""
    edges: dict[tuple[str, str], dict] = {}

    def add(a, b, kind, w):
        if a != b and w:
            e = edges.setdefault((min(a, b), max(a, b)), {"coread": 0, "flows": 0})
            e[kind] += w

    for sid, units in shapes.items():
        if keep is None or sid in keep:
            for i, a in enumerate(units):
                for b in units[i + 1 :]:
                    add(a, b, "coread", 1)
    for a, b, sh in flows:
        add(a, b, "flows", len(sh) if keep is None else sum(1 for x in sh if x in keep))
    return edges


def unit_edges(G: Graph) -> dict[tuple[str, str], dict]:
    """Usage between units: read by the same query, or connected by column lineage."""
    return edges_from(*evidence_sets(G))


def project(G: Graph, edges: dict, lineage: bool = True) -> dict:
    """Every unit except transient ingestion columns, and an undirected edge per related pair."""
    units = {
        r["id"]
        for r in G.rows("""MATCH (u) WHERE u:Variable
                                          OR (u:Unjoined AND NOT EXISTS { (u)<-[:HAS_COLUMN]-(:Table {kind: 'transient'}) })
                                        RETURN u.id AS id""")
    }
    rows, linked = [], set()
    for (a, b), e in edges.items():
        w = e["coread"] + (e["flows"] if lineage else 0)
        if w > 0 and a in units and b in units:
            rows.append({"a": a, "b": b, "w": float(w)})
            linked |= {a, b}
    rows += [{"a": u, "b": None, "w": None} for u in units - linked]
    return G.project_pairs(PROJECTION, rows)


def leiden(G: Graph, gamma: float, seed: int) -> dict[str, list[str]]:
    return {f"sem:{k}": ms for k, ms in G.leiden(PROJECTION, gamma, seed).items()}


def stability(G: Graph, groups: dict, shapes: Shapes, flows: Flows, p: dict) -> dict[str, float]:
    """How much of each group comes back when Leiden reruns: half the runs change only the seed, half
    also resample the evidence. Per group, the best Jaccard overlap with any community of a run,
    averaged over the runs: 1 = always comes back whole."""
    runs = p["stability_runs"]
    ids = sorted(shapes.keys() | {x for _, _, sh in flows for x in sh})
    score = defaultdict(float)
    for r in range(runs):
        keep = (
            None
            if r < runs // 2
            else set(random.Random(r).sample(ids, int(len(ids) * p["stability_sample"])))
        )
        project(G, edges_from(shapes, flows, keep), p["lineage"])
        of = {m: k for k, ms in leiden(G, p["gamma"], seed=r + 1).items() for m in ms}
        comm = defaultdict(set)
        for m, k in of.items():
            comm[k].add(m)
        for gid, members in groups.items():
            ms = set(members)
            score[gid] += max(len(ms & comm[k]) / len(ms | comm[k]) for k in {of[m] for m in ms if m in of})
    G.drop_projection(PROJECTION)
    return {g: v / runs for g, v in score.items()}


def evidence(G: Graph, groups: dict[str, list[str]]) -> dict[str, str]:
    """What the namer sees: tables, variables (named), other columns, and a query that reads many members."""
    unit = {}
    for r in G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       RETURN v.id AS u, v.name AS name, collect(DISTINCT t.id) AS tables, collect(c.id) AS cols"""):
        unit[r["u"]] = {"kind": "variable", "label": r["name"], "tables": r["tables"], "cols": r["cols"]}
    for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Unjoined)
                       RETURN c.id AS u, c.name AS name, c.type AS type, t.id AS t"""):
        unit[r["u"]] = {
            "kind": "column",
            "label": f"{short(r['t'])}.{r['name']} {r['type'] or ''}".rstrip(),
            "tables": [r["t"]],
            "cols": [r["u"]],
        }
    reads = {
        r["u"]: r["n"]
        for r in G.rows("""MATCH (u) WHERE u:Variable OR u:Unjoined
        MATCH (u)<-[:IS]-{0,1}(:Column)<-[:READS]-(s:QueryShape) RETURN u.id AS u, count(DISTINCT s) AS n""")
    }
    out = {}
    for sid, members in groups.items():
        tables = Counter(t for m in members for t in unit[m]["tables"])
        cols = {c for m in members for c in unit[m]["cols"]}
        best = G.rows(
            """MATCH (s:QueryShape)-[:READS]->(c:Column) WHERE c.id IN $cols
                         WITH s, count(DISTINCT c) AS n ORDER BY n DESC, s.jobs DESC LIMIT 1
                         RETURN s.sample_sql AS q""",
            cols=sorted(cols),
        )
        vs, cs = (
            sorted((m for m in members if unit[m]["kind"] == kind), key=lambda m: -reads.get(m, 0))
            for kind in ("variable", "column")
        )
        lines = [
            f"### semantic group {sid}",
            f"id: {sid}",
            f"{len(members)} members from {len(tables)} tables: "
            + ", ".join(f"{short(t)} ({n})" for t, n in tables.most_common(10))
            + (" ..." if len(tables) > 10 else ""),
        ]
        if vs:
            lines.append("variables: " + "; ".join(unit[m]["label"] or m for m in vs[:15]))
        if cs:
            lines.append(
                "columns: "
                + "; ".join(unit[m]["label"] for m in cs[:SHOW_MEMBERS])
                + (f"; ... and {len(cs) - SHOW_MEMBERS} more" if len(cs) > SHOW_MEMBERS else "")
            )
        if best and best[0]["q"]:
            q = best[0]["q"]
            lines.append("a query that reads many of them:\n" + (q if len(q) <= 900 else q[:897] + "..."))
        out[sid] = "\n".join(lines)
    return out


def size_buckets(sizes: list[int]) -> str:
    edges = [(2, "2"), (5, "3-5"), (10, "6-10"), (25, "11-25"), (50, "26-50"), (float("inf"), "51+")]
    count = Counter(next(label for top, label in edges if n <= top) for n in sizes)
    return ", ".join(f"{label}: {count[label]}" for _, label in edges)


def run(s: Settings, names: bool = True) -> None:
    p = s.params["cluster"]
    t0 = time.time()
    with Graph(s) as G:
        G.run("CREATE CONSTRAINT semantic_id IF NOT EXISTS FOR (n:Semantic) REQUIRE n.id IS UNIQUE")
        G.delete("(n:Semantic)")

        shapes, flows = evidence_sets(G)
        edges = edges_from(shapes, flows)
        proj = project(G, edges, p["lineage"])
        comms = leiden(G, p["gamma"], p["seed"])
        G.drop_projection(PROJECTION)
        groups = {k: ms for k, ms in comms.items() if len(ms) >= 2}
        G.batch(
            "Semantic",
            """UNWIND $rows AS r
                               CREATE (s:Semantic {id: r.id, level: 1, size: size(r.members), gamma: r.gamma})
                               WITH s, r UNWIND r.members AS mid
                               MATCH (u {id: mid}) WHERE u:Variable OR u:Unjoined CREATE (u)-[:IN_SEMANTIC]->(s)""",
            [{"id": k, "members": ms, "gamma": p["gamma"]} for k, ms in groups.items()],
            200,
        )
        G.run("""MATCH (s:Semantic)<-[:IN_SEMANTIC]-(u)<-[:IS]-{0,1}(:Column)<-[:HAS_COLUMN]-(t:Table)
                 WITH s, count(DISTINCT t) AS n SET s.tables = n""")
        sizes = sorted((len(ms) for ms in groups.values()), reverse=True)
        lineage_only = sum(1 for e in edges.values() if e["flows"] and not e["coread"])
        print(
            f"projection: {proj['nodes']:,} nodes, {proj['rels']:,} relationships ({lineage_only:,} pairs linked "
            f"only by lineage); Leiden gamma {p['gamma']}: {len(comms):,} communities"
        )
        print(
            f"Semantic: {len(groups):,} groups over {sum(sizes):,} members; "
            f"{sum(1 for ms in comms.values() if len(ms) == 1):,} nodes alone (no Semantic)"
        )
        print(f"  sizes: {size_buckets(sizes)}; largest {sizes[:8]}")

        stab = stability(G, groups, shapes, flows, p)
        G.batch(
            "Semantic.stability",
            "UNWIND $rows AS r MATCH (s:Semantic {id: r.id}) SET s.stability = r.v",
            [{"id": k, "v": v} for k, v in stab.items()],
        )
        vals = sorted(stab.values())
        print(
            f"stability ({p['stability_runs']} reruns, half on {p['stability_sample']:.0%} of the statements): "
            f"median {vals[len(vals) // 2]:.2f}, {sum(v >= 0.8 for v in vals)} of {len(vals)} groups at 0.8+, "
            f"{sum(v < 0.5 for v in vals)} below 0.5"
        )

        if names:
            llm = LLM(prompt("semantic_system", **s.business), s)
            named = name_all(llm, evidence(G, groups), ("semantic group", "semantic groups"), BATCH)
            write_names(G, "Semantic", named, llm.model)
            print(f"named: {dict(Counter(d['status'] for d in named.values()))}; {llm.summary()}")
    print(f"{time.time() - t0:.0f}s")

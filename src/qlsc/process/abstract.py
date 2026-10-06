"""Abstract: levels above the first of the State-Action graph (plans/2026-10-06-process-abstraction.md, phase 1).

The first level is faithful and fine (about 800 Action elements for 64 planted actions). Each level above is built from the one below, as
the semantic layer's hierarchy is (qlsc/hierarchy.py), by the same neighbours and Leiden as the first (qlsc/process/build.py):

  1. a node's vector is the mean of its members' stored vectors, so no turn is embedded or annotated again;
  2. each node links to its nearest of the same kind, by the vector index on the elements themselves (Cypher `db.index.vector.queryNodes`:
     as fast as GDS kNN on 3,000 elements, 99.98% exact against 98.5%, the same answer every run, and no scratch nodes), and **those links
     are kept**: `(:State|Action)-[:K_SIM {score, rank, level}]->(:State|Action)`, at every level, first included. A pair's grouping score is
     its text similarity, and when `transition_weight` is above 0 also how alike their transitions are (the same elements either side,
     lifted to the level below);
  3. seeded single-threaded Leiden at `gamma / (L - 1)` over those links, projected from the elements themselves: each community of two or more is a parent, named by an LLM from
     its children; a node that found no company is carried up unchanged and named nothing new;
  4. transitions are lifted to the level by assignment, from the turns, never from the level below's counts;
  5. stop, per kind, when the next level would not be at most `shrink` of the one below, or the kind is `min_nodes` or fewer.

Model: the same two labels. A parent is `(:State|Action {level: L})`, its children `-[:PART_OF]->` it; a node keeps its own `level`, and a node
carried up has no parent at the level. The graph at level L is the nodes of level L or below with no parent of level L or below, and the
transitions whose `level` is L (`SELECTS` and `LEADS_TO`, each joining nodes of that graph). The first level is never rewritten here.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, name_all, prompt
from qlsc.process import build
from qlsc.process.build import LABELS, RELS, BuildError


@dataclass
class Node:
    """One element of one level of one kind: its vector (the mean of its turns', unit length), its turns, and where it ends."""

    id: str
    vec: list[float]
    count: int
    ends: int
    name: str = ""
    description: str = ""
    children: list[str] = field(default_factory=list)  # the ids below it (empty at the first level)
    level: int = 1
    named_by: str | None = None


# ------------------------------------------------------------------------------------------------------------------ read


def first_level(s: Settings, G: Graph) -> tuple[dict[str, dict[str, Node]], dict[str, dict], list[dict]]:
    """The first level as built: {kind: {id: Node}}, each element's stored properties, and the turns (event, conversation, seq, kind, element)."""
    nodes: dict[str, dict[str, Node]] = {k: {} for k in LABELS}
    props: dict[str, dict] = {}
    for kind, label in LABELS.items():
        for r in G.rows(
            f"""MATCH (n:{label}) WHERE n.level = 1
                RETURN n.id AS id, n.embedding AS vec, n.count AS count, n.ends AS ends, n.name AS name, n.description AS description,
                       n.examples AS examples, n.example_conversations AS conversations"""
        ):
            nodes[kind][r["id"]] = Node(
                r["id"], build.unit(r["vec"]), r["count"], r["ends"], r["name"], r["description"]
            )
            props[r["id"]] = {"examples": r["examples"], "conversations": r["conversations"]}
    path = s.work / "process" / "observations.ndjson"
    if not path.is_file():
        raise BuildError(f"{path} does not exist: run qlsc process build first")
    turns = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return nodes, props, turns


# ------------------------------------------------------------------------------------------------------------------ climb


def transition_vectors(turns: list[dict], of: dict[str, str]) -> dict[str, dict]:
    """Per element, who it follows and who follows it, as a sparse unit vector: two elements are alike by their transitions when they sit
    in the same places. `of`: each turn's element at the level."""
    by: dict[str, list[dict]] = defaultdict(list)
    for t in turns:
        by[t["conversation"]].append(t)
    raw: dict[str, Counter] = defaultdict(Counter)
    for ts in by.values():
        ts.sort(key=lambda t: t["seq"])
        for a, b in zip(ts, ts[1:], strict=False):
            if a["kind"] != b["kind"]:
                raw[of[a["event"]]][("out", of[b["event"]])] += 1
                raw[of[b["event"]]][("in", of[a["event"]])] += 1
    out = {}
    for e, c in raw.items():
        norm = math.sqrt(sum(v * v for v in c.values()))
        out[e] = {k: v / norm for k, v in c.items()}
    return out


def sparse_cosine(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


def centroid(children: list[Node]) -> list[float]:
    dims = len(children[0].vec)
    total = sum(c.count for c in children)
    return build.unit([sum(c.vec[d] * c.count for c in children) / total for d in range(dims)])


def parent_id(kind: str, level: int, children: list[str]) -> str:
    """A parent's id: the kind, the level and a hash of its children's ids, so a rebuild that groups the same way gives the same ids,
    whatever the names say."""
    return f"{kind}:L{level}:{hashlib.sha1('|'.join(sorted(children)).encode()).hexdigest()[:12]}"


def nearest(G: Graph, kind: str, members: dict[str, Node], k: int) -> list[dict]:
    """Each member's `k` nearest members of the same kind, by the vector index: rows {a, b, cos, rank}, in rank order. The index holds every level's
    nodes, so it is asked for as many more than `k` as it holds that are not members, and those are filtered out: exact."""
    label = LABELS[kind]
    ids = sorted(members)
    extra = G.value(f"MATCH (n:{label}) RETURN count(n)") - len(ids)
    rows = []
    for i in range(0, len(ids), 500):
        got = G.rows(
            f"""UNWIND $ids AS id MATCH (a:{label} {{id: id}})
                CALL db.index.vector.queryNodes($index, $fetch, a.embedding) YIELD node, score
                WHERE node.id <> a.id
                RETURN a.id AS a, node.id AS b, score""",
            ids=ids[i : i + 500],
            index=build.INDEX[kind],
            fetch=k + extra + 1,
        )
        by: dict[str, list] = defaultdict(list)
        for r in got:
            if r["b"] in members:
                by[r["a"]].append((-r["score"], r["b"]))
        for a, found in by.items():
            for rank, (score, b) in enumerate(sorted(found)[:k], 1):
                rows.append(
                    {"a": a, "b": b, "cos": 2 * -score - 1, "rank": rank}
                )  # the index reports (1 + cosine) / 2
    return sorted(rows, key=lambda r: (r["a"], r["rank"]))


def leiden_rows(
    sim: list[dict], ids: list[str], cut: float, trans: dict[str, dict], lam: float
) -> list[dict]:
    """The nearest links as Leiden's weighted pairs: the cosine above the cut, rescaled to 0..1 and blended with how alike the transitions
    are; an element with no link above the cut is in the projection alone."""
    best: dict[tuple[str, str], float] = {}
    for r in sim:
        if r["cos"] > cut:
            key = tuple(sorted((r["a"], r["b"])))
            best[key] = max(best.get(key, 0.0), (r["cos"] - cut) / (1 - cut))
    rows = []
    for (a, b), w in sorted(best.items()):
        if lam:
            w = (1 - lam) * w + lam * sparse_cosine(trans.get(a, {}), trans.get(b, {}))
        rows.append({"a": a, "b": b, "w": max(w, 1e-6)})
    linked = {r["a"] for r in rows} | {r["b"] for r in rows}
    return rows + [{"a": i, "b": None, "w": None} for i in ids if i not in linked]


# ------------------------------------------------------------------------------------------------------------------ write


def write_neighbours(G: Graph, kind: str, level: int, sim: list[dict], trans: dict[str, dict]) -> None:
    """Keep the links a level was built from: K_SIM {score (the cosine), rank, level, and transitions when they were used}."""
    label = LABELS[kind]
    rows = [
        {
            "a": r["a"],
            "b": r["b"],
            "score": round(r["cos"], 6),
            "rank": r["rank"],
            "transitions": round(sparse_cosine(trans.get(r["a"], {}), trans.get(r["b"], {})), 6)
            if trans
            else None,
        }
        for r in sim
    ]
    for i in range(0, len(rows), 2000):
        G.run(
            f"""UNWIND $rows AS r MATCH (a:{label} {{id: r.a}}), (b:{label} {{id: r.b}})
                CREATE (a)-[:K_SIM {{score: r.score, rank: r.rank, level: $level, transitions: r.transitions}}]->(b)""",
            rows=rows[i : i + 2000],
            level=level,
        )
    G.counts[f"K_SIM{label}{level}"] += len(rows)


def write_parents(G: Graph, kind: str, level: int, parents: dict[str, Node]) -> None:
    """The level's parents, unnamed, and PART_OF from each child: so the index holds them before the next level asks it."""
    label = LABELS[kind]
    rows = [
        {
            "id": n.id,
            "count": n.count,
            "ends": n.ends,
            "children": len(n.children),
            "embedding": [round(x, 5) for x in n.vec],
            "kids": n.children,
        }
        for n in parents.values()
    ]
    for i in range(0, len(rows), 200):
        G.run(
            f"""UNWIND $rows AS r CREATE (p:{label} {{id: r.id, level: $level}})
                SET p.count = r.count, p.ends = r.ends, p.children = r.children, p.embedding = r.embedding
                WITH p, r UNWIND r.kids AS k MATCH (c:{label} {{id: k}}) CREATE (c)-[:PART_OF]->(p)""",
            rows=rows[i : i + 200],
            level=level,
        )


def write_names(G: Graph, kind: str, parents: dict[str, Node]) -> None:
    label = LABELS[kind]
    G.run(
        f"UNWIND $rows AS r MATCH (p:{label} {{id: r.id}}) SET p.name = r.name, p.description = r.description, p.named_by = r.named_by",
        rows=[
            {"id": n.id, "name": n.name, "description": n.description, "named_by": n.named_by}
            for n in parents.values()
        ],
    )


def write_transitions(
    G: Graph, level: int, nodes: dict[str, dict[str, Node]], turns: list[dict], of: dict[str, str]
) -> None:
    count, _, num = build.lift(turns, of)
    kinds = {i: k for k in LABELS for i in nodes[k]}
    for kind, (rel, other) in RELS.items():
        G.batch(
            f"{rel}{level}",
            f"""UNWIND $rows AS r MATCH (a:{LABELS[kind]} {{id: r.a}}), (b:{LABELS[other]} {{id: r.b}})
                CREATE (a)-[:{rel} {{num: r.num, probability: r.probability, level: r.level}}]->(b)""",
            [
                {"a": a, "b": b, "num": n, "probability": round(n / count[a], 6), "level": level}
                for (a, b), n in sorted(num.items())
                if kinds.get(a) == kind
            ],
            size=2000,
        )


# ------------------------------------------------------------------------------------------------------------------ climb


def climb(
    s: Settings, G: Graph, first: dict[str, dict[str, Node]], turns: list[dict], params: dict
) -> list[dict]:
    """The levels above the first, written as they are formed (the next level's neighbours come from the index, which holds them): K_SIM at
    every level, a level's parents unnamed. -> [{level, parents: {kind: {id: Node}}, nodes: {kind: {id: Node}}, of: {turn: node}}]"""
    p = params
    top = {k: dict(v) for k, v in first.items()}
    of = {t["event"]: t["element"] for t in turns}
    sims: dict[str, list[dict]] = {}
    for kind in LABELS:
        sims[kind] = nearest(G, kind, top[kind], p["neighbours"])
        write_neighbours(G, kind, 1, sims[kind], {})
    levels: list[dict] = []
    done = {k: False for k in LABELS}
    for level in range(2, p["max_levels"] + 2):
        trans = transition_vectors(turns, of) if p["transition_weight"] else {}
        made: dict[str, dict[str, Node]] = {}
        for kind in LABELS:
            below = top[kind]
            if done[kind] or kind not in p["kinds"] or len(below) <= p["min_nodes"]:
                done[kind] = True
                continue
            rows = leiden_rows(sims[kind], sorted(below), p["similarity"], trans, p["transition_weight"])
            groups = build.communities(
                G, s, kind, rows, gamma=p["gamma"] / max(1, level - 1), labels=(LABELS[kind],)
            )
            members = [ms for ms in groups.values() if len(ms) > 1]
            after = len(below) - sum(len(ms) for ms in members) + len(members)
            if not members or after > p["shrink"] * len(below):
                done[kind] = True
                continue
            parents = {}
            for ms in members:
                pid = parent_id(kind, level, ms)
                kids = [below[m] for m in ms]
                parents[pid] = Node(
                    pid,
                    centroid(kids),
                    sum(k.count for k in kids),
                    sum(k.ends for k in kids),
                    children=sorted(ms),
                    level=level,
                )
            made[kind] = parents
        if not made:
            break
        for kind, parents in made.items():
            below, grouped = top[kind], {c for n in parents.values() for c in n.children}
            write_parents(G, kind, level, parents)
            member_of = {c: pid for pid, n in parents.items() for c in n.children}
            of = {e: member_of.get(el, el) if LABEL_OF(el) == kind else el for e, el in of.items()}
            top[kind] = parents | {i: n for i, n in below.items() if i not in grouped}
            sims[kind] = nearest(G, kind, top[kind], p["neighbours"])
            write_neighbours(
                G, kind, level, sims[kind], transition_vectors(turns, of) if p["transition_weight"] else {}
            )
        levels.append(
            {"level": level, "parents": made, "nodes": {k: dict(v) for k, v in top.items()}, "of": dict(of)}
        )
    return levels


def LABEL_OF(element_id: str) -> str:
    """The kind an element id belongs to: its prefix."""
    return element_id.split(":", 1)[0]


# ------------------------------------------------------------------------------------------------------------------ name


def name_parents(
    s: Settings, kind: str, parents: dict[str, Node], below: dict[str, Node]
) -> tuple[dict[str, dict], LLM]:
    p = s["process"]
    verbs = ", ".join(p["action_verbs"])
    system = (
        prompt("process_state_parent_system", **s.business)
        if kind == "state"
        else prompt("process_action_parent_system", **s.business, verbs=verbs)
    )
    llm = LLM(system, s, s["llm"]["query_model"])
    ids = {pid: f"{kind[0].upper()}{n}" for n, pid in enumerate(sorted(parents), 1)}

    def evidence(pid: str) -> str:
        kids = sorted((below[c] for c in parents[pid].children), key=lambda n: (-n.count, n.id))[
            : p["name_evidence"]
        ]
        lines = "\n".join(f"- {k.name}: {k.description}" for k in kids)
        return f"[{ids[pid]}] {parents[pid].count} turns in {len(parents[pid].children)} finer {kind}s. The largest:\n{lines}\n\n"

    named = name_all(
        llm,
        {ids[pid]: evidence(pid) for pid in parents},
        (kind, f"{kind}s"),
        p["name_batch"],
        check=build.name_check(s, kind),
    )
    return {pid: named[ids[pid]] for pid in parents}, llm


# ------------------------------------------------------------------------------------------------------------------ run


def run(s: Settings, params: dict | None = None, naming: bool = True) -> dict:
    """Build the levels above the first from the first level in the process database: groups, parents, K_SIM, names, transitions."""
    p = params or s["process"]["levels"]
    seconds: dict[str, float] = {}
    clock = time.perf_counter()

    def lap(stage: str) -> None:
        nonlocal clock
        now = time.perf_counter()
        seconds[stage] = round(seconds.get(stage, 0.0) + now - clock, 2)
        clock = now

    with Graph(s, {"database": s["process"]["database"]}) as G:
        G.delete(build.IS_SCRATCH)
        build.ensure_indexes(s, G)
        G.delete("(n) WHERE n.level >= 2 AND (n:State OR n:Action)")  # parents, and what hangs on them
        G.run("MATCH ()-[r:SELECTS|LEADS_TO]->() WHERE r.level >= 2 DELETE r")
        G.run("MATCH ()-[r:K_SIM]->() DELETE r")
        first, _, turns = first_level(s, G)
        lap("read")
        levels = climb(s, G, first, turns, p)
        lap("group")
        llms: list[LLM] = []
        fallbacks = 0
        below = {k: dict(v) for k, v in first.items()}
        for lv in levels:
            for kind, parents in lv["parents"].items():
                if naming:
                    named, llm = name_parents(s, kind, parents, below[kind])
                    llms.append(llm)
                    # A name the checks refuse twice is not worth a pass: the parent takes its largest child's, and says so.
                    for pid, v in named.items():
                        if v["status"] == "failed":
                            big = max(
                                (below[kind][c] for c in parents[pid].children), key=lambda n: (n.count, n.id)
                            )
                            named[pid] = {
                                "name": big.name,
                                "description": big.description,
                                "status": "fallback",
                            }
                            fallbacks += 1
                else:
                    named = {
                        pid: {"name": f"{kind} L{lv['level']} {n}", "description": "not named"}
                        for n, pid in enumerate(sorted(parents), 1)
                    }
                for pid, n in parents.items():
                    n.name, n.description = named[pid]["name"], named[pid]["description"]
                    n.named_by = (
                        ("fallback" if named[pid].get("status") == "fallback" else llms[-1].model)
                        if naming
                        else None
                    )
                write_names(G, kind, parents)
            lap("name")
            for kind in LABELS:
                below[kind] = lv["nodes"][kind]
            write_transitions(G, lv["level"], lv["nodes"], turns, lv["of"])
        lap("write")
        made = sum(len(v) for lv in levels for v in lv["parents"].values())
        got = G.value("MATCH (n) WHERE n.level >= 2 AND (n:State OR n:Action) RETURN count(n)")
        if got != made:
            raise BuildError(f"the process database holds {got} parent elements, built {made}")
        if G.value("MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Observation') RETURN count(n)"):
            raise BuildError("scratch observation nodes were left in the process database")
        ksim = G.value("MATCH ()-[r:K_SIM]->() RETURN count(r)")
    return {
        "levels": [
            {
                "level": lv["level"],
                **{k: len(lv["nodes"][k]) for k in LABELS},
                **{f"{k}_parents": len(lv["parents"].get(k, {})) for k in LABELS},
            }
            for lv in levels
        ],
        "first": {k: len(v) for k, v in first.items()},
        "fallbacks": fallbacks,
        "k_sim": ksim,
        "seconds": seconds,
        "llm": [x.summary() for x in llms],
        "cost": sum(x.cost() or 0 for x in llms),
        "parents": made,
    }


def report(s: Settings) -> None:
    m = run(s)
    print(f"first level: {m['first']['state']} States, {m['first']['action']} Actions")
    for lv in m["levels"]:
        print(
            f"  level {lv['level']}: {lv['state']} States ({lv['state_parents']} new), {lv['action']} Actions ({lv['action_parents']} new)"
        )
    if not m["levels"]:
        print("  no level above the first would be smaller")
    print(f"  {m['k_sim']:,} K_SIM links kept")
    for line in m["llm"]:
        print(f"  {line}")
    if m["fallbacks"]:
        print(f"  {m['fallbacks']} parents were refused a name twice and took their largest child's")
    print("  seconds: " + ", ".join(f"{k} {v}" for k, v in m["seconds"].items()))

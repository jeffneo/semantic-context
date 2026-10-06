"""Build: the annotated turns become canonical States and Actions with counted, probabilistic transitions, in the `process` database.

Stages, each a pure function of its inputs (every LLM and embedding call is cached by request, the grouping is seeded and
single-threaded, projections are fed sorted), so the same annotations give the same graph and a rerun makes no calls:

  1. embed     each description once (a State by `process.state_embeds`)
  2. group     per kind, GDS kNN over the observations' embeddings (nearest neighbours, never all pairs), then seeded Leiden over
               the neighbour graph: each community is one element. Observations are scratch nodes for GDS only: they are deleted
               before the build ends, and what stays is the elements.
  3. name      an LLM names each element from the descriptions closest to its middle (llm.query_model: the judgement is here)
  4. fold      elements whose names are near-duplicates are one (greedy, largest first, by name vectors: never transitive, so no blobs)
  5. lift      consecutive turns become SELECTS (a State, then the Action the agent took) and LEADS_TO (an Action, then the State the
               customer was left in), `num` pairs and `probability` = num / the element's turns, by assignment, so a rerun repeats
  6. write     the elements and their transitions; the stage reads them back and fails if they are not what it built

The model is two labels, State and Action (plans/2026-10-05-text-graph-construction.md, decision 1). An element carries its name,
description, `count` of turns, `ends` (turns after which nothing followed), the mean `embedding` of its turns, and a few
`examples` (event ids) and the `example_conversations` they are from (the warehouse's key for each call); the event-to-element mapping is a file beside the build (`observations.ndjson`), not graph.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict

from qlsc.config import Settings, secret
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, check_name, cosine, name_all, prompt

LABELS = {"state": "State", "action": "Action"}
SCRATCH = "Observation"  # scratch nodes are Observation<Kind> (ObservationState, ObservationAction), never the elements' own labels
IS_SCRATCH = "(n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Observation')"
CREATE_DATABASE = "CREATE DATABASE $name IF NOT EXISTS WAIT"
CONSTRAINTS = (
    "CREATE CONSTRAINT process_state IF NOT EXISTS FOR (n:State) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT process_action IF NOT EXISTS FOR (n:Action) REQUIRE n.id IS UNIQUE",
)
RELS = {"state": ("SELECTS", "action"), "action": ("LEADS_TO", "state")}  # what follows a turn of each kind
KNN = "obs_knn"
LEIDEN = "obs_leiden"


class BuildError(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------------------- annotations


def load(s: Settings) -> list[dict]:
    """The per-turn annotations `qlsc process annotate` wrote, in conversation order; a turn with no description is not a turn."""
    path = s.work / "process" / "annotations-turn.ndjson"
    if not path.is_file():
        raise BuildError(f"{path} does not exist: run qlsc process annotate --unit turn first")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [r for r in rows if r["description"] and not r["problems"]]


def text_to_embed(s: Settings, r: dict) -> str:
    """What is embedded for grouping: an Action's description; a State's whole line, or only what is established."""
    if r["kind"] == "state" and s["process"]["state_embeds"] == "established":
        return r["answer"]["established"].strip()
    return r["description"]


# ------------------------------------------------------------------------------------------------------------------ group


def unit(v: list[float]) -> list[float]:
    n = sum(x * x for x in v) ** 0.5
    return [x / n for x in v]


def scratch(kind: str) -> str:
    return SCRATCH + LABELS[kind]


def neighbours(
    G: Graph,
    s: Settings,
    kind: str,
    ids: list[str],
    vec: dict[str, list[float]],
    k: int | None = None,
    cut: float | None = None,
) -> list[dict]:
    """GDS kNN over one kind's observations: rows {a, b, w} of near pairs (w in 0..1: the cosine above the cutoff, rescaled), and
    one row with no partner for an observation that has none, so every observation is in the projection."""
    p = s["process"]
    k, cut = (
        k or p["neighbours"],
        p["similarity"] if cut is None else cut,
    )  # levels above the first take their own
    label = scratch(kind)
    G.batch(
        label,
        f"UNWIND $rows AS r CREATE (:{label} {{id: r.id, embedding: r.embedding}})",
        [{"id": i, "embedding": vec[i]} for i in ids],
        size=500,
    )
    # GDS numbers nodes in the order they arrive, and the kNN's tie-breaking among near-duplicate turns follows that numbering. A
    # native projection takes Neo4j's internal ids, which a deleted-and-recreated scratch node does not get in the same order, so the
    # projection is built from a sorted query: the same turns are the same graph on every build.
    G.drop_projection(KNN)
    G.run(
        f"""MATCH (n:{label}) WITH n ORDER BY n.id
            WITH gds.graph.project($g, n, null, {{sourceNodeProperties: n {{.embedding}}, sourceNodeLabels: ['{label}'], targetNodeLabels: null, targetNodeProperties: null}}) AS g
            RETURN g.nodeCount""",
        g=KNN,
    )
    found = G.rows(
        """CALL gds.knn.stream($g, {nodeProperties: ['embedding'], topK: $k, similarityCutoff: $cut, randomSeed: $seed,
                                   concurrency: 1, sampleRate: 1.0, deltaThreshold: 0.0})
           YIELD node1, node2, similarity
           RETURN gds.util.asNode(node1).id AS a, gds.util.asNode(node2).id AS b, similarity AS w""",
        g=KNN,
        k=k,
        cut=(1 + cut) / 2,  # GDS reports (1 + cosine) / 2
        seed=p["seed"],
    )
    G.drop_projection(KNN)
    best: dict[tuple[str, str], float] = {}
    for r in found:
        key = tuple(sorted((r["a"], r["b"])))
        best[key] = max(best.get(key, 0.0), 2 * r["w"] - 1)  # back to the cosine
    rows = [{"a": a, "b": b, "w": max((w - cut) / (1 - cut), 1e-6)} for (a, b), w in sorted(best.items())]
    linked = {r["a"] for r in rows} | {r["b"] for r in rows}
    return rows + [{"a": i, "b": None, "w": None} for i in ids if i not in linked]


def communities(
    G: Graph,
    s: Settings,
    kind: str,
    rows: list[dict],
    gamma: float | None = None,
    labels: tuple[str, ...] | None = None,
) -> dict[str, list[str]]:
    """Seeded Leiden over rows {a, b, w}. The nodes are the scratch ones of a first-level grouping, or `labels`: the elements themselves."""
    G.project_pairs(LEIDEN, rows, labels=labels or (scratch(kind),))
    out = G.leiden(LEIDEN, gamma or s["process"]["gamma"], s["process"]["seed"])
    G.drop_projection(LEIDEN)
    return out


# -------------------------------------------------------------------------------------------------------------------- name


def centre(members: list[str], vec: dict[str, list[float]]) -> list[float]:
    dims = len(vec[members[0]])
    mean = [sum(vec[m][d] for m in members) / len(members) for d in range(dims)]
    return unit(mean)


def closest(members: list[str], vec: dict[str, list[float]], n: int) -> list[str]:
    c = centre(members, vec)
    return sorted(members, key=lambda m: (-cosine(c, vec[m]), m))[:n]


def name_check(s: Settings, kind: str):
    verbs = {v.lower() for v in s["process"]["action_verbs"]}

    def check(item: dict | None) -> str | None:
        error = check_name(item, words=(2, 8), chars=(15, 500))
        if error or kind == "state":
            return error
        first = item["name"].split()[0].lower()
        return None if first in verbs else f"an action's name must begin with one of {sorted(verbs)}"

    return check


def evidence(key: str, members: list[str], shown: list[str], text: dict[str, str]) -> str:
    lines = "\n".join(f"- {text[m]}" for m in shown)
    return (
        f"[{key}] {len(members)} turn{'s' if len(members) != 1 else ''}. Closest to the middle:\n{lines}\n\n"
    )


def name_elements(
    s: Settings, kind: str, groups: dict[str, list[str]], vec: dict, text: dict[str, str]
) -> tuple[dict[str, dict], LLM]:
    p = s["process"]
    verbs = ", ".join(p["action_verbs"])
    system = (
        prompt("process_state_name_system", **s.business)
        if kind == "state"
        else prompt("process_action_name_system", **s.business, verbs=verbs)
    )
    llm = LLM(system, s, s["llm"]["query_model"])
    # short ids the model can copy back: S1, S2, ... by the group's smallest member
    keys = sorted(groups)
    ids = {k: f"{kind[0].upper()}{n}" for n, k in enumerate(keys, 1)}
    ev = {
        ids[k]: evidence(ids[k], groups[k], closest(groups[k], vec, p["name_evidence"]), text) for k in keys
    }
    named = name_all(llm, ev, (kind, f"{kind}s"), p["name_batch"], check=name_check(s, kind))
    return {k: named[ids[k]] for k in keys}, llm


# --------------------------------------------------------------------------------------------------------------------- fold


def fold(
    s: Settings, groups: dict[str, list[str]], named: dict[str, dict], emb: Embedder
) -> dict[str, list[str]]:
    """Elements with near-duplicate names become one: largest first, each joins the first kept element it is close enough to
    (never a chain), so folding cannot grow a blob. Returns {kept key: all members}."""
    cut = s["process"]["fold_similarity"]
    order = sorted(groups, key=lambda k: (-len(groups[k]), named[k].get("name", ""), k))
    names = [named[k].get("name") or k for k in order]
    vectors = dict(zip(order, (unit(v) for v in emb.embed(names)), strict=True))
    kept: list[str] = []
    out: dict[str, list[str]] = {}
    for k in order:
        # unit vectors, so the cosine is the dot product, which math.sumprod does in C: the quadratic scan was the slowest warm stage
        home = next((j for j in kept if math.sumprod(vectors[k], vectors[j]) >= cut), None)
        if home is None:
            kept.append(k)
            out[k] = list(groups[k])
        else:
            out[home] += groups[k]
    return {k: sorted(v) for k, v in out.items()}


# --------------------------------------------------------------------------------------------------------------------- lift


def element_id(kind: str, name: str) -> str:
    return f"{kind}:{hashlib.sha1(name.encode()).hexdigest()[:12]}"


def lift(rows: list[dict], element_of: dict[str, str]) -> tuple[Counter, Counter, Counter]:
    """Counts per element: turns, turns after which nothing followed, and per transition the pairs of consecutive turns.
    A transition is a State then an Action, or an Action then a State; two turns of one kind in a row are not a transition."""
    count, ends, num = Counter(), Counter(), Counter()
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["conversation"]].append(r)
    for turns in by.values():
        turns.sort(key=lambda r: r["seq"])
        for i, r in enumerate(turns):
            here = element_of[r["event"]]
            count[here] += 1
            after = turns[i + 1] if i + 1 < len(turns) else None
            if after and after["kind"] == RELS[r["kind"]][1]:
                num[(here, element_of[after["event"]])] += 1
            else:
                ends[here] += 1
    return count, ends, num


# -------------------------------------------------------------------------------------------------------------------- write


INDEX = {"state": "process_state_embedding", "action": "process_action_embedding"}


def ensure_indexes(s: Settings, G: Graph) -> None:
    """A cosine vector index on each label's `embedding` (every level's nodes share it): how a query enters the graph by similarity, and
    how the levels find each element's nearest. Idempotent; waits until the indexes are online."""
    dims = s["embeddings"]["dimensions"]
    for kind, label in LABELS.items():
        G.run(
            f"CREATE VECTOR INDEX {INDEX[kind]} IF NOT EXISTS FOR (n:{label}) ON n.embedding "
            "OPTIONS {indexConfig: {`vector.dimensions`: $dims, `vector.similarity_function`: 'cosine'}}",
            dims=dims,
        )
    for _ in range(300):
        states = {
            r["state"]
            for r in G.rows(
                "SHOW INDEXES YIELD name, state WHERE name IN $names RETURN state", names=list(INDEX.values())
            )
        }
        if states == {"ONLINE"}:
            return
        time.sleep(1)
    raise BuildError("the vector indexes did not come online")


def write(s: Settings, elements: dict[str, dict], num: Counter, database: str) -> None:
    """Replace the elements and transitions in the process database, then read them back: a stage asserts that its output landed."""
    with Graph(s, {"database": "system"}) as system:
        system.run(CREATE_DATABASE, name=database)
    with Graph(s, {"database": database}) as G:
        for q in CONSTRAINTS:
            G.run(q)
        ensure_indexes(s, G)
        G.delete("(n) WHERE n:State OR n:Action")
        for kind, label in LABELS.items():
            G.batch(
                f"{label}",
                f"""UNWIND $rows AS r CREATE (n:{label} {{id: r.id, level: 1}})
                    SET n.name = r.name, n.description = r.description, n.count = r.count, n.ends = r.ends,
                        n.embedding = r.embedding, n.examples = r.examples, n.example_conversations = r.example_conversations,
                        n.named_by = r.named_by""",
                [dict(e, id=i) for i, e in sorted(elements.items()) if e["kind"] == kind],
                size=500,
            )
        for kind, (rel, _) in RELS.items():
            G.batch(
                rel,
                f"""UNWIND $rows AS r MATCH (a:{LABELS[kind]} {{id: r.a}}), (b:{LABELS[RELS[kind][1]]} {{id: r.b}})
                    CREATE (a)-[:{rel} {{num: r.num, probability: r.probability, level: 1}}]->(b)""",
                [
                    {
                        "a": a,
                        "b": b,
                        "num": n,
                        "probability": round(n / elements[a]["count"], 6),
                    }
                    for (a, b), n in sorted(num.items())
                    if elements[a]["kind"] == kind
                ],
                size=2000,
            )
        got = G.rows(
            "MATCH (n) WHERE n:State OR n:Action RETURN labels(n)[0] AS label, count(n) AS n, sum(n.count) AS turns"
        )
        want = Counter(e["kind"] for e in elements.values())
        for r in got:
            if r["n"] != want[r["label"].lower()]:
                raise BuildError(
                    f"the process database holds {r['n']} {r['label']} elements, built {want[r['label'].lower()]}"
                )
        rels = G.value("MATCH ()-[r:SELECTS|LEADS_TO]->() RETURN count(r)")
        if rels != len(num):
            raise BuildError(f"the process database holds {rels} transitions, built {len(num)}")
        if G.value("MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Observation') RETURN count(n)"):
            raise BuildError("scratch observation nodes were left in the process database")


# --------------------------------------------------------------------------------------------------------------------- run


# ------------------------------------------------------------------------------------------------------------------ composite


SAFE = re.compile(r"^[A-Za-z][A-Za-z0-9.]*$")


def join_composite(s: Settings) -> str | None:
    """The process database as an alias of the composite database (`process.composite`), on the Virtual Graph instance, so one Cypher
    query can put the process beside the semantic layer, memory and the rows (`USE <composite>.process`). Idempotent; None when no
    composite is configured. The composite's alias for the semantic layer's instance says how it reaches it (`url`); the password is the
    instance's own, never written down."""
    cfg = s["process"].get("composite")
    instance = s.get("virtualize", {}).get("neo4j")
    if not cfg or not instance:
        return None
    name = f"{cfg['database']}.{s['process']['database']}"
    if not SAFE.match(name):
        raise BuildError(f"{name!r} is not a plain composite alias name")
    with Graph(s, {**instance, "database": "system"}) as system:
        system.run(
            f"CREATE ALIAS {name} IF NOT EXISTS FOR DATABASE {s['process']['database']} AT $url USER $user PASSWORD $password",
            url=cfg["url"],
            user=s["neo4j"]["user"],
            password=secret("NEO4J_PASSWORD"),
        )
    return name


def run(
    s: Settings, rows: list[dict] | None = None, database: str | None = None, naming: bool = True
) -> dict:
    """The whole build from the annotations: elements, transitions, the observation record, and what it took.

    `rows`, `database` and `naming` exist for timing the stages that need no LLM at a size nobody would annotate (the scale set's
    placeholder text, in a database of its own, its elements named by number): a build of the estate passes none of them."""
    seconds: dict[str, float] = {}
    clock = time.perf_counter()

    def lap(stage: str) -> None:
        nonlocal clock
        now = time.perf_counter()
        seconds[stage] = round(seconds.get(stage, 0.0) + now - clock, 2)
        clock = now

    db = database or s["process"]["database"]
    rows = load(s) if rows is None else rows
    emb = Embedder(s)
    texts = {r["event"]: text_to_embed(s, r) for r in rows}
    ids = sorted(texts)
    vec = dict(zip(ids, (unit(v) for v in emb.embed([texts[i] for i in ids])), strict=True))
    description = {r["event"]: r["description"] for r in rows}
    kind_of = {r["event"]: r["kind"] for r in rows}
    conversation = {r["event"]: r["conversation"] for r in rows}
    lap("embed")

    elements: dict[str, dict] = {}
    element_of: dict[str, str] = {}
    llms: list[LLM] = []
    stats: dict = {}
    with Graph(s, {"database": "system"}) as system:
        system.run(CREATE_DATABASE, name=db)
    with Graph(s, {"database": db}) as G:
        G.delete(IS_SCRATCH)
        groups_of = {}
        try:
            for kind in LABELS:
                members = [i for i in ids if kind_of[i] == kind]
                if not members:
                    continue
                pairs = neighbours(G, s, kind, members, vec)
                lap("neighbours")
                groups_of[kind] = communities(G, s, kind, pairs)
                lap("group")
        finally:
            G.delete(IS_SCRATCH)  # scratch for GDS, gone whether or not the grouping finished
    for kind, groups in groups_of.items():
        if naming:
            named, llm = name_elements(s, kind, groups, vec, description)
            llms.append(llm)
            failed = [k for k, v in named.items() if v["status"] == "failed"]
            if failed:
                raise BuildError(f"{len(failed)} {kind} elements could not be named: {failed[:3]}")
            lap("name")
            folded = fold(s, groups, named, emb)
            lap("fold")
        else:
            keys = sorted(groups)
            named = {
                k: {"name": f"{kind} {n}", "description": "not named", "status": "ok"}
                for n, k in enumerate(keys, 1)
            }
            folded = {k: sorted(v) for k, v in groups.items()}
        for k, members in folded.items():
            name = named[k]["name"]
            eid = element_id(kind, name)
            if eid in elements:
                raise BuildError(f"two {kind} elements are named {name!r}")
            elements[eid] = {
                "kind": kind,
                "name": name,
                "description": named[k]["description"],
                "members": members,
                "embedding": [round(x, 5) for x in centre(members, vec)],
                "examples": (near := closest(members, vec, s["process"]["examples"])),
                # the conversations those turns are from: the warehouse's key for each call, so a State reaches its calls' rows
                "example_conversations": [conversation[e] for e in near],
                "named_by": llms[-1].model if naming else None,
            }
            for m in members:
                element_of[m] = eid
        stats[kind] = {"groups": len(groups), "after_fold": len(folded)}
    count, ends, num = lift(rows, element_of)
    for eid, e in elements.items():
        e["count"], e["ends"] = count[eid], ends[eid]
    lap("lift")
    write(s, {i: {k: v for k, v in e.items() if k != "members"} for i, e in elements.items()}, num, db)
    lap("write")
    alias = join_composite(s) if database is None else None
    if database is None:
        record = s.work / "process" / "observations.ndjson"
        with open(record, "w") as f:
            for r in sorted(rows, key=lambda r: (r["conversation"], r["seq"])):
                f.write(
                    json.dumps(
                        {
                            "event": r["event"],
                            "conversation": r["conversation"],
                            "seq": r["seq"],
                            "kind": r["kind"],
                            "element": element_of[r["event"]],
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
    sizes = {
        k: sorted((e["count"] for e in elements.values() if e["kind"] == k), reverse=True) for k in LABELS
    }
    return {
        "turns": len(rows),
        "elements": {k: len(v) for k, v in sizes.items()},
        "singletons": {k: sum(1 for n in v if n == 1) for k, v in sizes.items()},
        "largest": {k: v[:3] for k, v in sizes.items()},
        "transitions": len(num),
        "stages": stats,
        "seconds": seconds,
        "llm": [x.summary() for x in llms],
        "cost": sum(x.cost() or 0 for x in llms),
        "database": db,
        "composite": alias,
    }


def report(s: Settings) -> None:
    m = run(s)
    print(
        f"{m['turns']} turns -> {m['elements']['state']} States, {m['elements']['action']} Actions, {m['transitions']} transitions"
    )
    for k in LABELS:
        st = m["stages"][k]
        print(
            f"  {k}: {st['groups']} groups, {st['after_fold']} after folding names; "
            f"{m['singletons'][k]} singletons; largest {m['largest'][k]}"
        )
    for line in m["llm"]:
        print(f"  {line}")
    print("  seconds: " + ", ".join(f"{k} {v}" for k, v in m["seconds"].items()))
    if m["composite"]:
        print(f"joined to the composite as {m['composite']}")
    print(
        f"in database {s['process']['database']}; the turn-to-element record is {s.work}/process/observations.ndjson"
    )

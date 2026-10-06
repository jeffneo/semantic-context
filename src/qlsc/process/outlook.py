"""Outlook: where a live case stands, what usually follows, and how cases from there ended (plans/2026-10-06-process-abstraction.md, phase 4).

A conversation is read up to a turn, and:

  1. locate   the customer's latest turn is annotated as a State exactly as the build does (one cached call), embedded, and looked up in
              the State vector index (`process_state_embedding`): the nearest States with their similarity. Several, not one: a case between
              two States is said to be, and 90% of States are too thin to carry odds alone (phase 3).
  2. pool     the nearest States' counts are pooled, each weighted by how near it is (`exp((similarity - nearest) / temperature)`, so the
              nearest counts most): the case's odds of ending well and in what, and for each Action the reps took next, how often and how
              the cases that took it ended. Counts, not rates, so a State with few conversations weighs what it has. Nearness, not coarseness,
              is what covers the thin States without mixing stages (decision 9).
  3. compare  the Actions open from here, side by side: how often reps took each and how the cases that took each ended (pooled, then pulled
              toward that Action's own rate by `prior` pseudo-transitions, so a pair seen twice is not its two cases). **Observational:** the
              reps who take an Action may be handling easier cases; the payload says so.

`pool` is a function of counts alone, so the evaluation (eval/process_outlook.py) runs the same code over counts with a conversation taken
out. The counts come from properties `qlsc process absorb` stored on the graph (`support`, `support_good`, `outcome_kinds`, `outcome_counts`
on elements; `num`, `num_good` on transitions).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from contextlib import nullcontext
from dataclasses import dataclass, field

from qlsc import meter
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import Embedder
from qlsc.process import absorb, build
from qlsc.process.annotate import Annotator
from qlsc.process.build import BuildError
from qlsc.process.source import Turn

NOTE = (
    "Observational: these are how cases from here went when reps took each Action, not what the Action does. "
    "The reps who take one may be handling easier cases."
)


@dataclass
class Stats:
    """The counts pooling reads, however they were got (the graph's properties, or an evaluation's counts with a conversation taken out)."""

    state: dict[str, dict]  # id -> {name, n, good, kinds: {kind: count}}
    nexts: dict[
        str, dict[str, tuple[int, int]]
    ]  # State id -> {Action id: (transitions, those in cases that ended well)}
    action: dict[str, dict] = field(default_factory=dict)  # id -> {name, n, good}
    base: float = 0.5  # the share that ends well, the target thin counts are pulled toward


# ----------------------------------------------------------------------------------------------------------------------- read


def stats_from_graph(G: Graph, ids: list[str], level: int) -> Stats:
    """The counts for these States and the Actions at `level` that follow them, from the properties `qlsc process absorb` stored."""
    state = {}
    for r in G.rows(
        """MATCH (n:State) WHERE n.id IN $ids
           RETURN n.id AS id, n.name AS name, n.support AS n, n.support_good AS good, n.outcome_kinds AS kinds, n.outcome_counts AS counts""",
        ids=ids,
    ):
        if r["n"] is None:
            raise BuildError("the States hold no counts: run qlsc process absorb")
        state[r["id"]] = {
            "name": r["name"],
            "n": r["n"],
            "good": r["good"],
            "kinds": dict(zip(r["kinds"] or [], r["counts"] or [], strict=True)),
        }
    nexts: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    action = {}
    for r in G.rows(
        """MATCH (s:State)-[x:SELECTS]->(a:Action) WHERE s.id IN $ids AND x.level = $level
           RETURN s.id AS state, a.id AS action, a.name AS name, x.num AS num, x.num_good AS good, a.support AS n, a.support_good AS a_good""",
        ids=ids,
        level=level,
    ):
        nexts[r["state"]][r["action"]] = (r["num"], r["good"])
        action[r["action"]] = {"name": r["name"], "n": r["n"], "good": r["a_good"]}
    return Stats(state, dict(nexts), action, base_rate(G))


def base_rate(G: Graph) -> float:
    """The share of the turns through the States that were in cases that ended well: what a thin count is pulled toward."""
    r = G.rows("MATCH (n:State) RETURN sum(n.support_good) AS good, sum(n.support) AS n")[0]
    return r["good"] / r["n"]


def base_of(c: absorb.Counts) -> float:
    """`base_rate`, from counts."""
    states = [e for e in c.through if e.startswith("state:")]
    total = sum(c.through[e] for e in states)
    return sum(c.through_good[e] for e in states) / total if total else 0.5


def stats_from_counts(
    c: absorb.Counts,
    ids: list[str],
    names: dict[str, str] | None = None,
    base: float | None = None,
) -> Stats:
    """The same counts from an evaluation's `absorb.Counts` (built at a level, a conversation perhaps taken out)."""
    names = names or {}
    state = {
        e: {
            "name": names.get(e, e),
            "n": c.through.get(e, 0),
            "good": c.through_good.get(e, 0),
            "kinds": {k: v for k, v in c.through_kind[e].items() if v > 0} if e in c.through_kind else {},
        }
        for e in ids
    }
    nexts = {e: {a: (n, c.out_good[e][a]) for a, n in c.out[e].items() if n > 0} for e in ids if e in c.out}
    seen = {a for row in nexts.values() for a in row}
    action = {
        a: {
            "name": names.get(a, a),
            "n": c.through.get(a, 0),
            "good": c.through_good.get(a, 0),
        }
        for a in seen
    }
    return Stats(state, nexts, action, base_of(c) if base is None else base)


# ----------------------------------------------------------------------------------------------------------------------- pool


def weights(similarities: list[float], temperature: float) -> list[float]:
    """Each located State's weight: 1 for the nearest, falling off as exp(-(distance in cosine) / temperature). 0 temperature: the nearest only."""
    if not similarities:
        return []
    top = max(similarities)
    if temperature <= 0:
        return [1.0 if x == top else 0.0 for x in similarities]
    return [math.exp((x - top) / temperature) for x in similarities]


def pool(stats: Stats, located: list[tuple[str, float]], p: dict, floor: int, prior: float) -> dict:
    """The outlook from the nearest States: `located` is [(State id, cosine)], nearest first; `p` is `process.outlook`; `floor` is
    `process.min_support`; `prior` is `process.absorb.prior`.
    -> {end_well, support, outcomes: [(kind, odds)], actions: [{action, name, probability, support, end_well_after}], recommended, most_common}"""
    near = located[: p["states"]]
    w = weights([x for _, x in near], p["temperature"])
    mass = good = 0.0
    kinds: Counter = Counter()
    num: Counter = Counter()
    num_good: Counter = Counter()
    for (sid, _), wi in zip(near, w, strict=True):
        st = stats.state.get(sid)
        if st is None or wi <= 0:
            continue
        mass += wi * st["n"]
        good += wi * st["good"]
        for k, v in st["kinds"].items():
            kinds[k] += wi * v
        for a, (n, g) in stats.nexts.get(sid, {}).items():
            num[a] += wi * n
            num_good[a] += wi * g
    out = {
        "support": mass,
        "end_well": absorb.smoothed(good, mass, stats.base, prior) if mass >= floor else None,
        "outcomes": [
            (k, v / mass)
            for k, v in sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))[: p["outcomes_shown"]]
        ]
        if mass >= floor
        else [],
    }
    total = sum(num.values())
    actions = []
    for a in sorted(num, key=lambda a: (-num[a], a)):
        info = stats.action.get(a, {"name": a, "n": 0, "good": 0})
        own = absorb.smoothed(info["good"], info["n"], stats.base, prior)
        actions.append(
            {
                "action": a,
                "name": info["name"],
                "probability": num[a] / total,
                "support": num[a],
                "end_well_after": (num_good[a] + p["prior"] * own) / (num[a] + p["prior"]),
            }
        )
    out["actions"] = actions
    ranked = [x for x in actions if x["support"] >= floor]
    out["recommended"] = max(
        ranked, key=lambda x: (x["end_well_after"], x["probability"], x["action"]), default=None
    )
    out["most_common"] = ranked[0] if ranked else None  # `actions` are most often taken first
    return out


# ----------------------------------------------------------------------------------------------------------------------- locate


def last_state(turns: list[Turn], upto: int | None) -> int:
    """The index of the customer's latest turn up to sequence `upto` (all by default)."""
    shown = [i for i, t in enumerate(turns) if upto is None or t.seq <= upto]
    for i in reversed(shown):
        if turns[i].kind == "state":
            return i
    raise BuildError("the conversation has no customer turn yet: nothing to locate")


def embed_state(
    s: Settings, annotator: Annotator, embedder: Embedder, turns: list[Turn], i: int
) -> tuple[dict, list[float]]:
    """The turn as the build sees it: annotated from the conversation so far (cached when the build saw it), and embedded the same way."""
    r = annotator.turn(turns, i)
    if r["problems"] or not r["description"]:
        raise BuildError(f"turn {turns[i].seq} could not be annotated as a State: {r['problems']}")
    return r, build.unit(embedder.embed([build.text_to_embed(s, r)])[0])


def nearest_states(G: Graph, vec: list[float], k: int) -> list[tuple[str, float]]:
    """The `k` nearest States by the vector index: [(id, cosine)], nearest first (the index reports (1 + cosine) / 2)."""
    return [
        (r["id"], 2 * r["score"] - 1)
        for r in G.rows(
            "CALL db.index.vector.queryNodes($index, $k, $vec) YIELD node, score RETURN node.id AS id, score ORDER BY score DESC, id",
            index=build.INDEX["state"],
            k=k,
            vec=vec,
        )
    ]


def at(s: Settings, turns: list[Turn], upto: int | None = None, G: Graph | None = None) -> dict:
    """The outlook for a conversation read up to sequence `upto`: the State located, the odds, and the Actions open: {state, located, outlook, measured}."""
    p = s["process"]["outlook"]
    with (
        nullcontext(G) if G is not None else Graph(s, {"database": s["process"]["database"]}) as g,
        meter.measure() as m,
    ):
        i = last_state(turns, upto)
        r, vec = embed_state(s, Annotator(s), Embedder(s), turns, i)
        found = nearest_states(g, vec, p["states"])
        stats = stats_from_graph(g, [x for x, _ in found], p["level"])
        out = pool(stats, found, p, s["process"]["min_support"], s["process"]["absorb"]["prior"])
    return {
        "turn": turns[i].seq,
        "state": r["description"],
        "located": [
            {
                "id": x,
                "name": stats.state[x]["name"],
                "similarity": round(sim, 3),
                "support": stats.state[x]["n"],
            }
            for x, sim in found
            if x in stats.state
        ],
        "outlook": out,
        "measured": m.measure(),
    }


def show(o: dict, shown: int) -> str:
    """The outlook as text for a reader or an agent."""
    out = o["outlook"]
    lines = [f"The case after turn {o['turn']}: {o['state']}", "", "Nearest States:"]
    for x in o["located"][:3]:
        lines.append(f"  {x['similarity']:.2f}  {x['name']}  ({x['support']} conversations)")
    if out["end_well"] is None:
        lines.append(f"\nToo few like it to say how it ends ({out['support']:.1f} conversations pooled).")
    else:
        lines.append(
            f"\nCases like this ended well {out['end_well']:.0%} of the time ({out['support']:.0f} conversations pooled)."
        )
        lines += [f"  {odds:.0%}  {k}" for k, odds in out["outcomes"]]
    lines.append("\nWhat reps did next, and how those cases ended:")
    for a in out["actions"][:shown]:
        lines.append(
            f"  {a['probability']:.0%} of the time  {a['name']}  ->  ended well {a['end_well_after']:.0%}  ({a['support']:.1f} cases)"
        )
    if out["recommended"]:
        lines.append(f"\nBest ending after: {out['recommended']['name']}")
    lines.append("\n" + NOTE)
    m = o["measured"]
    lines.append(
        f"[{m['seconds']} s, {m['llm_calls']} LLM calls ({m['llm_cached']} cached), {m['embedded']} texts embedded]"
    )
    return "\n".join(lines)


def report(s: Settings, conversation: str, turn: int | None, with_context: bool = False) -> None:
    """`qlsc process outlook CONVERSATION [--turn N] [--with-context]`: the outlook, and beside it what the warehouse held about the customer as of the call."""
    from qlsc.process import context, source

    src = source.read(s)
    turns = src.conversations.get(conversation)
    if turns is None:
        raise BuildError(f"{conversation} is not in {src.location}")
    print(show(at(s, turns, turn), s["process"]["outlook"]["actions_shown"]))
    if with_context:
        print("\n" + context.show(context.at(s, conversation, turns, turn), turns, turn))

"""Absorb: where a case is likely to end, from each State and Action (plans/2026-10-06-process-abstraction.md, phase 3). No LLM.

Phase 2 gave every conversation how it ended (a kind of outcome and a rating). A conversation's last State is where it was absorbed into
that outcome, so each element of the graph can carry the odds of the outcomes the cases through it came to. Two estimates, each with its
support, and the evaluation (eval/process_absorb.py) says which to store:

  empirical  of the conversations that passed through the element, the share that ended well, and in each kind of outcome. It respects the
             history each case brought and is thin where an element is rare.
  chain      the absorbing Markov chain over the lifted transitions: an element's odds are its next elements' odds weighted by how often each
             follows it, and an ending is the outcomes of the cases that ended there. Solved by sparse sweeps (Gauss-Seidel; no matrix, so no
             size to fear). It carries odds along paths an element has never been seen on, and assumes the past does not matter.

Both can be pulled toward the global rate by `prior` pseudo-conversations, so a rare element is not its one case's outcome. Where support
(conversations through the element) is under `process.min_support` the element carries no odds and says so.

"Ended well" is the outcome rating at or above `good_rating`. Odds are stored **on the element**, as properties (decision 1: no Outcome label):
`support`, `end_well`, `likely_outcomes` and `likely_odds` (parallel lists of the kinds' names and their odds). Each node's values come from the
chain at its own level: the first level's for States and for Actions that no level groups, a level's own for the Actions it made. A rebuild
of the first level or of the levels deletes these properties with the nodes, so this stage follows them.

Everything here is counts, so a leave-one-conversation-out estimate is cheap: remove the conversation's contribution (`Counts.add(path, -1)`),
read the estimates, put it back.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.process.build import LABELS, BuildError


@dataclass
class Path:
    """One conversation as the chain sees it: the elements its transitions join, where it ended, and how."""

    conversation: str
    pairs: list[tuple[str, str]]  # consecutive turns of different kinds, as the graph's transitions are
    touched: frozenset[str]  # the elements it passed through (once each)
    last: str  # the element its last turn is in: where it was absorbed
    outcome: str  # the kind of outcome
    good: int  # 1 if it ended well


class Counts:
    """Everything the two estimates need, as counts that a conversation can be added to and taken from."""

    def __init__(self) -> None:
        self.n = 0
        self.good = 0
        self.kinds: Counter = Counter()
        self.through: dict[str, int] = defaultdict(int)
        self.through_good: dict[str, int] = defaultdict(int)
        self.through_kind: dict[str, Counter] = defaultdict(Counter)
        self.out: dict[str, Counter] = defaultdict(Counter)
        self.out_good: dict[str, Counter] = defaultdict(Counter)
        self.out_sum: dict[str, int] = defaultdict(int)
        self.fin: dict[str, int] = defaultdict(int)
        self.fin_good: dict[str, int] = defaultdict(int)
        self.fin_kind: dict[str, Counter] = defaultdict(Counter)

    def add(self, p: Path, sign: int = 1) -> None:
        self.n += sign
        self.good += sign * p.good
        self.kinds[p.outcome] += sign
        for e in p.touched:
            self.through[e] += sign
            self.through_good[e] += sign * p.good
            self.through_kind[e][p.outcome] += sign
        for a, b in p.pairs:
            self.out[a][b] += sign
            self.out_good[a][b] += sign * p.good
            self.out_sum[a] += sign
        self.fin[p.last] += sign
        self.fin_good[p.last] += sign * p.good
        self.fin_kind[p.last][p.outcome] += sign

    @property
    def base(self) -> float:
        return self.good / self.n if self.n else 0.0

    def elements(self) -> list[str]:
        """Every element the counts have ever seen, in a fixed order."""
        seen = set(self.through) | set(self.out) | set(self.fin)
        for row in self.out.values():
            seen |= set(row)
        return sorted(seen)


# ------------------------------------------------------------------------------------------------------------------ paths


def levels_of(G: Graph) -> tuple[dict[str, int], dict[str, str]]:
    """Each element's level and its parent (an element grouped by a level above has one `PART_OF` edge up)."""
    level = {
        r["id"]: r["level"]
        for r in G.rows("MATCH (n) WHERE n:State OR n:Action RETURN n.id AS id, n.level AS level")
    }
    parent = {r["a"]: r["b"] for r in G.rows("MATCH (a)-[:PART_OF]->(b) RETURN a.id AS a, b.id AS b")}
    return level, parent


def ancestor_at(element: str, level: int, levels: dict[str, int], parent: dict[str, str]) -> str:
    """The element that stands for `element` in the graph at `level`: its highest ancestor that is no higher than that."""
    while (up := parent.get(element)) is not None and levels[up] <= level:
        element = up
    return element


def paths(turns: list[dict], outcomes: dict[str, dict], of: Callable[[str], str] = lambda e: e) -> list[Path]:
    """One Path per conversation that has an outcome. `turns`: {conversation, seq, kind, element}; `of` maps a turn's first-level element to
    the element at the level being read."""
    by: dict[str, list[dict]] = defaultdict(list)
    for t in turns:
        by[t["conversation"]].append(t)
    out = []
    for c in sorted(by):
        o = outcomes.get(c)
        if o is None:
            continue
        ts = sorted(by[c], key=lambda t: t["seq"])
        els = [of(t["element"]) for t in ts]
        out.append(
            Path(
                conversation=c,
                pairs=[
                    (els[i], els[i + 1]) for i in range(len(ts) - 1) if ts[i]["kind"] != ts[i + 1]["kind"]
                ],
                touched=frozenset(els),
                last=els[-1],
                outcome=o["type"],
                good=o["good"],
            )
        )
    return out


def read_outcomes(s: Settings) -> tuple[dict[str, dict], list[dict]]:
    """{conversation: {type, rating, good}} from `qlsc process outcomes`, and the kinds' vocabulary. A conversation with no kind or rating is left out."""
    d = s.work / "process"
    path = d / "outcomes.ndjson"
    if not path.is_file():
        raise BuildError(f"{path} does not exist: run qlsc process outcomes first")
    good = s["process"]["absorb"]["good_rating"]
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    found = {
        r["conversation"]: {"type": r["type"], "rating": r["rating"], "good": int(r["rating"] >= good)}
        for r in rows
        if r.get("type") and r.get("rating")
    }
    return found, json.loads((d / "outcome_types.json").read_text())


# ---------------------------------------------------------------------------------------------------------------- estimates


def smoothed(k: float, n: float, base: float, prior: float) -> float:
    """k of n, pulled toward `base` by `prior` pseudo-conversations (the base itself where there is nothing)."""
    return (k + prior * base) / (n + prior) if n + prior > 0 else base


def empirical(c: Counts, e: str, prior: float) -> float:
    return smoothed(c.through_good.get(e, 0), c.through.get(e, 0), c.base, prior)


def solve(
    c: Counts,
    ending: Callable[[str], float],
    base: float,
    prior: float,
    tolerance: float,
    sweeps: int,
    start: dict[str, float] | None = None,
) -> dict[str, float]:
    """The absorbing probabilities: h(e) = [sum over y of out(e, y) * h(y) + fin(e) * ending(e)] / [out(e) + fin(e)], by Gauss-Seidel sweeps.
    `ending(e)` is the share of the cases that ended at `e` that were absorbed in the outcome (smoothed toward `base`). An element nothing
    leaves and nobody ended at is `base`. `start` warm-starts the sweeps (a leave-one-out solve begins from the full one)."""
    order = c.elements()
    h = dict(start) if start else {}
    for _ in range(sweeps):
        moved = 0.0
        for e in order:
            fin, left = c.fin.get(e, 0), c.out_sum.get(e, 0)
            if fin + left <= 0:
                v = base
            else:
                v = (
                    sum(n * h.get(y, base) for y, n in c.out[e].items() if n)
                    + fin * smoothed(ending(e), fin, base, prior)
                ) / (fin + left)
            moved = max(moved, abs(v - h.get(e, base)))
            h[e] = v
        if moved < tolerance:
            break
    return h


def chain(c: Counts, p: dict, start: dict[str, float] | None = None) -> dict[str, float]:
    """The chance each element's cases end well, from the chain."""
    return solve(c, lambda e: c.fin_good.get(e, 0), c.base, p["prior"], p["tolerance"], p["sweeps"], start)


def chain_kinds(c: Counts, p: dict) -> dict[str, dict[str, float]]:
    """The chance each element's cases end in each kind of outcome: {kind: {element: odds}}."""
    out = {}
    for k in sorted(c.kinds):
        if c.kinds[k] <= 0:
            continue
        out[k] = solve(
            c,
            lambda e, k=k: c.fin_kind[e][k] if e in c.fin_kind else 0,
            c.kinds[k] / c.n,
            p["prior"],
            p["tolerance"],
            p["sweeps"],
        )
    return out


def likely(
    c: Counts, estimator: str, kind_odds: dict[str, dict[str, float]], e: str, shown: int
) -> list[tuple[str, float]]:
    """An element's likeliest kinds of outcome with their odds, most likely first."""
    if estimator == "chain":
        odds = {k: v.get(e, 0.0) for k, v in kind_odds.items()}
    else:
        n = c.through.get(e, 0)
        odds = {k: v / n for k, v in c.through_kind[e].items() if v > 0} if n else {}
    return sorted(odds.items(), key=lambda kv: (-kv[1], kv[0]))[:shown]


# --------------------------------------------------------------------------------------------------------------------- write


def run(s: Settings, estimator: str | None = None) -> dict:
    """Estimate every element's odds at every level and store them on the elements. -> what was written, and how long it took."""
    p = s["process"]["absorb"]
    est = estimator or p["estimator"]
    if est not in ("empirical", "chain"):
        raise BuildError(f"process.absorb.estimator must be empirical or chain, not {est!r}")
    floor = s["process"]["min_support"]
    t0 = time.perf_counter()
    found, vocabulary = read_outcomes(s)
    names = {t["id"]: t["name"] for t in vocabulary}
    obs = s.work / "process" / "observations.ndjson"
    if not obs.is_file():
        raise BuildError(f"{obs} does not exist: run qlsc process build first")
    turns = [json.loads(line) for line in obs.read_text().splitlines() if line.strip()]
    written: dict[int, dict] = {}
    with Graph(s, {"database": s["process"]["database"]}) as G:
        levels, parent = levels_of(G)
        if not levels:
            raise BuildError("the process database holds no elements: run qlsc process build first")
        G.run(
            """MATCH (n) WHERE n:State OR n:Action
               REMOVE n.support, n.support_good, n.end_well, n.likely_outcomes, n.likely_odds, n.outcome_kinds, n.outcome_counts"""
        )
        G.run("MATCH ()-[x:SELECTS|LEADS_TO]->() REMOVE x.num_good")
        for level in sorted(set(levels.values())):
            ps = paths(turns, found, lambda e, level=level: ancestor_at(e, level, levels, parent))
            c = Counts()
            for x in ps:
                c.add(x)
            full = chain(c, p) if est == "chain" else {}
            kinds = chain_kinds(c, p) if est == "chain" else {}
            rows = []
            for e in c.elements():
                if levels.get(e) != level:
                    continue  # a node takes its values from the chain at its own level
                n = c.through.get(e, 0)
                seen = sorted((names.get(k, k), v) for k, v in c.through_kind[e].items() if v > 0)
                raw = {
                    "id": e,
                    "support": n,
                    "good": c.through_good.get(e, 0),
                    "seen": [k for k, _ in seen],
                    "seen_counts": [v for _, v in seen],
                }
                if n < floor:
                    rows.append({**raw, "end_well": None, "kinds": [], "odds": []})
                    continue
                top = likely(c, est, kinds, e, p["outcomes_shown"])
                rows.append(
                    {
                        **raw,
                        "end_well": round(full[e] if est == "chain" else empirical(c, e, p["prior"]), 4),
                        "kinds": [names.get(k, k) for k, _ in top],
                        "odds": [round(v, 4) for _, v in top],
                    }
                )
            for label in LABELS.values():
                G.batch(
                    f"absorb {label} L{level}",
                    f"""UNWIND $rows AS r MATCH (n:{label} {{id: r.id}})
                        SET n.support = r.support, n.support_good = r.good, n.end_well = r.end_well, n.likely_outcomes = r.kinds,
                            n.likely_odds = r.odds, n.outcome_kinds = r.seen, n.outcome_counts = r.seen_counts""",
                    rows,
                    size=1000,
                )
            pairs = [
                {"a": a, "b": b, "num": n, "good": c.out_good[a][b], "level": level}
                for a in sorted(c.out)
                for b, n in sorted(c.out[a].items())
                if n > 0
            ]
            for rel, (src, dst) in (("SELECTS", ("State", "Action")), ("LEADS_TO", ("Action", "State"))):
                G.batch(
                    f"absorb {rel} L{level}",
                    f"""UNWIND $rows AS r MATCH (a:{src} {{id: r.a}})-[x:{rel}]->(b:{dst} {{id: r.b}}) WHERE x.level = r.level
                        SET x.num_good = r.good""",
                    [r_ for r_ in pairs if r_["a"].startswith(src.lower() + ":")],
                    size=2000,
                )
            written[level] = {
                "conversations": c.n,
                "elements": len(rows),
                "with_odds": sum(1 for r in rows if r["end_well"] is not None),
                "end_well_rate": round(c.base, 4),
            }
        with_odds = G.value(
            "MATCH (n) WHERE (n:State OR n:Action) AND n.end_well IS NOT NULL RETURN count(n)"
        )
        elements = G.value("MATCH (n) WHERE (n:State OR n:Action) RETURN count(n)")
        recorded = G.value("MATCH (n) WHERE (n:State OR n:Action) AND n.support IS NOT NULL RETURN count(n)")
    if recorded != elements:
        raise BuildError(f"{elements - recorded} elements were left without a support count")
    if with_odds != sum(v["with_odds"] for v in written.values()):
        raise BuildError("the process database does not hold the odds that were written")
    return {
        "estimator": est,
        "min_support": floor,
        "levels": written,
        "elements": elements,
        "with_odds": with_odds,
        "seconds": round(time.perf_counter() - t0, 1),
    }


def report(s: Settings) -> None:
    m = run(s)
    print(
        f"{m['with_odds']:,} of {m['elements']:,} elements carry odds ({m['estimator']}; at least {m['min_support']} conversations through each); "
        f"{m['elements'] - m['with_odds']:,} are too thin and say so"
    )
    for level, v in m["levels"].items():
        print(
            f"  level {level}: {v['with_odds']:,} of {v['elements']:,} elements; {v['conversations']:,} conversations, {v['end_well_rate']:.1%} ended well"
        )
    print(f"  {m['seconds']} s")

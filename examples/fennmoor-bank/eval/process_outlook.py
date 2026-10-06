"""Process abstraction, phase 4 (plans/2026-10-06-process-abstraction.md): does locating a case by nearness help, and does ranking the reps' next
Actions by how those cases ended recommend what works?

`qlsc process outlook` finds a live case's nearest States by the vector index, pools their counts weighted by nearness, and lists the Actions reps
took next with how those cases ended. This runs that same code (`outlook.pool`, over counts) at every customer turn of the conversations scored, with
the conversation taken out of the counts first, and asks the answer key (which the tool never reads):

  nearness     the odds of ending well at checkpoints in a conversation's life (as phase 3): the State the build assigned (the empirical odds) against the
               nearest State by the index alone, and against the pool of the nearest several. Coverage, and Brier against the planted favourability.
  validity     at each customer turn followed by a rep's Action, the Action the graph recommends (the supported one whose cases ended best, or the one reps
               took most often) is classed against the world: a remedy that FIXES the real cause, or only partly, or nothing, or makes it worse (the
               efficacy table); a question that asks for a clue that is TRUE and not yet said; a verification; a hand-off; something else. Against what
               the rep actually did, the single best action with hindsight, and chance among the procedure's actions. Split by whether a true clue is still
               waiting to be asked (a question is useful) or not (only the fix is).
  confounding  the same by the rep's archetype and the customer's: does the graph recommend what rushed reps do, or what works?
  cost         seconds, LLM calls and texts embedded for a live outlook.
  --grid       on the TUNING conversations (the first 600 by id). The rules, set before looking: (states, temperature): the lowest pooled Brier;
               (level, prior): the most recommendations that are useful (a fix, or a question for a true unsaid clue) out of all decision points.

Writes results/process_outlook.md and .json (or process_outlook_grid.md). Usage: uv run examples/fennmoor-bank/eval/process_outlook.py [--grid]
"""

from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter, defaultdict
from statistics import median

import process_absorb as pa
import process_graph as pg
from common import settings, write_result

from qlsc.graph import Graph
from qlsc.llm import Embedder
from qlsc.process import absorb, build, outlook, source

KMAX = 20
FIXES, PARTIAL, NOTHING, WORSE = "fixes the cause", "partly fixes it", "does nothing for it", "makes it worse"
QTRUE, QOTHER, VERIFY, HANDOFF, OTHER = (
    "asks for a true, unsaid clue",
    "asks for nothing new",
    "verifies identity",
    "hands off",
    "other",
)
USEFUL = {FIXES, QTRUE}
EFFECT = {"fixes": FIXES, "partial": PARTIAL, "no-effect": NOTHING, "makes-worse": WORSE}
CLASSES = [FIXES, QTRUE, PARTIAL, NOTHING, WORSE, QOTHER, VERIFY, HANDOFF, OTHER]


# ------------------------------------------------------------------------------------------------------------------------- data


class Data:
    """Everything the scoring reads: the turns, the answer key, the outcomes, and where each customer turn is located."""

    def __init__(self, s) -> None:
        self.s = s
        self.obs = [
            json.loads(line) for line in (s.work / "process" / "observations.ndjson").read_text().splitlines()
        ]
        self.planted = pg.Planted(self.obs)
        self.world = self.planted.world
        self.ids = sorted({r["conversation"] for r in self.obs})
        self.tuning, self.holdout = set(self.ids[: pg.TUNING]), set(self.ids[pg.TUNING :])
        self.found = absorb.read_outcomes(s)[0]
        by = defaultdict(list)
        for r in self.obs:
            by[r["conversation"]].append(r)
        self.turns = {c: sorted(v, key=lambda r: r["seq"]) for c, v in by.items()}
        with Graph(s, {"database": s["process"]["database"]}) as G:
            self.levels, self.parent = absorb.levels_of(G)
            self.names = {
                r["id"]: r["name"] for r in G.rows("MATCH (n:Action) RETURN n.id AS id, n.name AS name")
            }
            self.located = self.locate(G)
        self.truth = {c: self.planted.truth[c] for c in self.ids if c in self.planted.truth}

    def locate(self, G: Graph) -> dict[str, list[tuple[str, float]]]:
        """Every State turn's nearest States by the vector index, from its annotation embedded as the build did: {event: [(id, cosine)]}."""
        rows = [r for r in build.load(self.s) if r["kind"] == "state"]
        emb = Embedder(self.s)
        texts = [build.text_to_embed(self.s, r) for r in rows]
        vecs = [build.unit(v) for v in emb.embed(texts)]
        out: dict[str, list[tuple[str, float]]] = {}
        for i in range(0, len(rows), 200):
            got = G.rows(
                """UNWIND $rows AS r CALL db.index.vector.queryNodes($index, $k, r.vec) YIELD node, score
                   RETURN r.event AS event, node.id AS id, score ORDER BY event, score DESC, id""",
                rows=[
                    {"event": r["event"], "vec": v}
                    for r, v in zip(rows[i : i + 200], vecs[i : i + 200], strict=True)
                ],
                index=build.INDEX["state"],
                k=KMAX,
            )
            for g in got:
                out.setdefault(g["event"], []).append((g["id"], 2 * g["score"] - 1))
        return out

    def counts(self, level: int) -> tuple[absorb.Counts, dict[str, absorb.Path], dict[str, str]]:
        """The counts at an Action level, each conversation's path, and each turn's element at that level (to name an Action by what it is)."""
        of = lambda e: absorb.ancestor_at(e, level, self.levels, self.parent)  # noqa: E731
        ps = absorb.paths(self.obs, self.found, of)
        c = absorb.Counts()
        for x in ps:
            c.add(x)
        return c, {x.conversation: x for x in ps}, {r["event"]: of(r["element"]) for r in self.obs}

    def checkpoints(self, c: str) -> list[tuple[str, str]]:
        """(label, event) of the customer turns scored in the life of a conversation: its 1st, 2nd, 3rd, 4th and 6th, and its last."""
        states = [r["event"] for r in self.turns[c] if r["kind"] == "state"]
        picks = [(pa.label(k), states[k - 1]) for k in pa.CHECKPOINTS if k <= len(states)]
        return picks + ([(pa.LAST, states[-1])] if states else [])

    def points(self, c: str) -> list[tuple[str, str]]:
        """(State event, the Action event that followed): the decision points of a conversation."""
        t = self.turns[c]
        return [
            (a["event"], b["event"])
            for a, b in zip(t, t[1:], strict=False)
            if a["kind"] == "state" and b["kind"] == "action"
        ]


# -------------------------------------------------------------------------------------------------------------------- nearness


def end_well_rows(d: Data, convs: set[str], p: dict, absorb_p: dict, floor: int) -> list[dict]:
    """Leave-one-conversation-out predictions at the checkpoints, by three arms: the State the build assigned, the nearest State by the index alone,
    and the pool of the nearest `p['states']` weighted by nearness. -> rows {conversation, checkpoint, arm, p, planted, covered}"""
    counts, by, _ = d.counts(1)
    rows = []
    for c in sorted(convs):
        x = by.get(c)
        if x is None or c not in d.truth:
            continue
        counts.add(x, -1)
        base_all, base_states = counts.base, outlook.base_of(counts)
        planted = int(d.truth[c]["favorability"] == "high")
        element = {r["event"]: r["element"] for r in d.turns[c]}
        for label, event in d.checkpoints(c):
            loc = d.located.get(event)
            if not loc:
                continue
            e = element[event]
            n = counts.through.get(e, 0)
            near1 = outlook.pool(
                outlook.stats_from_counts(counts, [loc[0][0]], base=base_states),
                loc[:1],
                {**p, "states": 1, "temperature": 0},
                floor,
                absorb_p["prior"],
            )
            pooled = outlook.pool(
                outlook.stats_from_counts(counts, [i for i, _ in loc[: p["states"]]], base=base_states),
                loc,
                p,
                floor,
                absorb_p["prior"],
            )
            for arm, pred, covered in (
                ("global rate", base_all, True),
                (
                    "the State the build assigned",
                    absorb.empirical(counts, e, absorb_p["prior"]) if n >= floor else base_all,
                    n >= floor,
                ),
                (
                    "the nearest State by the index",
                    near1["end_well"] if near1["end_well"] is not None else base_all,
                    near1["end_well"] is not None,
                ),
                (
                    "the pool of the nearest States",
                    pooled["end_well"] if pooled["end_well"] is not None else base_all,
                    pooled["end_well"] is not None,
                ),
            ):
                rows.append(
                    {
                        "conversation": c,
                        "group": 0,
                        "checkpoint": label,
                        "arm": arm,
                        "p": pred,
                        "planted": planted,
                        "favourability": d.truth[c]["favorability"],
                        "text": x.good,
                        "covered": covered,
                    }
                )
        counts.add(x, 1)
    return rows


# -------------------------------------------------------------------------------------------------------------------- validity


def classify(w, truth: dict, action: str | None, unbrought: set[str]) -> str:
    """What an action is, at a point in a conversation whose real cause and unsaid clues are known."""
    a = w.actions.get(action or "")
    if a is None:
        return OTHER
    if a.get("elicits"):
        return QTRUE if a["elicits"] in unbrought else QOTHER
    if a.get("elicits_any") is not None:
        return QTRUE if unbrought else QOTHER
    if a["type"] == "verify":
        return VERIFY
    if a["type"] in ("transfer", "escalate"):
        return HANDOFF
    if a.get("commits") or a.get("resolving"):
        return EFFECT[w.effect(action, truth["cause"])]
    return OTHER


def validity_points(d: Data, convs: set[str], level: int, p: dict, absorb_p: dict, floor: int) -> list[dict]:
    """At every decision point of the conversations scored (leave-one-conversation-out): what the graph recommends, what reps most often did, what
    the rep did, each classed; and what chance and the best fixed action would have done."""
    counts, by, of = d.counts(level)
    names = pg.element_labels(
        d.planted, [r for r in d.obs], of
    )  # an Action element's planted action: the majority of its turns'
    out = []
    for c in sorted(convs):
        x = by.get(c)
        if x is None or c not in d.truth:
            continue
        truth, plan = d.truth[c], d.planted.plans[c]
        avail = d.world.procedure_actions(plan["procedure"])
        counts.add(x, -1)
        base_states = outlook.base_of(counts)
        for state_event, action_event in d.points(c):
            loc = d.located.get(state_event)
            if not loc or state_event not in d.planted.unbrought:
                continue
            unbrought = d.planted.unbrought[state_event]
            ids = [i for i, _ in loc[: p["states"]]]
            o = outlook.pool(
                outlook.stats_from_counts(counts, ids, base=base_states),
                loc,
                p,
                floor,
                absorb_p["prior"],
            )
            label = lambda a: names.get(a["action"]) if a else None  # noqa: E731
            rec, common = label(o["recommended"]), label(o["most_common"])
            actual = d.planted.action.get(action_event)
            out.append(
                {
                    "conversation": c,
                    "pending": "a clue is waiting" if unbrought else "no clue waiting",
                    "rep": truth["rep"],
                    "customer": truth["customer"],
                    "ended_well": int(truth["favorability"] == "high"),
                    "recommended": rec,
                    "common": common,
                    "actual": actual,
                    "class": {
                        "the graph: best ending after": classify(d.world, truth, rec, unbrought)
                        if rec
                        else None,
                        "the graph: what reps most often did": classify(d.world, truth, common, unbrought)
                        if common
                        else None,
                        "the rep": classify(d.world, truth, actual, unbrought),
                    },
                    "avail_classes": [classify(d.world, truth, a, unbrought) for a in avail],
                    "avail": avail,
                    "useful_actions": [a for a in avail if classify(d.world, truth, a, unbrought) in USEFUL],
                }
            )
        counts.add(x, 1)
    return out


def hindsight(points: list[dict]) -> tuple[str | None, float]:
    """The one action that would have been useful at the most points, picked with hindsight: (action, its share of the points)."""
    tally = Counter(a for x in points for a in x["useful_actions"])
    if not tally:
        return None, 0.0
    best = min(tally, key=lambda a: (-tally[a], a))
    return best, tally[best] / len(points)


def share(
    points: list[dict], arm: str, classes: set[str] | None = None, covered: bool = False
) -> tuple[int, int]:
    pts = [x for x in points if x["class"].get(arm) is not None] if covered else points
    return sum(1 for x in pts if x["class"].get(arm) in (classes or USEFUL)), len(pts)


def pct(k_n: tuple[int, int]) -> str:
    k, n = k_n
    if not n:
        return "-"
    lo, hi = pg.wilson(k, n)
    return f"{k / n:.0%} [{lo:.0%}, {hi:.0%}]"


ARMS = ("the graph: best ending after", "the graph: what reps most often did", "the rep")


def validity_tables(points: list[dict]) -> tuple[list[str], dict]:
    """The headline table, by whether a clue is waiting, and a breakdown of what each arm does."""
    stages = [
        ("all decision points", points),
        *[(n, [x for x in points if x["pending"] == n]) for n in ("a clue is waiting", "no clue waiting")],
    ]
    covered = [x for x in points if x["class"]["the graph: best ending after"] is not None]
    md = [
        "| | " + " | ".join(f"{name} (n={len(pts)})" for name, pts in stages) + " |",
        "|---|" + "---|" * len(stages),
    ]
    record: dict = {}
    for arm in ARMS[:1]:
        md.append(f"| **{arm}**: useful | " + " | ".join(pct(share(pts, arm)) for _, pts in stages) + " |")
    md.append(
        "| the graph: has a recommendation (supported) | "
        + " | ".join(
            pct((sum(1 for x in pts if x["class"][ARMS[0]] is not None), len(pts))) for _, pts in stages
        )
        + " |"
    )
    for arm in ARMS[1:]:
        md.append(f"| {arm}: useful | " + " | ".join(pct(share(pts, arm)) for _, pts in stages) + " |")
    md.append(
        "| chance, among the procedure's actions | "
        + " | ".join(
            f"{sum(sum(1 for c in x['avail_classes'] if c in USEFUL) / len(x['avail_classes']) for x in pts) / len(pts):.0%}"
            if pts
            else "-"
            for _, pts in stages
        )
        + " |"
    )
    hs = [hindsight(pts) for _, pts in stages]
    md.append(
        "| the best single action, with hindsight | "
        + " | ".join(f"{h[1]:.0%} ({h[0].replace('ACT-', '') if h[0] else '-'})" for h in hs)
        + " |"
    )
    md.append(
        "| some useful action existed in the procedure | "
        + " | ".join(
            f"{sum(1 for x in pts if x['useful_actions']) / len(pts):.0%}" if pts else "-"
            for _, pts in stages
        )
        + " |"
    )
    md += [
        "",
        "Where the graph had a recommendation, the same points, the rep against the graph (useful):",
        "",
        "| | "
        + " | ".join(
            f"{n} (n={len([x for x in pts if x['class'][ARMS[0]] is not None])})" for n, pts in stages
        )
        + " |",
        "|---|" + "---|" * len(stages),
    ]
    for arm in ARMS:
        md.append(
            f"| {arm} | "
            + " | ".join(
                pct(share([x for x in pts if x["class"][ARMS[0]] is not None], arm)) for _, pts in stages
            )
            + " |"
        )
    record["points"] = len(points)
    record["covered"] = len(covered)
    # what each arm recommends, by class
    md += [
        "",
        "What each arm's action is, at all decision points where the graph had a recommendation:",
        "",
        "| class | " + " | ".join(ARMS) + " |",
        "|---|" + "---|" * len(ARMS),
    ]
    for cls in CLASSES:
        md.append(
            f"| {cls} | "
            + " | ".join(
                f"{sum(1 for x in covered if x['class'][arm] == cls) / max(1, len(covered)):.0%}"
                for arm in ARMS
            )
            + " |"
        )
    agree = {
        "graph = rep": sum(1 for x in covered if x["recommended"] == x["actual"]) / max(1, len(covered)),
        "graph = what reps most often did": sum(1 for x in covered if x["recommended"] == x["common"])
        / max(1, len(covered)),
        "rep = what reps most often did": sum(1 for x in covered if x["actual"] == x["common"])
        / max(1, len(covered)),
    }
    md += ["", "Agreement: " + "; ".join(f"{k} {v:.0%}" for k, v in agree.items()) + "."]
    record["agree"] = agree
    took = [x for x in covered if x["recommended"] == x["actual"]]
    did_not = [x for x in covered if x["recommended"] != x["actual"]]
    md += [
        "",
        "Where reps took the Action the graph recommends and where they did not, how the conversations ended (planted favourability high; observational: "
        "reps who differ from the graph may be in harder cases, and the points of one conversation are not independent):",
        "",
        "| the rep | points | ended well |",
        "|---|---|---|",
        f"| took the graph's recommendation | {len(took)} | {pct((sum(x['ended_well'] for x in took), len(took)))} |",
        f"| took something else | {len(did_not)} | {pct((sum(x['ended_well'] for x in did_not), len(did_not)))} |",
    ]
    record["took"] = [
        sum(x["ended_well"] for x in took),
        len(took),
        sum(x["ended_well"] for x in did_not),
        len(did_not),
    ]
    return md, record


def confounding(points: list[dict], key: str, names: dict[str, str]) -> list[str]:
    groups = sorted({x[key] for x in points})
    md = [
        "| "
        + key
        + " | points | the graph (useful) | what reps most often did | the rep | graph = most-common |",
        "|---|---|---|---|---|---|---|",
    ]
    for g in groups:
        pts = [x for x in points if x[key] == g]
        cov = [x for x in pts if x["class"][ARMS[0]] is not None]
        md.append(
            f"| {names.get(g, g)} | {len(pts)} | {pct(share(cov, ARMS[0]))} | {pct(share(cov, ARMS[1]))} | {pct(share(cov, ARMS[2]))} | {sum(1 for x in cov if x['recommended'] == x['common']) / max(1, len(cov)):.0%} |"
        )
    return md


# -------------------------------------------------------------------------------------------------------------------------- cost


def cost(s, d: Data, n: int = 30) -> dict:
    """Seconds, calls and embeddings for a live outlook, over a sample of conversations at a random turn (the annotation is cached: the build saw it)."""
    src = source.read(s)
    rng = random.Random(7)
    sample = rng.sample(sorted(d.holdout), n)
    seconds, calls, cached = [], 0, 0
    with Graph(s, {"database": s["process"]["database"]}) as G:
        for c in sample:
            turns = src.conversations[c]
            customers = [t for t in turns if t.kind == "state"]
            t = customers[rng.randrange(len(customers))]
            o = outlook.at(s, turns, t.seq, G)
            seconds.append(o["measured"]["seconds"])
            calls, cached = calls + o["measured"]["llm_calls"], cached + o["measured"]["llm_cached"]
    manifest = json.loads((s.work / "process" / "annotations-turn.json").read_text())
    per_call = manifest["api_seconds"] / max(1, manifest["calls"])
    return {
        "n": n,
        "median": median(seconds),
        "max": max(seconds),
        "calls": calls,
        "cached": cached,
        "annotation_call_seconds": per_call,
        "annotation_calls_cost": manifest["cost"] / max(1, manifest["calls"]),
    }


# --------------------------------------------------------------------------------------------------------------------------- main


def main() -> None:
    s = settings()
    if "--grid" in sys.argv:
        return grid(s)
    d = Data(s)
    p, ap, floor = s["process"]["outlook"], s["process"]["absorb"], s["process"]["min_support"]
    md = [
        "# Process abstraction, phase 4: the outlook",
        "",
        f"The {p['states']} nearest States by the vector index, weighted by exp(-distance / {p['temperature']}); Actions read at level {p['level']}, pulled toward their own rate by {p['prior']:g} pseudo-transitions; "
        f"a pool under {floor} conversations carries no odds. Every number takes the conversation scored out of the counts first. Holdout: the {len(d.holdout)} conversations after the first {pg.TUNING} by id.",
        "",
    ]
    record: dict = {}
    t0 = time.time()
    rows = end_well_rows(d, d.holdout, p, ap, floor)
    arms = (
        "global rate",
        "the State the build assigned",
        "the nearest State by the index",
        "the pool of the nearest States",
    )
    tbl, data = pa.table(rows, arms)
    md += [
        "## Nearness: Brier score for the odds of ending well, at checkpoints (planted favourability; the difference from the global rate, 95%)",
        "",
        *tbl,
        "",
    ]
    md += ["Coverage: " + ", ".join(f"{a} **{pa.coverage(rows, a):.0%}**" for a in arms[1:]) + "."]
    record["nearness"] = {
        "brier": {f"{a}|{g}": v for (a, g), v in data.items()},
        "coverage": {a: pa.coverage(rows, a) for a in arms},
    }
    for a, b in (
        ("the pool of the nearest States", "the State the build assigned"),
        ("the pool of the nearest States", "global rate"),
    ):
        dd, se = pa.paired(rows, a, b)
        md.append(f"Paired, {a} minus {b}: **{dd:+.4f} ± {1.96 * se:.4f}**.")
    md.append("")
    pts = validity_points(d, d.holdout, p["level"], p, ap, floor)
    vt, vr = validity_tables(pts)
    md += [
        "## Validity: is the Action the graph recommends one that works? (holdout)",
        "",
        "Useful: a remedy that fixes the real cause, or a question for a clue that is true and not yet said.",
        "",
        *vt,
        "",
    ]
    record["validity"] = vr
    md += [
        "## Confounding: by the rep's archetype",
        "",
        *confounding(pts, "rep", {k: v["label"] for k, v in d.world.rep_archetypes.items()}),
        "",
        "## by the customer's archetype",
        "",
        *confounding(pts, "customer", {k: v["label"] for k, v in d.world.customer_archetypes.items()}),
        "",
    ]
    c = cost(s, d)
    md += [
        "## Cost of a live outlook",
        "",
        f"{c['n']} outlooks at random turns of holdout conversations: median **{c['median']:.1f} s**, at most {c['max']:.1f} s, with the turn's annotation answered from the cache ({c['calls']} calls, {c['cached']} cached). "
        f"A turn the build had not seen costs one Haiku call: about {c['annotation_call_seconds']:.1f} s and ${c['annotation_calls_cost']:.4f}, from the build's own record. The service ceiling is {s['service']['targets']['seconds']} s and {s['service']['targets']['tokens']:,} tokens.",
        "",
        f"{time.time() - t0:.0f} seconds for the scoring.",
    ]
    record["cost"] = c
    print(write_result("process_outlook", md, record))
    print("\n".join(md))


def grid(s) -> None:
    d = Data(s)
    ap, floor, p0 = s["process"]["absorb"], s["process"]["min_support"], s["process"]["outlook"]
    md = ["# Process abstraction, phase 4: the grid on the tuning conversations", ""]
    md += [
        "## (states, temperature): Brier for the odds of ending well, pooled, at checkpoints",
        "",
        "| states | " + " | ".join(f"temperature {t:g}" for t in (0.0, 0.02, 0.05, 0.1, 0.3, 1.0)) + " |",
        "|---|---|---|---|---|---|",
    ]
    res = {}
    for k in (1, 3, 5, 10, 20):
        cells = []
        for t in (0.0, 0.02, 0.05, 0.1, 0.3, 1.0):
            rows = end_well_rows(d, d.tuning, {**p0, "states": k, "temperature": t}, ap, floor)
            sub = [r for r in rows if r["arm"] == "the pool of the nearest States"]
            res[(k, t)] = pa.brier(sub)
            cells.append(f"{res[(k, t)]:.4f}")
            print(k, t, res[(k, t)], flush=True)
        md.append(f"| {k} | " + " | ".join(cells) + " |")
    rows = end_well_rows(d, d.tuning, {**p0, "states": 1, "temperature": 0}, ap, floor)
    glob = pa.brier([r for r in rows if r["arm"] == "global rate"])
    assigned = pa.brier([r for r in rows if r["arm"] == "the State the build assigned"])
    best = min(res, key=lambda kt: (res[kt], kt))
    md += [
        "",
        f"The global rate scores {glob:.4f} and the State the build assigned {assigned:.4f}. Best: **{best[0]} States at temperature {best[1]:g}** ({res[best]:.4f}).",
        "",
    ]
    p1 = {**p0, "states": best[0], "temperature": best[1]}
    md += [
        "## (level, prior): the share of all decision points where the recommendation is useful",
        "",
        "| level | " + " | ".join(f"prior {x:g}" for x in (1.0, 5.0, 20.0, 50.0, 200.0)) + " |",
        "|---|---|---|---|---|---|",
    ]
    res2 = {}
    for level in (1, 2):
        cells = []
        for pr in (1.0, 5.0, 20.0, 50.0, 200.0):
            pts = validity_points(d, d.tuning, level, {**p1, "level": level, "prior": pr}, ap, floor)
            k, n = share(pts, "the graph: best ending after")
            cov = sum(1 for x in pts if x["class"]["the graph: best ending after"] is not None)
            res2[(level, pr)] = k / n
            cells.append(f"{k / n:.1%} (covered {cov / n:.0%})")
            print(level, pr, k / n, flush=True)
        md.append(f"| {level} | " + " | ".join(cells) + " |")
    best2 = max(res2, key=lambda lp: (res2[lp], -lp[0], -lp[1]))
    md += [
        "",
        f"Best: **level {best2[0]}, prior {best2[1]:g}** ({res2[best2]:.1%}).",
        "",
        "## The settings the rules choose",
        "",
        f"`process.outlook.states: {best[0]}`, `temperature: {best[1]:g}`, `level: {best2[0]}`, `prior: {best2[1]:g}`.",
    ]
    record = {
        "states": best[0],
        "temperature": best[1],
        "level": best2[0],
        "prior": best2[1],
        "brier": {f"{k}|{t}": v for (k, t), v in res.items()},
        "useful": {f"{lv}|{pr}": v for (lv, pr), v in res2.items()},
    }
    print(write_result("process_outlook_grid", md, record))
    print("\n".join(md))


if __name__ == "__main__":
    main()

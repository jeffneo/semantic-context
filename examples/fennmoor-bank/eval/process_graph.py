"""Process graph, phase 3 (plans/2026-10-05-text-graph-construction.md): is the State-Action graph the corpus's planted process?

Scores the graph `qlsc process build` wrote against the corpus's answer key (which the tool never reads; this evaluation may), the
same way for three arms, so only the grouping differs:
  graph   the States and Actions the build made, from LLM-annotated turns
  raw     the same embedder and grouping over the raw turn text, no annotation: what the LLM annotation buys
  oracle  the planted labels as the elements: the most a graph over these conversations could show

  abstraction   homogeneity, completeness and V-measure of the elements against the planted labels: an Action against the planted
                action; a State against the planted State key, (stage, the clues established so far, whether the caller is verified),
                and against its coarse form (the problem's domain, stage, verified). Stage purity, and singleton shares.
  fidelity      the discovered transition probabilities against the planted ones, by label (Pearson, Spearman, MAE), and a recount of
                the stored `num` from the turns.
  diagnostic    leave-one-conversation-out, at each customer turn where a discriminating clue is true, perceived, not yet brought up and
                has a question that elicits it: does the graph's most likely next Action ask it? Against what the rep actually did, the
                best fixed question (chosen with hindsight), the most frequent next action, and chance. Wilson 95% intervals. The
                grouping saw the conversation; the counts it recommends from do not (its own transitions are taken out).
  breach        whether a conversation that was served without verifying an unauthenticated caller can be found from its path.

  --grid        grouping only (no naming): similarity x resolution x State text, scored the same way, for tuning.

Writes results/process_graph.md and .json (or process_graph_grid.md). Usage: uv run examples/fennmoor-bank/eval/process_graph.py [--grid]
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter, defaultdict
from itertools import product
from math import log, sqrt

from common import BUILD, EXAMPLE, settings, write_result

sys.path.insert(0, str(EXAMPLE / "generate"))

from corpus_world import load_world  # noqa: E402

from qlsc.graph import Graph  # noqa: E402
from qlsc.llm import Embedder  # noqa: E402
from qlsc.process import build  # noqa: E402

TUNING = 600  # the conversations the parameters were chosen on: the first 100 by id (phase 3), then 100 to 600 (phase 4)
MIN_SUPPORT = 3  # planted transitions seen fewer times than this are not compared
IDENTITY_POLICIES = ("POL-AUTH-BEFORE-DETAIL", "POL-FRAUD-STEPUP-VERIFY")


# ------------------------------------------------------------------------------------------------------------- statistics


def entropy(counts) -> float:
    n = sum(counts)
    return -sum(c / n * log(c / n) for c in counts if c) if n else 0.0


def v_measure(classes: dict[str, str], clusters: dict[str, str]) -> tuple[float, float, float]:
    """Homogeneity, completeness, V over the events both name: each cluster of one class; each class in one cluster."""
    keys = [k for k in classes if k in clusters]
    n = len(keys)
    joint = Counter((classes[k], clusters[k]) for k in keys)
    by_class, by_cluster = Counter(classes[k] for k in keys), Counter(clusters[k] for k in keys)
    h_c, h_k = entropy(by_class.values()), entropy(by_cluster.values())
    h_c_given_k = -sum(c / n * log(c / by_cluster[k]) for (_, k), c in joint.items())
    h_k_given_c = -sum(c / n * log(c / by_class[cl]) for (cl, _), c in joint.items())
    hom = 1.0 if h_c == 0 else 1 - h_c_given_k / h_c
    comp = 1.0 if h_k == 0 else 1 - h_k_given_c / h_k
    return hom, comp, 0.0 if hom + comp == 0 else 2 * hom * comp / (hom + comp)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return centre - half, centre + half


def ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 3:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    return cov / sqrt(va * vb) if va and vb else float("nan")


def majority(labels: list[str]) -> str:
    return Counter(labels).most_common(1)[0][0]


# ------------------------------------------------------------------------------------------------------------- the planted


class Planted:
    """What the answer key says about each turn of the scored conversations."""

    def __init__(self, rows: list[dict]):
        self.world = load_world()
        convs = {r["conversation"] for r in rows}
        self.plans, self.truth = {}, {}
        with gzip.open(BUILD / "corpus" / "plans.ndjson.gz", "rt") as f:
            for line in f:
                p = json.loads(line)
                if p["conversation_id"] in convs:
                    self.plans[p["conversation_id"]] = p
        self.event: dict[str, dict] = {}
        with gzip.open(BUILD / "corpus" / "full" / "truth.ndjson.gz", "rt") as f:
            for line in f:
                t = json.loads(line)
                if t["conversation_id"] in convs:
                    self.truth[t["conversation_id"]] = t
                    for e in t["events"]:
                        self.event[e["event_id"]] = {**e, "conversation": t["conversation_id"]}
        self.identity = {a for k in IDENTITY_POLICIES for a in self.world.policies[k]["satisfied_by"]}
        self.action: dict[str, str] = {}
        self.state_fine: dict[str, str] = {}
        self.state_coarse: dict[str, str] = {}
        self.stage: dict[str, str] = {}
        self.unbrought: dict[
            str, set[str]
        ] = {}  # per customer turn: the discriminating clues true, perceived and not yet said
        for r in rows:
            e = self.event.get(r["event"])
            if e is None:
                continue
            if r["kind"] == "action":
                self.action[r["event"]] = e["action"] or e["role"]
            else:
                self.state(r["event"], e)

    def state(self, event: str, e: dict) -> None:
        plan = self.plans[e["conversation"]]
        steps, world, role, i = plan["steps"], plan["world"], e["role"], e["step"]
        if role == "cust_hangup":
            key = ("hangup",)
            self.state_fine[event], self.state_coarse[event], self.stage[event] = "hangup", "hangup", "hangup"
            self.unbrought[event] = set()
            return
        if role in (
            "cust_demand",
            "cust_pushback",
        ):  # said before the step's action: the case as the step before left it
            i = (i or 1) - 1
        upto = len(steps) - 1 if i is None else i
        stage = "close" if i is None else ("open" if i == 0 else steps[i].get("stage") or "open")
        said = set(world["volunteered"]) | {world["opener"]}
        for st in steps[1 : upto + 1]:
            said |= set(st.get("reveals") or [])
        verified = plan["authenticated"] or any(
            st.get("action") in self.identity for st in steps[1 : upto + 1]
        )
        key = (stage, tuple(sorted(said)), verified)
        self.state_fine[event] = repr(key)
        self.state_coarse[event] = repr((plan["domain"], stage, verified))
        self.stage[event] = stage
        discriminating = {
            m
            for m in world["present"]
            if m in world["perceived"] and self.world.manifestations[m].get("discriminating")
        }
        self.unbrought[event] = discriminating - said


# ------------------------------------------------------------------------------------------------------------------ arms


def sequences(rows: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["conversation"]].append(r)
    for turns in by.values():
        turns.sort(key=lambda r: r["seq"])
    return by


def pairs_of(rows: list[dict], element_of: dict[str, str]) -> dict[str, list[tuple[str, str, str]]]:
    """Per conversation, the (State element, Action element, the Action's event) of each customer turn followed by an agent turn."""
    out = {}
    for c, turns in sequences(rows).items():
        out[c] = [
            (element_of[a["event"]], element_of[b["event"]], b["event"])
            for a, b in zip(turns, turns[1:], strict=False)
            if a["kind"] == "state" and b["kind"] == "action"
        ]
    return out


def abstraction(
    p: Planted, rows: list[dict], element_of: dict[str, str], sizes: Counter | None = None
) -> dict:
    actions = {r["event"] for r in rows if r["kind"] == "action"}
    states = {r["event"] for r in rows if r["kind"] == "state"}
    a_cl, s_cl = {e: element_of[e] for e in actions}, {e: element_of[e] for e in states}
    a = v_measure({e: p.action[e] for e in actions if e in p.action}, a_cl)
    sf = v_measure({e: p.state_fine[e] for e in states if e in p.state_fine}, s_cl)
    sc = v_measure({e: p.state_coarse[e] for e in states if e in p.state_coarse}, s_cl)
    by_el = defaultdict(list)
    for e in states:
        if e in p.stage:
            by_el[s_cl[e]].append(p.stage[e])
    purity = sum(Counter(v).most_common(1)[0][1] for v in by_el.values()) / max(
        1, sum(map(len, by_el.values()))
    )
    size = sizes if sizes is not None else Counter(element_of[r["event"]] for r in rows)
    single = {
        k: sum(1 for r in rows if r["kind"] == k and size[element_of[r["event"]]] == 1)
        for k in ("state", "action")
    }
    counts = {k: len({element_of[r["event"]] for r in rows if r["kind"] == k}) for k in ("state", "action")}
    n = {k: sum(1 for r in rows if r["kind"] == k) for k in ("state", "action")}
    return {
        "action": a,
        "state_fine": sf,
        "state_coarse": sc,
        "stage_purity": purity,
        "elements": counts,
        "singleton_turns": {k: single[k] / n[k] for k in single},
    }


def element_labels(p: Planted, rows: list[dict], element_of: dict[str, str]) -> dict[str, str]:
    """Each element's planted label: the majority of its members' (an Action's action; a State's coarse key)."""
    members = defaultdict(list)
    for r in rows:
        label = p.action.get(r["event"]) if r["kind"] == "action" else p.state_coarse.get(r["event"])
        if label is not None:
            members[element_of[r["event"]]].append(label)
    return {el: majority(v) for el, v in members.items()}


def fidelity(
    p: Planted, rows: list[dict], element_of: dict[str, str], labels: dict[str, str] | None = None
) -> dict:
    """Transition probabilities by label: planted (from the planted labels) against discovered (the elements' counts, by their
    majority label). Pairs the plan makes at least MIN_SUPPORT times."""
    label = labels or element_labels(p, rows, element_of)
    planted, discovered, from_planted, from_discovered = Counter(), Counter(), Counter(), Counter()
    for turns in sequences(rows).values():
        for a, b in zip(turns, turns[1:], strict=False):
            if a["kind"] == b["kind"]:
                continue
            la = (p.action if a["kind"] == "action" else p.state_coarse).get(a["event"])
            lb = (p.action if b["kind"] == "action" else p.state_coarse).get(b["event"])
            if la is None or lb is None:
                continue
            planted[(la, lb)] += 1
            from_planted[la] += 1
        for a in turns:
            la = label.get(element_of[a["event"]])
            if la is not None:
                from_discovered[la] += 1
        for a, b in zip(turns, turns[1:], strict=False):
            if a["kind"] == b["kind"]:
                continue
            la, lb = label.get(element_of[a["event"]]), label.get(element_of[b["event"]])
            if la is not None and lb is not None:
                discovered[(la, lb)] += 1
    keys = [k for k, n in planted.items() if n >= MIN_SUPPORT]
    pp = [planted[k] / from_planted[k[0]] for k in keys]
    dp = [discovered[k] / from_discovered[k[0]] if from_discovered[k[0]] else 0.0 for k in keys]
    spear = pearson(ranks(pp), ranks(dp))
    return {
        "pairs": len(keys),
        "pearson": pearson(pp, dp),
        "spearman": spear,
        "mae": sum(abs(x - y) for x, y in zip(pp, dp, strict=True)) / len(keys) if keys else float("nan"),
    }


def diagnostic(
    p: Planted,
    rows: list[dict],
    element_of: dict[str, str],
    labels: dict[str, str],
    convs: set[str] | None = None,
) -> dict:
    """Leave one conversation out: at a customer turn with a discriminating clue true, perceived and not yet said, and a question in
    the procedure that elicits it, is the graph's likeliest next Action that question?"""
    w = p.world
    seq = sequences(rows)
    pairs = pairs_of(rows, element_of)
    total: Counter = Counter()
    for ps in pairs.values():
        for s_el, a_el, _ in ps:
            total[(s_el, a_el)] += 1
    nexts_by_state: dict[str, set[str]] = defaultdict(set)
    for s_el, a_el in total:
        nexts_by_state[s_el].add(a_el)
    overall_next: Counter = Counter()
    for ps in pairs.values():
        overall_next.update(labels.get(a_el) for _, a_el, _ in ps)
    most_frequent = overall_next.most_common(1)[0][0]

    points = []
    for c, turns in seq.items():
        if (
            convs is not None and c not in convs
        ):  # the counts come from every conversation; only these are scored
            continue
        plan = p.plans[c]
        available = set(w.procedure_actions(plan["procedure"]))
        own = Counter((s_el, a_el) for s_el, a_el, _ in pairs[c])
        for a, b in zip(turns, turns[1:], strict=False):
            if a["kind"] != "state" or b["kind"] != "action" or a["event"] not in p.unbrought:
                continue
            good = {w.elicitor[m] for m in p.unbrought[a["event"]] if m in w.elicitor} & available
            if not good:
                continue
            here = element_of[a["event"]]
            candidates = {x: total[(here, x)] - own[(here, x)] for x in nexts_by_state.get(here, ())}
            candidates = {x: n for x, n in candidates.items() if n > 0}
            pick = min(candidates, key=lambda x: (-candidates[x], x)) if candidates else None
            points.append(
                {
                    "good": good,
                    "available": available,
                    "actual": p.action.get(b["event"]),
                    "recommended": labels.get(pick) if pick else None,
                }
            )
    n = len(points)
    covered = [x for x in points if x["recommended"] is not None]
    hit = lambda rows_, key: sum(1 for x in rows_ if x[key] in x["good"])  # noqa: E731
    best_fixed = max(
        (sum(1 for x in points if cand in x["good"]) for cand in {c for x in points for c in x["good"]}),
        default=0,
    )
    return {
        "points": n,
        "coverage": len(covered) / n if n else float("nan"),
        "graph": (hit(covered, "recommended"), len(covered)),
        "rep_actual": (hit(points, "actual"), n),
        "rep_actual_where_covered": (hit(covered, "actual"), len(covered)),
        "best_fixed_question": (best_fixed, n),
        "most_frequent_next": (sum(1 for x in points if most_frequent in x["good"]), n),
        "chance": sum(len(x["good"]) / len(x["available"]) for x in points) / n if n else float("nan"),
    }


def breach(p: Planted, rows: list[dict], element_of: dict[str, str], labels: dict[str, str]) -> dict:
    """Among conversations with an unauthenticated caller, flag those whose path has no identity-verifying Action element."""
    tp = fp = fn = tn = 0
    for c, turns in sequences(rows).items():
        plan = p.plans[c]
        if plan["authenticated"] or plan["steps"][0]["kind"] == "queue":
            continue
        verified = any(
            labels.get(element_of[t["event"]]) in p.identity for t in turns if t["kind"] == "action"
        )
        planted = any(g["policy"] == "POL-AUTH-BEFORE-DETAIL" for g in plan["breaches"])
        flagged = not verified
        tp, fp, fn, tn = (
            tp + (planted and flagged),
            fp + (not planted and flagged),
            fn + (planted and not flagged),
            tn + (not planted and not flagged),
        )
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def score(
    p: Planted,
    rows: list[dict],
    element_of: dict[str, str],
    labels: dict[str, str] | None = None,
    convs: set[str] | None = None,
) -> dict:
    """The scores over `convs` (all by default): elements, their labels, and the transition counts are from every row given."""
    labels = labels or element_labels(p, rows, element_of)
    sub = [r for r in rows if convs is None or r["conversation"] in convs]
    sizes = Counter(element_of[r["event"]] for r in rows)
    return {
        "abstraction": abstraction(p, sub, element_of, sizes),
        "fidelity": fidelity(p, sub, element_of, labels),
        "diagnostic": diagnostic(p, rows, element_of, labels, convs),
        "breach": breach(p, sub, element_of, labels),
    }


# --------------------------------------------------------------------------------------------------------------- grouping


def grouped(s, G: Graph, rows: list[dict], texts: dict[str, str], emb: Embedder) -> dict[str, str]:
    """element_of from grouping `texts` (event -> the text to embed) with the build's own kNN and Leiden, under s's parameters."""
    ids = sorted(texts)
    vec = dict(zip(ids, (build.unit(v) for v in emb.embed([texts[i] for i in ids])), strict=True))
    kind_of = {r["event"]: r["kind"] for r in rows}
    out = {}
    try:
        for kind in build.LABELS:
            members = [i for i in ids if kind_of[i] == kind]
            for k, ms in build.communities(G, s, kind, build.neighbours(G, s, kind, members, vec)).items():
                for m in ms:
                    out[m] = f"{kind}:{k}"
    finally:
        G.delete(build.IS_SCRATCH)
    return out


# ------------------------------------------------------------------------------------------------------------------ report


def pct(x: float) -> str:
    return "-" if x != x else f"{100 * x:.0f}%"


def rate(pair: tuple[int, int]) -> str:
    k, n = pair
    lo, hi = wilson(k, n)
    return f"{pct(k / n if n else float('nan'))} ({k}/{n}; {pct(lo)}-{pct(hi)})"


def rows_for(arm: dict) -> list[str]:
    a, f, d = arm["abstraction"], arm["fidelity"], arm["diagnostic"]
    return [
        f"{a['elements']['state']} / {a['elements']['action']}",
        f"{pct(a['singleton_turns']['state'])} / {pct(a['singleton_turns']['action'])}",
        f"{a['action'][0]:.2f} / {a['action'][1]:.2f} / **{a['action'][2]:.2f}**",
        f"{a['state_fine'][0]:.2f} / {a['state_fine'][1]:.2f} / **{a['state_fine'][2]:.2f}**",
        f"{a['state_coarse'][0]:.2f} / {a['state_coarse'][1]:.2f} / **{a['state_coarse'][2]:.2f}**",
        pct(a["stage_purity"]),
        f"{f['pearson']:.2f} / {f['spearman']:.2f} / {f['mae']:.3f} ({f['pairs']} pairs)",
        pct(d["coverage"]),
        rate(d["graph"]),
    ]


def table_for(title: str, arms: dict, convs_note: str) -> list[str]:
    names = list(arms)
    table = [
        ("elements touched (States / Actions)", 0),
        ("turns in singleton elements (States / Actions)", 1),
        ("Action: homogeneity / completeness / V", 2),
        ("State vs the planted State key: h / c / V", 3),
        ("State vs the coarse key (domain, stage, verified)", 4),
        ("stage purity of States", 5),
        ("transition fidelity: Pearson / Spearman / MAE", 6),
        ("diagnostic: turns with a recommendation", 7),
        ("diagnostic: the likeliest next Action asks the clue's question", 8),
    ]
    d = arms["graph"]["diagnostic"]
    return [
        f"## {title}",
        "",
        convs_note,
        "",
        "| | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
        *[f"| {label} | " + " | ".join(rows_for(arms[n])[i] for n in names) + " |" for label, i in table],
        "",
        f"The diagnostic test: {d['points']} customer turns where a discriminating clue is true, perceived and not yet said, and a question "
        "in the procedure elicits it; success is the next Action being that question (leave one conversation out).",
        "",
        "| | success |",
        "|---|---|",
        f"| the graph's likeliest next Action | {rate(d['graph'])} |",
        f"| the same turns, what the rep actually did | {rate(d['rep_actual_where_covered'])} |",
        f"| the rep, over all {d['points']} turns | {rate(d['rep_actual'])} |",
        f"| the best single question, chosen with hindsight | {rate(d['best_fixed_question'])} |",
        f"| the most frequent next Action overall | {rate(d['most_frequent_next'])} |",
        f"| chance (a random action of the procedure) | {pct(d['chance'])} |",
        f"| the oracle's likeliest next Action | {rate(arms['oracle']['diagnostic']['graph'])}, covering {pct(arms['oracle']['diagnostic']['coverage'])} |",
        f"| the raw-text arm's | {rate(arms['raw text']['diagnostic']['graph'])}, covering {pct(arms['raw text']['diagnostic']['coverage'])} |",
        "",
        "Unauthenticated callers flagged when no Action on the path verifies identity, against the planted breach:",
        "",
        "| arm | found | false alarms | missed | correctly clear |",
        "|---|---|---|---|---|",
        *[
            f"| {n} | {arms[n]['breach']['tp']} | {arms[n]['breach']['fp']} | {arms[n]['breach']['fn']} | {arms[n]['breach']['tn']} |"
            for n in names
        ],
        "",
    ]


def main() -> None:
    s = settings()
    if "--grid" in sys.argv:
        return grid(s)
    rows = [
        json.loads(line) for line in (s.work / "process" / "observations.ndjson").read_text().splitlines()
    ]
    ann = {
        json.loads(line)["event"]: json.loads(line)
        for line in (s.work / "process" / "annotations-turn.ndjson").read_text().splitlines()
    }
    for r in rows:
        r["description"] = ann[r["event"]]["description"]
    p = Planted(rows)
    emb = Embedder(s)
    all_convs = sorted({r["conversation"] for r in rows})
    tuning = set(
        all_convs[:TUNING]
    )  # the conversations the parameters were chosen on (the first TUNING, by id)
    holdout = set(all_convs[TUNING:])

    graph_of = {r["event"]: r["element"] for r in rows}
    # the stored transitions against a recount from the turns
    with Graph(s, {"database": s["process"]["database"]}) as G:
        stored = {
            (r["a"], r["t"], r["b"]): r["num"]
            for r in G.rows("MATCH (a)-[r]->(b) RETURN a.id AS a, type(r) AS t, b.id AS b, r.num AS num")
        }
        recount = Counter()
        for ps in pairs_of(rows, graph_of).values():
            for a, b, _ in ps:
                recount[(a, "SELECTS", b)] += 1
        recount_ok = all(stored.get(k) == n for k, n in recount.items())

        events = {}
        with gzip.open(BUILD / "corpus" / "full" / "events.ndjson.gz", "rt") as f:
            wanted = {r["event"] for r in rows}
            for line in f:
                e = json.loads(line)
                if e["event_id"] in wanted:
                    events[e["event_id"]] = e["text"]
        raw_of = grouped(s, G, rows, {r["event"]: events[r["event"]] for r in rows}, emb)

    oracle_of = {
        r["event"]: (p.action[r["event"]] if r["kind"] == "action" else p.state_fine[r["event"]])
        for r in rows
        if r["event"] in p.action or r["event"] in p.state_fine
    }
    oracle_rows = [r for r in rows if r["event"] in oracle_of]

    def arms_on(convs: set[str] | None) -> dict:
        return {
            "graph": score(p, rows, graph_of, convs=convs),
            "raw text": score(p, rows, raw_of, convs=convs),
            "oracle": score(p, oracle_rows, oracle_of, convs=convs),
        }

    by = {"holdout": arms_on(holdout), "tuning": arms_on(tuning), "all": arms_on(None)}
    md = [
        "# Process graph: is it the planted process?",
        "",
        f"{len(all_convs)} conversations, {len(rows)} turns, one graph built from all of them (`qlsc process build`), scored against the answer "
        f"key. Parameters: similarity {s['process']['similarity']}, resolution {s['process']['gamma']}, State text {s['process']['state_embeds']}, "
        f"chosen on the first {TUNING} conversations by id (the first 100 in phase 3, then 100 to 600 at scale in phase 4). The **holdout** is the other {len(holdout)}: the parameters were never tuned "
        "on them. Arms: **graph** (the build), **raw text** (the same embedder and grouping over the unannotated turns), **oracle** (the planted "
        "labels as the elements).",
        "",
        *table_for("The holdout", by["holdout"], f"{len(holdout)} conversations."),
        *table_for(
            "The tuning conversations",
            by["tuning"],
            f"The first {TUNING}, which the parameters were chosen on, in the larger graph.",
        ),
        *table_for("All", by["all"], f"All {len(all_convs)}."),
        f"The stored `num` of every transition equals a recount from the turns: {recount_ok}.",
    ]
    print(
        write_result(
            "process_graph", md, {"subsets": by, "recount_ok": recount_ok, "parameters": s["process"]}
        )
    )
    print("\n".join(md))


def option(name: str, default: str) -> str:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def grid(s) -> None:
    """Grouping parameters scored by the grouping alone (no naming). The grouping is over every annotated turn; the score is over the
    conversations `--convs A:B` (by id order; default the first TUNING), so the parameters can be chosen on one slice and judged on another."""
    rows = [
        json.loads(line) for line in (s.work / "process" / "annotations-turn.ndjson").read_text().splitlines()
    ]
    rows = [r for r in rows if r["description"] and not r["problems"]]
    p = Planted(rows)
    emb = Embedder(s)
    all_convs = sorted({r["conversation"] for r in rows})
    a, b = (int(x) for x in option("--convs", f"0:{TUNING}").split(":"))
    scored = set(all_convs[a:b])
    embeds = option("--embeds", "both,established").split(",")
    sims = [float(x) for x in option("--sims", "0.70,0.75,0.80,0.85").split(",")]
    gammas = [float(x) for x in option("--gammas", "0.5,1.0,2.0").split(",")]
    out = []
    with Graph(s, {"database": s["process"]["database"]}) as G:
        for e, sim, gamma in product(embeds, sims, gammas):
            s["process"].update(state_embeds=e, similarity=sim, gamma=gamma)
            texts = {r["event"]: build.text_to_embed(s, r) for r in rows}
            element_of = grouped(s, G, rows, texts, emb)
            sc = score(p, rows, element_of, convs=scored)
            ab, d = sc["abstraction"], sc["diagnostic"]
            out.append(
                {
                    "state_embeds": e,
                    "similarity": sim,
                    "gamma": gamma,
                    "states": ab["elements"]["state"],
                    "actions": ab["elements"]["action"],
                    "action_v": ab["action"][2],
                    "action_c": ab["action"][1],
                    "state_fine_v": ab["state_fine"][2],
                    "state_coarse_v": ab["state_coarse"][2],
                    "stage_purity": ab["stage_purity"],
                    "fidelity": sc["fidelity"]["pearson"],
                    "coverage": d["coverage"],
                    "diag": d["graph"],
                }
            )
            print(out[-1], flush=True)
    out.sort(key=lambda r: -(r["action_v"] + r["state_fine_v"]))
    name = option("--name", "process_graph_grid")
    md = [
        "# Process graph: the grouping parameters, by the score",
        "",
        f"The grouping is over all {len(rows)} annotated turns; the score is over conversations {a} to {b} (by id), {len(scored)} of them. "
        "Sorted by Action V + State V (against the planted State key). Grouping only: no naming, no folding.",
        "",
        "| State text | similarity | resolution | States | Actions | Action V (completeness) | State V (key) | State V (coarse) | stage purity | fidelity r | diag covered | diag success |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
        *[
            f"| {r['state_embeds']} | {r['similarity']} | {r['gamma']} | {r['states']} | {r['actions']} | {r['action_v']:.2f} ({r['action_c']:.2f}) | {r['state_fine_v']:.2f} | {r['state_coarse_v']:.2f} | {pct(r['stage_purity'])} | {r['fidelity']:.2f} | {pct(r['coverage'])} | {r['diag'][0]}/{r['diag'][1]} |"
            for r in out
        ],
    ]
    print(write_result(name, md, {"grid": out}))


if __name__ == "__main__":
    main()

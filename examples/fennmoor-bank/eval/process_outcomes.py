"""Process abstraction, phase 2 (plans/2026-10-06-process-abstraction.md): are the kinds of outcome found in the text the outcomes the world planted?

`qlsc process outcomes` describes how each conversation ended (its last turns and the agent's note, one cheap call each), groups the descriptions,
and names the kinds. This reads the result and the corpus's answer key (which the tool never reads) and asks:

  types      the kinds against the planted outcome of each conversation (homogeneity, completeness, V-measure), and against what the text can
             show at all. Some planted outcomes differ only in what the text cannot say (a fix that did not fix, a verification that was
             skipped): the "visible" classes merge them, so the score has a ceiling that is the corpus's, not the method's.
  rating     the 1 to 5 rating against the planted favourability (Spearman), and how well it separates the cases that ended well.
  arms       the same grouping over the raw after-call note (no description), and the planted outcomes themselves (the ceiling).
  --grid     similarity x resolution, grouping only, on the TUNING conversations. The rule, set before looking: the highest V against the planted
             outcomes among settings that give 15 to 40 kinds; the vocabulary must be small enough for each kind to have the support odds need.

Writes results/process_outcomes.md and .json (or process_outcomes_grid.md). Usage: uv run examples/fennmoor-bank/eval/process_outcomes.py [--grid]
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter, defaultdict
from itertools import product

import process_graph as pg
from common import BUILD, settings, write_result

from qlsc.graph import Graph
from qlsc.llm import Embedder
from qlsc.process import build, outcomes, source

FAVOURABILITY = {"high": 4, "medium": 3, "low": 2, "very-low": 1}
VISIBLE = {  # what the conversation can show: how it was left, not whether the fix fixed or a gate was kept
    "OUT-RETAINED-WITH-OFFER": "retained",
    "OUT-RETAINED-WITH-BREACH": "retained",
    "OUT-CLOSED-AFTER-SAVE-ATTEMPT": "closed",
    "OUT-CLOSED-WITHOUT-SAVE-ATTEMPT": "closed",
    "OUT-ESCALATED": "escalated",
    "OUT-TRANSFERRED": "transferred",
    "OUT-ABANDONED-FRUSTRATED": "abandoned",
    "OUT-ABANDONED-IN-QUEUE": "abandoned",
}
TYPES_RULE = (15, 40)


def truth_of(convs: set[str]) -> dict[str, dict]:
    out = {}
    with gzip.open(BUILD / "corpus" / "full" / "truth.ndjson.gz", "rt") as f:
        for line in f:
            t = json.loads(line)
            if t["conversation_id"] in convs and t["events"]:
                out[t["conversation_id"]] = {
                    "outcome": t["outcome"],
                    "favourability": t["favorability"],
                    "visible": VISIBLE.get(t["outcome"], "handled"),
                }
    return out


def spearman(a: list[float], b: list[float]) -> float:
    return pg.pearson(pg.ranks(a), pg.ranks(b))


def auc(score: list[float], positive: list[bool]) -> float:
    r = pg.ranks(score)
    n1 = sum(positive)
    n0 = len(positive) - n1
    if not n1 or not n0:
        return float("nan")
    return (sum(x for x, p in zip(r, positive, strict=True) if p) - n1 * (n1 + 1) / 2) / (n1 * n0)


def scores(kind_of: dict[str, str], truth: dict[str, dict], convs: set[str]) -> dict:
    keep = [c for c in kind_of if c in truth and c in convs]
    planted = {c: truth[c]["outcome"] for c in keep}
    visible = {c: truth[c]["visible"] for c in keep}
    k = {c: kind_of[c] for c in keep}
    return {
        "n": len(keep),
        "types": len(set(k.values())),
        "vs_planted": pg.v_measure(planted, k),
        "vs_visible": pg.v_measure(visible, k),
    }


def rating_scores(rating: dict[str, int], truth: dict[str, dict], convs: set[str]) -> dict:
    keep = [c for c in rating if c in truth and c in convs and rating[c]]
    fav = [FAVOURABILITY[truth[c]["favourability"]] for c in keep]
    r = [rating[c] for c in keep]
    by = defaultdict(list)
    for c in keep:
        by[truth[c]["favourability"]].append(rating[c])
    return {
        "n": len(keep),
        "spearman": spearman(r, fav),
        "auc_high": auc(r, [truth[c]["favourability"] == "high" for c in keep]),
        "mean_by_favourability": {k: sum(v) / len(v) for k, v in by.items()},
    }


def load(s):
    rows = [json.loads(line) for line in (s.work / "process" / "outcomes.ndjson").read_text().splitlines()]
    obs = [json.loads(line) for line in (s.work / "process" / "observations.ndjson").read_text().splitlines()]
    all_convs = sorted({r["conversation"] for r in obs})
    return rows, set(all_convs[: pg.TUNING]), set(all_convs[pg.TUNING :]), set(all_convs)


def regroup(s, G, texts: dict[str, str], params: dict) -> dict[str, str]:
    emb = Embedder(s)
    ids = sorted(texts)
    vec = dict(zip(ids, (build.unit(v) for v in emb.embed([texts[i] for i in ids])), strict=True))
    groups = outcomes.group(s, G, vec, params)
    return {m: k for k, ms in groups.items() for m in ms}


def main() -> None:
    s = settings()
    if "--grid" in sys.argv:
        return grid(s)
    rows, tuning, holdout, everyone = load(s)
    truth = truth_of(everyone)
    types = json.loads((s.work / "process" / "outcome_types.json").read_text())
    kind_of = {r["conversation"]: r["type"] for r in rows if r["type"]}
    rating = {r["conversation"]: r["rating"] for r in rows if r["rating"]}
    notes = source.notes(s)
    with Graph(s, {"database": s["process"]["database"]}) as G:
        raw = regroup(s, G, {c: notes[c] for c in kind_of if c in notes}, s["process"]["outcomes"])
    oracle = {c: truth[c]["outcome"] for c in truth}
    arms = {"described (the build)": kind_of, "raw note, no description": raw, "planted (ceiling)": oracle}
    by_subset = {
        name: {a: scores(k, truth, convs) for a, k in arms.items()}
        for name, convs in (("holdout", holdout), ("tuning", tuning))
    }
    ratings = {
        name: rating_scores(rating, truth, convs)
        for name, convs in (("holdout", holdout), ("tuning", tuning))
    }

    def table(name: str) -> list[str]:
        rows_ = [
            f"| {a} | {x['types']} | {x['vs_planted'][0]:.2f} / {x['vs_planted'][1]:.2f} / **{x['vs_planted'][2]:.2f}** | {x['vs_visible'][0]:.2f} / {x['vs_visible'][1]:.2f} / **{x['vs_visible'][2]:.2f}** |"
            for a, x in by_subset[name].items()
        ]
        r = ratings[name]
        return [
            "| arm | kinds | against the planted outcomes: h / c / V | against what the text can show: h / c / V |",
            "|---|---|---|---|",
            *rows_,
            "",
            f"Rating against the planted favourability ({r['n']} conversations): Spearman **{r['spearman']:.2f}**; AUC for telling the cases that ended well "
            f"(planted high) from the rest **{r['auc_high']:.2f}**; mean rating by planted favourability: "
            + ", ".join(
                f"{k} {v:.1f}"
                for k, v in sorted(r["mean_by_favourability"].items(), key=lambda kv: -FAVOURABILITY[kv[0]])
            ),
        ]

    composition = []
    members = defaultdict(list)
    for c, k in kind_of.items():
        if c in truth:
            members[k].append(truth[c]["outcome"].replace("OUT-", ""))
    for t in types:
        comp = Counter(members[t["id"]]).most_common(3)
        composition.append(
            f"| {t['name']} | {t['count']} | {t['rating']:.1f} | "
            + ", ".join(f"{o} {n}" for o, n in comp)
            + " |"
        )
    planted_mix = Counter(v["outcome"].replace("OUT-", "") for v in truth.values()).most_common()
    md = [
        "# Process abstraction, phase 2: the kinds of outcome",
        "",
        f"{len(rows)} conversations; the kinds were found by describing how each ended (its last turns and the agent's after-call note), embedding "
        f"the descriptions and grouping them (similarity {s['process']['outcomes']['similarity']}, resolution {s['process']['outcomes']['gamma']}, "
        f"kinds under {s['process']['outcomes']['min_type']} conversations folded into the nearest). Tuning slice: the first {pg.TUNING} by id; holdout: the rest.",
        "",
        "## The holdout",
        "",
        *table("holdout"),
        "",
        "## The tuning conversations",
        "",
        *table("tuning"),
        "",
        "## What each kind is made of (planted outcomes, the three commonest)",
        "",
        "| kind | conversations | rating | planted outcomes |",
        "|---|---|---|---|",
        *composition,
        "",
        "The planted outcomes, for scale: " + ", ".join(f"{o} {n}" for o, n in planted_mix) + ".",
    ]
    print(write_result("process_outcomes", md, {"by_subset": by_subset, "ratings": ratings, "types": types}))
    print("\n".join(md))


def grid(s) -> None:
    rows, tuning, holdout, everyone = load(s)
    truth = truth_of(everyone)
    texts = {r["conversation"]: r["description"] for r in rows if r["description"] and not r["problems"]}
    out = []
    with Graph(s, {"database": s["process"]["database"]}) as G:
        for sim, gamma in product(
            [float(x) for x in pg.option("--sims", "0.70,0.75,0.80,0.85,0.90").split(",")],
            [float(x) for x in pg.option("--gammas", "0.5,1.0,2.0,4.0").split(",")],
        ):
            params = {**s["process"]["outcomes"], "similarity": sim, "gamma": gamma}
            kind_of = regroup(s, G, texts, params)
            x = scores(kind_of, truth, tuning)
            out.append({"similarity": sim, "gamma": gamma, **x})
            print(out[-1], flush=True)
    ok = [r for r in out if TYPES_RULE[0] <= r["types"] <= TYPES_RULE[1]]
    best = max(ok, key=lambda r: (r["vs_planted"][2], -r["types"])) if ok else None
    md = [
        "# Process abstraction, phase 2: the grouping parameters for outcomes",
        "",
        f"Grouping only, on the tuning conversations (the first {pg.TUNING} by id). The rule, set beforehand: the highest V against the planted outcomes "
        f"among settings that give {TYPES_RULE[0]} to {TYPES_RULE[1]} kinds.",
        "",
        "| similarity | resolution | kinds | against planted: h / c / V | against what the text can show: h / c / V | within the rule |",
        "|---|---|---|---|---|---|",
        *[
            f"| {r['similarity']} | {r['gamma']} | {r['types']} | {r['vs_planted'][0]:.2f} / {r['vs_planted'][1]:.2f} / {r['vs_planted'][2]:.2f} | "
            f"{r['vs_visible'][0]:.2f} / {r['vs_visible'][1]:.2f} / {r['vs_visible'][2]:.2f} | {'**yes**' if r in ok else ''} |"
            for r in out
        ],
        "",
        "Chosen: "
        + (
            f"similarity {best['similarity']}, resolution {best['gamma']}" if best else "none within the rule"
        ),
    ]
    print(write_result("process_outcomes_grid", md, {"grid": out, "chosen": best}))


if __name__ == "__main__":
    main()

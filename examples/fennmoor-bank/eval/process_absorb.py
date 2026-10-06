"""Process abstraction, phase 3 (plans/2026-10-06-process-abstraction.md): do the odds on a State say how a case will end?

`qlsc process absorb` puts on every element the chance its cases end well, two ways (the share of the conversations that passed through it
that ended well: `empirical`; the absorbing chain over the transitions: `chain`). This scores them where it counts: standing at a State in the
life of a conversation, how well does the State's end-well odds predict how the conversation ended?

  checkpoints  after the customer's 1st, 2nd, 3rd, 4th and 6th turn, and at the last (a conversation is scored at the ones it has).
  target       the planted favourability is high (the answer key: "the case ended well"), which the tool never reads; and, as a second score, the
               text's own label (the outcome call's rating at or above `good_rating`), which is what the odds were fitted to.
  honesty      leave-one-conversation-out, for every number: the conversation scored is taken out of the counts (and of the chain) before its
               State is read, so no case is scored by itself. A rare State has few conversations left, so it falls back to the global rate when
               fewer than `min_support` remain, and the coverage says how often.
  arms         the global rate; the rate by the conversation's domain; by turn position alone; by the planted State (the answer key's coarse
               key, the oracle: what a perfect State could say); the graph's empirical estimate; the graph's chain estimate.
  scores       Brier (lower is better) and its paired difference from the global rate with a 95% interval over conversations; AUC; coverage;
               calibration of the stored estimator; mean prediction by planted favourability.
  --grid       on the TUNING conversations (the first 600 by id): the pseudo-conversation `prior` for each estimator and `min_support`, and
               `good_rating`. The rules, set before looking: the prior with the lowest Brier against the planted label, per estimator; the
               estimator with the lower Brier, and `empirical` if the paired difference between them includes zero (decision 4); `min_support`
               the smallest of 3, 5 and 10 whose Brier is within 0.002 of the best; `good_rating` the one that agrees most with the planted label.

Writes results/process_absorb.md and .json (or process_absorb_grid.md). Usage: uv run examples/fennmoor-bank/eval/process_absorb.py [--grid]
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict

import process_graph as pg
import process_outcomes as po
from common import RESULTS, settings, write_result

from qlsc.process import absorb

CHECKPOINTS = (1, 2, 3, 4, 6)
LAST = "the last"
ARMS = ("global rate", "by domain", "by position", "by planted State", "empirical", "chain")


def label(k: int | str) -> str:
    return LAST if k == LAST else f"{k}{'st' if k == 1 else 'nd' if k == 2 else 'rd' if k == 3 else 'th'}"


class Tally:
    """Counts of conversations and of good ones per key, that a conversation can be taken out of and put back."""

    def __init__(self) -> None:
        self.n: dict = defaultdict(int)
        self.good: dict = defaultdict(int)

    def add(self, keys, good: int, sign: int = 1) -> None:
        for k in keys:
            self.n[k] += sign
            self.good[k] += sign * good

    def rate(self, key, base: float, prior: float, floor: int) -> float:
        n = self.n.get(key, 0)
        return absorb.smoothed(self.good.get(key, 0), n, base, prior) if n >= floor else base


def load(s):
    """Everything the scoring needs, as the tool left it: the paths, the checkpoints and the answer key's view of each."""
    obs = [json.loads(line) for line in (s.work / "process" / "observations.ndjson").read_text().splitlines()]
    planted = pg.Planted(obs)
    by = defaultdict(list)
    for r in obs:
        by[r["conversation"]].append(r)
    ids = sorted(by)
    checkpoints: dict[str, list[dict]] = {}
    for c in ids:
        states = [r for r in sorted(by[c], key=lambda r: r["seq"]) if r["kind"] == "state"]
        picks = [(k, states[k - 1]) for k in CHECKPOINTS if k <= len(states)]
        if states:
            picks.append((LAST, states[-1]))
        checkpoints[c] = [
            {"label": label(k), "element": r["element"], "key": planted.state_coarse.get(r["event"])}
            for k, r in picks
        ]
    truth = {c: planted.truth[c] for c in ids if c in planted.truth}
    return obs, ids, checkpoints, truth, planted


def contributions(c: str, checkpoints, domain: dict[str, str]):
    """The keys one conversation counts under in each of the answer-key arms."""
    cps = checkpoints[c]
    return {
        "domain": [domain.get(c)],
        "position": [x["label"] for x in cps],
        "oracle": [(x["label"], x["key"]) for x in cps if x["key"] is not None],
    }


def score(
    s,
    p: dict,
    floor: int,
    convs: set[str],
    data,
    outcomes,
    arms=ARMS,
    groups: list[list[str]] | None = None,
    chain_prior: float | None = None,
) -> list[dict]:
    """Every arm's prediction at every checkpoint of every scored conversation, each taken out of the counts (and the chain) before it is read:
    alone (leave-one-conversation-out, the default) or with its group (`groups`: a fold, so that the global rate is the same for every
    conversation in it: leaving one out moves the rate against its own label, which is harmless for a Brier score and makes a ranking
    measure like AUC read below one half for a rate that is constant). `chain_prior`: the chain's own pseudo-conversations (it scored best with none).
    -> rows {conversation, group, checkpoint, arm, p, planted, favourability, text, covered}."""
    obs, ids, checkpoints, truth, _ = data
    domain = {c: truth[c]["domain"] for c in truth}
    ps = absorb.paths(obs, outcomes)
    by_conv = {x.conversation: x for x in ps}
    counts = absorb.Counts()
    tallies = {k: Tally() for k in ("domain", "position", "oracle")}
    for x in ps:
        counts.add(x)
        for k, keys in contributions(x.conversation, checkpoints, domain).items():
            tallies[k].add(keys, x.good)
    pc = {**p, "prior": p["prior"] if chain_prior is None else chain_prior}
    full = absorb.chain(counts, pc) if "chain" in arms else None
    rows = []
    for g, group in enumerate(groups or [[c] for c in sorted(convs)]):
        group = [c for c in group if c in by_conv and c in truth]
        if not group:
            continue
        mine = {c: contributions(c, checkpoints, domain) for c in group}
        for c in group:
            counts.add(by_conv[c], -1)
            for k, keys in mine[c].items():
                tallies[k].add(keys, by_conv[c].good, -1)
        base = counts.base
        h = absorb.chain(counts, pc, start=full) if "chain" in arms else None
        for c in group:
            if c not in convs:
                continue
            for cp in checkpoints[c]:
                e, n = cp["element"], counts.through.get(cp["element"], 0)
                pred = {
                    "global rate": base,
                    "by domain": tallies["domain"].rate(domain[c], base, p["prior"], floor),
                    "by position": tallies["position"].rate(cp["label"], base, p["prior"], floor),
                    "by planted State": tallies["oracle"].rate(
                        (cp["label"], cp["key"]), base, p["prior"], floor
                    )
                    if cp["key"] is not None
                    else base,
                    "empirical": absorb.empirical(counts, e, p["prior"]) if n >= floor else base,
                    "chain": h[e] if h is not None and n >= floor and e in h else base,
                }
                for arm in arms:
                    rows.append(
                        {
                            "conversation": c,
                            "group": g,
                            "checkpoint": cp["label"],
                            "arm": arm,
                            "p": pred[arm],
                            "planted": int(truth[c]["favorability"] == "high"),
                            "favourability": truth[c]["favorability"],
                            "text": by_conv[c].good,
                            "covered": n >= floor,
                        }
                    )
        for c in group:
            counts.add(by_conv[c], 1)
            for k, keys in mine[c].items():
                tallies[k].add(keys, by_conv[c].good, 1)
    return rows


def folds(ids: list[str], k: int) -> list[list[str]]:
    """k folds of the conversations, by position in id order."""
    return [ids[i::k] for i in range(k)]


# -------------------------------------------------------------------------------------------------------------------- scores


def brier(rows: list[dict], target: str = "planted") -> float:
    return sum((r["p"] - r[target]) ** 2 for r in rows) / len(rows)


def paired(rows: list[dict], arm: str, against: str, target: str = "planted") -> tuple[float, float]:
    """The mean Brier difference (arm minus against) and its standard error, over conversations (a conversation's checkpoints are averaged)."""
    mine = {(r["conversation"], r["checkpoint"]): (r["p"] - r[target]) ** 2 for r in rows if r["arm"] == arm}
    other = {
        (r["conversation"], r["checkpoint"]): (r["p"] - r[target]) ** 2 for r in rows if r["arm"] == against
    }
    per: dict[str, list[float]] = defaultdict(list)
    for k, v in mine.items():
        per[k[0]].append(v - other[k])
    d = [sum(v) / len(v) for v in per.values()]
    m = sum(d) / len(d)
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1) / len(d)) if len(d) > 1 else float("nan")
    return m, se


def table(rows: list[dict], arms=ARMS, groups: list[str] | None = None) -> tuple[list[str], dict]:
    groups = groups or [*(label(k) for k in CHECKPOINTS), LAST, "all"]
    out, data = [], {}
    out.append(
        "| arm | "
        + " | ".join(
            f"{g} (n={sum(1 for r in rows if r['arm'] == arms[0] and (g == 'all' or r['checkpoint'] == g))})"
            for g in groups
        )
        + " |"
    )
    out.append("|---|" + "---|" * len(groups))
    for arm in arms:
        cells = []
        for g in groups:
            sub = [r for r in rows if r["arm"] == arm and (g == "all" or r["checkpoint"] == g)]
            if not sub:
                cells.append("-")
                continue
            b = brier(sub)
            glob = [r for r in rows if r["arm"] == "global rate" and (g == "all" or r["checkpoint"] == g)]
            if arm == "global rate":
                cells.append(f"{b:.3f}")
            else:
                d, se = paired([r for r in rows if g == "all" or r["checkpoint"] == g], arm, "global rate")
                cells.append(f"{b:.3f} ({d:+.3f} ± {1.96 * se:.3f})")
            data[(arm, g)] = {"brier": b, "n": len(sub), "global": brier(glob)}
        out.append(f"| {arm} | " + " | ".join(cells) + " |")
    return out, data


def aucs(rows: list[dict], arms=ARMS) -> list[str]:
    """AUC for telling the cases that end well, within each fold (rows scored with `groups`) and averaged over the folds by their pairs of
    one case that ended well and one that did not."""
    cols = [*(label(k) for k in CHECKPOINTS), LAST, "all"]
    out = ["| arm | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for arm in arms:
        cells = []
        for g in cols:
            num = den = 0.0
            by: dict[int, list[dict]] = defaultdict(list)
            for r in rows:
                if r["arm"] == arm and (g == "all" or r["checkpoint"] == g):
                    by[r["group"]].append(r)
            for sub in by.values():
                ys = [bool(r["planted"]) for r in sub]
                pairs = sum(ys) * (len(ys) - sum(ys))
                if pairs:
                    num += pairs * po.auc([r["p"] for r in sub], ys)
                    den += pairs
            cells.append(f"{num / den:.2f}" if den else "-")
        out.append(f"| {arm} | " + " | ".join(cells) + " |")
    return out


def calibration(rows: list[dict], arm: str, target: str = "planted", bins: int = 5) -> list[str]:
    sub = [r for r in rows if r["arm"] == arm]
    out = ["| predicted | checkpoints | mean predicted | ended well |", "|---|---|---|---|"]
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        got = [r for r in sub if lo <= r["p"] < hi or (b == bins - 1 and r["p"] == 1.0)]
        if not got:
            continue
        mp, rate = sum(r["p"] for r in got) / len(got), sum(r[target] for r in got) / len(got)
        ece += len(got) / len(sub) * abs(mp - rate)
        out.append(f"| {lo:.1f} to {hi:.1f} | {len(got)} | {mp:.2f} | {rate:.2f} |")
    out.append(f"\nExpected calibration error: **{ece:.3f}**.")
    return out


def by_favourability(rows: list[dict], arm: str) -> list[str]:
    cols = [label(k) for k in CHECKPOINTS] + [LAST]
    out = ["| planted favourability | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for fav in ("high", "medium", "low", "very-low"):
        cells = []
        for g in cols:
            sub = [r for r in rows if r["arm"] == arm and r["favourability"] == fav and r["checkpoint"] == g]
            cells.append(f"{sum(r['p'] for r in sub) / len(sub):.2f}" if sub else "-")
        out.append(f"| {fav} | " + " | ".join(cells) + " |")
    return out


def coverage(rows: list[dict], arm: str) -> float:
    sub = [r for r in rows if r["arm"] == arm]
    return sum(r["covered"] for r in sub) / len(sub)


# ----------------------------------------------------------------------------------------------------------------------- main


def outcomes_for(s, rating: int | None = None) -> dict:
    p = s["process"]["absorb"]
    found, _ = absorb.read_outcomes(s)
    if rating is None or rating == p["good_rating"]:
        return found
    return {c: {**v, "good": int(v["rating"] >= rating)} for c, v in found.items()}


FOLDS = 20


def chain_prior_from_grid(default: float) -> float:
    """The chain's best prior on the tuning conversations, from the grid's own record (it is not the empirical estimate's)."""
    path = RESULTS / "process_absorb_grid.json"
    if not path.is_file():
        return default
    by = json.loads(path.read_text())["by_prior"]
    return float(min(by, key=lambda k: (by[k]["chain"], float(k))))


def main() -> None:
    s = settings()
    if "--grid" in sys.argv:
        return grid(s)
    p, floor = s["process"]["absorb"], s["process"]["min_support"]
    data = load(s)
    ids = data[1]
    tuning, holdout = set(ids[: pg.TUNING]), set(ids[pg.TUNING :])
    found = outcomes_for(s)
    t0 = time.time()
    chain_prior = chain_prior_from_grid(p["prior"])
    rows = {
        name: score(s, p, floor, convs, data, found, chain_prior=chain_prior)
        for name, convs in (("holdout", holdout), ("tuning", tuning))
    }
    fold_rows = score(
        s, p, floor, set(ids), data, found, groups=folds(ids, FOLDS), chain_prior=chain_prior
    )  # the same arms, each fold taken out whole, for a ranking measure
    in_fold = {
        "holdout": [r for r in fold_rows if r["conversation"] in holdout],
        "tuning": [r for r in fold_rows if r["conversation"] in tuning],
    }
    stored = p["estimator"]
    md = [
        "# Process abstraction, phase 3: the odds on a State",
        "",
        f"Estimates are leave-one-conversation-out (the AUC tables, in {FOLDS} folds: see below); a State with fewer than {floor} conversations left carries none, and the global rate is used in its place (the coverage says how often). "
        f"Ended well: the outcome call's rating at least {p['good_rating']} (the fitting) and the planted favourability high (the score). "
        f"Prior {p['prior']} pseudo-conversations for every arm but the chain, which scored best with {chain_prior:g}. Tuning slice: the first {pg.TUNING} by id; holdout: the rest ({len(holdout)}). "
        f"The estimator stored on the graph is **{stored}**.",
        "",
    ]
    record = {}
    for name in ("holdout", "tuning"):
        r = rows[name]
        t, d = table(r)
        md += [
            f"## {name.capitalize()}: Brier score against the planted label (lower is better; the difference from the global rate, with a 95% interval)",
            "",
            *t,
            "",
            f"Coverage (checkpoints in a State with at least {floor} other conversations): empirical **{coverage(r, 'empirical'):.0%}**, chain **{coverage(r, 'chain'):.0%}**.",
            "",
            f"### {name.capitalize()}: Brier against the text's own label (what the odds were fitted to)",
            "",
        ]
        for arm in ARMS:
            sub = [x for x in r if x["arm"] == arm]
            md.append(f"- {arm}: {brier(sub, 'text'):.3f}")
        md += [
            "",
            f"### {name.capitalize()}: AUC for telling the cases that end well, at each checkpoint (in {FOLDS} folds of conversations, each taken out whole, and averaged over folds: leaving one conversation out moves a rate against its own label, which makes a constant rate read below one half)",
            "",
            *aucs(in_fold[name]),
            "",
        ]
        record[name] = {
            "brier": {f"{a}|{g}": v for (a, g), v in d.items()},
            "coverage": {a: coverage(r, a) for a in ("empirical", "chain")},
        }
    r = rows["holdout"]
    for a, b in (("empirical", "chain"), ("empirical", "by planted State"), ("chain", "by planted State")):
        d, se = paired(r, a, b)
        md.append(
            f"Holdout, {a} minus {b} (Brier, paired over conversations): **{d:+.4f} ± {1.96 * se:.4f}**."
        )
        record[f"holdout_{a}_minus_{b}"] = [d, 1.96 * se]
    md += [
        "",
        f"## Holdout: calibration of the stored estimator ({stored})",
        "",
        *calibration(r, stored),
        "",
        f"## Holdout: mean {stored} prediction by planted favourability (does the odds separate the cases as they unfold?)",
        "",
        *by_favourability(r, stored),
        "",
        f"{time.time() - t0:.0f} seconds for both slices.",
    ]
    print(write_result("process_absorb", md, record))
    print("\n".join(md))


def grid(s) -> None:
    p0, floor0 = s["process"]["absorb"], s["process"]["min_support"]
    data = load(s)
    ids = data[1]
    tuning = set(ids[: pg.TUNING])
    truth = data[3]
    md = ["# Process abstraction, phase 3: the grid on the tuning conversations", ""]
    record: dict = {}
    # good_rating: agreement with the planted label
    md += [
        "## good_rating: the rating that best separates the planted high favourability",
        "",
        "| rating at least | accuracy | precision | recall |",
        "|---|---|---|---|",
    ]
    agree = {}
    for g in (3, 4, 5):
        found = outcomes_for(s, g)
        tp = fp = fn = tn = 0
        for c in tuning:
            if c in found and c in truth:
                y, pr = truth[c]["favorability"] == "high", bool(found[c]["good"])
                tp, fp, fn, tn = (
                    tp + (y and pr),
                    fp + (not y and pr),
                    fn + (y and not pr),
                    tn + (not y and not pr),
                )
        agree[g] = (tp + tn) / (tp + fp + fn + tn)
        md.append(f"| {g} | {agree[g]:.3f} | {tp / (tp + fp):.3f} | {tp / (tp + fn):.3f} |")
    best_rating = max(agree, key=lambda g: (agree[g], -g))
    md += ["", f"Chosen: **{best_rating}**.", ""]
    found = outcomes_for(s, best_rating)
    # prior, per estimator
    md += [
        "## prior: Brier against the planted label, all checkpoints, per estimator",
        "",
        "| prior | empirical | chain |",
        "|---|---|---|",
    ]
    best = {}
    results = {}
    for prior in (0.0, 1.0, 2.0, 5.0, 10.0, 20.0):
        p = {**p0, "prior": prior, "good_rating": best_rating}
        rows = score(s, p, floor0, tuning, data, found, arms=("global rate", "empirical", "chain"))
        b = {a: brier([r for r in rows if r["arm"] == a]) for a in ("global rate", "empirical", "chain")}
        results[prior] = {"brier": b, "rows": rows}
        md.append(f"| {prior:g} | {b['empirical']:.4f} | {b['chain']:.4f} |")
        print(f"prior {prior}: {b}", flush=True)
    for a in ("empirical", "chain"):
        best[a] = min(results, key=lambda pr: (results[pr]["brier"][a], pr))
    glob = results[best["empirical"]]["brier"]["global rate"]
    md += [
        "",
        f"The global rate scores {glob:.4f}. Best prior: empirical **{best['empirical']:g}**, chain **{best['chain']:g}**.",
        "",
    ]
    emp_rows = [r for r in results[best["empirical"]]["rows"] if r["arm"] in ("empirical", "global rate")]
    chn_rows = [r for r in results[best["chain"]]["rows"] if r["arm"] in ("chain", "global rate")]
    # estimator: paired difference between the best of each
    a = {
        (r["conversation"], r["checkpoint"]): (r["p"] - r["planted"]) ** 2
        for r in emp_rows
        if r["arm"] == "empirical"
    }
    b = {
        (r["conversation"], r["checkpoint"]): (r["p"] - r["planted"]) ** 2
        for r in chn_rows
        if r["arm"] == "chain"
    }
    per: dict[str, list[float]] = defaultdict(list)
    for k in a:
        per[k[0]].append(a[k] - b[k])
    d = [sum(v) / len(v) for v in per.values()]
    m = sum(d) / len(d)
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1) / len(d))
    if m + 1.96 * se < 0:
        estimator = "empirical"
    elif m - 1.96 * se > 0:
        estimator = "chain"
    else:
        estimator = "empirical"
    md += [
        f"Empirical minus chain, paired over conversations: **{m:+.4f} ± {1.96 * se:.4f}**. "
        + (
            f"The interval excludes zero: **{estimator}** is better."
            if abs(m) > 1.96 * se
            else "The interval includes zero: **empirical** (decision 4: it needs no assumption, and says thin honestly)."
        ),
        "",
    ]
    prior = best[estimator]
    # min_support
    md += [
        f"## min_support: Brier of {estimator} (prior {prior:g}), against the coverage",
        "",
        "| min_support | Brier | coverage |",
        "|---|---|---|",
    ]
    ms_result = {}
    for ms in (1, 3, 5, 10, 20):
        p = {**p0, "prior": prior, "good_rating": best_rating}
        rows = score(s, p, ms, tuning, data, found, arms=("global rate", estimator))
        sub = [r for r in rows if r["arm"] == estimator]
        ms_result[ms] = (brier(sub), coverage(rows, estimator))
        md.append(f"| {ms} | {ms_result[ms][0]:.4f} | {ms_result[ms][1]:.0%} |")
    top = min(ms_result[ms][0] for ms in (3, 5, 10))
    chosen_ms = min(ms for ms in (3, 5, 10) if ms_result[ms][0] <= top + 0.002)
    md += ["", f"Best of 3, 5 and 10: {top:.4f}; the smallest within 0.002 of it: **{chosen_ms}**.", ""]
    md += [
        "## The settings the rules choose",
        "",
        f"`process.absorb.good_rating: {best_rating}`, `prior: {prior:g}`, `estimator: {estimator}`, `process.min_support: {chosen_ms}`.",
    ]
    record = {
        "good_rating": best_rating,
        "prior": prior,
        "estimator": estimator,
        "min_support": chosen_ms,
        "by_prior": {str(k): v["brier"] for k, v in results.items()},
    }
    print(write_result("process_absorb_grid", md, record))
    print("\n".join(md))


if __name__ == "__main__":
    main()

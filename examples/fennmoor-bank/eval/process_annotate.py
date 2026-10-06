"""Process graph, phase 1 (plans/2026-10-05-text-graph-construction.md): annotate one call per turn, or one per conversation?

Reads the two annotation runs `qlsc process annotate --unit turn|conversation --limit N` wrote (work/process/), the events, and the
corpus's answer key (which the tool never reads; this evaluation may). Compares the units on:
  cost and time, projected to the full corpus from the measured tokens and seconds;
  agreement: the cosine between the two units' descriptions of the same turn;
  leakage: a State described from the turns so far must not use words that appear only in later turns (the per-turn unit cannot;
    any excess in the per-conversation unit is the future leaking back);
  separation: how well the descriptions tell the planted actions apart (Action), and the planted problem and stage (State):
    the chance that two descriptions of the same planted label are more alike than two of different labels (an AUC; 0.5 is chance).
It judges nothing alone: the abstraction scores of phase 3 are the real test. Writes results/process_annotate.md and .json.

Usage: uv run examples/fennmoor-bank/eval/process_annotate.py
"""

from __future__ import annotations

import gzip
import json
import re
from collections import defaultdict
from statistics import median

from common import BUILD, settings, write_result

from qlsc.llm import Embedder

FULL_TURNS = 19360  # the demo corpus (qlsc process read)
FULL_CONVERSATIONS = 2032


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5))


def auc(vectors: list[list[float]], labels: list[str]) -> tuple[float, int]:
    """P(a same-label pair is more alike than a different-label pair), over all pairs (ties count half)."""
    same, diff = [], []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            (same if labels[i] == labels[j] else diff).append(cosine(vectors[i], vectors[j]))
    if not same or not diff:
        return float("nan"), len(same)
    diff.sort()
    from bisect import bisect_left, bisect_right

    wins = sum(bisect_left(diff, x) + 0.5 * (bisect_right(diff, x) - bisect_left(diff, x)) for x in same)
    return wins / (len(same) * len(diff)), len(same)


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{5,}", text.lower()))


def read(path):
    return [json.loads(line) for line in open(path)]


def main() -> None:
    s = settings()
    work = s.work / "process"
    runs = {u: read(work / f"annotations-{u}.ndjson") for u in ("turn", "conversation")}
    manifests = {u: json.loads((work / f"annotations-{u}.json").read_text()) for u in runs}
    by = {u: {r["event"]: r for r in rows} for u, rows in runs.items()}
    events = {}
    with gzip.open(BUILD / "corpus" / "full" / "events.ndjson.gz", "rt") as f:
        for line in f:
            e = json.loads(line)
            events[e["event_id"]] = e
    truth = {}
    with gzip.open(BUILD / "corpus" / "full" / "truth.ndjson.gz", "rt") as f:
        for line in f:
            t = json.loads(line)
            for e in t["events"]:
                truth[e["event_id"]] = {**e, "domain": t["domain"], "cause": t["cause"]}

    emb = Embedder(s)
    ids = sorted(by["turn"])
    vec = {
        u: dict(zip(ids, emb.embed([by[u][i]["description"] or "-" for i in ids]), strict=True)) for u in by
    }

    # --- cost and time, projected ----------------------------------------------------------------------------------------
    cost = {}
    for u, m in manifests.items():
        per = m["cost"] / m["turns"]
        cost[u] = {
            "calls": m["calls"],
            "cost": m["cost"],
            "per_turn": per,
            "full_corpus": per * FULL_TURNS,
            "wall_seconds": m["wall_seconds"],
            "api_seconds_per_turn": m["api_seconds"] / m["turns"],
            "problems": m["problems"],
            "turns": m["turns"],
        }

    # --- agreement ---------------------------------------------------------------------------------------------------------
    agree = {"state": [], "action": []}
    for i in ids:
        agree[by["turn"][i]["kind"]].append(cosine(vec["turn"][i], vec["conversation"][i]))

    # --- leakage: words in a State that appear only in turns after it ----------------------------------------------------
    turns_of = defaultdict(list)
    for i in ids:
        turns_of[by["turn"][i]["conversation"]].append(i)
    leak = {}
    for u in by:
        hits = total = 0
        for evs in turns_of.values():
            evs.sort(key=lambda i: by["turn"][i]["seq"])
            texts = [events[i]["text"] for i in evs]
            for k, i in enumerate(evs):
                if by[u][i]["kind"] != "state":
                    continue
                past, future = words(" ".join(texts[: k + 1])), words(" ".join(texts[k + 1 :]))
                ahead = (words(by[u][i]["description"]) - past) & future
                total += 1
                hits += bool(ahead)
        leak[u] = {"states": total, "with_future_words": hits, "share": hits / total}

    # --- separation by planted label ----------------------------------------------------------------------------------------
    sep = {}
    for u in by:
        acts = [i for i in ids if by[u][i]["kind"] == "action" and i in truth and by[u][i]["description"]]
        keys = [truth[i]["action"] or truth[i]["role"] for i in acts]
        sts = [i for i in ids if by[u][i]["kind"] == "state" and i in truth and by[u][i]["description"]]
        sep[u] = {
            "action vs the planted action": auc([vec[u][i] for i in acts], keys),
            "state vs the planted domain": auc([vec[u][i] for i in sts], [truth[i]["domain"] for i in sts]),
            "state vs the planted stage": auc(
                [vec[u][i] for i in sts], [str(truth[i]["stage"]) for i in sts]
            ),
        }

    # --- what to read -------------------------------------------------------------------------------------------------------
    words_of = {
        u: median(len(by[u][i]["description"].split()) for i in ids if by[u][i]["kind"] == "state")
        for u in by
    }

    md = [
        "# Process graph, phase 1: one call per turn, or one per conversation",
        "",
        f"{len(turns_of)} conversations, {len(ids)} turns, annotated by {manifests['turn']['model']}. Reference: one call per turn from the "
        "turns so far. Candidate: one call per conversation, told to annotate each turn from the turns up to it.",
        "",
        "| | per turn | per conversation |",
        "|---|---|---|",
        f"| calls | {cost['turn']['calls']} | {cost['conversation']['calls']} |",
        f"| cost for these | ${cost['turn']['cost']:.2f} | ${cost['conversation']['cost']:.2f} |",
        f"| projected, {FULL_CONVERSATIONS:,} conversations | ${cost['turn']['full_corpus']:.0f} | ${cost['conversation']['full_corpus']:.0f} |",
        f"| wall seconds (concurrency {s['llm']['concurrency']}) | {cost['turn']['wall_seconds']} | {cost['conversation']['wall_seconds']} |",
        f"| turns with an unresolved problem | {cost['turn']['problems']} | {cost['conversation']['problems']} |",
        f"| median words in a State | {words_of['turn']} | {words_of['conversation']} |",
        "",
        "## Do the two units describe a turn the same way?",
        "",
        f"Cosine between the two descriptions of the same turn ({s['embeddings']['deployment']}, {s['embeddings']['dimensions']} dimensions): "
        f"Actions median {median(agree['action']):.3f} (lowest tenth {sorted(agree['action'])[len(agree['action']) // 10]:.3f}), "
        f"States median {median(agree['state']):.3f} (lowest tenth {sorted(agree['state'])[len(agree['state']) // 10]:.3f}).",
        "",
        "## Does the future leak into a State?",
        "",
        "Share of States that use a word (five letters or more) which is in no turn up to theirs and is in a later turn:",
        "",
        "| | States | with a future word | share |",
        "|---|---|---|---|",
        *[
            f"| per {u} | {v['states']} | {v['with_future_words']} | {100 * v['share']:.0f}% |"
            for u, v in leak.items()
        ],
        "",
        "## Do the descriptions tell the planted labels apart?",
        "",
        "The chance that two descriptions with the same planted label are more alike than two with different labels (0.5 is chance, 1 perfect).",
        "",
        "| | per turn | per conversation | same-label pairs |",
        "|---|---|---|---|",
        *[
            f"| {k} | {sep['turn'][k][0]:.3f} | {sep['conversation'][k][0]:.3f} | {sep['turn'][k][1]} |"
            for k in sep["turn"]
        ],
    ]
    data = {
        "cost": cost,
        "agreement": {k: {"median": median(v), "n": len(v)} for k, v in agree.items()},
        "leak": leak,
        "separation": {
            u: {k: {"auc": a, "same_pairs": n} for k, (a, n) in v.items()} for u, v in sep.items()
        },
    }
    print(write_result("process_annotate", md, data))
    print("\n".join(md))


if __name__ == "__main__":
    main()

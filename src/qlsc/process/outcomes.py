"""Outcomes: how each conversation ended, and the kinds of outcome there are (plans/2026-10-06-process-abstraction.md, phase 2).

The States and Actions never see how a case ends: a closing line ends a good call and a bad one alike, and the agent's after-call note, which
says what was done and how it came out, is excluded from every State because it would carry the outcome into each one. The outcome reads
exactly that:

  1. describe  one cheap call per conversation reads the end of the conversation and the agent's note and says how it ended in a sentence or
               two, with a rating from 1 to 5 (strict structured output, cached by request, a failing answer recorded and never fatal);
  2. group     each description is embedded and grouped by the first level's own neighbours and seeded Leiden (GDS, scratch nodes: a
               conversation is not a node); a kind with fewer than `min_type` conversations is folded into its nearest;
  3. name      an LLM names each kind from the descriptions closest to its middle.

So **the vocabulary of outcomes is discovered, not given**. What it is made of is judged against the planted outcomes by the evaluation
(eval/process_outcomes.py); nothing here reads an answer key. The result is two files beside the build, `outcomes.ndjson` (a kind and a rating
per conversation) and `outcome_types.json` (the vocabulary), which phase 3 turns into odds on the States.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import anthropic

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, check_name, cosine, name_all, prompt
from qlsc.process import build, source
from qlsc.process.source import Turn

SCHEMA = {
    "type": "object",
    "required": ["outcome", "rating"],
    "properties": {"outcome": {"type": "string"}, "rating": {"type": "integer"}},
}
RATINGS = range(1, 6)


def ending(turns: list[Turn], last: int) -> str:
    """The last turns, each by its role: how the conversation was left."""
    return "\n".join(f"{t.role.capitalize()}: {t.text}" for t in turns[-last:])


def problems(a: dict) -> list[str]:
    out = []
    if not a["outcome"].strip():
        out.append("outcome is empty")
    if a["rating"] not in RATINGS:
        out.append("rating must be a whole number from 1 to 5")
    return out


def describe_one(llm: LLM, s: Settings, conversation: str, turns: list[Turn], note: str) -> dict:
    ask = prompt(
        "process_outcome",
        ending=ending(turns, s["process"]["outcomes"]["last_turns"]),
        note=note or "(no note)",
    )
    why: list[str] = []
    a: dict = {}
    for attempt in range(2):
        try:
            a = llm.call(
                ask if not why else ask + f"\nYour last answer was rejected: {'; '.join(why)}.\n",
                SCHEMA,
                max_tokens=400,
            )
        except (
            RuntimeError,
            anthropic.APIError,
        ) as e:  # a request the API refuses fails that conversation, never the pass
            why = [f"no answer: {e}"]
            continue
        why = problems(a)
        if not why:
            return {
                "conversation": conversation,
                "description": a["outcome"].strip(),
                "rating": a["rating"],
                "attempts": attempt + 1,
                "problems": [],
            }
    return {
        "conversation": conversation,
        "description": (a.get("outcome") or "").strip(),
        "rating": a.get("rating"),
        "attempts": 2,
        "problems": why,
    }


def describe(s: Settings, limit: int | None, model: str | None) -> tuple[list[dict], dict]:
    src = source.read(s)
    notes = source.notes(s)
    ids = [c for c in src.conversations if src.conversations[c]]
    ids = ids[:limit] if limit else ids
    llm = LLM(
        prompt("process_outcome_system", **s.business),
        s,
        s["llm"]["query_model"] if model == "query" else model,
    )
    done, lock, t0 = [0], threading.Lock(), time.time()

    def one(c: str) -> dict:
        r = describe_one(llm, s, c, src.conversations[c], notes.get(c, ""))
        with lock:
            done[0] += 1
            if done[0] % 200 == 0 or done[0] == len(ids):
                print(f"  {done[0]}/{len(ids)} conversations, {time.time() - t0:.0f} s", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=s["llm"]["concurrency"]) as pool:
        rows = list(pool.map(one, ids))
    return rows, {
        "calls": llm.calls,
        "cached": llm.cached,
        "cost": llm.cost() or 0.0,
        "model": llm.model,
        "seconds": round(time.time() - t0, 1),
    }


# ------------------------------------------------------------------------------------------------------------------ group


def unit_vectors(s: Settings, rows: list[dict]) -> dict[str, list[float]]:
    emb = Embedder(s)
    texts = [r["description"] for r in rows]
    return {r["conversation"]: build.unit(v) for r, v in zip(rows, emb.embed(texts), strict=True)}


def group(
    s: Settings, G: Graph, vec: dict[str, list[float]], params: dict | None = None
) -> dict[str, list[str]]:
    """Kinds of outcome: the descriptions' communities, small ones folded into their nearest. -> {smallest member: members}"""
    p = params or s["process"]["outcomes"]
    ids = sorted(vec)
    try:
        rows = build.neighbours(G, s, "state", ids, vec, k=p["neighbours"], cut=p["similarity"])
        groups = build.communities(G, s, "state", rows, gamma=p["gamma"])
    finally:
        G.delete(build.IS_SCRATCH)
    big = {k: ms for k, ms in groups.items() if len(ms) >= p["min_type"]}
    if not big:
        return groups
    centres = {k: build.centre(ms, vec) for k, ms in big.items()}
    for k, ms in sorted(groups.items()):
        if k not in big:  # too few for odds worth reading: folded into the nearest kind
            near = max(sorted(centres), key=lambda b: cosine(centres[b], build.centre(ms, vec)))
            big[near] = sorted(big[near] + ms)
    return {min(ms): sorted(ms) for ms in big.values()}


# -------------------------------------------------------------------------------------------------------------------- name


def name_types(
    s: Settings, groups: dict[str, list[str]], by: dict[str, dict], vec: dict[str, list[float]]
) -> tuple[dict[str, dict], LLM]:
    p = s["process"]
    llm = LLM(prompt("process_outcome_name_system", **s.business), s, s["llm"]["query_model"])
    keys = sorted(groups)
    ids = {k: f"O{n}" for n, k in enumerate(keys, 1)}

    def evidence(k: str) -> str:
        ms = groups[k]
        near = build.closest(ms, vec, p["name_evidence"])
        mean = sum(by[m]["rating"] for m in ms) / len(ms)
        lines = "\n".join(f"- {by[m]['description']}" for m in near)
        return f"[{ids[k]}] {len(ms)} conversations, average rating {mean:.1f}. Closest to the middle:\n{lines}\n\n"

    named = name_all(
        llm,
        {ids[k]: evidence(k) for k in keys},
        ("outcome", "outcomes"),
        p["name_batch"],
        check=lambda i: check_name(i, words=(2, 8), chars=(15, 500)),
    )
    return {k: named[ids[k]] for k in keys}, llm


# --------------------------------------------------------------------------------------------------------------------- run


def run(s: Settings, limit: int | None = None, model: str | None = None) -> dict:
    rows, desc = describe(s, limit, model)
    good = [r for r in rows if r["description"] and not r["problems"]]
    out = s.work / "process"
    out.mkdir(parents=True, exist_ok=True)
    vec = unit_vectors(s, good)
    by = {r["conversation"]: r for r in good}
    with Graph(s, {"database": s["process"]["database"]}) as G:
        groups = group(s, G, vec)
    named, llm = name_types(s, groups, by, vec)
    types, assigned = [], {}
    for k, ms in sorted(groups.items()):
        n = named[k]
        name = n["name"] if n["status"] != "failed" else "Outcome " + by[k]["description"][:40]
        tid = "outcome:" + hashlib.sha1("|".join(ms).encode()).hexdigest()[:12]
        mean = sum(by[m]["rating"] for m in ms) / len(ms)
        types.append(
            {
                "id": tid,
                "name": name,
                "description": n.get("description", ""),
                "count": len(ms),
                "rating": round(mean, 3),
                "named_by": llm.model,
            }
        )
        assigned.update({m: tid for m in ms})
    with open(out / "outcomes.ndjson", "w") as f:
        for r in rows:
            f.write(json.dumps({**r, "type": assigned.get(r["conversation"])}, sort_keys=True) + "\n")
    types.sort(key=lambda t: (-t["count"], t["id"]))
    (out / "outcome_types.json").write_text(json.dumps(types, indent=1))
    return {
        "conversations": len(rows),
        "failed": len(rows) - len(good),
        "types": types,
        "describe": desc,
        "naming": llm.summary(),
        "cost": desc["cost"] + (llm.cost() or 0.0),
    }


def report(s: Settings, limit: int | None, model: str | None) -> None:
    m = run(s, limit, model)
    d = m["describe"]
    print(
        f"{m['conversations']} conversations described by {d['model']}: {d['calls']} calls, {d['cached']} cached, ${d['cost']:.2f}, {d['seconds']} s; {m['failed']} failed"
    )
    print(f"{len(m['types'])} kinds of outcome (naming: {m['naming']}):")
    for t in m["types"]:
        print(f"  {t['count']:>5}  rating {t['rating']:.1f}  {t['name']}")
    print(f"wrote {s.work}/process/outcomes.ndjson and outcome_types.json")

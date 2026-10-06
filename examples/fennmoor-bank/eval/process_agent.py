"""Process abstraction, phase 5 (plans/2026-10-06-process-abstraction.md): does the outlook help an agent choose the next action?

An LLM agent (the query model) is shown a call part-way through and the menu of actions the procedure allows, and picks the one the representative should
take next. The same sampled decision points are put to it with different things beside the call (arms):

  alone                  the call and the menu
  outlook                + what `qlsc process outlook` says (nearest States, the odds, what reps did next and how those cases ended), from counts with
                           the conversation taken out, exactly as the tool returns it (without its recommendation)
  call record            + the phone system's record of the call as of the call: whether the caller was already authenticated, and the menu choice
  fees and purchases     + what the bank held on the customer's account: the fees in the prior 60 days and the card purchases in the prior 30
  context (both)          (the corpus's pool rows, from the warehouse's own tables: the call record and the account facts together)
  knowledge              + how the process works: the causes the procedure can draw, how each shows in a call, which question asks for each clue, and
                           what fixes, partly helps or worsens each (the world's own tables, given as a designed ontology: an experiment, not what the
                           tool has)
  context + knowledge, all three

Each choice is scored against the answer key (which the agent never sees) the way the outlook's recommendations were: a remedy that fixes the real cause, or a
question for a clue that is true and not yet said, is useful; a remedy that does nothing, or makes it worse, is not. Against the rep's own action at the point,
the typical rep's (what reps most often did), chance, and the best single action with hindsight. Points: holdout conversations, one point each, half where a
true clue is still waiting and half where none is. Paired: against the agent alone, a sign test over the points where they differ.

Writes results/process_agent.md and .json. Usage: uv run examples/fennmoor-bank/eval/process_agent.py [--points N] (default 200)
"""

from __future__ import annotations

import gzip
import json
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from math import comb
from pathlib import Path

import process_graph as pg
import process_outlook as po
from common import BUILD, settings, write_result

from qlsc.llm import LLM
from qlsc.process import build, outlook, source

ARMS = {
    "alone": (),
    "outlook": ("outlook",),
    "call record": ("call",),
    "fees and purchases": ("account",),
    "context (both)": ("call", "account"),
    "knowledge": ("knowledge",),
    "context + knowledge": ("call", "account", "knowledge"),
    "all three": ("outlook", "call", "account", "knowledge"),
}
BLOCKS = ("outlook", "call", "account", "knowledge")
SEED = 11
HERE_PROMPTS = Path(__file__).resolve().parent / "prompts"
FEES_DAYS, PURCHASE_DAYS = 60, 30


def text(name: str, **values) -> str:
    return (HERE_PROMPTS / f"{name}.md").read_text().format(**values)


# --------------------------------------------------------------------------------------------------------------------- the points


def pool_rows(convs: set[str]) -> dict[str, dict]:
    out = {}
    with gzip.open(BUILD / "corpus" / "pool.ndjson.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            if r["conversation_id"] in convs:
                out[r["conversation_id"]] = r
    return out


def sample(d: po.Data, n: int) -> list[dict]:
    """One decision point per holdout conversation, half with a true clue waiting and half without, in a fixed random order."""
    rng = random.Random(SEED)
    convs = sorted(d.holdout)
    rng.shuffle(convs)
    quota = {"a clue is waiting": n // 2, "no clue waiting": n - n // 2}
    out = []
    for c in convs:
        if c not in d.truth:
            continue
        pts = [(s, a) for s, a in d.points(c) if s in d.planted.unbrought and s in d.located]
        if not pts:
            continue
        s_event, a_event = pts[rng.randrange(len(pts))]
        kind = "a clue is waiting" if d.planted.unbrought[s_event] else "no clue waiting"
        if quota[kind] <= 0:
            continue
        quota[kind] -= 1
        out.append({"conversation": c, "state_event": s_event, "action_event": a_event, "pending": kind})
        if not any(quota.values()):
            break
    return out


# ------------------------------------------------------------------------------------------------------------------------ the arms


def call_text(turns: list[source.Turn], state_event: str) -> str:
    upto = next(i for i, t in enumerate(turns) if t.event == state_event)
    return "\n".join(f"{t.role.capitalize()}: {t.text}" for t in turns[: upto + 1])


def menu_text(w, actions: list[str]) -> str:
    return "\n".join(f"- {a}: {w.actions[a]['label']}" for a in actions)


def call_block(row: dict) -> str:
    return (
        "\nThe phone system's record of this call, as of the call:\n"
        f"- The caller was {'already authenticated' if row['is_authenticated'] else 'not authenticated'} (result {row['ivr_auth_result']}); "
        f"the menu choice was {row['ivr_intent']}\n"
    )


def account_block(row: dict) -> str:
    fees = [
        f"{f['fee_type']} fee of {f['fee_amount']:.2f} on {f['assessed_date']} ({f['product_code']})"
        for f in row["fees"]
    ]
    buys = [
        ", ".join(f"{k} {v}" for k, v in sorted(p.items()) if v not in (None, "")) for p in row["purchases"]
    ]
    return (
        f"\nWhat the bank holds about this customer's account, as of the call:\n- Fees in the last {FEES_DAYS} days: "
        + ("; ".join(fees) if fees else "none")
        + f"\n- Card purchases in the last {PURCHASE_DAYS} days: "
        + ("; ".join(buys) if buys else "none")
        + "\n"
    )


def knowledge_block(w, procedure: str) -> str:
    actions = w.procedure_actions(procedure)
    lines = ["\nHow this process works (the causes a case can have, how each shows, and what addresses it):"]
    for cid in w.procedures[procedure]["hypotheses"]:
        c = w.causes[cid]
        clues = []
        for m in c["manifestations"]:
            info = w.manifestations[m["id"]]
            ask = w.elicitor.get(m["id"])
            clues.append(
                f"{info['label']} ({m['probability']:.0%}"
                + (f"; ask: {w.actions[ask]['label']}" if ask and not info.get("presenting") else "")
                + ")"
            )
        by: dict[str, list[str]] = defaultdict(list)
        for a in actions:
            eff = w.effect(a, cid)
            if eff != "no-effect":
                by[eff].append(w.actions[a]["label"])
        lines.append(
            f"- {c['label']}. Shows as: {'; '.join(clues)}. "
            + "".join(f"{k.replace('-', ' ')}: {', '.join(v)}. " for k, v in sorted(by.items()))
        )
    return "\n".join(lines) + "\n"


def outlook_block(
    d: po.Data, counts, base: float, p: dict, ap: dict, floor: int, event: str, turn_seq: int, desc: str
) -> str:
    loc = d.located[event]
    stats = outlook.stats_from_counts(counts, [i for i, _ in loc[: p["states"]]], names=d.names, base=base)
    out = outlook.pool(stats, loc, p, floor, ap["prior"])
    out.pop("recommended")
    o = {
        "turn": turn_seq,
        "state": desc,
        "located": [
            {
                "id": i,
                "name": stats.state[i]["name"],
                "similarity": round(x, 3),
                "support": stats.state[i]["n"],
            }
            for i, x in loc[: p["states"]]
            if i in stats.state
        ],
        "outlook": out,
        "measured": {},
    }
    v = outlook.view(o, p["actions_shown"])
    v.pop("measured")
    return (
        "\nWhat the process graph says about cases like this one (observations of past calls, not advice):\n"
        + json.dumps(v, indent=1)
        + "\n"
    )


# ----------------------------------------------------------------------------------------------------------------------- scoring


def sign_p(better: int, worse: int) -> float:
    """Two-sided exact sign test over the points where two arms differ."""
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def main() -> None:
    s = settings()
    n = int(sys.argv[sys.argv.index("--points") + 1]) if "--points" in sys.argv else 200
    d = po.Data(s)
    d.names = {}
    from qlsc.graph import Graph

    with Graph(s, {"database": s["process"]["database"]}) as G:
        d.names = {
            r["id"]: r["name"]
            for r in G.rows("MATCH (n) WHERE n:State OR n:Action RETURN n.id AS id, n.name AS name")
        }
    p, ap, floor = s["process"]["outlook"], s["process"]["absorb"], s["process"]["min_support"]
    w = d.world
    pts = sample(d, n)
    src = source.read(s)
    pool = pool_rows({x["conversation"] for x in pts})
    annotations = {r["event"]: r for r in build.load(s) if r["kind"] == "state"}
    counts, by, of = d.counts(p["level"])
    names = pg.element_labels(d.planted, d.obs, of)
    # what each arm is shown, per point; the counts have the conversation taken out while its outlook is made
    for x in pts:
        c = x["conversation"]
        truth, plan = d.truth[c], d.planted.plans[c]
        turns = src.conversations[c]
        counts.add(by[c], -1)
        base = outlook.base_of(counts)
        ev = x["state_event"]
        x["procedure"] = plan["procedure"]
        x["avail"] = w.procedure_actions(plan["procedure"])
        x["unbrought"] = sorted(d.planted.unbrought[ev])
        x["blocks"] = {
            "outlook": outlook_block(
                d,
                counts,
                base,
                p,
                ap,
                floor,
                ev,
                next(t.seq for t in turns if t.event == ev),
                annotations[ev]["description"],
            ),
            "call": call_block(pool[c]),
            "account": account_block(pool[c]),
            "knowledge": knowledge_block(w, plan["procedure"]),
        }
        loc = d.located[ev]
        pooled = outlook.pool(
            outlook.stats_from_counts(counts, [i for i, _ in loc[: p["states"]]], names=d.names, base=base),
            loc,
            p,
            floor,
            ap["prior"],
        )
        x["graph"] = names.get((pooled["recommended"] or {}).get("action"))
        x["common"] = names.get((pooled["most_common"] or {}).get("action"))
        counts.add(by[c], 1)
        x["call"] = call_text(turns, ev)
        x["rep"] = d.planted.action.get(x["action_event"])
    llm = LLM(text("agent_next_action_system", **s.business), s, s["llm"]["query_model"])
    jobs = [(i, arm) for i in range(len(pts)) for arm in ARMS]
    done, t0 = [0], time.time()

    def one(job: tuple[int, str]) -> tuple[int, str, dict]:
        i, arm = job
        x = pts[i]
        extra = "".join(x["blocks"][b] for b in BLOCKS if b in ARMS[arm])
        ask = text("agent_next_action", call=x["call"], menu=menu_text(w, x["avail"]), extra=extra)
        schema = {
            "type": "object",
            "required": ["action", "reason"],
            "properties": {"action": {"type": "string", "enum": x["avail"]}, "reason": {"type": "string"}},
        }
        a = llm.call(ask, schema, max_tokens=600)
        done[0] += 1
        if done[0] % 100 == 0:
            print(f"  {done[0]}/{len(jobs)} calls, {time.time() - t0:.0f} s", flush=True)
        return i, arm, a

    with ThreadPoolExecutor(max_workers=s["llm"]["concurrency"]) as pool_:
        got = list(pool_.map(one, jobs))
    for i, arm, a in got:
        pts[i].setdefault("choice", {})[arm] = a["action"]
    for x in pts:
        truth, unb = d.truth[x["conversation"]], set(x["unbrought"])
        cls = lambda a, truth=truth, unb=unb: po.classify(w, truth, a, unb) if a else None  # noqa: E731
        x["class"] = {arm: cls(a) for arm, a in x["choice"].items()}
        x["class"]["the rep"] = cls(x["rep"])
        x["class"]["the typical rep"] = cls(x["common"])
        x["class"]["the graph's best ending"] = cls(x["graph"])
        x["useful_actions"] = [a for a in x["avail"] if po.classify(w, truth, a, unb) in po.USEFUL]
        x["chance"] = len(x["useful_actions"]) / len(x["avail"])

    rows = [*ARMS, "the rep", "the typical rep", "the graph's best ending"]
    groups = [
        ("all points", pts),
        *[(k, [x for x in pts if x["pending"] == k]) for k in ("a clue is waiting", "no clue waiting")],
    ]

    def useful(sub, arm):
        return sum(1 for x in sub if x["class"][arm] in po.USEFUL), len(sub)

    md = [
        "# Process abstraction, phase 5: does the outlook help an agent choose?",
        "",
        f"{len(pts)} decision points, one per holdout conversation, half where a true clue is waiting and half where none is. Each is put to {llm.model} with the call so far and the "
        f"menu of the procedure's actions, with different things beside it. Useful: a remedy that fixes the real cause, or a question for a true, unsaid clue (the answer key's view; "
        f"the agent never sees it). The outlook and the context are what the tool and the warehouse hold with the conversation taken out; the knowledge is the world's own tables as a designed ontology (an experiment).",
        "",
        "| | " + " | ".join(f"{name} (n={len(sub)})" for name, sub in groups) + " |",
        "|---|" + "---|" * len(groups),
    ]
    for arm in rows:
        md.append(f"| {arm} | " + " | ".join(po.pct(useful(sub, arm)) for _, sub in groups) + " |")
    md.append(
        "| chance, among the procedure's actions | "
        + " | ".join(f"{sum(x['chance'] for x in sub) / len(sub):.0%}" for _, sub in groups)
        + " |"
    )
    hs = [po.hindsight(sub) for _, sub in groups]
    md.append(
        "| the best single action, with hindsight | "
        + " | ".join(f"{h[1]:.0%} ({h[0].replace('ACT-', '') if h[0] else '-'})" for h in hs)
        + " |"
    )
    md += [
        "",
        "What each arm chooses, as a share of all points:",
        "",
        "| class | " + " | ".join(rows) + " |",
        "|---|" + "---|" * len(rows),
    ]
    for cls in po.CLASSES:
        md.append(
            f"| {cls} | "
            + " | ".join(f"{sum(1 for x in pts if x['class'][a] == cls) / len(pts):.0%}" for a in rows)
            + " |"
        )
    md += [
        "",
        "Paired against the agent alone (points where one is useful and the other is not; two-sided sign test):",
        "",
        "| arm | better | worse | p |",
        "|---|---|---|---|",
    ]
    record = {"points": len(pts)}
    for arm in list(ARMS)[1:] + ["the rep"]:
        better = sum(1 for x in pts if x["class"][arm] in po.USEFUL and x["class"]["alone"] not in po.USEFUL)
        worse = sum(1 for x in pts if x["class"][arm] not in po.USEFUL and x["class"]["alone"] in po.USEFUL)
        md.append(f"| {arm} | {better} | {worse} | {sign_p(better, worse):.3f} |")
        record[arm] = [better, worse]
    md += [
        "",
        f"{len(jobs)} calls, {llm.calls} made and {llm.cached} from the cache, ${llm.cost() or 0:.2f}, {time.time() - t0:.0f} s.",
    ]
    record["useful"] = {a: {g: useful(sub, a) for g, sub in groups} for a in rows}
    record["points_detail"] = [{k: v for k, v in x.items() if k not in ("blocks", "call")} for x in pts]
    print(write_result("process_agent", md, record))
    print("\n".join(md))


if __name__ == "__main__":
    main()

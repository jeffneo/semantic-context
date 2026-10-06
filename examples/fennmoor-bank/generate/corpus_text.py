"""Phase B of the process corpus: render each plan as event objects. The model chooses words. It does not choose what happens.

Plan: plans/2026-10-05-process-corpus.md. The boundary is structural, not a request: this module computes the exact skeleton of a
conversation in Python (who speaks, in what order, in response to what, carrying which fact from the plan), and the model fills in
the text of each numbered slot. It cannot add a turn, drop one, reorder them, or resolve anything the plan does not resolve,
because there is nowhere for that to go in the output. `corpus_check` then checks every slot came back once, that nothing the plan
left unsaid was said, and that no step the agent skipped (a verification, an offer) appears anyway.

Prompts are files (`generate/prompts/`), loaded here; the per-slot wording and the variety are in `styles.yaml`. The LLM client is
qlsc's (cached by the full request in work/llm_cache), so a rerun over the same plans costs nothing.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import yaml
from corpus_check import as_utc, check, event_problems
from corpus_world import World

HERE = Path(__file__).resolve().parent
PROMPTS = HERE / "prompts"
STYLES = yaml.safe_load((PROMPTS / "styles.yaml").read_text())
SCHEMA = {
    "type": "object",
    "required": ["turns"],
    "properties": {
        "turns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["slot", "text"],
                "properties": {"slot": {"type": "integer"}, "text": {"type": "string"}},
            },
        }
    },
}
MANIFESTATION_OF_FEE = {"MAN-RET-FEE-ON-STATEMENT", "MAN-PAY-FEE-ON-STATEMENT"}
MANIFESTATION_OF_PURCHASE = {"MAN-DSP-CHARGE-NAMED"}
SCRIPTED = {
    "queue": "Customer disconnected before an agent connected.",
    "chat_queue": "Chat abandoned before an agent joined.",
}


def load_prompt(name: str, **values) -> str:
    return (PROMPTS / f"{name}.md").read_text().format(**values)


# --------------------------------------------------------------------------------------------------------------- the facts


def surfaced(w: World, plan: dict) -> set[str]:
    """What was brought up in this conversation: the opener, what was volunteered, what a question retrieved."""
    out = {plan["world"]["opener"], *plan["world"]["volunteered"]}
    for s in plan["steps"]:
        out.update(s.get("reveals") or [])
    return {m for m in out if m}


def asked_about(w: World, plan: dict) -> set[str]:
    """The manifestations the agent's own questions are about: the agent may name them, whatever the answer."""
    return {
        w.actions[s["action"]]["elicits"]
        for s in plan["steps"]
        if s.get("action") and w.actions[s["action"]].get("elicits")
    }


def facts(w: World, plan: dict, seen: set[str]) -> dict | None:
    """The real fee or purchase the conversation is about, if the cause needs one and the customer got to it."""
    needs = w.causes[plan["cause"]].get("needs", {})
    if "fee_unwaived_prior_days" in needs and seen & MANIFESTATION_OF_FEE and plan["mentions"]["fees"]:
        fee = plan["mentions"]["fees"][0]
        return {
            "kind": "fee",
            "fee_id": fee["fee_id"],
            "label": STYLES["fee_labels"].get(fee["fee_type"], "fee"),
            "amount": float(fee["fee_amount"]),
            "date": fee["assessed_date"],
        }
    if (
        "card_purchase_prior_days" in needs
        and seen & MANIFESTATION_OF_PURCHASE
        and plan["mentions"]["purchases"]
    ):
        buy = plan["mentions"]["purchases"][0]
        return {
            "kind": "purchase",
            "settlement_id": buy["settlement_id"],
            "merchant_id": buy["merchant_id"],
            "merchant": buy["merchant_name"],
            "category": buy.get("mcc_category_group"),
            "amount": float(buy["amount"]),
            "date": buy["post_date"],
        }
    return None


def facts_line(f: dict | None) -> str:
    if not f:
        return ""
    if f["kind"] == "fee":
        return f"FACTS: the fee is a {f['label']} of ${f['amount']:.2f}, charged on {f['date']}. Use it where the fee comes up.\n"
    return (
        f"FACTS: the charge is ${f['amount']:.2f} at {f['merchant']} ({f['category'] or 'retail'}), posted {f['date']}. "
        "Use the merchant and amount where the charge comes up.\n"
    )


# ------------------------------------------------------------------------------------------------------------- the skeleton


def build_skeleton(w: World, plan: dict, seen: set[str], mood: str, closing_style: str) -> list[dict]:
    """The exact sequence of things said. Slot roles are keyed to styles.yaml."""
    slots: list[dict] = []

    def add(speaker: str, role: str, step: int | None = None, **extra) -> None:
        slots.append({"slot": len(slots), "speaker": speaker, "role": role, "step": step, **extra})

    label = lambda mid: w.manifestations[mid]["label"].rstrip(".")  # noqa: E731
    open_step = plan["steps"][0]
    said = [label(m) for m in open_step["volunteers"]]
    claim = label(open_step["false_claim"]) if open_step.get("false_claim") else None
    add("agent", "rep_greeting", 0)
    add(
        "customer",
        "cust_opening",
        0,
        opener=label(open_step["manifestation"])
        + (f", specifically {plan['world']['topic']}" if plan["world"].get("topic") else ""),
        said=(" They also mention: " + "; ".join(said) + ".") if said else "",
        claim=(
            f" They say, confidently, that the cause is: {claim} (it is what they believe, whether or not it is so)."
        )
        if claim
        else "",
    )

    steps = plan["steps"]
    for i, step in enumerate(steps[1:], 1):
        if step["kind"] == "hangup":
            add("customer", "cust_hangup", i)
            continue
        action = step["action"]
        a = w.actions[action]
        before_hangup = i + 1 < len(steps) and steps[i + 1]["kind"] == "hangup"
        reason = step.get("reason", "")
        if "supervisor" in reason:
            add("customer", "cust_demand", i)
        elif "pushes back" in reason:
            add("customer", "cust_pushback", i)
        kind = a["type"]
        if kind == "verify":
            add("agent", "rep_verify", i, label=a["label"].lower())
        elif kind == "check":
            add("agent", "rep_check", i, label=a["label"].lower())
        elif kind == "elicit":
            add("agent", "rep_open" if a.get("elicits_any") else "rep_ask", i, label=a["label"])
        elif kind == "offer":
            add("agent", "rep_offer", i, label=a["label"])
        elif kind == "transfer":
            add("agent", "rep_transfer", i)
        elif kind == "escalate":
            add("agent", "rep_escalate", i, label=a["label"])
        else:
            add("agent", "rep_commit", i, label=a["label"])
        if before_hangup:
            continue
        if kind == "verify":
            add("customer", "cust_verify", i)
        elif kind == "check":
            add("customer", "cust_wait", i)
        elif kind == "elicit" and a.get("elicits_any"):
            got = [label(m) for m in step.get("reveals") or []]
            if got:
                add("customer", "cust_open_reveals", i, list="; ".join(got))
            else:
                add("customer", "cust_open_nothing", i)
        elif kind == "elicit":
            if step.get("answer") == "yes":
                add("customer", "cust_yes", i, about=label(a["elicits"]))
            elif a["elicits"] in plan["world"]["present"]:
                add(
                    "customer", "cust_no_unnoticed", i
                )  # true, and the customer did not notice: not a flat denial
            else:
                add("customer", "cust_no", i)
        elif kind == "offer":
            accepted = plan["retained"] and action == plan["final_action"]
            add("customer", "cust_accept" if accepted else "cust_decline", i)
        elif kind == "transfer":
            add("customer", "cust_ack_transfer", i, mood=mood)
        else:
            add("customer", "cust_react", i, mood=mood)

    # A hang-up, a transfer and an escalation end the agent's part: someone else takes over, or nobody does.
    last = plan["final_action"]
    ended_by = steps[-1]["kind"] == "hangup" or (last and w.actions[last]["type"] in {"transfer", "escalate"})
    if not ended_by:
        add("agent", "rep_closing", None, closing_style=closing_style)
        add("customer", "cust_closing", None)
    did = [w.actions[s["action"]]["label"].lower() for s in steps if s.get("action")]
    result = (
        "the customer kept the account"
        if plan["retained"]
        else (
            w.actions[plan["final_action"]]["label"].lower()
            if plan["final_action"]
            else "the customer hung up"
        )
    )
    add(
        "agent",
        "case_note",
        None,
        said="; ".join(
            [
                label(open_step["manifestation"]),
                *said,
                *[label(m) for s in steps for m in s.get("reveals") or []],
            ]
        ),
        did="; ".join(did),
        result=result,
    )
    return slots


def describe(slot: dict) -> str:
    text = STYLES["slots"][slot["role"]].format(**{k: v for k, v in slot.items() if isinstance(v, str)})
    return f"  {slot['slot']}. {slot['speaker'].upper()}: {text}"


def callback_block(w: World, plan: dict, anchor: dict | None, days: int | None) -> str:
    if not anchor:
        return ""
    when = "earlier the same day" if not days else f"{days} day{'s' if days != 1 else ''} ago"
    last = (
        w.actions[anchor["final_action"]]["label"].lower()
        if anchor.get("final_action")
        else "they gave up and hung up"
    )
    return (
        f"\nTHIS IS A CALLBACK. The same customer was in touch about this {when}, and it was not settled. They open by referring "
        f"to that, and do not describe it from scratch. They are more worn down, and resent being asked what they have already "
        f"answered. Last time: {last}.\n"
    )


# ----------------------------------------------------------------------------------------------------------------- one plan


def style_for(seed: int, plan: dict) -> tuple[str, str]:
    rng = random.Random(f"style:{seed}:{plan['index']}:{plan['conversation_id']}")
    return rng.choice(STYLES["registers"]), rng.choice(STYLES["closings"])


def request_for(w: World, plan: dict, seed: int, anchor: dict | None, days: int | None) -> tuple[str, dict]:
    seen = surfaced(w, plan)
    f = facts(w, plan, seen)
    register, closing = style_for(seed, plan)
    mood = STYLES["moods"][plan["favorability"]]
    skeleton = build_skeleton(w, plan, seen, mood, closing)
    media = plan["row"]["media_type"]
    cust = w.customer_archetypes[plan["customer"]]
    rep = w.rep_archetypes[plan["rep"]]
    text = load_prompt(
        "realise_request",
        channel_style=STYLES["channels"].get(media, STYLES["channels"]["voice"]),
        customer=f"{cust['label']}; starts {cust['initial_sentiment']}.",
        rep=f"{rep['label']}. Warmth {rep['empathy']:.1f} of 1, talkativeness {rep['verbosity']:.1f} of 1.",
        register=register,
        closing_style=closing,
        mood_end=mood,
        facts=facts_line(f),
        callback=callback_block(w, plan, anchor, days),
        slots="\n".join(describe(s) for s in skeleton),
    )
    return text, {
        "skeleton": skeleton,
        "facts": f,
        "surfaced": sorted(seen),
        "register": register,
        "closing": closing,
    }


def stub_turns(skeleton: list[dict]) -> list[dict]:
    """Free placeholder text for tuning the pipeline: the slot's own description, nothing more. It fails the diversity gates by
    construction and exists for timing the builder."""
    return [{"slot": s["slot"], "text": describe(s).split(": ", 1)[1]} for s in skeleton]


CHANNEL = {"voice": "voice_turn", "callback": "voice_turn", "chat": "chat_message", "email": "email"}


def events_for(w: World, plan: dict, skeleton: list[dict], turns: dict[int, str], seed: int) -> list[dict]:
    """Event objects: ids, order, timestamps inside the row's span, the channel and who spoke."""
    row = plan["row"]
    start = as_utc(row["conversation_start"])
    media = row["media_type"]
    rng = random.Random(f"time:{seed}:{plan['conversation_id']}")
    spread = {"voice": (5, 40), "callback": (5, 40), "chat": (15, 120), "email": (300, 3600)}[media]
    gaps = [rng.uniform(*spread) for _ in skeleton]
    span = max(1.0, sum(gaps[:-1]) if len(gaps) > 1 else 1.0)
    budget = 0.9 * (row["handle_sec"] or span)
    scale = min(1.0, budget / span)
    out, t = [], 0.0
    note_gap = rng.uniform(120, 480)
    for i, s in enumerate(skeleton):
        if s["role"] == "case_note":
            ts, channel = start + timedelta(seconds=t + note_gap), "case_note"
        else:
            t += gaps[i] * scale if i else 0.0
            ts, channel = start + timedelta(seconds=t), CHANNEL[media]
        agent = s["speaker"] == "agent"
        out.append(
            {
                "event_id": hashlib.sha1(f"{plan['conversation_id']}|{i}".encode()).hexdigest()[:16],
                "conversation_id": plan["conversation_id"],
                "seq": i,
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "channel": channel,
                "role": s["speaker"] if not agent or s["role"] != "case_note" else "agent",
                "agent_user_id": row["agent_user_id"] if agent else None,
                "text": turns[s["slot"]].strip(),
            }
        )
    return out


def scripted_events(plan: dict, seed: int) -> list[dict]:
    """A conversation that never reached an agent is a system line, not a model's invention."""
    row = plan["row"]
    start = as_utc(row["conversation_start"])
    text = SCRIPTED["chat_queue" if row["media_type"] == "chat" else "queue"]
    return [
        {
            "event_id": hashlib.sha1(f"{plan['conversation_id']}|0".encode()).hexdigest()[:16],
            "conversation_id": plan["conversation_id"],
            "seq": 0,
            "ts": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "channel": "system_log",
            "role": "system",
            "agent_user_id": None,
            "text": text,
        }
    ]


# ------------------------------------------------------------------------------------------------------------------ a run


def realise(
    w: World, settings, plans: list[dict], seed: int, model: str | None, stub: bool, out_dir: Path
) -> dict:
    """Render the plans; write events.ndjson.gz, truth.ndjson.gz and a manifest; return what it took."""
    from qlsc.llm import LLM

    by_index = {p["index"]: p for p in plans if "follow_up_of" not in p}
    gaps = {}
    for p in plans:
        if "follow_up_of" in p:
            a, b = by_index[p["follow_up_of"]], p
            d = as_utc(b["row"]["conversation_start"]) - as_utc(a["row"]["conversation_start"])
            gaps[b["conversation_id"]] = max(0, round(d.total_seconds() / 86400))
    llm = None if stub else LLM(load_prompt("realise_system"), settings, model)

    def one(plan: dict) -> dict:
        if plan["steps"][0]["kind"] == "queue":
            return {
                "plan": plan,
                "events": scripted_events(plan, seed),
                "skeleton": [],
                "meta": {},
                "attempts": 0,
                "problems": [],
            }
        anchor = by_index.get(plan.get("follow_up_of"))
        text, meta = request_for(w, plan, seed, anchor, gaps.get(plan["conversation_id"]))
        problems: list[str] = []
        turns: dict[int, str] = {}
        for attempt in range(2):
            # A retry says what was wrong, and drops the register: an unusual one (a customer who interrupts) is the usual cause.
            ask = text
            if problems:
                ask = text.replace(meta["register"], STYLES["registers"][0]) + (
                    "\nYour last attempt was rejected: " + "; ".join(problems[:4]) + ". Fix exactly that.\n"
                )
            try:
                raw = (
                    stub_turns(meta["skeleton"]) if stub else llm.call(ask, SCHEMA, max_tokens=4000)["turns"]
                )
            except RuntimeError as e:
                problems = [f"no answer: {e}"]
                continue
            turns = {t["slot"]: t["text"] for t in raw}
            # Placeholder text cannot pass the checks on prose (it names no merchant), and they mean nothing for it: only the events are checked.
            problems = [] if stub else check(w, plan, meta, raw, turns, STYLES)
            events = [] if problems else events_for(w, plan, meta["skeleton"], turns, seed)
            problems += event_problems(events, plan) if events else []
            if not problems:
                return {
                    "plan": plan,
                    "events": events,
                    "skeleton": meta["skeleton"],
                    "meta": meta,
                    "attempts": attempt + 1,
                    "problems": [],
                }
        return {
            "plan": plan,
            "events": [],
            "skeleton": meta["skeleton"],
            "meta": meta,
            "attempts": 2,
            "problems": problems,
            # What was rejected, kept for diagnosis: the only way to see why a check keeps failing.
            "rejected": turns,
        }

    workers = 1 if stub else settings["llm"]["concurrency"]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, plans))

    out_dir.mkdir(parents=True, exist_ok=True)
    with (
        gzip.open(out_dir / "events.ndjson.gz", "wt") as events,
        gzip.open(out_dir / "truth.ndjson.gz", "wt") as truth,
    ):
        for r in results:
            for e in r["events"]:
                events.write(json.dumps(e, sort_keys=True) + "\n")
            truth.write(json.dumps(truth_for(w, r), sort_keys=True, default=str) + "\n")
    summary = {
        "conversations": len(results),
        "written": sum(1 for r in results if r["events"]),
        "failed": [(r["plan"]["conversation_id"], r["problems"]) for r in results if not r["events"]],
        "regenerated": sum(1 for r in results if r["attempts"] == 2 and r["events"]),
        "events": sum(len(r["events"]) for r in results),
        "model": None if stub else llm.model,
        "llm": None if stub else llm.summary(),
        "calls": 0 if stub else llm.calls,
        "cached": 0 if stub else llm.cached,
        "tokens": {} if stub else dict(llm.tokens),
    }
    (out_dir / "manifest.json").write_text(json.dumps({**summary, "seed": seed}, indent=1, default=str))
    summary["results"] = results
    return summary


def truth_for(w: World, r: dict) -> dict:
    """The sidecar: the plan, per event the step it realises, and the warehouse entities mentioned. Never read by the builder."""
    plan = r["plan"]
    step_of = {s["slot"]: s for s in r["skeleton"]}
    f = (r["meta"] or {}).get("facts")
    events = []
    for e, s in zip(r["events"], r["skeleton"], strict=False):
        mentioned = []
        low = e["text"].lower()
        if f and f["kind"] == "purchase" and f["merchant"].lower() in low:
            mentioned.append({"type": "Merchant", "key": f["merchant_id"]})
        if f and f["kind"] == "fee" and re.search(rf"\${int(f['amount'])}\b", e["text"]):
            mentioned.append({"type": "Fee", "key": f["fee_id"]})
        step = plan["steps"][s["step"]] if s["step"] is not None else None
        events.append(
            {
                "event_id": e["event_id"],
                "role": s["role"],
                "step": s["step"],
                "action": (step or {}).get("action"),
                "stage": (step or {}).get("stage"),
                "belief": (step or {}).get("belief"),
                "mentions": mentioned,
            }
        )
    del step_of
    keep = (
        "index",
        "conversation_id",
        "domain",
        "procedure",
        "cause",
        "intent",
        "customer",
        "rep",
        "site",
        "authenticated",
        "outcome",
        "favorability",
        "final_action",
        "efficacy",
        "retained",
        "save_attempted",
        "believed_cause",
        "misdiagnosed",
        "abandoned",
        "breaches",
        "gates",
        "recurrence",
        "follow_up_of",
        "world",
        "facts",
    )
    return {
        **{k: plan.get(k) for k in keep},
        "row": plan["row"],
        "fact": f,
        "register": (r["meta"] or {}).get("register"),
        "closing": (r["meta"] or {}).get("closing"),
        "events": events,
        "attempts": r["attempts"],
        "problems": r["problems"],
        "rejected": r.get("rejected"),
    }


def counts(results: list[dict]) -> Counter:
    return Counter(r["attempts"] for r in results)


def render(w: World, results: list[dict], limit: int | None = None) -> str:
    """The conversations as a person would read them, each under what the plan says really happened. For review, not for the builder."""
    out = []
    for r in results[:limit]:
        p = r["plan"]
        belief = w.causes[p["believed_cause"]]["label"] if p.get("believed_cause") else "-"
        out.append(
            f"=== {p['conversation_id']}  {p['procedure']}  {p['row']['media_type']}  site {p['site']}  rep {p['rep']}  customer {p['customer']}\n"
            f"    truth: {w.causes[p['cause']]['label']}  |  rep believed: {belief}  |  outcome: {p['outcome']}"
            + (f"  |  breach: {', '.join(b['policy'] for b in p['breaches'])}" if p["breaches"] else "")
            + (f"  |  CALLBACK of {p['follow_up_of']}" if p.get("follow_up_of") is not None else "")
            + ("\n    " + "; ".join(r["problems"]) if r["problems"] else "")
        )
        for e in r["events"]:
            who = {"agent": "AGENT   ", "customer": "CUSTOMER", "system": "SYSTEM  "}[e["role"]]
            tag = "[note] " if e["channel"] == "case_note" else ""
            out.append(f"    {e['ts'][11:19]} {who} {tag}{e['text']}")
        out.append("")
    return "\n".join(out)

"""Checks on the realised text: reasons a conversation must not be accepted, and the gates over a whole run.

An invalid conversation is worse than a missing one: it reads fine and silently disagrees with the ground truth the corpus exists
to protect. So each is checked against its plan, and a failure is regenerated once and then dropped with its reasons. The checks
are deliberately conservative: a false negative costs a slightly leaky conversation, a false positive rejects good text and burns
the retry.

Plan: plans/2026-10-05-process-corpus.md (validation steps 4 and 5).
"""

from __future__ import annotations

import re
from collections import Counter

from corpus_world import World

STOPWORDS = set(
    """a all also an and any are as at back be been but by can cannot did do does else far fine for from get has have in into is it
    its just keep keeps like long more much no not now of on one only or other out over per put same some such than that the their
    them then there they thing this time to up very was well what when which while will with work working would everything something
    anything customer bank account""".split()
)
# Things the text must never contain: the plan's own vocabulary, and anything that looks like an identifier.
JARGON = re.compile(
    r"\b(?:CAU|MAN|ACT|OUT|PROC|POL)-[A-Z]|(?i:\bslot\b|manifestation|hypothesis|efficacy|ground truth)"
)
IDENTIFIER = re.compile(r"\b\d{9,}\b|\b\d{3}[- .]\d{3}[- .]\d{4}\b|\S+@\S+\.\S+")
# Steps the agent skipped must not appear anyway: a skipped verification is the breach, and a courtesy would erase it.
SKIPPED = {
    "verify": re.compile(
        r"(?i)\b(date of birth|last (four|4)|security question|one-time|passcode|verify (your|who|you)|verified (your|who|you)"
        r"|confirm your (identity|account|details|name)|who you are|full name|maiden)\b"
    ),
    # Said by the agent: what a customer's reason was ("another bank offers a better rate"), in a note, is not an offer.
    "offer": re.compile(
        r"(?i)\b(waive|bonus|incentive|better rate|lower rate|special offer|match that|credit you)\b"
    ),
    "offer_note": re.compile(r"(?i)\b(offered|offer of|waived|credited|incentive)\b"),
    "window": re.compile(r"(?i)\b(dispute window|within the window|60 days|120 days)\b"),
}
MAX_WORDS = {"voice": 90, "callback": 90, "chat": 60, "email": 220}
NOTE_WORDS = 90


def email_complete(text: str) -> bool:
    """The body of an email, before its sign-off, ends a sentence."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    signoff = re.compile(
        r"(?i)^((best|kind|warm)?\s*(regards|thanks|thank you|sincerely|cheers)[,.!]?\s*)?(\[REDACTED\])?[.,]?$"
    )
    if len(paragraphs) > 1 and signoff.match(paragraphs[-1]):
        paragraphs.pop()
    return paragraphs[-1].rstrip()[-1] in ".?!\"')]"


def keywords(label: str) -> set[str]:
    return {x for x in re.findall(r"[a-z]{4,}", label.lower())} - STOPWORDS


def mentions(text: str, label: str) -> bool:
    """Whole-word match on the distinctive words of a label, per turn: a leak is one turn discussing it."""
    keys = keywords(label)
    if len(keys) < 2:
        return False
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    return len(keys & words) >= max(2, round(len(keys) * 0.7))


def check(
    w: World, plan: dict, meta: dict, raw: list[dict], turns: dict[int, str], styles: dict
) -> list[str]:
    """Reasons this conversation must not be accepted. Empty if it can be."""
    skeleton, problems = meta["skeleton"], []
    slots = [s["slot"] for s in skeleton]
    got = [t["slot"] for t in raw]
    # Extra entries after the last slot are a model that kept writing: they are dropped, and nothing else is forgiven.
    if got[: len(slots)] == slots and all(g > slots[-1] for g in got[len(slots) :]):
        raw[:] = raw[: len(slots)]
        got = slots
    if got != slots:
        missing, extra = sorted(set(slots) - set(got)), sorted(set(got) - set(slots))
        dup = [k for k, v in Counter(got).items() if v > 1]
        order = "out of order" if got == sorted(got) else ""
        return [f"the slots are wrong (missing {missing}, extra {extra}, repeated {dup} {order})".strip()]
    media = plan["row"]["media_type"]
    for s in skeleton:
        text = turns[s["slot"]].strip()
        if not text:
            problems.append(f"slot {s['slot']} is empty")
            continue
        limit = NOTE_WORDS if s["role"] == "case_note" else MAX_WORDS.get(media, 90)
        if len(text.split()) > limit:
            problems.append(f"slot {s['slot']} is {len(text.split())} words (at most {limit})")
        if s["role"] == "cust_closing" and "?" in text:
            problems.append(f"slot {s['slot']} (the customer's last line) asks something new")
        if media == "email" and s["role"] != "case_note" and not email_complete(text):
            problems.append(f"slot {s['slot']} is an email that stops mid-sentence")
        if JARGON.search(text):
            problems.append(f"slot {s['slot']} uses the plan's vocabulary")
        if IDENTIFIER.search(text):
            problems.append(f"slot {s['slot']} contains an identifier: write [REDACTED]")

    agent_text = " ".join(turns[s["slot"]] for s in skeleton if s["speaker"] == "agent")
    taken = {s["action"] for s in plan["steps"] if s.get("action")}
    types = {w.actions[a]["type"] for a in taken}
    # Verifying the caller is the identity actions the auth policies name; the other "verify" actions (checking a window or a
    # history) are checks on the account, and an agent who runs them has not verified anyone.
    identity = {
        a
        for k in ("POL-AUTH-BEFORE-DETAIL", "POL-FRAUD-STEPUP-VERIFY")
        for a in w.policies[k]["satisfied_by"]
    }
    unauthenticated = not plan["authenticated"]
    if not (taken & identity) and (
        SKIPPED["verify"].search(agent_text)
        or (unauthenticated and re.search(r"(?i)\bverif(y|ying|ication)\b|\bidentity\b", agent_text))
    ):
        problems.append("the agent verifies the caller, and no slot has them do it")
    spoken = " ".join(
        turns[s["slot"]] for s in skeleton if s["speaker"] == "agent" and s["role"] != "case_note"
    )
    noted = " ".join(turns[s["slot"]] for s in skeleton if s["role"] == "case_note")
    if (
        plan["procedure"] == "PROC-RETENTION"
        and "offer" not in types
        and (SKIPPED["offer"].search(spoken) or SKIPPED["offer_note"].search(noted))
    ):
        problems.append("the agent makes an offer, and no slot has them do it")
    if "ACT-CHECK-DISPUTE-WINDOW" not in taken and SKIPPED["window"].search(agent_text):
        problems.append("the agent checks the dispute window, and no slot has them do it")

    # Nothing the plan left unsaid: a manifestation that is true, discriminating and neither brought up nor asked about.
    seen, asked = (
        set(meta["surfaced"]),
        {w.actions[a]["elicits"] for a in taken if w.actions[a].get("elicits")},
    )
    unsaid = [
        m
        for m, p in w.cause_manifestations[plan["cause"]].items()
        if p > 0
        and w.manifestations[m].get("discriminating")
        and m not in seen
        and m not in asked
        and m in plan["world"]["present"]
    ]
    for s in skeleton:
        if s["role"] == "case_note":
            continue
        for m in unsaid:
            if mentions(turns[s["slot"]], w.manifestations[m]["label"]):
                problems.append(
                    f"slot {s['slot']} brings up something nobody did: {w.manifestations[m]['label']}"
                )

    # The real fee or purchase, if there is one, is used.
    f = meta["facts"]
    whole = " ".join(turns.values())
    if f and f["kind"] == "purchase" and f["merchant"].lower() not in whole.lower():
        problems.append(f"the merchant {f['merchant']} is never named")
    if f and f["kind"] == "fee" and not re.search(rf"\${int(f['amount'])}\b", whole):
        problems.append(f"the fee amount ${f['amount']:.2f} is never stated")
    return problems


def as_utc(stamp: str):
    """An ISO timestamp as a UTC datetime; one with no zone is taken to be UTC (the warehouse's are zoned)."""
    from datetime import UTC, datetime

    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def event_problems(events: list[dict], plan: dict) -> list[str]:
    """The event objects agree with the plan and its row: contiguous order, time moving forward and inside the row's span, an
    agent only on what an agent said and the row's own agent, one channel for the media."""
    from datetime import timedelta

    out, row = [], plan["row"]
    if [e["seq"] for e in events] != list(range(len(events))):
        out.append("sequence numbers are not contiguous")
    if len({e["event_id"] for e in events}) != len(events):
        out.append("event ids repeat")
    stamps = [as_utc(e["ts"]) for e in events]
    if stamps != sorted(stamps):
        out.append("time runs backwards")
    start = as_utc(row["conversation_start"])
    spans = [e for e in events if e["channel"] != "case_note"]
    if spans and (
        stamps[0] < start
        or max(s for s, e in zip(stamps, events) if e["channel"] != "case_note")
        > start + timedelta(seconds=(row["handle_sec"] or 0) + 1)
    ):
        out.append("the conversation runs outside its row's span")
    for e in events:
        if e["role"] == "agent" and e["agent_user_id"] != row["agent_user_id"]:
            out.append(f"event {e['seq']} names the wrong agent")
        if e["role"] != "agent" and e["agent_user_id"]:
            out.append(f"event {e['seq']} names an agent on {e['role']}")
        if e["channel"] not in {"voice_turn", "chat_message", "email", "case_note", "system_log"}:
            out.append(f"event {e['seq']} has channel {e['channel']}")
    return out


# ------------------------------------------------------------------------------------------------------------------ gates


def gates(results: list[dict]) -> str:
    """What a run looks like as a corpus: acceptance, repetition, length, and what was rejected for."""
    done = [r for r in results if r["events"]]
    lines = [f"{len(done)} of {len(results)} conversations written"]
    first = sum(1 for r in done if r["attempts"] <= 1)
    lines.append(
        f"  accepted first time {first}, after one regeneration {len(done) - first}, dropped {len(results) - len(done)}"
    )
    reasons = Counter()
    for r in results:
        for p in r["problems"]:
            reasons[re.sub(r"\d+", "N", p.split(":")[0])[:70]] += 1
    if reasons:
        lines.append("  last reasons given for the ones dropped:")
        lines += [f"    {n:>3}  {why}" for why, n in reasons.most_common(6)]
    texts = [e["text"] for r in done for e in r["events"] if e["channel"] != "system_log"]
    if texts:
        unique = len(set(t.lower() for t in texts))
        substantive = [t for t in texts if len(t.split()) >= 6]
        lines.append(
            f"  messages {len(texts):,}; unique {100 * unique / len(texts):.0f}% of all, "
            f"{100 * len(set(t.lower() for t in substantive)) / max(1, len(substantive)):.0f}% of those of six words or more"
        )
        lengths = Counter()
        for r in done:
            for e in r["events"]:
                lengths[e["channel"]] += len(e["text"].split())
        per = Counter(e["channel"] for r in done for e in r["events"])
        lines.append(
            "  words per message: " + ", ".join(f"{c} {lengths[c] / per[c]:.0f}" for c in sorted(per))
        )
        top = Counter(t.lower() for t in texts).most_common(3)
        lines.append(
            "  most repeated: " + "; ".join(f"{n}x '{t[:50]}'" for t, n in top if n > 1)
            or "  most repeated: none"
        )
    return "\n".join(lines)

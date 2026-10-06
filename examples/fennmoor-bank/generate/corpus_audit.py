"""The audit of a written corpus: does what was written agree with the plans, the warehouse and the world, read back from the files.

Plan: plans/2026-10-05-process-corpus.md (validation steps 3 to 6, and phase 5). The generator checks each conversation as it is
written; this reads the outputs afterwards and trusts nothing the run said about itself, because a bug in the skeleton (a check
typed as a verification) once passed every check made at generation time. It needs the plans file, the corpus folder and the pool,
and spends nothing. A failure of a hard check makes `corpus.py --audit` exit 1; the gates are reported against the world's
thresholds (`spec/corpus/mechanics.yaml`, `gate_*`).
"""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from corpus_check import IDENTIFIER, JARGON, MAX_WORDS, SKIPPED, event_problems
from corpus_world import World

# Fields the plan copied from its row, and that the pool's row must still hold.
ROW_FIELDS = (
    "agent_user_id",
    "cif_number",
    "conversation_start",
    "handle_sec",
    "is_abandoned",
    "is_authenticated",
    "ivr_intent",
    "media_type",
    "queue_site_id",
    "site_id",
    "was_transferred",
    "wrapup_code_name",
)
EXAMPLES = 3
# The date the estate switched its wrap-up code for closures (the planted finding the text is to resolve).
SWITCH = "2026-06-02"


def read(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle]


class Findings:
    """Hard checks: each a name, how many things it looked at, and the ones that failed."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, int, list[str]]] = []

    def add(self, name: str, looked_at: int, bad: list[str]) -> None:
        self.rows.append((name, looked_at, bad))

    @property
    def failed(self) -> int:
        return sum(1 for _, _, bad in self.rows if bad)

    def render(self) -> str:
        lines = []
        for name, n, bad in self.rows:
            lines.append(
                f"  {'FAIL' if bad else 'ok  '}  {name}  ({n:,} checked"
                + (f", {len(bad)} failed)" if bad else ")")
            )
            lines += [f"          {b}" for b in bad[:EXAMPLES]]
        return "\n".join(lines)


def audit(w: World, directory: Path, plans_file: Path, pool: list[dict]) -> tuple[str, int]:
    """The audit as text, and the number of hard checks that failed."""
    events = read(directory / "events.ndjson.gz")
    truth = read(directory / "truth.ndjson.gz")
    plans = {p["conversation_id"]: p for p in read(plans_file)}
    rows = {r["conversation_id"]: r for r in pool}
    manifest = json.loads((directory / "manifest.json").read_text())
    by_conv: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_conv[e["conversation_id"]].append(e)
    written = [t for t in truth if t["conversation_id"] in by_conv]
    realised = [
        t for t in written if t["events"]
    ]  # the truth of a queue hang-up has no slots: its one line is not scripted by a plan
    f = Findings()
    identity = {
        a
        for k in ("POL-AUTH-BEFORE-DETAIL", "POL-FRAUD-STEPUP-VERIFY")
        for a in w.policies[k]["satisfied_by"]
    }

    # --- 3. the warehouse ---------------------------------------------------------------------------------------------------
    f.add(
        "every conversation is in the warehouse's calls",
        len(by_conv),
        [c for c in by_conv if c not in rows],
    )
    drift = []
    for t in truth:
        row, plan_row = rows.get(t["conversation_id"]), t["row"]
        if row:
            for key in ROW_FIELDS:
                if row.get(key) != plan_row.get(key):
                    drift.append(
                        f"{t['conversation_id']}: {key} {plan_row.get(key)!r} against {row.get(key)!r}"
                    )
    f.add("each plan's row is the warehouse's row, field for field", len(truth), drift)
    f.add(
        "every plan has a truth record, and every event a conversation in the truth",
        len(plans),
        [c for c in plans if c not in {t["conversation_id"] for t in truth}]
        + [c for c in by_conv if c not in plans],
    )
    out = []
    for t in written:
        if t["conversation_id"] in by_conv:
            out += [
                f"{t['conversation_id']}: {p}"
                for p in event_problems(by_conv[t["conversation_id"]], {"row": t["row"]})
            ]
    f.add(
        "events: contiguous, forward in time, inside the row's span, the row's own agent and channel",
        len(by_conv),
        out,
    )
    ids = [e["event_id"] for e in events]
    f.add("event ids are unique across the corpus", len(ids), [i for i, n in Counter(ids).items() if n > 1])
    # Mentions (validation 6): the key named in the truth is a fee or merchant the row's customer really had.
    # A callback names what its anchor call was about, so the test is the customer's, not the one call's.
    fees_of, merchants_of = defaultdict(set), defaultdict(set)
    for r in pool:
        fees_of[r["cif_number"]] |= {x["fee_id"] for x in r.get("fees") or []}
        merchants_of[r["cif_number"]] |= {x["merchant_id"] for x in r.get("purchases") or []}
    mention_bad, n_mentions = [], 0
    for t in truth:
        cif = (rows.get(t["conversation_id"]) or {}).get("cif_number")
        fees, merchants = fees_of[cif], merchants_of[cif]
        for e in t["events"]:
            for m in e["mentions"]:
                n_mentions += 1
                if m["key"] not in (fees if m["type"] == "Fee" else merchants):
                    mention_bad.append(f"{t['conversation_id']}: {m['type']} {m['key']} is not the row's")
    f.add("every fee and merchant named is a real row of the customer's", n_mentions, mention_bad)
    # Callbacks: the successor is the same customer, after the anchor, inside the window.
    call_bad = []
    n_call = 0
    for t in truth:
        a = t["follow_up_of"]
        if a is None:
            continue
        n_call += 1
        anchor = rows.get(plans[a]["conversation_id"]) if a in plans else None
        anchor = anchor or next((rows[p["conversation_id"]] for p in plans.values() if p["index"] == a), None)
        row = rows[t["conversation_id"]]
        gap = (
            (_when(row["conversation_start"]) - _when(anchor["conversation_start"])).days if anchor else None
        )
        if (
            not anchor
            or row["cif_number"] != anchor["cif_number"]
            or gap is None
            or not 0 <= gap <= w.mechanics["callback_days"]
        ):
            call_bad.append(f"{t['conversation_id']}: gap {gap}")
    f.add("a callback is the same customer, later, inside the window", n_call, call_bad)

    # --- 4. the text against the plan ---------------------------------------------------------------------------------------
    jargon = [
        f"{e['event_id']}: {m.group(0)}"
        for e in events
        for m in [JARGON.search(e["text"]) or IDENTIFIER.search(e["text"])]
        if m
    ]
    f.add("no plan vocabulary and no identifier in any text", len(events), jargon)
    long = [
        f"{e['event_id']}: {len(e['text'].split())} words"
        for e in events
        if len(e["text"].split()) > max(MAX_WORDS.values())
    ]
    f.add("no message longer than the longest allowed", len(events), long)
    order_bad = []
    for t in realised:
        steps = [e["step"] for e in t["events"] if e["step"] is not None]
        plan = plans[t["conversation_id"]]
        if steps != sorted(steps) or set(steps) != set(range(len(plan["steps"]))):
            order_bad.append(f"{t['conversation_id']}: steps {sorted(set(steps))} of {len(plan['steps'])}")
    f.add("every plan step is realised, in order", len(realised), order_bad)
    leaks, recalls = [], Counter()
    for t in realised:
        plan = plans[t["conversation_id"]]
        taken = {s["action"] for s in plan["steps"] if s.get("action")}
        agent = " ".join(e["text"] for e in by_conv[t["conversation_id"]] if e["role"] == "agent")
        said_verify = bool(
            SKIPPED["verify"].search(agent) or re.search(r"(?i)\bverif(y|ying|ication)\b|\bidentity\b", agent)
        )
        if taken & identity:
            recalls["verified"] += 1
            recalls["verified and said so"] += said_verify
        elif SKIPPED["verify"].search(agent):
            leaks.append(f"{t['conversation_id']}: verification talk, no identity action")
        spoken = " ".join(
            e["text"]
            for e in by_conv[t["conversation_id"]]
            if e["role"] == "agent" and e["channel"] != "case_note"
        )
        if (
            plan["procedure"] == "PROC-RETENTION"
            and not any(w.actions[a]["type"] == "offer" for a in taken)
            and SKIPPED["offer"].search(spoken)
        ):
            leaks.append(f"{t['conversation_id']}: an offer, none planned")
    f.add("no verification and no offer in the text that the plan did not take", len(realised), leaks)
    breach = [
        t
        for t in realised
        if any(g["policy"] == "POL-AUTH-BEFORE-DETAIL" and g["at"] == "S-DISCOVER" for g in t["breaches"])
    ]
    f.add(
        "the planted authentication breaches carry no verification talk",
        len(breach),
        [
            t["conversation_id"]
            for t in breach
            if any(
                SKIPPED["verify"].search(e["text"])
                for e in by_conv[t["conversation_id"]]
                if e["role"] == "agent"
            )
        ],
    )

    # --- 5. the gates -------------------------------------------------------------------------------------------------------
    texts = [e["text"].lower() for e in events if e["channel"] != "system_log"]
    substantive = [t for t in texts if len(t.split()) >= 6]
    n = len(truth)
    gates = [
        ("unique messages, of all", len(set(texts)) / len(texts), w.mechanics["gate_unique_all"], ">="),
        (
            "unique messages, of six words or more",
            len(set(substantive)) / len(substantive),
            w.mechanics["gate_unique_substantive"],
            ">=",
        ),
        (
            "conversations dropped",
            (len(truth) - len(written)) / n,
            w.mechanics["gate_dropped"],
            "<=",
        ),
        (
            "accepted first time",
            sum(1 for t in written if t["attempts"] <= 1) / len(written),
            w.mechanics["gate_first_time"],
            ">=",
        ),
    ]
    lines = ["", "gates (the world's thresholds, mechanics.yaml)"]
    gate_failed = 0
    for name, got, want, op in gates:
        ok = got >= want if op == ">=" else got <= want
        gate_failed += not ok
        lines.append(f"  {'ok  ' if ok else 'FAIL'}  {name}: {100 * got:.1f}%  (want {op} {100 * want:.0f}%)")

    # --- what the corpus holds ----------------------------------------------------------------------------------------------
    out_lines = [
        f"audit of {directory} ({manifest.get('model')}): {len(plans):,} plans, {len(truth):,} truth records, {len(events):,} events",
        "",
        "hard checks",
        f.render(),
        *lines,
        "",
        f"recall: of {recalls['verified']} conversations where the plan verifies the caller, {recalls['verified and said so']} say so",
    ]
    out_lines.append(_truth_table(w, written, plans))
    return "\n".join(out_lines), f.failed + gate_failed


def _when(stamp: str):
    from corpus_check import as_utc

    return as_utc(stamp)


def _truth_table(w: World, done: list[dict], plans: dict) -> str:
    """The planted truths as they stand in what was written, which is what a later scorer is tested on: the plans' own report
    over the conversations that were written, and truth 1, which only the warehouse's rows can show."""
    from corpus_report import report

    closures = [t for t in done if t["row"]["ivr_intent"] == "CLOSE_ACCOUNT" and t["follow_up_of"] is None]
    before = Counter(
        t["row"]["wrapup_code_name"] for t in closures if t["row"]["conversation_start"][:10] < SWITCH
    )
    after = Counter(
        t["row"]["wrapup_code_name"] for t in closures if t["row"]["conversation_start"][:10] >= SWITCH
    )
    show = lambda c: ", ".join(f"{k or 'none'} {n}" for k, n in c.most_common(4))  # noqa: E731
    return "\n".join(
        [
            "",
            "truth 1, the closure code the text resolves (closure-intent conversations, by the wrap-up code the warehouse holds)",
            f"  before {SWITCH}: {sum(before.values())}: {show(before)}",
            f"  from {SWITCH}:   {sum(after.values())}: {show(after)}",
            "",
            report(w, [plans[t["conversation_id"]] for t in done]),
        ]
    )

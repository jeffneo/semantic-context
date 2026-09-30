"""Explore: an answer a consumer checks, and corrects (plans/2026-09-30-accuracy-orthogonal.md, "The tests").

Turn one is the baseline's answer. The consumer sees it the way an answer should present itself: the
assumptions it made (the fact table, each measure's definition, the groupings, filters, period, the
joins that keep rows without a match), and a preview of the result. The consumer accepts it, or says
what is wrong; the request is asked again with the previous request and everything said so far; at most
MAX_ANSWERS answers.

What counts against the service (the plan's "Measurement"): a wrong answer the consumer accepts, and an
exchange that doesn't converge: no right answer, or the first right one delivered only past the
service's targets (tokens, seconds: defaults.yaml `service.targets`, the service's share only; the
consumer's reading and writing is measured apart). A right answer the consumer rejects is the
consumer's failure, not the service's: whatever follows, the service delivered.

The consumers (personas), each knowing only what such a consumer would know:
  state          an AI agent part-way through a business process, holding its working state (the
                 process, the step, what is settled, what the next step needs; written from the
                 reference query in business words); asks the question as it is, reads the SQL too
  state-context  the same agent, which writes its first request itself: the question and what from its
                 state the service needs
  agent          (the first test) an automated agent that knows only the question
  analyst, terse (the first test) a person who knows what they meant (an intent card), in full or in a word
The reference's own identifiers are masked out of anything a consumer writes (a guard against leaking
the answer key); how often that happened is counted. `--retrace`: a correction is navigated again (the
cohort and examples found for the corrected question), not only compiled again.

Prep (once): uv run examples/fennmoor-bank/eval/explore_confirm.py prep intents|states|states-plain
             (states-plain: the state without where the data comes from or how it is joined: the
             consumer knows its process, not the business's data; run with --cards=states-plain)
Run:         uv run examples/fennmoor-bank/eval/explore_confirm.py run <persona> [--retrace] [--precedent] [--cards=KIND] [--set=full] [--fresh=TAG] [--workers=N] [--only=...]
             (--precedent: the service tries the request bank's precedents first, explore_precedent.serve_precedent)
"""

from __future__ import annotations

import json
import re
import sys

from explore import load_set, run, text, trace_of
from match import ROWS, verdict

from qlsc import meter, navigate
from qlsc.llm import LLM

JUDGE = {
    "type": "object",
    "required": ["accept", "problem"],
    "properties": {
        "accept": {"type": "boolean", "description": "true when the answer answers the question as meant"},
        "problem": {
            "type": "string",
            "description": "when not accepted: what is wrong, in a sentence or two",
        },
    },
}
INTENT = {"type": "object", "required": ["intent"], "properties": {"intent": {"type": "string"}}}
STATE = {
    "type": "object",
    "required": ["process", "step", "established", "next_step", "needs"],
    "properties": {
        "process": {"type": "string"},
        "step": {"type": "string"},
        "established": {"type": "array", "items": {"type": "string"}},
        "next_step": {"type": "string"},
        "needs": {"type": "array", "items": {"type": "string"}},
    },
}
REQUEST = {"type": "object", "required": ["request"], "properties": {"request": {"type": "string"}}}
MAX_ANSWERS = 4


def cards_path(s, kind: str):
    return s.work / "qdd" / "explore" / f"{kind}.json"


def state_text(st: dict) -> str:
    return "\n".join(
        [f"Process: {st['process']}", f"Step: {st['step']}", "Established:"]
        + [f"- {x}" for x in st["established"]]
        + [f"Next step: {st['next_step']}", "It needs from the result:"]
        + [f"- {x}" for x in st["needs"]]
    )


def prep(kind: str) -> int:
    """A card per probe question, from its reference query: the asker's intent (`intents`), or the
    agent's working state (`states`), identifiers masked."""
    from common import settings

    s = settings()
    if kind == "intents":
        writer = LLM(text("explore_intent_system"), s, s["llm"]["query_model"])
        make = lambda q: writer.call(text("explore_intent", question=q["question"], sql=q["sql"]), INTENT,
                                     max_tokens=2000)["intent"]  # fmt: skip
    else:
        writer = LLM(text("explore_state_system", **s.business), s, s["llm"]["query_model"])
        which = "explore_state_plain" if kind == "states-plain" else "explore_state"
        make = lambda q: state_text(writer.call(text(which, question=q["question"], sql=q["sql"]), STATE,
                                                max_tokens=3000))  # fmt: skip
    cards, leaks = {}, 0
    for q in load_set(s):
        cards[q["qid"]], n = masked(make(q), q)
        leaks += n
    cards_path(s, kind).write_text(json.dumps(cards, indent=1))
    print(f"{len(cards)} {kind} ({leaks} identifiers masked) -> {cards_path(s, kind)}")
    return 0


def presentation(a: dict, with_sql: bool) -> str:
    """The answer as it presents itself: its assumptions, then a preview of the result."""
    lines = []
    req = a.get("request") if a.get("writer") == "compiled" else None
    if req:
        lines.append("Assumptions:")
        for m in req.get("measures") or []:
            what = (
                m.get("computation")
                and f"the business's computation {m['computation']}"
                or (
                    f"{m.get('aggregate') or ''}({m.get('column') or 'rows'})"
                    + (f" over rows where {conds(m['where'])}" if m.get("where") else "")
                )
            )
            if m.get("ratio_of"):
                what = f"{m['ratio_of'][0]} / {m['ratio_of'][1]}"
            if m.get("difference_of"):
                what = f"{m['difference_of'][0]} - {m['difference_of'][1]}"
            if m.get("per"):
                what += f", per {', '.join(m['per'])}, then {m.get('then') or 'SUM'}"
            lines.append(f"- measure {m['alias']}: {what}")
        for d in req.get("dimensions") or []:
            lines.append(f"- broken down by {d.get('column') or d.get('computation')}"
                         + (f" ({d['grain']})" if d.get("grain") else ""))  # fmt: skip
        if req.get("filters"):
            lines.append(f"- only rows where {conds(req['filters'])}")
        per = req.get("period") or {}
        if per.get("column"):
            lines.append(
                f"- period: {per['column']} from {per.get('from') or 'the start'} to {per.get('to') or 'today'}, both included"
            )
        for h in req.get("having") or []:
            lines.append(f"- keeping groups where {h['alias']} {h['op']} {h['value']}")
        if req.get("order") or req.get("limit"):
            lines.append(f"- ordered by {', '.join(o['alias'] + (' desc' if o['desc'] else '') for o in req.get('order') or [])}"
                         + (f", top {req['limit']}" if req.get("limit") else ""))  # fmt: skip
        outer = re.findall(r"LEFT JOIN `([^`]+)`", a.get("sql") or "")
        if outer:
            lines.append(f"- rows with no match in {', '.join(outer)} are kept (their columns empty)")
    else:
        lines.append(f"How it was answered: {a.get('explanation') or 'a query written for the question'}")
    if with_sql and a.get("sql"):
        lines += ["", "SQL:", a["sql"]]
    got = a.get("result") or {}
    if got.get("ok") is False or not got:
        lines += ["", f"The query failed: {got.get('error') or a.get('error') or a.get('fallback')}"]
    else:
        cols = got.get("columns") or []
        lines += ["", f"Result: {got.get('total', 0):,} rows. The first {min(8, len(got.get('rows') or []))}:",
                  " | ".join(cols)]  # fmt: skip
        for r in (got.get("rows") or [])[:8]:
            lines.append(" | ".join(str(r.get(c)) for c in cols))
    return "\n".join(lines)


def conds(cs: list[dict]) -> str:
    out = []
    for c in cs:
        if c.get("computation"):
            out.append(f"the business's population {c['computation']}")
        else:
            vals = c.get("values") or ([c["value"]] if c.get("value") not in (None, "") else [])
            out.append(f"{c.get('column')} {c.get('op')} {', '.join(map(str, vals))}".strip())
    return " and ".join(out)


def masked(feedback: str, q: dict) -> tuple[str, int]:
    """The reference's identifiers the question doesn't use, masked out of feedback."""
    names = set(re.findall(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+", q["sql"])) - set(
        re.findall(r"\w+", q["question"])
    )
    n = 0
    for x in sorted(names, key=len, reverse=True):
        if re.search(rf"\b{re.escape(x)}\b", feedback, re.I):
            feedback, n = re.sub(rf"\b{re.escape(x)}\b", "[...]", feedback, flags=re.I), n + 1
    return feedback, n


def compiled(G, s, tr: dict, q: dict, rejected: set) -> dict:
    return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS)


def answer_for(persona: str, cards: dict, retrace: bool = False, serve=compiled):
    """`serve(G, s, tr, q, rejected) -> answer`: the service (the compiled request, or precedent first);
    `rejected`, the precedents the asker rejected in this exchange."""
    stateful = persona.startswith("state")

    def answer(G, s, q: dict, tr: dict | None) -> dict:
        ours, theirs = meter.current(), meter.Meter()
        targets = s["service"]["targets"]
        model = s["llm"]["query_model"]
        judge = LLM(text("explore_persona_state" if stateful else f"explore_persona_{persona}"), s, model)
        card, question, leaks = cards.get(q["qid"], ""), q["question"], 0
        if persona == "state-context":  # the agent's own first request
            with meter.aside(theirs):
                w = LLM(text("explore_state_request_system"), s, model)
                out = w.call(
                    text("explore_state_request", state=card, question=question), REQUEST, max_tokens=2000
                )
            question, n = masked(out["request"], q)
            leaks += n
        if tr is None:
            tr = trace_of(G, s, q | {"question": question})
        rejected: set = set()
        a = serve(G, s, tr, q, rejected)
        ours.add("turns")
        turns, said = [], []
        for turn in range(MAX_ANSWERS):
            v, why = verdict(a, q["refs"])
            at = ours.measure()
            view = presentation(a, with_sql=stateful or persona == "agent")
            if stateful:
                history = "".join(f"\nEarlier in this exchange you said: {x}" for x in said)
                ask = text("explore_consumer_state", state=card, question=question, history=history + "\n",
                           answer=view)  # fmt: skip
            else:
                ask = text("explore_consumer", question=question, intent=card if persona != "agent" else "",
                           answer=view)  # fmt: skip
            with meter.aside(theirs):
                j = judge.call(ask, JUDGE, max_tokens=2000)
            turns.append({"verdict": v, "why": why, "accepted": j["accept"], "problem": j["problem"], "via": a.get("via"),
                          "tokens": at["tokens"], "seconds": at["seconds"], "within": meter.within(at, targets)})  # fmt: skip
            if j["accept"] or turn == MAX_ANSWERS - 1:
                break
            feedback, n = masked(j["problem"], q)
            leaks += n
            if a.get("precedent"):
                rejected.add(a["precedent"])
            said.append(feedback)
            previous = json.dumps(a.get("request")) if a.get("request") else (a.get("sql") or "")
            # the clarification is part of the question now, as in a conversation: navigation (with
            # --retrace), the request checks and the week rule read the question, and must hear it too
            asked = f"{question} ({'; '.join(said)})"
            base = trace_of(G, s, q | {"question": asked}) if retrace else tr
            tr2 = base | {"question": asked,
                          "addendum": "\n\n" + text("explore_correction", previous=previous, feedback="; ".join(said))}  # fmt: skip
            a = serve(G, s, tr2, q, rejected)
            ours.add("turns")
        first = next((i for i, t in enumerate(turns) if t["verdict"] == "correct"), None)
        last = turns[-1]
        if first is not None:
            t = turns[first]
            outcome = ("right, over target" if not t["within"] else "right, rejected by the consumer"
                       if not t["accepted"] else "right at once" if first == 0 else "right after corrections")  # fmt: skip
            scored, delivered = ("correct", t["why"]), t["within"]
        else:
            outcome = "accepted wrong" if last["accepted"] else "not converged"
            scored, delivered = (last["verdict"], last["why"]), False
        return a | {"scored": scored, "delivered": delivered,
                    "explore": {"turns": turns, "outcome": outcome, "leaks": leaks, "accepted": last["accepted"],
                                "ideal": delivered and first <= 1, "consumer": theirs.measure(),
                                "request": question if persona == "state-context" else None}}  # fmt: skip

    answer.own_trace = persona == "state-context"
    return answer


def main() -> int:
    from common import settings

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if args[0] == "prep":
        return prep(args[1])
    persona = args[1]
    retrace = "--retrace" in sys.argv
    serve = compiled
    if "--precedent" in sys.argv:  # precedent first, over the request bank
        from explore_precedent import other_texts, serve_precedent

        from qlsc.graph import Graph

        s = settings()
        with Graph(s) as G:
            serve = serve_precedent(other_texts(G, s, {q["shape"] for q in load_set(s) if q["shape"]}))
    kind = opt.get("cards") or ("states" if persona.startswith("state") else "intents")
    cards = json.loads(cards_path(settings(), kind).read_text())
    only = set(opt["only"].split(",")) if "only" in opt else None
    run(f"confirm-{persona}" + ("-retrace" if retrace else "") + (f"-{kind}" if "cards" in opt else "")
        + ("-precedent" if serve is not compiled else ""),
        answer_for(persona, cards, retrace, serve),
        int(opt.get("workers", 6)), only,
        notes=f"The baseline's answer, checked and corrected by the {persona} consumer (at most {MAX_ANSWERS} "
              f"answers){'; corrections navigated again' if retrace else ''}.")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

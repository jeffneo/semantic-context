"""The agent that uses qlsc: an AI agent part-way through a business process (run.py, README.md).

Its state is written once per question from the question's reference query, in the business's words
(prompts/state*.md): the process and its goal, the step, what the process has settled (the period, the
definitions it uses, the population), the next step and what it needs from the result (one row per what,
which figures, their order). Never where the data comes from or how it is joined: the agent knows its
process, not the business's data. The reference's identifiers are masked out of it.

The exchange:
  1. The agent writes its request: the question, and what from its state the service needs
     (prompts/request*.md).
  2. qlsc answers by its router over the SQL routes: a precedent (the business's own query, its values
     set), else the compiled request, else free SQL (navigate.answer_routed). The question's own query is
     left out, as the log evaluations leave it out; a re-ask may still find it through another of its
     texts in the log (the same query run with other values: `texts`).
  3. The agent reads the answer as it presents itself (its assumptions, its SQL, a preview of the rows)
     against its state, and accepts it, or says what is wrong (prompts/consumer*.md).
  4. A correction is asked again with everything said (navigate.corrected: navigated again, the previous
     request beside it), a rejected precedent not offered again; at most MAX_ANSWERS answers.
What counts against qlsc: a wrong answer the agent accepts, and an exchange that doesn't converge (no right
answer, or the first right one only past the service's targets). A right answer the agent rejects is the
agent's failure: qlsc delivered.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import defaultdict

from match import ROWS, verdict
from run import out_dir, questions, text, trace_of

from qlsc import meter, navigate
from qlsc.graph import Graph
from qlsc.llm import LLM
from qlsc.names import text_id

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
MAX_ANSWERS = 4
ROUTES = ("precedent", "sql", "free")  # scored as SQL, as the log evaluations are


def states_path(s):
    return out_dir(s) / "states.json"


def state_text(st: dict) -> str:
    return "\n".join(
        [f"Process: {st['process']}", f"Step: {st['step']}", "Established:"]
        + [f"- {x}" for x in st["established"]]
        + [f"Next step: {st['next_step']}", "It needs from the result:"]
        + [f"- {x}" for x in st["needs"]]
    )


def masked(feedback: str, q: dict) -> tuple[str, int]:
    """The reference's identifiers the question doesn't use, masked out of what the agent writes."""
    names = set(re.findall(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+", q["sql"])) - set(
        re.findall(r"\w+", q["question"])
    )
    n = 0
    for x in sorted(names, key=len, reverse=True):
        if re.search(rf"\b{re.escape(x)}\b", feedback, re.I):
            feedback, n = re.sub(rf"\b{re.escape(x)}\b", "[...]", feedback, flags=re.I), n + 1
    return feedback, n


def prep() -> int:
    """The agent's state for every question, from its reference query."""
    from common import settings

    s = settings()
    writer = LLM(text("state_system", **s.business), s, s["llm"]["query_model"])
    states, leaks = {}, 0
    for q in questions(s):
        st = writer.call(text("state", question=q["question"], sql=q["sql"]), STATE, max_tokens=3000)
        states[q["qid"]], n = masked(state_text(st), q)
        leaks += n
    states_path(s).write_text(json.dumps(states, indent=1))
    print(f"{len(states)} states ({leaks} identifiers masked) -> {states_path(s)}")
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


def other_texts(G, s, own: set[str]) -> dict[str, str]:
    """Another text of each of these shapes, with other literals (the re-ask precedent: the business ran the
    question's own query with other values), when the log has one."""
    texts = defaultdict(list)
    for line in gzip.open(s.work / "texts.ndjson.gz", "rt"):
        t = json.loads(line)
        if t.get("shape_id") in own:
            texts[t["shape_id"]].append(t)
    sample = {
        r["id"]: r["sql"]
        for r in G.rows(
            "MATCH (s:QueryShape) WHERE s.id IN $ids RETURN s.id AS id, s.sample_sql AS sql", ids=sorted(own)
        )
    }
    sample_tid = {sh: text_id(sql) for sh, sql in sample.items()}
    want = {}
    for sh, ts in texts.items():
        mine = next((t["literals"] for t in ts if t["text_id"] == sample_tid.get(sh)), None)
        other = next((t for t in ts if t["text_id"] != sample_tid.get(sh) and t["literals"] != mine), None)
        if other:
            want[other["text_id"]] = sh
    alt = {}
    for line in gzip.open(s.work / "log_groups.ndjson.gz", "rt"):
        g = json.loads(line)
        if g["query"] and (tid := text_id(g["query"])) in want:
            alt[want.pop(tid)] = g["query"]
    return alt


def answerer():
    """answer(G, s, q): one question's exchange between the agent and qlsc."""
    from common import settings

    s = settings()
    states = json.loads(states_path(s).read_text())
    with Graph(s) as G:
        texts = other_texts(G, s, {q["shape"] for q in questions(s) if q["shape"]})

    def answer(G, s, q: dict) -> dict:
        ours, theirs = meter.current(), meter.Meter()
        targets, model = s["service"]["targets"], s["llm"]["query_model"]
        state, leaks = states[q["qid"]], 0
        judge = LLM(text("consumer_system"), s, model)
        with meter.aside(theirs):  # the agent writes its request
            w = LLM(text("request_system"), s, model)
            out = w.call(text("request", state=state, question=q["question"]), REQUEST, max_tokens=2000)
        request, n = masked(out["request"], q)
        leaks += n
        exclude = frozenset({q["shape"]}) if q["shape"] else frozenset()
        reask = {q["shape"]: texts[q["shape"]]} if q["shape"] in texts else {}
        tr = trace_of(G, s, q, request) | {"texts": reask}
        a = navigate.answer_routed(G, s, tr, execute=True, rows=ROWS, routes=ROUTES)
        ours.add("turns")
        turns, said, rejected = [], [], set()
        for i in range(MAX_ANSWERS):
            v, why = verdict(a, q["refs"])
            at = ours.measure()
            history = "".join(f"\nEarlier in this exchange you said: {x}" for x in said)
            ask = text(
                "consumer",
                state=state,
                question=request,
                history=history + "\n",
                answer=presentation(a, True),
            )
            with meter.aside(theirs):
                j = judge.call(ask, JUDGE, max_tokens=2000)
            turns.append({"verdict": v, "why": why, "accepted": j["accept"], "problem": j["problem"],
                          "route": a.get("route"), "tokens": at["tokens"], "seconds": at["seconds"],
                          "within": meter.within(at, targets)})  # fmt: skip
            if j["accept"] or i == MAX_ANSWERS - 1:
                break
            feedback, n = masked(j["problem"], q)
            leaks += n
            said.append(feedback)
            if a.get("precedent"):
                rejected.add(a["precedent"])
            tr = navigate.corrected(G, s, request, a, said, exclude=exclude) | {"texts": reask}
            a = navigate.answer_routed(
                G, s, tr, execute=True, rows=ROWS, routes=ROUTES, rejected=frozenset(rejected)
            )
            ours.add("turns")
        first = next((i for i, t in enumerate(turns) if t["verdict"] == "correct"), None)
        last = turns[-1]
        if first is not None:
            t = turns[first]
            outcome = ("right, past the targets" if not t["within"] else "right, rejected by the agent"
                       if not t["accepted"] else "right at once" if first == 0 else "right after corrections")  # fmt: skip
            scored, delivered = ("correct", t["why"]), t["within"]
        else:
            outcome = "accepted wrong" if last["accepted"] else "never right"
            scored, delivered = (last["verdict"], last["why"]), False
        return a | {"scored": scored, "delivered": delivered,
                    "exchange": {"turns": turns, "outcome": outcome, "leaks": leaks, "request": request,
                                 "consumer": theirs.measure()}}  # fmt: skip

    return answer

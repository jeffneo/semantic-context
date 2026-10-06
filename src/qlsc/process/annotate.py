"""Annotate: each turn of a conversation described as a State (the case as the customer's turn leaves it) or an Action (what the
agent's turn does), by an LLM, from the conversation so far and never from what comes after.

Two units, to be compared (plans/2026-10-05-text-graph-construction.md, phase 1):
  turn          one call per turn, given the turns up to it. Cannot see the future, so it is the reference; costs a call per turn.
  conversation  one call per conversation, told to annotate each turn from the turns up to it. About a tenth of the calls, and a
                risk that what the conversation goes on to say leaks into earlier States.

Every answer is a strict structured output and the call is cached by request, so a rerun costs nothing. A turn whose answer fails
the checks twice is recorded with its problem and never stops the pass.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

from qlsc.config import Settings
from qlsc.llm import LLM, prompt
from qlsc.process.source import Source, Turn

STATE = {
    "type": "object",
    "required": ["latest_turn", "established"],
    "properties": {"latest_turn": {"type": "string"}, "established": {"type": "string"}},
}
ACTION = {"type": "object", "required": ["action"], "properties": {"action": {"type": "string"}}}
CONVERSATION = {
    "type": "object",
    "required": ["turns"],
    "properties": {
        "turns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["turn", "latest_turn", "established", "action"],
                "properties": {
                    "turn": {"type": "integer"},
                    "latest_turn": {"type": "string"},
                    "established": {"type": "string"},
                    "action": {"type": "string"},
                },
            },
        }
    },
}
WHAT = {"state": "state of the case", "action": "action the agent takes"}


def transcript(turns: list[Turn], upto: int | None = None) -> str:
    """Numbered lines, each by its role: the whole conversation, or up to and including index `upto`."""
    shown = turns if upto is None else turns[: upto + 1]
    return "\n".join(f"[{i + 1}] {t.role.capitalize()}: {t.text}" for i, t in enumerate(shown))


def state_text(a: dict) -> str:
    """The State's description, latest turn first: the line the turn is about, then what is known."""
    return f"{a['latest_turn'].strip()} {a['established'].strip()}".strip()


def problems(s: Settings, kind: str, a: dict) -> list[str]:
    """Reasons an answer is not accepted: an empty field, an Action not starting with a listed verb, a too long State line."""
    cfg = s["process"]
    if kind == "action":
        words = a["action"].split()
        verbs = {v.lower() for v in cfg["action_verbs"]}
        if not words:
            return ["the action is empty"]
        return (
            [] if words[0].lower() in verbs else [f"the action must begin with one of {cfg['action_verbs']}"]
        )
    out = [f"{k} is empty" for k in ("latest_turn", "established") if not a[k].strip()]
    # A State line a little over the limit is not worth a retry; one that retells the call is.
    if len(a["established"].split()) > cfg["state_words"] * 2:
        out.append(f"established must be at most {cfg['state_words']} words")
    return out


class Annotator:
    def __init__(self, s: Settings, model: str | None = None):
        self.s = s
        cfg = s["process"]
        words, verbs = cfg["state_words"], ", ".join(cfg["action_verbs"])
        self.state = LLM(prompt("process_state_system", **s.business, state_words=words), s, model)
        self.action = LLM(prompt("process_action_system", **s.business, verbs=verbs), s, model)
        self.conversation = LLM(
            prompt("process_conversation_system", **s.business, state_words=words, verbs=verbs), s, model
        )
        self.model = self.state.model

    def llms(self) -> list[LLM]:
        return [self.state, self.action, self.conversation]

    # -- one call per turn ------------------------------------------------------------------------------------------------

    def turn(self, turns: list[Turn], i: int) -> dict:
        t = turns[i]
        llm, schema = (self.state, STATE) if t.kind == "state" else (self.action, ACTION)
        ask = prompt("process_turn", conversation=transcript(turns, i), what=WHAT[t.kind], turn=i + 1)
        why: list[str] = []
        a: dict = {}
        for attempt in range(2):
            try:
                a = llm.call(
                    ask if not why else ask + f"\nYour last answer was rejected: {'; '.join(why)}.\n",
                    schema,
                    max_tokens=400,
                )
            except (
                RuntimeError,
                anthropic.APIError,
            ) as e:  # a request the API refuses fails that turn, never the pass
                why = [f"no answer: {e}"]
                continue
            why = problems(self.s, t.kind, a)
            if not why:
                return record(t, a, attempt + 1, [])
        return record(t, a, 2, why)

    def by_turn(self, conversation: list[Turn]) -> list[dict]:
        return [self.turn(conversation, i) for i in range(len(conversation))]

    # -- one call per conversation ----------------------------------------------------------------------------------------

    def by_conversation(self, conversation: list[Turn]) -> list[dict]:
        ask = prompt("process_conversation", conversation=transcript(conversation))
        why: list[str] = []
        got: list[dict] = []
        for _ in range(2):
            try:
                got = self.conversation.call(
                    ask if not why else ask + f"\nYour last answer was rejected: {'; '.join(why)}.\n",
                    CONVERSATION,
                    max_tokens=6000,
                )["turns"]
            except (
                RuntimeError,
                anthropic.APIError,
            ) as e:  # a request the API refuses fails that turn, never the pass
                why = [f"no answer: {e}"]
                continue
            why = (
                []
                if [g["turn"] for g in got] == list(range(1, len(conversation) + 1))
                else [f"return exactly turns 1 to {len(conversation)}, in order"]
            )
            if not why:
                break
        out = []
        for t, g in zip(conversation, got, strict=False):
            bad = why or problems(self.s, t.kind, g)
            out.append(record(t, g, 1 + bool(why), bad))
        return out


def record(t: Turn, a: dict, attempts: int, bad: list[str]) -> dict:
    description = state_text(a) if t.kind == "state" and a else a.get("action", "").strip()
    return {
        "event": t.event,
        "conversation": t.conversation,
        "seq": t.seq,
        "kind": t.kind,
        "description": description,
        "answer": a,
        "attempts": attempts,
        "problems": bad,
    }


def select(src: Source, limit: int | None) -> list[str]:
    """The conversations to annotate: in id order, so the same limit is the same sample."""
    ids = list(src.conversations)
    return ids[:limit] if limit else ids


def run(s: Settings, src: Source, unit: str, limit: int | None, model: str | None, out: Path) -> dict:
    """Annotate the first `limit` conversations by `unit`; write the records and a manifest; return the manifest."""
    a = Annotator(s, s["llm"]["query_model"] if model == "query" else model)
    work = a.by_turn if unit == "turn" else a.by_conversation
    ids = select(src, limit)
    t0 = time.time()
    done, lock = [0], threading.Lock()

    def one(c: str) -> list[dict]:
        out = work(src.conversations[c])
        with lock:  # progress, flushed: a long run is watched, and a killed one resumes from the cache
            done[0] += 1
            if done[0] % 100 == 0 or done[0] == len(ids):
                print(f"  {done[0]}/{len(ids)} conversations, {time.time() - t0:.0f} s", flush=True)
        return out

    with ThreadPoolExecutor(max_workers=s["llm"]["concurrency"]) as pool:
        results = list(pool.map(one, ids))
    seconds = time.time() - t0
    out.mkdir(parents=True, exist_ok=True)
    rows = [r for conversation in results for r in conversation]
    with open(out / f"annotations-{unit}.ndjson", "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    llms = a.llms()
    manifest = {
        "unit": unit,
        "model": a.model,
        "conversations": len(ids),
        "turns": len(rows),
        "problems": sum(1 for r in rows if r["problems"]),
        "retried": sum(1 for r in rows if r["attempts"] > 1),
        "calls": sum(x.calls for x in llms),
        "cached": sum(x.cached for x in llms),
        "tokens": {k: sum(x.tokens[k] for x in llms) for k in ("in", "out")},
        "cost": sum(x.cost() or 0 for x in llms),
        "api_seconds": round(sum(x.seconds for x in llms), 1),
        "wall_seconds": round(seconds, 1),
    }
    (out / f"annotations-{unit}.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def report(s: Settings, unit: str, limit: int | None, model: str | None) -> None:
    """`qlsc process annotate`: read the events, annotate, say what it took."""
    from qlsc.process import source

    src = source.read(s)
    out = s.work / "process"
    m = run(s, src, unit, limit, model, out)
    print(f"{m['conversations']} conversations, {m['turns']} turns, by {unit} with {m['model']}")
    print(
        f"  {m['calls']} calls, {m['cached']} cached, ${m['cost']:.2f}, {m['wall_seconds']} s ({m['api_seconds']} s in the API)"
    )
    print(f"  {m['retried']} turns needed a second attempt, {m['problems']} still have a problem")
    print(f"wrote {out}/annotations-{unit}.ndjson")

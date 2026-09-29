"""Converse: the agent's side of memory, in the Context Memory model (plans/2026-09-29-context-memory-model.md),
beside the warehouse facts `remember` keeps.

  labels       Conversation, Message, Task, Step, Decision, Fact, Entity (and Skill: qlsc/distill.py); the
               warehouse's own nodes (Customer, Account, ...) are the long-term memory, and the semantic
               layer's Table, Column and Computation stubs link into it
  structure    (Message)-[:PART_OF]->(Conversation), (Task)-[:PART_OF]->(Conversation),
               (Step)-[:PART_OF]->(Task), (Decision)-[:PART_OF]->(Task); NEXT in order, with seq
  a Task       is one request an agent worked on: each user message starts one, -[:FROM]-> it, and the
               agent's reply closes it. Its Steps are qlsc's tools:
                 recall  an entity's context (qlsc/memory.py writes the step): -[:READ]-> the anchor
                 ask     a question: its result summary, and -[:READ]-> the Table and Computation stubs its
                         query read. Its fingerprint is its compiled request with every value out, as the
                         parser fingerprints SQL: what distillation groups by
  knowledge    (Fact {predicate, value})-[:ABOUT]->(its subject), -[:MENTIONS]-> anything else it names,
               -[:FROM]-> the message it was learned in. A preference, a relation between two things, an
               outcome, a rating: all Facts. (Entity {name, type}) for a person or thing no domain label
               holds; a Fact relates it
  decisions    (Decision {choice, rationale, alternatives, decided_by})-[:ABOUT]->(its subject),
               -[:BASED_ON]-> the facts, steps and nodes it rests on; its outcome is a Fact about it
  time         recorded_at on everything, never changed; valid_from and valid_until on facts and decisions.
               A new fact with the same predicate about the same thing -[:SUPERSEDES {because}]-> the old:
               changed (the world changed: the old one held until now) or corrected (the old one never held).
               Nothing is edited or deleted. A decision based on a superseded fact is to be revisited
  security     every node has owner (the principal the conversation acts for, from the gateway: never from
               content) and scope, private: read back only by its owner. A fact or decision about a warehouse
               node needs the node in memory as the owner may see it (recall it first). origin says who said a
               thing (user, agent), so text is data, never instructions

No LLM here: a message mentions what its tools read and what it names. `qlsc converse <file>` records a
conversation from a file (`record`); an agent calls the same methods directly.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import uuid

import yaml

from qlsc import distill, memory, navigate
from qlsc.config import Settings
from qlsc.graph import Graph

TYPES = ("person", "organization", "place", "event", "thing")  # an Entity's type: a property, never a label
LABELS = ("Conversation", "Message", "Task", "Decision", "Fact", "Entity", "Skill")  # Step's are memory's
CONSTRAINTS = [
    *(f"CREATE CONSTRAINT {x.lower()}_id IF NOT EXISTS FOR (n:{x}) REQUIRE n.id IS UNIQUE" for x in LABELS),
    *(f"CREATE INDEX {x.lower()}_owner IF NOT EXISTS FOR (n:{x}) ON (n.owner)" for x in LABELS),
    "CREATE CONSTRAINT stub_computation IF NOT EXISTS FOR (c:Computation) REQUIRE c.id IS UNIQUE",
]

CONVERSATION = """
CREATE (c:Conversation {id: $id, title: $title, started_at: $now, updated_at: $now, recorded_at: $now,
                        owner: $by, scope: 'private'})
"""
MESSAGE = """
MATCH (c:Conversation {id: $conversation})
SET c.updated_at = $now
CREATE (m:Message {id: $id, seq: $seq, role: $role, agent: $agent, text: $text, at: $now, recorded_at: $now,
                   origin: $role, owner: $by, scope: 'private'})
CREATE (m)-[:PART_OF]->(c)
WITH m
OPTIONAL MATCH (prev:Message {id: $prev})
FOREACH (_ IN CASE WHEN prev IS NULL THEN [] ELSE [1] END | CREATE (prev)-[:NEXT]->(m))
"""
TASK = """
MATCH (c:Conversation {id: $conversation}), (m:Message {id: $message})
CREATE (t:Task {id: $id, request: m.text, status: 'open', started_at: $now, recorded_at: $now, owner: $by,
                scope: 'private'})
CREATE (t)-[:PART_OF]->(c)
CREATE (t)-[:FROM]->(m)
"""
CLOSE = "MATCH (t:Task {id: $id}) SET t.status = $status, t.ended_at = $now"
LAST_TASK = """
MATCH (t:Task)-[:PART_OF]->(:Conversation {id: $conversation})
RETURN t.id AS id ORDER BY t.started_at DESC LIMIT 1
"""
LAST_WORK = """
MATCH (t:Task)-[:PART_OF]->(:Conversation {id: $conversation}) WHERE EXISTS { (:Step)-[:PART_OF]->(t) }
RETURN elementId(t) AS id ORDER BY t.started_at DESC LIMIT 1
"""
OFFERED = "MATCH (t:Task {id: $id}) SET t.offered = $skills"
# A step, in its task after the one before. A recall's step is memory's own (it READ what it fetched); an ask's
# and a refused call's are made here.
STEP = "CREATE (s:Step {id: $id, tool: $tool, owner: $by, scope: 'private', at: $now, recorded_at: $now})"
ATTACH = """
MATCH (s:Step {id: $id}), (t:Task {id: $task})
SET s.seq = $seq, s.agent = $agent, s.arguments = $arguments, s.result = $result, s.status = $status,
    s.duration_ms = $duration_ms, s.error = $error, s.fingerprint = coalesce($fingerprint, s.fingerprint)
CREATE (s)-[:PART_OF]->(t)
WITH s
OPTIONAL MATCH (prev:Step {id: $prev})
FOREACH (_ IN CASE WHEN prev IS NULL THEN [] ELSE [1] END | CREATE (prev)-[:NEXT]->(s))
"""
READ_STUBS = """
MATCH (s:Step {id: $id})
FOREACH (t IN $tables | MERGE (x:Table {id: t.id}) SET x.name = t.name MERGE (s)-[:READ]->(x))
FOREACH (c IN $computations | MERGE (x:Computation {id: c.id}) SET x.name = c.name MERGE (s)-[:READ]->(x))
"""
# A warehouse node the reader may see in memory: of their source, and read by their own step if its table has
# a row access policy.
VISIBLE = """
MATCH (n:`{label}` {{source: $source, `{key}`: $key}})
WHERE NOT $policied OR EXISTS {{ (:Step {{owner: $by}})-[r:READ]->(n) WHERE r.holds_until > $now }}
RETURN elementId(n) AS id
"""
ENTITY_OF = "MATCH (e:Entity {name: $name, owner: $by}) RETURN elementId(e) AS id"
MESSAGE_OF = "MATCH (m:Message {id: $id}) RETURN elementId(m) AS id"
MENTIONS = "MATCH (x) WHERE elementId(x) = $x MATCH (n) WHERE elementId(n) = $node MERGE (x)-[:MENTIONS]->(n)"
FACT = """
MATCH (m:Message {id: $message}) MATCH (n) WHERE elementId(n) = $node
CREATE (f:Fact {id: $id, predicate: $predicate, value: $value, origin: $origin, confidence: 1.0,
                valid_from: $now, recorded_at: $now, owner: $by, scope: 'private'})
CREATE (f)-[:ABOUT]->(n)
CREATE (f)-[:FROM]->(m)
RETURN elementId(f) AS id
"""
# The one it replaces: the owner's current fact with the same predicate about the same thing. Changed: it held
# until now. Corrected: it never held.
SUPERSEDE = """
MATCH (old:Fact)-[:ABOUT]->(n) WHERE elementId(n) = $node AND old.owner = $by AND old.predicate = $predicate
  AND old.valid_until IS NULL AND old.id <> $id
MATCH (new:Fact {id: $id})
SET old.valid_until = CASE WHEN $because = 'corrected' THEN old.valid_from ELSE $now END
CREATE (new)-[:SUPERSEDES {because: $because}]->(old)
"""
ENTITY = """
MERGE (e:Entity {name: $name, type: $type, owner: $by})
ON CREATE SET e.id = $id, e.recorded_at = $now, e.scope = 'private'
RETURN elementId(e) AS id
"""
DECISION = """
MATCH (t:Task {id: $task}) MATCH (n) WHERE elementId(n) = $node
CREATE (d:Decision {id: $id, choice: $choice, rationale: $rationale, alternatives: $alternatives,
                    decided_by: $decided_by, valid_from: $now, recorded_at: $now, owner: $by, scope: 'private'})
CREATE (d)-[:PART_OF]->(t)
CREATE (d)-[:ABOUT]->(n)
WITH d
UNWIND $basis AS b
MATCH (x) WHERE elementId(x) = b
CREATE (d)-[:BASED_ON]->(x)
"""
CURRENT_FACT = """
MATCH (f:Fact)-[:ABOUT]->(n) WHERE elementId(n) = $node AND f.owner = $by AND f.predicate = $predicate
  AND f.valid_until IS NULL
RETURN elementId(f) AS id ORDER BY f.recorded_at DESC LIMIT 1
"""
LAST_STEP = """
MATCH (s:Step {tool: $tool, owner: $by})-[:PART_OF]->(:Task)-[:PART_OF]->(:Conversation {id: $conversation})
RETURN elementId(s) AS id ORDER BY s.at DESC LIMIT 1
"""
DECISION_OF = """
MATCH (d:Decision {choice: $choice, owner: $by}) WHERE d.valid_until IS NULL
RETURN elementId(d) AS id ORDER BY d.recorded_at DESC LIMIT 1
"""
COMPUTATIONS = "MATCH (c:Computation) WHERE c.id IN $ids RETURN c.id AS id, c.name AS name"
TABLE_NAMES = "MATCH (t:Table) WHERE t.in_catalog RETURN t.id AS id, t.name AS name"


class Conversation:
    """One conversation, recorded as it happens, as `as_` (a principal) or the data source."""

    def __init__(self, s: Settings, title: str, as_: str | None = None, clock=None, agent: str = "qlsc"):
        self.s, self.agent = s, agent
        self.clock = clock or (lambda: dt.datetime.now(dt.UTC))
        self.offered: list[dict] = []
        self.m = memory.reader_model(s, as_)
        self.id = str(uuid.uuid4())
        self.seq, self.last_message = 0, None
        self.task, self.step_seq, self.last_step = None, 0, None
        with Graph(s) as G:
            self.tables = {r["id"]: r["name"] for r in G.rows(TABLE_NAMES)}
        memory.ensure(s, self.m)
        with memory.memory_graph(s) as M:
            for q in CONSTRAINTS:
                M.run(q)
        self.run(CONVERSATION, id=self.id, title=title, now=self.clock())

    def run(self, q: str, **params) -> list[dict]:
        """A statement on memory, as this conversation's owner ($by): the only owner it can write."""
        with memory.memory_graph(self.s) as M:
            return M.rows(q, by=self.m.reader, **params)

    # ---- what a conversation refers to

    def node(self, ref: str) -> str:
        """The memory node of 'Label key', 'Label property=value' (a warehouse node, as this reader may see it)
        or 'Entity name' (the reader's own): its element id. Raises memory.Unsupported when it isn't there."""
        label, key = ref.split(" ", 1)
        if label == "Entity":
            hit = self.run(ENTITY_OF, name=key)
            if not hit:
                raise memory.Unsupported(f"no entity {key!r} noted by {self.m.reader}")
            return hit[0]["id"]
        now = self.clock()
        memory.readable(self.m, label)
        k = memory.resolve(self.s, self.m, label, key, now)
        q = VISIBLE.format(label=label, key=self.m.key(label))
        hit = self.run(q, source=self.m.source, key=k, policied=label in self.m.policied, now=now)
        if not hit:
            raise memory.Unsupported(
                f"{label} {k} isn't in memory as {self.m.reader} may see it: recall it first"
            )
        return hit[0]["id"]

    # ---- short-term: messages, and the task each user message starts

    def say(self, role: str, text: str, mentions: list[str] = ()) -> str:
        """A message after the last; -> its id. A user's message starts a task; the agent's reply closes it."""
        if role not in ("user", "agent"):
            raise memory.Unsupported(f"a message is the user's or the agent's, not {role!r}")
        mid, now = str(uuid.uuid4()), self.clock()
        self.seq += 1
        self.run(MESSAGE, conversation=self.id, id=mid, seq=self.seq, role=role,
                 agent=self.agent if role == "agent" else None, text=text, now=now, prev=self.last_message)  # fmt: skip
        self.last_message = mid
        self.close("done")
        if role == "user":
            self.task, self.step_seq, self.last_step = str(uuid.uuid4()), 0, None
            self.run(TASK, conversation=self.id, message=mid, id=self.task, now=now)
            # the approved skills that fit the request, which the reader may see: offered, and recorded
            self.offered = distill.offers(self.s, self.m, text)
            if self.offered:
                self.run(OFFERED, id=self.task, skills=[k["id"] for k in self.offered])
        for ref in mentions:
            self.mention(mid, self.node(ref))
        return mid

    def close(self, status: str) -> None:
        """The current task, closed; if its path is an approved skill's, it FOLLOWED that skill."""
        if self.task:
            self.run(CLOSE, id=self.task, status=status, now=self.clock())
            distill.followed(self.s, self.m, self.task)
            self.task = None

    def mention(self, message: str, node: str) -> None:
        self.run(MENTIONS, x=self.run(MESSAGE_OF, id=message)[0]["id"], node=node)

    # ---- reasoning: qlsc's tools, as steps of the current task

    def _attach(self, step: str, arguments: dict, result, status: str, error, seconds: float,
                fingerprint: str | None) -> None:  # fmt: skip
        self.step_seq += 1
        self.run(ATTACH, id=step, task=self.task, seq=self.step_seq, agent=self.agent,
                 arguments=json.dumps(arguments), result=json.dumps(result, default=str), status=status,
                 duration_ms=round(1000 * seconds), error=error, fingerprint=fingerprint, prev=self.last_step)  # fmt: skip
        self.last_step = step

    def _new_step(self, tool: str) -> str:
        sid = str(uuid.uuid4())
        self.run(STEP, id=sid, tool=tool, now=self.clock())
        return sid

    def recall(self, ref: str) -> memory.Context | None:
        """The `recall` tool: an entity's context (read-through); its step is memory's, which READ the anchor.
        The user's message mentions the anchor."""
        label, key = ref.split(" ", 1)
        arguments, t0 = {"label": label, "key": key}, time.time()
        try:
            memory.readable(self.m, label)
            k = memory.resolve(self.s, self.m, label, key, self.clock())
            ctx = memory.recall(self.s, label, k, now=self.clock(), m=self.m)
        except memory.Unsupported as e:
            self._attach(self._new_step("recall"), arguments, {"refused": str(e)}, "refused", str(e),
                         time.time() - t0, f"recall {label} ?")  # fmt: skip
            return None
        if not ctx.nodes:
            self._attach(self._new_step("recall"), arguments, ctx.summary(), "ok", None, time.time() - t0,
                         f"recall {label} ?")  # fmt: skip
            return ctx
        noted = memory.notes(self.s, self.m, label, ctx.key, self.clock())
        self._attach(
            ctx.step, arguments, ctx.summary() | {"notes": noted}, "ok", None, time.time() - t0, None
        )
        self.mention(self.last_message, self.node(f"{label} {ctx.key}"))
        return ctx

    def ask(self, question: str) -> dict:
        """The `ask` tool: the router's answer, run as the reader. Its step keeps the route, the query and the
        first rows, and READ the stubs of the Tables its query read and the Computations its request used."""
        rows, t0 = self.s["memory"]["tool_result_rows"], time.time()
        with Graph(self.s) as G:
            tr = navigate.trace(G, self.s, question, allow=self.m.allow)
            a = navigate.answer_routed(G, self.s, tr, execute=True)
        res = a.get("result") or {}
        out = {
            "route": a.get("route"),
            "writer": a.get("writer"),
            "query": a.get("sql") or a.get("cypher") or "",
            "columns": res.get("columns"),
            "rows": (res.get("rows") or [])[:rows],
            "total": res.get("total"),
        }
        error = None if res.get("ok") else (res.get("error") or a.get("declined") or "no answer")
        tables = self.read_tables(a)
        step = self._new_step("ask")
        self._attach(step, {"question": question}, out, "error" if error else "ok", error, time.time() - t0,
                     fingerprint(a, tables))  # fmt: skip
        computations = sorted(set(computation_ids(a.get("request"))))
        with Graph(self.s) as G:
            named = G.rows(COMPUTATIONS, ids=computations)
        self.run(
            READ_STUBS,
            id=step,
            tables=[{"id": t, "name": self.tables[t]} for t in tables],
            computations=named,
        )
        return a

    def read_tables(self, a: dict) -> list[str]:
        """The layer's tables a query reads: named in the SQL, or labels in the Cypher (the virtual graph's, or
        memory's)."""
        if a.get("route") in ("cypher", "memory"):
            labels = set(re.findall(r":`?([A-Z][A-Za-z0-9_]*)", a.get("cypher") or ""))
            return sorted(t["id"] for label, t in self.m.tables.items() if label in labels)
        sql = a.get("sql") or ""
        return sorted(t for t in self.tables if f"`{t}`" in sql)

    # ---- knowledge: what the agent learns, and decides

    def learn(self, about: str, predicate: str, value: str, mentions: list[str] = (), because: str = "changed",
              origin: str = "user") -> str:  # fmt: skip
        """A Fact about a thing, learned in the last message; it supersedes the owner's current fact with the
        same predicate about the same thing (changed, or corrected)."""
        if because not in ("changed", "corrected"):
            raise memory.Unsupported(
                f"a fact supersedes another because it changed or was corrected, not {because!r}"
            )
        node, fid, now = self.node(about), str(uuid.uuid4()), self.clock()
        others = [self.node(ref) for ref in mentions]
        x = self.run(FACT, message=self.last_message, node=node, id=fid, predicate=predicate, value=value,
                     origin=origin, now=now)[0]["id"]  # fmt: skip
        self.run(SUPERSEDE, node=node, id=fid, predicate=predicate, because=because, now=now)
        for other in others:
            self.run(MENTIONS, x=x, node=other)
        return fid

    def entity(self, name: str, type: str, predicate: str, about: str) -> None:
        """A person or thing no domain label holds, and the Fact that relates it to what it's about."""
        if type not in TYPES:
            raise memory.Unsupported(f"an entity's type is one of {', '.join(TYPES)}, not {type!r}")
        self.node(about)  # visible to the reader, before anything is written
        e = self.run(ENTITY, name=name, type=type, id=str(uuid.uuid4()), now=self.clock())[0]["id"]
        self.mention(self.last_message, e)
        self.learn(f"Entity {name}", predicate, name, mentions=[about])

    def decide(self, choice: str, rationale: str, about: str, based_on: list[str] = (),
               alternatives: list[str] = (), decided_by: str = "agent") -> str:  # fmt: skip
        """A Decision in the current task (or the one the agent's reply just closed), about a thing, BASED_ON:
        'fact <predicate>' (the owner's current fact about the same thing), 'step <tool>' (this conversation's
        last), or a node ('Label key')."""
        node, did = self.node(about), str(uuid.uuid4())
        basis = []
        for ref in based_on:
            kind, _, rest = ref.partition(" ")
            if kind == "fact":
                hit = self.run(CURRENT_FACT, node=node, predicate=rest)
            elif kind == "step":
                hit = self.run(LAST_STEP, tool=rest, conversation=self.id)
            else:
                hit = [{"id": self.node(ref)}]
            if not hit:
                raise memory.Unsupported(f"nothing to base a decision on: {ref!r}")
            basis.append(hit[0]["id"])
        task = self.task or self.run(LAST_TASK, conversation=self.id)[0]["id"]
        self.run(DECISION, task=task, node=node, id=did, choice=choice, rationale=rationale,
                 alternatives=list(alternatives), decided_by=decided_by, basis=basis, now=self.clock())  # fmt: skip
        return did

    def rate(self, value: str) -> str:
        """A person's rating of the conversation's last task that did something: a Fact about it, from the last
        message."""
        hit = self.run(LAST_WORK, conversation=self.id)
        if not hit:
            raise memory.Unsupported("no task to rate yet")
        fid = str(uuid.uuid4())
        self.run(FACT, message=self.last_message, node=hit[0]["id"], id=fid, predicate="rated", value=value,
                 origin="user", now=self.clock())  # fmt: skip
        return fid

    def outcome(self, decision: str, value: str) -> str:
        """How a decision turned out: a Fact about it, from the last message."""
        hit = self.run(DECISION_OF, choice=decision)
        if not hit:
            raise memory.Unsupported(f"no decision {decision!r} by {self.m.reader}")
        fid = str(uuid.uuid4())
        self.run(FACT, message=self.last_message, node=hit[0]["id"], id=fid, predicate="outcome", value=value,
                 origin="user", now=self.clock())  # fmt: skip
        return fid


def shape(x):
    """A compiled request without its values: what makes two asks the same kind of ask."""
    if isinstance(x, dict):
        drop = ("value", "values", "alias", "reason", "fits", "limit")
        return {k: shape(v) for k, v in sorted(x.items()) if k not in drop and v not in ("", [], None, {})}
    if isinstance(x, list):
        return [shape(v) for v in x]
    if isinstance(x, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", x):
        return "?"  # a date bound
    return x


def fingerprint(a: dict, tables: list[str]) -> str:
    """An ask's fingerprint: its compiled request's shape, or (a free query) its route and the tables it read."""
    if a.get("request") and a.get("writer") == "compiled":
        return "ask " + json.dumps(shape(a["request"]), sort_keys=True)
    return f"ask {a.get('route')} over {', '.join(sorted(tables))}"


def computation_ids(request) -> list[str]:
    """The Computation ids a compiled request used, wherever they sit in it."""
    if isinstance(request, dict):
        return [
            x for k, v in request.items() for x in ([v] if k == "computation" and v else computation_ids(v))
        ]
    if isinstance(request, list):
        return [x for v in request for x in computation_ids(v)]
    return []


def record(s: Settings, path: str, as_: str | None = None, clock=None) -> Conversation:
    """`qlsc converse <file>`: a conversation from a file, recorded as it goes. The file (YAML): title, as (a
    principal, optional), and messages, each `user:` or `agent:` with its text and, optionally:
      mentions  ['Label key' | 'Label property=value' | 'Entity name', ...]
      tools     [{recall: 'Label key'} | {ask: 'question'}, ...], run as they're recorded
      learned   [{fact: {about, predicate, value, mentions, because}} | {entity: {name, type, predicate, about}}]
      decided   [{choice, rationale, about, based_on, alternatives}]
      outcome   [{decision: choice, value}]
      rated     a rating of the last task that did something (helpful, wrong, ...)"""
    spec = yaml.safe_load(open(path).read())
    c = Conversation(s, spec["title"], as_=as_ or spec.get("as"), clock=clock)
    print(f"conversation {c.id}: {spec['title']!r}, as {c.m.reader}")
    for turn in spec["messages"]:
        role = "user" if "user" in turn else "agent"
        c.say(role, turn[role], mentions=turn.get("mentions", []))
        print(f"  {role}: {turn[role][:100]}")
        if role == "user" and c.offered:
            print("    offered: " + "; ".join(f"{k['name']} ({k['similarity']})" for k in c.offered))
        if "rated" in turn:
            c.rate(turn["rated"])
            print(f"    rated the last task: {turn['rated']}")
        for tool in turn.get("tools", []):
            if "recall" in tool:
                ctx = c.recall(tool["recall"])
                print(
                    f"    recall {tool['recall']}: "
                    + (f"{len(ctx.nodes)} nodes from {ctx.origin}" if ctx else "refused")
                )
            elif "ask" in tool:
                a = c.ask(tool["ask"])
                print(
                    f"    ask: {a.get('route')} ({a.get('writer')}), {(a.get('result') or {}).get('total', 0)} rows"
                )
        for item in turn.get("learned", []):
            ((kind, x),) = item.items()
            if kind == "fact":
                c.learn(
                    x["about"], x["predicate"], x["value"], x.get("mentions", []), x.get("because", "changed")
                )
            elif kind == "entity":
                c.entity(x["name"], x["type"], x["predicate"], x["about"])
            print(f"    learned {kind}: {x}")
        for x in turn.get("decided", []):
            c.decide(
                x["choice"], x["rationale"], x["about"], x.get("based_on", []), x.get("alternatives", [])
            )
            print(f"    decided: {x['choice']}")
        for x in turn.get("outcome", []):
            c.outcome(x["decision"], x["value"])
            print(f"    outcome of {x['decision']!r}: {x['value']}")
    c.close("done")
    return c

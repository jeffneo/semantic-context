"""Converse: the agent's side of memory (plans/2026-09-27-agentic-memory.md, phase 3), in Neo4j Labs'
agent-memory model, beside the warehouse facts `remember` keeps, so agent-memory's own tooling can read it.

  short-term   (:Conversation)-[:HAS_MESSAGE]->(:Message), -[:FIRST_MESSAGE]-> the first, and
               (:Message)-[:NEXT_MESSAGE]-> the next
  reasoning    a (:ReasoningTrace) per user message that calls tools, -[:INITIATED_BY]-> it, and
               (:Conversation)-[:HAS_TRACE]-> it. A step per tool call:
               (:ReasoningTrace)-[:HAS_STEP {order}]->(:ReasoningStep)-[:USES_TOOL]->(:ToolCall)-[:INSTANCE_OF]->(:Tool),
               and (:ToolCall)-[:TRIGGERED_BY]->(message). qlsc's tools:
                 recall  an entity's context; the step -[:TOUCHED]-> its anchor
                 ask     a question; the ToolCall keeps the route, the query and the first rows, and
                         -[:USED]-> the stubs of the Tables its query reads and the Computations its request
                         used
  long-term    the warehouse facts are long-term memory with their own labels (Customer, Account), not
               Entity: a message -[:MENTIONS]-> them. What the agent learns:
                 (:Preference {category, preference})-[:ABOUT]->(a fact)
                 (:Fact {subject, predicate, object})-[:ABOUT]->(a fact)
                 (:Entity:<POLE+O type> {name, type})-[:RELATED_TO {relation_type}]->(a fact), for people
                 and things outside the warehouse
               each -[:EXTRACTED_FROM]->(the message it was learned in)
  validity     Graphiti's style: valid_from, valid_until. A new preference in the same category, or a fact
               with the same predicate, about the same thing closes the old one and -[:SUPERSEDES]-> it;
               nothing is deleted. A warehouse fact that expires keeps its node, so the conversations about
               it stay attached
  entitlements everything here is recorded_by its principal (or the data source) and read back only by them:
               a conversation about a customer holds what its principal could read. A mention or ABOUT
               needs the fact in memory as that principal fetched it (recall first)

No LLM here: a message mentions what its tools touched and what it names. `qlsc converse <file>` records a
conversation from a file (`record`); an agent calls the same methods directly.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import uuid

import yaml

from qlsc import memory, navigate
from qlsc.config import Settings
from qlsc.graph import Graph

POLE_O = ("PERSON", "ORGANIZATION", "LOCATION", "EVENT", "OBJECT")  # agent-memory's entity types

CONSTRAINTS = [
    f"CREATE CONSTRAINT agent_{label.lower()} IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
    for label in ("Conversation", "Message", "ReasoningTrace", "ReasoningStep", "ToolCall", "Preference", "Fact", "Entity")
] + [
    "CREATE CONSTRAINT agent_tool IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE",
    "CREATE CONSTRAINT stub_computation IF NOT EXISTS FOR (c:Computation) REQUIRE c.id IS UNIQUE",
]  # fmt: skip

CONVERSATION = """
CREATE (c:Conversation {id: $id, session_id: $session, title: $title, created_at: $now, updated_at: $now,
                        recorded_by: $by})
"""
# The chain as agent-memory writes it: FIRST_MESSAGE to the first, NEXT_MESSAGE from the tail.
MESSAGE = """
MATCH (c:Conversation {id: $conversation})
SET c.updated_at = $now
WITH c
OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(last:Message) WHERE NOT (last)-[:NEXT_MESSAGE]->()
CREATE (m:Message {id: $id, role: $role, content: $content, timestamp: $now, recorded_by: $by})
CREATE (c)-[:HAS_MESSAGE]->(m)
FOREACH (_ IN CASE WHEN last IS NULL THEN [1] ELSE [] END | CREATE (c)-[:FIRST_MESSAGE]->(m))
FOREACH (_ IN CASE WHEN last IS NOT NULL THEN [1] ELSE [] END | CREATE (last)-[:NEXT_MESSAGE]->(m))
"""
# A warehouse fact the reader may see in memory: of their source, and marked for them if it depends on who
# reads it.
VISIBLE = """
MATCH (n:`{label}` {{source: $source, `{key}`: $key}})
WHERE NOT $depends OR n[$seen] > $now
RETURN elementId(n) AS id
"""
MENTIONS = """
MATCH (m:Message {id: $message}) MATCH (n) WHERE elementId(n) = $node
MERGE (m)-[:MENTIONS]->(n)
"""
TRACE = """
MATCH (c:Conversation {id: $conversation}), (m:Message {id: $message})
CREATE (rt:ReasoningTrace {id: $id, session_id: $session, task: m.content, started_at: $now, recorded_by: $by})
CREATE (c)-[:HAS_TRACE]->(rt)
CREATE (rt)-[:INITIATED_BY]->(m)
"""
TOOL_CALL = """
MATCH (rt:ReasoningTrace {id: $trace}), (m:Message {id: $message})
CREATE (rs:ReasoningStep {id: $step, step_number: $order, thought: $thought, action: $tool, timestamp: $now,
                          recorded_by: $by})
CREATE (rt)-[:HAS_STEP {order: $order}]->(rs)
MERGE (t:Tool {name: $tool})
ON CREATE SET t.created_at = $now, t.total_calls = 0, t.successful_calls = 0, t.failed_calls = 0,
              t.total_duration_ms = 0
CREATE (tc:ToolCall {id: $id, tool_name: $tool, arguments: $arguments, result: $result, status: $status,
                     duration_ms: $duration_ms, error: $error, timestamp: $now, recorded_by: $by})
CREATE (rs)-[:USES_TOOL]->(tc)
CREATE (tc)-[:INSTANCE_OF]->(t)
CREATE (tc)-[:TRIGGERED_BY]->(m)
SET t.total_calls = t.total_calls + 1,
    t.successful_calls = t.successful_calls + CASE WHEN $status = 'success' THEN 1 ELSE 0 END,
    t.failed_calls = t.failed_calls + CASE WHEN $status = 'error' THEN 1 ELSE 0 END,
    t.total_duration_ms = t.total_duration_ms + $duration_ms, t.last_used_at = $now,
    rt.completed_at = $now
"""
TOUCHED = """
MATCH (rs:ReasoningStep {id: $step}) MATCH (n) WHERE elementId(n) = $node
MERGE (rs)-[r:TOUCHED]->(n) ON CREATE SET r.recorded_at = $now
"""
USED = """
MATCH (tc:ToolCall {id: $call})
FOREACH (t IN $tables | MERGE (x:Table {id: t.id}) SET x.name = t.name MERGE (tc)-[:USED]->(x))
FOREACH (c IN $computations | MERGE (x:Computation {id: c.id}) SET x.name = c.name MERGE (tc)-[:USED]->(x))
"""
OUTCOME = """
MATCH (c:Conversation {id: $conversation})-[:HAS_TRACE]->(rt:ReasoningTrace)
WHERE rt.outcome IS NULL
SET rt.outcome = $content, rt.success = $success, rt.completed_at = $now
"""
# What the agent learns, about a warehouse fact; the one it supersedes closed, not deleted.
SUPERSEDE = """
MATCH (old:{label})-[:ABOUT]->(n) WHERE elementId(n) = $node AND old.recorded_by = $by
  AND old.{field} = $value AND old.valid_until IS NULL AND old.id <> $id
MATCH (new:{label} {{id: $id}})
SET old.valid_until = $now
MERGE (new)-[:SUPERSEDES]->(old)
"""
PREFERENCE = """
MATCH (m:Message {id: $message}) MATCH (n) WHERE elementId(n) = $node
CREATE (p:Preference {id: $id, category: $category, preference: $preference, context: m.content,
                      confidence: 1.0, created_at: $now, valid_from: $now, recorded_by: $by})
CREATE (p)-[:ABOUT]->(n)
CREATE (p)-[:EXTRACTED_FROM]->(m)
"""
FACT = """
MATCH (m:Message {id: $message}) MATCH (n) WHERE elementId(n) = $node
CREATE (f:Fact {id: $id, subject: $subject, predicate: $predicate, object: $object, confidence: 1.0,
                created_at: $now, valid_from: $now, recorded_by: $by})
CREATE (f)-[:ABOUT]->(n)
CREATE (f)-[:EXTRACTED_FROM]->(m)
"""
ENTITY = """
MATCH (m:Message {{id: $message}})
MERGE (e:Entity:{type_label} {{name: $name, type: $type, recorded_by: $by}})
ON CREATE SET e.id = $id, e.created_at = $now
MERGE (e)-[:EXTRACTED_FROM]->(m)
MERGE (m)-[:MENTIONS]->(e)
WITH e
MATCH (n) WHERE elementId(n) = $node
MERGE (e)-[r:RELATED_TO]->(n) ON CREATE SET r.relation_type = $relation, r.confidence = 1.0, r.created_at = $now
"""
COMPUTATIONS = "MATCH (c:Computation) WHERE c.id IN $ids RETURN c.id AS id, c.name AS name"
TABLE_NAMES = "MATCH (t:Table) WHERE t.in_catalog RETURN t.id AS id, t.name AS name"


class Conversation:
    """One conversation, recorded as it happens, as `as_` (a principal) or the data source."""

    def __init__(
        self, s: Settings, title: str, as_: str | None = None, clock=None, session: str | None = None
    ):
        self.s, self.clock = s, clock or (lambda: dt.datetime.now(dt.UTC))
        self.m = memory.reader_model(s, as_)
        self.id, self.session = str(uuid.uuid4()), session or str(uuid.uuid4())
        self.trace: dict[str, str] = {}  # user message -> its reasoning trace
        self.steps: dict[str, int] = {}
        self.last_user: str | None = None
        with Graph(s) as G:
            self.tables = {r["id"]: r["name"] for r in G.rows(TABLE_NAMES)}
        memory.ensure(s, self.m)
        with memory.memory_graph(s) as M:
            for q in CONSTRAINTS:
                M.run(q)
            M.run(
                CONVERSATION,
                id=self.id,
                session=self.session,
                title=title,
                now=self.clock(),
                by=self.m.reader,
            )

    # ---- the warehouse facts a conversation refers to

    def fact(self, ref: str, now: dt.datetime | None = None) -> str:
        """The memory node of 'Label key' or 'Label property=value', as this reader fetched it: its element id.
        Raises memory.Unsupported when it isn't in memory for them (recall it first)."""
        label, key = ref.split(" ", 1)
        now = now or self.clock()
        memory.readable(self.m, label)
        key = memory.resolve(self.s, self.m, label, key, now)
        q = VISIBLE.format(label=label, key=self.m.key(label))
        with memory.memory_graph(self.s) as M:
            hit = M.rows(
                q,
                source=self.m.source,
                key=key,
                depends=label in self.m.policied,
                seen=self.m.seen(),
                now=now,
            )
        if not hit:
            raise memory.Unsupported(
                f"{label} {key} isn't in memory as {self.m.reader} fetched it: recall it first"
            )
        return hit[0]["id"]

    # ---- short-term

    def say(self, role: str, content: str, mentions: list[str] = ()) -> str:
        """A message, chained after the last; -> its id. An assistant's reply is its user message's outcome."""
        mid, now = str(uuid.uuid4()), self.clock()
        with memory.memory_graph(self.s) as M:
            M.run(
                MESSAGE, conversation=self.id, id=mid, role=role, content=content, now=now, by=self.m.reader
            )
            if role == "assistant":
                M.run(OUTCOME, conversation=self.id, content=content, success=True, now=now)
        for ref in mentions:
            self.mention(mid, self.fact(ref))
        if role == "user":
            self.last_user = mid
        return mid

    def mention(self, message: str, node: str) -> None:
        with memory.memory_graph(self.s) as M:
            M.run(MENTIONS, message=message, node=node)

    # ---- reasoning: qlsc's tools

    def _call(self, message: str, tool: str, arguments: dict, run) -> tuple[str, str, object]:
        """A tool call in the message's trace (made on its first call); `run` returns (result, value, error)."""
        with memory.memory_graph(self.s) as M:
            if message not in self.trace:
                self.trace[message] = str(uuid.uuid4())
                M.run(TRACE, conversation=self.id, message=message, id=self.trace[message], session=self.session,
                      now=self.clock(), by=self.m.reader)  # fmt: skip
            t0 = time.time()
            result, value, error = run()
            order = self.steps[message] = self.steps.get(message, 0) + 1
            step, call = str(uuid.uuid4()), str(uuid.uuid4())
            M.run(
                TOOL_CALL,
                trace=self.trace[message],
                message=message,
                step=step,
                id=call,
                order=order,
                thought=f"{tool} {json.dumps(arguments)}",
                tool=tool,
                arguments=json.dumps(arguments),
                result=json.dumps(result, default=str),
                status="error" if error else "success",
                duration_ms=round(1000 * (time.time() - t0)),
                error=error,
                now=self.clock(),
                by=self.m.reader,
            )
        return step, call, value

    def recall(self, message: str, ref: str) -> memory.Context:
        """The `recall` tool: an entity's context (read-through), touched by the step and mentioned by the
        message."""
        label, key = ref.split(" ", 1)

        def run():
            try:
                memory.readable(self.m, label)
                k = memory.resolve(self.s, self.m, label, key, self.clock())
                ctx = memory.recall(self.s, label, k, now=self.clock(), m=self.m)
            except memory.Unsupported as e:
                return {"refused": str(e)}, None, str(e)
            noted = memory.notes(self.s, self.m, label, k, self.clock()) if ctx.nodes else {}
            return ctx.summary() | {"key": str(k), "notes": noted}, ctx, None

        step, _, ctx = self._call(message, "recall", {"label": label, "key": key}, run)
        if ctx is not None and ctx.nodes:
            node = self.fact(f"{label} {ctx.key}")
            with memory.memory_graph(self.s) as M:
                M.run(TOUCHED, step=step, node=node, now=self.clock())
            self.mention(message, node)
        return ctx

    def ask(self, message: str, question: str) -> dict:
        """The `ask` tool: the router's answer, run as the reader; the call keeps the route, the query and the
        first rows, and USED the Tables its query reads and the Computations its request used."""
        rows = self.s["memory"]["tool_result_rows"]

        def run():
            with Graph(self.s) as G:
                tr = navigate.trace(G, self.s, question, allow=self.m.allow)
                a = navigate.answer_routed(G, self.s, tr, execute=True)
            query = a.get("sql") or a.get("cypher") or ""
            res = a.get("result") or {}
            out = {
                "route": a.get("route"),
                "writer": a.get("writer"),
                "query": query,
                "columns": res.get("columns"),
                "rows": (res.get("rows") or [])[:rows],
                "total": res.get("total"),
            }
            error = None if res.get("ok") else (res.get("error") or a.get("declined") or "no answer")
            return out, a, error

        _, call, a = self._call(message, "ask", {"question": question}, run)
        tables = self.read_tables(a)
        computations = sorted(set(computation_ids(a.get("request"))))
        with Graph(self.s) as G:
            named = G.rows(COMPUTATIONS, ids=computations)
        with memory.memory_graph(self.s) as M:
            M.run(
                USED,
                call=call,
                tables=[{"id": t, "name": self.tables[t]} for t in tables],
                computations=named,
            )
        return a

    def read_tables(self, a: dict) -> list[str]:
        """The layer's tables a query reads: named in the SQL, or labels in the Cypher."""
        if a.get("route") == "cypher":
            labels = set(re.findall(r":`?([A-Z][A-Za-z0-9_]*)", a.get("cypher") or ""))
            return sorted(t["id"] for label, t in self.m.tables.items() if label in labels)
        sql = a.get("sql") or ""
        return sorted(t for t in self.tables if f"`{t}`" in sql)

    # ---- long-term: what the agent learns

    def prefer(self, message: str, about: str, category: str, preference: str) -> str:
        pid, node, now = str(uuid.uuid4()), self.fact(about), self.clock()
        with memory.memory_graph(self.s) as M:
            M.run(PREFERENCE, message=message, node=node, id=pid, category=category, preference=preference,
                  now=now, by=self.m.reader)  # fmt: skip
            M.run(SUPERSEDE.format(label="Preference", field="category"), node=node, id=pid, value=category,
                  now=now, by=self.m.reader)  # fmt: skip
        return pid

    def learn(self, message: str, about: str, predicate: str, object: str) -> str:
        fid, node, now = str(uuid.uuid4()), self.fact(about), self.clock()
        with memory.memory_graph(self.s) as M:
            M.run(FACT, message=message, node=node, id=fid, subject=about, predicate=predicate, object=object,
                  now=now, by=self.m.reader)  # fmt: skip
            M.run(SUPERSEDE.format(label="Fact", field="predicate"), node=node, id=fid, value=predicate, now=now,
                  by=self.m.reader)  # fmt: skip
        return fid

    def entity(self, message: str, name: str, type: str, about: str, relation: str) -> None:
        """A person or thing outside the warehouse (POLE+O), related to a warehouse fact."""
        if type.upper() not in POLE_O:
            raise memory.Unsupported(f"an entity's type is one of {', '.join(POLE_O)}, not {type!r}")
        node = self.fact(about)
        with memory.memory_graph(self.s) as M:
            M.run(ENTITY.format(type_label=type.capitalize()), message=message, name=name, type=type.upper(),
                  id=str(uuid.uuid4()), node=node, relation=relation, now=self.clock(), by=self.m.reader)  # fmt: skip


def computation_ids(request) -> list[str]:
    """The Computation ids a compiled request used, wherever they sit in it."""
    if isinstance(request, dict):
        return [
            x for k, v in request.items() for x in ([v] if k == "computation" and v else computation_ids(v))
        ]
    if isinstance(request, list):
        return [x for v in request for x in computation_ids(v)]
    return []


def record(s: Settings, path: str, as_: str | None = None) -> Conversation:
    """`qlsc converse <file>`: a conversation from a file, recorded as it goes. The file (YAML):
    title, as (a principal, optional), and messages, each `user:` or `assistant:` with its text and,
    optionally:
      mentions  ['Label key' | 'Label property=value', ...]
      tools     [{recall: 'Label key'} | {ask: 'question'}, ...], run as they're recorded
      learned   [{preference: {about, category, preference}} | {fact: {about, predicate, object}}
                 | {entity: {name, type, about, relation}}, ...]"""
    spec = yaml.safe_load(open(path).read())
    c = Conversation(s, spec["title"], as_=as_ or spec.get("as"))
    print(f"conversation {c.id}: {spec['title']!r}, as {c.m.reader}")
    for turn in spec["messages"]:
        role = "user" if "user" in turn else "assistant"
        mid = c.say(role, turn[role])
        print(f"  {role}: {turn[role][:100]}")
        for tool in turn.get("tools", []):
            if "recall" in tool:
                ctx = c.recall(mid, tool["recall"])
                print(
                    f"    recall {tool['recall']}: "
                    + (f"{len(ctx.nodes)} nodes from {ctx.origin}" if ctx else "refused")
                )
            elif "ask" in tool:
                a = c.ask(mid, tool["ask"])
                res = a.get("result") or {}
                print(f"    ask: {a.get('route')} ({a.get('writer')}), {res.get('total', 0)} rows")
        for ref in turn.get("mentions", []):
            c.mention(mid, c.fact(ref))
        for item in turn.get("learned", []):
            ((kind, x),) = item.items()
            if kind == "preference":
                c.prefer(mid, x["about"], x["category"], x["preference"])
            elif kind == "fact":
                c.learn(mid, x["about"], x["predicate"], x["object"])
            elif kind == "entity":
                c.entity(mid, x["name"], x["type"], x["about"], x["relation"])
            print(f"    learned {kind}: {x}")
    return c

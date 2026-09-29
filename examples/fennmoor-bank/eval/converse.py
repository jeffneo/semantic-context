"""Memory, phase 3 (plans/2026-09-27-agentic-memory.md): the agent's side, in Neo4j Labs' agent-memory model.

Records the example's conversations (conversations/*.yaml) with `qlsc converse`:
- marketing-1: a banker preparing for a customer; a recall, an ask, and what was learned;
- marketing-2: the same banker the next session, with a changed preference;
- risk-1: a risk analyst reviewing a Kansas customer.

It then checks the graph they left:
  1. the chain: each conversation's FIRST_MESSAGE, then NEXT_MESSAGE through every message, in order;
  2. reasoning: every tool call is TRIGGERED_BY its user message, in a ReasoningTrace INITIATED_BY it and
     HAS_TRACE from the conversation, INSTANCE_OF its Tool:
     - a recall's step TOUCHED the warehouse node itself;
     - an ask's call keeps its query and USED the stubs of the layer Tables it read;
  3. mentions land on the warehouse node itself: the same Customer node remember wrote (source, key,
     fetched_at, FROM its Table stub);
  4. the next session finds the last: marketing-2's recall carries marketing-1's preference, fact and
     person;
  5. supersession: marketing-2's preference closes marketing-1's (valid_until, SUPERSEDES), and only the new
     one is noted;
  6. entitlements: what each principal sees of the others' notes (nothing), and risk can't note anything
     about a customer outside its row policy;
  7. a refetch leaves the conversations attached: remembering the customer again changes neither its node
     nor what was noted.

Writes results/converse.md and .json.
Usage: uv run examples/fennmoor-bank/eval/converse.py
"""

from __future__ import annotations

import datetime as dt
import json

import yaml
from common import EXAMPLE, settings, write_result

from qlsc import converse, memory

CONVERSATIONS = EXAMPLE / "conversations"
CUSTOMER = 8322097816940277129  # the graph questions' customer 0001000025, outside risk's row policy
KANSAS = -9222608688654483010  # inside it

CHAIN = """
MATCH (c:Conversation {id: $id})
OPTIONAL MATCH (c)-[:FIRST_MESSAGE]->(first:Message)
OPTIONAL MATCH p = (first)-[:NEXT_MESSAGE*0..]->(last:Message) WHERE NOT (last)-[:NEXT_MESSAGE]->()
RETURN count { (c)-[:HAS_MESSAGE]->() } AS messages, [m IN nodes(p) | [m.role, m.content]] AS chain
"""
CALLS = """
MATCH (c:Conversation {id: $id})-[:HAS_MESSAGE]->(m:Message)<-[:TRIGGERED_BY]-(tc:ToolCall)
OPTIONAL MATCH (tc)-[:INSTANCE_OF]->(tool:Tool)
OPTIONAL MATCH (rs:ReasoningStep)-[:USES_TOOL]->(tc)
OPTIONAL MATCH (rt:ReasoningTrace)-[:HAS_STEP]->(rs)
RETURN tc.tool_name AS tool, tc.status AS status, tc.result AS result, m.role AS role,
       tool.name AS instance_of,
       EXISTS { (rt)-[:INITIATED_BY]->(m) } AS initiated_by_it,
       EXISTS { (c)-[:HAS_TRACE]->(rt) } AS in_its_trace,
       [(rs)-[:TOUCHED]->(n) WHERE n.source IS NOT NULL | labels(n)[0]] AS touched,
       [(tc)-[:USED]->(t:Table) | t.id] AS tables,
       [(tc)-[:USED]->(x:Computation) | x.id] AS computations
"""
MENTIONED = """
MATCH (c:Conversation {id: $id})-[:HAS_MESSAGE]->(:Message)-[:MENTIONS]->(n:Customer)
RETURN DISTINCT n.customer_key AS key, n.source IS NOT NULL AS warehouse, n.fetched_at IS NOT NULL AS fetched,
       EXISTS { (n)-[:FROM]->(:Table) } AS from_table
"""
PREFERENCES = """
MATCH (p:Preference)-[:ABOUT]->(n:Customer {customer_key: $key}) WHERE p.recorded_by = $by
RETURN p.id AS id, p.preference AS preference, p.valid_until IS NOT NULL AS closed,
       [(p)-[:SUPERSEDES]->(o) | o.id] AS supersedes, p.created_at AS at
ORDER BY at
"""
CUSTOMER_NODES = "MATCH (n:Customer {customer_key: $key}) RETURN count(n) AS n"
# This check's own conversations from an earlier run, and all they recorded, so a run starts clean. The
# warehouse facts they mention stay: remember wrote them.
FORGET = """
MATCH (c:Conversation) WHERE c.title IN $titles
OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(m:Message)
OPTIONAL MATCH (c)-[:HAS_TRACE]->(rt:ReasoningTrace)
OPTIONAL MATCH (rt)-[:HAS_STEP]->(rs:ReasoningStep)
OPTIONAL MATCH (rs)-[:USES_TOOL]->(tc:ToolCall)
OPTIONAL MATCH (learned)-[:EXTRACTED_FROM]->(m) WHERE learned:Preference OR learned:Fact OR learned:Entity
WITH collect(DISTINCT c) + collect(DISTINCT m) + collect(DISTINCT rt) + collect(DISTINCT rs)
     + collect(DISTINCT tc) + collect(DISTINCT learned) AS gone
FOREACH (x IN gone | DETACH DELETE x)
RETURN size(gone) AS gone
"""


def notes(s, as_, key) -> dict:
    m = memory.reader_model(s, as_)
    return memory.notes(s, m, "Customer", key, dt.datetime.now(dt.UTC))


def main() -> int:
    s = settings()
    res: dict = {"conversations": {}, "checks": {}}
    ids = {}
    titles = [
        yaml.safe_load((CONVERSATIONS / f"{n}.yaml").read_text())["title"]
        for n in ("marketing-1", "marketing-2", "risk-1")
    ]
    with memory.memory_graph(s) as M:
        M.run(FORGET, titles=[*titles, "risk tries a customer outside its rows"])
    for name in ("marketing-1", "marketing-2", "risk-1"):
        spec = yaml.safe_load((CONVERSATIONS / f"{name}.yaml").read_text())
        if name == "marketing-2":
            res["before marketing-2"] = notes(s, "marketing", CUSTOMER)
        c = converse.record(s, str(CONVERSATIONS / f"{name}.yaml"))
        ids[name] = c.id
        res["conversations"][name] = {
            "id": c.id,
            "as": c.m.reader,
            "messages": len(spec["messages"]),
            "spec": spec,
        }

    checks = res["checks"]
    by = {name: x["as"] for name, x in res["conversations"].items()}
    with memory.memory_graph(s) as M:
        # 1. the chain
        for name, x in res["conversations"].items():
            got = M.rows(CHAIN, id=x["id"])[0]
            want = [
                ["user" if "user" in t else "assistant", t.get("user") or t.get("assistant")]
                for t in x["spec"]["messages"]
            ]
            checks[f"{name}: the message chain"] = {
                "ok": got["messages"] == len(want) and got["chain"] == want,
                "messages": got["messages"],
            }
        # 2. reasoning
        for name, x in res["conversations"].items():
            for i, call in enumerate(M.rows(CALLS, id=x["id"]), 1):
                linked = (
                    call["role"] == "user"
                    and call["instance_of"] == call["tool"]
                    and call["initiated_by_it"]
                    and call["in_its_trace"]
                )
                ok = linked and call["status"] == "success"
                if call["tool"] == "recall":
                    ok = ok and call["touched"] == ["Customer"]
                if call["tool"] == "ask":
                    ok = ok and bool(json.loads(call["result"]).get("query")) and bool(call["tables"])
                checks[f"{name}: tool call {i} ({call['tool']})"] = {
                    "ok": ok,
                    "touched": call["touched"],
                    "tables": call["tables"],
                    "computations": call["computations"],
                }
        # 3. mentions land on the warehouse node
        for name in ("marketing-1", "risk-1"):
            got = M.rows(MENTIONED, id=ids[name])
            checks[f"{name}: mentions are the warehouse's Customer"] = {
                "ok": bool(got) and all(r["warehouse"] and r["fetched"] and r["from_table"] for r in got),
                "customers": [str(r["key"]) for r in got],
            }

    # 4. the next session finds the last
    before = res["before marketing-2"]
    checks["marketing-2 finds marketing-1's notes"] = {
        "ok": [p["preference"] for p in before.get("preferences", [])] == ["email, not phone"]
        and [f["object"] for f in before.get("facts", [])] == ["a travel rewards card"]
        and [e["name"] for e in before.get("entities", [])] == ["Ana"]
        and [x["id"] for x in before.get("conversations", [])] == [ids["marketing-1"]],
        "noted": memory.show_notes(before),
    }
    # 5. supersession
    with memory.memory_graph(s) as M:
        prefs = M.rows(PREFERENCES, key=CUSTOMER, by=by["marketing-2"])
    after = notes(s, "marketing", CUSTOMER)
    old, new = prefs[-2], prefs[-1]
    checks["a new preference supersedes the old"] = {
        "ok": old["closed"] and not new["closed"] and old["id"] in new["supersedes"]
        and [p["preference"] for p in after["preferences"]] == ["phone, mornings"]
        and [x["id"] for x in after["conversations"]] == [ids["marketing-1"], ids["marketing-2"]],
        "noted": memory.show_notes(after),
    }  # fmt: skip
    # 6. entitlements
    checks["the data source sees nothing of marketing's notes"] = {
        "ok": not any(
            notes(s, None, CUSTOMER).get(k) for k in ("preferences", "facts", "entities", "conversations")
        )
    }
    checks["marketing sees nothing of risk's notes on a Kansas customer"] = {
        "ok": not any(
            notes(s, "marketing", KANSAS).get(k)
            for k in ("preferences", "facts", "entities", "conversations")
        )
    }
    checks["risk sees its own note on it"] = {"ok": [f["object"] for f in notes(s, "risk", KANSAS).get("facts", [])] == ["address change pending verification"]}  # fmt: skip
    c = converse.Conversation(s, "risk tries a customer outside its rows", as_="risk")
    mid = c.say("user", f"Note something about customer {CUSTOMER}.")
    try:
        c.learn(mid, f"Customer {CUSTOMER}", "note", "should be refused")
        refused = False
    except memory.Unsupported as e:
        refused = str(e)
    checks["risk can't note a customer outside its rows"] = {"ok": bool(refused), "why": refused}
    # 7. a refetch leaves the conversations attached
    m = memory.reader_model(s, "marketing")
    memory.recall(s, "Customer", CUSTOMER, force=True, m=m)
    again = notes(s, "marketing", CUSTOMER)
    with memory.memory_graph(s) as M:
        nodes = M.value(CUSTOMER_NODES, key=CUSTOMER)
    checks["a refetch leaves them attached"] = {"ok": nodes == 1 and again == after, "customer nodes": nodes}

    for name, x in checks.items():
        print(f"{'ok    ' if x['ok'] else 'FAILED'} {name}", flush=True)
    return report(res)


def report(res: dict) -> int:
    checks = res["checks"]
    L = [
        "# Memory: the agent's side, in the agent-memory model",
        "",
        "Phase 3 of plans/2026-09-27-agentic-memory.md: the example's conversations (`conversations/*.yaml`) "
        "recorded with `qlsc converse`, then the graph they left checked. The model is Neo4j Labs' agent-memory "
        "(Conversation, Message, ReasoningTrace, ReasoningStep, ToolCall, Tool, Preference, Fact, Entity); the "
        "warehouse facts `remember` keeps are its long-term memory, under their own labels.",
        "",
        f"**{sum(x['ok'] for x in checks.values())} of {len(checks)} checks passed.**",
        "",
        "| check | result |",
        "|---|---|",
    ]
    L += [f"| {name} | {'ok' if x['ok'] else '**FAILED**'} |" for name, x in checks.items()]
    L += ["", "## What recall noted", "", "Before marketing-2 (marketing-1's notes):", ""]
    L += [f"    {line.strip()}" for line in checks["marketing-2 finds marketing-1's notes"]["noted"]]
    L += ["", "After marketing-2:", ""]
    L += [f"    {line.strip()}" for line in checks["a new preference supersedes the old"]["noted"]]
    res = json.loads(json.dumps(res, default=str))  # Neo4j's dates as text
    print(f"-> {write_result('converse', L, res)}")
    ok = all(x["ok"] for x in checks.values())
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

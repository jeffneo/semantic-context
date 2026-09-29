"""Memory, phase 3: the agent's side, in the Context Memory model (plans/2026-09-29-context-memory-model.md).

Records the example's conversations (conversations/*.yaml) with `qlsc converse`:
- marketing-1: a banker preparing for a customer. It has a recall, an ask, what was learned, and a decision;
- marketing-2: the same banker the next session. A changed preference, and the decision's outcome;
- risk-1: a risk analyst reviewing a Kansas customer, and a decision.

Then it checks the graph they left:
  1.  the chain: each conversation's messages PART_OF it, in seq, linked by NEXT;
  2.  tasks: one per user message, FROM it, PART_OF the conversation, closed; each task's steps PART_OF it, in
      order;
  3.  a recall's step READ the warehouse Customer (the context record), from memory too;
  4.  an ask's step READ the stubs of the layer Tables it read, and its fingerprint holds no value (not the
      customer's key);
  5.  mentions land on the warehouse node itself;
  6.  a decision is PART_OF its task, ABOUT the customer, BASED_ON the two facts and the ask;
  7.  the next session finds the last: marketing-2's recall carries marketing-1's facts, Ana, the decision and
      the conversation;
  8.  supersession:
      - changed: marketing-2's preference closes marketing-1's, and the decision based on it is to revisit;
      - corrected: the old fact never held;
  9.  an outcome is a Fact about its decision;
  10. security:
      - every node the conversations wrote is owned by their principal, and private;
      - each principal sees nothing of the others' notes;
      - risk can't note a customer outside its rows;
  11. a refetch leaves the conversations attached.

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
NAMES = ("marketing-1", "marketing-2", "risk-1")
EXTRA = ("risk corrects a fact", "risk tries a customer outside its rows")  # this check's own conversations

CHAIN = """
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(m:Message)
WITH c, m ORDER BY m.seq
WITH c, collect(m) AS ms
RETURN [m IN ms | [m.role, m.text]] AS messages, [m IN ms | m.seq] AS seqs,
       [m IN ms | [(m)-[:NEXT]->(n:Message) | n.seq]] AS nexts
"""
TASKS = """
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(t:Task)-[:FROM]->(m:Message)
OPTIONAL MATCH (t)<-[:PART_OF]-(s:Step)
WITH t, m, s ORDER BY s.seq
WITH t, m, collect(s) AS steps
RETURN m.seq AS seq, m.role AS role, t.status AS status, [s IN steps | s.tool] AS tools,
       [s IN steps | s.seq] AS seqs, [s IN steps | [(s)-[:NEXT]->(n:Step) | n.seq]] AS nexts
ORDER BY seq
"""
STEPS = """
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(t:Task)<-[:PART_OF]-(s:Step)
RETURN s.tool AS tool, s.status AS status, s.fingerprint AS fingerprint, s.origin AS origin,
       [(s)-[r:READ {context: true}]->(n:Customer) | n.customer_key] AS anchor,
       [(s)-[:READ]->(x:Table) | x.id] AS tables,
       [(s)-[:READ]->(x:Computation) | x.id] AS computations
ORDER BY t.started_at, s.seq
"""
MENTIONED = """
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(:Message)-[:MENTIONS]->(n:Customer)
RETURN DISTINCT n.customer_key AS key, n.source IS NOT NULL AS warehouse, n.fetched_at IS NOT NULL AS fetched,
       EXISTS { (n)-[:FROM]->(:Table) } AS from_table
"""
DECISIONS = """
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(:Task)<-[:PART_OF]-(d:Decision)-[:ABOUT]->(n)
RETURN d.choice AS choice, labels(n)[0] AS about,
       [(d)-[:BASED_ON]->(b:Fact) | b.predicate] AS facts, [(d)-[:BASED_ON]->(b:Step) | b.tool] AS steps
"""
SUPERSEDED = """
MATCH (new:Fact)-[s:SUPERSEDES]->(old:Fact) WHERE old.owner = $by AND old.predicate = $predicate
RETURN s.because AS because, old.valid_until = old.valid_from AS never_held,
       old.valid_until = new.valid_from AS until_the_new, new.valid_until IS NULL AS new_current
ORDER BY new.recorded_at DESC LIMIT 1
"""
OWNERS = """
MATCH (c:Conversation) WHERE c.id IN $ids
CALL (c) {
  MATCH (x)-[:PART_OF]->(c) RETURN x
  UNION MATCH (x)-[:PART_OF]->(:Task)-[:PART_OF]->(c) RETURN x
  UNION MATCH (x:Fact)-[:FROM]->(:Message)-[:PART_OF]->(c) RETURN x
  UNION MATCH (x:Entity)<-[:MENTIONS]-(:Message)-[:PART_OF]->(c) RETURN x
  UNION MATCH (x:Conversation) WHERE x = c RETURN x
}
RETURN c.id AS conversation, collect(DISTINCT [x.owner, x.scope]) AS owners, count(DISTINCT x) AS nodes
"""
CUSTOMER_NODES = "MATCH (n:Customer {customer_key: $key}) RETURN count(n) AS n"
# This check's own conversations from an earlier run, and all they recorded, so a run starts clean. The
# warehouse facts they mention stay: remember wrote them.
FORGET = """
MATCH (c:Conversation) WHERE c.title IN $titles
OPTIONAL MATCH (m:Message)-[:PART_OF]->(c)
OPTIONAL MATCH (t:Task)-[:PART_OF]->(c)
OPTIONAL MATCH (x)-[:PART_OF]->(t)
OPTIONAL MATCH (f:Fact)-[:FROM]->(m)
OPTIONAL MATCH (m)-[:MENTIONS]->(e:Entity)
WITH collect(DISTINCT c) + collect(DISTINCT m) + collect(DISTINCT t) + collect(DISTINCT x) + collect(DISTINCT f)
     + collect(DISTINCT e) AS gone
FOREACH (x IN gone | DETACH DELETE x)
RETURN size(gone) AS gone
"""


def chained(seqs: list, nexts: list) -> bool:
    """Numbered 1, 2, ... and each NEXT the one after it (the last, none)."""
    return seqs == list(range(1, len(seqs) + 1)) and nexts == [[i + 1] for i in seqs[:-1]] + [[]] * bool(seqs)


def notes(s, as_, key) -> dict:
    return memory.notes(s, memory.reader_model(s, as_), "Customer", key, dt.datetime.now(dt.UTC))


def main() -> int:
    s = settings()
    res: dict = {"conversations": {}, "checks": {}}
    specs = {n: yaml.safe_load((CONVERSATIONS / f"{n}.yaml").read_text()) for n in NAMES}
    with memory.memory_graph(s) as M:
        M.run(FORGET, titles=[x["title"] for x in specs.values()] + list(EXTRA))
    ids = {}
    for name in NAMES:
        if name == "marketing-2":
            res["before marketing-2"] = notes(s, "marketing", CUSTOMER)
        c = converse.record(s, str(CONVERSATIONS / f"{name}.yaml"))
        ids[name] = c.id
        res["conversations"][name] = {"id": c.id, "as": c.m.reader}
    by = {name: x["as"] for name, x in res["conversations"].items()}
    checks = res["checks"]

    with memory.memory_graph(s) as M:
        for name in NAMES:
            spec = specs[name]["messages"]
            want = [["user" if "user" in t else "agent", t.get("user") or t.get("agent")] for t in spec]
            got = M.rows(CHAIN, id=ids[name])[0]
            checks[f"{name}: messages, in order"] = {
                "ok": got["messages"] == want and chained(got["seqs"], got["nexts"])
            }
            tasks = M.rows(TASKS, id=ids[name])
            want_tools = [[next(iter(x)) for x in t.get("tools", [])] for t in spec if "user" in t]
            checks[f"{name}: a task per request, its steps in order"] = {
                "ok": [t["tools"] for t in tasks] == want_tools
                and all(
                    t["role"] == "user" and t["status"] == "done" and chained(t["seqs"], t["nexts"])
                    for t in tasks
                ),
                "tasks": [t["tools"] for t in tasks],
            }
            for i, step in enumerate(M.rows(STEPS, id=ids[name]), 1):
                if step["tool"] == "recall":
                    ok = (
                        step["status"] == "ok"
                        and len(step["anchor"]) == 1
                        and step["fingerprint"] == "recall Customer ?"
                    )
                else:
                    ok = (
                        step["status"] == "ok"
                        and bool(step["tables"])
                        and str(CUSTOMER) not in (step["fingerprint"] or "")
                    )
                where = f", from {step['origin']}" if step["origin"] else ""
                checks[f"{name}: step {i} ({step['tool']}{where})"] = {"ok": ok} | step
            got = M.rows(MENTIONED, id=ids[name])
            checks[f"{name}: mentions are the warehouse's Customer"] = {
                "ok": bool(got) and all(r["warehouse"] and r["fetched"] and r["from_table"] for r in got)
            }
        d = M.rows(DECISIONS, id=ids["marketing-1"])
        checks["marketing-1: the decision, ABOUT the customer, BASED_ON two facts and the ask"] = {
            "ok": len(d) == 1 and d[0]["about"] == "Customer"
            and sorted(d[0]["facts"]) == ["interested in", "prefers contact channel"] and d[0]["steps"] == ["ask"],
        }  # fmt: skip

    before = res["before marketing-2"]
    checks["marketing-2 finds marketing-1's notes"] = {
        "ok": sorted((f["predicate"], f["value"]) for f in before.get("facts", []))
        == [("interested in", "a travel rewards card"), ("prefers contact channel", "email, not phone")]
        and [e["name"] for e in before.get("related", [])] == ["Ana"]
        and [x["choice"] for x in before.get("decisions", [])] == ["offer a travel rewards card, by email"]
        and [x["id"] for x in before.get("conversations", [])] == [ids["marketing-1"]],
        "noted": memory.show_notes(before),
    }
    after = notes(s, "marketing", CUSTOMER)
    with memory.memory_graph(s) as M:
        changed = M.rows(SUPERSEDED, by=by["marketing-2"], predicate="prefers contact channel")[0]
    decision = after["decisions"][0]
    checks["changed: the new preference closes the old, and the decision based on it is to revisit"] = {
        "ok": changed["because"] == "changed" and changed["until_the_new"] and changed["new_current"]
        and [f["value"] for f in after["facts"] if f["predicate"] == "prefers contact channel"] == ["phone, mornings"]
        and len(decision["revisit"]) == 1 and "phone, mornings" in decision["revisit"][0],
        "noted": memory.show_notes(after),
    }  # fmt: skip
    checks["an outcome is a fact about its decision"] = {"ok": decision["outcomes"] == ["accepted"]}
    c = converse.Conversation(s, EXTRA[0], as_="risk")
    c.say("user", "Correction: that address change was verified last week; there was never a hold.")
    c.learn(f"Customer {KANSAS}", "review status", "address verified", because="corrected")
    with memory.memory_graph(s) as M:
        corrected = M.rows(SUPERSEDED, by=by["risk-1"], predicate="review status")[0]
    checks["corrected: the old fact never held"] = {
        "ok": corrected["because"] == "corrected" and corrected["never_held"]
    }

    # security
    with memory.memory_graph(s) as M:
        owned = {r["conversation"]: r for r in M.rows(OWNERS, ids=list(ids.values()))}
    for name in NAMES:
        r = owned[ids[name]]
        checks[f"{name}: every node it wrote is its principal's, and private"] = {
            "ok": r["owners"] == [[by[name], "private"]],
            "nodes": r["nodes"],
        }
    empty = lambda n: not any(n.get(k) for k in ("facts", "related", "decisions", "conversations"))
    checks["the data source sees nothing of marketing's notes"] = {
        "ok": empty(notes(s, None, CUSTOMER))
    }  # it has none
    theirs = notes(
        s, "marketing", KANSAS
    )  # marketing may have notes of its own on this customer (eval/distill.py)
    checks["marketing sees nothing of risk's notes on a Kansas customer"] = {
        "ok": not {f["value"] for f in theirs.get("facts", [])}
        & {"address verified", "address change pending verification"}
        and "hold any credit limit increase" not in [x["choice"] for x in theirs.get("decisions", [])]
        and ids["risk-1"] not in [x["id"] for x in theirs.get("conversations", [])]
    }
    mine = notes(s, "risk", KANSAS)
    checks["risk sees its own"] = {
        "ok": [f["value"] for f in mine.get("facts", [])] == ["address verified"]
        and [x["choice"] for x in mine.get("decisions", [])] == ["hold any credit limit increase"]
    }
    c = converse.Conversation(s, EXTRA[1], as_="risk")
    c.say("user", f"Note something about customer {CUSTOMER}.")
    try:
        c.learn(f"Customer {CUSTOMER}", "note", "should be refused")
        refused = ""
    except memory.Unsupported as e:
        refused = str(e)
    checks["risk can't note a customer outside its rows"] = {"ok": bool(refused), "why": refused}
    memory.recall(s, "Customer", CUSTOMER, force=True, m=memory.reader_model(s, "marketing"))
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
        "# Memory: the agent's side, in the Context Memory model",
        "",
        "The example's conversations (`conversations/*.yaml`), recorded with `qlsc converse`, and the graph they "
        "left, checked (plans/2026-09-29-context-memory-model.md). The labels are Conversation, Message, Task, "
        "Step, Decision, Fact and Entity. The warehouse facts `remember` keeps are the long-term memory, under "
        "their own labels.",
        "",
        f"**{sum(x['ok'] for x in checks.values())} of {len(checks)} checks passed.**",
        "",
        "| check | result |",
        "|---|---|",
    ]
    L += [f"| {name} | {'ok' if x['ok'] else '**FAILED**'} |" for name, x in checks.items()]
    L += ["", "## What recall noted", "", "Before marketing-2:", ""]
    L += [f"    {line.strip()}" for line in checks["marketing-2 finds marketing-1's notes"]["noted"]]
    L += ["", "After marketing-2:", ""]
    key = "changed: the new preference closes the old, and the decision based on it is to revisit"
    L += [f"    {line.strip()}" for line in checks[key]["noted"]]
    res = json.loads(json.dumps(res, default=str))  # Neo4j's dates as text
    print(f"-> {write_result('converse', L, res)}")
    ok = all(x["ok"] for x in checks.values())
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

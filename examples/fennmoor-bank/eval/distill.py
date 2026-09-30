"""Memory, phase 4 (plans/2026-09-29-context-memory-model.md): distillation. Do the agents' repeated,
successful procedures become skills, with no values in them, offered only where they should be, measured
and retired when they stop working?

A simulated record of experience, one conversation per session, each with a request that calls two tools (a
recall, then an ask) and a rating:
  A  marketing, 5 sessions: prepare for a customer meeting (the customer, and their card spend by merchant
     category), rated helpful
  B  risk, 4 sessions: review a Kansas or Nebraska customer (the customer, and their deposits by transaction
     type), rated helpful
  C  marketing, 3 sessions: what a customer browsed before calling (data memory doesn't hold), rated wrong
  one-offs: two sessions of their own kind

Then:
  1. distill: skills for A and B, none for C (it failed) or the one-offs (too few); no value of the evidence
     (a customer's key) in any skill; each ABOUT the stubs of the tables it read; distilling again changes
     nothing;
  2. approve:
     - contact-center may not approve B (it can't read B's tables);
     - marketing approves A;
     - A can't be approved twice;
  3. offer:
     - a new A-like request of marketing's is offered A;
     - contact-center's same request is offered nothing (it can't read A's tables);
     - B (proposed) is offered to no one;
  4. measure: 2 new A sessions follow A and succeed (A used 2, 2 successful); then 2 that follow it are rated
     wrong, and the next distillation retires A (2 of 4), recorded as a Fact about it;
  5. privacy: a reader sees how many tasks a skill came from, not which.

Writes results/distill.md and .json. About 18 LLM-written queries: about ten minutes.
Usage: uv run examples/fennmoor-bank/eval/distill.py
"""

from __future__ import annotations

import json

from common import settings, typed, write_result

from qlsc import converse, distill, entitle, memory

TITLE = "distill check: "
CARD_CUSTOMERS = typed("""
MATCH (t:CardTransaction)-[:REL(CardTransaction,Customer)]->(c:Customer) WHERE t.post_date >= $since
RETURN DISTINCT c.customer_key AS key ORDER BY key LIMIT $n
""")
KS_NE_CUSTOMERS = typed("""
MATCH (d:DepositTransaction)-[:REL(DepositTransaction,Customer)]->(c:Customer) WHERE d.posted_date >= $since AND c.state_code IN ['KS', 'NE']
RETURN DISTINCT c.customer_key AS key ORDER BY key LIMIT $n
""")
FORGET = """
MATCH (c:Conversation) WHERE c.title STARTS WITH $title
OPTIONAL MATCH (x)-[:PART_OF]->(c)
OPTIONAL MATCH (y)-[:PART_OF]->(:Task)-[:PART_OF]->(c)
OPTIONAL MATCH (f:Fact)-[:FROM]->(:Message)-[:PART_OF]->(c)
WITH collect(DISTINCT c) + collect(DISTINCT x) + collect(DISTINCT y) + collect(DISTINCT f) AS gone
FOREACH (n IN gone | DETACH DELETE n)
"""
FORGET_SKILLS = "MATCH (k:Skill) OPTIONAL MATCH (f:Fact)-[:ABOUT]->(k) DETACH DELETE f, k"
FOLLOWED = "MATCH (t:Task {id: $id})-[:FOLLOWED]->(k:Skill) RETURN k.id AS id"
OFFERED = "MATCH (t:Task {id: $id}) RETURN t.offered AS offered"
RETIRED = "MATCH (f:Fact {predicate: 'retired'})-[:ABOUT]->(k:Skill {id: $id}) RETURN f.value AS why"

PATTERNS = {
    "A": (
        "marketing",
        "Prepare me for my meeting with customer {k}: what do we hold, and what did they spend on cards last quarter by merchant category?",
        "Card spend by merchant category for the customer with customer_key {k}, last quarter",
    ),
    "B": (
        "risk",
        "Risk review of customer {k}: their context, and their deposits last quarter by transaction type.",
        "Deposit amounts by transaction type for the customer with customer_key {k}, last quarter",
    ),
    "C": (
        "marketing",
        "What did customer {k} browse on our website before they last called us?",
        "Which web pages did the customer with customer_key {k} visit before calling, last quarter?",
    ),
    "branch": ("marketing", "How is branch {k}'s product mix?", "Accounts by product line at branch {k}"),
    "risk-calls": (
        "risk",
        "Has customer {k} called us much lately?",
        "Number of calls from the customer with customer_key {k}, last quarter",
    ),
}  # fmt: skip


def session(s, pattern: str, key, rating: str, label: str = "Customer") -> dict:
    """One session: the request, the two tools, the agent's reply, and the rating. -> what it recorded"""
    who, request, question = PATTERNS[pattern]
    c = converse.Conversation(s, f"{TITLE}{pattern} {key}", as_=who)
    c.say("user", request.format(k=key))
    task, offered = c.task, [k["id"] for k in c.offered]
    c.recall(f"{label} {key}")
    a = c.ask(question.format(k=key))
    c.say("agent", "Here it is.")
    c.say("user", "That was right." if rating == "helpful" else "That's not what I needed.")
    c.rate(rating)
    c.close("done")
    with memory.memory_graph(s) as M:
        follows = [r["id"] for r in M.rows(FOLLOWED, id=task)]
    ok = (a.get("result") or {}).get("ok")
    print(f"  {pattern} {key} as {who}: ask {a.get('route')} ({a.get('writer')}) {'ok' if ok else 'failed'}; "
          f"rated {rating}; offered {len(offered)}; followed {len(follows)}", flush=True)  # fmt: skip
    return {
        "pattern": pattern,
        "key": str(key),
        "task": task,
        "offered": offered,
        "followed": follows,
        "ask_ok": ok,
    }


def by_pattern(skills: list[dict], sessions: list[dict]) -> dict[str, list[dict]]:
    """Which pattern's sessions each skill came from: the skills whose evidence holds them."""
    tasks = {x["task"]: x["pattern"] for x in sessions}
    out: dict[str, list[dict]] = {}
    for k in skills:
        for p in sorted({tasks[t] for t in k["evidence"] if t in tasks}):
            out.setdefault(p, []).append(k)
    return out


def main() -> int:
    s = settings()
    with memory.memory_graph(s) as M:
        M.run(FORGET, title=TITLE)
        M.run(FORGET_SKILLS)
    since = memory.window_start(s)
    with memory.virtual_graph(s) as V:
        q, e = entitle.signing(s, None, CARD_CUSTOMERS)
        cards = [r["key"] for r in V.rows(q, since=since, n=12, **e)]
        q, e = entitle.signing(s, None, KS_NE_CUSTOMERS)
        kansas = [r["key"] for r in V.rows(q, since=since, n=5, **e)]
    res: dict = {"sessions": [], "checks": {}, "skills": {}}
    checks, sessions = res["checks"], res["sessions"]

    print("experience", flush=True)
    sessions += [session(s, "A", k, "helpful") for k in cards[:5]]
    sessions += [session(s, "B", k, "helpful") for k in kansas[:4]]
    sessions += [session(s, "C", k, "wrong") for k in cards[5:8]]
    sessions += [
        session(s, "branch", 101, "helpful", label="Branch"),
        session(s, "risk-calls", kansas[4], "helpful"),
    ]

    # 1. distill
    first = distill.distill(s)
    found = by_pattern(first, sessions)
    checks["skills for A and B, and no other"] = {
        "ok": sorted(found) == ["A", "B"] and len(first) == 2 and all(len(v) == 1 for v in found.values()),
        "found": {p: [k["name"] for k in ks] for p, ks in found.items()},
    }
    evidence_keys = {x["key"] for x in sessions}
    text = lambda k: json.dumps(
        [k["name"], k["description"], k["trigger"], k["procedure"], k.get("parameters")]
    )
    checks["no value of the evidence in any skill"] = {
        "ok": not any(key in text(k) for k in first for key in evidence_keys),
    }
    tables = {p: ks[0]["tables"] for p, ks in found.items()}
    checks["each skill ABOUT the tables its steps read"] = {
        "ok": all("fennmoor-dw.dw_core.dim_customer" in t for t in tables.values())
        and "fennmoor-dw.dw_core.fct_card_transactions" in tables.get("A", [])
        and "fennmoor-dw.dw_core.fct_deposit_transactions" in tables.get("B", []),
        "tables": tables,
    }
    again = distill.distill(s)
    checks["distilling again changes nothing"] = {
        "ok": sorted(k["key"] for k in again) == sorted(k["key"] for k in first)
        and all(k["status"] == "proposed" for k in again)
    }
    a, b = found["A"][0], found["B"][0]
    res["skills"] = {"A": {x: a[x] for x in ("name", "description", "trigger", "procedure", "tables")},
                     "B": {x: b[x] for x in ("name", "description", "trigger", "procedure", "tables")}}  # fmt: skip

    # 2. approve
    def refused(skill, who) -> str:
        try:
            distill.approve(s, skill, who)
        except memory.Unsupported as e:
            return str(e)
        return ""

    checks["contact-center may not approve B"] = {"ok": bool(refused(b["id"], "contact-center"))}
    distill.approve(s, a["id"], "marketing")
    checks["marketing approves A, once"] = {"ok": bool(refused(a["id"], "marketing"))}

    # 3. offer
    request = PATTERNS["A"][1].format(k=cards[8])
    mk, cc, rk = (memory.reader_model(s, who) for who in ("marketing", "contact-center", "risk"))
    offered = {who: distill.offers(s, m, request) for who, m in (("marketing", mk), ("contact-center", cc))}
    checks["a new A-like request of marketing's is offered A"] = {
        "ok": [k["id"] for k in offered["marketing"]][:1] == [a["id"]],
        "offered": offered["marketing"],
    }
    checks["contact-center's same request is offered nothing"] = {"ok": offered["contact-center"] == []}
    b_offered = distill.offers(s, rk, PATTERNS["B"][1].format(k=kansas[0]))
    checks["B, proposed, is offered to no one"] = {
        "ok": b["id"] not in [k["id"] for k in b_offered + offered["marketing"]]
    }

    # 4. measure
    print("following A", flush=True)
    follow = [session(s, "A", k, "helpful") for k in cards[8:10]]
    sessions += follow
    distill.distill(s)
    now_a = next(k for k in distill.skills(s, mk) if k["id"] == a["id"])
    checks["2 sessions offered A follow it and succeed"] = {
        "ok": all(x["followed"] == [a["id"]] and a["id"] in x["offered"] for x in follow)
        and (now_a["uses"], now_a["successes"], now_a["status"]) == (2, 2, "approved"),
        "uses": now_a["uses"],
        "successes": now_a["successes"],
    }
    print("A stops working", flush=True)
    failing = [session(s, "A", k, "wrong") for k in cards[10:12]]
    sessions += failing
    distill.distill(s)
    now_a = next(k for k in distill.skills(s, mk) if k["id"] == a["id"])
    with memory.memory_graph(s) as M:
        why = [r["why"] for r in M.rows(RETIRED, id=a["id"])]
    checks["2 more that follow it fail, and A is retired"] = {
        "ok": all(x["followed"] == [a["id"]] for x in failing) and now_a["status"] == "retired" and bool(why),
        "why": why,
    }
    checks["a retired skill is offered to no one"] = {
        "ok": a["id"] not in [k["id"] for k in distill.offers(s, mk, request)]
    }

    # 5. privacy
    seen = distill.skills(s, mk)
    checks["a reader sees how many tasks a skill came from, not which"] = {
        "ok": all(isinstance(k["evidence"], int) and "embedding" not in k for k in seen)
    }
    res["final"] = seen
    for name, x in checks.items():
        print(f"{'ok    ' if x['ok'] else 'FAILED'} {name}", flush=True)
    return report(res)


def report(res: dict) -> int:
    checks = res["checks"]
    L = [
        "# Memory: skills distilled from the agents' experience",
        "",
        "Phase 4 of the memory plan (plans/2026-09-29-context-memory-model.md). A simulated record:",
        "- two patterns that repeat and work: marketing's customer-meeting preparation, 5 sessions; risk's review, 4;",
        "- one that repeats and fails: rated wrong, 3 sessions;",
        "- two one-offs.",
        "",
        "`qlsc distill` groups the tasks by what they did and read (Leiden over their similarity), and proposes a "
        "skill from each group that repeats and succeeds. A person approves one. It's then offered to new tasks "
        "that fit, measured as they follow it, and retired when it stops working.",
        "",
        f"**{sum(x['ok'] for x in checks.values())} of {len(checks)} checks passed.**",
        "",
        "| check | result |",
        "|---|---|",
    ]
    L += [f"| {name} | {'ok' if x['ok'] else '**FAILED**'} |" for name, x in checks.items()]
    for p, k in res["skills"].items():
        L += ["", f"## Skill {p}: {k['name']}", "", k["description"], "", f"Trigger: {k['trigger']}", ""]
        L += [f"{i}. {x}" for i, x in enumerate(k["procedure"], 1)]
        L += ["", "About: " + ", ".join(f"`{t}`" for t in k["tables"])]
    res = json.loads(json.dumps(res, default=str))
    print(f"-> {write_result('distill', L, res)}")
    ok = all(x["ok"] for x in checks.values())
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

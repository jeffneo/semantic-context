"""Memory, phase 1 (plans/2026-09-27-agentic-memory.md): is a remembered context the virtual graph's, and is
a stale one ever served?

For 20 customers (the two the graph questions name, then 18 who called in the window, by key):
  1. correctness: the context fetched from the virtual graph (qlsc remember) is the context read back from
     memory (qlsc recall), node for node, property for property, relationship for relationship; and the
     same Cypher, six context questions, gives the same rows on memory and on the virtual graph. A
     question over a capped relationship (the most recent facts only) is left out: memory holds the cap,
     the virtual graph all.
  2. idempotence: remembering three contexts again leaves memory's facts unchanged: its nodes and
     relationships, besides the Step each recall leaves (the record of who read what).
  3. freshness, on the first customer:
     - within its lifetime, recall reads memory;
     - past it, recall fetches again;
     - a planted stale fact (a call whose relationship's holds_until has passed) is never read, and a
       refetch removes it;
     - a changed template (a 30-day window) is a different context, fetched again.
  4. a batch: the 20 remembered together, in one batch (qlsc remember Customer KEY...), give each customer the
     context it got alone (its nodes, properties, relationships, and each read's keys, rows and cap), and
     read back from memory as that.
  Latency: fetch and recall per context, and each question on either target.

Writes results/memory.md and .json. Prints a line per customer as it goes.
Usage: uv run examples/fennmoor-bank/eval/memory.py
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import time

from common import settings, write_result

from qlsc import entitle, memory
from qlsc.graph import Graph

NAMED = ["0001000025", "0001000021"]  # the graph questions' customers (graph_questions.yaml)
OTHERS = 18
CALLERS = """
MATCH (k:Call)-[:RECEIVED_FROM]->(c:Customer) WHERE k.conversation_date >= $since
RETURN DISTINCT c.customer_key AS key ORDER BY key LIMIT $n
"""
BY_CIF = "MATCH (c:Customer) WHERE c.cif_number IN $cifs RETURN c.customer_key AS key, c.cif_number AS cif"

# The same text on memory and on the virtual graph: one source, so no source filter (plan: Collisions).
# Each reads within the template and its window; `over` names the relationships it needs uncapped.
QUESTIONS = {
    "accounts by product line": (
        ["Customer<-OWNED_BY-Account"],
        """MATCH (a:Account)-[:OWNED_BY]->(c:Customer), (a)-[:CONTAINS]->(p:Product)
WHERE c.customer_key = $key
RETURN p.product_line AS product_line, count(a) AS accounts ORDER BY product_line""",
    ),
    "accounts by branch": (
        ["Customer<-OWNED_BY-Account"],
        """MATCH (a:Account)-[:OWNED_BY]->(c:Customer), (a)-[:MAINTAINED_AT]->(b:Branch)
WHERE c.customer_key = $key
RETURN b.branch_name AS branch, count(a) AS accounts ORDER BY branch""",
    ),
    "calls by agent": (
        ["Customer<-RECEIVED_FROM-Call"],
        """MATCH (k:Call)-[:RECEIVED_FROM]->(c:Customer), (k)-[:HANDLED_BY]->(g:Agent)
WHERE c.customer_key = $key AND k.conversation_date >= $since
RETURN g.agent_name AS agent, count(k) AS calls ORDER BY agent""",
    ),
    "calls by site and queue": (
        ["Customer<-RECEIVED_FROM-Call"],
        """MATCH (k:Call)-[:RECEIVED_FROM]->(c:Customer), (k)-[:SERVICED_AT]->(x:ContactCenterSite),
      (k)-[:ROUTED_THROUGH]->(q:Queue)
WHERE c.customer_key = $key AND k.conversation_date >= $since
RETURN x.site_name AS site, q.queue_name AS queue, count(k) AS calls ORDER BY site, queue""",
    ),
    "card spend by merchant category": (
        ["Customer<-MADE_BY-CardTransaction"],
        """MATCH (t:CardTransaction)-[:MADE_BY]->(c:Customer), (t)-[:TRANSACTED_AT]->(m:Merchant)
WHERE c.customer_key = $key AND t.post_date >= $since
RETURN m.category_group AS category, count(t) AS purchases, sum(t.amount) AS amount ORDER BY category""",
    ),
    "deposits by account product": (
        ["Customer<-INITIATED_BY-DepositTransaction"],
        """MATCH (d:DepositTransaction)-[:INITIATED_BY]->(c:Customer), (d)-[:CREDITED_TO]->(a:Account)
WHERE c.customer_key = $key AND d.posted_date >= $since
RETURN a.product_name AS product, d.transaction_type AS type, count(d) AS n, sum(d.amount) AS amount
ORDER BY product, type""",
    ),
}
# The remembered facts: not the Steps each recall leaves, nor their READs (the record of who read what)
COUNTS = """
MATCH (n) WHERE NOT n:Step WITH count(n) AS nodes
MATCH ()-[r]->() WHERE type(r) <> 'READ' RETURN nodes, count(r) AS relationships
"""
PLANT = """
MATCH (c:Customer {source: $source, customer_key: $key})
MERGE (k:Call {source: $source, conversation_id: $id})
SET k.conversation_date = $day, k.fetched_at = $old, k.holds_until = $old
MERGE (k)-[x:RECEIVED_FROM]->(c) SET x.fetched_at = $old, x.holds_until = $old
"""
PLANTED = "MATCH (k:Call {source: $source, conversation_id: $id})-[x:RECEIVED_FROM]->() RETURN count(x) AS n"
UNPLANT = "MATCH (k:Call {source: $source, conversation_id: $id}) DETACH DELETE k"
STALE_ID = "qlsc-memory-check-stale"
# The freshness checks start from no record of the customer's context for this reader, and leave none dated
# after now (they move the clock): every fetch is a kept Step, and one from an earlier run would still hold.
FORGET_STEPS = """
MATCH (s:Step {tool: 'recall', owner: $by})-[:READ {context: true}]->(:Customer {customer_key: $key})
DETACH DELETE s
"""
FORGET_FUTURE = "MATCH (s:Step {tool: 'recall'}) WHERE s.at > $now DETACH DELETE s"


def norm(rows: list[dict]) -> list[str]:
    """Rows as comparable text: floats to 9 significant digits (a SUM's last digits depend on its order)."""
    f = lambda x: float(f"{x:.9g}") if isinstance(x, float) else x
    return sorted(json.dumps({k: f(v) for k, v in r.items()}, sort_keys=True, default=str) for r in rows)


def compare(a: memory.Context, b: memory.Context) -> list[str]:
    """How two contexts differ: nodes, properties and relationships."""
    out = []
    if set(a.nodes) != set(b.nodes):
        out.append(f"nodes: {len(set(a.nodes) - set(b.nodes))} only in {a.origin}, "
                   f"{len(set(b.nodes) - set(a.nodes))} only in {b.origin}")  # fmt: skip
    props = [k for k in set(a.nodes) & set(b.nodes) if norm([a.nodes[k]]) != norm([b.nodes[k]])]
    if props:
        out.append(f"properties differ on {len(props)} nodes, e.g. {props[0]}")
    if a.edges != b.edges:
        out.append(
            f"relationships: {len(a.edges - b.edges)} only in {a.origin}, {len(b.edges - a.edges)} only in {b.origin}"
        )
    return out


def ask(s, G: Graph, q: str, key, virtual: bool) -> tuple[list[dict], float]:
    params = {"key": key, "since": memory.window_start(s)}
    sent, extra = entitle.signing(s, None, q) if virtual else (q, {})
    t = time.time()
    rows = G.rows(sent, **params, **extra)
    return rows, time.time() - t


def quantiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    return (
        {
            "median": round(statistics.median(xs), 3),
            "p95": round(xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))], 3),
        }
        if xs
        else {}
    )


def main() -> int:
    s = settings()
    with Graph(s) as G:
        m = memory.model(G, s)
    since = memory.window_start(s)
    with memory.virtual_graph(s) as V:
        q, extra = entitle.signing(s, None, BY_CIF)
        named = {r["cif"]: r["key"] for r in V.rows(q, cifs=NAMED, **extra)}
        q, extra = entitle.signing(s, None, CALLERS)
        callers = [r["key"] for r in V.rows(q, since=since, n=OTHERS + len(NAMED), **extra)]
    keys = [named[c] for c in NAMED] + [k for k in callers if k not in named.values()][:OTHERS]
    res: dict = {
        "window_since": str(since),
        "window_days": s["memory"]["window_days"],
        "cap": s["memory"]["cap"],
        "customers": {},
        "freshness": {},
    }

    # 1. correctness and latency
    alone = {}
    with memory.memory_graph(s) as M, memory.virtual_graph(s) as V:
        for i, key in enumerate(keys, 1):
            fetched = alone[key] = memory.recall(s, "Customer", key, force=True, m=m)
            recalled = memory.recall(s, "Customer", key, m=m)
            diff = (
                compare(fetched, recalled) if recalled.origin == "memory" else ["recall didn't read memory"]
            )
            capped = fetched.capped()
            questions = {}
            for name, (over, q) in QUESTIONS.items():
                if any(x in capped for x in over):
                    questions[name] = {"verdict": "capped"}
                    continue
                on_vg, t_vg = ask(s, V, q, key, virtual=True)
                on_mem, t_mem = ask(s, M, q, key, virtual=False)
                questions[name] = {
                    "verdict": "same" if norm(on_vg) == norm(on_mem) else "DIFFERENT",
                    "rows": len(on_vg),
                    "virtual_graph_seconds": round(t_vg, 3),
                    "memory_seconds": round(t_mem, 3),
                }
            res["customers"][str(key)] = {
                "fetched": fetched.summary(),
                "recalled": recalled.summary(),
                "differences": diff,
                "questions": questions,
            }
            verdicts = [x["verdict"] for x in questions.values()]
            print(
                f"{i}/{len(keys)} {key}: {len(fetched.nodes)} nodes, {len(fetched.edges)} relationships, "
                f"fetch {fetched.seconds:.2f} s, recall {recalled.seconds:.2f} s from {recalled.origin}; "
                f"{'same context' if not diff else 'DIFFERENT: ' + '; '.join(diff)}; questions "
                f"{verdicts.count('same')} same, {verdicts.count('DIFFERENT')} different, {verdicts.count('capped')} capped",
                flush=True,
            )

        # 2. idempotence
        before = M.rows(COUNTS)[0]
        for key in keys[:3]:
            memory.recall(s, "Customer", key, force=True, m=m)
        after = M.rows(COUNTS)[0]
        res["idempotence"] = {"before": before, "after": after, "same": before == after}
        print(f"idempotence: {before} -> {after}", flush=True)

        # 3. freshness, on the first customer
        key, f = keys[0], res["freshness"]
        M.run(FORGET_STEPS, by=m.reader, key=key)
        ctx = memory.recall(s, "Customer", key, force=True, m=m)
        until = ctx.holds_until
        inside = memory.recall(s, "Customer", key, now=until - dt.timedelta(minutes=1), m=m)
        f["within its lifetime"] = {"origin": inside.origin, "ok": inside.origin == "memory"}
        past = memory.recall(s, "Customer", key, now=until + dt.timedelta(seconds=1), m=m)
        f["past it"] = {
            "origin": past.origin,
            "ok": past.origin == "virtual graph" and past.holds_until > until,
        }
        old = dt.datetime.now(dt.UTC) - dt.timedelta(days=2)
        day = dt.date.fromisoformat(res["window_since"]) + dt.timedelta(days=1)
        M.run(PLANT, source=m.source, key=key, id=STALE_ID, day=day, old=old)
        served = memory.recall(s, "Customer", key, m=m)
        leaked = ("Call", STALE_ID) in served.nodes
        f["a stale fact"] = {
            "origin": served.origin,
            "served": leaked,
            "ok": served.origin == "memory" and not leaked,
        }
        memory.recall(s, "Customer", key, force=True, m=m)
        left = M.value(PLANTED, source=m.source, id=STALE_ID)
        f["a refetch removes it"] = {"relationships left": left, "ok": left == 0}
        M.run(UNPLANT, source=m.source, id=STALE_ID)
        configured = s["memory"]["window_days"]
        s["memory"]["window_days"] = 30
        other = memory.recall(s, "Customer", key, m=m)
        f["a changed template"] = {"origin": other.origin, "ok": other.origin == "virtual graph"}
        s["memory"]["window_days"] = configured
        memory.recall(s, "Customer", key, force=True, m=m)  # back to the configured template
        M.run(FORGET_FUTURE, now=dt.datetime.now(dt.UTC))
        for name, x in f.items():
            print(f"freshness: {name}: {'ok' if x['ok'] else 'FAILED'} {x}", flush=True)

    # 4. a batch
    t0 = time.time()
    batch = memory.recall_batch(s, "Customer", keys, force=True, m=m)
    seconds = time.time() - t0
    reads = lambda c: [(x["read"], x["keys"], x["rows"], x["capped"]) for x in c.reads]
    diffs = {}
    for key in keys:
        d = compare(batch[key], alone[key]) + (
            ["reads differ"] if reads(batch[key]) != reads(alone[key]) else []
        )
        back = memory.recall(s, "Customer", key, m=m)
        d += ["not read back from memory"] if back.origin != "memory" else compare(back, batch[key])
        if d:
            diffs[str(key)] = d
    res["batch"] = {
        "customers": len(keys),
        "seconds": round(seconds, 2),
        "seconds one at a time": round(sum(c.seconds for c in alone.values()), 2),
        "differences": diffs,
        "ok": not diffs,
    }
    print(f"a batch: {res['batch']}", flush=True)

    fetch = [c["fetched"]["seconds"] for c in res["customers"].values()]
    recall = [c["recalled"]["seconds"] for c in res["customers"].values()]
    qs = [q for c in res["customers"].values() for q in c["questions"].values() if q["verdict"] != "capped"]
    res["latency"] = {
        "fetch": quantiles(fetch),
        "recall": quantiles(recall),
        "question on the virtual graph": quantiles([q["virtual_graph_seconds"] for q in qs]),
        "question on memory": quantiles([q["memory_seconds"] for q in qs]),
    }
    return report(res)


def report(res: dict) -> int:
    cs = res["customers"]
    same_ctx = sum(not c["differences"] for c in cs.values())
    qs = [q for c in cs.values() for q in c["questions"].values()]
    count = lambda v: sum(q["verdict"] == v for q in qs)
    L = [
        "# Memory: remembered contexts against the virtual graph",
        "",
        "Phase 1 of plans/2026-09-27-agentic-memory.md: `qlsc remember` fetches a customer's context from the "
        "virtual graph (the node, its relationships, their dimensions; facts from the last "
        f"{res['window_days']} days, since {res['window_since']}, at most {res['cap']} per relationship) into the "
        "`memory` database; "
        "`qlsc recall` reads it back while it holds. Read as the data source.",
        "",
        "## Correctness",
        "",
        f"- **Contexts:** {same_ctx} of {len(cs)} read back from memory exactly as fetched: the same nodes, "
        "properties and relationships.",
        f"- **The same Cypher on both:** {count('same')} of {count('same') + count('DIFFERENT')} context "
        f"questions gave the same rows on memory and on the virtual graph; {count('capped')} were left out, "
        "over a capped relationship.",
        f"- **Idempotence:** remembering three contexts again left memory's counts "
        f"{'unchanged' if res['idempotence']['same'] else 'CHANGED'} "
        f"({res['idempotence']['before']['nodes']} nodes, {res['idempotence']['before']['relationships']} relationships).",
        "",
        "| customer | nodes | relationships | capped | fetch s | recall s | context | questions same / different / capped |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key, c in cs.items():
        v = [q["verdict"] for q in c["questions"].values()]
        L.append(
            f"| {key} | {c['fetched']['nodes']} | {c['fetched']['edges']} | {', '.join(c['fetched']['capped']) or '-'} "
            f"| {c['fetched']['seconds']:.2f} | {c['recalled']['seconds']:.2f} "
            f"| {'same' if not c['differences'] else '; '.join(c['differences'])} "
            f"| {v.count('same')} / {v.count('DIFFERENT')} / {v.count('capped')} |"
        )
    L += ["", "## Freshness", "", "| check | result |", "|---|---|"]
    L += [f"| {name} | {'ok' if x['ok'] else '**FAILED**'} |" for name, x in res["freshness"].items()]
    b = res["batch"]
    L += [
        "",
        "## A batch",
        "",
        f"The {b['customers']} remembered together, in one batch: "
        + (
            "each got the context it got alone (nodes, properties, relationships, and each read's keys, rows "
            "and cap), and read back from memory as that."
            if b["ok"]
            else f"**{len(b['differences'])} differ**: {b['differences']}"
        )
        + f" {b['seconds']} s together, against {b['seconds one at a time']} s one at a time.",
    ]
    L += ["", "## Latency (seconds)", "", "| | median | p95 |", "|---|---|---|"]
    L += [f"| {name} | {x.get('median')} | {x.get('p95')} |" for name, x in res["latency"].items()]
    print(f"-> {write_result('memory', L, res)}")
    ok = same_ctx == len(cs) and not count("DIFFERENT") and res["idempotence"]["same"]
    ok = ok and all(x["ok"] for x in res["freshness"].values()) and res["batch"]["ok"]
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

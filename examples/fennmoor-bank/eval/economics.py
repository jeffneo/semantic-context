"""Memory, phase 5 (plans/2026-09-27-agentic-memory.md, check 2): what memory saves. A simulated agent session
of 50 questions, 10 about each of 5 customers, with and without memory.

  without  each question's compiled SQL runs in BigQuery, its cache off (a first-time query): latency and
           bytes billed
  with     the customers' contexts are fetched together, in one batch (`qlsc remember Customer KEY...`: its
           latency, and the bytes Virtual Graph's jobs billed, from BigQuery's own job log), then each question
           goes by the router's memory route when memory holds its whole answer, and by the same SQL otherwise
What a fetch costs per customer, three ways, each on customers of its own (a fetch's queries for the same
customers would be answered by BigQuery's result cache): one at a time (5 customers), in a batch of 5 (the
session's), in a batch of 50. A warehouse bills the columns it scans, not the rows it returns, so a batch's
reads cost about what one customer's do.
Each fetch has the job log to itself: the next starts GAP seconds after it ends, and its jobs are those between
its start and end, MARGIN seconds either side (BigQuery's clock against ours). BigQuery withholds the statistics
of a job that reads a table with a row access policy (dim_customer): billed, but not reported. Such a job is
counted at BigQuery's minimum, 10 MiB per table it references, and the report says how many there were.
The customers' contexts weren't fetched in the day before (BigQuery's result cache lasts a day). A dimension
read can still be answered by the cache, since the same few sites, branches and products recur across
customers: such a job is counted at the minimum a first read bills, and the report says how many there were.
Both compile each question once, with the same LLM call (its time is common to both, and reported apart). Every
answer memory gives is compared with the SQL's, row for row.

The customers are those, by key, who called and made card purchases in the window, whose contexts aren't
capped (at most memory.cap card and deposit transactions in the window) and weren't fetched in the last day:
the first 5 for the session, the next 5 one at a time, the next 50 in a batch. Read as the data source.

Writes results/economics.md and .json. About 50 LLM calls (compiling the questions) and 120 BigQuery queries:
about ten minutes.
Usage: uv run examples/fennmoor-bank/eval/economics.py
"""

from __future__ import annotations

import datetime as dt
import json
import time

from common import native, quantiles, settings, typed, write_result
from entitlements import owner_client
from google.cloud import bigquery

from qlsc import entitle, memory, navigate
from qlsc.graph import Graph

CANDIDATES = typed("""
MATCH (k:Call)-[:REL(Call,Customer)]->(c:Customer)<-[:REL(CardTransaction,Customer)]-(t:CardTransaction)
WHERE k.conversation_date >= $since AND t.post_date >= $since
RETURN DISTINCT c.customer_key AS key ORDER BY key LIMIT $n
""")
QUESTIONS = [
    "How many accounts does the customer with customer_key {k} hold, by product line?",
    "Card spend by merchant category for the customer with customer_key {k}, last quarter",
    "Number of card purchases by merchant for the customer with customer_key {k}, last quarter",
    "Deposit amounts by transaction type for the customer with customer_key {k}, last quarter",
    "How many calls did the customer with customer_key {k} make last quarter, by queue?",
    "Calls from the customer with customer_key {k} last quarter, by contact center site",
    "Total card spend of the customer with customer_key {k} in June 2026",
    "How many of the accounts of the customer with customer_key {k} are maintained at each branch?",
    "Average call handle time in seconds for the customer with customer_key {k}, last quarter",
    "Monthly deposit totals for the customer with customer_key {k}, last quarter",
]
# What Virtual Graph's jobs billed between two times, and how many BigQuery's result cache answered (billing
# nothing): the customers are chosen so none should be.
VG_BILLED = """
SELECT COUNT(*) AS jobs, IFNULL(SUM(total_bytes_billed), 0) AS billed, COUNTIF(cache_hit) AS cached,
       COUNTIF(total_bytes_billed IS NULL AND NOT cache_hit) AS hidden,
       IFNULL(SUM(IF(total_bytes_billed IS NULL AND NOT cache_hit, ARRAY_LENGTH(referenced_tables), 0)), 0)
         * @minimum AS hidden_floor,
       IFNULL(SUM(IF(cache_hit, ARRAY_LENGTH(referenced_tables), 0)), 0) * @minimum AS cached_floor
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time BETWEEN @since AND @until
  AND EXISTS (SELECT 1 FROM UNNEST(labels) l WHERE l.key = 'app' AND l.value = 'neo4j-virtual-graph')
  AND TRIM(query) != 'SELECT 1'
"""
# Customers whose context the data source fetched in the last day: their fetch's queries may be in BigQuery's
# result cache (a day), so a fetch now would bill nothing and flatter memory.
RECENT = """
MATCH (s:Step {tool: 'recall', owner: $by, origin: 'virtual graph'})-[:READ {context: true}]->(c:Customer)
WHERE s.at > $since
RETURN collect(DISTINCT c.customer_key) AS keys
"""
# How many facts a customer has in the window, per relationship memory caps: an uncapped context is under the
# cap on each.
COUNTS = """
MATCH (t:`{label}`) WHERE t.customer_key IN $keys AND t.`{date}` >= $since
RETURN t.customer_key AS key, count(*) AS n
"""
CAPPED = {"CardTransaction": "post_date", "DepositTransaction": "posted_date"}
SIZES = {"one at a time": 5, "a batch of 5 (the session's)": 5, "a batch of 50": 50}
MIB = 2**20
MINIMUM = 10 * MIB  # what BigQuery bills at least, per table a query references
GAP, MARGIN = 5, 1  # seconds between fetches; and either side of one, for the job log's clock


def norm(rows: list[dict]) -> list[str]:
    """Rows as comparable text, each value as the same thing in BigQuery and Neo4j (a Decimal and a float, a
    date and Neo4j's): the same answer compares equal."""
    return sorted(json.dumps({k: native(v) for k, v in r.items()}, sort_keys=True, default=str) for r in rows)


def vg_billed(since: dt.datetime, until: dt.datetime) -> dict:
    """What Virtual Graph's jobs billed between two times, from BigQuery's job log: it trails the jobs, so
    read until two reads agree."""
    config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("since", "TIMESTAMP", since),
            bigquery.ScalarQueryParameter("until", "TIMESTAMP", until),
            bigquery.ScalarQueryParameter("minimum", "INT64", MINIMUM),
        ]
    )
    last = None
    for _ in range(12):
        r = dict(next(iter(owner_client(settings()).query(VG_BILLED, job_config=config).result())).items())
        if r["jobs"] and r == last:
            return r
        last = r
        time.sleep(10)
    return r


def main() -> int:
    s = settings()
    since_window = memory.window_start(s)
    m = memory.reader_model(s, None)
    p = s["navigate"]
    with memory.virtual_graph(s) as V:
        q, e = entitle.signing(s, None, CANDIDATES)
        candidates = [r["key"] for r in V.rows(q, since=since_window, n=1000, **e)]
    with memory.memory_graph(s) as M:
        day = dt.datetime.now(dt.UTC) - dt.timedelta(days=1)
        recent = set(M.rows(RECENT, by=m.reader, since=day)[0]["keys"])
    candidates = [k for k in candidates if k not in recent]
    with memory.virtual_graph(s) as V:  # uncapped: so every question about them can go to memory
        over = set()
        for label, date in CAPPED.items():
            q, e = entitle.signing(s, None, COUNTS.format(label=label, date=date))
            rows = V.rows(q, keys=candidates, since=since_window, **e)
            over |= {r["key"] for r in rows if r["n"] > s["memory"]["cap"]}
    candidates = [k for k in candidates if k not in over]
    need = sum(SIZES.values())
    if len(candidates) < need:
        raise SystemExit(f"{len(candidates)} customers to fetch, {need} needed")
    res: dict = {"fetches": {}, "customers": {}, "questions": []}

    def fetch(keys: list) -> tuple[dict, dict]:
        """The keys' contexts in one batch, with what its jobs billed: the job log trails the jobs, so read
        afterwards (by `billed`)."""
        t0 = dt.datetime.now(dt.UTC)
        ctxs = memory.recall_batch(s, "Customer", keys, force=True, m=m)
        t1 = dt.datetime.now(dt.UTC)
        time.sleep(GAP)  # the next fetch's jobs start after this one's window
        return ctxs, {"since": t0, "until": t1, "seconds": (t1 - t0).total_seconds()}

    def billed(w: dict) -> dict:
        margin = dt.timedelta(seconds=MARGIN)
        c = vg_billed(w["since"] - margin, w["until"] + margin)
        c["billed"] += c.pop("hidden_floor") + c.pop("cached_floor")
        return c | {"seconds": round(w["seconds"], 3)}

    customers, rest = candidates[:5], candidates[5:]
    ctxs, session = fetch(customers)  # the session's first step: its customers' contexts
    alone = [fetch([k]) for k in rest[:5]]
    _, fifty = fetch(rest[5:55])
    print(
        f"fetched: the session's 5 in {session['seconds']:.1f} s, 5 alone, 50 in {fifty['seconds']:.1f} s",
        flush=True,
    )
    for key in customers:
        c = ctxs[key]
        res["customers"][str(key)] = {"nodes": len(c.nodes), "reads": len(c.reads), "capped": c.capped()}
    runs = {"one at a time": [billed(w) for _, w in alone], "a batch of 5 (the session's)": [billed(session)],
            "a batch of 50": [billed(fifty)]}  # fmt: skip
    for mode, ws in runs.items():
        n = SIZES[mode]
        res["fetches"][mode] = {
            "customers": n,
            "fetches": len(ws),
            "seconds": round(sum(w["seconds"] for w in ws), 3),
            "billed": sum(w["billed"] for w in ws),
            "billed per customer": sum(w["billed"] for w in ws) / n,
            "jobs": sum(w["jobs"] for w in ws),
            "cached": sum(w["cached"] for w in ws),
            "hidden": sum(w["hidden"] for w in ws),
        }
        print(f"{mode}: {res['fetches'][mode]}", flush=True)

    wh = entitle.warehouse(s, None)
    with Graph(s) as G:
        for key in customers:
            for template in QUESTIONS:
                question = template.format(k=key)
                t0 = time.time()
                tr = navigate.trace(G, s, question)
                sql = navigate.answer_compiled(G, s, tr)
                compile_seconds = time.time() - t0
                row = {
                    "customer": str(key),
                    "question": template,
                    "compile_seconds": round(compile_seconds, 2),
                }
                if "sql" not in sql:
                    row |= {"sql": {"ok": False, "why": sql.get("fallback")}}
                    res["questions"].append(row)
                    print(
                        f"{key} {template[:50]}: didn't compile ({sql.get('fallback', '')[:80]})", flush=True
                    )
                    continue
                t0 = time.time()
                out = wh.run(sql["sql"], p["maximum_bytes_billed"], p["cypher_max_rows"], cache=False)
                hidden = bool(out.get("bytes_hidden"))
                row["sql"] = {"ok": out["ok"], "seconds": round(time.time() - t0, 3), "rows": len(out.get("rows") or []),
                              "billed": out.get("bytes_billed", 0) + hidden * MINIMUM * out.get("tables_referenced", 0),
                              "hidden": hidden}  # fmt: skip
                mem = navigate.answer_memory(G, s, tr, execute=True, rows=p["cypher_max_rows"])
                if "result" in mem:
                    same = out["ok"] and norm(out["rows"]) == norm(mem["result"]["rows"])
                    row["memory"] = {"ok": True, "seconds": round(mem["result"]["seconds"], 4), "same": same,
                                     "rows": mem["result"]["total"]}  # fmt: skip
                else:
                    row["memory"] = {"ok": False, "why": mem.get("fallback")}
                res["questions"].append(row)
                x = row["memory"]
                print(f"{key} {template[:50]}: SQL {row['sql']['seconds']:.2f} s {row['sql']['billed'] / MIB:.0f} MiB; "
                      + (f"memory {x['seconds'] * 1000:.0f} ms, {'same' if x['same'] else 'DIFFERENT'}" if x["ok"] else f"not memory: {x['why'][:70]}"),
                      flush=True)  # fmt: skip
    return report(res)


def summarize(res: dict) -> dict:
    qs = [q for q in res["questions"] if q["sql"].get("ok")]
    mem = [q for q in qs if q["memory"]["ok"]]
    session = res["fetches"]["a batch of 5 (the session's)"]
    without = {"seconds": sum(q["sql"]["seconds"] for q in qs), "billed": sum(q["sql"]["billed"] for q in qs)}
    with_ = {
        "seconds": session["seconds"]
        + sum(q["memory"]["seconds"] if q["memory"]["ok"] else q["sql"]["seconds"] for q in qs),
        "billed": session["billed"] + sum(0 if q["memory"]["ok"] else q["sql"]["billed"] for q in qs),
    }
    question = without["billed"] / len(qs) if qs else 0
    return {
        "questions": len(res["questions"]),
        "compiled": len(qs),
        "from memory": len(mem),
        "same answer": sum(q["memory"]["same"] for q in mem),
        "not memory": sorted({q["memory"]["why"] for q in qs if not q["memory"]["ok"]}),
        "sql latency": quantiles([q["sql"]["seconds"] for q in qs]),
        "memory latency": quantiles([q["memory"]["seconds"] for q in mem]),
        "compile latency": quantiles([q["compile_seconds"] for q in res["questions"]]),
        "without memory": without,
        "with memory": with_,
        "sql jobs hidden": sum(q["sql"].get("hidden", False) for q in qs),
        "question billed (mean)": question,
        "break-even questions per customer": {
            mode: f["billed per customer"] / question if question else None
            for mode, f in res["fetches"].items()
        },
    }


def report(res: dict) -> int:
    x = res["summary"] = summarize(res)
    w, wo = x["with memory"], x["without memory"]
    L = [
        "# Memory's economics: a simulated session, with and without memory",
        "",
        "Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as "
        "the data source.",
        "",
        "- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time "
        "query).",
        "- **With memory,** the 5 customers' contexts are fetched together, in one batch. Each question then goes "
        "to memory when the router's memory route finds memory holds its whole answer, and to the same SQL "
        "otherwise.",
        "",
        "Compiling a question (the LLM's typed request) is common to both, so it's reported apart.",
        "",
        f"- **Answered from memory:** {x['from memory']} of {x['compiled']} compiled questions; {x['same answer']} "
        "of them gave the same rows as the SQL.",
        f"- **Latency, from memory:** median {x['memory latency'].get('median')} s, p95 "
        f"{x['memory latency'].get('p95')} s. The SQL's: median {x['sql latency'].get('median')} s, p95 "
        f"{x['sql latency'].get('p95')} s.",
        f"- **The session's query time:** {wo['seconds']:.1f} s without memory, {w['seconds']:.1f} s with it (the "
        "batch fetch included).",
        f"- **The session's bytes billed:** {wo['billed'] / MIB:,.0f} MiB without memory, {w['billed'] / MIB:,.0f} MiB "
        "with it (the batch fetch included).",
        f"- **Compiling a question** (common to both): median {x['compile latency'].get('median')} s.",
        "",
        f"## What a fetch costs, per customer (a question's SQL bills {x['question billed (mean)'] / MIB:,.0f} MiB "
        "on average)",
        "",
        "| fetched | customers | seconds | MiB billed | MiB per customer | break-even: questions per customer | jobs | cached | not reported |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for mode, f in res["fetches"].items():
        be = x["break-even questions per customer"][mode]
        L.append(
            f"| {mode} | {f['customers']} | {f['seconds']:.1f} | {f['billed'] / MIB:,.0f} | "
            f"{f['billed per customer'] / MIB:,.0f} | {be:.1f} | {f['jobs']} | {f['cached']} | {f['hidden']} |"
        )
    L += [
        "",
        "A job BigQuery answered from its result cache (a dimension read whose keys recur), or whose bytes it "
        "didn't report (it reads a row-policied table), is counted at the minimum a first read bills: 10 MiB per "
        f"table it references. {x['sql jobs hidden']} of the questions' SQL jobs weren't reported.",
        "",
        "Why a question didn't go to memory:",
        "",
    ]
    L += [f"- {why}" for why in x["not memory"]] or ["- (every compiled question did)"]
    L += ["", "| customer | question | SQL s | MiB billed | memory ms | same |", "|---|---|---|---|---|---|"]
    for q in res["questions"]:
        sq, mq = q["sql"], q.get("memory", {"ok": False})
        L.append(
            f"| {q['customer']} | {q['question'].replace('{k}', '…')} | {sq.get('seconds', '-')} | "
            f"{round(sq.get('billed', 0) / MIB) if sq.get('ok') else '-'} | "
            f"{round(mq['seconds'] * 1000) if mq.get('ok') else '-'} | "
            f"{('yes' if mq['same'] else '**no**') if mq.get('ok') else '-'} |"
        )
    res = json.loads(json.dumps(res, default=str))
    print(f"-> {write_result('economics', L, res)}")
    ok = x["from memory"] > 0 and x["same answer"] == x["from memory"]
    print("all answers from memory match the SQL" if ok else "SOME ANSWERS FROM MEMORY DIFFER")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

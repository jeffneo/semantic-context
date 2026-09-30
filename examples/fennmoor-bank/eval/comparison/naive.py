"""Naive baselines: the same model with only what the warehouse says about its own data (run.py, README.md).

Its information schema, as the catalog snapshot holds it: 323 tables, their columns and types. No log,
no Variables, no joins, no Computations, no examples, no filter values: nothing of the semantic layer.
  naive-schema  the whole schema in the prompt (a cached prefix: it is the same for every question), one
                query written, dry-run, one fix after a failed dry run: the free SQL route, with the
                schema in place of the layer's cohort
  naive-agent   a generic tool-using agent: list_tables, describe_table, run_sql (rows, capped), submit;
                at most MAX_TURNS model turns, prompt caching
Sonnet 5.5 with the baseline's thinking setting.
"""

from __future__ import annotations

import json

import anthropic
from match import ROWS
from run import text

from qlsc import meter, navigate
from qlsc.config import secret
from qlsc.llm import strict
from qlsc.warehouse import connect

SQL = {"type": "object", "required": ["sql", "explanation"],
       "properties": {"sql": {"type": "string"}, "explanation": {"type": "string"}}}  # fmt: skip
TOOLS = [
    {"name": "list_tables", "description": "The warehouse's tables (project.dataset.table), with their column "
     "counts; `words`: only those whose name contains one of them.",
     "input_schema": {"type": "object", "properties": {"words": {"type": "string"}}}},
    {"name": "describe_table", "description": "A table's columns and their types, and its partition column.",
     "input_schema": {"type": "object", "required": ["table"], "properties": {"table": {"type": "string"}}}},
    {"name": "run_sql", "description": "Run a query and see its first 20 rows and how many there are.",
     "input_schema": {"type": "object", "required": ["sql"], "properties": {"sql": {"type": "string"}}}},
    {"name": "submit", "description": "The final query. Call it once, last.",
     "input_schema": {"type": "object", "required": ["sql"], "properties": {"sql": {"type": "string"}}}},
]  # fmt: skip
MAX_TURNS = 15
MAXIMUM_BYTES_BILLED = 2 * 10**9


def catalog(s) -> dict:
    return json.loads((s.work / "catalog.json").read_text())["tables"]


def schema_text(tables: dict) -> str:
    return "\n".join(
        f"`{t}`: " + ", ".join(f"{c} {ty}" for c, ty in v["columns"].items())
        for t, v in sorted(tables.items())
    )


def client_and_price(s):
    price = next(
        ((p["in"], p["out"]) for p in s["llm"]["prices"] if p["model"] == s["llm"]["query_model"]), None
    )
    return anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY")), price


def create(s, client, price, **kw):
    """One call, retried on a rate limit, measured. Cached: the system prompt when it is a list with its own
    breakpoint (the schema), else the conversation so far (the agent's)."""
    thinking = s["llm"]["query_thinking"]
    if not isinstance(kw.get("system"), list):
        kw["cache_control"] = {"type": "ephemeral"}
    for attempt in range(5):
        try:
            resp = client.messages.create(model=s["llm"]["query_model"],
                                          **({"thinking": {"type": thinking}} if thinking else {}), **kw)  # fmt: skip
            meter.llm(resp.usage, price, s["llm"]["cache_prices"])
            return resp
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
            import time

            time.sleep(2**attempt * 3)
            meter.report(waits=2**attempt * 3)
    raise RuntimeError("no answer after 5 attempts")


def answer_schema(G, s, q: dict) -> dict:
    client, price = client_and_price(s)
    wh = connect(s)
    system = text("naive_system", dialect=wh.sql, today=navigate.calendar(navigate.today(s)),
                  schema=schema_text(catalog(s)), **s.business)  # fmt: skip
    system = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]  # the schema, cached
    msgs = [{"role": "user", "content": text("naive_request", question=q["question"])}]
    fmt = {"output_config": {"format": {"type": "json_schema", "schema": strict(SQL)}}}
    out = None
    for _ in range(2):
        resp = create(s, client, price, max_tokens=4000, system=system, messages=msgs, extra_body=fmt)
        out = json.loads(next(b.text for b in resp.content if b.type == "text"))
        res = wh.dry_run(out["sql"])
        if res["ok"] is not False:
            break
        msgs += [{"role": "assistant", "content": resp.content},
                 {"role": "user", "content": f"The warehouse rejected it: {res['error'][:400]}. Fix the query."}]  # fmt: skip
    return {"writer": "naive", "sql": out["sql"], "result": wh.run(out["sql"], MAXIMUM_BYTES_BILLED, ROWS)}


def answer_agent(G, s, q: dict) -> dict:
    client, price = client_and_price(s)
    wh, tables = connect(s), catalog(s)
    system = text("naive_agent_system", dialect=wh.sql, today=navigate.calendar(navigate.today(s)),
                  **s.business)  # fmt: skip
    msgs = [{"role": "user", "content": q["question"]}]
    used, submitted = {}, None
    for _turn in range(MAX_TURNS):
        resp = create(s, client, price, max_tokens=8000, system=system, messages=msgs, tools=TOOLS)
        msgs.append({"role": "assistant", "content": resp.content})
        calls = [b for b in resp.content if b.type == "tool_use"]
        if not calls:
            msgs.append({"role": "user", "content": "Call submit with the query."})
            continue
        results = []
        for b in calls:
            used[b.name] = used.get(b.name, 0) + 1
            if b.name == "submit":
                submitted = b.input["sql"]
                out = "submitted"
            elif b.name == "list_tables":
                words = (b.input.get("words") or "").lower().split()
                out = json.dumps({t: len(v["columns"]) for t, v in sorted(tables.items())
                                  if not words or any(w in t.lower() for w in words)})  # fmt: skip
            elif b.name == "describe_table":
                v = tables.get(b.input["table"].strip("`"))
                out = json.dumps(v and {"columns": v["columns"], "partition": v.get("partition")} or
                                 {"error": "no such table"})  # fmt: skip
            else:
                r = wh.run(b.input["sql"], MAXIMUM_BYTES_BILLED, 20)
                out = json.dumps(
                    {k: r.get(k) for k in ("ok", "error", "columns", "rows", "total")}, default=str
                )[:6000]
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        if submitted is not None:
            break
        msgs.append({"role": "user", "content": results})
    extra = {"exchange": {"tools": used}}
    if submitted is None:
        return {"writer": "naive-agent", "error": "no query submitted"} | extra
    return {
        "writer": "naive-agent",
        "sql": submitted,
        "result": wh.run(submitted, MAXIMUM_BYTES_BILLED, ROWS),
    } | extra

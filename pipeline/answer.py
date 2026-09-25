#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40", "sqlglot>=30", "google-cloud-bigquery>=3.25"]
# ///
"""Stage 7c: answer a data question with the semantic layer.

An LLM (estate.yaml `qa.model`) works the question the way a careful analyst would, with
the tools in pipeline/tools.py: find candidate tables, check each one's status and
evidence, take joins from the ones the business runs, follow how the business filters,
write BigQuery SQL and dry-run it. It finishes by calling `answer` with the tables, the
joins, the SQL, the warnings an analyst must hear, the traps it stepped around, and what
the evidence cannot tell.

The final SQL is dry-run again by us; a failure goes back to the model once to fix.

--baseline gives the same model the same loop with only what BigQuery's catalog offers
(table names, columns, types, partitioning, dry runs): the comparison M6 is scored on.

Every model call is cached by its full request (work/qa_cache/), so a rerun over an
unchanged graph is free, and any change in what a tool returns re-asks from there on.
Transcripts go to work/answers/.

Usage: uv run pipeline/answer.py [--baseline] "Which contact centers see the most account closures?"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from pathlib import Path

import anthropic

from graphdb import Graph, config, env
from llm import prompt
from tools import CATALOG_TOOLS, SEMANTIC_TOOLS, CatalogTools, SemanticTools

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
CACHE = WORK / "qa_cache"
OUT = WORK / "answers"
MAX_TURNS = 18

COMMON = prompt("answer_common")
SEMANTIC = COMMON + prompt("answer_semantic")
BASELINE = COMMON + prompt("answer_baseline")

ANSWER_TOOL = {"name": "answer", "description": "Give the final answer.", "input_schema": {
    "type": "object", "required": ["summary", "tables", "joins", "sql", "warnings", "avoided", "cannot_tell"],
    "properties": {
        "summary": {"type": "string"},
        "tables": {"type": "array", "items": {"type": "object", "required": ["table", "role", "why"], "properties": {
            "table": {"type": "string"}, "role": {"type": "string"}, "why": {"type": "string"}}}},
        "joins": {"type": "array", "items": {"type": "string"}},
        "sql": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "avoided": {"type": "array", "items": {"type": "object", "required": ["table", "why"], "properties": {
            "table": {"type": "string"}, "why": {"type": "string"}}}},
        "cannot_tell": {"type": "array", "items": {"type": "string"}}}}}


def normalize(ans: dict) -> dict:
    """Models sometimes send a nested array as a JSON string; accept either."""
    out = dict(ans)
    for k in ("tables", "joins", "warnings", "avoided", "cannot_tell"):
        v = out.get(k)
        if isinstance(v, str):
            try:
                v = json.JSONDecoder().raw_decode(v.strip())[0]
            except ValueError:
                v = [v] if v.strip() else []
        out[k] = [x for x in (v or []) if isinstance(x, (dict, str))]
        if k in ("tables", "avoided"):
            out[k] = [x if isinstance(x, dict) else {"table": x, "why": "", "role": ""} for x in out[k]]
    return out


class Agent:
    def __init__(self, baseline: bool = False, cfg: dict | None = None, G: Graph | None = None, trial: int = 0):
        self.cfg = cfg or config()
        qa = self.cfg.get("qa", {})
        self.model = qa.get("model") or self.cfg["llm"]["model"]
        self.baseline = baseline
        self.trial = trial                    # independent repeats: part of the cache key, not the request
        self.G = G or Graph(self.cfg)
        self.tools = CatalogTools(self.G, self.cfg) if baseline else SemanticTools(self.G, self.cfg)
        self.schemas = (CATALOG_TOOLS if baseline else SEMANTIC_TOOLS) + [ANSWER_TOOL]
        today = self.G.rows("MATCH ()-[r:RAN]->() RETURN substring(max(r.last_seen), 0, 10) AS d")[0]["d"]
        self.system = (BASELINE if baseline else SEMANTIC).format(today=today)
        self.client = anthropic.Anthropic(api_key=env()["ANTHROPIC_API_KEY"])
        self.lock = threading.Lock()          # the embedding cache is one file
        CACHE.mkdir(parents=True, exist_ok=True)
        OUT.mkdir(parents=True, exist_ok=True)
        self.usage = {"calls": 0, "cached": 0, "in": 0, "out": 0}

    def create(self, messages: list, force: bool = False):
        req = {"model": self.model, "max_tokens": 6000, "system": self.system, "tools": self.schemas,
               "messages": messages, "tool_choice": {"type": "tool", "name": "answer"} if force else {"type": "auto"}}
        key = hashlib.sha256((json.dumps(req, sort_keys=True, default=str) +
                              (f"|trial {self.trial}" if self.trial else "")).encode()).hexdigest()
        path = CACHE / f"{key}.json"
        if path.exists():
            self.usage["cached"] += 1
            return json.loads(path.read_text())
        for attempt in range(5):
            try:
                resp = self.client.messages.create(**req)
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
                time.sleep(2 ** attempt * 3)
        else:
            raise RuntimeError("LLM unavailable")
        out = {"content": [b.model_dump() for b in resp.content], "stop_reason": resp.stop_reason,
               "usage": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens}}
        self.usage["calls"] += 1
        self.usage["in"] += out["usage"]["in"]
        self.usage["out"] += out["usage"]["out"]
        path.write_text(json.dumps(out))
        return out

    def call_tool(self, name: str, args: dict) -> dict:
        fn = getattr(self.tools, name, None)
        if not fn:
            return {"error": f"no tool {name}"}
        try:
            if name in ("search_tables", "find_columns"):
                with self.lock:
                    return fn(**args)
            return fn(**args)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:300]}"}

    def ask(self, question: str) -> dict:
        messages = [{"role": "user", "content": question}]
        trace, final, fixes = [], None, 0
        for turn in range(MAX_TURNS + 2):
            resp = self.create(messages, force=turn >= MAX_TURNS)
            content = [{k: v for k, v in b.items() if k in ("type", "text", "id", "name", "input")} for b in resp["content"]]
            messages.append({"role": "assistant", "content": content})
            uses = [b for b in content if b["type"] == "tool_use"]
            if not uses:
                messages.append({"role": "user", "content": "Call the answer tool with your final answer."})
                continue
            results = []
            for u in uses:
                if u["name"] == "answer":
                    final = normalize(u["input"])
                    unknown = [t["table"] for t in final["tables"] if not self.tools.resolve(str(t.get("table", "")))]
                    check = self.tools.dry_run(final["sql"]) if (final.get("sql") or "").strip() else {"ok": None}
                    final["dry_run"] = check
                    problem = (f"These entries in tables are not table names: {unknown}. Resend the answer with each "
                               "table's full name." if unknown else
                               f"The SQL fails a dry run: {check.get('error')}. Fix it and call answer again."
                               if check.get("ok") is False else None)
                    if problem and fixes < 2:
                        fixes += 1
                        results.append({"type": "tool_result", "tool_use_id": u["id"], "is_error": True, "content": problem})
                        final = None
                        continue
                    results.append({"type": "tool_result", "tool_use_id": u["id"], "content": "recorded"})
                else:
                    out = self.call_tool(u["name"], u["input"])
                    trace.append({"tool": u["name"], "input": u["input"], "output_chars": len(json.dumps(out))})
                    results.append({"type": "tool_result", "tool_use_id": u["id"],
                                    "content": json.dumps(out, default=str)[:24000]})
            messages.append({"role": "user", "content": results})
            if final:
                break
        rec = {"question": question, "mode": "baseline" if self.baseline else "semantic", "model": self.model,
               "answer": final, "tool_calls": trace, "turns": len([m for m in messages if m["role"] == "assistant"])}
        name = hashlib.sha256(f"{rec['mode']}|{self.model}|{question}".encode()).hexdigest()[:16]
        (OUT / f"{rec['mode']}_{name}_t{self.trial}.json").write_text(json.dumps(rec | {"messages": messages}, indent=1, default=str))
        return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--baseline", action="store_true")
    a = ap.parse_args()
    agent = Agent(baseline=a.baseline)
    rec = agent.ask(" ".join(a.question))
    ans = rec["answer"] or {}
    print(f"# {rec['question']}\n\n{ans.get('summary', '(no answer)')}\n")
    for t in ans.get("tables", []):
        print(f"- {t['table']} ({t['role']}): {t['why']}")
    print("\n```sql\n" + (ans.get("sql") or "") + "\n```")
    print(f"dry run: {ans.get('dry_run')}")
    for k in ("joins", "warnings", "cannot_tell"):
        if ans.get(k):
            print(f"\n{k}:\n" + "\n".join(f"- {x}" for x in ans[k]))
    if ans.get("avoided"):
        print("\navoided:\n" + "\n".join(f"- {x['table']}: {x['why']}" for x in ans["avoided"]))
    print(f"\n{len(rec['tool_calls'])} tool calls, {rec['turns']} turns; {agent.usage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

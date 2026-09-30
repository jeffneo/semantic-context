"""A larger answer key, written from the log: one question per query the business really ran.

The fourteen gold questions are too few to tell two methods apart (one question moves a score by ten
points). The log holds hundreds of queries that answer something. Each becomes a test:
  write  the query shapes that could be a business question: successful SELECTs, not dbt's tests or
         freshness checks, over tables the fill has rows in (or views),
         none a sandbox or a frozen table. A query relative to today runs as of the log's last day.
         For each, Sonnet writes the question the query answers, which output columns an answer must
         hold, and the house-rule filters it leaves unstated; or says it isn't a business question.
         -> eval/log_questions.yaml (prompts in eval/prompts/)
  run    each remaining query runs against the filled data. It is the reference answer. Kept: one to
         ROWS rows, every compared column among its outputs, and not cut short by a row cap the
         question doesn't ask for.
         -> work/log_answers/<id>.json, results/log_answers.md and .json
Scoring is log_accuracy.py. It leaves each question's own query out of the examples navigation
offers, so no test is answered by being handed its reference.

Usage: uv run examples/fennmoor-bank/eval/log_questions.py write [N] | run   (N: only the first N queries)
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import yaml
from common import BUILD, EXAMPLE, settings, write_result
from match import ROWS

from qlsc import navigate
from qlsc.graph import Graph
from qlsc.llm import LLM
from qlsc.warehouse import connect

HERE = Path(__file__).resolve().parent
QUESTIONS = HERE / "log_questions.yaml"
MAXIMUM_BYTES_BILLED = 2 * 10**9

SHAPES = """
MATCH (s:QueryShape {succeeded: true, statement_type: 'SELECT'}) WHERE s.sample_sql IS NOT NULL
MATCH (s)-[:REFERENCES]->(t:Table)
WITH s, collect({id: t.id, kind: t.kind}) AS tables
MATCH (p:Principal)-[r:RAN]->(s)
RETURN s.id AS id, s.sample_sql AS sql, tables, collect(DISTINCT p.kind) AS kinds, sum(r.jobs) AS jobs
ORDER BY id
"""

SCHEMA = {
    "type": "object",
    "required": ["answerable", "reason", "question", "compare", "unstated_filters"],
    "properties": {
        "answerable": {"type": "boolean"},
        "reason": {"type": "string", "description": "why it is or isn't a business question"},
        "question": {"type": "string"},
        "compare": {"type": "array", "items": {"type": "string"}},
        "unstated_filters": {"type": "array", "items": {"type": "string"}},
    },
}

TODAY = re.compile(r"\b(CURRENT_DATE|CURRENT_DATETIME|CURRENT_TIMESTAMP)\s*\([^()]*\)", re.I)
LAST_DAY = "MATCH (t:Table) WHERE t.write_days IS NOT NULL RETURN max(last(t.write_days)) AS d"


def as_of(sql: str, day: str) -> str:
    """A query relative to today, as it ran on the log's last day: its result then has rows."""
    literal = {"CURRENT_DATE": f"DATE '{day}'", "CURRENT_DATETIME": f"DATETIME '{day} 23:59:59'"}
    return TODAY.sub(lambda m: literal.get(m.group(1).upper(), f"TIMESTAMP '{day} 23:59:59'"), sql)


def filled() -> set[str]:
    """The logical tables the fill has rows in (build/data/state.json), shards by their prefix."""
    st = json.loads((BUILD / "data" / "state.json").read_text())
    return set(st["checked"]) | set(st["computed"]) | {re.sub(r"\d{6,8}$", "", k) for k in st["loaded"]}


def candidates(G: Graph) -> list[dict]:
    """Queries that could answer a business question, over tables with rows, none of them a sandbox
    or frozen table (navigation's own test of trust): their result is not the business's answer."""
    have = filled()
    distrusted = {r["t"] for r in G.rows(navigate.DISTRUSTED)}
    day = G.rows(LAST_DAY)[0]["d"]
    logical = lambda t: t.split(".", 1)[1].rstrip("*")
    out = []
    for x in G.rows(SHAPES):
        if '"app": "dbt"' in x["sql"][:400]:
            continue
        x["sql"] = as_of(x["sql"], day)
        ids = {t["id"] for t in x["tables"]}
        if ids & distrusted:
            continue
        if all(t["kind"] == "view" or logical(t["id"]) in have for t in x["tables"]):
            out.append(x)
    return out


def who(x: dict) -> str:
    if "Looker Query Context" in x["sql"]:
        return "a Looker dashboard (production)"
    return "a production service" if "service_account" in x["kinds"] else "an analyst"


def write(limit: int | None = None) -> int:
    s = settings()
    text = lambda name, **v: (HERE / "prompts" / f"{name}.md").read_text().format(**v)
    llm = LLM(text("question_system", **s.business), s, s["llm"]["query_model"])
    with Graph(s) as G:
        shapes = candidates(G)[:limit]
    ask = lambda x: llm.call(
        text("question_request", sql=x["sql"], jobs=x["jobs"], who=who(x)), SCHEMA, "record_question", 1500
    )
    with ThreadPoolExecutor(s["llm"]["concurrency"]) as pool:
        answers = list(pool.map(ask, shapes))
    out = {}
    for x, a in zip(shapes, answers):
        if a["answerable"] and a["question"].strip() and a["compare"]:
            out[f"L{x['id'][:8]}"] = {
                "question": a["question"].strip(),
                "compare": a["compare"],
                "unstated_filters": a["unstated_filters"],
                "shape": x["id"],
                "who": who(x),
                "tables": sorted(t["id"] for t in x["tables"]),
                "sql": x["sql"],
            }
    head = (
        "# Questions written from the log's own queries (eval/log_questions.py write). Each query's\n"
        "# result is the question's reference answer; `compare` names the columns an answer must hold.\n"
    )
    QUESTIONS.write_text(head + yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=110))
    print(
        f"{len(shapes)} candidate queries, {len(out)} questions -> {QUESTIONS.relative_to(EXAMPLE)}; "
        f"{llm.calls} LLM calls ({llm.cached} cached), {llm.tokens['in']:,} tokens in, {llm.tokens['out']:,} out"
    )
    return 0


def plain(v):
    """A warehouse value as JSON keeps it for the matcher: numbers as numbers, dates as ISO text."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dt.date | dt.datetime | dt.time):
        return v.isoformat()
    return str(v)


def answers_dir(s) -> Path:
    d = s.work / "log_answers"
    d.mkdir(exist_ok=True)
    return d


def capped(q: dict, out: dict) -> int | None:
    """The query's final LIMIT, if its result stopped there: a row cap (Looker's 500 or 5000) cuts the
    reference short, unless the question asks for that many (a top ten)."""
    m = re.search(r"\blimit\s+(\d+)\s*;?\s*$", q["sql"].strip(), re.I)
    return int(m.group(1)) if m and out.get("total") == int(m.group(1)) else None


def run() -> int:
    s = settings()
    wh = connect(s)
    qs = yaml.safe_load(QUESTIONS.read_text())
    res, billed = {}, 0
    for qid, q in qs.items():
        path = answers_dir(s) / f"{qid}.json"
        if path.exists():
            out = json.loads(path.read_text())
        else:
            out = wh.run(q["sql"], MAXIMUM_BYTES_BILLED, ROWS)
            path.write_text(json.dumps(out, default=plain))
            billed += out.get("bytes_billed") or 0
        if not out["ok"]:
            verdict = f"failed: {out['error'][:100]}"
        elif not out["rows"]:
            verdict = "empty"
        elif out["total"] > ROWS:
            verdict = f"too many rows ({out['total']:,})"
        elif (cap := capped(q, out)) and not re.search(rf"\b{cap}\b", q["question"]):
            verdict = f"cut off by LIMIT {cap}, which the question doesn't ask for"
        elif missing := [c for c in q["compare"] if c not in out["columns"]]:
            verdict = f"compare names no output column: {', '.join(missing)}"
        else:
            verdict = "kept"
        res[qid] = {"verdict": verdict, "rows": out.get("total"), "question": q["question"]}
        print(f"{qid} {verdict[:60]:60} {out.get('total') or 0:>7,} rows")
    kept = [q for q, r in res.items() if r["verdict"] == "kept"]
    L = ["# Reference answers for the log's questions", ""]
    L.append(
        f"{len(qs)} questions written from the log (`eval/log_questions.yaml`); {len(kept)} kept, with "
        f"one to {ROWS:,} rows and every compared column in the query's output. Billed this run: "
        f"{billed / 2**30:,.2f} GiB."
    )
    L += ["", "| question | verdict | rows |", "|---|---|---|"]
    L += [f"| {q}. {r['question']} | {r['verdict']} | {r['rows'] or 0:,} |" for q, r in res.items()]
    print(f"{len(kept)} of {len(qs)} kept -> {write_result('log_answers', L, res)}")
    return 0


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "write":
        raise SystemExit(write(int(sys.argv[2]) if len(sys.argv) > 2 else None))
    raise SystemExit(run() if step == "run" else print(__doc__) or 2)

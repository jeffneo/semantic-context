"""Explore: a request bank across the log's query shapes (plans/2026-09-30-accuracy-orthogonal.md, "The shape").

For every query shape that could serve a business consumer (a successful SELECT from the log, not dbt's
tests, reading no sandbox or frozen table), Haiku decides whether it does (not a load step, a data test,
a metadata lookup, a look at a table), and writes three requests it answers: two questions by different
askers, and one task, the step of a business process that ran it as an agent would ask for it. The
shape's own SQL is the requests' answer: the business ran it.

  (:Request {id, text, kind: question | task, who, bank: 'shapes', embedding})-[:FROM]->(:QueryShape)
  (:QueryShape)-[:SUCCEEDS {gap_days}]->(:QueryShape)   the same people started running it as they stopped
                                                        running the other, reading alike, a table changed
  (:QueryShape)-[:VARIANT_OF]->(:QueryShape)            the same table and one of the business's
                                                        Computations in common, otherwise different
A Request reaches another through its shape: Request -FROM-> shape -SUCCEEDS|VARIANT_OF- shape <-FROM-
Request. Experimental: in the layer's database, which a rebuild wipes; it replaces the precedent test's
small bank (explore_precedent.py prep writes that one back).

Run: uv run examples/fennmoor-bank/eval/explore_bank.py [--limit=N]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from common import settings
from explore import out_dir, text
from explore_agent import embedder
from explore_precedent import INDEX, similar_reads
from log_questions import LAST_DAY

from qlsc import navigate
from qlsc.graph import Graph
from qlsc.llm import LLM
from qlsc.names import text_id

SHAPES = """
MATCH (s:QueryShape {succeeded: true, statement_type: 'SELECT', origin: 'log'}) WHERE s.sample_sql IS NOT NULL
  AND NOT EXISTS { (s)-[:REFERENCES]->(t:Table) WHERE t.id IN $distrusted }
RETURN s.id AS id, s.sample_sql AS sql, s.jobs AS jobs, s.first_seen AS first_seen, s.last_seen AS last_seen,
       [(p:Principal)-[:RAN]->(s) | p.id] AS principals, [(p:Principal)-[:RAN]->(s) | p.kind] AS kinds,
       [(s)-[:REFERENCES]->(t:Table) | t.id] AS tables, [(s)-[:READS]->(c:Column) | c.name] AS reads,
       [(s)-[:COMPUTES]->(c:Computation) WHERE c.trusted | c.id] AS computes
ORDER BY id
"""
WRITE = """
UNWIND $rows AS r
MERGE (q:Request {id: r.id})
SET q.text = r.text, q.kind = r.kind, q.who = r.who, q.bank = 'shapes', q.embedding = r.embedding
WITH q, r MATCH (s:QueryShape {id: r.shape}) MERGE (q)-[:FROM]->(s)
"""
EDGES = """
UNWIND $rows AS r MATCH (a:QueryShape {{id: r.a}}), (b:QueryShape {{id: r.b}})
CALL (a, b, r) {{ MERGE (a)-[x:{type}]->(b) SET x += r.props }}
"""
REQUESTS = {
    "type": "object",
    "required": ["business", "why", "requests"],
    "properties": {
        "business": {"type": "boolean"},
        "why": {
            "type": "string",
            "description": "in a sentence: what it is, and why it is or isn't business",
        },
        "requests": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "who", "text"],
                "properties": {
                    "kind": {"type": "string", "enum": ["question", "task"]},
                    "who": {"type": "string", "description": "the asker's role, or the process"},
                    "text": {"type": "string"},
                },
            },
        },
    },
}


def edges(shapes: list[dict]) -> tuple[list[dict], list[dict]]:
    import datetime as dt

    day = lambda x: x and dt.datetime.fromisoformat(str(x)[:19])
    succ, variants = [], []
    for a in shapes:
        for b in shapes:
            if a["id"] == b["id"]:
                continue
            fa, lb = day(a["last_seen"]), day(b["first_seen"])
            if (fa and lb and lb > fa and (lb - fa).days <= 21 and set(a["principals"]) & set(b["principals"])
                    and similar_reads(a, b)):  # fmt: skip
                succ.append({"a": b["id"], "b": a["id"], "props": {"gap_days": (lb - fa).days}})
            if (
                a["id"] < b["id"]
                and set(a["tables"]) & set(b["tables"])
                and set(a["computes"]) & set(b["computes"])
            ):
                variants.append({"a": a["id"], "b": b["id"], "props": {}})
    return succ, variants


def main() -> int:
    opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    s = settings()
    writer = LLM(text("explore_bank_requests_system"), s)  # Haiku: not the eval's question writer
    with Graph(s) as G:
        distrusted = [r["t"] for r in G.rows(navigate.DISTRUSTED)]
        shapes = [x for x in G.rows(SHAPES, distrusted=distrusted) if '"app": "dbt"' not in x["sql"][:400]]
        shapes = shapes[: int(opt["limit"])] if "limit" in opt else shapes
        print(f"{len(shapes)} candidate shapes (last log day {G.value(LAST_DAY)})", flush=True)

        def one(x: dict) -> dict:
            who = "a production service" if "service_account" in x["kinds"] else "an analyst"
            out = writer.call(text("explore_bank_requests", who=who, jobs=x["jobs"], sql=x["sql"][:6000]),
                              REQUESTS, max_tokens=2000)  # fmt: skip
            return x | {"verdict": out}

        with ThreadPoolExecutor(8) as pool:
            judged = list(pool.map(one, shapes))
        business = [x for x in judged if x["verdict"]["business"] and x["verdict"]["requests"]]
        rows = [{"id": text_id(f"{x['id']}|{i}"), "shape": x["id"], **r}
                for x in business for i, r in enumerate(x["verdict"]["requests"][:3])]  # fmt: skip
        vecs = embedder(s).embed([r["text"] for r in rows])
        for r, v in zip(rows, vecs):
            r["embedding"] = v
        G.delete("(n:Request)")
        G.run(INDEX, dims=len(vecs[0]))
        G.batch("Request", WRITE, rows)
        succ, variants = edges(business)
        G.run("MATCH (:QueryShape)-[x:SUCCEEDS|VARIANT_OF]->(:QueryShape) DELETE x")
        G.batch("SUCCEEDS", EDGES.format(type="SUCCEEDS"), succ)
        G.batch("VARIANT_OF", EDGES.format(type="VARIANT_OF"), variants)
    kinds = Counter(r["kind"] for r in rows)
    stats = {"candidates": len(shapes), "business": len(business), "requests": len(rows), "kinds": dict(kinds),
             "succeeds": len(succ), "variants": len(variants), "llm": writer.summary()}  # fmt: skip
    (out_dir(s) / "bank-shapes.json").write_text(json.dumps(
        stats | {"not_business": [(x["id"][:12], x["verdict"]["why"]) for x in judged if not x["verdict"]["business"]],
                 "sample": [{k: r[k] for k in ("shape", "kind", "who", "text")} for r in rows]}, indent=1))  # fmt: skip
    print(json.dumps(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

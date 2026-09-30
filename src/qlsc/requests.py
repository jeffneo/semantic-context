"""Requests: what the business asks of the queries it runs, a bank of precedents (plans/2026-09-30-accuracy-orthogonal.md).

For every query shape that could serve a business consumer (a successful SELECT from the log, reading no
sandbox or frozen table), the LLM (prompts/requests*.md) decides whether it does (not a load step, a
data test or freshness check, a metadata lookup, a look at a table) and writes three requests it
answers, as their askers would send them: two questions by different roles, and one task, the step of
a business process that ran it, as an agent carrying out that process would ask for it. The shape's own
SQL is their answer: the business ran it.

  (:Request {id, text, kind: question | task, who, embedding})-[:FROM]->(:QueryShape)
  (:QueryShape)-[:SUCCEEDS {gap_days}]->(:QueryShape)   the same people started running it within
                  requests.succeeds_days of stopping the other, reading alike (requests.succeeds_reads),
                  a table changed: the query that replaced another
  (:QueryShape)-[:VARIANT_OF]->(:QueryShape)            a table and one of the business's trusted
                  Computations in common, otherwise different

A Request reaches another through its shape (Request -FROM-> shape -SUCCEEDS|VARIANT_OF- shape <-FROM-
Request). navigate's precedent route retrieves Requests by embedding (index request_embedding) and runs
their shape's query with the question's values.
"""

from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

from qlsc import navigate
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.llm import LLM, Embedder, prompt
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
INDEX = """CREATE VECTOR INDEX request_embedding IF NOT EXISTS FOR (q:Request) ON q.embedding
OPTIONS {indexConfig: {`vector.dimensions`: $dims, `vector.similarity_function`: 'cosine'}}"""
WRITE = """
UNWIND $rows AS r
MERGE (q:Request {id: r.id})
SET q.text = r.text, q.kind = r.kind, q.who = r.who, q.embedding = r.embedding
WITH q, r MATCH (s:QueryShape {id: r.shape}) MERGE (q)-[:FROM]->(s)
"""
EDGES = """
UNWIND $rows AS r MATCH (a:QueryShape {{id: r.a}}), (b:QueryShape {{id: r.b}})
CALL (a, b, r) {{ MERGE (a)-[x:{type}]->(b) SET x += r.props }}
"""
CLEAR_EDGES = "MATCH (:QueryShape)-[x:SUCCEEDS|VARIANT_OF]->(:QueryShape) DELETE x"
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
PER_SHAPE = 3  # two questions and a task, as prompts/requests.md asks


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def when(x) -> dt.datetime | None:
    return dt.datetime.fromisoformat(str(x)[:19]) if x else None


def edges(shapes: list[dict], days: int, reads: float) -> tuple[list[dict], list[dict]]:
    """SUCCEEDS (b replaced a: the same people, within `days`, reading alike, a table changed) and
    VARIANT_OF (a table and a Computation in common), between the bank's shapes, in a fixed order."""
    succ, variants = [], []
    for a in shapes:
        for b in shapes:
            if a["id"] == b["id"]:
                continue
            last, first = when(a["last_seen"]), when(b["first_seen"])
            if (last and first and first > last and (first - last).days <= days
                    and set(a["principals"]) & set(b["principals"])
                    and jaccard(a["reads"], b["reads"]) >= reads and set(a["tables"]) != set(b["tables"])):  # fmt: skip
                succ.append({"a": b["id"], "b": a["id"], "props": {"gap_days": (first - last).days}})
            if (
                a["id"] < b["id"]
                and set(a["tables"]) & set(b["tables"])
                and set(a["computes"]) & set(b["computes"])
            ):
                variants.append({"a": a["id"], "b": b["id"], "props": {}})
    return succ, variants


def run(s: Settings) -> dict:
    p = s["requests"]
    writer = LLM(prompt("requests_system"), s)
    with Graph(s) as G:
        distrusted = [r["t"] for r in G.rows(navigate.DISTRUSTED)]
        shapes = G.rows(SHAPES, distrusted=distrusted)

        def one(x: dict) -> dict:
            who = "a production service" if "service_account" in x["kinds"] else "an analyst"
            text = prompt("requests", who=who, jobs=x["jobs"], sql=x["sql"][: p["sql_chars"]])
            return x | {"verdict": writer.call(text, REQUESTS, max_tokens=2000)}

        with ThreadPoolExecutor(writer.workers) as pool:
            judged = list(pool.map(one, shapes))
        business = [x for x in judged if x["verdict"]["business"] and x["verdict"]["requests"]]
        rows = [{"id": text_id(f"{x['id']}|{i}"), "shape": x["id"], **r}
                for x in business for i, r in enumerate(x["verdict"]["requests"][:PER_SHAPE])]  # fmt: skip
        vecs = Embedder(s).embed([r["text"] for r in rows])
        for r, v in zip(rows, vecs):
            r["embedding"] = v
        G.delete("(n:Request)")
        if rows:
            G.run(INDEX, dims=len(vecs[0]))
            G.batch("Request", WRITE, rows)
        succ, variants = edges(business, p["succeeds_days"], p["succeeds_reads"])
        G.run(CLEAR_EDGES)
        G.batch("SUCCEEDS", EDGES.format(type="SUCCEEDS"), succ)
        G.batch("VARIANT_OF", EDGES.format(type="VARIANT_OF"), variants)
    out = {"shapes": len(shapes), "business": len(business), "requests": len(rows), "succeeds": len(succ),
           "variants": len(variants)}  # fmt: skip
    print(f"requests: {len(rows)} for {len(business)} of {len(shapes)} shapes (the rest aren't a business "
          f"consumer's); {len(succ)} SUCCEEDS, {len(variants)} VARIANT_OF; {writer.summary()}")  # fmt: skip
    return out

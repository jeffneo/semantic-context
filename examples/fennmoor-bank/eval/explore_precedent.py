"""Explore: precedent, as Request nodes in the graph (plans/2026-09-30-accuracy-orthogonal.md, "The tests").

A small bank simulated for the probe set, not the whole log: for each probe question, the log shapes whose
SQL is closest to it (as today's examples are found) and the most-run shapes over the reference's tables,
standing in for a full bank that would hold them anyway (the answer key chooses what the small bank
contains, never what a question retrieves). Each becomes a Request:
  (:Request {question, request, verified, jobs, first_seen, last_seen, embedding})-[:FROM]->(:QueryShape)
  - question: written by Haiku, in a business user's words (a different writer and prompt from the eval's
    questions, so the bank's phrasing isn't the eval's);
  - request: the typed request that computes the shape's SQL (compiled back by the query model);
  - verified: the request, compiled and run, gives the shape's own result.
Between Requests, from the log:
  (:Request)-[:SUCCEEDS]->(:Request)    a query the same people started running as they stopped running
                                        another like it (the reads alike, the tables not)
  (:Request)-[:VARIANT_OF]->(:Request)  the same fact table and a measure in common, other groupings or
                                        filters
A question is asked with its closest verified Requests as precedents (question -> request), a superseded
one followed to its successor, and the closest one's variants beside it. Never a Request from the
question's own shape (novel questions, the probe's leave-one-out).

`precedent-reask` asks the log questions whose shape the log ran with other values too: the precedent may
then be the question's own query, built from another of its texts (other literals), never the text the
question was written from.

Prep: uv run examples/fennmoor-bank/eval/explore_precedent.py prep      (bank, requests, verification, relationships)
Run:  uv run examples/fennmoor-bank/eval/explore_precedent.py run precedent|precedent-reask [--workers=N]
"""

from __future__ import annotations

import gzip
import json
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from common import settings
from explore import load_probe, out_dir, run, safe_unique_checks, text
from explore_agent import embedder
from log_questions import LAST_DAY, as_of
from match import ROWS, compare

from qlsc import compile as compiler
from qlsc import navigate
from qlsc.graph import Graph
from qlsc.llm import LLM, prompt
from qlsc.names import text_id
from qlsc.warehouse import connect

SHAPE = """
MATCH (s:QueryShape {id: $id})
RETURN s.id AS id, s.sample_sql AS sql, s.jobs AS jobs, s.first_seen AS first_seen, s.last_seen AS last_seen,
       s.statement_type AS type,
       [(s)-[:REFERENCES]->(t:Table) WHERE t.in_catalog | t.id] AS tables,
       [(p:Principal)-[:RAN]->(s) | p.id] AS principals,
       [(s)-[:READS]->(c:Column) | c.name] AS reads,
       [(s)-[:COMPUTES]->(c:Computation) | c.id] AS computes
"""
OVER_TABLES = """
MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table) WHERE t.id IN $tables AND s.origin = 'log'
  AND s.statement_type IN ['SELECT', 'CREATE_TABLE_AS_SELECT']
WITH s, count(DISTINCT t) AS hit ORDER BY hit DESC, s.jobs DESC, s.id LIMIT $n
RETURN s.id AS id
"""
# A query the same people started running as they stopped running another, reading alike: its successor.
SUCCESSORS = """
MATCH (p:Principal)-[:RAN]->(a:QueryShape {id: $id}), (p)-[:RAN]->(b:QueryShape {succeeded: true})
WHERE b <> a AND b.first_seen > a.last_seen
  AND duration.inDays(datetime(a.last_seen), datetime(b.first_seen)).days <= $days
  AND b.statement_type = a.statement_type
WITH DISTINCT b
RETURN b.id AS id, [(b)-[:READS]->(c:Column) | c.name] AS reads, [(b)-[:REFERENCES]->(t:Table) | t.id] AS tables
"""
WRITE_REQUESTS = """
UNWIND $rows AS r
MERGE (q:Request {id: r.id})
SET q += r {.question, .request, .verified, .why, .jobs, .first_seen, .last_seen, .alt}, q.embedding = r.embedding
WITH q, r MATCH (s:QueryShape {id: r.shape}) MERGE (q)-[:FROM]->(s)
"""
WRITE_EDGES = """
UNWIND $rows AS r MATCH (a:Request {{id: r.a}}), (b:Request {{id: r.b}})
CALL (a, b, r) {{ MERGE (a)-[x:{type}]->(b) SET x += r.props }}
"""
INDEX = """CREATE VECTOR INDEX request_embedding IF NOT EXISTS FOR (q:Request) ON q.embedding
OPTIONS {indexConfig: {`vector.dimensions`: $dims, `vector.similarity_function`: 'cosine'}}"""
CLOSEST = """
CALL db.index.vector.queryNodes('request_embedding', 40, $v) YIELD node AS q, score
WHERE q.verified AND CASE WHEN EXISTS { (q)-[:FROM]->(:QueryShape {id: $own}) }
                          THEN $reask AND coalesce(q.alt, false)  // the question's own query: only another text of it
                          ELSE NOT coalesce(q.alt, false) END
RETURN q.id AS id, q.question AS question, q.request AS request, q.jobs AS jobs,
       q.last_seen AS last_seen, score,
       [(q)<-[:SUCCEEDS]-(n:Request) WHERE n.verified |
        n {.id, .question, .request, .jobs, .last_seen, .first_seen}] AS successors,
       [(q)-[:VARIANT_OF]-(v:Request) WHERE v.verified | v {.id, .question, .request}] AS variants
ORDER BY score DESC LIMIT $k
"""
QUESTION = {"type": "object", "required": ["question"], "properties": {"question": {"type": "string"}}}


def rid(shape: str, alt: bool) -> str:
    return f"{shape[:16]}{':alt' if alt else ''}"


def bank_shapes(G, s) -> tuple[set[str], dict[str, str]]:
    """The small bank's shapes, and for the probe's own shapes another text of theirs (other literals)."""
    emb = embedder(s)
    p = s["navigate"]
    shapes = G.rows(navigate.SHAPES, statements=p["example_statements"])
    vecs = emb.embed([navigate.shape_text(x["sql"], p["example_chars"]) for x in shapes])
    distrusted = {r["t"] for r in G.rows(navigate.DISTRUSTED)}
    bank = set()
    probe = load_probe(s)
    for q in probe:
        v = emb.embed([q["question"]])[0]
        bank |= {x["id"] for x in navigate.similar(v, shapes, vecs, distrusted, 8)}
        tables = q.get("tables") or navigate.sql_tables(q["sql"], "bigquery")
        bank |= {r["id"] for r in G.rows(OVER_TABLES, tables=tables, n=5)}
        if q["shape"]:
            bank.add(q["shape"])
    own = {q["shape"] for q in probe if q["shape"]}
    return bank, other_texts(G, s, own)


def other_texts(G, s, own: set[str]) -> dict[str, str]:
    """Another text of each of these shapes, with other literals (the re-ask precedent: the business ran the
    question's own query with other values), when the log has one."""
    texts = defaultdict(list)
    for line in gzip.open(s.work / "texts.ndjson.gz", "rt"):
        t = json.loads(line)
        if t.get("shape_id") in own:
            texts[t["shape_id"]].append(t)
    sample = {
        r["id"]: r["sql"]
        for r in G.rows(
            "MATCH (s:QueryShape) WHERE s.id IN $ids RETURN s.id AS id, s.sample_sql AS sql", ids=sorted(own)
        )
    }
    sample_tid = {sh: text_id(sql) for sh, sql in sample.items()}
    want = {}
    for sh, ts in texts.items():
        mine = next((t["literals"] for t in ts if t["text_id"] == sample_tid.get(sh)), None)
        other = next((t for t in ts if t["text_id"] != sample_tid.get(sh) and t["literals"] != mine), None)
        if other:
            want[other["text_id"]] = sh
    alt = {}
    for line in gzip.open(s.work / "log_groups.ndjson.gz", "rt"):
        g = json.loads(line)
        if g["query"] and (tid := text_id(g["query"])) in want:
            alt[want.pop(tid)] = g["query"]
    return alt


def compile_back(G, s, sh: dict, sql: str, day: str, wh) -> dict:
    """The typed request that computes a shape's SQL, and whether it gives the shape's own result."""
    tables = {r["t"]: {c["name"]: c["type"] for c in r["cols"]} for r in navigate.columns(G, sh["tables"])}
    joins = G.rows(navigate.TRUSTED_JOINS, tables=list(tables), usable=s["variables"]["joins"])
    comps = {r["c"]["id"]: r["c"] for r in G.rows(
        "MATCH (c:Computation) WHERE c.id IN $ids AND c.same_as IS NULL "
        "RETURN c {.id, .name, .kind, .expression, .filters, .grain, .tables, .shapes, .production, .jobs} AS c",
        ids=sh["computes"])}  # fmt: skip
    comps = {k: c for k, c in comps.items() if set(c["tables"]) <= set(tables)}
    cat = compiler.Catalogue(tables, joins, comps)
    values = navigate.filter_values(G, list(tables), s["navigate"]["filter_values"])
    llm = LLM(prompt("compile_system", **s.business), s, s["llm"]["query_model"])
    ask = text("explore_bank_request", sql=sql, tables=compiler.options_text(cat, values), joins=compiler.joins_text(joins),
               computations=compiler.computations_text(cat), today=navigate.calendar(navigate.today(s)))  # fmt: skip
    request = llm.call(ask, compiler.SCHEMA, max_tokens=3000)
    if not request.get("fits", True):
        return {
            "request": request,
            "verified": False,
            "why": "doesn't fit: " + request.get("reason", "")[:200],
        }
    try:
        plan = compiler.plan(request, cat, navigate.unique_check(s), s["navigate"]["compile_hops"])
        mine = compiler.render_sql(plan, wh.dialect)
    except compiler.Unfit as e:
        return {"request": request, "verified": False, "why": "unfit: " + str(e)[:200]}
    body = select_of(sql)
    if body is None:
        return {"request": request, "verified": False, "why": "not a query that can be run safely"}
    ref = wh.run(as_of(body, day), 2 * 10**9, ROWS)
    got = wh.run(mine, 2 * 10**9, ROWS)
    if not ref.get("ok") or not got.get("ok"):
        return {
            "request": request,
            "verified": False,
            "why": "didn't run: " + str(ref.get("error") or got.get("error"))[:200],
        }
    v, why = compare(ref, got, [[c] for c in ref["columns"]])
    return {"request": request, "verified": v == "correct", "why": why[:200]}


def select_of(sql: str) -> str | None:
    """The query a statement computes, when it's safe to run: a SELECT, or a CREATE TABLE AS's or a CREATE
    VIEW's own query. Never DDL or DML itself: verification must not write to the warehouse."""
    import sqlglot
    from sqlglot import exp

    try:
        trees = [t for t in sqlglot.parse(sql, read="bigquery") if t is not None]
    except sqlglot.errors.ParseError:
        return None
    if len(trees) != 1:
        return None
    t = trees[0]
    if isinstance(t, exp.Create) and isinstance(t.expression, exp.Query):
        t = t.expression
    return t.sql(dialect="bigquery") if isinstance(t, exp.Query) else None


def native_times(sh: dict) -> dict:
    import datetime as dt

    for k in ("first_seen", "last_seen"):
        sh[k] = dt.datetime.fromisoformat(sh[k]) if sh.get(k) else None
    return sh


def prep() -> int:
    s = settings()
    safe_unique_checks()
    wh = connect(s)
    writer = LLM(text("explore_bank_question_system"), s)  # Haiku: not the eval's question writer
    emb = embedder(s)
    with Graph(s) as G:
        day = str(G.value(LAST_DAY))[:10]
        bank, alt = bank_shapes(G, s)
        # one round of successors from the whole log: the query that replaced a bank query is in the bank
        infos = {x: native_times(G.rows(SHAPE, id=x)[0]) for x in sorted(bank)}
        for x, sh in list(infos.items()):
            for b in G.rows(SUCCESSORS, id=x, days=21):
                if b["id"] not in infos and similar_reads(sh, b):
                    infos[b["id"]] = native_times(G.rows(SHAPE, id=b["id"])[0])
        print(f"bank: {len(infos)} shapes (successors included), {len(alt)} re-ask texts", flush=True)
        jobs = [(x, sh, sh["sql"], False) for x, sh in infos.items()] + [
            (x, infos[x], sql, True) for x, sql in alt.items()
        ]

        def one(job):
            x, sh, sql, is_alt = job
            q = writer.call(text("explore_bank_question", sql=sql), QUESTION, max_tokens=1000)["question"]
            try:
                back = compile_back(G, s, sh, sql, day, wh)
            except Exception as e:
                back = {"request": {}, "verified": False, "why": f"error: {e!r}"[:200]}
            return {"id": rid(x, is_alt), "shape": x, "question": q, "request": json.dumps(back["request"]),
                    "verified": back["verified"], "why": back["why"], "jobs": sh["jobs"], "alt": is_alt,
                    "first_seen": str(sh["first_seen"]), "last_seen": str(sh["last_seen"])}  # fmt: skip

        rows = []
        with ThreadPoolExecutor(8) as pool:
            for i, r in enumerate(pool.map(one, jobs), 1):
                rows.append(r)
                if i % 25 == 0:
                    print(
                        f"  {i}/{len(jobs)} requests, {sum(x['verified'] for x in rows)} verified", flush=True
                    )
        vecs = emb.embed([r["question"] for r in rows])
        for r, v in zip(rows, vecs):
            r["embedding"] = v
        G.delete("(n:Request)")
        G.run(INDEX, dims=len(vecs[0]))
        G.batch("Request", WRITE_REQUESTS, rows)
        succ, variants = edges(infos, rows)
        G.batch("SUCCEEDS", WRITE_EDGES.format(type="SUCCEEDS"), succ)
        G.batch("VARIANT_OF", WRITE_EDGES.format(type="VARIANT_OF"), variants)
    stats = {"requests": len(rows), "verified": sum(r["verified"] for r in rows), "re-ask": sum(r["alt"] for r in rows),
             "succeeds": len(succ), "variants": len(variants)}  # fmt: skip
    (out_dir(s) / "bank.json").write_text(
        json.dumps(stats | {"why": [(r["id"], r["verified"], r["why"]) for r in rows]}, indent=1)
    )
    print(f"bank: {stats}")
    return 0


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def similar_reads(a: dict, b: dict) -> bool:
    """Alike enough to be one query rewritten: most columns read in common, and a table changed."""
    return jaccard(a["reads"], b["reads"]) >= 0.4 and set(a["tables"]) != set(b["tables"])


def fact(request: str) -> str | None:
    r = json.loads(request or "{}")
    ms = r.get("measures") or []
    col = next((m.get("column") for m in ms if m.get("column")), None)
    return col.rsplit(".", 1)[0] if col else None


def signatures(request: str) -> set[str]:
    r = json.loads(request or "{}")
    return {
        m.get("computation") or f"{m.get('aggregate')}({m.get('column')})" for m in r.get("measures") or []
    }


def edges(infos: dict, rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_shape = {r["shape"]: r for r in rows if not r["alt"]}
    succ, variants = [], []
    for a_id, a in infos.items():
        for b_id, b in infos.items():
            if a_id == b_id or a_id not in by_shape or b_id not in by_shape:
                continue
            if (b["first_seen"] and a["last_seen"] and b["first_seen"] > a["last_seen"]
                    and (b["first_seen"] - a["last_seen"]).days <= 21 and set(a["principals"]) & set(b["principals"])
                    and similar_reads(a, b)):  # fmt: skip
                succ.append({"a": by_shape[b_id]["id"], "b": by_shape[a_id]["id"],
                             "props": {"gap_days": (b["first_seen"] - a["last_seen"]).days}})  # fmt: skip
            ra, rb = by_shape[a_id]["request"], by_shape[b_id]["request"]
            if (
                a_id < b_id
                and fact(ra)
                and fact(ra) == fact(rb)
                and signatures(ra) & signatures(rb)
                and ra != rb
            ):
                variants.append({"a": by_shape[a_id]["id"], "b": by_shape[b_id]["id"], "props": {}})
    return succ, variants


def answer_for(reask: bool):
    lock = threading.Lock()

    def answer(G, s, q: dict, tr: dict) -> dict:
        with lock:
            v = embedder(s).embed([q["question"]])[0]
        hits = G.rows(CLOSEST, v=v, own=q["shape"] or "", reask=reask, k=4)
        entries, seen = [], set()
        for i, h in enumerate(hits):
            for x, note in [(h, "")] + [
                (n, f"(this replaced the one above from {n['first_seen'][:10]})") for n in h["successors"]
            ]:
                if x["id"] not in seen:
                    seen.add(x["id"])
                    entries.append(text("explore_precedent_entry", question=x["question"], note=note,
                                        request=compact(x["request"])))  # fmt: skip
            if i == 0:
                for x in h["variants"][:2]:
                    if x["id"] not in seen:
                        seen.add(x["id"])
                        entries.append(text("explore_precedent_entry", question=x["question"],
                                            note="(a variant of the first)", request=compact(x["request"])))  # fmt: skip
        tr2 = (
            tr | {"addendum": "\n\n" + text("explore_precedents", entries="\n".join(entries))}
            if entries
            else tr
        )
        a = navigate.answer_sql(G, s, tr2, execute=True, rows=ROWS)
        top = hits[0] if hits else {}
        return a | {"explore": {"precedents": len(entries), "top": top.get("question"), "top_score": round(top.get("score", 0), 3),
                                "top_is_own": bool(top) and top["id"].startswith((q["shape"] or "~")[:16])}}  # fmt: skip

    return answer


SLOTS = {"type": "object", "required": ["same_query", "sql"], "properties": {
    "same_query": {"type": "boolean", "description": "true when the question asks this query with other values"},
    "sql": {"type": "string", "description": "the query with only its literal values changed; empty when not the same query"}}}  # fmt: skip


RETRIEVE = """
CALL db.index.vector.queryNodes('request_embedding', 40, $v) YIELD node AS q, score
MATCH (q)-[:FROM]->(sh:QueryShape)
WHERE CASE WHEN sh.id = $own THEN coalesce(q.alt, false) ELSE NOT coalesce(q.alt, false) END
RETURN sh.id AS shape, sh.sample_sql AS sql, q.alt AS alt, score, q.question AS question
ORDER BY score DESC LIMIT $k
"""


def route_retrieved(alt: dict[str, str]):
    """The precedent route with retrieval: the three Requests closest to the question (the question's own
    query only through another of its texts); the first whose query, its values set from the question, is
    still that query shape runs. Else the compiled request."""
    from qlsc_parse import Catalog, fingerprint

    lock = threading.Lock()

    def answer(G, s, q: dict, tr: dict) -> dict:
        wh = connect(s)
        with lock:
            v = embedder(s).embed([q["question"]])[0]
        filler = LLM(text("explore_slot_system"), s, s["llm"]["query_model"])
        cat = Catalog(json.loads((s.work / "catalog.json").read_text()))
        tried = []
        for h in G.rows(RETRIEVE, v=v, own=q["shape"] or "", k=3):
            sql = alt.get(h["shape"]) if h["alt"] else h["sql"]
            if not sql:
                continue
            out = filler.call(text("explore_slot", question=q["question"], sql=sql, today=navigate.today(s).isoformat()),
                              SLOTS, max_tokens=8000)  # fmt: skip
            proj = next((t.split(".")[0] for t in navigate.sql_tables(sql, "bigquery")), None)
            same = (
                out["same_query"]
                and out["sql"]
                and fingerprint(out["sql"], cat, proj).get("shape_id") == h["shape"]
            )
            tried.append(
                {
                    "shape": h["shape"][:8],
                    "own": h["shape"] == q["shape"],
                    "score": round(h["score"], 3),
                    "same": bool(same),
                }
            )
            body = select_of(out["sql"]) if same else None
            if body:
                return {"writer": "precedent", "sql": body, "result": wh.run(body, 2 * 10**9, ROWS),
                        "explore": {"route": "precedent" + (" (own)" if h["shape"] == q["shape"] else " (other)"), "tried": tried}}  # fmt: skip
        return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS) | {
            "explore": {"route": "compiled", "tried": tried}
        }

    return answer


BANK_RETRIEVE = """
CALL db.index.vector.queryNodes('request_embedding', 60, $v) YIELD node AS q, score
WHERE q.bank = 'shapes'
MATCH (q)-[:FROM]->(sh:QueryShape) WHERE NOT sh.id IN $rejected
WITH sh, max(score) AS score ORDER BY score DESC, sh.id LIMIT $k
RETURN sh.id AS shape, sh.sample_sql AS sql, sh.jobs AS jobs, score
"""


def serve_precedent(alt: dict[str, str]):
    """The service with precedent first, over the request bank (explore_bank.py): the shapes of the three
    Requests closest to the request as asked (its context and corrections in it), none the asker rejected;
    the first whose query, its values set from the request, is still that shape runs. The question's own
    shape only through another of its texts (`alt`: the business ran it with other values), never the text
    the question was written from. Else the compiled request, as the baseline."""
    from qlsc_parse import Catalog, fingerprint

    lock = threading.Lock()

    def serve(G, s, tr: dict, q: dict, rejected: set) -> dict:
        wh = connect(s)
        with lock:
            v = embedder(s).embed([tr["question"]])[0]
        filler = LLM(text("explore_slot_system"), s, s["llm"]["query_model"])
        cat = Catalog(json.loads((s.work / "catalog.json").read_text()))
        tried = []
        for h in G.rows(BANK_RETRIEVE, v=v, rejected=sorted(rejected), k=3):
            own = h["shape"] == q["shape"]
            sql = alt.get(h["shape"]) if own else h["sql"]
            if not sql:
                continue
            out = filler.call(text("explore_slot", question=tr["question"], sql=sql, today=navigate.today(s).isoformat()),
                              SLOTS, max_tokens=8000)  # fmt: skip
            proj = next((t.split(".")[0] for t in navigate.sql_tables(sql, "bigquery")), None)
            same = (
                out["same_query"]
                and out["sql"]
                and fingerprint(out["sql"], cat, proj).get("shape_id") == h["shape"]
            )
            tried.append(
                {"shape": h["shape"][:8], "own": own, "score": round(h["score"], 3), "same": bool(same)}
            )
            body = select_of(out["sql"]) if same else None
            if body:
                return {"writer": "precedent", "precedent": h["shape"], "sql": body, "tried": tried,
                        "via": "own" if own else "other",
                        "explanation": f"the business's own query (run {h['jobs']} times), its values set for this request",
                        "result": wh.run(body, 2 * 10**9, ROWS)}  # fmt: skip
        return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS) | {"tried": tried, "via": "compiled"}

    return serve


def route_for(alt: dict[str, str]):
    """The precedent route: the business's own query (another of its texts), its literal values set from the
    question, run as it is; checked to be still the same query shape (the parser's fingerprint). Else, the
    compiled request, as the baseline."""
    from qlsc_parse import Catalog, fingerprint

    def answer(G, s, q: dict, tr: dict) -> dict:
        wh = connect(s)
        sql = alt.get(q["shape"])
        if not sql:
            return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS) | {
                "explore": {"route": "compiled: no precedent"}
            }
        filler = LLM(text("explore_slot_system"), s, s["llm"]["query_model"])
        day = navigate.today(s).isoformat()
        out = filler.call(
            text("explore_slot", question=q["question"], sql=sql, today=day), SLOTS, max_tokens=8000
        )
        cat = Catalog(json.loads((s.work / "catalog.json").read_text()))
        same = (
            out["same_query"]
            and out["sql"]
            and fingerprint(out["sql"], cat, sh_project(q)).get("shape_id") == q["shape"]
        )
        if not same:
            return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS) | {
                "explore": {
                    "route": "compiled: "
                    + ("not the same query" if not out["same_query"] else "the filled query changed shape")
                }
            }
        body = select_of(out["sql"])
        if body is None:
            return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS) | {
                "explore": {"route": "compiled: not a query"}
            }
        return {
            "writer": "precedent",
            "sql": body,
            "result": wh.run(body, 2 * 10**9, ROWS),
            "explore": {"route": "precedent"},
        }

    return answer


def sh_project(q: dict) -> str | None:
    t = (q.get("tables") or [None])[0]
    return t.split(".")[0] if t else None


def compact(request: str) -> str:
    r = {
        k: v
        for k, v in json.loads(request or "{}").items()
        if v not in ("", [], {}, None, 0) and k not in ("fits", "reason")
    }
    return json.dumps(r)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if args[0] == "prep":
        return prep()
    name = args[1]
    only = set(opt["only"].split(",")) if "only" in opt else None
    if name in ("precedent-route", "precedent-route-retrieved", "precedent-route-novel"):
        s = settings()
        with Graph(s) as G:
            _, alt = bank_shapes(G, s)
        if name == "precedent-route-novel":  # the route with the question's own query out of reach
            alt = {}
        else:
            only = only or {q["qid"] for q in load_probe(s) if q["shape"] in alt}
        fn = route_for(alt) if name == "precedent-route" else route_retrieved(alt)
        run(name, fn, int(opt.get("workers", 6)), only,
            notes="The precedent route: the question's own query (another of its texts), its values set from the question.")  # fmt: skip
        return 0
    reask = name == "precedent-reask"
    if reask and not only:
        s = settings()
        with Graph(s) as G:
            only = {q["qid"] for q in load_probe(s) if q["shape"] and G.value(
                "MATCH (q:Request {alt: true})-[:FROM]->(:QueryShape {id: $sh}) RETURN count(q) > 0", sh=q["shape"])}  # fmt: skip
    run(name, answer_for(reask), int(opt.get("workers", 6)), only,
        notes="Precedents from a small bank of Request nodes: " + ("the question's own query, from another of its texts." if reask else "never the question's own shape."))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

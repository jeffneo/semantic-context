"""Explore: iterated context from the semantic layer (plans/2026-09-30-accuracy-orthogonal.md, "The tests").

The compiled request as a loop instead of one call. The model starts from exactly the baseline's prompt
(the cohort's tables, joins, Computations and example SQL), so submitting at once is the baseline's
answer, and may first explore the layer with tools:
  find_columns       the columns whose meaning is closest to some words, anywhere in the layer, with the
                     Variable and business area each belongs to and the log's filter values
  describe_table     a table's columns, liveness (frozen, sandbox), the log's write days, who reads it,
                     its trusted joins; the table joins the request's options
  find_computations  the Computations closest to some words; they join the options
  similar_queries    the log's queries closest to some words (never the question's own)
  check_request      compile a draft request against the options: its SQL, or why it can't compile, the
                     warehouse's dry run, and the request checks' notes. No rows: the data is a separate
                     factor, tested apart
  submit             the final request
The same model and thinking as the baseline (Sonnet 5.5, between tools), so only the loop differs. After
submit, the answer is compiled and run as the baseline's is; a request that doesn't compile falls back to
free SQL, as there.

Prep (once, before the run): uv run examples/fennmoor-bank/eval/explore_agent.py prep   (column embeddings)
Run:                          uv run examples/fennmoor-bank/eval/explore_agent.py run [--workers=N] [--only=...]
"""

from __future__ import annotations

import json
import sys
import threading
from collections import Counter

import anthropic
from explore import run, text

from qlsc import compile as compiler
from qlsc import meter, navigate
from qlsc.config import secret
from qlsc.graph import Graph
from qlsc.llm import Embedder, cosine, prompt
from qlsc.names import short
from qlsc.warehouse import connect

COLUMNS = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog AND c.in_catalog AND NOT t.id CONTAINS '{'
OPTIONAL MATCH (c)-[:IS]->(v:Variable)
OPTIONAL MATCH (c)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(g:Semantic {level: 1}) WHERE u:Variable OR u:Unjoined
RETURN t.id AS t, c.name AS c, c.type AS type, v.name AS variable, collect(DISTINCT g.name)[0] AS area,
       t.frozen AS frozen, t.sandbox AS sandbox
ORDER BY t, c
"""
ALL_VALUES = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column {type: 'STRING'})<-[f:FILTERS]-(:QueryShape)
WHERE f.values IS NOT NULL
UNWIND f.values AS v
WITH t, c, v, count(*) AS shapes ORDER BY shapes DESC, v
RETURN t.id AS t, c.name AS c, collect(v)[..6] AS vals
"""
TABLE = """
MATCH (t:Table {id: $table})
RETURN t.kind AS kind, t.frozen AS frozen, t.sandbox AS sandbox, t.partition_column AS partition,
       t.write_days[0] AS first_write, t.write_days[-1] AS last_write, size(coalesce(t.write_days, [])) AS write_days,
       size(COLLECT { MATCH (p:Principal)-[:RAN]->(:QueryShape)-[:REFERENCES]->(t) RETURN DISTINCT p }) AS readers,
       EXISTS { (p:Principal {kind: 'service_account'})-[:RAN]->(:QueryShape)-[:REFERENCES]->(t) } AS production_reads,
       [(t)-[:HAS_COLUMN]->(c:Column) WHERE c.in_catalog |
        {name: c.name, type: c.type, variable: [(c)-[:IS]->(v:Variable) | v.name][0]}] AS columns
"""
JOINS_FROM = """
MATCH (a:Table {id: $table})-[:HAS_COLUMN]->(x:Column)<-[:ON]-(k:JoinKey)-[:ON]->(y:Column)<-[:HAS_COLUMN]-(b:Table)
WHERE a <> b AND k.identity AND k.confidence IN $usable AND b.in_catalog
RETURN DISTINCT x.name AS column, b.id AS table, y.name AS their_column ORDER BY table, column LIMIT 25
"""
COMPUTATIONS = """
CALL db.index.vector.queryNodes('computation_embedding', 60, $v) YIELD node AS c, score
WHERE score >= 0.6 AND c.trusted AND NOT c.health_check AND c.same_as IS NULL
  AND EXISTS { MATCH (s:QueryShape)-[:COMPUTES]->(c) WHERE NOT s.id IN $exclude }
RETURN c {.id, .name, .kind, .expression, .filters, .grain, .tables, .shapes, .production, .jobs} AS c, score
ORDER BY score DESC LIMIT 8
"""

TOOLS = [
    {"name": "find_columns", "description": "The columns anywhere in the semantic layer whose meaning is closest to "
     "some words (a thing the question names: 'line of business', 'churn score'). Each with its table, type, the "
     "Variable (the real-world thing joined columns share) and business area it belongs to, whether its table is "
     "frozen or a sandbox, and values the log's queries filter it on.",
     "input_schema": {"type": "object", "required": ["words"], "properties": {"words": {"type": "string"}}}},
    {"name": "describe_table", "description": "A table's columns, whether it is frozen (no longer written) or a "
     "sandbox, when the log's queries wrote it (first and last day), how many principals read it and whether "
     "production does, and its trusted joins. The table becomes one the request may use.",
     "input_schema": {"type": "object", "required": ["table"], "properties": {"table": {"type": "string",
                      "description": "project.dataset.table"}}}},
    {"name": "find_computations", "description": "The business's own Computations (measures, derived dimensions, "
     "populations, as its queries compute them) closest to some words. They become options the request may use.",
     "input_schema": {"type": "object", "required": ["words"], "properties": {"words": {"type": "string"}}}},
    {"name": "similar_queries", "description": "SQL the business runs that is closest to some words: how it "
     "computes something, which tables and joins it uses.",
     "input_schema": {"type": "object", "required": ["words"], "properties": {"words": {"type": "string"}}}},
    {"name": "check_request", "description": "Compile a draft request against the options: the SQL it becomes, or "
     "why it can't compile; whether the warehouse accepts it; and notes on it against the question's own words. "
     "No rows are returned.", "input_schema": compiler.SCHEMA},
    {"name": "submit", "description": "The final request. Call it once, last.", "input_schema": compiler.SCHEMA},
]  # fmt: skip

_index: dict = {}
_index_lock = threading.Lock()


def column_docs(G) -> list[dict]:
    values = {(r["t"], r["c"]): r["vals"] for r in G.rows(ALL_VALUES)}
    docs = []
    for r in G.rows(COLUMNS):
        vals = values.get((r["t"], r["c"]))
        doc = f"{short(r['t'])}.{r['c']} ({r['type']})"
        doc += f"; variable: {r['variable']}" if r["variable"] else ""
        doc += f"; area: {r['area']}" if r["area"] else ""
        doc += f"; values: {', '.join(map(str, vals))}" if vals else ""
        docs.append(r | {"doc": doc, "values": vals})
    return docs


class Embeddings:
    """Embeddings for the agent: the shared cache read once and never written (runs in parallel read it),
    and new texts in the agent's own cache, one thread at a time."""

    _lock = threading.Lock()
    _shared: dict = {}

    def __init__(self, s):
        with self._lock:
            if not Embeddings._shared:
                Embeddings._shared.update(Embedder(s).cache)
            self.own = Embedder(s)
            self.own.cache_path = s.work / "qdd" / "explore" / "agent_embeddings.json"
            self.own.cache = (
                json.loads(self.own.cache_path.read_text()) if self.own.cache_path.exists() else {}
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib

        keys = [hashlib.sha256(f"{self.own.dims}|{t}".encode()).hexdigest() for t in texts]
        missing = [t for k, t in zip(keys, texts) if k not in self._shared]
        with self._lock:
            got = (
                dict(zip([k for k in keys if k not in self._shared], self.own.embed(missing)))
                if missing
                else {}
            )
        return [self._shared.get(k) or got[k] for k in keys]


def embedder(s) -> Embeddings:
    return Embeddings(s)


def index(G, s) -> list[tuple[dict, list[float]]]:
    with _index_lock:
        if not _index:
            docs = column_docs(G)
            _index["cols"] = list(zip(docs, embedder(s).embed([d["doc"] for d in docs])))
        return _index["cols"]


class Session:
    """One question's exploration: the options it has opened, and the tools over them."""

    def __init__(self, G, s, tr: dict):
        self.G, self.s, self.tr = G, s, tr
        self.text, cat, self.values = navigate.request_options(G, s, tr)
        self.tables = dict(cat.tables)
        self.computations = dict(cat.computations)
        self.used = Counter()
        self.emb = embedder(s)

    def catalogue(self) -> compiler.Catalogue:
        joins = self.G.rows(
            navigate.TRUSTED_JOINS, tables=list(self.tables), usable=self.s["variables"]["joins"]
        )
        return compiler.Catalogue(self.tables, joins, self.computations)

    def open_table(self, t: str) -> None:
        if t not in self.tables:
            for r in navigate.columns(self.G, [t]):
                self.tables[r["t"]] = {c["name"]: c["type"] for c in r["cols"]}
                self.values |= navigate.filter_values(self.G, [r["t"]], self.s["navigate"]["filter_values"])

    def tool(self, name: str, args: dict) -> str:
        self.used[name] += 1
        if name == "find_columns":
            v = self.emb.embed([args["words"]])[0]
            ranked = sorted(index(self.G, self.s), key=lambda x: -cosine(v, x[1]))[:12]
            return json.dumps([{"table": d["t"], "column": d["c"], "type": d["type"], "variable": d["variable"],
                                "area": d["area"], "frozen": d["frozen"], "sandbox": d["sandbox"],
                                "values": d["values"], "in_options": d["t"] in self.tables} for d, _ in ranked])  # fmt: skip
        if name == "describe_table":
            t = args["table"].strip("`")
            got = self.G.rows(TABLE, table=t)
            if not got:
                return json.dumps({"error": f"no table {t} in the layer"})
            info = got[0] | {"joins": self.G.rows(JOINS_FROM, table=t, usable=self.s["variables"]["joins"])}
            self.open_table(t)
            info["values"] = {c: v for (tt, c), v in self.values.items() if tt == t}
            return json.dumps(info, default=str)[:8000]
        if name == "find_computations":
            v = self.emb.embed([args["words"]])[0]
            rows = self.G.rows(COMPUTATIONS, v=v, exclude=self.tr.get("exclude", []))
            out = []
            for r in rows:
                c = r["c"]
                for t in c["tables"]:
                    self.open_table(t)
                self.computations[c["id"]] = c
                out.append(c | {"similarity": round(r["score"], 3)})
            return json.dumps(out, default=str)[:8000]
        if name == "similar_queries":
            v = self.emb.embed([args["words"]])[0]
            p = self.s["navigate"]
            shapes = [x for x in self.G.rows(navigate.SHAPES, statements=p["example_statements"])
                      if x["id"] not in self.tr.get("exclude", [])]  # fmt: skip
            vecs = self.emb.embed([navigate.shape_text(x["sql"], p["example_chars"]) for x in shapes])
            distrusted = {r["t"] for r in self.G.rows(navigate.DISTRUSTED)}
            got = navigate.similar(v, shapes, vecs, distrusted, 4)
            return json.dumps([{"sql": " ".join(x["sql"].split())[:1200], "tables": x["tables"], "runs": x["jobs"]}
                               for x in got])  # fmt: skip
        if name == "check_request":
            return json.dumps(self.check(args))
        return json.dumps({"error": f"no tool {name}"})

    def check(self, request: dict) -> dict:
        cat = self.catalogue()
        wh = connect(self.s)
        try:
            plan = compiler.plan(
                request, cat, navigate.unique_check(self.s), self.s["navigate"]["compile_hops"]
            )
            sql = compiler.render_sql(plan, wh.dialect)
        except compiler.Unfit as e:
            return {"compiles": False, "why": str(e)}
        dry = wh.dry_run(sql)
        notes = compiler.check(
            request, cat, self.tr["question"], self.values, self.s["navigate"]["compile_check_chars"]
        )
        return {
            "compiles": True,
            "sql": sql,
            "warehouse_accepts": dry["ok"],
            "error": dry.get("error"),
            "notes": notes,
        }


def answer(G, s, q: dict, tr: dict) -> dict:
    """The loop, then the submitted request compiled and run as the baseline's is."""
    sess = Session(G, s, tr)
    client = anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY"))
    system = prompt("compile_system", **s.business) + "\n\n" + text("explore_agent_system")
    msgs = [{"role": "user", "content": sess.text + "\n\n" + text("explore_agent_request")}]
    thinking = s["llm"]["query_thinking"]
    price = next(
        ((p["in"], p["out"]) for p in s["llm"]["prices"] if p["model"] == s["llm"]["query_model"]), None
    )
    submitted, turns, tokens = None, 0, Counter()
    while turns < 12:
        turns += 1
        resp = client.messages.create(
            model=s["llm"]["query_model"], max_tokens=8000, system=system, messages=msgs, tools=TOOLS,
            cache_control={"type": "ephemeral"}, **({"thinking": {"type": thinking}} if thinking else {}),
        )  # fmt: skip
        tokens["in"] += resp.usage.input_tokens + (resp.usage.cache_read_input_tokens or 0)
        tokens["out"] += resp.usage.output_tokens
        meter.llm(resp.usage, price, s["llm"]["cache_prices"])
        msgs.append({"role": "assistant", "content": resp.content})
        calls = [b for b in resp.content if b.type == "tool_use"]
        if not calls:
            msgs.append({"role": "user", "content": "Call submit with the request."})
            continue
        results = []
        for b in calls:
            if b.name == "submit":
                submitted = b.input
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": "submitted"})
            else:
                try:
                    out = sess.tool(b.name, b.input)
                except Exception as e:
                    out = json.dumps({"error": repr(e)[:300]})
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        if submitted is not None:
            break
        msgs.append({"role": "user", "content": results})
    extra = {"explore": {"turns": turns, "tools": dict(sess.used), "tokens": dict(tokens),
                         "opened": sorted(set(sess.tables) - set(tr["top"]))}}  # fmt: skip
    if submitted is None or not submitted.get("fits", True):
        from match import ROWS

        a = navigate.answer_free(G, s, tr, execute=True, rows=ROWS) | {"writer": "free"}
        return a | extra | {"fallback": (submitted or {}).get("reason", "no request submitted")}
    return execute(G, s, tr, submitted, sess) | extra


def execute(G, s, tr: dict, request: dict, sess: Session) -> dict:
    """The submitted request as answer_compiled treats one: the week convention set, compiled, run."""
    from match import ROWS

    p = s["navigate"]
    cat = sess.catalogue()
    starts = compiler.week_starts(
        G.rows(navigate.WEEKS, tables=list(cat.tables), exclude=tr.get("exclude", []))
    )
    compiler.weeks(request, cat, starts, tr["question"])
    wh = connect(s)
    try:
        plan = compiler.plan(request, cat, navigate.unique_check(s), p["compile_hops"])
        sql = compiler.render_sql(plan, wh.dialect)
    except compiler.Unfit as e:
        return navigate.answer_free(G, s, tr, execute=True, rows=ROWS) | {
            "writer": "free",
            "fallback": str(e),
        }
    res = wh.dry_run(sql)
    if res["ok"] is False:
        return navigate.answer_free(G, s, tr, execute=True, rows=ROWS) | {
            "writer": "free",
            "fallback": res["error"][:200],
        }
    return {"writer": "compiled", "request": request, "sql": sql, "dry_run": res,
            "result": wh.run(sql, p["maximum_bytes_billed"], ROWS)}  # fmt: skip


def prep() -> int:
    from common import settings

    s = settings()
    with Graph(s) as G:
        n = len(index(G, s))
    print(f"{n} column documents embedded")
    return 0


def main() -> int:
    opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if sys.argv[1] == "prep":
        return prep()
    only = set(opt["only"].split(",")) if "only" in opt else None
    run(opt.get("name", "agent"), answer, int(opt.get("workers", 6)), only,
        notes="The compiled request as a loop over the semantic layer's tools (Sonnet 5.5, as the baseline).")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

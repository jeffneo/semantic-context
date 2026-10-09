"""The demo page's live connection: Cypher, SQL and a few qlsc commands, run for real from the page.

uv run examples/fennmoor-bank/server.py          # from the repository root; http://127.0.0.1:8787 (QLSC_DEMO_PORT)

The page (ui/) is a static app and cannot hold a database password or reach Bolt, so it talks to this process (Vite proxies /api to it in development).
Everything runs on this machine against the same services the rest of the example uses: the semantic layer and memory (estate.yaml `neo4j`), Virtual Graph
and the composite (`virtualize.neo4j`), and BigQuery through the estate's connector. Nothing is mocked or replayed.

  POST /api/cypher   {target, query, principal?, signed?}  one Cypher query -> columns, rows, and the nodes and relationships in them
  POST /api/sql      {query, principal?}                   one SELECT, in the graph's table names -> columns, rows
  POST /api/method   {command, ...}                        a qlsc command from a fixed list, its output streamed as it prints (one JSON line each)
  POST /api/pick                                           a customer to try memory on: one the page may use, not yet remembered
  GET  /api/info                                           the principals and targets the page offers

Read only, by layers: a Cypher session is opened with READ access, which the server enforces, so a write is refused whatever the query says; procedures that
reach out of the database (files, URLs, other databases, administration) are refused before they are sent; SQL must be one query statement and bills at most
`navigate.maximum_bytes_billed`; every query has a time limit and a row limit. The commands are the example's own and are given fixed argument lists, never a
shell. (`recall` keeps what it fetched in memory: that is what it is for.) The server answers only this machine, and only a page served from it.

Who is asking: `admin` is the data source's own identity, the administrator's view and the page's default. A named principal (entitlements.principals) is
impersonated for real, on Virtual Graph through the JDBC pass-through (the query is signed for them) and on BigQuery as their service account, so the
warehouse's own row and column rules apply. The semantic layer and memory hold the estate's metadata, not its rows, and are the administrator's view.

Presets only, everywhere: the server runs what the page offers and nothing else. ui/dist/presets.json (`npm run presets`, part of `npm run build`; `scripts/stack up` runs it) is the
whole list of Cypher, SQL, questions and recalls, written from the page's own presets, so there is no second list. A visitor's own query, question or customer is refused: a public
page spends no model or warehouse call that the page did not choose, and the local page is the same page. The one thing a visitor does not pick from a list is a customer for
memory: /api/pick chooses one (a customer with calls and card activity, from the warehouse's customer_360, not yet remembered), and a preset names it as `*`, or as the Cypher
parameter $customer; any customer of that pool is allowed, so every instance of a deployment agrees without sharing anything.

Hosted (QLSC_DEMO_HOSTED=1, plans/2026-10-08-cloud-deploy.md): the same process also serves the built page (QLSC_DEMO_STATIC, `ui/dist`) from the address it is on, and listens on
QLSC_DEMO_HOST and $PORT. Commands run QLSC_DEMO_COMMANDS_AT_ONCE at a time (they are processes: it is a memory limit); a visitor beyond that waits for a free slot, and is told.
"""

from __future__ import annotations

import json
import math
import mimetypes
import os
import random
import re
import subprocess
import sys
import threading
import time
from datetime import date, datetime, timedelta
from datetime import time as dtime
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import neo4j
import sqlglot
from neo4j.exceptions import Neo4jError

from qlsc import config, entitle, memory
from qlsc.graph import Graph
from qlsc.warehouse import connect

EXAMPLE = Path(__file__).resolve().parent
ROOT = EXAMPLE.parents[1]
HOST = os.environ.get("QLSC_DEMO_HOST", "127.0.0.1")
PORT = int(
    os.environ.get("PORT") or os.environ.get("QLSC_DEMO_PORT", "8787")
)  # $PORT: where Cloud Run says to listen
HOSTED = os.environ.get("QLSC_DEMO_HOSTED") == "1"
STATIC = Path(os.environ.get("QLSC_DEMO_STATIC") or ROOT / "ui" / "dist").resolve()

ROWS = 500  # rows sent back; the result says when there were more
SECONDS = 30  # a query's time limit
METHOD_SECONDS = 240  # a command's
METHODS_AT_ONCE = int(
    os.environ.get("QLSC_DEMO_COMMANDS_AT_ONCE", "4")
)  # commands are processes (about 300 MB each): this is a memory limit, not a rule about visitors
QUEUE_SECONDS = 120  # a command waits this long for a free slot before it is refused
BODY_BYTES = 20_000
LONG_LIST = 64  # a list property longer than this (an embedding) is summarised: the page never needs its 3,072 numbers
ADMIN = "admin"

# What reaches out of the database, or administers it, is refused before it is sent. The READ session is the barrier; this is the second.
FORBIDDEN = re.compile(
    r"\b(?:apoc\.(?:load|export|import|cypher|periodic|trigger|systemdb|util\.sleep|do|custom|bolt|dv|ttl|config|log)\b"
    r"|gds\.|dbms\.|db\.(?:create|drop|awaitIndex|resample|clearQueryCaches|prepareForReplanning)"
    r"|LOAD\s+CSV|IN\s+TRANSACTIONS)",
    re.I,
)
USING = re.compile(r"\bUSE\s+`?([\w.-]+)`?", re.I)
KNOWN_DATABASES = re.compile(r"(?:bigquery|memory|neo4j|fennmoor(?:\.\w+)?)", re.I)

s = config.load(EXAMPLE / "estate.yaml")
VG = s["virtualize"]["neo4j"]
TARGETS = {  # where a Cypher query goes
    "layer": {"instance": None, "database": s["neo4j"]["database"]},  # the semantic layer
    "memory": {
        "instance": s["memory"]["neo4j"] or None,
        "database": s["memory"]["database"],
    },  # what Virtual Graph reads fetched (the layer's instance, or memory's own)
    "rows": {
        "instance": VG,
        "database": VG["database"],
        "sign": True,
    },  # Virtual Graph: the warehouse's rows as a graph
    "composite": {
        "instance": VG,
        "database": "fennmoor",
        "token": True,
    },  # all of them in one query (USE fennmoor.rows ...)
}
PRESETS_FILE = Path(os.environ.get("QLSC_DEMO_PRESETS") or STATIC / "presets.json")
if not PRESETS_FILE.is_file():
    raise SystemExit(
        f"{PRESETS_FILE} is not there: the page's presets are written by `cd ui && npm run presets` (scripts/stack up does it)"
    )
PRESETS = json.loads(PRESETS_FILE.read_text())  # all that may run
PRESETS_ONLY = "This demo runs the page's own examples: choose one from the list."
PRINCIPALS = {ADMIN: ""} | {name: entitle.principal(s, name) for name in s["entitlements"]["principals"]}

_graphs: dict[str, Graph] = {}
_lock = (
    threading.RLock()
)  # re-entrant: a warehouse for a principal needs their allowlist, which needs the layer's graph
_busy = threading.BoundedSemaphore(METHODS_AT_ONCE)


DEPLOYED = re.compile(
    re.escape(s["warehouse"]["project"]) + "[:.]" + re.escape(s["warehouse"]["dataset_prefix"])
)


SERVICE_ACCOUNTS = re.compile(
    r"[\w.-]+@" + re.escape(s["warehouse"]["project"]) + r"\.iam\.gserviceaccount\.com"
)
NAMED = {v: k for k, v in s["entitlements"]["principals"].items()}


def logical(message: str) -> str:
    """Text in the estate's own words: a principal by its short name, a table without the project and prefix it is deployed under, never the project."""
    message = SERVICE_ACCOUNTS.sub(lambda m: NAMED.get(m.group(0), "a service account"), message)
    return DEPLOYED.sub("", message).replace(s["warehouse"]["project"], "the project")


DENIED = re.compile(
    r"Access Denied|does not have (bigquery\.\w+ )?permission|not authorized|permission denied", re.I
)


def told(message: str) -> str:
    """What a Cypher query's error says. A refusal by the warehouse names the SQL it ran, which the visitor never wrote and which says it may not exist (BigQuery
    does not tell a principal which): so it is said without them, and without saying whether the data exists or whose it is (a denied principal is not told). Anything else, a typo in the query, is said as the database said it."""
    if DENIED.search(message):
        return "This query could not be completed: the data it needs either does not exist or is not available to you."
    return logical(message)


class Refused(Exception):
    """What the visitor asked is not allowed, or cannot be run: said to them as it is."""


def only_presets(ok: bool) -> None:
    """What was asked must be one of the page's presets (as the page sends it: the text unchanged, or the question and route)."""
    if not ok:
        raise Refused(PRESETS_ONLY)


# ---- a customer for memory

CUSTOMERS_SQL = (  # the graph's table names: customers with card and contact-centre activity in the last 90 days, in an order that spreads them
    "SELECT cif_number FROM dw_customer.customer_360 WHERE card_txn_count_90d > 0 AND contacts_90d > 0 "
    "ORDER BY FARM_FINGERPRINT(cif_number) LIMIT 500"
)
_customers: list[str] | None = None


def customers() -> list[str]:
    """The customers the page may use for memory, read once per process: the same on every instance, since it is a function of the warehouse."""
    global _customers
    with _lock:
        if _customers is None:
            out = warehouse(ADMIN).run(CUSTOMERS_SQL, s["navigate"]["maximum_bytes_billed"], 500)
            if not out.get("ok"):
                raise Refused(
                    "the customers are not available: "
                    + logical(out.get("error") or "the warehouse did not answer")
                )
            _customers = [str(r["cif_number"]) for r in out["rows"]]
        return _customers


def pick() -> dict:
    """A customer not yet remembered, at random: so what one visitor's recall fetches is a first fetch, and what is left expires (memory.retain)."""
    pool = customers()
    with memory.memory_graph(s) as M:
        remembered = {r["k"] for r in M.rows("MATCH (c:Customer) RETURN c.cif_number AS k")}
    fresh = [c for c in pool if c not in remembered] or pool
    return {"customer": random.choice(fresh), "of": len(pool), "remembered": len(remembered & set(pool))}


def customer_of(body: dict) -> str | None:
    """The customer a request names, if it is one of the pool: never one a visitor typed."""
    c = body.get("customer")
    if c is None:
        return None
    if str(c) not in customers():
        raise Refused(PRESETS_ONLY)
    return str(c)


def graph(target: str) -> Graph:
    t = TARGETS[target]
    key = json.dumps(
        t["instance"], sort_keys=True
    )  # one connection per instance: the layer's (null), memory's own, Virtual Graph
    with _lock:
        if key not in _graphs:
            _graphs[key] = Graph(s, t["instance"])
        return _graphs[key]


def masked(text: str) -> str:
    """The query without its comments and string literals, so a check does not read what a string says."""
    text = re.sub(r"/\*.*?\*/|//[^\n]*", " ", text, flags=re.S)
    return re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`[^`]*`", " ", text)


def check_cypher(query: str) -> None:
    if not query.strip():
        raise Refused("there is no query")
    body = masked(query)
    if m := FORBIDDEN.search(body):
        raise Refused(
            f"not run: `{m.group(0).strip()}` reaches outside the database, and this demo only reads"
        )
    for m in USING.finditer(body):
        if not KNOWN_DATABASES.fullmatch(m.group(1)):
            raise Refused(f"not run: database `{m.group(1)}` is not one of this demo's")


# ---- values as JSON


def plain(v):
    """A value the page can read: nodes and relationships are kept as such (its graph view draws them); the rest is its text or number."""
    match v:
        case None | bool() | int():
            return v
        case str():
            return logical(v)
        case float():
            return v if math.isfinite(v) else None
        case Decimal():
            return float(v)
        case datetime() | date() | dtime():
            return v.isoformat()
        case timedelta():
            return str(v)
        case bytes():
            return f"<{len(v)} bytes>"
        case neo4j.graph.Node():
            return {"$": "node", "id": v.element_id, "labels": sorted(v.labels), "properties": props(v)}
        case neo4j.graph.Relationship():
            return {
                "$": "rel",
                "id": v.element_id,
                "type": v.type,
                "from": v.start_node.element_id,
                "to": v.end_node.element_id,
                "properties": props(v),
            }
        case neo4j.graph.Path():
            return {
                "$": "path",
                "nodes": [plain(n) for n in v.nodes],
                "rels": [plain(r) for r in v.relationships],
            }
        case list() | tuple():
            if len(v) > LONG_LIST:
                return f"[{len(v):,} values]"
            return [plain(x) for x in v]
        case dict():
            return {str(k): plain(x) for k, x in v.items()}
    return str(v)


def props(e) -> dict:
    return {k: plain(v) for k, v in e.items()}


def elements(value, nodes: dict, rels: dict) -> None:
    """Every node and relationship in a result, once: what the graph view draws."""
    if isinstance(value, dict):
        match value.get("$"):
            case "node":
                nodes.setdefault(value["id"], value)
            case "rel":
                rels.setdefault(value["id"], value)
            case "path":
                for x in value["nodes"] + value["rels"]:
                    elements(x, nodes, rels)
            case _:
                for x in value.values():
                    elements(x, nodes, rels)
    elif isinstance(value, list):
        for x in value:
            elements(x, nodes, rels)


def shaped(columns: list[str], rows: list[list], more: bool, seconds: float, **extra) -> dict:
    nodes: dict = {}
    rels: dict = {}
    elements(rows, nodes, rels)
    rels = {k: r for k, r in rels.items() if r["from"] in nodes and r["to"] in nodes}
    return {
        "columns": columns,
        "rows": rows,
        "more": more,
        "seconds": round(seconds, 3),
        "graph": {"nodes": list(nodes.values()), "relationships": list(rels.values())},
    } | extra


# ---- Cypher


def principal_of(body: dict) -> str:
    who = body.get("principal") or ADMIN
    if who not in PRINCIPALS:
        raise Refused(f"unknown principal {who!r}")
    return who


def cypher(body: dict) -> dict:
    target = body.get("target")
    if target not in TARGETS:
        raise Refused(f"unknown target {target!r}")
    query = str(body.get("query") or "")
    check_cypher(query)
    only_presets(query.rstrip() in PRESETS["cypher"].get(target, []))
    t = TARGETS[target]
    who = principal_of(body)
    G = graph(target)
    params: dict = {}
    if (c := customer_of(body)) and "$customer" in query:
        params["customer"] = c
    sent = query
    if t.get("sign") and body.get("signed", True):
        # the gateway's signature: for a named principal only where the pass-through runs, as `qlsc ask --cypher --as` does
        allow = None if who == ADMIN else entitle.allowlist(graph("layer"), s, who)
        sent, signed = entitle.signing(s, allow, query, G)
        params |= signed
    elif t.get("token"):
        params |= {"qlsc_principal": entitle.token(s, PRINCIPALS[who])}
    elif who != ADMIN and not t.get("sign"):
        raise Refused(
            f"the {target} holds the estate's metadata, not its rows: it is the administrator's view"
        )
    t0 = time.time()
    try:
        with G.driver.session(database=t["database"], default_access_mode=neo4j.READ_ACCESS) as session:
            result = session.run(neo4j.Query(sent, timeout=SECONDS), params)
            columns = list(result.keys())
            rows, more = [], False
            for record in result:
                if len(rows) == ROWS:
                    more = True
                    break
                rows.append([plain(v) for v in record.values()])
            result.consume()
    except Neo4jError as e:
        raise Refused(told((e.message or str(e)).strip())) from e
    return shaped(columns, rows, more, time.time() - t0, sent=sent if sent != query else None, principal=who)


# ---- SQL


_wh: dict[str, object] = {}


def warehouse(who: str):
    """The connector for a principal (the data source's own for admin), made once."""
    with _lock:
        if who not in _wh:
            _wh[who] = (
                connect(s)
                if who == ADMIN
                else entitle.warehouse(s, entitle.allowlist(graph("layer"), s, who))
            )
        return _wh[who]


def sql(body: dict) -> dict:
    asked = str(body.get("query") or "")
    only_presets(asked.rstrip() in PRESETS["sql"])
    query = asked.strip().rstrip(";")
    if not query:
        raise Refused("there is no query")
    who = principal_of(body)
    try:
        statements = sqlglot.parse(query, read="bigquery")
    except sqlglot.errors.ParseError as e:
        raise Refused(str(e)[:300]) from e
    if len(statements) != 1 or not isinstance(statements[0], sqlglot.exp.Query):
        raise Refused("not run: this demo runs one SELECT, and only reads")
    wh = warehouse(who)
    t0 = time.time()
    out = wh.run(query, s["navigate"]["maximum_bytes_billed"], ROWS)
    if not out.get("ok"):
        raise Refused(logical(out.get("error") or "the warehouse did not run it"))
    rows = [[plain(r[c]) for c in out["columns"]] for r in out["rows"]]
    return shaped(
        out["columns"],
        rows,
        out["total"] > len(rows),
        time.time() - t0,
        total=out["total"],
        bytesBilled=out.get("bytes_billed"),
        bytesHidden=bool(out.get("bytes_hidden")),
        principal=who,
    )


# ---- commands


def argv(body: dict) -> list[str]:
    """A command from the fixed list, as an argument list: nothing the visitor typed is ever a command or a flag."""
    command = body.get("command")
    qlsc = [sys.executable, "-c", "from qlsc.cli import main; raise SystemExit(main())"]
    who = body.get("principal") or ADMIN
    if who not in PRINCIPALS:
        raise Refused(f"unknown principal {who!r}")
    acting = [] if who == ADMIN else ["--as", who]
    text = lambda key, n=500: str(body.get(key) or "").strip()[:n]
    if command == "ask":
        if not text("question"):
            raise Refused("there is no question")
        route = {"": [], "auto": [], "sql": ["--sql"], "cypher": ["--cypher"], "memory": ["--memory"]}.get(
            text("route")
        )
        if route is None:
            raise Refused("unknown route")
        only_presets({"question": text("question"), "route": text("route") or "auto"} in PRESETS["ask"])
        return [*qlsc, "ask", *route, "--run", *acting, text("question")]
    if command in ("recall", "remember"):
        label, key = text("label", 80), text("key", 200)
        # a recall's key is a customer of the pool: the preset says `cif_number=*`, the page sends the one it was given
        prop, _, value = key.partition("=")
        only_presets(
            command == "recall"
            and prop == "cif_number"
            and value in customers()
            and {"entity": label, "key": f"{prop}=*"} in PRESETS["recall"]
        )
        if not re.fullmatch(r"\w+", label) or not key or key.startswith("-"):
            raise Refused("a label, and a key or property=value")
        return [*qlsc, command, label, key, *acting]
    if command == "composite":
        only_presets(False)  # no panel runs it: the page's own queries on the composite are Cypher
        return [sys.executable, str(EXAMPLE / "demo.py"), "composite"]
    if command == "exchange":
        n = text("n", 2) or "0"
        if n not in ("0", "1", "2"):
            raise Refused("an exchange is 0, 1 or 2")
        only_presets(n in PRESETS["exchange"])
        return [sys.executable, str(EXAMPLE / "demo.py"), "exchange", n]
    raise Refused(f"unknown command {command!r}")


def stream(body: dict, send) -> None:
    args = argv(body)
    t0 = time.time()
    if not _busy.acquire(blocking=False):  # every slot is in use: wait for one, and say so
        send({"t": "out", "line": "Others are running; waiting for a free place…", "at": 0})
        if not _busy.acquire(timeout=QUEUE_SECONDS):
            raise Refused("Too many are running at once: try again in a moment.")
    try:
        env = os.environ | {
            "QLSC_CONFIG": str(EXAMPLE / "estate.yaml"),
            "PYTHONUNBUFFERED": "1",
            "NO_COLOR": "1",
        }
        proc = subprocess.Popen(
            args, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        timer = threading.Timer(METHOD_SECONDS, proc.kill)
        timer.start()
        try:
            for line in proc.stdout:
                send({"t": "out", "line": logical(line.rstrip("\n")), "at": round(time.time() - t0, 2)})
            code = proc.wait()
        finally:
            timer.cancel()
            proc.kill()
        send({"t": "end", "code": code, "seconds": round(time.time() - t0, 2)})
    finally:
        _busy.release()


# ---- HTTP


class Handler(BaseHTTPRequestHandler):
    server_version = "qlsc-demo"

    def log_message(self, fmt, *args):  # one line a request; a query's text and a token never reach the log
        print(f"{self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)

    def reply(self, code: int, body: dict) -> None:
        data = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def allowed(self) -> bool:
        """Only a page served from this machine: a request from another site open in the same browser carries its own Origin. Hosted, the page is
        served from this process, wherever it is: its Origin is the address the request came to."""
        origin = self.headers.get("Origin")
        if not origin:
            return True
        o = urlparse(origin)
        return o.hostname in ("localhost", "127.0.0.1", "::1") or (
            HOSTED and o.netloc == self.headers.get("Host")
        )

    def page(self, path: str) -> None:
        """Hosted: a file of the built page, or index.html for a route of the page's own (the app's paths are not files)."""
        target = (STATIC / path.lstrip("/")).resolve()
        if not (target.is_file() and STATIC in target.parents) or target.name == "presets.json":
            target = STATIC / "index.html"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        # Vite names an asset by its content, so one never changes; the page itself must be fetched again
        self.send_header(
            "Cache-Control",
            "public, max-age=31536000, immutable" if "/assets/" in f"/{path.lstrip('/')}" else "no-cache",
        )
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/healthz":
            return self.reply(200, {"ok": True})
        if path != "/api/info":
            return (
                self.page(path)
                if HOSTED and not path.startswith("/api/")
                else self.reply(404, {"error": "not found"})
            )
        self.reply(
            200,
            {
                "principals": [{"name": k} for k in PRINCIPALS],
                "targets": list(TARGETS),
                "limits": {"rows": ROWS, "seconds": SECONDS, "bytes": s["navigate"]["maximum_bytes_billed"]},
            },
        )

    def do_POST(self):
        path = urlparse(self.path).path
        if not self.allowed():
            return self.reply(403, {"error": "this demo answers only a page served from this machine"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "send JSON"})
        size = int(self.headers.get("Content-Length") or 0)
        if size > BODY_BYTES:
            return self.reply(413, {"error": "too large"})
        try:
            body = json.loads(self.rfile.read(size) or b"{}")
            if path == "/api/cypher":
                return self.reply(200, cypher(body))
            if path == "/api/sql":
                return self.reply(200, sql(body))
            if path == "/api/pick":
                return self.reply(200, pick())
            if path == "/api/method":
                return self.method(body)
            return self.reply(404, {"error": "not found"})
        except Refused as e:
            return self.reply(400, {"error": str(e)})
        except (json.JSONDecodeError, TypeError, AttributeError):
            return self.reply(400, {"error": "that is not a request this demo understands"})
        except Exception as e:  # a service is down, a login lapsed: said plainly, not as a stack trace
            print(f"{type(e).__name__}: {e}", file=sys.stderr, flush=True)
            return self.reply(502, {"error": f"{type(e).__name__}: {str(e)[:300]}"})

    def method(self, body: dict) -> None:
        argv(body)  # refused before the stream starts, as a plain 400
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        def send(event: dict) -> None:
            self.wfile.write(json.dumps(event, separators=(",", ":")).encode() + b"\n")
            self.wfile.flush()

        try:
            stream(body, send)
        except Refused as e:
            send({"t": "error", "message": str(e)})
        except BrokenPipeError:
            pass


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(
        f"qlsc demo server on http://{HOST}:{PORT}{' (hosted: it serves the page too)' if HOSTED else ''} (targets: {', '.join(TARGETS)}; principals: {', '.join(PRINCIPALS)})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

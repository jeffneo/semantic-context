"""The demo page's live connection: Cypher, SQL and a few qlsc commands, run for real from the page.

uv run examples/fennmoor-bank/server.py          # from the repository root; http://127.0.0.1:8787 (QLSC_DEMO_PORT)

The page (ui/) is a static app and cannot hold a database password or reach Bolt, so it talks to this process (Vite proxies /api to it in development).
Everything runs on this machine against the same services the rest of the example uses: the semantic layer and memory (estate.yaml `neo4j`), Virtual Graph
and the composite (`virtualize.neo4j`), and BigQuery through the estate's connector. Nothing is mocked or replayed.

  POST /api/cypher   {target, query, principal?, signed?}  one Cypher query -> columns, rows, and the nodes and relationships in them
  POST /api/sql      {query, principal?}                   one SELECT, in the graph's table names -> columns, rows
  POST /api/method   {command, ...}                        a qlsc command from a fixed list, its output streamed as it prints (one JSON line each)
  GET  /api/info                                           the principals and targets the page offers

Read only, by layers: a Cypher session is opened with READ access, which the server enforces, so a write is refused whatever the query says; procedures that
reach out of the database (files, URLs, other databases, administration) are refused before they are sent; SQL must be one query statement and bills at most
`navigate.maximum_bytes_billed`; every query has a time limit and a row limit. The commands are the example's own and are given fixed argument lists, never a
shell. (`recall` keeps what it fetched in memory: that is what it is for.) The server answers only this machine, and only a page served from it.

Who is asking: `admin` is the data source's own identity, the administrator's view and the page's default. A named principal (entitlements.principals) is
impersonated for real, on Virtual Graph through the JDBC pass-through (the query is signed for them) and on BigQuery as their service account, so the
warehouse's own row and column rules apply. The semantic layer and memory hold the estate's metadata, not its rows, and are the administrator's view.
"""

from __future__ import annotations

import json
import math
import os
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

from qlsc import config, entitle
from qlsc.graph import Graph
from qlsc.warehouse import connect

EXAMPLE = Path(__file__).resolve().parent
ROOT = EXAMPLE.parents[1]
PORT = int(os.environ.get("QLSC_DEMO_PORT", "8787"))

ROWS = 500  # rows sent back; the result says when there were more
SECONDS = 30  # a query's time limit
METHOD_SECONDS = 240  # a command's
METHODS_AT_ONCE = 2  # the commands that call a model or the warehouse run two at a time
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
    "memory": {"instance": None, "database": s["memory"]["database"]},  # what Virtual Graph reads fetched
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


def graph(target: str) -> Graph:
    t = TARGETS[target]
    key = "vg" if t["instance"] else "layer"
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
    t = TARGETS[target]
    who = principal_of(body)
    G = graph(target)
    params: dict = {}
    sent = query
    if t.get("sign") and body.get("signed", True):
        # the gateway's signature: for a named principal only where the pass-through runs, as `qlsc ask --cypher --as` does
        allow = None if who == ADMIN else entitle.allowlist(graph("layer"), s, who)
        sent, params = entitle.signing(s, allow, query, G)
    elif t.get("token"):
        params = {"qlsc_principal": entitle.token(s, PRINCIPALS[who])}
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


def sql(body: dict) -> dict:
    query = str(body.get("query") or "").strip().rstrip(";")
    if not query:
        raise Refused("there is no query")
    who = principal_of(body)
    try:
        statements = sqlglot.parse(query, read="bigquery")
    except sqlglot.errors.ParseError as e:
        raise Refused(str(e)[:300]) from e
    if len(statements) != 1 or not isinstance(statements[0], sqlglot.exp.Query):
        raise Refused("not run: this demo runs one SELECT, and only reads")
    with _lock:
        if who not in _wh:
            _wh[who] = (
                connect(s)
                if who == ADMIN
                else entitle.warehouse(s, entitle.allowlist(graph("layer"), s, who))
            )
        wh = _wh[who]
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
        return [*qlsc, "ask", *route, "--run", *acting, text("question")]
    if command in ("recall", "remember"):
        label, key = text("label", 80), text("key", 200)
        if not re.fullmatch(r"\w+", label) or not key or key.startswith("-"):
            raise Refused("a label, and a key or property=value")
        return [*qlsc, command, label, key, *acting]
    if command == "composite":
        return [sys.executable, str(EXAMPLE / "demo.py"), "composite"]
    if command == "exchange":
        n = text("n", 2) or "0"
        if n not in ("0", "1", "2"):
            raise Refused("an exchange is 0, 1 or 2")
        return [sys.executable, str(EXAMPLE / "demo.py"), "exchange", n]
    raise Refused(f"unknown command {command!r}")


def stream(body: dict, send) -> None:
    args = argv(body)
    if not _busy.acquire(blocking=False):
        raise Refused("two commands are already running: try again in a moment")
    t0 = time.time()
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
        """Only a page served from this machine: a request from another site open in the same browser carries its own Origin."""
        origin = self.headers.get("Origin")
        return not origin or urlparse(origin).hostname in ("localhost", "127.0.0.1", "::1")

    def do_GET(self):
        if urlparse(self.path).path != "/api/info":
            return self.reply(404, {"error": "not found"})
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
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(
        f"qlsc demo server on http://127.0.0.1:{PORT} (targets: {', '.join(TARGETS)}; principals: {', '.join(PRINCIPALS)})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

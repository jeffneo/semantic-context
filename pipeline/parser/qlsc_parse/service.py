"""HTTP face of qlsc-parse. Plain WSGI, so it runs under gunicorn in docker-compose or
Cloud Run, and behind the AWS Lambda Web Adapter unchanged. No state beyond the
catalog snapshot, which each worker loads once and reloads if the file changes.

  GET  /healthz          {"parser", "catalog"}
  POST /v1/fingerprint   NDJSON {"id", "sql", "project"}             -> {"id", **fingerprint}
  POST /v1/resolve       NDJSON {"id", "sql", "project", "shape_id"} -> {"id", **record}

A request may send `X-Catalog-Version`; if the worker holds a different snapshot it
answers 409, so a driver never mixes records from two catalogs.

Env: CATALOG_PATH (default /catalog/catalog.json).
"""
from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path

from . import COMPILED, PARSER_ID
from .catalog import Catalog
from .fingerprint import fingerprint
from .resolve import resolve

CATALOG_PATH = Path(os.environ.get("CATALOG_PATH", "/catalog/catalog.json"))
_state: dict = {"catalog": None, "mtime": None}


def catalog() -> Catalog:
    m = CATALOG_PATH.stat().st_mtime
    if _state["mtime"] != m:
        _state["catalog"], _state["mtime"] = Catalog.load(CATALOG_PATH), m
    return _state["catalog"]


def _fingerprint(item: dict, cat: Catalog) -> dict:
    return fingerprint(item["sql"], cat, item.get("project"))


def _resolve(item: dict, cat: Catalog) -> dict:
    return resolve(item["sql"], cat, item.get("project"), item.get("shape_id"))


ROUTES = {"/v1/fingerprint": _fingerprint, "/v1/resolve": _resolve}


def respond(start, status: str, body: bytes, ctype="application/json"):
    start(status, [("Content-Type", ctype), ("Content-Length", str(len(body)))])
    return [body]


def app(environ, start_response):
    path, method = environ.get("PATH_INFO", ""), environ.get("REQUEST_METHOD", "GET")
    try:
        cat = catalog()
    except FileNotFoundError:
        return respond(start_response, "503 Service Unavailable",
                       json.dumps({"error": f"no catalog at {CATALOG_PATH}"}).encode())
    if path == "/healthz":
        return respond(start_response, "200 OK", json.dumps({"parser": PARSER_ID, "compiled": COMPILED, "catalog": cat.version}).encode())
    fn = ROUTES.get(path)
    if fn is None or method != "POST":
        return respond(start_response, "404 Not Found", b'{"error": "not found"}')
    want = environ.get("HTTP_X_CATALOG_VERSION")
    if want and want != cat.version:
        return respond(start_response, "409 Conflict",
                       json.dumps({"error": "catalog mismatch", "have": cat.version, "want": want}).encode())
    n = int(environ.get("CONTENT_LENGTH") or 0)
    lines = environ["wsgi.input"].read(n).decode().splitlines()
    t0, out = time.perf_counter(), []
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        try:
            res = fn(item, cat)
        except Exception as e:     # a bug on one item must not fail the batch
            res = {"status": "error", "error": f"crash: {type(e).__name__}: {e}",
                   "trace": traceback.format_exc()[-800:]}
        out.append(json.dumps({"id": item.get("id"), **res}))
    body = ("\n".join(out) + "\n").encode()
    start_response("200 OK", [("Content-Type", "application/x-ndjson"), ("Content-Length", str(len(body))),
                              ("X-Parser", PARSER_ID), ("X-Catalog-Version", cat.version),
                              ("X-Elapsed-Ms", f"{(time.perf_counter() - t0) * 1e3:.1f}")])
    return [body]

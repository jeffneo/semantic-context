"""Batch mode, for Cloud Run jobs or local runs without the HTTP service.

  python -m qlsc_parse fingerprint --catalog catalog.json < texts.ndjson  > fps.ndjson
  python -m qlsc_parse resolve     --catalog catalog.json < shapes.ndjson > records.ndjson

Input and output are the same NDJSON items as the HTTP endpoints.
"""
from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import Pool

from .catalog import Catalog
from .fingerprint import fingerprint
from .resolve import resolve

_cat: Catalog | None = None


def _init(path):
    global _cat
    _cat = Catalog.load(path)


def _fp(line):
    item = json.loads(line)
    return json.dumps({"id": item.get("id"), **fingerprint(item["sql"], _cat, item.get("project"))})


def _rs(line):
    item = json.loads(line)
    return json.dumps({"id": item.get("id"),
                       **resolve(item["sql"], _cat, item.get("project"), item.get("shape_id"))})


def main() -> int:
    ap = argparse.ArgumentParser(prog="qlsc_parse")
    ap.add_argument("op", choices=["fingerprint", "resolve"])
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    fn = _fp if a.op == "fingerprint" else _rs
    lines = (l for l in sys.stdin if l.strip())
    if a.workers > 1:
        with Pool(a.workers, _init, (a.catalog,)) as pool:
            for out in pool.imap(fn, lines, chunksize=64):
                sys.stdout.write(out + "\n")
    else:
        _init(a.catalog)
        for l in lines:
            sys.stdout.write(fn(l) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

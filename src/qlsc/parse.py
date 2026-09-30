"""Parse: fingerprint every distinct query text and resolve one per shape, with the parser (parser/,
qlsc_parse) in a pool of processes (parse.workers).

Inputs (qlsc/extract.py):  <work>/log_groups.ndjson.gz, <work>/catalog.json
Outputs:
  <work>/texts.ndjson.gz    per distinct text: shape id, literal values
  <work>/shapes.ndjson.gz   per shape: usage statistics and the parse record
  <work>/PARSE_HEALTH.md    resolution health, cross-check against the warehouse's own references
  <work>/REVIEW_SAMPLE.md   20 shapes across workloads, SQL next to what was extracted

A shape is a query text with its literals taken out: the same query run for different dates or ids.
"""

from __future__ import annotations

import gzip
import json
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from qlsc import health
from qlsc.config import Settings
from qlsc.names import text_id
from qlsc_parse import COMPILED, PARSER_ID, Catalog, fingerprint, resolve

# ------------------------------------------------------------------------ the pool

_catalog: Catalog | None = None  # each worker process's, loaded once


def _load(path: str) -> None:
    global _catalog
    _catalog = Catalog.load(path)


def _guarded(fn, item: dict, *args) -> tuple[str, dict]:
    try:
        return item["id"], fn(item["sql"], _catalog, item["project"], *args)
    except Exception as e:  # a bug on one item must not fail the run
        return item["id"], {"status": "error", "error": f"crash: {type(e).__name__}: {e}",
                            "trace": traceback.format_exc()[-800:]}  # fmt: skip


def _fingerprint(item: dict) -> tuple[str, dict]:
    return _guarded(fingerprint, item)


def _resolve(item: dict) -> tuple[str, dict]:
    return _guarded(resolve, item, item["id"])


def pooled(fn, items: list[dict], pool: ProcessPoolExecutor) -> dict[str, dict]:
    return dict(pool.map(fn, items, chunksize=64))


# ---------------------------------------------------------------------- helpers


def load_groups(work: Path, sample: float | None) -> tuple[list[dict], dict[str, dict]]:
    groups, texts = [], {}
    for line in gzip.open(work / "log_groups.ndjson.gz", "rt"):
        g = json.loads(line)
        if not g["query"]:
            continue
        tid = text_id(g["query"])
        if sample is not None and int(tid[:8], 16) / 0xFFFFFFFF >= sample:
            continue
        g["text_id"] = tid
        groups.append(g)
        t = texts.setdefault(tid, {"sql": g["query"], "jobs": 0, "errors": 0, "projects": Counter()})
        t["jobs"] += g["jobs"]
        t["errors"] += g["errors"]
        t["projects"][g["project_id"]] += g["jobs"]
    return groups, texts


def shape_stats(groups: list[dict], text_shape: dict[str, str]) -> dict[str, dict]:
    S: dict[str, dict] = {}
    for g in groups:
        sid = text_shape.get(g["text_id"])
        if sid is None:
            continue
        s = S.setdefault(
            sid,
            {
                "jobs": 0,
                "errors": 0,
                "cache_hits": 0,
                "bytes_billed": 0,
                "bytes_processed": 0,
                "texts": set(),
                "principals": Counter(),
                "statement_types": Counter(),
                "projects": Counter(),
                "error_reasons": Counter(),
                "first_seen": g["first_seen"],
                "last_seen": g["last_seen"],
            },
        )
        for k in ("jobs", "errors", "cache_hits", "bytes_billed", "bytes_processed"):
            s[k] += g[k] or 0
        s["texts"].add(g["text_id"])
        s["principals"][g["user_email"]] += g["jobs"]
        s["statement_types"][g["statement_type"]] += g["jobs"]
        s["projects"][g["project_id"]] += g["jobs"]
        if g["error_reason"]:
            s["error_reasons"][g["error_reason"]] += g["errors"]
        s["first_seen"] = min(s["first_seen"], g["first_seen"])
        s["last_seen"] = max(s["last_seen"], g["last_seen"])
    for s in S.values():
        s["texts"] = len(s["texts"])
        for k in ("principals", "statement_types", "projects", "error_reasons"):
            s[k] = dict(s[k].most_common())
    return S


# ------------------------------------------------------------------------- main


def run(s: Settings, sample: float | None = None) -> None:
    work = s.work
    cat = json.loads((work / "catalog.json").read_text())
    workers = s["parse"]["workers"]
    pool = ProcessPoolExecutor(workers, initializer=_load, initargs=(str(work / "catalog.json"),))

    groups, texts = load_groups(work, sample)
    jobs = sum(g["jobs"] for g in groups)
    print(
        f"{jobs:,} jobs, {len(groups):,} groups, {len(texts):,} distinct texts"
        + (f" (sample {sample:.0%})" if sample else "")
    )

    # fingerprint every distinct text, plus every view definition in the catalog
    items = [
        {"id": tid, "sql": t["sql"], "project": t["projects"].most_common(1)[0][0]}
        for tid, t in texts.items()
    ]
    views = {
        f"catalog:{fqn}": {"sql": f"CREATE VIEW `{fqn}` AS {t['view_sql']}", "project": fqn.split(".")[0]}
        for fqn, t in cat["tables"].items()
        if t.get("view_sql")
    }
    items += [{"id": k, **v} for k, v in views.items()]
    t0 = time.perf_counter()
    fps = pooled(_fingerprint, items, pool)
    fp_wall = time.perf_counter() - t0
    text_shape = {tid: f["shape_id"] for tid, f in fps.items() if f.get("shape_id")}

    # representative per shape: the text with the most successful jobs, then the shortest
    by_shape: dict[str, list[str]] = defaultdict(list)
    for tid, sid in text_shape.items():
        by_shape[sid].append(tid)

    def rank(tid):
        if tid.startswith("catalog:"):
            return (0, 0)
        t = texts[tid]
        return (t["jobs"] - t["errors"], -len(t["sql"]))

    rep = {sid: max(tids, key=rank) for sid, tids in by_shape.items()}

    def sql_of(tid):
        return views[tid]["sql"] if tid.startswith("catalog:") else texts[tid]["sql"]

    def project_of(tid):
        return (
            views[tid]["project"]
            if tid.startswith("catalog:")
            else texts[tid]["projects"].most_common(1)[0][0]
        )

    # resolve one representative per shape
    t0 = time.perf_counter()
    with pool:
        recs = pooled(
            _resolve,
            [{"id": sid, "sql": sql_of(tid), "project": project_of(tid)} for sid, tid in rep.items()],
            pool,
        )
    res_wall = time.perf_counter() - t0

    stats = shape_stats(groups, text_shape)
    with gzip.open(work / "texts.ndjson.gz", "wt") as f:
        for tid, fp in fps.items():
            f.write(
                json.dumps(
                    {
                        "text_id": tid,
                        "shape_id": fp.get("shape_id"),
                        "literals": fp.get("literals"),
                        "error": fp.get("error"),
                    }
                )
                + "\n"
            )
    shapes = []
    for sid, tid in rep.items():
        origin = "catalog_view" if all(t.startswith("catalog:") for t in by_shape[sid]) else "log"
        rec = recs[sid]
        shapes.append(
            {
                "shape_id": sid,
                "origin": origin,
                "sample_text_id": tid,
                "sample_sql": sql_of(tid),
                "stats": stats.get(sid),
                "record": rec,
            }
        )
    with gzip.open(work / "shapes.ndjson.gz", "wt") as f:
        for s in shapes:
            f.write(json.dumps(s) + "\n")

    timing = {
        "fingerprint_items": len(items),
        "fingerprint_wall_s": fp_wall,
        "resolve_items": len(rep),
        "resolve_wall_s": res_wall,
        "parser": PARSER_ID,
        "compiled": COMPILED,
        "workers": workers,
        "sample": sample,
        "jobs": jobs,
        "groups": len(groups),
        "texts": len(texts),
    }
    health.write(shapes, groups, fps, cat, timing, work)
    print(
        f"fingerprinted {len(items):,} texts in {fp_wall:.1f}s, resolved {len(rep):,} shapes in {res_wall:.1f}s "
        f"-> {work / 'PARSE_HEALTH.md'}, {work / 'REVIEW_SAMPLE.md'}"
    )

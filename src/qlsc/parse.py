"""Parse: fingerprint every distinct query text and resolve one per shape, through the parser service.

Inputs (qlsc/extract.py):  <work>/log_groups.ndjson.gz, <work>/catalog.json
Outputs:
  <work>/texts.ndjson.gz    per distinct text: shape id, literal values, annotations
  <work>/shapes.ndjson.gz   per shape: usage statistics and the parse record
  <work>/PARSE_HEALTH.md    resolution health, cross-check against the warehouse's own references
  <work>/REVIEW_SAMPLE.md   20 shapes across workloads, SQL next to what was extracted

A shape is a query text with its literals taken out: the same query run for different dates or ids.
The service must be up: docker compose up -d parser
"""

from __future__ import annotations

import gzip
import json
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from qlsc import health
from qlsc.config import ConfigError, Settings
from qlsc.names import text_id

# ------------------------------------------------------------------------ service


class Parser:
    def __init__(self, url: str, catalog_version: str, batch: int, concurrency: int):
        self.url, self.version, self.batch, self.conc = url.rstrip("/"), catalog_version, batch, concurrency
        self.server_ms = 0.0

    def health(self) -> dict:
        with urllib.request.urlopen(self.url + "/healthz", timeout=10) as r:
            return json.loads(r.read())

    def _post(self, path: str, items: list[dict]) -> list[dict]:
        body = ("\n".join(json.dumps(i) for i in items) + "\n").encode()
        req = urllib.request.Request(
            self.url + path,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-ndjson", "X-Catalog-Version": self.version},
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            self.server_ms += float(r.headers.get("X-Elapsed-Ms", 0))
            return [json.loads(line) for line in r.read().decode().splitlines() if line.strip()]

    def run(self, path: str, items: list[dict]) -> dict:
        batches = [items[i : i + self.batch] for i in range(0, len(items), self.batch)]
        out = {}
        with ThreadPoolExecutor(self.conc) as ex:
            for res in ex.map(lambda b: self._post(path, b), batches):
                for r in res:
                    out[r["id"]] = r
        return out


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
                "slot_ms": 0,
                "texts": set(),
                "principals": Counter(),
                "statement_types": Counter(),
                "projects": Counter(),
                "weeks": Counter(),
                "week_bytes": Counter(),
                "error_reasons": Counter(),
                "first_seen": g["first_seen"],
                "last_seen": g["last_seen"],
            },
        )
        for k in ("jobs", "errors", "cache_hits", "bytes_billed", "bytes_processed", "slot_ms"):
            s[k] += g[k] or 0
        s["texts"].add(g["text_id"])
        s["principals"][g["user_email"]] += g["jobs"]
        s["statement_types"][g["statement_type"]] += g["jobs"]
        s["projects"][g["project_id"]] += g["jobs"]
        s["weeks"][g["week"]] += g["jobs"]
        s["week_bytes"][g["week"]] += g["bytes_billed"] or 0
        if g["error_reason"]:
            s["error_reasons"][g["error_reason"]] += g["errors"]
        s["first_seen"] = min(s["first_seen"], g["first_seen"])
        s["last_seen"] = max(s["last_seen"], g["last_seen"])
    for s in S.values():
        s["texts"] = len(s["texts"])
        for k in ("principals", "statement_types", "projects", "weeks", "week_bytes", "error_reasons"):
            s[k] = dict(s[k].most_common())
    return S


# ------------------------------------------------------------------------- main


def run(s: Settings, sample: float | None = None) -> None:
    work = s.work
    cat = json.loads((work / "catalog.json").read_text())
    pc = s["parser"]
    P = Parser(pc["url"], cat["version"], pc["batch_size"], pc["concurrency"])
    h = P.health()
    if h["catalog"] != cat["version"]:
        raise ConfigError(f"the parser holds catalog {h['catalog']}, {work} has {cat['version']}: restart it")

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
    fps = P.run("/v1/fingerprint", items)
    fp_wall, fp_server = time.perf_counter() - t0, P.server_ms
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
    P.server_ms = 0.0
    t0 = time.perf_counter()
    recs = P.run(
        "/v1/resolve",
        [
            {"id": sid, "sql": sql_of(tid), "project": project_of(tid), "shape_id": sid}
            for sid, tid in rep.items()
        ],
    )
    res_wall, res_server = time.perf_counter() - t0, P.server_ms

    stats = shape_stats(groups, text_shape)
    with gzip.open(work / "texts.ndjson.gz", "wt") as f:
        for tid, fp in fps.items():
            f.write(
                json.dumps(
                    {
                        "text_id": tid,
                        "shape_id": fp.get("shape_id"),
                        "literals": fp.get("literals"),
                        "annotations": fp.get("annotations"),
                        "error": fp.get("error"),
                    }
                )
                + "\n"
            )
    shapes = []
    for sid, tid in rep.items():
        origin = "catalog_view" if all(t.startswith("catalog:") for t in by_shape[sid]) else "log"
        rec = {k: v for k, v in recs[sid].items() if k != "id"}
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
        "fingerprint_server_ms": fp_server,
        "resolve_items": len(rep),
        "resolve_wall_s": res_wall,
        "resolve_server_ms": res_server,
        "workers": h,
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

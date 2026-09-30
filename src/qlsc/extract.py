"""Extract: the aggregated query log and the catalog snapshot, through the warehouse connector.

  <work>/log_groups.ndjson.gz          one record per distinct (query text, principal, statement type,
                                       project, week) with counts, bytes, time range, references
  <work>/principal_profiles.ndjson.gz  per principal, its time profile (schedule or people)
  <work>/catalog.json                  tables, columns, types, partitioning, view SQL, shard families,
                                       physical -> logical dataset aliases; what the parser resolves against

Job rows never leave the warehouse: the connector groups them there. On a real estate this is the
step that turns billions of jobs into distinct texts.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict

from qlsc.config import Settings
from qlsc.warehouse import Warehouse, connect
from qlsc_parse.catalog import canonical

SHARD = re.compile(r"^(20\d{6}|20\d{4})$")  # a date shard's suffix


def jsonable(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    if isinstance(v, list):
        return [jsonable(x) for x in v]
    return v


def write_ndjson(path, rows) -> int:
    n = 0
    with gzip.open(path, "wt") as f:
        for r in rows:
            f.write(json.dumps({k: jsonable(v) for k, v in r.items()}) + "\n")
            n += 1
    return n


def extract_log(wh: Warehouse, work) -> None:
    groups = [{k: jsonable(v) for k, v in r.items()} for r in wh.log_groups()]
    write_ndjson(work / "log_groups.ndjson.gz", groups)
    jobs = sum(g["jobs"] for g in groups)
    texts = len({g["query"] for g in groups if g["query"]})
    print(f"log: {jobs:,} jobs -> {len(groups):,} groups, {texts:,} distinct texts")
    n = write_ndjson(work / "principal_profiles.ndjson.gz", wh.principal_profiles())
    print(f"log: {n} principal time profiles")


def build_catalog(physical: dict, rules: list[dict], warehouse: str, dialect: str) -> dict:
    """The connector's physical tables -> the snapshot the parser and the graph use, keyed by canonical name
    (qlsc_parse.catalog.canonical): logical names, shard families (2+ tables sharing a prefix with a date
    suffix) as one wildcard table, volatile identifiers canonicalized (a Looker PDT generation -> LR_{id}_name)."""
    project, aliases = physical["project"], physical["aliases"]
    families = defaultdict(list)
    for ds, name in physical["tables"]:
        head, _, tail = name.rpartition("_")
        if head and SHARD.match(tail):
            families[(ds, head + "_")].append(name)
    shard_families = {
        f"{aliases[f'{project}.{ds}']}.{prefix}"
        for (ds, prefix), names in families.items()
        if len(names) >= 2 and f"{project}.{ds}" in aliases
    }
    compiled = [(re.compile(r["pattern"]), r["replace"]) for r in rules]
    tables = {}
    for (ds, name), t in sorted(physical["tables"].items()):
        if f"{project}.{ds}" not in aliases:
            continue
        fqn = ".".join(canonical(project, ds, name, aliases, compiled, shard_families))
        if fqn.endswith("_*"):
            entry = tables.setdefault(
                fqn, {"kind": "WILDCARD", "columns": {}, "partition": None, "cluster": [], "shards": []}
            )
            entry["columns"].update(t["columns"])
            entry["shards"].append(name)
            continue
        entry = {
            "kind": {"BASE TABLE": "TABLE"}.get(t["type"], t["type"]),
            "columns": t["columns"],
            "partition": t["partition"],
            "cluster": t["cluster"],
        }
        if t.get("view_sql"):
            entry["view_sql"] = t["view_sql"]
        if fqn.rsplit(".", 1)[1] != name:
            entry["physical"] = [name]
            if fqn in tables:
                prev = tables[fqn]
                prev["columns"].update(entry["columns"])
                prev["physical"].append(name)
                continue
        tables[fqn] = entry
    for e in tables.values():
        if e["kind"] == "WILDCARD":
            e["columns"]["_TABLE_SUFFIX"] = "STRING"
            e["shards"].sort()
    body = {
        "rules": rules,
        "aliases": aliases,
        "shard_families": sorted(shard_families),
        "tables": tables,
    }
    version = "cat-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    return {
        "version": version,
        "extracted_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "source": physical["source"],
        "warehouse": warehouse,
        "dialect": dialect,
        **body,
    }


def extract_catalog(wh: Warehouse, s: Settings) -> None:
    cat = build_catalog(wh.catalog(), s.get("canonical_identifiers", []), wh.name, wh.dialect)
    (s.work / "catalog.json").write_text(json.dumps(cat, indent=1))
    tables = cat["tables"]
    print(
        f"catalog {cat['version']}: {len(tables)} tables {dict(Counter(e['kind'] for e in tables.values()))}, "
        f"{sum(len(e['columns']) for e in tables.values()):,} columns, {len(cat['shard_families'])} shard families"
    )


def run(s: Settings, log: bool = True, catalog: bool = True) -> None:
    wh = connect(s)
    if log:
        extract_log(wh, s.work)
    if catalog:
        extract_catalog(wh, s)

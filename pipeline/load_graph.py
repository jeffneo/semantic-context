#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stage 4: load the bottom layer - what the query log and the catalog directly show.

Inputs: work/catalog.json, work/t0_groups.ndjson.gz, work/t0_principals.ndjson.gz,
work/texts.ndjson.gz, work/shapes.ndjson.gz. Target: estate.yaml `neo4j.database`.

Seven labels, nothing inferred:

  (:Project)<-[:IN_PROJECT]-(:Dataset)<-[:IN_DATASET]-(:Table)-[:HAS_COLUMN]->(:Column)
  (:Principal)-[:RAN]->(:QueryShape)        jobs, errors, cache hits, bytes, days, first/last seen
  (:Principal)-[:LOADED]->(:Table)          load jobs (no SQL)
  (:QueryShape)-[:REFERENCES]->(:Table)     with the partition/shard pruning seen for that table
  (:QueryShape)-[:READS]->(:Column)         roles: project/filter/group/join/order/window/unnest, aggregates
  (:QueryShape)-[:FILTERS]->(:Column)       operator, and the literal values it was run with: values,
                                            value_jobs, value_first_seen, value_last_seen (parallel lists)
  (:QueryShape)-[:USES_JOIN]->(:JoinKey)-[:ON {side}]->(:Column)   one JoinKey per join predicate a = b
  (:QueryShape)-[:WRITES]->(:Table)
  (:Column)-[:FLOWS]->(:Column)             column lineage from write statements and view SQL
  (:Column)-[:COMPARED]->(:Column)          two columns compared in one expression (CORR, a - b, a > b)
  (:Table)-[:DERIVED_FROM]->(:Table)        a statement read the one and wrote the other

QueryShape.unresolved lists the names the parser could not place (details: work/PARSE_HEALTH.md).
A shape whose every job failed in BigQuery is loaded as error evidence only (RAN, REFERENCES,
unresolved) - a query that never ran creates no structure.

Usage: uv run pipeline/load_graph.py [--reset]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
ROOT = HERE.parent
MAX_VALUES_PER_FILTER = 50

CONSTRAINTS = ["Project", "Dataset", "Table", "Column", "QueryShape", "Principal", "JoinKey"]


def canonical_table(cat: dict, p: str, d: str, n: str) -> str:
    """Same rules as the parser: physical -> logical dataset, volatile names, shard families."""
    home = cat.get("aliases", {}).get(f"{p}.{d}")
    if home:
        p, d = home.split(".", 1)
    for r in cat.get("rules", []):
        n = re.sub(r["pattern"], r["replace"], n)
    head, _, tail = n.rpartition("_")
    if head and f"{p}.{d}.{head}_" in set(cat.get("shard_families", [])) and (tail.isdigit() or tail.endswith("*")):
        n = head + "_*"
    return f"{p}.{d}.{n}"


def col_id(table: str, column: str, path: str | None = None) -> str:
    return f"{table}.{column}"


def reset(G: Graph):
    G.auto("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS")
    for label in CONSTRAINTS:
        G.run(f"DROP CONSTRAINT {label.lower()}_id IF EXISTS")


def constraints(G: Graph):
    for label in CONSTRAINTS:
        G.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete everything in the target database first")
    a = ap.parse_args()
    cfg = yaml.safe_load((HERE / "estate.yaml").read_text())
    cat = json.loads((WORK / "catalog.json").read_text())
    shapes = [json.loads(l) for l in gzip.open(WORK / "shapes.ndjson.gz", "rt")]
    texts = {t["text_id"]: t for t in (json.loads(l) for l in gzip.open(WORK / "texts.ndjson.gz", "rt"))}
    groups = [json.loads(l) for l in gzip.open(WORK / "t0_groups.ndjson.gz", "rt")]
    t0 = time.perf_counter()

    # ----------------------------------------------------------- catalog
    tables: dict[str, dict] = {}
    columns: dict[str, dict] = {}
    for fqn, t in cat["tables"].items():
        p, d, n = fqn.split(".", 2)
        tables[fqn] = {"id": fqn, "project": p, "dataset": f"{p}.{d}", "name": n, "kind": t["kind"].lower(),
                       "partition_column": t.get("partition"), "cluster_columns": t.get("cluster") or [],
                       "physical_names": t.get("physical") or t.get("shards") or [], "in_catalog": True}
        for c, typ in t["columns"].items():
            columns[col_id(fqn, c)] = {"id": col_id(fqn, c), "name": c, "table": fqn, "type": typ, "in_catalog": True}

    def ensure_table(fqn: str, kind: str):
        if fqn not in tables:
            p, d, n = (fqn.split(".", 2) + ["", ""])[:3]
            tables[fqn] = {"id": fqn, "project": p, "dataset": f"{p}.{d}", "name": n, "kind": kind,
                           "partition_column": None, "cluster_columns": [], "physical_names": [], "in_catalog": False}

    def ensure_column(table: str, column: str) -> str:
        cid = col_id(table, column)
        if cid not in columns:
            ensure_table(table, "transient" if "{" in table else "unknown")
            columns[cid] = {"id": cid, "name": column, "table": table, "type": None, "in_catalog": False}
        return cid

    # ------------------------------------------------------------ shapes
    text_shape = {tid: t["shape_id"] for tid, t in texts.items() if t.get("shape_id")}
    shape_nodes, ran, refs, reads, filt, writes, uses = ([] for _ in range(7))
    flows: dict[tuple, dict] = {}
    compared: dict[tuple, dict] = {}
    derived: dict[tuple, dict] = {}
    joinkeys: dict[str, dict] = {}
    by_id = {s["shape_id"]: s for s in shapes}

    for s in shapes:
        r, st = s["record"], s.get("stats") or {}
        sid = s["shape_id"]
        succeeded = s["origin"] == "catalog_view" or (st.get("jobs", 0) > st.get("errors", 0))
        weeks = sorted((st.get("weeks") or {}).items())
        shape_nodes.append({
            "id": sid, "origin": s["origin"], "statement_type": r.get("statement_type"), "status": r["status"],
            "succeeded": succeeded, "jobs": st.get("jobs", 0), "errors": st.get("errors", 0),
            "cache_hits": st.get("cache_hits", 0), "texts": st.get("texts", 0),
            "bytes_billed": st.get("bytes_billed", 0), "bytes_processed": st.get("bytes_processed", 0),
            "slot_ms": st.get("slot_ms", 0), "first_seen": st.get("first_seen"), "last_seen": st.get("last_seen"),
            "weeks": [w for w, _ in weeks], "week_jobs": [n for _, n in weeks],
            "week_bytes": [(st.get("week_bytes") or {}).get(w, 0) for w, _ in weeks],
            "family_id": r.get("family_id"),
            "output_columns": (r.get("output") or {}).get("columns"),
            "output_aggregate_only": (r.get("output") or {}).get("aggregate_only"),
            "output_grouped": (r.get("output") or {}).get("grouped"),
            "root_from": (r.get("output") or {}).get("root_from"),
            "error_reasons": json.dumps(st.get("error_reasons") or {}), "sample_sql": s["sample_sql"],
            "select_star": bool(r.get("scan", {}).get("select_star")), "limit": r.get("scan", {}).get("limit"),
            "parser": r.get("parser"), "catalog": r.get("catalog"),
            "annotations": json.dumps((texts.get(s["sample_text_id"]) or {}).get("annotations") or []),
            "unresolved": sorted({f"{u['kind']}:{u['name']} ({u['reason']})" for u in r.get("unresolved", [])}),
        })
        pf = r.get("scan", {}).get("partition_filter") or {}
        for t in r.get("tables", []):
            if t["kind"] == "unknown" and not succeeded:
                continue            # an unknown name in a failed query is not a Table: it stays in QueryShape.unresolved
            ensure_table(t["id"], t["kind"])
            refs.append({"shape": sid, "table": t["id"], "kind": t["kind"], "partition_filter": pf.get(t["id"])})
        if not succeeded:
            continue
        for x in r.get("reads", []):
            cid = ensure_column(x["table"], x["column"])
            reads.append({"shape": sid, "col": cid, "path": x["path"], "roles": x["roles"],
                          "derived_roles": x["derived_roles"], "agg": x["agg"]})
        for i, f in enumerate(r.get("filters", [])):
            cid = ensure_column(f["table"], f["column"])
            filt.append({"shape": sid, "i": i, "col": cid, "path": f["path"], "op": f["op"], "clause": f["clause"],
                         "scope": f["scope"], "wrap": f["wrap"]})
        for j in r.get("joins", []):
            sides = []
            for side in (j["left"], j["right"]):
                cid = ensure_column(side["table"], side["column"])
                sides.append((cid + (f"#{side['path']}" if side["path"] else ""), cid, side))
            (ka, a_, L), (kb, b_, R) = sorted(sides, key=lambda x: x[0])
            key = f"{ka}={kb}"
            joinkeys[key] = {"id": key, "left": a_, "right": b_, "left_path": L["path"], "right_path": R["path"]}
            uses.append({"shape": sid, "key": key, "type": j["type"], "left_wrap": L["wrap"], "right_wrap": R["wrap"],
                         "left_via": L["via"], "right_via": R["via"], "scopes": j["scopes"]})
        for c in r.get("comparisons", []):
            a_ = ensure_column(c["left"]["table"], c["left"]["column"])
            b_ = ensure_column(c["right"]["table"], c["right"]["column"])
            e = compared.setdefault((a_, b_), {"a": a_, "b": b_, "ops": set(), "shapes": set()})
            e["ops"].update(c["ops"])
            e["shapes"].add(sid)
        for w in r.get("writes", []):
            ensure_table(w["table"], "table")
            writes.append({"shape": sid, "table": w["table"], "mode": w["mode"],
                           "merge_keys": [k["target"] for k in w.get("merge_keys", [])]})
            srcs = set()
            for c in w["columns"]:
                tgt = ensure_column(w["table"], c["target"])
                for f in c["from"]:
                    src = ensure_column(f["table"], f["column"])
                    srcs.add(f["table"])
                    e = flows.setdefault((src, tgt), {"src": src, "tgt": tgt, "kinds": set(), "fns": set(),
                                                      "paths": set(), "shapes": set(), "jobs": 0, "control": True})
                    e["control"] &= bool(f.get("control"))     # only steers the value, in every statement
                    e["kinds"].add(c["kind"])
                    e["fns"].update(c["fn"])
                    if f.get("path"):
                        e["paths"].add(f["path"])
                    e["shapes"].add(sid)
                    e["jobs"] += st.get("jobs", 0)
            # tables read by the statement feed the written table, even without column lineage
            srcs |= {t["id"] for t in r.get("tables", []) if t["id"] != w["table"] and t["kind"] != "system"}
            for src in srcs:
                d = derived.setdefault((w["table"], src), {"tgt": w["table"], "src": src, "modes": set(),
                                                           "shapes": set(), "jobs": 0})
                d["modes"].add(w["mode"])
                d["shapes"].add(sid)
                d["jobs"] += st.get("jobs", 0)

    # principals: RAN and LOADED, straight from the T0 groups
    ran_agg: dict[tuple, dict] = {}
    loaded: dict[tuple, dict] = {}
    write_days: dict[str, set] = defaultdict(set)
    shape_writes = defaultdict(list)
    for w in writes:
        if by_id[w["shape"]]["record"].get("statement_type") != "CREATE_VIEW":
            shape_writes[w["shape"]].append(w["table"])
    principals = {}
    aliases = cat.get("aliases", {})
    profiles = {}
    if (WORK / "t0_principals.ndjson.gz").exists():
        for line in gzip.open(WORK / "t0_principals.ndjson.gz", "rt"):
            r = json.loads(line)
            profiles[r["user_email"]] = {
                "active_days": r["active_days"], "total_jobs": r["jobs"],
                "weekend_share": r["weekend_jobs"] / r["jobs"], "business_hours_share": r["business_hours_jobs"] / r["jobs"],
                "recurring_slot_share": r["recurring_slot_share"], "distinct_slots": r["distinct_slots"],
                "daily_cv": r["daily_cv"], "first_job": r["first_job"], "last_job": r["last_job"]}
    for g in groups:
        email = g["user_email"]
        principals[email] = {"id": email, "kind": "service_account" if email.endswith("gserviceaccount.com")
                             else "user", "domain": email.split("@")[-1], **profiles.get(email, {})}
        if g["job_type"] == "LOAD":
            dest = g.get("destination_table")
            if not dest:
                continue
            dest = canonical_table(cat, *dest.split(".", 2))
            ensure_table(dest, "table")
            e = loaded.setdefault((email, dest), {"principal": email, "table": dest, "jobs": 0, "errors": 0,
                                                  "first_seen": g["first_seen"], "last_seen": g["last_seen"],
                                                  "days": set()})
            e["days"].update(g["days"] or [])
            write_days[dest].update(g["days"] or [])
            e["jobs"] += g["jobs"]
            e["errors"] += g["errors"]
            e["first_seen"], e["last_seen"] = min(e["first_seen"], g["first_seen"]), max(e["last_seen"], g["last_seen"])
            continue
        sid = text_shape.get(hashlib.sha1(g["query"].encode()).hexdigest()) if g["query"] else None
        if sid is None or sid not in by_id:
            continue
        e = ran_agg.setdefault((email, sid), {"principal": email, "shape": sid, "jobs": 0, "errors": 0,
                                              "cache_hits": 0, "bytes_billed": 0, "days": set(),
                                              "first_seen": g["first_seen"], "last_seen": g["last_seen"]})
        if g["jobs"] > g["errors"]:
            e["days"].update(g["days"] or [])
            for tgt in shape_writes.get(sid, ()):
                write_days[tgt].update(g["days"] or [])
        for k in ("jobs", "errors", "cache_hits", "bytes_billed"):
            e[k] += g[k] or 0
        e["first_seen"], e["last_seen"] = min(e["first_seen"], g["first_seen"]), max(e["last_seen"], g["last_seen"])

    # literal values per filtered column, with first/last seen - from every text of every shape
    text_stats: dict[str, dict] = {}
    for g in groups:
        if not g["query"]:
            continue
        tid = hashlib.sha1(g["query"].encode()).hexdigest()
        t = text_stats.setdefault(tid, {"jobs": 0, "ok": 0, "first": g["first_seen"], "last": g["last_seen"]})
        t["jobs"] += g["jobs"]
        t["ok"] += g["jobs"] - g["errors"]
        t["first"], t["last"] = min(t["first"], g["first_seen"]), max(t["last"], g["last_seen"])
    texts_of: dict[str, list[str]] = defaultdict(list)
    for tid, sid in text_shape.items():
        texts_of[sid].append(tid)
    values: dict[tuple, dict] = {}          # (shape, filter index) -> value -> stats
    for s in shapes:
        if s["origin"] != "log":
            continue
        fs = [(i, f) for i, f in enumerate(s["record"].get("filters", [])) if f.get("slots")]
        if not fs:
            continue
        for tid in texts_of[s["shape_id"]]:
            ts = text_stats.get(tid)
            lits = texts[tid].get("literals") or []
            if not ts or ts["ok"] == 0:
                continue
            for i, f in fs:
                for slot in f["slots"]:
                    if slot >= len(lits):
                        continue
                    for v in (lits[slot] if isinstance(lits[slot], list) else [lits[slot]]):
                        per = values.setdefault((s["shape_id"], i), {})
                        e = per.setdefault(str(v), {"jobs": 0, "first": ts["first"], "last": ts["last"]})
                        e["jobs"] += ts["ok"]
                        e["first"], e["last"] = min(e["first"], ts["first"]), max(e["last"], ts["last"])
    for f in filt:
        vs = sorted((values.get((f["shape"], f.pop("i"))) or {}).items(), key=lambda x: -x[1]["jobs"])[:MAX_VALUES_PER_FILTER]
        f["values"] = [v for v, _ in vs]
        f["value_jobs"] = [e["jobs"] for _, e in vs]
        f["value_first_seen"] = [e["first"] for _, e in vs]
        f["value_last_seen"] = [e["last"] for _, e in vs]

    # ----------------------------------------------------------- write
    G = Graph(cfg)
    if a.reset:
        reset(G)
    constraints(G)
    datasets = {t["dataset"]: {"id": t["dataset"], "project": t["project"], "name": t["dataset"].split(".", 1)[-1]}
                for t in tables.values()}
    G.batch("Project", "UNWIND $rows AS r MERGE (:Project {id: r})", sorted({t["project"] for t in tables.values()}))
    G.batch("Dataset", """UNWIND $rows AS r MERGE (d:Dataset {id: r.id}) SET d.name = r.name
                          WITH d, r MATCH (p:Project {id: r.project}) MERGE (d)-[:IN_PROJECT]->(p)""", list(datasets.values()))
    G.batch("Table", """UNWIND $rows AS r MERGE (t:Table {id: r.id})
                        SET t += r {.name, .kind, .partition_column, .cluster_columns, .physical_names, .in_catalog}
                        WITH t, r MATCH (d:Dataset {id: r.dataset}) MERGE (t)-[:IN_DATASET]->(d)""", list(tables.values()))
    G.batch("Column", """UNWIND $rows AS r MERGE (c:Column {id: r.id}) SET c += r {.name, .type, .in_catalog}
                         WITH c, r MATCH (t:Table {id: r.table}) MERGE (t)-[:HAS_COLUMN]->(c)""", list(columns.values()))
    G.batch("QueryShape", "UNWIND $rows AS r MERGE (s:QueryShape {id: r.id}) SET s += r", shape_nodes, 1000)
    G.batch("Principal", "UNWIND $rows AS r MERGE (p:Principal {id: r.id}) SET p += r", list(principals.values()))
    G.batch("RAN", """UNWIND $rows AS r MATCH (p:Principal {id: r.principal}), (s:QueryShape {id: r.shape})
                      MERGE (p)-[x:RAN]->(s) SET x += r {.jobs, .errors, .cache_hits, .bytes_billed, .first_seen, .last_seen,
                      .days}""", [{**e, "days": sorted(e["days"])} for e in ran_agg.values()])
    G.batch("LOADED", """UNWIND $rows AS r MATCH (p:Principal {id: r.principal}), (t:Table {id: r.table})
                         MERGE (p)-[x:LOADED]->(t) SET x += r {.jobs, .errors, .first_seen, .last_seen, .days}""",
            [{**e, "days": sorted(e["days"])} for e in loaded.values()])
    G.batch("Table.write_days", "UNWIND $rows AS r MATCH (t:Table {id: r.id}) SET t.write_days = r.days",
            [{"id": t, "days": sorted(d)} for t, d in write_days.items()])
    G.batch("REFERENCES", """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (t:Table {id: r.table})
                             MERGE (s)-[x:REFERENCES]->(t) SET x.kind = r.kind, x.partition_filter = r.partition_filter""", refs)
    G.batch("READS", """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (c:Column {id: r.col})
                        CREATE (s)-[:READS {path: r.path, roles: r.roles, derived_roles: r.derived_roles, agg: r.agg}]->(c)""", reads)
    G.batch("FILTERS", """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (c:Column {id: r.col})
                          CREATE (s)-[:FILTERS {path: r.path, op: r.op, clause: r.clause, scope: r.scope, wrap: r.wrap,
                                  values: r.values, value_jobs: r.value_jobs, value_first_seen: r.value_first_seen,
                                  value_last_seen: r.value_last_seen}]->(c)""", filt)
    G.batch("JoinKey", """UNWIND $rows AS r MERGE (k:JoinKey {id: r.id})
                          WITH k, r MATCH (a:Column {id: r.left}), (b:Column {id: r.right})
                          MERGE (k)-[:ON {side: 'left', path: coalesce(r.left_path, '')}]->(a)
                          MERGE (k)-[:ON {side: 'right', path: coalesce(r.right_path, '')}]->(b)""", list(joinkeys.values()))
    G.batch("USES_JOIN", """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (k:JoinKey {id: r.key})
                            CREATE (s)-[:USES_JOIN {type: r.type, left_wrap: r.left_wrap, right_wrap: r.right_wrap,
                                    left_via: r.left_via, right_via: r.right_via, scopes: r.scopes}]->(k)""", uses)
    G.batch("WRITES", """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (t:Table {id: r.table})
                         MERGE (s)-[x:WRITES]->(t) SET x.mode = r.mode, x.merge_keys = r.merge_keys""", writes)
    G.batch("FLOWS", """UNWIND $rows AS r MATCH (a:Column {id: r.src}), (b:Column {id: r.tgt})
                        MERGE (a)-[x:FLOWS]->(b) SET x.kinds = r.kinds, x.fns = r.fns, x.paths = r.paths,
                        x.shapes = r.shapes, x.jobs = r.jobs, x.control = r.control""",
            [{**e, "kinds": sorted(e["kinds"]), "fns": sorted(e["fns"]), "paths": sorted(e["paths"]),
              "shapes": sorted(e["shapes"])} for e in flows.values()])
    G.batch("COMPARED", """UNWIND $rows AS r MATCH (a:Column {id: r.a}), (b:Column {id: r.b})
                           MERGE (a)-[x:COMPARED]->(b) SET x.ops = r.ops, x.shapes = r.shapes""",
            [{**e, "ops": sorted(e["ops"]), "shapes": sorted(e["shapes"])} for e in compared.values()])
    G.batch("DERIVED_FROM", """UNWIND $rows AS r MATCH (a:Table {id: r.tgt}), (b:Table {id: r.src})
                               MERGE (a)-[x:DERIVED_FROM]->(b) SET x.modes = r.modes, x.shapes = r.shapes, x.jobs = r.jobs""",
            [{**d, "modes": sorted(d["modes"]), "shapes": sorted(d["shapes"])} for d in derived.values()])
    res = G.run("MATCH (n) RETURN count(n) AS n").records[0]["n"], \
        G.run("MATCH ()-[r]->() RETURN count(r) AS n").records[0]["n"]
    print(f"loaded into {G.db} in {time.perf_counter() - t0:.1f}s: {res[0]:,} nodes, {res[1]:,} relationships")
    for k, v in G.counts.items():
        print(f"  {k:14} {v:,}")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

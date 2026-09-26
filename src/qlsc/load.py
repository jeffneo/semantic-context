"""Load: the bottom layer - what the query log and the catalog directly show, nothing inferred.

Inputs: <work>/catalog.json, log_groups.ndjson.gz, principal_profiles.ndjson.gz, texts.ndjson.gz,
shapes.ndjson.gz. Target: the config's `neo4j.database`. Seven labels:

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

QueryShape.unresolved lists the names the parser could not place (details: PARSE_HEALTH.md). A shape
whose every job failed is loaded as error evidence only (RAN, REFERENCES, unresolved): a query that
never ran creates no structure.
"""

from __future__ import annotations

import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.names import canonical_table, text_id
from qlsc.warehouse import connect
from qlsc_parse.catalog import Catalog

LABELS = ["Project", "Dataset", "Table", "Column", "QueryShape", "Principal", "JoinKey"]


def ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in gzip.open(path, "rt")] if path.exists() else []


class Assets:
    """Tables and columns: the catalog's, plus any the log names that the catalog lacks."""

    def __init__(self, cat: dict):
        self.tables: dict[str, dict] = {}
        self.columns: dict[str, dict] = {}
        for fqn, t in cat["tables"].items():
            p, d, n = fqn.split(".", 2)
            self.tables[fqn] = {
                "id": fqn,
                "project": p,
                "dataset": f"{p}.{d}",
                "name": n,
                "kind": t["kind"].lower(),
                "partition_column": t.get("partition"),
                "cluster_columns": t.get("cluster") or [],
                "physical_names": t.get("physical") or t.get("shards") or [],
                "in_catalog": True,
            }
            for c, typ in t["columns"].items():
                cid = f"{fqn}.{c}"
                self.columns[cid] = {"id": cid, "name": c, "table": fqn, "type": typ, "in_catalog": True}

    def table(self, fqn: str, kind: str) -> str:
        if fqn not in self.tables:
            p, d, n = (fqn.split(".", 2) + ["", ""])[:3]
            self.tables[fqn] = {
                "id": fqn,
                "project": p,
                "dataset": f"{p}.{d}",
                "name": n,
                "kind": kind,
                "partition_column": None,
                "cluster_columns": [],
                "physical_names": [],
                "in_catalog": False,
            }
        return fqn

    def column(self, table: str, column: str) -> str:
        cid = f"{table}.{column}"
        if cid not in self.columns:
            self.table(table, "transient" if "{" in table else "unknown")
            self.columns[cid] = {"id": cid, "name": column, "table": table, "type": None, "in_catalog": False}
        return cid


def succeeded(shape: dict) -> bool:
    st = shape.get("stats") or {}
    return shape["origin"] == "catalog_view" or st.get("jobs", 0) > st.get("errors", 0)


def shape_node(s: dict, texts: dict) -> dict:
    r, st = s["record"], s.get("stats") or {}
    out = r.get("output") or {}
    weeks = sorted((st.get("weeks") or {}).items())
    return {
        "id": s["shape_id"],
        "origin": s["origin"],
        "statement_type": r.get("statement_type"),
        "status": r["status"],
        "succeeded": succeeded(s),
        "jobs": st.get("jobs", 0),
        "errors": st.get("errors", 0),
        "cache_hits": st.get("cache_hits", 0),
        "texts": st.get("texts", 0),
        "bytes_billed": st.get("bytes_billed", 0),
        "bytes_processed": st.get("bytes_processed", 0),
        "slot_ms": st.get("slot_ms", 0),
        "first_seen": st.get("first_seen"),
        "last_seen": st.get("last_seen"),
        "weeks": [w for w, _ in weeks],
        "week_jobs": [n for _, n in weeks],
        "week_bytes": [(st.get("week_bytes") or {}).get(w, 0) for w, _ in weeks],
        "family_id": r.get("family_id"),
        "output_columns": out.get("columns"),
        "output_aggregate_only": out.get("aggregate_only"),
        "output_grouped": out.get("grouped"),
        "root_from": out.get("root_from"),
        "error_reasons": json.dumps(st.get("error_reasons") or {}),
        "sample_sql": s["sample_sql"],
        "select_star": bool(r.get("scan", {}).get("select_star")),
        "limit": r.get("scan", {}).get("limit"),
        "parser": r.get("parser"),
        "catalog": r.get("catalog"),
        "annotations": json.dumps((texts.get(s["sample_text_id"]) or {}).get("annotations") or []),
        "unresolved": sorted({f"{u['kind']}:{u['name']} ({u['reason']})" for u in r.get("unresolved", [])}),
    }


class Evidence:
    """What each shape's parse record says: references, reads, filters, joins, comparisons, writes, lineage."""

    def __init__(self):
        self.shapes, self.refs, self.reads, self.filters, self.writes, self.uses = ([] for _ in range(6))
        self.joinkeys: dict[str, dict] = {}
        self.flows: dict[tuple, dict] = {}
        self.compared: dict[tuple, dict] = {}
        self.derived: dict[tuple, dict] = {}

    def add(self, s: dict, texts: dict, assets: Assets) -> None:
        r, sid, jobs = s["record"], s["shape_id"], (s.get("stats") or {}).get("jobs", 0)
        ok = succeeded(s)
        self.shapes.append(shape_node(s, texts))
        pruning = r.get("scan", {}).get("partition_filter") or {}
        for t in r.get("tables", []):
            if t["kind"] == "unknown" and not ok:
                continue  # an unknown name in a failed query is not a Table: it stays in QueryShape.unresolved
            assets.table(t["id"], t["kind"])
            self.refs.append(
                {"shape": sid, "table": t["id"], "kind": t["kind"], "partition_filter": pruning.get(t["id"])}
            )
        if not ok:
            return
        for x in r.get("reads", []):
            self.reads.append(
                {
                    "shape": sid,
                    "col": assets.column(x["table"], x["column"]),
                    "path": x["path"],
                    "roles": x["roles"],
                    "derived_roles": x["derived_roles"],
                    "agg": x["agg"],
                }
            )
        for i, f in enumerate(r.get("filters", [])):
            self.filters.append(
                {
                    "shape": sid,
                    "i": i,
                    "col": assets.column(f["table"], f["column"]),
                    "path": f["path"],
                    "op": f["op"],
                    "clause": f["clause"],
                    "scope": f["scope"],
                    "wrap": f["wrap"],
                }
            )
        for j in r.get("joins", []):
            self._join(sid, j, assets)
        for c in r.get("comparisons", []):
            a = assets.column(c["left"]["table"], c["left"]["column"])
            b = assets.column(c["right"]["table"], c["right"]["column"])
            e = self.compared.setdefault((a, b), {"a": a, "b": b, "ops": set(), "shapes": set()})
            e["ops"].update(c["ops"])
            e["shapes"].add(sid)
        for w in r.get("writes", []):
            self._write(sid, jobs, w, r, assets)

    def _join(self, sid: str, j: dict, assets: Assets) -> None:
        sides = []
        for side in (j["left"], j["right"]):
            cid = assets.column(side["table"], side["column"])
            sides.append((cid + (f"#{side['path']}" if side["path"] else ""), cid, side))
        (ka, a, left), (kb, b, right) = sorted(sides, key=lambda x: x[0])
        key = f"{ka}={kb}"
        self.joinkeys[key] = {
            "id": key,
            "left": a,
            "right": b,
            "left_path": left["path"],
            "right_path": right["path"],
        }
        self.uses.append(
            {
                "shape": sid,
                "key": key,
                "type": j["type"],
                "left_wrap": left["wrap"],
                "right_wrap": right["wrap"],
                "left_via": left["via"],
                "right_via": right["via"],
                "scopes": j["scopes"],
            }
        )

    def _write(self, sid: str, jobs: int, w: dict, r: dict, assets: Assets) -> None:
        assets.table(w["table"], "table")
        self.writes.append(
            {
                "shape": sid,
                "table": w["table"],
                "mode": w["mode"],
                "merge_keys": [k["target"] for k in w.get("merge_keys", [])],
            }
        )
        sources = set()
        for c in w["columns"]:
            tgt = assets.column(w["table"], c["target"])
            for f in c["from"]:
                src = assets.column(f["table"], f["column"])
                sources.add(f["table"])
                e = self.flows.setdefault(
                    (src, tgt),
                    {
                        "src": src,
                        "tgt": tgt,
                        "kinds": set(),
                        "fns": set(),
                        "paths": set(),
                        "shapes": set(),
                        "jobs": 0,
                        "control": True,
                    },
                )
                e["control"] &= bool(f.get("control"))  # only steers the value, in every statement
                e["kinds"].add(c["kind"])
                e["fns"].update(c["fn"])
                if f.get("path"):
                    e["paths"].add(f["path"])
                e["shapes"].add(sid)
                e["jobs"] += jobs
        # tables read by the statement feed the written table, even without column lineage
        sources |= {t["id"] for t in r.get("tables", []) if t["id"] != w["table"] and t["kind"] != "system"}
        for src in sources:
            d = self.derived.setdefault(
                (w["table"], src), {"tgt": w["table"], "src": src, "modes": set(), "shapes": set(), "jobs": 0}
            )
            d["modes"].add(w["mode"])
            d["shapes"].add(sid)
            d["jobs"] += jobs


def principals(
    groups, profiles, shapes_by_id, text_shape, ev: Evidence, cat: Catalog, assets: Assets, is_service_account
) -> tuple[dict, dict, dict, dict]:
    """Principals, what each ran (RAN) and loaded (LOADED), and the days each table was written."""
    ran: dict[tuple, dict] = {}
    loaded: dict[tuple, dict] = {}
    write_days: dict[str, set] = defaultdict(set)
    shape_writes = defaultdict(list)
    for w in ev.writes:
        if shapes_by_id[w["shape"]]["record"].get("statement_type") != "CREATE_VIEW":
            shape_writes[w["shape"]].append(w["table"])
    people = {}
    for g in groups:
        email = g["user_email"]
        people[email] = {
            "id": email,
            "kind": "service_account" if is_service_account(email) else "user",
            "domain": email.split("@")[-1],
            **profiles.get(email, {}),
        }
        if g["job_type"] == "LOAD":
            if not g.get("destination_table"):
                continue
            dest = assets.table(canonical_table(cat, g["destination_table"]), "table")
            e = loaded.setdefault(
                (email, dest),
                {
                    "principal": email,
                    "table": dest,
                    "jobs": 0,
                    "errors": 0,
                    "first_seen": g["first_seen"],
                    "last_seen": g["last_seen"],
                    "days": set(),
                },
            )
            e["days"].update(g["days"] or [])
            write_days[dest].update(g["days"] or [])
            e["jobs"] += g["jobs"]
            e["errors"] += g["errors"]
            e["first_seen"], e["last_seen"] = (
                min(e["first_seen"], g["first_seen"]),
                max(e["last_seen"], g["last_seen"]),
            )
            continue
        sid = text_shape.get(text_id(g["query"])) if g["query"] else None
        if sid is None or sid not in shapes_by_id:
            continue
        e = ran.setdefault(
            (email, sid),
            {
                "principal": email,
                "shape": sid,
                "jobs": 0,
                "errors": 0,
                "cache_hits": 0,
                "bytes_billed": 0,
                "days": set(),
                "first_seen": g["first_seen"],
                "last_seen": g["last_seen"],
            },
        )
        if g["jobs"] > g["errors"]:
            e["days"].update(g["days"] or [])
            for tgt in shape_writes.get(sid, ()):
                write_days[tgt].update(g["days"] or [])
        for k in ("jobs", "errors", "cache_hits", "bytes_billed"):
            e[k] += g[k] or 0
        e["first_seen"], e["last_seen"] = (
            min(e["first_seen"], g["first_seen"]),
            max(e["last_seen"], g["last_seen"]),
        )
    return people, ran, loaded, write_days


def profile(r: dict) -> dict:
    return {
        "active_days": r["active_days"],
        "total_jobs": r["jobs"],
        "weekend_share": r["weekend_jobs"] / r["jobs"],
        "business_hours_share": r["business_hours_jobs"] / r["jobs"],
        "recurring_slot_share": r["recurring_slot_share"],
        "distinct_slots": r["distinct_slots"],
        "daily_cv": r["daily_cv"],
        "first_job": r["first_job"],
        "last_job": r["last_job"],
    }


def filter_values(
    ev: Evidence, shapes: list[dict], groups: list[dict], texts: dict, text_shape: dict, limit: int
) -> None:
    """The literal values each FILTERS edge was run with, from every text of its shape, most-run first."""
    text_stats: dict[str, dict] = {}
    for g in groups:
        if not g["query"]:
            continue
        t = text_stats.setdefault(
            text_id(g["query"]), {"jobs": 0, "ok": 0, "first": g["first_seen"], "last": g["last_seen"]}
        )
        t["jobs"] += g["jobs"]
        t["ok"] += g["jobs"] - g["errors"]
        t["first"], t["last"] = min(t["first"], g["first_seen"]), max(t["last"], g["last_seen"])
    texts_of: dict[str, list[str]] = defaultdict(list)
    for tid, sid in text_shape.items():
        texts_of[sid].append(tid)
    values: dict[tuple, dict] = {}  # (shape, filter index) -> value -> stats
    for s in shapes:
        if s["origin"] != "log":
            continue
        fs = [(i, f) for i, f in enumerate(s["record"].get("filters", [])) if f.get("slots")]
        for tid in texts_of[s["shape_id"]] if fs else ():
            ts = text_stats.get(tid)
            lits = texts[tid].get("literals") or []
            if not ts or ts["ok"] == 0:
                continue
            for i, f in fs:
                for slot in f["slots"]:
                    if slot >= len(lits):
                        continue
                    for v in lits[slot] if isinstance(lits[slot], list) else [lits[slot]]:
                        e = values.setdefault((s["shape_id"], i), {}).setdefault(
                            str(v), {"jobs": 0, "first": ts["first"], "last": ts["last"]}
                        )
                        e["jobs"] += ts["ok"]
                        e["first"], e["last"] = min(e["first"], ts["first"]), max(e["last"], ts["last"])
    for f in ev.filters:
        vs = sorted((values.get((f["shape"], f.pop("i"))) or {}).items(), key=lambda x: -x[1]["jobs"])[:limit]
        f["values"] = [v for v, _ in vs]
        f["value_jobs"] = [e["jobs"] for _, e in vs]
        f["value_first_seen"] = [e["first"] for _, e in vs]
        f["value_last_seen"] = [e["last"] for _, e in vs]


def sets(d: dict, *keys) -> dict:
    return {**d, **{k: sorted(d[k]) for k in keys}}


def write(
    G: Graph, assets: Assets, people: dict, ev: Evidence, ran: dict, loaded: dict, write_days: dict
) -> None:
    tables = assets.tables.values()
    datasets = {
        t["dataset"]: {"id": t["dataset"], "project": t["project"], "name": t["dataset"].split(".", 1)[-1]}
        for t in tables
    }
    G.batch("Project", "UNWIND $rows AS r MERGE (:Project {id: r})", sorted({t["project"] for t in tables}))
    G.batch(
        "Dataset",
        """UNWIND $rows AS r MERGE (d:Dataset {id: r.id}) SET d.name = r.name
                          WITH d, r MATCH (p:Project {id: r.project}) MERGE (d)-[:IN_PROJECT]->(p)""",
        list(datasets.values()),
    )
    G.batch(
        "Table",
        """UNWIND $rows AS r MERGE (t:Table {id: r.id})
                        SET t += r {.name, .kind, .partition_column, .cluster_columns, .physical_names, .in_catalog}
                        WITH t, r MATCH (d:Dataset {id: r.dataset}) MERGE (t)-[:IN_DATASET]->(d)""",
        list(tables),
    )
    G.batch(
        "Column",
        """UNWIND $rows AS r MERGE (c:Column {id: r.id}) SET c += r {.name, .type, .in_catalog}
                         WITH c, r MATCH (t:Table {id: r.table}) MERGE (t)-[:HAS_COLUMN]->(c)""",
        list(assets.columns.values()),
    )
    G.batch("QueryShape", "UNWIND $rows AS r MERGE (s:QueryShape {id: r.id}) SET s += r", ev.shapes, 1000)
    G.batch("Principal", "UNWIND $rows AS r MERGE (p:Principal {id: r.id}) SET p += r", list(people.values()))
    G.batch(
        "RAN",
        """UNWIND $rows AS r MATCH (p:Principal {id: r.principal}), (s:QueryShape {id: r.shape})
                      MERGE (p)-[x:RAN]->(s)
                      SET x += r {.jobs, .errors, .cache_hits, .bytes_billed, .first_seen, .last_seen, .days}""",
        [sets(e, "days") for e in ran.values()],
    )
    G.batch(
        "LOADED",
        """UNWIND $rows AS r MATCH (p:Principal {id: r.principal}), (t:Table {id: r.table})
                         MERGE (p)-[x:LOADED]->(t) SET x += r {.jobs, .errors, .first_seen, .last_seen, .days}""",
        [sets(e, "days") for e in loaded.values()],
    )
    G.batch(
        "Table.write_days",
        "UNWIND $rows AS r MATCH (t:Table {id: r.id}) SET t.write_days = r.days",
        [{"id": t, "days": sorted(d)} for t, d in write_days.items()],
    )
    G.batch(
        "REFERENCES",
        """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (t:Table {id: r.table})
                             MERGE (s)-[x:REFERENCES]->(t) SET x.kind = r.kind, x.partition_filter = r.partition_filter""",
        ev.refs,
    )
    G.batch(
        "READS",
        """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (c:Column {id: r.col})
                        CREATE (s)-[:READS {path: r.path, roles: r.roles, derived_roles: r.derived_roles, agg: r.agg}]->(c)""",
        ev.reads,
    )
    G.batch(
        "FILTERS",
        """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (c:Column {id: r.col})
                          CREATE (s)-[:FILTERS {path: r.path, op: r.op, clause: r.clause, scope: r.scope, wrap: r.wrap,
                                  values: r.values, value_jobs: r.value_jobs, value_first_seen: r.value_first_seen,
                                  value_last_seen: r.value_last_seen}]->(c)""",
        ev.filters,
    )
    G.batch(
        "JoinKey",
        """UNWIND $rows AS r MERGE (k:JoinKey {id: r.id})
                          WITH k, r MATCH (a:Column {id: r.left}), (b:Column {id: r.right})
                          MERGE (k)-[:ON {side: 'left', path: coalesce(r.left_path, '')}]->(a)
                          MERGE (k)-[:ON {side: 'right', path: coalesce(r.right_path, '')}]->(b)""",
        list(ev.joinkeys.values()),
    )
    G.batch(
        "USES_JOIN",
        """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (k:JoinKey {id: r.key})
                            CREATE (s)-[:USES_JOIN {type: r.type, left_wrap: r.left_wrap, right_wrap: r.right_wrap,
                                    left_via: r.left_via, right_via: r.right_via, scopes: r.scopes}]->(k)""",
        ev.uses,
    )
    G.batch(
        "WRITES",
        """UNWIND $rows AS r MATCH (s:QueryShape {id: r.shape}), (t:Table {id: r.table})
                         MERGE (s)-[x:WRITES]->(t) SET x.mode = r.mode, x.merge_keys = r.merge_keys""",
        ev.writes,
    )
    G.batch(
        "FLOWS",
        """UNWIND $rows AS r MATCH (a:Column {id: r.src}), (b:Column {id: r.tgt})
                        MERGE (a)-[x:FLOWS]->(b) SET x.kinds = r.kinds, x.fns = r.fns, x.paths = r.paths,
                        x.shapes = r.shapes, x.jobs = r.jobs, x.control = r.control""",
        [sets(e, "kinds", "fns", "paths", "shapes") for e in ev.flows.values()],
    )
    G.batch(
        "COMPARED",
        """UNWIND $rows AS r MATCH (a:Column {id: r.a}), (b:Column {id: r.b})
                           MERGE (a)-[x:COMPARED]->(b) SET x.ops = r.ops, x.shapes = r.shapes""",
        [sets(e, "ops", "shapes") for e in ev.compared.values()],
    )
    G.batch(
        "DERIVED_FROM",
        """UNWIND $rows AS r MATCH (a:Table {id: r.tgt}), (b:Table {id: r.src})
                               MERGE (a)-[x:DERIVED_FROM]->(b) SET x.modes = r.modes, x.shapes = r.shapes, x.jobs = r.jobs""",
        [sets(d, "modes", "shapes") for d in ev.derived.values()],
    )


def reset(G: Graph) -> None:
    G.delete("(n)", 10000)
    for label in LABELS:
        G.run(f"DROP CONSTRAINT {label.lower()}_id IF EXISTS")


def run(s: Settings, reset_graph: bool = False) -> None:
    work = s.work
    t0 = time.perf_counter()
    cat_data = json.loads((work / "catalog.json").read_text())
    cat = Catalog(cat_data)
    shapes = ndjson(work / "shapes.ndjson.gz")
    texts = {t["text_id"]: t for t in ndjson(work / "texts.ndjson.gz")}
    groups = ndjson(work / "log_groups.ndjson.gz")
    profiles = {r["user_email"]: profile(r) for r in ndjson(work / "principal_profiles.ndjson.gz")}
    text_shape = {tid: t["shape_id"] for tid, t in texts.items() if t.get("shape_id")}

    assets, ev = Assets(cat_data), Evidence()
    for shape in shapes:
        ev.add(shape, texts, assets)
    people, ran, loaded, write_days = principals(
        groups,
        profiles,
        {x["shape_id"]: x for x in shapes},
        text_shape,
        ev,
        cat,
        assets,
        connect(s).is_service_account,
    )
    filter_values(ev, shapes, groups, texts, text_shape, s.params["load"]["max_values_per_filter"])

    with Graph(s) as G:
        if reset_graph:
            reset(G)
        for label in LABELS:
            G.run(
                f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
        write(G, assets, people, ev, ran, loaded, write_days)
        nodes, rels = G.value("MATCH (n) RETURN count(n)"), G.value("MATCH ()-[r]->() RETURN count(r)")
        print(
            f"loaded into {G.db} in {time.perf_counter() - t0:.1f}s: {nodes:,} nodes, {rels:,} relationships"
        )
        for k, v in G.counts.items():
            print(f"  {k:16} {v:,}")

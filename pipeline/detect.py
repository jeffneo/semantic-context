#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stage 5e: lifecycle and cost findings, from usage statistics on the evidence graph.

Needs Stage 3 (actors.py): consumption excludes probes and monitors, so a table read
only by health checks counts as unused, and the monitor's breadth does not keep dead
tables alive (F19).

Every finding becomes (:Finding {kind, title, summary, cost_bytes, evidence})-[:ABOUT {role}]->(...)
and a section of work/FINDINGS.md:

  monitor             principals whose reads are almost all single-row checks, and what they touch
  dead                no consumption and no writes in the window; also stale generations of a table
  write_only          written in the window, consumed by nobody - with the write cost
  straggler           a writer stopped mid-window while readers carried on - with the stop date
  superseded_live     a pipeline table rebuilt in parallel with a broader-used one from the same
                      sources, whose downstream chain still reaches live consumers
  unpruned_scan       consumption of partitioned/sharded data with no pruning filter - the filter
                      it used instead, and what it cost
  star_limit          SELECT * ... LIMIT by people: LIMIT prunes nothing
  probe_cost          health checks and cache triggers that scan data
  incremental_rescan  incremental builds whose source is not pruned, and whose bytes per run grow
  literal_drift       a new value appearing mid-window in the filters on an established column

Usage: uv run pipeline/detect.py
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
CONSUMPTION = ["adhoc", "bi", "extract", "ml_read", "build"]
GIB = 2 ** 30
DATE_LIKE = re.compile(r"^-?\d+(\.\d+)?$|^\d{4}-\d{2}-\d{2}|^\d{6,8}$")
# period labels are expected to be new each period: APR-26, 2026-Q2, FY26, 202605
PERIOD_LIKE = re.compile(r"(?i)^(?:(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[-_ ]?\d{2,4}|"
                         r"\d{4}[-_ ]?Q[1-4]|Q[1-4][-_ ]?\d{2,4}|FY\d{2,4}|\d{4}[-_]?\d{2})$")


def day(ts: str | None) -> dt.date | None:
    return dt.date.fromisoformat(ts[:10]) if ts else None


def gib(b) -> str:
    return f"{(b or 0) / GIB:,.1f} GiB"


class Findings:
    def __init__(self):
        self.items = []

    def add(self, kind, fid, title, summary, about, cost_bytes=0, evidence=None):
        if any(f["id"] == f"{kind}:{fid}" for f in self.items):
            return
        self.items.append({"id": f"{kind}:{fid}", "kind": kind, "title": title, "summary": summary,
                           "cost_bytes": int(cost_bytes or 0), "evidence": json.dumps(evidence or {}, default=str),
                           "about": about})


def main() -> int:
    G = Graph()
    G.auto("MATCH (f:Finding) CALL (f) { DETACH DELETE f } IN TRANSACTIONS OF 5000 ROWS")
    F = Findings()

    win = G.rows("MATCH ()-[r:RAN]->() RETURN min(r.first_seen) AS a, max(r.last_seen) AS b")[0]
    w0, w1 = day(win["a"]), day(win["b"])
    tables = {r["t"]["id"]: r["t"] for r in G.rows("MATCH (t:Table) RETURN t {.*} AS t")}
    pclass = {r["id"]: r["cls"] for r in G.rows("MATCH (p:Principal) RETURN p.id AS id, p.class AS cls")}
    shapes = {r["s"]["id"]: r["s"] for r in G.rows("""MATCH (s:QueryShape) RETURN s {.id, .purpose, .statement_type,
        .jobs, .errors, .bytes_billed, .weeks, .week_jobs, .week_bytes, .select_star, .limit, .sample_sql,
        .succeeded, .output_aggregate_only} AS s""")}
    refs = G.rows("MATCH (s:QueryShape)-[r:REFERENCES]->(t:Table) RETURN s.id AS s, t.id AS t, r.partition_filter AS pf")
    ran = G.rows("""MATCH (p:Principal)-[r:RAN]->(s:QueryShape) RETURN p.id AS p, s.id AS s, r.jobs AS jobs,
                    r.errors AS errors, r.first_seen AS first, r.last_seen AS last, r.bytes_billed AS bytes""")
    writes = G.rows("MATCH (s:QueryShape)-[w:WRITES]->(t:Table) RETURN s.id AS s, t.id AS t, w.mode AS mode")
    loads = G.rows("""MATCH (p:Principal)-[l:LOADED]->(t:Table) RETURN p.id AS p, t.id AS t, l.jobs AS jobs,
                      l.first_seen AS first, l.last_seen AS last""")
    views = defaultdict(set)      # view -> direct sources
    for r in G.rows("""MATCH (v:Table {kind: 'view'})-[d:DERIVED_FROM]->(src:Table) WHERE 'VIEW' IN d.modes
                       RETURN v.id AS v, src.id AS s"""):
        views[r["v"]].add(r["s"])
    derived = defaultdict(set)    # table -> tables it is built from (non-view builds)
    for r in G.rows("""MATCH (a:Table)-[d:DERIVED_FROM]->(b:Table) RETURN a.id AS a, b.id AS b, d.modes AS modes"""):
        derived[r["a"]].add(r["b"])
    runs_of = defaultdict(list)
    for r in ran:
        runs_of[r["s"]].append(r)

    def expand(t, seen=()):
        """A read of a view reads its sources, all the way down."""
        out = {t}
        for s in views.get(t, ()):
            if s not in seen:
                out |= expand(s, seen + (t,))
        return out

    # ---------------------------------------------------------- table usage
    U = defaultdict(lambda: {"consumed_jobs": 0, "consumers": set(), "last_consumed": None, "probe_jobs": 0,
                             "probers": set(), "written_jobs": 0, "writers": set(), "first_written": None,
                             "last_written": None, "write_bytes": 0, "consumer_after": defaultdict(str)})
    for r in refs:
        s = shapes[r["s"]]
        if not s["succeeded"]:
            continue
        for t in expand(r["t"]):
            for run in runs_of[r["s"]]:
                ok = (run["jobs"] or 0) - (run["errors"] or 0)
                if ok <= 0:
                    continue
                u = U[t]
                if s["purpose"] in CONSUMPTION and not (s["purpose"] == "build" and any(
                        w["s"] == r["s"] and w["t"] == t for w in writes)):
                    u["consumed_jobs"] += ok
                    u["consumers"].add(run["p"])
                    u["last_consumed"] = max(filter(None, [u["last_consumed"], run["last"]]))
                    u["consumer_after"][run["p"]] = max(u["consumer_after"][run["p"]], run["last"] or "")
                elif s["purpose"] == "probe":
                    u["probe_jobs"] += ok
                    u["probers"].add(run["p"])
    for w in writes:
        s = shapes[w["s"]]
        if not s["succeeded"] or s["purpose"] not in ("build", "ingest"):
            continue
        for run in runs_of[w["s"]]:
            u = U[w["t"]]
            u["written_jobs"] += run["jobs"] - (run["errors"] or 0)
            u["writers"].add(run["p"])
            u["write_bytes"] += run["bytes"] or 0
            u["first_written"] = min(filter(None, [u["first_written"], run["first"]]))
            u["last_written"] = max(filter(None, [u["last_written"], run["last"]]))
    for l in loads:
        u = U[l["t"]]
        u["written_jobs"] += l["jobs"]
        u["writers"].add(l["p"])
        u["first_written"] = min(filter(None, [u["first_written"], l["first"]]))
        u["last_written"] = max(filter(None, [u["last_written"], l["last"]]))

    G.batch("Table.usage", """UNWIND $rows AS r MATCH (t:Table {id: r.id}) SET t += r.u""",
            [{"id": t, "u": {"consumed_jobs": u["consumed_jobs"], "consumer_count": len(u["consumers"]),
                             "last_consumed": u["last_consumed"], "probe_jobs": u["probe_jobs"],
                             "written_jobs": u["written_jobs"], "writer_count": len(u["writers"]),
                             "first_written": u["first_written"], "last_written": u["last_written"],
                             "write_bytes": u["write_bytes"]}}
             for t, u in U.items() if t in tables])

    # -------------------------------------------------------------- monitor
    for r in G.rows("""MATCH (p:Principal {class: 'monitor'})-[r:RAN]->(s:QueryShape)
                       OPTIONAL MATCH (s)-[:REFERENCES]->(t:Table)
                       WITH p, sum(r.jobs) AS jobs, count(DISTINCT s) AS shapes, count(DISTINCT s.family_id) AS families,
                            count(DISTINCT t) AS tables
                       MATCH (:Principal)-[all:RAN]->() WITH p, jobs, shapes, families, tables, sum(all.jobs) AS total
                       RETURN p.id AS p, jobs, shapes, families, tables, total, p.class_evidence AS ev"""):
        kept = [t for t, u in U.items() if u["probe_jobs"] and not u["consumed_jobs"] and not u["written_jobs"]]
        F.add("monitor", r["p"], f"Monitoring traffic: {r['p'].split('@')[0]}",
              f"{r['jobs']:,} jobs ({r['jobs'] / r['total']:.1%} of all), {r['shapes']} shapes in {r['families']} "
              f"families over {r['tables']} tables. Excluded from consumption; without that exclusion "
              f"{len(kept)} otherwise-unused tables would look alive.",
              [{"id": r["p"], "label": "Principal", "role": "monitor"}] +
              [{"id": t, "label": "Table", "role": "kept_alive"} for t in kept],
              evidence={"families": r["families"], "tables": r["tables"], "kept_alive": kept})

    # ------------------------------------------------------ dead, write-only
    for t, meta in tables.items():
        if not meta.get("in_catalog"):
            continue
        u = U.get(t) or U[t]
        if u["consumed_jobs"] == 0 and u["written_jobs"] == 0:
            probed = sorted(u["probers"])
            F.add("dead", t, f"Unused: {t.split('.', 1)[1]}",
                  "No consumption and no writes in the window" +
                  (f"; only health checks read it ({', '.join(p.split('@')[0] for p in probed)}, "
                   f"{u['probe_jobs']:,} jobs)" if probed else "; nothing reads it at all") + ".",
                  [{"id": t, "label": "Table", "role": "subject"}],
                  evidence={"probe_jobs": u["probe_jobs"], "probers": probed, "kind": meta["kind"]})
        elif u["consumed_jobs"] == 0 and u["written_jobs"] > 0:
            F.add("write_only", t, f"Written, never read: {t.split('.', 1)[1]}",
                  f"{u['written_jobs']:,} writes by {', '.join(sorted(p.split('@')[0] for p in u['writers']))}"
                  f" ({gib(u['write_bytes'])} billed); no consumption"
                  + (f" beyond {u['probe_jobs']:,} health-check reads" if u["probe_jobs"] else "") + ".",
                  [{"id": t, "label": "Table", "role": "subject"}], cost_bytes=u["write_bytes"],
                  evidence={"writers": sorted(u["writers"]), "written_jobs": u["written_jobs"]})

    # stale generations: one logical table, several physical tables; which ones are still used?
    multi = {t: m for t, m in tables.items() if len(m.get("physical_names") or []) > 1 and "*" not in t}
    if multi:
        text_shape = {}
        for line in gzip.open(WORK / "texts.ndjson.gz", "rt"):
            x = json.loads(line)
            text_shape[x["text_id"]] = x["shape_id"]
        seen = defaultdict(set)
        for line in gzip.open(WORK / "t0_groups.ndjson.gz", "rt"):
            g = json.loads(line)
            if not g["query"] or g["jobs"] <= g["errors"]:
                continue
            sid = text_shape.get(hashlib.sha1(g["query"].encode()).hexdigest())
            if sid not in shapes or shapes[sid]["purpose"] not in CONSUMPTION + ["build"]:
                continue
            for t, m in multi.items():
                for ph in m["physical_names"]:
                    if ph in g["query"]:
                        seen[t].add(ph)
        for t, m in multi.items():
            for ph in m["physical_names"]:
                if ph not in seen[t]:
                    phys = ".".join(t.split(".")[:2] + [ph])
                    F.add("dead", phys, f"Stale generation: {ph}",
                          f"One of {len(m['physical_names'])} physical tables behind {t.split('.', 2)[2]}; "
                          f"no statement in the window reads or writes this one "
                          f"(in use: {', '.join(sorted(seen[t])) or 'none'}).",
                          [{"id": t, "label": "Table", "role": "logical"}],
                          evidence={"physical": phys, "in_use": sorted(seen[t])})

    # -------------------------------------------------------------- straggler
    # A table written on a cadence that went quiet for well past its usual interval, while
    # consumers kept reading it. One-off writes (a sandbox CTAS, then weeks of reads) are
    # not stragglers; a monthly refresh is not stopped two weeks after it last ran.
    wdays = {t: sorted(day(d) for d in (m.get("write_days") or [])) for t, m in tables.items()}
    ran_days = defaultdict(set)      # (principal, table) -> consumption days, views expanded
    probe_days = defaultdict(set)
    for r in G.rows("""MATCH (p:Principal)-[x:RAN]->(s:QueryShape)-[:REFERENCES]->(t:Table)
                       WHERE s.succeeded RETURN p.id AS p, s.id AS s, t.id AS t, x.days AS days"""):
        purpose = shapes[r["s"]]["purpose"]
        for t in expand(r["t"]):
            if purpose in CONSUMPTION and not any(w["s"] == r["s"] and w["t"] == t for w in writes):
                ran_days[(r["p"], t)].update(day(d) for d in r["days"] or [])
            elif purpose == "probe":
                probe_days[(r["p"], t)].update(day(d) for d in r["days"] or [])

    def stopped(t):
        d = wdays.get(t) or []
        if len(d) < 4:
            return None
        gaps = sorted((b - a).days for a, b in zip(d, d[1:]))
        typical = gaps[len(gaps) // 2]
        return d[-1] if (w1 - d[-1]).days > max(7, 3 * typical) else None

    stops = {t: stopped(t) for t in tables}
    stops = {t: d for t, d in stops.items() if d}
    first_written = {t: d[0] for t, d in wdays.items() if d}
    for t, lw in stops.items():
        after = {p: max(ds) for (p, tt), ds in ran_days.items() if tt == t and ds and max(ds) > lw + dt.timedelta(days=1)}
        n_after = {p: len([x for x in ran_days[(p, t)] if x > lw]) for p in after}
        checks = {p: len([x for x in ds if x > lw]) for (p, tt), ds in probe_days.items() if tt == t and ds and max(ds) > lw}
        if not after:
            continue
        cols = {c["c"] for c in G.rows("MATCH (:Table {id: $t})-[:HAS_COLUMN]->(c) RETURN c.name AS c", t=t)}
        succ = []
        for t2, fw in first_written.items():
            if t2 != t and abs((fw - lw).days) <= 2 and fw > w0 + dt.timedelta(days=2):
                c2 = {c["c"] for c in G.rows("MATCH (:Table {id: $t})-[:HAS_COLUMN]->(c) RETURN c.name AS c", t=t2)}
                succ.append((len(cols & c2) / max(len(cols), 1), t2))
        succ = [t2 for o, t2 in sorted(succ, reverse=True) if o >= 0.3][:2]
        cause = sorted(x for x in derived.get(t, ()) if x in stops and abs((stops[x] - lw).days) <= 2)
        name = lambda x: x.split(".", 1)[1]
        F.add("straggler", t, f"Writer stopped, readers did not: {name(t)}",
              f"Written on {len(wdays[t])} days, last on {lw} ({', '.join(sorted(p.split('@')[0] for p in U[t]['writers']))}). "
              f"Still consumed after that by "
              + ", ".join(f"{p.split('@')[0]} ({n_after[p]} days, until {d})" for p, d in sorted(after.items()))
              + (f"; health checks kept polling it too ({', '.join(f'{p.split(chr(64))[0]}: {n} days' for p, n in checks.items())})"
                 if checks else "")
              + (f". It stopped because its source stopped: {', '.join(f'{name(x)} (last written {stops[x]})' for x in cause)}"
                 if cause else "")
              + (f". Likely successor: {', '.join(name(x) for x in succ)} (first written {first_written[succ[0]]})"
                 if succ else "") + ".",
              [{"id": t, "label": "Table", "role": "subject"}] + [{"id": x, "label": "Table", "role": "successor"} for x in succ]
              + [{"id": x, "label": "Table", "role": "stopped_source"} for x in cause]
              + [{"id": p, "label": "Principal", "role": "reader_after_stop"} for p in after],
              evidence={"last_written": str(lw), "write_days": len(wdays[t]),
                        "readers_after": {p: str(d) for p, d in after.items()}, "successors": succ,
                        "stopped_sources": cause, "checks_after": checks})

    # ---------------------------------------------------------- superseded_live
    flows_up = defaultdict(set)
    for r in G.rows("MATCH (a:Column)-[:FLOWS]->(b:Column) RETURN a.id AS a, b.id AS b"):
        flows_up[r["b"]].add(r["a"])
    tcols = defaultdict(set)
    for r in G.rows("MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) RETURN t.id AS t, c.id AS c"):
        tcols[r["t"]].add(r["c"])

    def roots(col, seen=()):
        if not flows_up.get(col):
            return {col}
        out = set()
        for up in flows_up[col]:
            if up not in seen:
                out |= roots(up, seen + (col,))
        return out

    def upstream(t, seen=()):
        out = set()
        for s in derived.get(t, ()):
            if s not in seen:
                out |= {s} | upstream(s, seen + (t,))
        return out

    def downstream_of(t):
        out, frontier = set(), {t}
        while frontier:
            nxt = {a for a, bs in derived.items() for b in bs if b in frontier and a not in out and a != t}
            out |= nxt
            frontier = nxt
        return out

    built = {t for t, u in U.items() if u["written_jobs"] and t in tables and tables[t]["kind"] == "table"
             and all(pclass.get(p) == "transformation" for p in u["writers"])}
    R = {t: {r for c in tcols[t] for r in roots(c)} - tcols[t] for t in built}
    audience = {t: len({p for x in {t} | downstream_of(t) for p in U[x]["consumers"]
                        if pclass.get(p) != "transformation"} | {p for p in U[t]["consumers"]}) for t in built}
    seen_pairs, cands = set(), []
    for a in built:
        for b in built:
            if a >= b or not R[a] or not R[b] or U[a]["writers"] == U[b]["writers"]:
                continue
            if b in upstream(a) or a in upstream(b):
                continue
            small, big = (a, b) if audience[a] <= audience[b] else (b, a)
            overlap = len(R[small] & R[big]) / len(R[small])
            src_small = {c.rsplit(".", 1)[0] for c in R[small]}
            if overlap < 0.6 or (small, big) in seen_pairs:
                continue
            seen_pairs.add((small, big))
            chain = sorted(downstream_of(small))
            ends = {p for x in [small] + chain for p in U[x]["consumers"] if pclass.get(p) != "transformation"}
            if not ends:
                continue
            cands.append((small, big, overlap, src_small, chain, ends))
    flagged = {(c[0], c[1]) for c in cands}
    for small, big, overlap, src_small, chain, ends in cands:
        if any(o != small and (o, big) in flagged and small in downstream_of(o) for o, _ in flagged):
            continue            # already part of the chain of an upstream candidate
        if True:
            F.add("superseded_live", small, f"Parallel legacy pipeline still feeding reports: {small.split('.', 1)[1]}",
                  f"Rebuilt by {', '.join(sorted(p.split('@')[0] for p in U[small]['writers']))} from the same sources "
                  f"as {big.split('.', 1)[1]} ({overlap:.0%} of its source columns; {', '.join(sorted(x.split('.', 1)[1] for x in src_small))}), "
                  f"which {audience[big]} principals use against its {audience[small]}. Its chain "
                  f"{' -> '.join([small.split('.', 1)[1]] + [x.split('.', 1)[1] for x in chain])} still reaches "
                  f"{', '.join(sorted(p.split('@')[0] + ' (' + str(pclass.get(p)) + ')' for p in ends))}.",
                  [{"id": small, "label": "Table", "role": "subject"}, {"id": big, "label": "Table", "role": "replacement"}]
                  + [{"id": x, "label": "Table", "role": "downstream"} for x in chain]
                  + [{"id": p, "label": "Principal", "role": "consumer"} for p in ends],
                  evidence={"overlap": overlap, "chain": chain, "consumers": sorted(ends)})

    # ------------------------------------------------------------ scan costs
    part_col = {t: ("_TABLE_SUFFIX" if m["kind"] == "wildcard" else m.get("partition_column")) for t, m in tables.items()}
    filt = defaultdict(set)
    for r in G.rows("""MATCH (s:QueryShape)-[f:FILTERS]->(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       RETURN s.id AS s, t.id AS t, c.name AS c, c.id AS cid"""):
        filt[(r["s"], r["t"])].add(r["c"])
        filt[(r["s"], "*cols")].add(r["cid"])
    view_def_pushed = {r["v"] for r in G.rows("""MATCH (s:QueryShape)-[w:WRITES]->(v:Table {kind: 'view'}),
        (s)-[r:REFERENCES]->(:Table) WHERE r.partition_filter = 'pushed' RETURN DISTINCT v.id AS v""")}
    passthrough_from = defaultdict(set)   # view column -> base columns it passes through unchanged
    for r in G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column)
                       WHERE all(k IN f.kinds WHERE k IN ['passthrough', 'rename']) RETURN a.id AS a, b.id AS b"""):
        passthrough_from[r["b"]].add(r["a"])

    def unpruned(sid, t, pf):
        """(table actually scanned without pruning, filter used instead) for one reference."""
        if pf == "none" and part_col.get(t):
            return [(t, sorted(filt[(sid, t)]))]
        if pf == "view" and t not in view_def_pushed:
            out = []
            for base in expand(t) - {t}:
                pc = part_col.get(base)
                if not pc or tables.get(base, {}).get("kind") == "view":
                    continue
                pcid = f"{base}.{pc}"
                ok = any(pcid in passthrough_from.get(c, set()) for c in filt[(sid, "*cols")])
                if not ok:
                    out.append((base, sorted(filt[(sid, t)])))
            return out
        return []

    scans = defaultdict(lambda: {"bytes": 0, "jobs": 0, "shapes": set(), "principals": set(), "instead": Counter(),
                                 "via": set()})
    probes = defaultdict(lambda: {"bytes": 0, "jobs": 0, "shapes": set(), "principals": set()})
    rescans = []
    by_shape_refs = defaultdict(list)
    for r in refs:
        by_shape_refs[r["s"]].append(r)
    for sid, rs in by_shape_refs.items():
        s = shapes[sid]
        if not s["succeeded"]:
            continue
        hits = [(r["t"], base, instead) for r in rs for base, instead in unpruned(sid, r["t"], r["pf"])]
        if not hits:
            continue
        share = (s["bytes_billed"] or 0) / len(hits)
        who = {r["p"] for r in runs_of[sid]}
        consumer_build = s["purpose"] == "build" and who and all(pclass.get(p) in ("human", "bi_service") for p in who)
        for via, base, instead in hits:
            if s["purpose"] in ("adhoc", "bi", "extract", "ml_read") or consumer_build:
                x = scans[base]
                x["bytes"] += share
                x["jobs"] += s["jobs"]
                x["shapes"].add(sid)
                x["principals"] |= who
                x["instead"].update(instead)
                if via != base:
                    x["via"].add(via)
            elif s["purpose"] == "probe":
                x = probes[base]
                x["bytes"] += share
                x["jobs"] += s["jobs"]
                x["shapes"].add(sid)
                x["principals"] |= who
        if s["purpose"] == "build" and s["statement_type"] in ("MERGE", "INSERT"):
            wb, wj = s.get("week_bytes") or [], s.get("week_jobs") or []
            per = [b / j for b, j in zip(wb, wj) if j]
            growth = (sum(per[-3:]) / 3) / (sum(per[:3]) / 3) if len(per) >= 6 and sum(per[:3]) else None
            targets = [w["t"] for w in writes if w["s"] == sid]
            has_time_filter = bool(filt[(sid, "*cols")])
            rescans.append((sid, targets, [h[1] for h in hits], [h[0] for h in hits], growth, has_time_filter))

    total_scan = sum(x["bytes"] for x in scans.values())
    for base, x in sorted(scans.items(), key=lambda kv: -kv[1]["bytes"]):
        # reading every shard of a sharded table is always worth naming; partitioned ones by cost
        if x["bytes"] < min(100 * GIB, 0.005 * total_scan) and tables[base]["kind"] != "wildcard":
            continue
        pc = part_col[base]
        instead = [c for c, _ in x["instead"].most_common(3) if c != pc]
        F.add("unpruned_scan", base, f"Unpruned scans of {base.split('.', 1)[1]}",
              f"{x['jobs']:,} jobs in {len(x['shapes'])} shapes by {len(x['principals'])} principals read it with no "
              f"{pc} filter" + (f" (through {', '.join(v.split('.', 1)[1] for v in sorted(x['via']))}, which cannot pass "
                                f"a pruning filter down)" if x["via"] else "")
              + (f"; they filter on {', '.join(instead)} instead" if instead else "") + f". {gib(x['bytes'])} billed.",
              [{"id": base, "label": "Table", "role": "subject"}] + [{"id": v, "label": "Table", "role": "via"} for v in x["via"]]
              + [{"id": s_, "label": "QueryShape", "role": "example"} for s_ in sorted(x["shapes"], key=lambda k: -(shapes[k]["bytes_billed"] or 0))[:5]],
              cost_bytes=x["bytes"], evidence={"missing": pc, "instead": instead, "principals": sorted(x["principals"])})
    total_probe = sum(x["bytes"] for x in probes.values())
    for base, x in sorted(probes.items(), key=lambda kv: -kv[1]["bytes"]):
        if x["bytes"] < 0.01 * total_probe:
            continue
        F.add("probe_cost", base, f"Health checks scanning {base.split('.', 1)[1]}",
              f"{x['jobs']:,} single-row checks by {', '.join(sorted(p.split('@')[0] for p in x['principals']))} scan it "
              f"with no {part_col[base]} filter: {gib(x['bytes'])} billed. A partition filter, or table metadata "
              f"(INFORMATION_SCHEMA.PARTITIONS / last_modified_time), answers the same question for almost nothing.",
              [{"id": base, "label": "Table", "role": "subject"}] + [{"id": p, "label": "Principal", "role": "checker"}
                                                                     for p in x["principals"]],
              cost_bytes=x["bytes"], evidence={"principals": sorted(x["principals"])})
    for sid, targets, bases, vias, growth, tf in rescans:
        s = shapes[sid]
        if not (tf or (growth and growth > 1.05)):
            continue
        for t in targets:
            F.add("incremental_rescan", t, f"Incremental build rescans its source: {t.split('.', 1)[1]}",
                  f"{s['jobs']:,} runs, {gib(s['bytes_billed'])} billed. Its source "
                  f"{', '.join(sorted({b.split('.', 1)[1] for b in bases}))} is read with no pruning"
                  + (" although the statement filters on a date - the filter is applied after the scan" if tf else "")
                  + (f"; bytes per run grew {growth:.2f}x over the window" if growth else "") + ".",
                  [{"id": t, "label": "Table", "role": "subject"}, {"id": sid, "label": "QueryShape", "role": "statement"}]
                  + [{"id": b, "label": "Table", "role": "source"} for b in set(bases)],
                  cost_bytes=s["bytes_billed"], evidence={"growth": growth, "sources": sorted(set(bases))})
    for r in G.rows("""MATCH (s:QueryShape {purpose: 'adhoc', select_star: true})-[:REFERENCES]->(t:Table)
                       WHERE s.limit IS NOT NULL AND s.succeeded
                       RETURN t.id AS t, collect(s.id) AS shapes, sum(s.jobs) AS jobs, sum(s.bytes_billed) AS bytes
                       ORDER BY bytes DESC"""):
        if (r["bytes"] or 0) < GIB:
            continue
        F.add("star_limit", r["t"], f"SELECT * ... LIMIT on {r['t'].split('.', 1)[1]}",
              f"{r['jobs']:,} ad-hoc jobs select every column with a LIMIT: {gib(r['bytes'])} billed. LIMIT does not "
              f"reduce what BigQuery scans; the table preview is free, and a column list or partition filter is not.",
              [{"id": r["t"], "label": "Table", "role": "subject"}] +
              [{"id": s_, "label": "QueryShape", "role": "example"} for s_ in r["shapes"][:5]], cost_bytes=r["bytes"])

    # ---------------------------------------------------------- literal drift
    for r in G.rows("""MATCH (c:Column)-[v:HAS_VALUE]->(l:Literal)
                       WHERE c.type STARTS WITH 'STRING' AND v.op IN ['=', 'IN']
                       WITH c, collect({value: l.value, first: v.first_seen, jobs: v.jobs, texts: v.texts}) AS vals
                       WHERE size(vals) >= 2 RETURN c.id AS c, vals"""):
        early = [v for v in r["vals"] if day(v["first"]) <= w0 + dt.timedelta(days=7)]
        if not early:
            continue
        for v in r["vals"]:
            fs = day(v["first"])
            if (fs > w0 + dt.timedelta(days=21) and v["jobs"] >= 10 and not DATE_LIKE.match(v["value"])
                    and not PERIOD_LIKE.match(v["value"])):
                F.add("literal_drift", f"{r['c']}={v['value']}", f"New value in filters: {r['c'].split('.', 1)[1]} = '{v['value']}'",
                      f"First filtered on {fs}, {(fs - w0).days} days into the window; {v['jobs']:,} jobs since. "
                      f"Before that, queries on this column used {', '.join(repr(e['value']) for e in early[:4])}. "
                      f"A new code usually means the source changed; queries on only one of the codes miscount "
                      f"the other period.",
                      [{"id": r["c"], "label": "Column", "role": "subject"}],
                      evidence={"value": v["value"], "first_seen": str(fs), "jobs": v["jobs"],
                                "earlier": [e["value"] for e in early]})

    # -------------------------------------------------------------- write
    G.batch("Finding", """UNWIND $rows AS r
        CREATE (f:Finding {id: r.id, kind: r.kind, title: r.title, summary: r.summary, cost_bytes: r.cost_bytes,
                           evidence: r.evidence})""", [{k: v for k, v in f.items() if k != "about"} for f in F.items])
    about = [{"f": f["id"], "id": a["id"], "role": a["role"], "label": a["label"]} for f in F.items for a in f["about"]]
    for label in ("Table", "Column", "Principal", "QueryShape"):
        G.batch(f"ABOUT {label}", f"""UNWIND $rows AS r MATCH (f:Finding {{id: r.f}}), (x:{label} {{id: r.id}})
            MERGE (f)-[a:ABOUT]->(x) SET a.role = r.role""", [a for a in about if a["label"] == label])
    report(F, w0, w1)
    by = Counter(f["kind"] for f in F.items)
    print(f"window {w0}..{w1}: {len(F.items)} findings {dict(by)} -> {WORK / 'FINDINGS.md'}")
    G.close()
    return 0


ORDER = ["monitor", "dead", "write_only", "straggler", "superseded_live", "unpruned_scan", "star_limit", "probe_cost",
         "incremental_rescan", "literal_drift"]


def report(F: Findings, w0, w1):
    L = ["# Lifecycle and cost findings", "", f"Window {w0} to {w1}. Generated by pipeline/detect.py from the evidence "
         "graph; consumption excludes health checks and monitors.", ""]
    for kind in ORDER:
        items = [f for f in F.items if f["kind"] == kind]
        if not items:
            continue
        items.sort(key=lambda f: -f["cost_bytes"])
        L += [f"## {kind} ({len(items)})", ""]
        for f in items:
            L.append(f"- **{f['title']}**. {f['summary']}")
        L.append("")
    (WORK / "FINDINGS.md").write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stage 7a: guidance - which tables to use, which to avoid, and why.

Everything here is a reading of evidence earlier stages put in the graph; nothing new
is inferred. Each table gets:

  status          current | caution | avoid
  status_reasons  the evidence, one sentence each (a finding, its layer, its freshness)
  freshness       how current it is, from writes in the log
  (:Table)-[:USE_INSTEAD {why}]->(:Table)
                  only where the evidence names the alternative: a superseded pipeline's
                  replacement, a stopped writer's successor, a copy's original, the mart
                  production builds from a raw feed

Freshness: a table no job wrote in the window is either frozen or fed outside BigQuery
jobs (CDC streams, the Storage Write API). The log tells them apart by dependence: if
production builds keep reading it (directly or through a view) in the window's last two
weeks, it is live; if not, nothing depends on it being current and it is frozen.

For exploring (Bloom, pipeline/views/), joins are summarised table to table:
  (:Table)-[:JOINS {on, confidence, suspect, shapes}]->(:Table)
from the column-level JoinKeys, which stay the evidence.

Usage: uv run pipeline/guide.py      (writes work/GUIDE.md)
"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
PRODUCTION = ("dbt", "looker", "tableau", "service")
RANK = {"current": 0, "caution": 1, "avoid": 2}


def short(x: str) -> str:
    return x.split(".", 1)[1] if x.count(".") >= 2 else x


def main() -> int:
    G = Graph()
    G.run("MATCH ()-[r:USE_INSTEAD|JOINS]->() DELETE r")
    end = dt.date.fromisoformat(G.rows("MATCH ()-[r:RAN]->() RETURN max(r.last_seen) AS b")[0]["b"][:10])
    recent = (end - dt.timedelta(days=14)).isoformat()
    T = {r["t"]["id"]: r["t"] for r in G.rows("""MATCH (t:Table)-[:IN_DATASET]->(d:Dataset) WHERE t.in_catalog
        RETURN t {.id, .kind, .layer, .last_written, .first_written, .write_days, .consumer_count, .consumed_jobs,
                  .last_consumed, restricted: d.restricted} AS t""")}
    status = {t: "current" for t in T}
    reasons = defaultdict(list)
    instead = {}                     # (table, alternative) -> why

    def mark(t, level, why, alt=None, alt_why=None):
        if t not in T:
            return
        if RANK[level] > RANK[status[t]]:
            status[t] = level
        if why not in reasons[t]:
            reasons[t].append(why)
        if alt and alt in T and alt != t:
            instead.setdefault((t, alt), alt_why or why)

    # ---------------------------------------------------------- freshness
    views = defaultdict(set)
    for r in G.rows("""MATCH (v:Table {kind: 'view'})-[d:DERIVED_FROM]->(s:Table) WHERE 'VIEW' IN d.modes
                       RETURN v.id AS v, s.id AS s"""):
        views[r["v"]].add(r["s"])
    prod_read = {r["t"] for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table)
        WHERE split(s.author, ':')[0] IN $prod AND s.purpose IN ['build', 'bi', 'extract', 'ml_read'] AND s.last_seen >= $recent
        RETURN DISTINCT t.id AS t""", prod=list(PRODUCTION), recent=recent)}
    stack = list(prod_read)
    while stack:
        for s in views.get(stack.pop(), ()):
            if s not in prod_read:
                prod_read.add(s)
                stack.append(s)
    fresh = {}
    for t, m in T.items():
        if m["kind"] == "view":
            fresh[t] = "a view: as current as the tables it reads"
        elif m.get("last_written"):
            lw = m["last_written"][:10]
            days = len(m.get("write_days") or [])
            fresh[t] = f"written on {days} day(s) in the window, last {lw}"
            if (end - dt.date.fromisoformat(lw)).days > 7:
                fresh[t] += f" ({(end - dt.date.fromisoformat(lw)).days} days before the window ends)"
        elif t in prod_read:
            fresh[t] = ("no write jobs in the log, but production builds read it every day: fed outside BigQuery "
                        "jobs (a CDC stream or the Storage Write API), so live")
        else:
            fresh[t] = "no writes in the window and no production process reads it: frozen"
            if m.get("consumer_count"):         # unread ones are reported as unused
                mark(t, "avoid", "Frozen: nothing wrote it in the window and no production process depends on it"
                     + (f"; still read by {m['consumer_count']} principal(s), last {m['last_consumed'][:10]}"
                        if m.get("last_consumed") else "") + ".")

    # ---------------------------------------------------------- findings
    F = G.rows("""MATCH (f:Finding)-[a:ABOUT]->(x) RETURN f.id AS id, f.kind AS kind, f.title AS title,
                  f.summary AS summary, f.evidence AS ev, a.role AS role, x.id AS x, labels(x)[0] AS label""")
    by = defaultdict(list)
    for r in F:
        by[r["id"]].append(r)
    for fid, rows in by.items():
        kind = rows[0]["kind"]
        ev = json.loads(rows[0]["ev"] or "{}")
        role = defaultdict(list)
        for r in rows:
            role[r["role"]].append(r["x"])
        if kind == "dead":
            for t in role["subject"]:
                mark(t, "avoid", "Unused: nothing consumed or wrote it in the window" +
                     (" (only health checks read it)." if ev.get("probe_jobs") else "."))
        elif kind == "write_only":
            for t in role["subject"]:
                mark(t, "caution", "Written, but nothing reads it: no one relies on its contents.")
        elif kind == "superseded_live":
            alt = (role["replacement"] or [None])[0]
            for t in role["subject"] + role["downstream"]:
                mark(t, "avoid", f"Deprecated pipeline: rebuilt in parallel with {short(alt)}, which most of the business "
                     f"uses; this chain is kept alive only by its remaining readers.", alt,
                     "the pipeline this legacy chain duplicates, used by most of the business")
        elif kind == "straggler":
            alt = (role["successor"] or [None])[0]
            for t in role["subject"]:
                mark(t, "avoid", f"Its writer stopped on {ev.get('last_written')}; readers continued on stale data"
                     + (f"; likely successor {short(alt)}." if alt else "."), alt, "first written the day after this one stopped")
        elif kind == "copy_chain":
            orig = (role["consolidate_into"] or [None])[0]
            for t in role["copy"]:
                mark(t, "avoid", f"A copy of {short(orig)} made by a person or BI tool; the original is what production "
                     "maintains.", orig, "the original this copy was made from")
        elif kind == "suspect_join":
            for t in role["built_by_it"]:
                mark(t, "avoid", f"Built with a join production contradicts ({rows[0]['title']}); its results are "
                     "likely wrong or empty.")
        elif kind == "unit_mismatch":
            for c in role["subject"]:
                t = c.rsplit(".", 1)[0]
                mark(t, "avoid", f"{c.rsplit('.', 1)[1]} is named in dollars but computed from cents with no /100 "
                     f"({rows[0]['summary'][:160]}).")
        elif kind == "pii_exposure":
            for t in role["copy"]:
                mark(t, "caution", "Holds raw sensitive values copied out of a restricted dataset, outside its protection.")
        elif kind == "pii_candidate":
            for c in role["subject"]:
                mark(c.rsplit(".", 1)[0], "caution", f"{c.rsplit('.', 1)[1]} looks like a raw SSN or tax id, outside the "
                     "restricted datasets.")
        elif kind == "competing_measures":
            sanctioned = (role["sanctioned"] or [None])[0]
            names = {r["x"]: r["x"].rsplit(".", 1)[1] for r in rows}
            for v in role["alternative"]:
                for r in G.rows("""MATCH (:Variable {id: $v})<-[:IS]-(:Column)<-[:HAS_COLUMN]-(t:Table) RETURN DISTINCT t.id AS t""", v=v):
                    mark(r["t"], "caution", f"Its {names[v]} is an alternative to the measure production and BI use "
                         f"({names.get(sanctioned, '?')}); people compare them, and they are not the same numbers.")

    # ---------------------------------------------------------- layers
    down = defaultdict(set)
    for r in G.rows("MATCH (a:Table)-[:DERIVED_FROM]->(b:Table) RETURN a.id AS a, b.id AS b"):
        down[r["b"]].add(r["a"])

    # which current marts carry a raw table's columns forward, and how many of them
    carry = defaultdict(lambda: defaultdict(set))
    for r in G.rows("""MATCH (t:Table {layer: 'raw'})-[:HAS_COLUMN]->(c:Column)-[:FLOWS*1..4]->(d:Column)<-[:HAS_COLUMN]-(m:Table)
                       WHERE m.layer = 'mart' AND m <> t RETURN DISTINCT t.id AS t, m.id AS m, c.id AS c"""):
        carry[r["t"]][r["m"]].add(r["c"])

    def marts_from(t):
        """Current marts built from t: the one carrying most of its columns first, a table before a view."""
        return sorted((m for m in carry[t] if status.get(m) == "current"),
                      key=lambda m: (-len(carry[t][m]), T[m]["kind"] == "view", -(T[m].get("consumer_count") or 0)))

    for t, m in T.items():
        if m["layer"] == "sandbox":
            days = len(m.get("write_days") or [])
            mark(t, "caution", "Maintained by a person, not by a production process"
                 + (f"; written by hand on {days} day(s) in the window, last {m['last_written'][:10]}" if days else "") + ".")
        elif m["layer"] == "raw" and status[t] == "current":
            ms = marts_from(t)
            if ms:
                mark(t, "caution", f"A raw feed; production models it into {', '.join(short(x) for x in ms[:3])}.",
                     ms[0], "the production model built from this raw feed that the business uses most")
        elif m["layer"] == "bi":
            mark(t, "caution", "Generated by a BI tool (a derived table the tool rebuilds); query its sources for "
                 "anything the BI model does not already answer.")
        if m.get("restricted"):
            mark(t, "caution", "In a restricted dataset: people are denied access.")

    G.batch("Table.status", """UNWIND $rows AS r MATCH (t:Table {id: r.t})
        SET t.status = r.s, t.status_reasons = r.why, t.freshness = r.f""",
            [{"t": t, "s": status[t], "why": reasons[t], "f": fresh.get(t)} for t in T])
    # status as labels too, so a Bloom / Explore perspective can colour tables by it (pipeline/views.py)
    G.run("MATCH (t:Table) REMOVE t:Avoid:Caution")
    G.run("MATCH (t:Table {status: 'avoid'}) SET t:Avoid")
    G.run("MATCH (t:Table {status: 'caution'}) SET t:Caution")
    G.batch("USE_INSTEAD", """UNWIND $rows AS r MATCH (a:Table {id: r.a}), (b:Table {id: r.b})
        MERGE (a)-[u:USE_INSTEAD]->(b) SET u.why = r.why""",
            [{"a": a, "b": b, "why": w} for (a, b), w in instead.items()])

    # ---------------------------------------------------------- joins, table to table
    G.run("""MATCH (t1:Table)-[:HAS_COLUMN]->(a:Column)<-[o1:ON {side: 'left'}]-(k:JoinKey)-[o2:ON {side: 'right'}]->(b:Column)
                   <-[:HAS_COLUMN]-(t2:Table)
             WHERE t1 <> t2 AND k.confidence <> 'self'
             OPTIONAL MATCH (s:QueryShape)-[:USES_JOIN]->(k)
             WITH t1, t2, k, a, b, count(DISTINCT s) AS shapes
             WITH CASE WHEN t1.id < t2.id THEN t1 ELSE t2 END AS x, CASE WHEN t1.id < t2.id THEN t2 ELSE t1 END AS y,
                  collect(a.name + ' = ' + b.name + ' (' + k.confidence + ')') AS on,
                  collect(k.confidence) AS conf, sum(shapes) AS shapes
             MERGE (x)-[j:JOINS]->(y)
             SET j.on = on, j.shapes = shapes, j.suspect = 'suspect' IN conf,
                 j.confidence = CASE WHEN 'production' IN conf THEN 'production' WHEN 'corroborated' IN conf THEN 'corroborated'
                                     WHEN 'single' IN conf THEN 'single' ELSE 'suspect' END""")

    # ---------------------------------------------------------- report
    n = defaultdict(int)
    for s in status.values():
        n[s] += 1
    L = ["# Guidance: which tables to use", "", f"Window ends {end}. {n['current']} current, {n['caution']} caution, "
         f"{n['avoid']} avoid; {len(instead)} use-instead links.", "", "## Avoid", "", "| table | why | use instead |", "|---|---|---|"]
    alt = defaultdict(list)
    for (a, b) in instead:
        alt[a].append(short(b))
    for t in sorted(T, key=short):
        if status[t] == "avoid":
            L.append(f"| {short(t)} | {' '.join(reasons[t])} | {', '.join(alt[t])} |")
    L += ["", "## Caution", "", "| table | why | use instead |", "|---|---|---|"]
    for t in sorted(T, key=short):
        if status[t] == "caution":
            L.append(f"| {short(t)} | {' '.join(reasons[t])} | {', '.join(alt[t])} |")
    (WORK / "GUIDE.md").write_text("\n".join(L) + "\n")
    joins = G.rows("MATCH ()-[j:JOINS]->() RETURN count(j) AS n, sum(CASE WHEN j.suspect THEN 1 ELSE 0 END) AS s")[0]
    print(f"guidance: {dict(n)}; use-instead {len(instead)}; table joins {joins['n']} ({joins['s']} with a suspect key) "
          f"-> {WORK / 'GUIDE.md'}")
    G.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

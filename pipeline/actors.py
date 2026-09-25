#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stage 3: the actor model. Who is doing what, decided by behaviour.

Writes to the graph (semanticlayer):

  Principal.class      human | ingestion | transformation | bi_service | ml | monitor | scheduled_reader
  Principal.tool_hint  from the account name only (dbt, looker, fivetran, ...) - a hint, never the basis
  Principal.class_evidence  the measured facts behind the class
  QueryShape.purpose   adhoc | bi | extract | ml_read | build | ingest | probe | view_definition | metadata | failed
  (:Author)-[:AUTHORED]->(:QueryShape), (:Author)-[:RUNS_AS]->(:Principal)
                       who wrote the SQL: a dbt model, a BI model rooted at one table, a person, a service
  (:Consumer)-[:USED]->(:QueryShape), (:Consumer)-[:THROUGH]->(:Principal)
                       end users behind a BI service account (Looker's user_id in its query context)
  (:Principal)-[:CONSUMES]->(:Table)
                       consumption reads only: not probes, metadata, view definitions or failed jobs
  (:Team)<-[:MEMBER_OF]-(:Principal)
                       people grouped by what they consume (GDS node similarity + Leiden)

Consumption is what later stages count as use; probes (health checks, tests, freshness,
BI cache triggers) and monitors are kept, labelled, and excluded from it (F19).

Usage: uv run pipeline/actors.py
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"

TOOL_TOKENS = [("dbt", "dbt"), ("looker", "looker"), ("fivetran", "fivetran"), ("tableau", "tableau"),
               ("hightouch", "hightouch"), ("elementary", "elementary"), ("vertex", "vertex"),
               ("composer", "airflow"), ("amplitude", "amplitude"), ("firebase", "ga4"), ("sftp", "sftp")]
CONSUMPTION = {"adhoc", "bi", "extract", "ml_read", "build"}


def tool_hint(email: str) -> str | None:
    e = email.lower()
    return next((t for k, t in TOOL_TOKENS if k in e), None)


def classify(p: dict) -> tuple[str, list[str]]:
    """Ordered rules over measured behaviour. Returns (class, reasons)."""
    if p["kind"] == "user":
        return "human", ["a user account"]
    R = []
    sel, wr, ing, loads = p["select_jobs"], p["write_jobs"], p["ingest_write_jobs"], p["loaded_tables"]
    if loads and sel:
        return "ml", [f"reads {p['tables_read']} tables and loads results into {loads} (out and back)"]
    if loads and not sel and not wr:
        return "ingestion", [f"only loads files into {loads} tables"]
    if wr and ing >= 0.8 * wr:
        return "ingestion", [f"{ing:,} of {wr:,} writes merge from per-run staging tables"]
    human_hours = p.get("business_hours_share", 0) >= 0.4 and p.get("weekend_share", 1) <= 0.25
    if p["consumers"] >= 3 or (sel and human_hours):
        R.append(f"{p['consumers']} end users in query context" if p["consumers"] >= 3 else
                 f"works human hours ({p.get('business_hours_share', 0):.0%} business hours, "
                 f"{p.get('weekend_share', 0):.0%} weekend)")
        return "bi_service", R
    if wr:
        return "transformation", [f"{wr:,} write jobs into {p['tables_written']} tables from warehouse sources"]
    if sel and p["probe_jobs"] >= 0.8 * sel:
        return "monitor", [f"{p['probe_jobs'] / sel:.0%} of its reads are single-row checks, "
                           f"{p['shapes']} shapes in {p['families']} families over {p['tables_read']} tables"]
    if sel:
        return "scheduled_reader", [f"reads {p['tables_read']} tables on a schedule "
                                    f"({p.get('recurring_slot_share', 0):.0%} same-slot)"]
    return "unknown", ["no reads or writes"]


def main() -> int:
    G = Graph()
    # clear previous Stage 3 output
    G.auto("MATCH (n) WHERE n:Author OR n:Consumer OR n:Team CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS")
    G.run("MATCH ()-[r:CONSUMES]->() DELETE r")
    G.run("MATCH ()-[r:SIMILAR]->() DELETE r")

    shapes = {r["id"]: r for r in G.rows("""
        MATCH (s:QueryShape)
        OPTIONAL MATCH (s)-[:WRITES]->(w:Table)
        OPTIONAL MATCH (s)-[:REFERENCES]->(t:Table)
        RETURN s.id AS id, s.succeeded AS ok, s.origin AS origin, s.statement_type AS st, s.jobs AS jobs,
               s.output_aggregate_only AS agg_only, s.output_grouped AS grouped, s.family_id AS family,
               s.root_from AS root_from, collect(DISTINCT w.id) AS writes,
               collect(DISTINCT {id: t.id, kind: t.kind}) AS refs""")}
    ran = G.rows("""MATCH (p:Principal)-[r:RAN]->(s:QueryShape)
                    RETURN p.id AS p, s.id AS s, r.jobs AS jobs, r.errors AS errors, r.first_seen AS first""")
    loaded = Counter(r["p"] for r in G.rows("MATCH (p:Principal)-[:LOADED]->(t:Table) RETURN p.id AS p"))
    principals = {r["p"]["id"]: r["p"] for r in G.rows("MATCH (p:Principal) RETURN p {.*} AS p")}

    # end users and dbt nodes, from query-context annotations on each text
    text_shape, notes = {}, {}
    for line in gzip.open(WORK / "texts.ndjson.gz", "rt"):
        t = json.loads(line)
        text_shape[t["text_id"]] = t["shape_id"]
        if t.get("annotations"):
            notes[t["text_id"]] = t["annotations"]
    users = defaultdict(Counter)            # (principal, shape) -> end user -> jobs
    dbt_node = {}
    for line in gzip.open(WORK / "t0_groups.ndjson.gz", "rt"):
        g = json.loads(line)
        if not g["query"]:
            continue
        tid = hashlib.sha1(g["query"].encode()).hexdigest()
        for a in notes.get(tid, []):
            sid = text_shape.get(tid)
            if a.get("user_id") is not None and sid:
                users[(g["user_email"], sid)][f"{(a.get('source') or 'context').split()[0].lower()}:{a['user_id']}"] += g["jobs"]
            if a.get("app") == "dbt" and a.get("node_id") and sid:
                dbt_node[sid] = a["node_id"]
    user_shapes = {s for (_, s) in users}

    def is_probe(s):
        return s["st"] == "SELECT" and s["agg_only"] and not s["grouped"] and s["id"] not in user_shapes

    def ingest_write(s):
        return bool(s["writes"]) and any(r["kind"] == "transient" for r in s["refs"])

    # ------------------------------------------------ principal features + class
    feats = {}
    for pid, p in principals.items():
        mine = [r for r in ran if r["p"] == pid]
        ok = [(r, shapes[r["s"]]) for r in mine if r["s"] in shapes and shapes[r["s"]]["ok"]]
        f = {"kind": p["kind"],
             "business_hours_share": p.get("business_hours_share", 0), "weekend_share": p.get("weekend_share", 0),
             "recurring_slot_share": p.get("recurring_slot_share", 0),
             "select_jobs": sum(r["jobs"] for r, s in ok if s["st"] == "SELECT"),
             "write_jobs": sum(r["jobs"] for r, s in ok if s["writes"] and s["st"] != "CREATE_VIEW"),
             "ingest_write_jobs": sum(r["jobs"] for r, s in ok if ingest_write(s)),
             "probe_jobs": sum(r["jobs"] for r, s in ok if is_probe(s)),
             "loaded_tables": loaded.get(pid, 0),
             "consumers": len({u for (pp, _), c in users.items() if pp == pid for u in c}),
             "tables_read": len({t["id"] for _, s in ok for t in s["refs"] if t["kind"] not in ("system", "transient")}),
             "tables_written": len({w for _, s in ok for w in s["writes"]}),
             "shapes": len(ok), "families": len({s["family"] for _, s in ok})}
        cls, reasons = classify(f)
        f["class"], f["reasons"] = cls, reasons
        feats[pid] = f

    # --------------------------------------------------------- shape purpose
    runner = {}
    for r in ran:
        if r["s"] not in runner or r["jobs"] > runner[r["s"]]["jobs"]:
            runner[r["s"]] = r
    purpose = {}
    for sid, s in shapes.items():
        cls = feats.get((runner.get(sid) or {}).get("p"), {}).get("class")
        if not s["ok"]:
            p_ = "failed"
        elif s["origin"] == "catalog_view" or s["st"] == "CREATE_VIEW":
            p_ = "view_definition"
        elif s["refs"] and all(t["kind"] == "system" for t in s["refs"]):
            p_ = "metadata"
        elif s["writes"]:
            p_ = "ingest" if ingest_write(s) else "build"
        elif sid in user_shapes:
            p_ = "bi"
        elif cls == "human":
            p_ = "adhoc"
        elif is_probe(s) or cls in ("monitor", "transformation"):
            p_ = "probe"
        else:
            p_ = {"bi_service": "bi", "scheduled_reader": "extract", "ml": "ml_read"}.get(cls, "extract")
        purpose[sid] = p_

    # ------------------------------------------------------------ authorship
    human_runs = defaultdict(list)
    for r in ran:
        if feats.get(r["p"], {}).get("class") == "human":
            human_runs[r["s"]].append(r)
    authors, authored = {}, []
    for sid, s in shapes.items():
        run = runner.get(sid)
        if run is None:
            continue
        cls = feats[run["p"]]["class"]
        if sid in dbt_node:
            aid, kind = f"dbt:{dbt_node[sid]}", "dbt_model"
        elif cls == "bi_service":
            target = s["writes"][0] if s["writes"] else s["root_from"]
            aid, kind = f"{tool_hint(run['p']) or 'bi'}:{target}", "bi_model"
        elif human_runs.get(sid):
            first = min(human_runs[sid], key=lambda r: r["first"] or "")
            aid, kind = f"person:{first['p']}", "person"
        else:
            aid, kind = f"service:{run['p']}", "service"
        authors.setdefault(aid, {"id": aid, "kind": kind, "principal": run["p"]})
        authored.append({"author": aid, "shape": sid})

    # -------------------------------------------------------------- write
    G.batch("Principal.class", """UNWIND $rows AS r MATCH (p:Principal {id: r.id})
        SET p.class = r.class, p.tool_hint = r.tool, p.class_evidence = r.reasons, p += r.f""",
            [{"id": pid, "class": f["class"], "tool": tool_hint(pid), "reasons": f["reasons"],
              "f": {k: v for k, v in f.items() if k not in ("class", "reasons", "kind", "business_hours_share",
                                                           "weekend_share", "recurring_slot_share")}}
             for pid, f in feats.items()])
    G.batch("QueryShape.purpose", "UNWIND $rows AS r MATCH (s:QueryShape {id: r.id}) SET s.purpose = r.purpose",
            [{"id": k, "purpose": v} for k, v in purpose.items()])
    G.batch("Author", """UNWIND $rows AS r MERGE (a:Author {id: r.id}) SET a.kind = r.kind
        WITH a, r MATCH (p:Principal {id: r.principal}) MERGE (a)-[:RUNS_AS]->(p)""", list(authors.values()))
    G.batch("AUTHORED", """UNWIND $rows AS r MATCH (a:Author {id: r.author}), (s:QueryShape {id: r.shape})
        MERGE (a)-[:AUTHORED]->(s)""", authored)
    G.run("MATCH (s:QueryShape) OPTIONAL MATCH (a:Author)-[:AUTHORED]->(s) SET s.author = a.id")
    cons = [{"id": u, "principal": pp, "shape": sid, "jobs": n, "tool": u.split(":")[0]}
            for (pp, sid), c in users.items() for u, n in c.items()]
    G.batch("Consumer", """UNWIND $rows AS r MERGE (c:Consumer {id: r.id}) SET c.tool = r.tool
        WITH c, r MATCH (p:Principal {id: r.principal}), (s:QueryShape {id: r.shape})
        MERGE (c)-[:THROUGH]->(p) MERGE (c)-[u:USED]->(s) SET u.jobs = r.jobs""", cons)
    # consumption: direct references by consumption shapes (views are followed in Stage 5)
    G.run("""MATCH (p:Principal)-[r:RAN]->(s:QueryShape)-[:REFERENCES]->(t:Table)
             WHERE s.purpose IN $purposes AND r.jobs > r.errors AND NOT t.kind IN ['system', 'transient']
             WITH p, t, sum(r.jobs - r.errors) AS jobs, count(DISTINCT s) AS shapes, collect(DISTINCT s.purpose) AS ps,
                  min(r.first_seen) AS first, max(r.last_seen) AS last
             MERGE (p)-[c:CONSUMES]->(t)
             SET c.jobs = jobs, c.shapes = shapes, c.purposes = ps, c.first_seen = first, c.last_seen = last""",
          purposes=sorted(CONSUMPTION))

    teams = infer_teams(G)
    print_summary(G, feats, purpose, authors, cons, teams)
    G.close()
    return 0


def infer_teams(G: Graph) -> int:
    """People who consume the same tables work together: weighted Jaccard over ad-hoc
    consumption (GDS node similarity), then Leiden on the similarity graph."""
    G.run("""MATCH (p:Principal {class: 'human'})-[c:CONSUMES]->(t:Table)
             SET c.weight = log(1 + c.jobs)""")
    for name in ("qlsc_people", "qlsc_similar"):
        G.auto("CALL gds.graph.drop($n, false) YIELD graphName RETURN graphName", n=name)
    G.auto("""MATCH (p:Principal {class: 'human'})-[c:CONSUMES]->(t:Table)
              WITH gds.graph.project('qlsc_people', p, t, {relationshipProperties: c {.weight}}) AS g
              RETURN g.graphName""")
    G.auto("""CALL gds.nodeSimilarity.write('qlsc_people', {relationshipWeightProperty: 'weight',
              writeRelationshipType: 'SIMILAR', writeProperty: 'score', topK: 5, similarityCutoff: 0.1, concurrency: 1})
              YIELD relationshipsWritten RETURN relationshipsWritten""")
    G.auto("""MATCH (a:Principal)-[s:SIMILAR]->(b:Principal)
              WITH gds.graph.project('qlsc_similar', a, b, {relationshipProperties: s {.score}},
                                     {undirectedRelationshipTypes: ['*']}) AS g
              RETURN g.graphName""")
    res = G.auto("""CALL gds.leiden.stream('qlsc_similar', {relationshipWeightProperty: 'score', randomSeed: 7, concurrency: 1,
                    gamma: 1.0, theta: 0.01, maxLevels: 10})
                    YIELD nodeId, communityId
                    RETURN gds.util.asNode(nodeId).id AS p, communityId AS c""")
    for name in ("qlsc_people", "qlsc_similar"):
        G.auto("CALL gds.graph.drop($n, false) YIELD graphName RETURN graphName", n=name)
    # people with no similar peer get their own team
    comm = {r["p"]: f"team-{r['c']}" for r in res}
    for r in G.rows("MATCH (p:Principal {class: 'human'}) RETURN p.id AS p"):
        comm.setdefault(r["p"], f"team-solo-{r['p'].split('@')[0]}")
    G.batch("Team", """UNWIND $rows AS r MERGE (t:Team {id: r.team})
        WITH t, r MATCH (p:Principal {id: r.p}) MERGE (p)-[:MEMBER_OF]->(t)""",
            [{"p": p, "team": t} for p, t in comm.items()])
    # describe each team by the datasets its members consume most, relative to everyone else
    G.run("""MATCH (t:Team)<-[:MEMBER_OF]-(p:Principal)-[c:CONSUMES]->(tb:Table)-[:IN_DATASET]->(d:Dataset)
             WITH t, d, sum(c.jobs) AS jobs ORDER BY jobs DESC
             WITH t, collect(d.name)[0..3] AS top
             SET t.top_datasets = top, t.size = count { (t)<-[:MEMBER_OF]-() }""")
    return len(set(comm.values()))


def print_summary(G, feats, purpose, authors, cons, teams):
    print(f"{'principal':28} {'class':16} {'tool':11} evidence")
    for pid, f in sorted(feats.items(), key=lambda kv: (kv[1]["class"] == "human", kv[0])):
        if f["class"] != "human":
            print(f"{pid.split('@')[0][:28]:28} {f['class']:16} {str(tool_hint(pid)):11} {'; '.join(f['reasons'])}")
    print(f"{sum(1 for f in feats.values() if f['class'] == 'human')} humans; "
          f"shape purposes {dict(Counter(purpose.values()).most_common())}")
    print(f"{len(authors)} authors {dict(Counter(a['kind'] for a in authors.values()))}; "
          f"{len({c['id'] for c in cons})} end users behind BI services; {teams} teams")
    for r in G.rows("""MATCH (t:Team)<-[:MEMBER_OF]-(p:Principal)
                       RETURN t.id AS team, t.top_datasets AS datasets, collect(split(p.id, '@')[0]) AS members
                       ORDER BY size(members) DESC"""):
        print(f"  {r['team']:24} {', '.join(r['members'])}  <- {', '.join(r['datasets'] or [])}")


if __name__ == "__main__":
    sys.exit(main())

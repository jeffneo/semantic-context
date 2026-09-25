#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stages 5a/5d: layers, subject areas, copy chains and sensitive-data lineage.

Needs M2 (actors, detect: table usage) and M3 (variables, hubs).

Layer - from who writes a table and what it is built from, never from dataset names:
  raw           written by ingestion (Fivetran merges, file loads), or never written and fed by nothing
  staging       a transformation view over raw tables that mostly passes columns through
  intermediate  built by a transformation, consumed only by other builds
  mart          built by a transformation, consumed by people, BI or ML
  bi            written by a BI service (Looker PDTs)
  sandbox       written by people
  ml            loaded by an ML job

Subject areas (D7): tables are grouped by the non-hub variables they share, each weighted
by how rare it is (a variable in two tables says more than one in twenty). Hub variables -
customer, account, product, branch - do not vote on membership; they link subjects, and
each subject records which hubs it is keyed by. Tables whose only keys are hubs (dim_customer,
customer_360) form the hub's entity subject. GDS Leiden over the similarity graph. For
comparison, a baseline partition with hubs counted like any other variable is stored too.

Writes:
  Table.layer, (:Subject)<-[:IN_SUBJECT]-(:Table), (:Subject)-[:KEYED_BY {tables}]->(:Variable),
  (:Subject)-[:LINKED {via, joins}]->(:Subject), Table.subject_baseline,
  (:Table)-[:COPY_OF {evidence, share}]->(:Table)
  (:Finding) kinds: copy_chain, pii_exposure, pii_candidate
  work/TOPOLOGY.md

Usage: uv run pipeline/topology.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
HASH_FNS = {"SHA256", "SHA512", "SHA1", "MD5"}
PII_NAME = re.compile(r"(?i)(^|_)(ssn|ssn_nbr|social_sec\w*|tax_?id|tin)($|_)")
ROLE_WEIGHT = {"identifier": 3.0, "measure": 1.0, "category": 1.0, "time": 0.5, "attribute": 1.0}


def short(x: str) -> str:
    return ".".join(x.split(".")[1:])


def main() -> int:
    G = Graph()
    G.run("CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (n:Subject) REQUIRE n.id IS UNIQUE")
    G.auto("MATCH (n:Subject) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS")
    G.run("MATCH ()-[r:COPY_OF|SHARES]->() DELETE r")
    G.auto("""MATCH (f:Finding) WHERE f.kind IN ['copy_chain', 'pii_exposure', 'pii_candidate']
              CALL (f) { DETACH DELETE f } IN TRANSACTIONS OF 5000 ROWS""")
    findings = []

    def finding(kind, fid, title, summary, about, evidence=None):
        findings.append({"id": f"{kind}:{fid}", "kind": kind, "title": title, "summary": summary, "cost_bytes": 0,
                         "evidence": json.dumps(evidence or {}, default=str), "about": about})

    tables = {r["t"]["id"]: r["t"] for r in G.rows("""MATCH (t:Table) WHERE t.in_catalog
        RETURN t {.id, .name, .kind, .consumed_jobs, .consumer_count, .written_jobs, .first_written, .last_written,
                  .last_consumed, dataset: split(t.id, '.')[1]} AS t""")}
    writers = defaultdict(set)
    for r in G.rows("""MATCH (p:Principal)-[:RAN]->(s:QueryShape {succeeded: true})-[w:WRITES]->(t:Table)
                       WHERE s.statement_type <> 'CREATE_VIEW' RETURN t.id AS t, p.class AS c"""):
        writers[r["t"]].add(r["c"])
    for r in G.rows("MATCH (p:Principal)-[:LOADED]->(t:Table) RETURN t.id AS t, p.class AS c"):
        writers[r["t"]].add(r["c"])
    view_def = {r["t"] for r in G.rows("""MATCH (s:QueryShape)-[w:WRITES]->(t:Table {kind: 'view'}) RETURN DISTINCT t.id AS t""")}
    sources = defaultdict(set)
    for r in G.rows("MATCH (a:Table)-[:DERIVED_FROM]->(b:Table) WHERE b.kind <> 'system' RETURN a.id AS a, b.id AS b"):
        sources[r["a"]].add(r["b"])
    consumers = defaultdict(set)
    for r in G.rows("MATCH (p:Principal)-[:CONSUMES]->(t:Table) RETURN t.id AS t, p.class AS c"):
        consumers[r["t"]].add(r["c"])
    tcols = defaultdict(list)
    for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) OPTIONAL MATCH (c)-[:IS]->(v:Variable)
                       RETURN t.id AS t, c.id AS c, c.name AS name, v.id AS v, v.role AS role, v.hub AS hub"""):
        tcols[r["t"]].append(r)
    flows = G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column)<-[:HAS_COLUMN]-(tb:Table), (ta:Table)-[:HAS_COLUMN]->(a)
                      RETURN a.id AS a, b.id AS b, ta.id AS ta, tb.id AS tb, f.kinds AS kinds, f.fns AS fns,
                             f.shapes AS shapes""")

    # ---------------------------------------------------------------- layers
    layer = {}
    for t in tables:
        w = writers.get(t, set())
        if w & {"ingestion"}:
            layer[t] = "raw"
        elif w & {"ml"}:
            layer[t] = "ml"
        elif w & {"human"} and not w & {"transformation"}:
            layer[t] = "sandbox"
        elif w & {"bi_service"} and not w & {"transformation"}:
            layer[t] = "bi"
    for _ in range(3):                                  # staging depends on its sources' layers
        for t, m in tables.items():
            if t in layer and layer[t] not in ("staging", "intermediate", "mart", "unwritten"):
                continue
            w = writers.get(t, set())
            src = sources.get(t, set())
            built = "transformation" in w or t in view_def or (m["kind"] == "view" and src)
            if not built and not src:
                layer[t] = "unwritten"                # exists; nothing wrote or fed it in the window
                continue
            if not built:
                layer[t] = "sandbox" if "human" in w else "unwritten"
                continue
            fed = [f for f in flows if f["tb"] == t]
            same = sum(1 for f in fed if set(f["kinds"]) <= {"passthrough", "rename"}) / max(len(fed), 1)
            if m["kind"] == "view" and src and all(layer.get(s) in ("raw", "unwritten", "sandbox") for s in src) \
                    and same >= 0.5:
                layer[t] = "staging"
            elif consumers.get(t, set()) - {"transformation"}:
                layer[t] = "mart"
            else:
                layer[t] = "intermediate"
    G.batch("Table.layer", "UNWIND $rows AS r MATCH (t:Table {id: r.id}) SET t.layer = r.layer",
            [{"id": t, "layer": l} for t, l in layer.items()])

    # --------------------------------------------------------------- copies
    colset = {t: {c["name"].lower() for c in cs} for t, cs in tcols.items()}
    copies = {}
    per_pair = defaultdict(lambda: {"same": 0, "cols": set()})
    for f in flows:
        if f["ta"] != f["tb"] and set(f["kinds"]) <= {"passthrough", "rename"}:
            per_pair[(f["tb"], f["ta"])]["cols"].add(f["b"])
    # A copy holds most of the original, and most of it comes from the original - both ways.
    # An audience that selects five columns of customer_360 is an extract, not a copy; dbt
    # promoting an intermediate model to a mart is modelling, not sprawl.
    for (t2, t1), e in per_pair.items():
        if t1 in tables and t2 in tables and layer.get(t2) in ("sandbox", "bi", "unwritten"):
            share = len(e["cols"]) / max(len(tcols[t2]), 1)
            covers = len({f["a"] for f in flows if f["tb"] == t2 and f["ta"] == t1
                          and set(f["kinds"]) <= {"passthrough", "rename"}}) / max(len(tcols[t1]), 1)
            if share >= 0.8 and covers >= 0.8 and len(tcols[t2]) >= 5 and tables[t2]["kind"] != "view":
                copies[(t2, t1)] = ("lineage", min(share, covers))
    # a copy made before the window has no lineage in it; the same columns are the evidence then
    for t2, c2 in colset.items():
        if t2 not in tables or len(c2) < 5 or tables[t2]["kind"] == "view" or any(k[0] == t2 for k in copies):
            continue
        for t1, c1 in colset.items():
            if t1 == t2 or t1 not in tables or tables[t1]["kind"] == "view" or len(c1) < 5:
                continue
            j = len(c1 & c2) / len(c1 | c2)
            if j >= 0.9 and (layer.get(t1) in ("mart", "intermediate") or (tables[t1]["first_written"] or "9") <
                             (tables[t2]["first_written"] or "9")) and layer.get(t2) in ("sandbox", "unwritten"):
                copies[(t2, t1)] = ("schema", j)
    G.batch("COPY_OF", """UNWIND $rows AS r MATCH (a:Table {id: r.a}), (b:Table {id: r.b})
        MERGE (a)-[x:COPY_OF]->(b) SET x.evidence = r.ev, x.share = r.share""",
            [{"a": a, "b": b, "ev": ev, "share": sh} for (a, b), (ev, sh) in copies.items()])
    parent = {}
    for (a, b), (ev, sh) in sorted(copies.items(), key=lambda kv: -kv[1][1]):
        parent.setdefault(a, b)                   # a copy has one original: the closest match

    def root_of(t, seen=()):
        return t if t not in parent or parent[t] in seen else root_of(parent[t], seen + (t,))
    families = defaultdict(set)
    for a, b in parent.items():
        families[root_of(a)] |= {a, b}
    for root, fam in families.items():
        if len(fam) < 3:
            continue
        depth = {root: 0}
        for _ in range(len(fam)):
            for a, b in parent.items():
                if a in fam and b in depth and a not in depth:
                    depth[a] = depth[b] + 1
        order = sorted(fam, key=lambda t: (depth.get(t, 9), t))
        use = {t: tables[t].get("consumed_jobs") or 0 for t in fam}
        top = max(fam, key=lambda t: use[t])
        least = min(fam, key=lambda t: use[t])
        top_copy = max((t for t in fam if t != root), key=lambda t: use[t])
        stale = [t for t in fam if t != root and not tables[t].get("last_written")]
        line = lambda t: (t.split(".")[-1] + (f" (copy of {parent[t].split('.')[-1]}, {copies[(t, parent[t])][0]})"
                                               if t in parent else " (original)") + f": {use[t]:,} jobs")
        finding("copy_chain", root, f"Copy family of {root.split('.')[-1]}: {len(fam)} tables",
                "; ".join(line(t) for t in order) + f". Actually used: {top.split('.')[-1]}; most used copy: "
                f"{top_copy.split('.')[-1]}; least used: "
                f"{least.split('.')[-1]}" + (f"; not rewritten in the window (stale snapshots): "
                                               f"{', '.join(t.split('.')[-1] for t in stale)}" if stale else "")
                + f". Consolidation target, by usage: {top.split('.')[-1]}.",
                [{"id": t, "label": "Table", "role": "consolidate_into" if t == top else ("original" if t == root else "copy")}
                 for t in order],
                evidence={"order": order, "parent": {t: parent[t] for t in fam if t in parent}, "use": use,
                          "de_facto": top, "top_copy": top_copy, "least_used": least, "stale": stale})

    # --------------------------------------------------------------- subjects
    hub_vars = {c["v"] for cs in tcols.values() for c in cs if c["hub"]}
    df = Counter()
    tvars = defaultdict(dict)
    for t, cs in tcols.items():
        if t not in tables:
            continue
        for c in cs:
            if c["v"]:
                tvars[t][c["v"]] = c["role"]
    for t, vs in tvars.items():
        df.update(vs.keys())
    N = len(tvars)

    def similarity(include_hubs: bool):
        idx = defaultdict(set)
        for t, vs in tvars.items():
            for v in vs:
                if df[v] >= 2 and (include_hubs or v not in hub_vars):
                    idx[v].add(t)
        w = defaultdict(float)
        for v, ts in idx.items():
            role = tvars[next(iter(ts))][v]
            wt = ROLE_WEIGHT.get(role or "attribute", 1.0) * math.log(1 + N / len(ts))
            ts = sorted(ts)
            for i, a in enumerate(ts):
                for b in ts[i + 1:]:
                    w[(a, b)] += wt
        return w

    def leiden(weights, name):
        rows = [{"a": a, "b": b, "w": x} for (a, b), x in weights.items() if x > 0]
        G.run("MATCH ()-[r:SHARES]->() DELETE r")
        G.batch("SHARES", """UNWIND $rows AS r MATCH (a:Table {id: r.a}), (b:Table {id: r.b})
            CREATE (a)-[:SHARES {w: r.w}]->(b)""", rows)
        G.auto("CALL gds.graph.drop($n, false) YIELD graphName RETURN graphName", n=name)
        G.auto("""MATCH (a:Table)-[s:SHARES]->(b:Table)
                  WITH gds.graph.project($n, a, b, {relationshipProperties: s {.w}},
                                         {undirectedRelationshipTypes: ['*']}) AS g RETURN g.graphName""", n=name)
        res = G.auto(f"""CALL gds.leiden.stream($n, {{relationshipWeightProperty: 'w', randomSeed: 7, concurrency: 1,
                             includeIntermediateCommunities: true}})
                         YIELD nodeId, communityId, intermediateCommunityIds
                         RETURN gds.util.asNode(nodeId).id AS t, communityId AS c, intermediateCommunityIds AS levels""", n=name)
        G.auto("CALL gds.graph.drop($n, false) YIELD graphName RETURN graphName", n=name)
        G.run("MATCH ()-[r:SHARES]->() DELETE r")
        # finest level = subject; coarsest = area
        return ({r["t"]: (r["levels"] or [r["c"]])[0] for r in res}, {r["t"]: r["c"] for r in res})

    # D7: a hub's own tables - the dimension it is homed in, and crosswalks that map its ids -
    # form the hub's entity subject; they do not glue the subjects that key on it.
    homes = {}
    for r in G.rows("""MATCH (v:Variable {hub: true})<-[:IS]-(c:Column)<-[:ON]-(k:JoinKey)
                       WHERE k.confidence IN ['production', 'corroborated', 'single']
                       MATCH (t:Table)-[:HAS_COLUMN]->(c)
                       WITH v, t, count(DISTINCT k) AS n ORDER BY n DESC
                       WITH v, collect(t.id)[0] AS home RETURN v.id AS v, home"""):
        homes.setdefault(r["home"], r["v"])
    for r in G.rows("""MATCH (f:Finding {kind: 'identity_map'})-[a:ABOUT {role: 'crosswalk'}]->(t:Table)
                       MATCH (f)-[:ABOUT {role: 'identifier'}]->(v:Variable {hub: true})
                       RETURN t.id AS t, collect(v.id)[0] AS v"""):
        homes.setdefault(r["t"], r["v"])
    homes = {t: v for t, v in homes.items() if t in tvars}
    held = {t: tvars.pop(t) for t in homes}      # out of the clustering; placed in their entity subject
    main_w = similarity(include_hubs=False)
    comm, area = leiden(main_w, "qlsc_subjects")
    tvars.update(held)
    base, base_area = leiden(similarity(include_hubs=True), "qlsc_subjects_baseline")
    entities = {r["v"]: r["e"] for r in G.rows("MATCH (v:Variable)-[:IDENTIFIES]->(e:Entity) RETURN v.id AS v, e.name AS e")}
    joined_tables = {r["v"]: r["n"] for r in G.rows("MATCH (v:Variable) RETURN v.id AS v, v.joined_tables AS n")}
    vname = {r["v"]: r["n"] for r in G.rows("MATCH (v:Variable) RETURN v.id AS v, v.name AS n")}
    subject_of = {}
    for t in tvars:
        if t in homes:
            h = homes[t]
            subject_of[t] = f"entity-{entities.get(h, vname.get(h, h))}"
        elif t in comm:
            subject_of[t] = f"subject-{comm[t]}"
        else:
            hubs_here = [v for v in tvars[t] if v in hub_vars and tvars[t][v] == "identifier"]
            if hubs_here:                       # only hub keys: the hub's entity subject
                h = min(hubs_here, key=lambda v: joined_tables.get(v) or 99)
                subject_of[t] = f"entity-{entities.get(h, vname.get(h, h))}"
            else:
                subject_of[t] = f"solo-{t.split('.')[-1]}"
    # name each subject by its most distinctive shared variable (M5 will name them properly)
    members = defaultdict(list)
    for t, s in subject_of.items():
        members[s].append(t)
    subjects = {}
    for sid, ts in members.items():
        vc = Counter(v for t in ts for v in tvars[t] if v not in hub_vars and df[v] >= 2)
        best = max(vc, key=lambda v: vc[v] * math.log(1 + N / df[v]), default=None)
        name = sid.split("-", 1)[1] if sid.startswith(("entity-", "solo-")) else (vname.get(best) or sid)
        keyed = Counter(v for t in ts for v, r in tvars[t].items() if v in hub_vars and r == "identifier")
        subjects[sid] = {"id": sid, "name": name, "size": len(ts), "kind": sid.split("-")[0],
                         "keyed_by": {v: n for v, n in keyed.items()}}
    G.batch("Subject", "UNWIND $rows AS r CREATE (s:Subject {id: r.id, name: r.name, size: r.size, kind: r.kind})",
            list(subjects.values()))
    G.batch("IN_SUBJECT", """UNWIND $rows AS r MATCH (t:Table {id: r.t}), (s:Subject {id: r.s})
        MERGE (t)-[:IN_SUBJECT]->(s) SET t.subject_baseline = r.b, t.area = r.a, t.area_baseline = r.ba""",
            [{"t": t, "s": s, "b": f"b-{base.get(t, 'solo-' + t)}", "ba": f"ba-{base_area.get(t, 'solo-' + t)}",
              "a": (f"a-{area[t]}" if t in area else s)} for t, s in subject_of.items()])
    G.batch("KEYED_BY", """UNWIND $rows AS r MATCH (s:Subject {id: r.s}), (v:Variable {id: r.v})
        MERGE (s)-[k:KEYED_BY]->(v) SET k.tables = r.n""",
            [{"s": sid, "v": v, "n": n} for sid, s in subjects.items() for v, n in s["keyed_by"].items()])
    # subjects linked by accepted joins between their tables, through which variable
    G.run("""MATCH (s1:Subject)<-[:IN_SUBJECT]-(t1:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)
                   <-[:HAS_COLUMN]-(t2:Table)-[:IN_SUBJECT]->(s2:Subject)
             WHERE s1 <> s2 AND elementId(s1) < elementId(s2) AND k.confidence IN ['production', 'corroborated', 'single']
             OPTIONAL MATCH (a)-[:IS]->(v:Variable)
             WITH s1, s2, collect(DISTINCT v.name) AS via, count(DISTINCT k) AS joins
             MERGE (s1)-[l:LINKED]->(s2) SET l.via = via, l.joins = joins""")

    # ---------------------------------------------------- sensitive data (F08)
    denied = {r["d"] for r in G.rows("""MATCH (p:Principal)-[:RAN]->(s:QueryShape)-[:REFERENCES]->(:Table)-[:IN_DATASET]->(d:Dataset)
        WHERE s.error_reasons CONTAINS 'accessDenied' WITH d, count(DISTINCT p) AS n WHERE n >= 2 RETURN d.id AS d""")}
    restricted = {t for t in tables if ".".join(t.split(".")[:2]) in denied}
    hashed = {f["a"] for f in flows if set(f["fns"] or []) & HASH_FNS}          # the business protects these
    sensitive = hashed | {c["c"] for t in restricted for c in tcols[t] if c["c"] in hashed or PII_NAME.search(c["name"])}
    down = defaultdict(list)
    for f in flows:
        down[f["a"]].append(f)
    exposed = {}
    for s0 in sensitive:
        stack = [(s0, [])]
        seen = set()
        while stack:
            cur, path = stack.pop()
            for f in down.get(cur, []):
                if f["b"] in seen or set(f["fns"] or []) & HASH_FNS:
                    continue            # hashed on the way: protected
                seen.add(f["b"])
                if not set(f["kinds"]) <= {"passthrough", "rename"}:
                    continue
                if f["tb"] not in restricted and f["tb"] in tables:
                    exposed.setdefault(f["b"], (s0, path + [f]))
                stack.append((f["b"], path + [f]))
    authors = {r["s"]: r["a"] for r in G.rows("MATCH (a:Author)-[:AUTHORED]->(s:QueryShape) RETURN s.id AS s, a.id AS a")}
    readers = defaultdict(set)
    for r in G.rows("""MATCH (p:Principal)-[:RAN]->(s:QueryShape {succeeded: true})-[:READS]->(c:Column)
                       WHERE s.purpose IN ['adhoc', 'bi', 'extract', 'ml_read'] RETURN c.id AS c, p.id AS p"""):
        readers[r["c"]].add(r["p"].split("@")[0])
    for col, (src, path) in exposed.items():
        who = sorted({authors.get(s_, "?").split(":", 1)[-1].split("@")[0] for f in path for s_ in f["shapes"] or []})
        why = ("its source is in a dataset people are denied (" + ".".join(src.split(".")[:2]).split(".", 1)[1] + ")"
               if any(src.startswith(d + ".") for d in denied) else "production hashes it everywhere else")
        finding("pii_exposure", col, f"Sensitive value copied raw: {short(col)}",
                f"{short(col)} is a raw copy of {short(src)} - {why} - made by {', '.join(who)} "
                f"({' -> '.join(short(f['b']) for f in path)}), in a dataset without that protection. "
                f"CREATE TABLE AS SELECT does not carry column policy tags. Read by: "
                f"{', '.join(sorted(readers.get(col, []))) or 'nobody in the window'}.",
                [{"id": col, "label": "Column", "role": "exposed"}, {"id": src, "label": "Column", "role": "source"}],
                evidence={"source": src, "path": [f["b"] for f in path], "authors": who})
    # a copy made before the window: nearly every column of an unprotected table exists in a restricted one
    for t2, c2 in colset.items():
        if t2 not in tables or t2 in restricted or len(c2) < 4 or layer.get(t2) not in ("sandbox", "unwritten"):
            continue
        for t1 in restricted:
            share = len(c2 & colset.get(t1, set())) / len(c2)
            if share < 0.8:
                continue
            for c in [c for c in tcols[t2] if PII_NAME.search(c["name"]) and "hash" not in c["name"].lower()]:
                src = next((x["c"] for x in tcols[t1] if x["name"].lower() == c["name"].lower()), None)
                if not src or c["c"] in exposed:
                    continue
                exposed[c["c"]] = (src, [])
                finding("pii_exposure", c["c"], f"Sensitive value copied raw: {short(c['c'])}",
                        f"{short(t2)} is a copy of {short(t1)} ({share:.0%} of its columns are {t1.split('.')[-1]}'s; "
                        f"copied before the window), and {t1.split('.')[1]} is a dataset people are denied. Its "
                        f"{c['name']} sits unprotected in {t2.split('.')[1]}: CREATE TABLE AS SELECT does not carry "
                        f"column policy tags. Read by: {', '.join(sorted(readers.get(c['c'], []))) or 'nobody in the window'}.",
                        [{"id": c["c"], "label": "Column", "role": "exposed"}, {"id": src, "label": "Column", "role": "source"},
                         {"id": t2, "label": "Table", "role": "copy"}, {"id": t1, "label": "Table", "role": "restricted_source"}],
                        evidence={"source_table": t1, "share": share, "evidence": "schema"})
    hash_outputs = {f["b"] for f in flows if set(f["fns"] or []) & HASH_FNS}
    for t, cs in tcols.items():
        if t not in tables or t in restricted:
            continue
        for c in cs:
            if PII_NAME.search(c["name"]) and c["c"] not in hash_outputs and c["c"] not in exposed and "hash" not in c["name"].lower():
                prot = c["c"] in hashed
                finding("pii_candidate", c["c"], f"Possible raw SSN/tax id outside the restricted zone: {short(c['c'])}",
                        f"Named like an SSN or tax id, in {t.split('.')[1]}, which nobody is denied. "
                        + ("Production hashes it downstream, so the business treats it as sensitive; check that a column "
                           "policy tag protects it here (tags are not in the catalog snapshot)."
                           if prot else f"Never hashed anywhere in the log; {'read by ' + ', '.join(sorted(readers[c['c']])) if readers.get(c['c']) else 'not read in the window'}."),
                        [{"id": c["c"], "label": "Column", "role": "subject"}], evidence={"hashed_downstream": prot})

    # properties the question-answering tools read (M6): what is restricted, sensitive, or a hash
    G.run("MATCH (d:Dataset) SET d.restricted = d.id IN $ds", ds=sorted(denied))
    # a hash: the output of a hash function in lineage, carried on by passthroughs and renames;
    # or, with no lineage, a column named as one (a feed that arrives hashed)
    hash_out = {f["b"] for f in flows if set(f["fns"] or []) & HASH_FNS}
    stack = list(hash_out)
    while stack:
        for f in down.get(stack.pop(), []):
            if f["b"] not in hash_out and set(f["kinds"]) <= {"passthrough", "rename"}:
                hash_out.add(f["b"])
                stack.append(f["b"])
    by_name = {c["c"] for t in tables for c in tcols[t] if re.search(r"(?i)(^|_)hash(ed)?($|_)", c["name"])} - hash_out
    G.run("""MATCH (c:Column) SET c.sensitive = c.id IN $s, c.hashed = c.id IN $h OR c.id IN $n,
             c.hash_evidence = CASE WHEN c.id IN $h THEN 'lineage' WHEN c.id IN $n THEN 'name' END""",
          s=sorted(sensitive | {c["c"] for t in tables for c in tcols[t] if PII_NAME.search(c["name"])}),
          h=sorted(hash_out), n=sorted(by_name))

    # ---------------------------------------------------------------- write
    G.batch("Finding", """UNWIND $rows AS r CREATE (f:Finding {id: r.id, kind: r.kind, title: r.title, summary: r.summary,
        cost_bytes: r.cost_bytes, evidence: r.evidence})""", [{k: v for k, v in f.items() if k != "about"} for f in findings])
    about = [{"f": f["id"], "id": a["id"], "role": a["role"], "label": a["label"]} for f in findings for a in f["about"]]
    for lab in ("Table", "Column"):
        G.batch(f"ABOUT {lab}", f"""UNWIND $rows AS r MATCH (f:Finding {{id: r.f}}), (x:{lab} {{id: r.id}})
            MERGE (f)-[a:ABOUT]->(x) SET a.role = r.role""", [a for a in about if a["label"] == lab])
    report(G, subjects, members, layer, findings, vname, restricted, denied)
    print(f"layers {dict(Counter(layer.values()))}; {len(subjects)} subjects "
          f"({sum(1 for s in subjects.values() if s['kind'] == 'subject')} clustered, "
          f"{sum(1 for s in subjects.values() if s['kind'] == 'entity')} entity, "
          f"{sum(1 for s in subjects.values() if s['kind'] == 'solo')} solo); baseline with hubs: "
          f"{len(set(base.values()))} communities; copies {len(copies)}; restricted datasets {sorted(d.split('.')[1] for d in denied)}")
    print(f"findings {dict(Counter(f['kind'] for f in findings))}")
    G.close()
    return 0


def report(G, subjects, members, layer, findings, vname, restricted, denied):
    L = ["# Topology: layers, subjects, copies, sensitive data", "", "Generated by pipeline/topology.py.", "",
         f"Restricted datasets (people are denied access): {', '.join(sorted(d.split('.')[1] for d in denied))}.", "",
         "## Subjects", "", "Hub variables link subjects; they do not decide membership (D7).", ""]
    keyed = defaultdict(list)
    for r in G.rows("""MATCH (s:Subject)-[k:KEYED_BY]->(v:Variable) RETURN s.id AS s, v.name AS v, k.tables AS n
                       ORDER BY n DESC"""):
        keyed[r["s"]].append(f"{r['v']} ({r['n']})")
    for sid, s in sorted(subjects.items(), key=lambda kv: (kv[1]["kind"] != "entity", -kv[1]["size"])):
        if s["kind"] == "solo":
            continue
        ts = sorted(members[sid])
        L.append(f"- **{s['name']}** ({s['kind']}, {len(ts)} tables; keyed by {', '.join(keyed[sid][:4]) or 'no hub'}): "
                 + ", ".join(f"{t.split('.', 1)[1]} [{layer.get(t, '?')}]" for t in ts[:14]) + (" ..." if len(ts) > 14 else ""))
    solos = [sid for sid, s in subjects.items() if s["kind"] == "solo"]
    L += ["", f"{len(solos)} tables share no non-hub variable with any other table (their own subject).", ""]
    for kind in ("copy_chain", "pii_exposure", "pii_candidate"):
        items = [f for f in findings if f["kind"] == kind]
        if items:
            L += [f"## {kind} ({len(items)})", ""] + [f"- **{f['title']}**. {f['summary']}" for f in items] + [""]
    (WORK / "TOPOLOGY.md").write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20"]
# ///
"""Stages 5b/5c: variables, join confidence, identity, units and competing measures.

A Variable is one real-world thing that one or more columns identify or measure. Two
columns are the same variable when the business treats them as interchangeable: it
joins them, or passes one straight into the other (lineage passthrough or rename).
Nothing is discounted for being common: `customer_key` joined across 28 tables is the
strongest identity evidence there is.

Join confidence comes from usage, never from a designed model:

  production    made by a production author: a dbt model, a BI model, a scheduled pipeline
  corroborated  made by two or more people independently, and contradicted by nothing
  single        made by one person, contradicted by nothing
  suspect       joins two id spaces that production keeps apart. Production never makes
                it; the finding names the bridge production uses instead.

Suspect joins stay in the graph with their evidence; they just do not merge variables.

Writes:
  (:Column)-[:IS]->(:Variable {name, role, hub, ...})
  (:Variable)-[:IDENTIFIES]->(:Entity)                identifier variables of one entity
  (:Variable)-[:LINKED_VIA {table}]->(:Variable)      id spaces linked through a table
  JoinKey.confidence / .confidence_reason
  (:Finding) kinds: suspect_join, homonym, synonym, identity_map, hub, unit_mismatch,
                    competing_measures, limits

Usage: uv run pipeline/variables.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
TIME_TYPES = ("DATE", "TIMESTAMP", "DATETIME", "TIME")
PRODUCTION_AUTHORS = {"dbt_model", "bi_model"}


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)

    def groups(self):
        g = defaultdict(set)
        for x in self.p:
            g[self.find(x)].add(x)
        return g


# Functions that keep a value's identity: format changes, and aggregates that return one
# of their inputs (MAX(user_id) is still a user id). CONCAT('DEP-', id) or SHA256(id) is
# a new id space; MAX(balance) is a different measure.
FORMAT_FNS = {"TRIM", "LTRIM", "RTRIM", "LPAD", "RPAD", "UPPER", "LOWER"}
PICK_FNS = {"MAX", "MIN", "ANY_VALUE", "ARRAY_AGG", "BRACKET", "SAFE_OFFSET", "OFFSET"}
NUMERIC = ("INT64", "NUMERIC", "BIGNUMERIC", "FLOAT64")


def keeps_identity(f: dict, cols: dict, joined: set | None = None) -> bool:
    kinds, fns = set(f["kinds"]), set(f["fns"] or [])
    if f.get("control"):            # ORDER BY t in ARRAY_AGG(x ORDER BY t): t picks the row, it is not the value
        return False
    if kinds <= {"passthrough", "rename"}:
        return True
    fns = {x for x in fns if not x.startswith(("CAST<", "SAFE_CAST<"))}
    if not fns or not fns <= FORMAT_FNS | PICK_FNS:
        return False
    if fns & PICK_FNS:
        src = cols.get(f["a"], {})
        # MAX of a number is a new measure unless the number is used as a key
        if (src.get("type") or "").upper().startswith(NUMERIC) and not (joined and f["a"] in joined):
            return False
    return True


def short(c: str) -> str:
    return ".".join(c.split(".")[1:])


def main() -> int:
    G = Graph()
    for label in ("Variable", "Entity"):
        G.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")
    G.auto("MATCH (n) WHERE n:Variable OR n:Entity CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 5000 ROWS")
    G.auto("""MATCH (f:Finding) WHERE f.kind IN ['suspect_join', 'homonym', 'synonym', 'identity_map', 'hub',
              'unit_mismatch', 'competing_measures', 'limits'] CALL (f) { DETACH DELETE f } IN TRANSACTIONS OF 5000 ROWS""")
    findings = []

    def finding(kind, fid, title, summary, about, evidence=None):
        findings.append({"id": f"{kind}:{fid}", "kind": kind, "title": title, "summary": summary, "cost_bytes": 0,
                         "evidence": json.dumps(evidence or {}, default=str), "about": about})

    cols = {r["c"]["id"]: r["c"] for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)
        RETURN c {.id, .name, .type, table: t.id, table_kind: t.kind, dataset: split(t.id, '.')[1]} AS c""")}
    # every join key with its authors and runners
    jk = G.rows("""
        MATCH (k:JoinKey)-[:ON {side: 'left'}]->(l:Column), (k)-[:ON {side: 'right'}]->(r:Column)
        MATCH (s:QueryShape {succeeded: true})-[u:USES_JOIN]->(k)
        OPTIONAL MATCH (a:Author)-[:AUTHORED]->(s)
        OPTIONAL MATCH (a)-[:RUNS_AS]->(p:Principal)
        OPTIONAL MATCH (s)-[:WRITES]->(w:Table)
        RETURN k.id AS id, l.id AS l, r.id AS r,
               collect(DISTINCT {author: a.id, kind: a.kind, cls: p.class}) AS authors,
               collect(DISTINCT s.id) AS shapes, sum(s.jobs) AS jobs, collect(DISTINCT w.id) AS writes,
               collect(DISTINCT {wraps: u.left_wrap + u.right_wrap, vias: [u.left_via, u.right_via]}) AS uses""")
    def keeps(use):
        """A join equates its columns only if both keys arrive unchanged or reformatted
        (CAST, TRIM, LPAD...). DATE_TRUNC(post_date, MONTH) = month_start relates two
        variables; it does not make them one."""
        fns = {w for w in use["wraps"] if not w.startswith(("CAST<", "SAFE_CAST<"))}
        return fns <= FORMAT_FNS and set(use["vias"]) <= {"direct", "passthrough", "rename", "unnest"}

    for k in jk:
        k["identity"] = any(keeps(u) for u in k["uses"])
        k["production"] = any(a["kind"] in PRODUCTION_AUTHORS or (a["kind"] == "service" and a["cls"] == "transformation")
                              for a in k["authors"])
        k["people"] = sorted({a["author"] for a in k["authors"] if a["kind"] == "person"})
    flows = G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column)
                      RETURN a.id AS a, b.id AS b, f.kinds AS kinds, f.fns AS fns, f.shapes AS shapes,
                             f.control AS control""")
    same_flow = [(f["a"], f["b"]) for f in flows if keeps_identity(f, cols)]

    # -------------------------------------------- id spaces and join confidence
    # Every join is judged against everything else the business does - production and the
    # people's joins accepted so far - but never against itself (leave-one-out), iterated
    # until stable. An id space is "established" when some accepted join keys on it.
    table_cols = defaultdict(set)
    for c, m in cols.items():
        table_cols[m["table"]].add(c)
    human = [k for k in jk if not k["production"] and k["l"] != k["r"]]
    prod = [k for k in jk if k["production"] and k["l"] != k["r"]]
    prod_joined = {c for k in prod for c in (k["l"], k["r"])}

    def world(accepted):
        D = DSU()
        for a, b in same_flow:
            D.union(a, b)
        for k in accepted:
            if k["identity"]:
                D.union(k["l"], k["r"])
        est = {D.find(c) for k in accepted for c in (k["l"], k["r"])}
        homes = defaultdict(set)
        for root, members in D.groups().items():
            if root in est:
                for c in members:
                    homes[cols.get(c, {}).get("name", c.rsplit(".", 1)[-1]).lower()].add(root)
        return D, est, homes

    def judge(k, D, est, homes):
        def spaces(c):
            r = D.find(c)
            if r in est:
                return {r}, "usage"
            h = homes.get(cols.get(c, {}).get("name", "").lower(), set())
            return (set(h), "name") if h else (set(), None)

        def bridges(ra, rb):
            """Tables production joins through that hold both id spaces as separate columns."""
            out = Counter()
            for pk in prod:
                for c in (pk["l"], pk["r"]):
                    t = cols.get(c, {}).get("table")
                    if t and {ra, rb} <= {D.find(x) for x in table_cols[t]}:
                        out[t] += 1
            return [t for t, _ in out.most_common(3)]

        (A, ha), (B, hb) = spaces(k["l"]), spaces(k["r"])
        if A and B and not (A & B):
            for a in A:
                for b in B:
                    via = bridges(a, b)
                    if via:
                        return a, b, via, ("name" if "name" in (ha, hb) else "usage")
        return None

    def label(D, root):
        """Most common column name, plus the source system it comes from when that is known:
        'account_id (core_banking_cdc)' vs 'account_id (card_processor)'."""
        members = [c for c in cols if D.find(c) == root]
        names = Counter(cols[c]["name"].lower() for c in members)
        raw = Counter(cols[c]["dataset"] for c in members
                      if c.startswith("fennmoor-raw.") and "fivetran_staging" not in c) if False else Counter(
            cols[c]["dataset"] for c in members if cols[c]["table_kind"] in ("table", "wildcard")
            and not cols[c]["dataset"].startswith(("dw_", "sbx_", "fivetran", "looker", "legacy", "reverse")))
        name = names.most_common(1)[0][0] if names else root.rsplit(".", 1)[-1]
        return f"{name} ({raw.most_common(1)[0][0]})" if raw else name

    # First pass against production alone, so wrong joins cannot vouch for each other; later
    # passes add the people's joins that survived, which places columns production never touches.
    suspect = {}
    for i in range(5):
        accepted = prod if i == 0 else prod + [k for k in human if k["id"] not in suspect]
        new = {}
        for k in human:
            D, est, homes = world([x for x in accepted if x is not k])
            hit = judge(k, D, est, homes)
            if hit:
                a, b, via, how = hit
                new[k["id"]] = (label(D, a), label(D, b), via, how)
        if i > 0 and new.keys() == suspect.keys():
            break
        suspect = new

    conf = {}
    for k in jk:
        if k["l"] == k["r"]:
            conf[k["id"]] = ("self", "the same column on both sides - says nothing about identity")
        elif k["production"]:
            kinds = sorted({a["kind"] for a in k["authors"] if a["kind"] in PRODUCTION_AUTHORS} or {"pipeline"})
            conf[k["id"]] = ("production", f"made by {', '.join(kinds)}")
        elif k["id"] in suspect:
            la, lb, via, how = suspect[k["id"]]
            conf[k["id"]] = ("suspect", f"joins the {la} id space to the {lb} id space. Production keeps them as "
                                        f"separate columns and translates between them through "
                                        f"{', '.join(short(t) for t in via)}"
                                        + (" (one side placed by its column name)" if how == "name" else ""))
            k["bridge"], k["spaces"], k["how"] = via, (la, lb), how
        elif len(k["people"]) >= 2:
            conf[k["id"]] = ("corroborated", f"{len(k['people'])} people made it independently")
        else:
            conf[k["id"]] = ("single", "one person's join, contradicted by nothing")
    G.batch("JoinKey.confidence", """UNWIND $rows AS r MATCH (k:JoinKey {id: r.id})
        SET k.confidence = r.c, k.confidence_reason = r.why, k.production = r.prod, k.people = r.people,
            k.identity = r.identity""",
            [{"id": k["id"], "c": conf[k["id"]][0], "why": conf[k["id"]][1], "prod": k["production"],
              "people": len(k["people"]), "identity": k["identity"]} for k in jk])
    for k in jk:
        if conf[k["id"]][0] != "suspect":
            continue
        who = sorted({a["author"].split(":", 1)[1].split("@")[0] for a in k["authors"] if a["author"]})
        finding("suspect_join", k["id"], f"Suspect join: {short(k['l'])} = {short(k['r'])}",
                f"{conf[k['id']][1]}. Made by {', '.join(who)} in {len(k['shapes'])} statement shapes ({k['jobs']:,} jobs)"
                + (f", which build {', '.join(short(w) for w in k['writes'])}" if k["writes"] else "") + ".",
                [{"id": k["l"], "label": "Column", "role": "side"}, {"id": k["r"], "label": "Column", "role": "side"}]
                + [{"id": s, "label": "QueryShape", "role": "statement"} for s in k["shapes"]]
                + [{"id": w, "label": "Table", "role": "built_by_it"} for w in k["writes"]]
                + [{"id": t, "label": "Table", "role": "bridge"} for t in k.get("bridge", [])],
                evidence={"spaces": k.get("spaces"), "bridge": k.get("bridge"), "placed_by": k.get("how"),
                          "authors": who})

    # ---------------------------------------------------------- variables
    used = {r["c"] for r in G.rows("""MATCH (c:Column) WHERE (c)<-[:READS|FILTERS|ON]-() OR (c)-[:FLOWS]-()
                                      RETURN c.id AS c""")}
    V = DSU()
    for c in used:
        V.find(c)
    for a, b in same_flow:
        V.union(a, b)
    for k in jk:
        if conf[k["id"]][0] in ("production", "corroborated", "single") and k["identity"]:
            V.union(k["l"], k["r"])
    groups = V.groups()
    reads = defaultdict(lambda: {"roles": Counter(), "agg": Counter()})
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[x:READS]->(c:Column)
                       RETURN c.id AS c, x.roles AS roles, x.agg AS agg, s.jobs AS jobs"""):
        for role in r["roles"]:
            reads[r["c"]]["roles"][role] += r["jobs"] or 1
        for a in r["agg"]:
            reads[r["c"]]["agg"][a] += r["jobs"] or 1
    joined = {c for k in jk if conf[k["id"]][0] != "self" for c in (k["l"], k["r"])}
    merge_keys = {f"{r['t']}.{mk}" for r in G.rows("MATCH (:QueryShape)-[w:WRITES]->(t:Table) "
                                                  "RETURN t.id AS t, w.merge_keys AS mk") for mk in r["mk"] or []}

    def role_of(members):
        types = [(cols.get(c, {}).get("type") or "").upper() for c in members]
        if sum(t.startswith(TIME_TYPES) for t in types) > len(types) / 2:
            return "time"
        if members & (joined | merge_keys):
            return "identifier"
        agg = sum((reads[c]["agg"] for c in members), Counter())
        roles = sum((reads[c]["roles"] for c in members), Counter())
        if sum(v for a, v in agg.items() if a in ("SUM", "AVG", "MAX", "MIN", "SAFE_DIVIDE")) > 0:
            return "measure"
        if roles["group"] or roles["filter"]:
            return "category"
        return "attribute"

    variables, member_of, groups_by_vid = {}, {}, {}
    join_count = Counter()
    for k in jk:
        if conf[k["id"]][0] in ("production", "corroborated", "single") and k["identity"]:
            join_count[k["l"]] += 1
            join_count[k["r"]] += 1
    for root, members in groups.items():
        known = [c for c in members if c in cols]
        if not known:
            continue
        names = Counter(cols[c]["name"].lower() for c in known)
        # named after its home column - the one most joined to (dim_date.date_day) - else the commonest spelling
        home_col = max(known, key=lambda c: (join_count.get(c, 0), cols[c]["table_kind"] != "view"))
        name = cols[home_col]["name"].lower() if join_count.get(home_col) else \
            sorted(names.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))[0][0]
        vid = f"var:{root}"          # stable: rooted at the smallest member column id
        tables = {cols[c]["table"] for c in known}
        datasets = {cols[c]["dataset"] for c in known}
        variables[vid] = {"id": vid, "name": name, "role": role_of(set(known)), "size": len(known),
                          "names": sorted(names), "tables": len(tables), "datasets": len(datasets),
                          "members": sorted(known)}
        for c in known:
            member_of[c] = vid
        groups_by_vid[vid] = known
    # hubs: keys used across teams, not just across layers of one pipeline. A hub links
    # subject areas; conversation_id, joined in six tables but only by the contact-center
    # team, is that area's own key.
    joined_tables = defaultdict(set)
    for k in jk:
        if conf[k["id"]][0] in ("production", "corroborated", "single"):
            for c in (k["l"], k["r"]):
                if c in cols:
                    joined_tables[c].add(cols[c]["table"])
    team_tables = defaultdict(set)
    for r in G.rows("""MATCH (t:Team)<-[:MEMBER_OF]-(:Principal)-[:CONSUMES]->(tb:Table) RETURN t.id AS team, tb.id AS t"""):
        team_tables[r["t"]].add(r["team"])
    n_teams = len({t for ts in team_tables.values() for t in ts}) or 1
    for vid, v in variables.items():
        ms = [c for c in groups_by_vid[vid]]
        jt = {t for c in ms for t in joined_tables.get(c, ())}
        teams = {tm for c in ms for tm in team_tables.get(cols[c]["table"], ())}
        v["joined_tables"], v["team_breadth"] = len(jt), len(teams)
        v["hub"] = v["role"] in ("identifier", "time") and len(jt) >= 5 and len(teams) >= max(3, n_teams // 2)

    # ------------------------------------------------ homonyms and synonyms
    by_name = defaultdict(set)
    for vid, v in variables.items():
        if v["role"] == "identifier":
            for c in v["members"]:
                by_name[cols[c]["name"].lower()].add(vid)
    est_vars = {member_of[c] for c in prod_joined if c in member_of}
    for nm, vids in sorted(by_name.items()):
        big = [v for v in vids if v in est_vars]
        if len(big) >= 2:
            desc = "; ".join(f"{variables[v]['name']} ({variables[v]['size']} columns: "
                             f"{', '.join(short(c) for c in variables[v]['members'] if cols[c]['name'].lower() == nm)[:160]})"
                             for v in big)
            finding("homonym", nm, f"'{nm}' names {len(big)} different identifiers",
                    f"Columns called {nm} belong to {len(big)} identifiers that production keys on separately: {desc}. "
                    f"Matching on the name would merge them.",
                    [{"id": v, "label": "Variable", "role": "meaning"} for v in big], evidence={"variables": big})
    for vid, v in variables.items():
        if v["role"] == "identifier" and len(v["names"]) >= 4:
            finding("synonym", vid, f"One identifier, {len(v['names'])} spellings: {v['name']}",
                    f"{v['size']} columns across {v['tables']} tables and {v['datasets']} datasets are the same "
                    f"identifier by usage (joined or passed through): {', '.join(v['names'][:16])}"
                    + (" ..." if len(v["names"]) > 16 else "") + ".",
                    [{"id": vid, "label": "Variable", "role": "subject"}], evidence={"names": v["names"]})
    hubs = sorted((v for v in variables.values() if v["hub"]), key=lambda v: -v["joined_tables"])
    if hubs:
        finding("hub", "estate", f"{len(hubs)} hub variables connect the estate",
                "Joined across many tables by most teams, so they link subject areas rather than define them: "
                + "; ".join(f"{v['name']} ({v['role']}; joined in {v['joined_tables']} tables; used by "
                            f"{v['team_breadth']} of {n_teams} teams)" for v in hubs[:12]),
                [{"id": v["id"], "label": "Variable", "role": "hub"} for v in hubs], evidence={"hubs": [v["id"] for v in hubs]})

    # ---------------------------------------------- identity: entities
    idvars = {vid for vid, v in variables.items() if v["role"] == "identifier"}
    join_partners = Counter()
    for k in jk:
        if conf[k["id"]][0] not in ("suspect", "self"):
            join_partners[k["l"]] += 1
            join_partners[k["r"]] += 1
    home = {}
    for vid in idvars:
        ms = variables[vid]["members"]
        best = max(ms, key=lambda c: (join_partners[c], cols[c]["table_kind"] != "view"))
        if join_partners[best]:
            home[vid] = cols[best]["table"]
    # what is read from each table, by role, in consumption
    read_cols = defaultdict(set)
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[:READS]->(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       WHERE s.purpose IN ['adhoc', 'bi', 'extract', 'ml_read', 'build'] RETURN t.id AS t, c.id AS c"""):
        read_cols[r["t"]].add(r["c"])
    E = DSU()
    links = []
    for vid in idvars:
        E.find(vid)
    by_home = defaultdict(set)
    for vid, t in home.items():
        by_home[t].add(vid)
    for t, vids in by_home.items():            # two identifiers homed in one table name one thing
        vids = sorted(vids)
        for a, b in zip(vids, vids[1:]):
            E.union(a, b)
            links.append((a, b, t, "home"))
    # Same entity (merged): two ids homed in one dimension (above), or a table built keyed
    # on one id that picks the others per key - GROUP BY cif_number with ANY_VALUE(contact_id),
    # ARRAY_AGG(olb_user_id): a mapping by construction.
    group_vars = defaultdict(set)          # build shape -> identifier variables it groups by
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true, purpose: 'build'})-[x:READS]->(c:Column)
                       WHERE 'group' IN x.roles RETURN s.id AS s, c.id AS c"""):
        if member_of.get(r["c"]) in idvars:
            group_vars[r["s"]].add(member_of[r["c"]])
    # ...and only a table whose output is mostly ids carried per key: int_customer_identity is;
    # int_calls_enriched (grouped by conversation_id, picking each call's agent and customer,
    # but mostly durations and flags) is a fact that references other entities.
    out_cols = defaultdict(dict)                 # table -> column -> is an id carried per key
    for f in flows:
        tv = member_of.get(f["b"])
        carried = tv in idvars or bool(set(f["fns"] or []) & PICK_FNS)
        out_cols[cols.get(f["b"], {}).get("table")][f["b"]] = out_cols[cols.get(f["b"], {}).get("table")].get(
            f["b"], False) or carried
    is_mapping = {t: sum(v.values()) / len(v) >= 0.6 for t, v in out_cols.items() if t and v}
    for f in flows:
        tv = member_of.get(f["b"])
        if tv not in idvars or f.get("control") or not set(f["fns"] or []) & PICK_FNS:
            continue
        if not is_mapping.get(cols.get(f["b"], {}).get("table")):
            continue
        for s_ in f["shapes"] or []:
            for gv in group_vars.get(s_, ()):
                if gv != tv:
                    E.union(gv, tv)
                    links.append((gv, tv, cols[f["b"]]["table"], "mapping"))
    # Linked (not merged): a pure translation hop - a statement joins into a table on one id
    # space and carries out another, reading nothing else from it. That is a crosswalk or an
    # association table (cases <-> alerts); telling them apart needs cardinality, which the
    # log does not show, so hops are reported as links only.
    hop = defaultdict(lambda: {"shapes": set(), "production": 0})
    shape_reads = defaultdict(lambda: defaultdict(set))
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[x:READS]->(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       RETURN s.id AS s, t.id AS t, c.id AS c, x.roles AS roles"""):
        shape_reads[r["s"]][r["t"]].add((r["c"], tuple(sorted(r["roles"]))))
    prod_shapes = {s_ for k in jk if k["production"] for s_ in k["shapes"]}
    for k in jk:
        if conf[k["id"]][0] in ("suspect", "self"):
            continue
        for s_ in k["shapes"]:
            for t, rd in shape_reads[s_].items():
                ids = {(member_of.get(c), roles) for c, roles in rd if member_of.get(c) in idvars}
                non_id = [c for c, roles in rd if member_of.get(c) not in idvars]
                joined_in = {v for v, roles in ids if "join" in roles}
                carried = {v for v, roles in ids if set(roles) - {"join"}}
                if joined_in and (joined_in | carried) != joined_in and not non_id:
                    e = hop[(t, tuple(sorted(joined_in | carried)))]
                    e["shapes"].add(s_)
                    e["production"] += s_ in prod_shapes
    for (t, keys), e in hop.items():
        if e["production"] or len(e["shapes"]) >= 2:
            for a, b in zip(keys, keys[1:]):
                links.append((a, b, t, "hop"))
    entities = {}
    for root, vids in E.groups().items():
        if len(vids) < 2:
            continue
        top = max(vids, key=lambda v: variables[v]["tables"])
        entities[f"entity:{root}"] = {"id": f"entity:{root}", "name": variables[top]["name"],
                                      "identifiers": sorted(vids), "anchor": top}
    for eid, e in entities.items():
        ids = set(e["identifiers"])
        anchor = e["anchor"]
        same = [(a, b, t, h) for a, b, t, h in links if h in ("home", "mapping") and (a in ids or b in ids)]
        # hops inside the entity, or out to an id space that is not itself a hub
        hopped = [(a, b, t, h) for a, b, t, h in links if h == "hop" and (a in ids or b in ids) and a != b
                  and all(x in ids or not variables[x]["hub"] for x in (a, b))]
        outside = sorted({x for a, b, t, h in hopped for x in (a, b) if x not in ids})
        xw = sorted({t for a, b, t, h in same if h == "mapping"} | {t for a, b, t, h in hopped})
        vname = lambda v: variables[v]["name"]
        finding("identity_map", eid, f"Identity: {len(ids)} id spaces for {vname(anchor)}",
                f"One entity, anchored on {vname(anchor)} ({variables[anchor]['tables']} tables): "
                f"{', '.join(vname(v) for v in sorted(ids, key=vname))}. Same entity because "
                + "; ".join(sorted({f"{vname(a)} and {vname(b)} " + ("share the dimension " if h == 'home' else
                                    "are mapped per key in ") + short(t) for a, b, t, h in same}))
                + (". Also linked through translation hops (a crosswalk or an association table; the "
                   "cardinality that would tell them apart is not in the log): "
                   + "; ".join(sorted({f"{vname(a)} <-> {vname(b)} via {short(t)}" for a, b, t, h in hopped}))
                   if hopped else "") + ".",
                [{"id": v, "label": "Variable", "role": "identifier"} for v in ids]
                + [{"id": v, "label": "Variable", "role": "linked"} for v in outside]
                + [{"id": t, "label": "Table", "role": "crosswalk"} for t in xw],
                evidence={"anchor": anchor, "identifiers": sorted(ids), "linked": outside, "crosswalks": xw,
                          "links": [(a, b, t, h) for a, b, t, h in same + hopped]})

    # --------------------------------------------------------- units
    up = defaultdict(list)
    for f in flows:
        up[f["b"]].append(f)
    UNIT_USD = re.compile(r"(?i)(_usd|usd_|dollars?|_amt$|_amount$)")
    UNIT_CENTS = re.compile(r"(?i)cents?")
    for c, m in cols.items():
        if not UNIT_USD.search(m["name"]) or UNIT_CENTS.search(m["name"]):
            continue
        stack, seen = [(c, [])], set()
        while stack:
            cur, fns = stack.pop()
            for f in up.get(cur, []):
                if (f["a"], cur) in seen:
                    continue
                seen.add((f["a"], cur))
                path_fns = fns + list(f["fns"] or [])
                src = cols.get(f["a"], {})
                if UNIT_CENTS.search(src.get("name", "")):
                    scaled = any(x in ("/100", "/100.0", "*0.01", "/ 100") for x in path_fns)
                    if not scaled:
                        finding("unit_mismatch", c, f"Named in dollars, computed from cents: {short(c)}",
                                f"{short(c)} comes from {short(f['a'])} through {', '.join(dict.fromkeys(path_fns)) or 'a copy'}"
                                f" with no division by 100, so it is 100x any dollar figure it is compared with.",
                                [{"id": c, "label": "Column", "role": "subject"},
                                 {"id": f["a"], "label": "Column", "role": "source"}],
                                evidence={"source": f["a"], "fns": path_fns})
                else:
                    stack.append((f["a"], path_fns))

    # -------------------------------------------- competing measures
    comp = G.rows("""MATCH (a:Column)-[x:COMPARED]->(b:Column) RETURN a.id AS a, b.id AS b, x.ops AS ops, x.shapes AS shapes""")
    C = DSU()
    for r in comp:
        if not set(r["ops"]) & {"CORR", "COVARPOP", "COVARSAMP"}:
            continue            # a - b combines complementary measures (debit - credit); it is not a comparison
        va, vb = member_of.get(r["a"]), member_of.get(r["b"])
        if va and vb and va != vb and variables[va]["role"] not in ("identifier", "time") \
                and variables[vb]["role"] not in ("identifier", "time"):
            C.union(va, vb)
    consumers = {r["c"]: r for r in G.rows("""MATCH (p:Principal)-[x:RAN]->(s:QueryShape {succeeded: true})-[:READS]->(c:Column)
        WHERE s.purpose IN ['adhoc', 'bi', 'extract', 'ml_read', 'build']
        RETURN c.id AS c, count(DISTINCT p) AS principals, collect(DISTINCT p.class) AS classes""")}
    for root, vids in C.groups().items():
        if len(vids) < 2:
            continue

        def reach(v):
            ps = [consumers[c] for c in variables[v]["members"] if c in consumers]
            return (sum(p["principals"] for p in ps),
                    any(cl in ("bi_service", "transformation") for p in ps for cl in p["classes"]))
        ranked = sorted(vids, key=lambda v: (not reach(v)[1], -reach(v)[0]))
        best = ranked[0]
        finding("competing_measures", root, f"Competing measures: {' vs '.join(variables[v]['name'] for v in ranked)}",
                f"People correlate these with each other, so they are alternatives for the same "
                f"thing, each with its own lineage: "
                + "; ".join(f"{variables[v]['name']} ({', '.join(short(c) for c in variables[v]['members'][:4])}; "
                            f"{reach(v)[0]} consumers{', used by production/BI' if reach(v)[1] else ''})" for v in ranked)
                + f". The sanctioned one, by usage: {variables[best]['name']}.",
                [{"id": v, "label": "Variable", "role": "sanctioned" if v == best else "alternative"} for v in ranked],
                evidence={"ranked": ranked})

    # ---------------------------------------------------------- limits
    finding("limits", "profiling", "Not determinable from usage: data-level breakage",
            "A column that silently went null, a code that changed meaning without changing value, or a sum that "
            "double-counts because of how a ledger is structured, leave no trace in query text. Queries keep "
            "running unchanged. These need data profiling or domain knowledge; this pipeline does not guess at them.",
            [], evidence={})

    # ---------------------------------------------------------- write
    G.batch("Variable", """UNWIND $rows AS r CREATE (v:Variable) SET v = r""",
            [{k: v for k, v in x.items() if k != "members"} for x in variables.values()])
    G.batch("IS", """UNWIND $rows AS r MATCH (c:Column {id: r.c}), (v:Variable {id: r.v}) MERGE (c)-[:IS]->(v)""",
            [{"c": c, "v": v} for c, v in member_of.items()])
    G.batch("Entity", """UNWIND $rows AS r CREATE (e:Entity {id: r.id, name: r.name, anchor: r.anchor})
        WITH e, r UNWIND r.identifiers AS vid MATCH (v:Variable {id: vid}) MERGE (v)-[:IDENTIFIES]->(e)""",
            list(entities.values()))
    G.batch("LINKED_VIA", """UNWIND $rows AS r MATCH (a:Variable {id: r.a}), (b:Variable {id: r.b})
        MERGE (a)-[x:LINKED_VIA {table: r.t}]->(b) SET x.how = r.how""",
            [{"a": a, "b": b, "t": t, "how": h} for a, b, t, h in links])
    G.batch("Finding", """UNWIND $rows AS r CREATE (f:Finding {id: r.id, kind: r.kind, title: r.title, summary: r.summary,
        cost_bytes: r.cost_bytes, evidence: r.evidence})""", [{k: v for k, v in f.items() if k != "about"} for f in findings])
    about = [{"f": f["id"], "id": a["id"], "role": a["role"], "label": a["label"]} for f in findings for a in f["about"]]
    for lab in ("Table", "Column", "Variable", "QueryShape"):
        G.batch(f"ABOUT {lab}", f"""UNWIND $rows AS r MATCH (f:Finding {{id: r.f}}), (x:{lab} {{id: r.id}})
            MERGE (f)-[a:ABOUT]->(x) SET a.role = r.role""", [a for a in about if a["label"] == lab])

    roles = Counter(v["role"] for v in variables.values())
    confs = Counter(c for c, _ in conf.values())
    print(f"{len(variables)} variables {dict(roles)}; {sum(v['hub'] for v in variables.values())} hubs; "
          f"{len(entities)} entities; joins {dict(confs)}")
    print(f"findings {dict(Counter(f['kind'] for f in findings))}")
    report(findings)
    G.close()
    return 0


def report(findings):
    order = ["suspect_join", "homonym", "synonym", "identity_map", "hub", "unit_mismatch", "competing_measures", "limits"]
    L = ["# Variables, joins and identity", "", "Generated by pipeline/variables.py.", ""]
    for kind in order:
        items = [f for f in findings if f["kind"] == kind]
        if items:
            L += [f"## {kind} ({len(items)})", ""] + [f"- **{f['title']}**. {f['summary']}" for f in items] + [""]
    (WORK / "VARIABLES.md").write_text("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())

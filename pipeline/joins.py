"""Join confidence: which of the joins in the log say that two columns hold the same thing.

Every JoinKey gets, as properties (no new nodes):

  identity    true if some query joins the two keys unchanged, reformatted (CAST, TRIM, LPAD,
              LOWER...) or picked out of an aggregate (ARRAY_AGG(id ...)[OFFSET(0)], MAX(id)). DATE_TRUNC(post_date, MONTH) = month_start relates two
              variables; it does not make them one.
  production  true if a service account ran it: dbt, Looker, Tableau, a scheduled pipeline
  people      how many different people ran it
  confidence  production | corroborated (2+ people) | single (1 person) | suspect | self
  confidence_reason

  suspect     the join equates two id spaces that production keeps as separate columns of one
              table and translates between (dim_account holds both the core and the card account
              id). Two id spaces that never happened to meet are not separate; separation needs
              that positive evidence. Production never makes a suspect join.

Id spaces come from production's joins plus identity-preserving lineage (a column copied or
renamed into another is the same thing). Each person's join is judged against production and
the other people's joins accepted so far, never against itself, iterated until stable; the
first pass uses production alone, so wrong joins cannot vouch for each other.

Ported from the M3 build (legacy/variables_m3.py), on the bottom layer: production is read
from who ran the query (Principal.kind), not from the old actor model.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from graphdb import Graph

FORMAT_FNS = {"TRIM", "LTRIM", "RTRIM", "LPAD", "RPAD", "UPPER", "LOWER"}
PICK_FNS = {"MAX", "MIN", "ANY_VALUE", "ARRAY_AGG", "BRACKET", "SAFE_OFFSET", "OFFSET"}
NUMERIC = ("INT64", "NUMERIC", "BIGNUMERIC", "FLOAT64")
USABLE = ("production", "corroborated", "single")       # what builds variables


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


def keeps_identity(f: dict, cols: dict) -> bool:
    """Lineage that passes a value through: a copy, a rename, a format change, or an aggregate
    that returns one of its inputs (MAX(user_id) is still a user id; MAX(balance) is a new measure)."""
    kinds, fns = set(f["kinds"]), {x for x in (f["fns"] or []) if not x.startswith(("CAST<", "SAFE_CAST<"))}
    if f.get("control"):
        return False
    if kinds <= {"passthrough", "rename"}:
        return True
    if not fns or not fns <= FORMAT_FNS | PICK_FNS:
        return False
    return not (fns & PICK_FNS and (cols.get(f["a"], {}).get("type") or "").upper().startswith(NUMERIC))


def short(c: str) -> str:
    return c.split(".", 1)[1]


def judge_joins(G: Graph) -> Counter:
    cols = {r["id"]: r for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)
                                          RETURN c.id AS id, c.name AS name, c.type AS type, t.id AS table""")}
    jk = G.rows("""
        MATCH (k:JoinKey)-[:ON {side: 'left'}]->(l:Column), (k)-[:ON {side: 'right'}]->(r:Column)
        MATCH (s:QueryShape {succeeded: true})-[u:USES_JOIN]->(k)
        MATCH (p:Principal)-[:RAN]->(s)
        RETURN k.id AS id, l.id AS l, r.id AS r,
               collect(DISTINCT CASE WHEN p.kind = 'service_account' THEN p.id END) AS services,
               collect(DISTINCT CASE WHEN p.kind <> 'service_account' THEN p.id END) AS people,
               collect(DISTINCT {wraps: u.left_wrap + u.right_wrap, vias: [u.left_via, u.right_via]}) AS uses""")
    for k in jk:
        # a key picked out of an aggregate (ARRAY_AGG(queue_id ...)[OFFSET(0)]) is still that key
        k["identity"] = any({w for w in u["wraps"] if not w.startswith(("CAST<", "SAFE_CAST<"))} <= FORMAT_FNS | PICK_FNS
                            and set(u["vias"]) <= {"direct", "passthrough", "rename", "unnest", "aggregate"}
                            for u in k["uses"])
        k["production"] = bool(k["services"])
    same = [(f["a"], f["b"]) for f in G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column)
        RETURN a.id AS a, b.id AS b, f.kinds AS kinds, f.fns AS fns, f.control AS control""") if keeps_identity(f, cols)]
    table_cols = defaultdict(set)
    for c, m in cols.items():
        table_cols[m["table"]].add(c)
    prod = [k for k in jk if k["production"] and k["l"] != k["r"]]
    human = [k for k in jk if not k["production"] and k["l"] != k["r"]]

    def world(accepted):
        D = DSU()
        for a, b in same:
            D.union(a, b)
        for k in accepted:
            if k["identity"]:
                D.union(k["l"], k["r"])
        est = {D.find(c) for k in accepted for c in (k["l"], k["r"])}
        homes = defaultdict(set)
        for c in list(D.p):
            if D.find(c) in est:
                homes[cols.get(c, {}).get("name", c.rsplit(".", 1)[-1]).lower()].add(D.find(c))
        return D, est, homes

    def judge(k, D, est, homes):
        def spaces(c):
            r = D.find(c)
            if r in est:
                return {r}
            return set(homes.get(cols.get(c, {}).get("name", "").lower(), set()))

        def bridges(ra, rb):
            """Tables production joins through that hold both id spaces as separate columns."""
            out = Counter()
            for pk in prod:
                for c in (pk["l"], pk["r"]):
                    t = cols.get(c, {}).get("table")
                    if t and {ra, rb} <= {D.find(x) for x in table_cols[t]}:
                        out[t] += 1
            return [t for t, _ in out.most_common(3)]
        A, B = spaces(k["l"]), spaces(k["r"])
        if A and B and not A & B:
            for a in A:
                for b in B:
                    via = bridges(a, b)
                    if via:
                        return via
        return None

    suspect = {}
    for i in range(5):
        accepted = prod if i == 0 else prod + [k for k in human if k["id"] not in suspect]
        new = {}
        for k in human:
            D, est, homes = world([x for x in accepted if x is not k])
            via = judge(k, D, est, homes)
            if via:
                new[k["id"]] = via
        if i > 0 and new.keys() == suspect.keys():
            break
        suspect = new

    rows = []
    for k in jk:
        people = [p for p in k["people"] if p]
        if k["l"] == k["r"]:
            c, why = "self", "the same column on both sides: says nothing about identity"
        elif k["production"]:
            c, why = "production", "run by " + ", ".join(sorted(s.split("@")[0] for s in k["services"] if s))
        elif k["id"] in suspect:
            c, why = "suspect", ("equates two id spaces that production keeps as separate columns and translates "
                                 "between, through " + ", ".join(short(t) for t in suspect[k["id"]]))
        elif len(people) >= 2:
            c, why = "corroborated", f"{len(people)} people made it independently"
        else:
            c, why = "single", "one person's join, contradicted by nothing"
        rows.append({"id": k["id"], "c": c, "why": why, "prod": k["production"], "people": len(people),
                     "identity": k["identity"]})
    G.batch("JoinKey.confidence", """UNWIND $rows AS r MATCH (k:JoinKey {id: r.id})
        SET k.confidence = r.c, k.confidence_reason = r.why, k.production = r.prod, k.people = r.people,
            k.identity = r.identity""", rows)
    return Counter(r["c"] for r in rows)

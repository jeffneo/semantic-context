"""Join confidence: which joins in the log say that two columns hold the same thing.

Every JoinKey gets, as properties (no new nodes):

  identity    true if some query joins the two keys unchanged, reformatted (CAST, TRIM, LPAD, LOWER...)
              or picked out of an aggregate (ARRAY_AGG(id ...)[OFFSET(0)], MAX(id)).
              DATE_TRUNC(post_date, MONTH) = month_start relates two variables; it does not make them one.
  production  true if a service account ran it: dbt, a BI tool, a scheduled pipeline
  people      how many different people ran it
  confidence  production | corroborated (2+ people) | single (1 person) | suspect | self
  confidence_reason

  suspect     the join equates two id spaces that production keeps as separate columns of one table and
              translates between (one dimension holds both the core and the card account id). Two id
              spaces that never happened to meet are not separate: separation needs that positive
              evidence. Production never makes a suspect join.

Id spaces come from production's joins plus identity-preserving lineage (a column copied or renamed
into another is the same thing). Each person's join is judged against production and the other
people's joins accepted so far, never against itself, until stable. The first pass uses production
alone, so wrong joins cannot vouch for each other.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from qlsc.graph import Graph
from qlsc.names import short

FORMAT_FNS = {"TRIM", "LTRIM", "RTRIM", "LPAD", "RPAD", "UPPER", "LOWER"}
PICK_FNS = {"MAX", "MIN", "ANY_VALUE", "ARRAY_AGG", "BRACKET", "SAFE_OFFSET", "OFFSET"}
IDENTITY_VIAS = {"direct", "passthrough", "rename", "unnest", "aggregate"}
NUMERIC = ("INT64", "NUMERIC", "BIGNUMERIC", "FLOAT64")
MAX_PASSES = 5


class DSU:
    """Disjoint sets: union-find with path halving."""

    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def uncast(fns) -> set[str]:
    """Functions applied to a key, ignoring type casts."""
    return {f for f in fns or () if not f.startswith(("CAST<", "SAFE_CAST<"))}


def keeps_identity(flow: dict, cols: dict) -> bool:
    """Lineage that passes a value through: a copy, a rename, a format change, or an aggregate that
    returns one of its inputs (MAX(user_id) is still a user id; MAX(balance) is a new measure)."""
    kinds, fns = set(flow["kinds"]), uncast(flow["fns"])
    if flow.get("control"):
        return False
    if kinds <= {"passthrough", "rename"}:
        return True
    if not fns or not fns <= FORMAT_FNS | PICK_FNS:
        return False
    numeric = (cols.get(flow["a"], {}).get("type") or "").upper().startswith(NUMERIC)
    return not (fns & PICK_FNS and numeric)


def joins_identity(uses: list[dict]) -> bool:
    """Some query joins the keys unchanged, reformatted, or picked out of an aggregate."""
    return any(uncast(u["wraps"]) <= FORMAT_FNS | PICK_FNS and set(u["vias"]) <= IDENTITY_VIAS for u in uses)


class IdSpaces:
    """The id spaces a set of accepted joins and identity lineage imply: columns joined or copied into
    one another share a space. Columns no accepted join touches fall back to spaces of the same name."""

    def __init__(self, same: list[tuple[str, str]], accepted: list[dict], cols: dict):
        self.cols = cols
        self.sets = DSU()
        for a, b in same:
            self.sets.union(a, b)
        for k in accepted:
            if k["identity"]:
                self.sets.union(k["l"], k["r"])
        self.established = {self.sets.find(c) for k in accepted for c in (k["l"], k["r"])}
        self.by_name = defaultdict(set)
        for c in list(self.sets.parent):
            if self.sets.find(c) in self.established:
                self.by_name[self.name(c)].add(self.sets.find(c))

    def name(self, column: str) -> str:
        return self.cols.get(column, {}).get("name", column.rsplit(".", 1)[-1]).lower()

    def of(self, column: str) -> set:
        root = self.sets.find(column)
        return {root} if root in self.established else set(self.by_name.get(self.name(column), set()))

    def bridges(self, a, b, production: list[dict], table_cols: dict) -> list[str]:
        """Tables production joins through that hold both id spaces as separate columns."""
        found = Counter()
        for pk in production:
            for c in (pk["l"], pk["r"]):
                t = self.cols.get(c, {}).get("table")
                if t and {a, b} <= {self.sets.find(x) for x in table_cols[t]}:
                    found[t] += 1
        return [t for t, _ in found.most_common(3)]

    def contradicted(self, k: dict, production: list[dict], table_cols: dict) -> list[str] | None:
        """If the join equates two separate id spaces, the tables that keep them apart."""
        left, right = self.of(k["l"]), self.of(k["r"])
        if left and right and not left & right:
            for a in left:
                for b in right:
                    via = self.bridges(a, b, production, table_cols)
                    if via:
                        return via
        return None


def suspects(production, human, same, cols, table_cols) -> dict[str, list[str]]:
    """Each person's join against production and the other accepted people's joins, until stable."""
    found: dict[str, list[str]] = {}
    for i in range(MAX_PASSES):
        accepted = production if i == 0 else production + [k for k in human if k["id"] not in found]
        new = {}
        for k in human:
            spaces = IdSpaces(same, [x for x in accepted if x is not k], cols)
            via = spaces.contradicted(k, production, table_cols)
            if via:
                new[k["id"]] = via
        if i > 0 and new.keys() == found.keys():
            break
        found = new
    return found


def confidence(k: dict, suspect: dict) -> tuple[str, str]:
    people = [p for p in k["people"] if p]
    if k["l"] == k["r"]:
        return "self", "the same column on both sides: says nothing about identity"
    if k["production"]:
        return "production", "run by " + ", ".join(sorted(s.split("@")[0] for s in k["services"] if s))
    if k["id"] in suspect:
        return "suspect", (
            "equates two id spaces that production keeps as separate columns and translates "
            "between, through " + ", ".join(short(t) for t in suspect[k["id"]])
        )
    if len(people) >= 2:
        return "corroborated", f"{len(people)} people made it independently"
    return "single", "one person's join, contradicted by nothing"


def judge_joins(G: Graph) -> Counter:
    cols = {
        r["id"]: r
        for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)
                                          RETURN c.id AS id, c.name AS name, c.type AS type, t.id AS table""")
    }
    keys = G.rows("""
        MATCH (k:JoinKey)-[:ON {side: 'left'}]->(l:Column), (k)-[:ON {side: 'right'}]->(r:Column)
        MATCH (s:QueryShape {succeeded: true})-[u:USES_JOIN]->(k)
        MATCH (p:Principal)-[:RAN]->(s)
        RETURN k.id AS id, l.id AS l, r.id AS r,
               collect(DISTINCT CASE WHEN p.kind = 'service_account' THEN p.id END) AS services,
               collect(DISTINCT CASE WHEN p.kind <> 'service_account' THEN p.id END) AS people,
               collect(DISTINCT {wraps: u.left_wrap + u.right_wrap, vias: [u.left_via, u.right_via]}) AS uses""")
    for k in keys:
        k["identity"] = joins_identity(k["uses"])
        k["production"] = bool(k["services"])
    same = [
        (f["a"], f["b"])
        for f in G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column)
        RETURN a.id AS a, b.id AS b, f.kinds AS kinds, f.fns AS fns, f.control AS control""")
        if keeps_identity(f, cols)
    ]
    table_cols = defaultdict(set)
    for c, m in cols.items():
        table_cols[m["table"]].add(c)
    production = [k for k in keys if k["production"] and k["l"] != k["r"]]
    human = [k for k in keys if not k["production"] and k["l"] != k["r"]]
    suspect = suspects(production, human, same, cols, table_cols)

    rows = []
    for k in keys:
        c, why = confidence(k, suspect)
        rows.append(
            {
                "id": k["id"],
                "c": c,
                "why": why,
                "prod": k["production"],
                "people": len([p for p in k["people"] if p]),
                "identity": k["identity"],
            }
        )
    G.batch(
        "JoinKey.confidence",
        """UNWIND $rows AS r MATCH (k:JoinKey {id: r.id})
        SET k.confidence = r.c, k.confidence_reason = r.why, k.production = r.prod, k.people = r.people,
            k.identity = r.identity""",
        rows,
    )
    return Counter(r["c"] for r in rows)

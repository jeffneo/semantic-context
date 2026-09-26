"""Score the bottom layer against the answer key: parse health, join recovery, column lineage.

  parse health   successful shapes resolved, from the graph itself
  join recovery  column-level JoinKeys vs the joins that actually executed
  lineage        column FLOWS vs the model column lineage of models that actually ran

The keys are usage truth: only statements that ran successfully in the log window count. Join truth
has three independent sources, none of them qlsc's parser:

  declared-model  build/joins.json - joins in model SQL, resolved by generate/build.py
  declared-bi     spec/templates/bi.yaml explore joins, where the executed Looker SQL contains the join line
  reference       a deliberately simple regex extractor over every successful executed statement:
                  `a.x = b.y` in ON, and `USING (x)`, where both aliases name a table directly. It cannot
                  see through CTEs or subqueries, so qlsc joins it does not have are classified, not
                  counted as wrong.

Writes results/bottom_layer.md and .json.
Usage: uv run examples/fennmoor-bank/eval/bottom_layer.py
"""

from __future__ import annotations

import gzip
import json
import re
from collections import defaultdict

import yaml
from common import BUILD, SPEC, Names, build, settings, write_result

from qlsc.graph import Graph
from qlsc.names import short


def pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a.lower(), b.lower())))


# ------------------------------------------------------------ truth: runs


def executed(names: Names):
    """Successful jobs: job_id -> (sql, truth row)."""
    truth = {}
    for line in gzip.open(BUILD / "log" / "jobs_truth.ndjson.gz", "rt"):
        t = json.loads(line)
        truth[t["job_id"]] = t
    ok = {}
    for line in gzip.open(BUILD / "log" / "jobs.ndjson.gz", "rt"):
        j = json.loads(line)
        if j["job_type"] == "QUERY" and j["query"] and not j["error_result"]:
            ok[j["job_id"]] = (j["query"], truth[j["job_id"]], j["project_id"], j["statement_type"])
    return ok


# --------------------------------------------------------- truth: joins

TABLE_REF = re.compile(
    r"(?:FROM|JOIN)\s+((?:`[^`]+`\.?)+|[A-Za-z_]\w*\.[A-Za-z_]\w*\b)(?:\s+(?:AS\s+)?(?!ON\b|USING\b|WHERE\b|LEFT\b|JOIN\b|INNER\b"
    r"|GROUP\b|ORDER\b|CROSS\b|FULL\b|RIGHT\b|LIMIT\b|QUALIFY\b)([A-Za-z_]\w*))?",
    re.I,
)
ON_EQ = re.compile(r"\b([A-Za-z_]\w*)\.`?(\w+)`?\s*=\s*([A-Za-z_]\w*)\.`?(\w+)`?")
USING = re.compile(
    r"JOIN\s+((?:`[^`]+`\.?)+|[A-Za-z_]\w*\.[A-Za-z_]\w*\b)(?:\s+(?:AS\s+)?([A-Za-z_]\w*))?\s+USING\s*\(([^)]+)\)",
    re.I,
)
ON_CLAUSE = re.compile(
    r"\bON\s+(.+?)(?=\b(?:LEFT|RIGHT|INNER|FULL|CROSS|JOIN|WHERE|GROUP|ORDER|QUALIFY|UNION|LIMIT|WHEN)\b|\)\s*(?:,|$|SELECT)|$)",
    re.I | re.S,
)


def unquote(ref: str) -> str:
    return ref.replace("`", "")


def reference_joins(sql: str, names: Names, project: str) -> tuple[set, int]:
    """Direct-table joins in one statement; also returns how many predicates it had to skip."""
    alias = {}
    for m in TABLE_REF.finditer(sql):
        fqn = unquote(m.group(1))
        if fqn.count(".") == 1:
            fqn = f"{project}.{fqn}"  # dataset.table resolves in the job's project
        if fqn.count(".") != 2:
            continue
        a = m.group(2) or fqn.split(".")[-1]
        alias[a.lower()] = names.table(fqn)
    out, skipped = set(), 0
    if re.search(r"\bMERGE\b", sql[:600], re.I):
        return out, 0  # MERGE ... ON is write mechanics, not a join
    for clause in ON_CLAUSE.finditer(sql):
        for m in ON_EQ.finditer(clause.group(1)):
            ta, tb = alias.get(m.group(1).lower()), alias.get(m.group(3).lower())
            if not ta or not tb:
                skipped += 1
                continue
            a, b = names.column(f"{ta}.{m.group(2)}"), names.column(f"{tb}.{m.group(4)}")
            if a and b and m.group(1).lower() != m.group(3).lower():  # two aliases (self-joins allowed)
                out.add(pair(a, b))
            else:
                skipped += 1
    tables = list(dict.fromkeys(alias.values()))
    for m in USING.finditer(sql):
        ref = unquote(m.group(1))
        right = names.table(f"{project}.{ref}" if ref.count(".") == 1 else ref)
        lefts = [t for t in tables if t != right]
        for col in (c.strip().strip("`") for c in m.group(3).split(",")):
            hits = [t for t in lefts if names.column(f"{t}.{col}")]
            if len(hits) == 1:
                out.add(pair(names.column(f"{hits[0]}.{col}"), names.column(f"{right}.{col}")))
            else:
                skipped += 1
    return out, skipped


def join_truth(names: Names, ok: dict) -> tuple[dict, dict]:
    """pair -> set of sources."""
    T: dict[tuple, set] = defaultdict(set)
    written = {names.table(t) for _, tr, _, _st in ok.values() for t in tr["tables_written"]}
    for j in build("joins.json"):
        if names.table(j["model"]) in written:
            a, b = names.column(j["left"]), names.column(j["right"])
            if a and b:
                T[pair(a, b)].add("declared-model")
    bi = yaml.safe_load((SPEC / "templates" / "bi.yaml").read_text())
    declared_bi = []
    for ex in bi.get("explores", {}).values():
        base_alias, base = ex.get("view"), names.table(ex["from"])
        for line in ex.get("joins") or []:
            m = re.search(r"JOIN\s+`([^`]+)`\s+AS\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)", line)
            if not m:
                continue
            amap = {base_alias: base, m.group(2): names.table(m.group(1))}
            a = names.column(f"{amap.get(m.group(3), '?')}.{m.group(4)}")
            b = names.column(f"{amap.get(m.group(5), '?')}.{m.group(6)}")
            if a and b:
                declared_bi.append((" ".join(line.split()), pair(a, b)))
    skipped = 0
    seen_sql = set()
    for sql, _tr, project, _st in ok.values():
        if sql in seen_sql:
            continue
        seen_sql.add(sql)
        flat = " ".join(sql.split())
        for line, p in declared_bi:
            if line in flat:
                T[p].add("declared-bi")
        pairs, sk = reference_joins(sql, names, project)
        skipped += sk
        for p in pairs:
            T[p].add("reference")
    return T, {"reference_skipped_predicates": skipped, "statements": len(seen_sql)}


# ------------------------------------------------------- truth: lineage


def lineage_truth(names: Names, ok: dict, wh: dict) -> set:
    written = {names.table(t) for _, tr, _, _st in ok.values() for t in tr["tables_written"]}
    T = set()
    for t in wh["tables"]:
        tgt_t = names.table(t["fqn"])
        if tgt_t not in written:
            continue
        for c in t["columns"]:
            for src in c.get("lineage") or []:
                s = names.column(src)
                if s:
                    T.add((s.lower(), f"{tgt_t}.{c['name']}".lower()))
    return T


# ------------------------------------------------------------ the graph


def graph_evidence(G: Graph):
    """What qlsc built: column-level join pairs, lineage edges, parse status of successful shapes."""
    joins = defaultdict(
        lambda: {"types": set(), "vias": set(), "scopes": set(), "wrapped": False, "shapes": 0, "jobs": 0}
    )
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[u:USES_JOIN]->(k:JoinKey)
                       MATCH (k)-[:ON {side:'left'}]->(a:Column), (k)-[:ON {side:'right'}]->(b:Column)
                       RETURN a.id AS a, b.id AS b, u.type AS type, u.left_via AS lv, u.right_via AS rv,
                              u.scopes AS scopes, s.jobs AS jobs,
                              size(u.left_wrap) + size(u.right_wrap) > 0 AS wrapped"""):
        e = joins[pair(r["a"], r["b"])]
        e["types"].add(r["type"])
        e["vias"].update([r["lv"], r["rv"]])
        e["scopes"].update(r["scopes"])
        e["wrapped"] |= r["wrapped"]
        e["shapes"] += 1
        e["jobs"] += r["jobs"] or 0
    flows = {
        (r["a"].lower(), r["b"].lower()): {"src_kind": r["src_kind"], "kinds": r["kinds"]}
        for r in G.rows(
            """MATCH (a:Column)-[f:FLOWS]->(b:Column)<-[:HAS_COLUMN]-(t:Table)
           MATCH (a)<-[:HAS_COLUMN]-(st:Table)
           RETURN a.id AS a, b.id AS b, st.kind AS src_kind, f.kinds AS kinds"""
        )
    }
    health = {
        r["status"]: r["n"]
        for r in G.rows("""MATCH (s:QueryShape {succeeded: true})
                                                      RETURN s.status AS status, count(*) AS n""")
    }
    return joins, flows, health


# ---------------------------------------------------------------- score


def prf(tp, p, t):
    prec = tp / p if p else 0.0
    rec = tp / t if t else 0.0
    return prec, rec, (2 * prec * rec / (prec + rec) if prec + rec else 0.0)


def invisible(e: dict) -> bool:
    """The regex reference only sees columns of directly named tables: anything traced through a
    CTE/subquery, a semi-join, a nested scope or a transformed key is beyond it."""
    return bool(
        e["types"] & {"IN", "WHERE"} or e["vias"] - {"direct"} or e["scopes"] - {"main"} or e["wrapped"]
    )


def score(names: Names, wh: dict, G: Graph) -> dict:
    ok = executed(names)
    truth_joins, jmeta = join_truth(names, ok)
    truth_lineage = lineage_truth(names, ok, wh)
    found_joins, found_flows, health = graph_evidence(G)
    P, T = set(found_joins), set(truth_joins)
    tp = P & T
    extras = sorted(P - T)
    # ingestion lineage from transient staging tables has no spec counterpart
    PL = {k for k, v in found_flows.items() if v["src_kind"] != "transient"}
    ok_shapes = sum(health.values())
    jp, jr, jf = prf(len(tp), len(P), len(T))
    lp, lr, lf = prf(len(PL & truth_lineage), len(PL), len(truth_lineage))
    return {
        "parse_health": {
            "successful_shapes": ok_shapes,
            "status": health,
            "resolved_rate": health.get("ok", 0) / ok_shapes if ok_shapes else 0,
        },
        "joins": {
            "found": len(P),
            "truth": len(T),
            "true_positive": len(tp),
            "precision": jp,
            "recall": jr,
            "f1": jf,
            "recall_by_source": {
                s: (
                    len({p for p in T if s in truth_joins[p]} & P),
                    len({p for p in T if s in truth_joins[p]}),
                )
                for s in ("declared-model", "declared-bi", "reference")
            },
            **jmeta,
            "extras_invisible": [{"pair": p, **found_joins[p]} for p in extras if invisible(found_joins[p])],
            "extras_plain": [{"pair": p, **found_joins[p]} for p in extras if not invisible(found_joins[p])],
            "misses": [{"pair": p, "sources": sorted(truth_joins[p])} for p in sorted(T - P)],
        },
        "lineage": {
            "found": len(PL),
            "truth": len(truth_lineage),
            "true_positive": len(PL & truth_lineage),
            "precision": lp,
            "recall": lr,
            "f1": lf,
            "ingestion_edges_not_scored": len(found_flows) - len(PL),
            "misses": sorted(truth_lineage - PL),
            "extras": [{"pair": p, "kinds": found_flows[p]["kinds"]} for p in sorted(PL - truth_lineage)],
        },
    }


def render(res: dict, db: str) -> list[str]:
    j, lin, ph = res["joins"], res["lineage"], res["parse_health"]
    edge = lambda p: f"`{short(p[0])}` = `{short(p[1])}`"
    L = [
        "# Bottom layer: parse health, joins, lineage",
        "",
        f"Graph: Neo4j `{db}`. Keys: usage truth (successful statements in the window only).",
        "",
        "| | found | truth | matched | precision | recall | F1 |",
        "|---|---|---|---|---|---|---|",
        f"| Join pairs (column level) | {j['found']} | {j['truth']} | {j['true_positive']} | {j['precision']:.1%} | "
        f"{j['recall']:.1%} | {j['f1']:.1%} |",
        f"| Lineage edges (column level) | {lin['found']} | {lin['truth']} | {lin['true_positive']} | "
        f"{lin['precision']:.1%} | {lin['recall']:.1%} | {lin['f1']:.1%} |",
        "",
        f"Parse health: {ph['status'].get('ok', 0):,} of {ph['successful_shapes']:,} successful shapes resolved "
        f"with status ok ({ph['resolved_rate']:.1%}).",
        "",
        "## Joins",
        "",
        "Recall by truth source (a pair can come from several):",
        "",
        "| source | found | in truth |",
        "|---|---|---|",
    ]
    L += [f"| {s} | {a} | {b} |" for s, (a, b) in j["recall_by_source"].items()]
    L += [
        "",
        f"The reference extractor skipped {j['reference_skipped_predicates']:,} predicates it could not "
        f"resolve (CTE or subquery aliases) across {j['statements']:,} successful statements.",
        "",
        f"Found pairs not in the truth: {len(j['extras_invisible']) + len(j['extras_plain'])}. Of these, "
        f"{len(j['extras_invisible'])} are invisible to the reference by construction (semi-joins, joins through "
        f"CTEs/subqueries or transformed keys); {len(j['extras_plain'])} are not, and are listed for inspection:",
        "",
    ]
    L += [
        f"- {edge(e['pair'])} ({', '.join(sorted(e['types']))}; {e['shapes']} shapes)"
        for e in j["extras_plain"][:30]
    ]
    L += ["", f"Misses (in truth, not in the graph): {len(j['misses'])}", ""]
    L += [f"- {edge(m['pair'])} ({', '.join(m['sources'])})" for m in j["misses"][:30]]
    L += ["", "Found pairs invisible to the reference extractor (all, for checking by hand):", ""]
    L += [
        f"- {edge(e['pair'])} ({', '.join(sorted(e['types']))}; via {', '.join(sorted(e['vias']))}; "
        f"scopes {', '.join(sorted(e['scopes']))})"
        for e in j["extras_invisible"]
    ]
    L += [
        "",
        "## Lineage",
        "",
        f"{lin['ingestion_edges_not_scored']:,} ingestion edges (Fivetran staging -> raw) are not scored: raw "
        "tables have no model SQL in the spec.",
        "",
        f"Misses: {len(lin['misses'])}",
        "",
    ]
    L += [f"- `{short(a)}` -> `{short(b)}`" for a, b in lin["misses"][:25]]
    L += ["", f"Extras: {len(lin['extras'])}", ""]
    L += [f"- `{short(e['pair'][0])}` -> `{short(e['pair'][1])}` ({e['kinds']})" for e in lin["extras"][:25]]
    return L


def main() -> int:
    s = settings()
    wh = build("warehouse.json")
    with Graph(s) as G:
        res = score(Names(s, wh), wh, G)
        path = write_result("bottom_layer", render(res, G.db), res)
    j, lin = res["joins"], res["lineage"]
    print(
        f"joins    P={j['precision']:.1%} R={j['recall']:.1%} F1={j['f1']:.1%}  ({j['true_positive']}/{j['truth']} "
        f"truth, {j['found']} found; {len(j['extras_invisible'])} extras invisible to the reference, "
        f"{len(j['extras_plain'])} plain extras)"
    )
    print(
        f"lineage  P={lin['precision']:.1%} R={lin['recall']:.1%} F1={lin['f1']:.1%}  "
        f"({lin['true_positive']}/{lin['truth']} truth, {lin['found']} found)"
    )
    print(
        f"parse    {res['parse_health']['resolved_rate']:.1%} of {res['parse_health']['successful_shapes']:,} "
        f"successful shapes ok\n-> {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

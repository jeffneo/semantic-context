#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40", "sqlglot>=30", "google-cloud-bigquery>=3.25"]
# ///
"""Score the pipeline's graph against ground truth. The only code that reads both.

M1 scores the evidence graph (Neo4j `semanticlayer`):

  parse health   successful shapes resolved, from the graph itself
  join recovery  column-level JoinKeys vs the joins that actually executed
  lineage        column FLOWS vs the model column lineage of models that actually ran

The keys are usage truth, as PIPELINE_PLAN.md §0 and §8 require: only statements
that ran successfully in the log window count. Join truth has three independent
sources, none of them the pipeline's parser:

  declared-model  build/joins.json - joins in model SQL, resolved by build.py
  declared-bi     templates/bi.yaml explore joins, where the executed Looker SQL
                  contains the join line
  reference       a deliberately simple regex extractor over every successful
                  executed statement: `a.x = b.y` in ON, and `USING (x)`, where both
                  aliases name a table directly. It cannot see through CTEs or
                  subqueries, so pipeline joins it does not have are classified,
                  not counted as wrong.

Writes build/score/M1_SCORE.md and M1_SCORE.json.

Usage: uv run specs/tools/score.py
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from neo4j import GraphDatabase

SPECS = Path(__file__).resolve().parents[1]
ROOT = SPECS.parent
BUILD = SPECS / "build"
OUT = BUILD / "score"


def env() -> dict:
    out = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ------------------------------------------------------------------ naming

class Names:
    """Canonical names, using the rules the pipeline publishes in its catalog snapshot."""

    def __init__(self, cat: dict, wh: dict):
        self.rules = [(re.compile(r["pattern"]), r["replace"]) for r in cat.get("rules", [])]
        self.fam = set(cat.get("shard_families", []))
        self.cols = {}
        for t in wh["tables"]:
            self.cols[self.table(t["fqn"])] = {c["name"].lower(): c["name"] for c in t["columns"]}

    def table(self, fqn: str) -> str:
        p, d, n = fqn.split(".", 2)
        for rx, rep in self.rules:
            n = rx.sub(rep, n)
        head, _, tail = n.rpartition("_")
        if head and f"{p}.{d}.{head}_" in self.fam and (tail.isdigit() or tail.endswith("*")):
            n = head + "_*"
        return f"{p}.{d}.{n}"

    def column(self, fqn_col: str) -> str | None:
        t, _, c = fqn_col.rpartition(".")
        t = self.table(t)
        spelled = self.cols.get(t, {}).get(c.lower())
        return f"{t}.{spelled}" if spelled else None


def short(x: str) -> str:
    return ".".join(x.split(".")[1:])


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

TABLE_REF = re.compile(r"(?:FROM|JOIN)\s+((?:`[^`]+`\.?)+|[A-Za-z_]\w*\.[A-Za-z_]\w*\b)(?:\s+(?:AS\s+)?(?!ON\b|USING\b|WHERE\b|LEFT\b|JOIN\b|INNER\b"
                       r"|GROUP\b|ORDER\b|CROSS\b|FULL\b|RIGHT\b|LIMIT\b|QUALIFY\b)([A-Za-z_]\w*))?", re.I)
ON_EQ = re.compile(r"\b([A-Za-z_]\w*)\.`?(\w+)`?\s*=\s*([A-Za-z_]\w*)\.`?(\w+)`?")
USING = re.compile(r"JOIN\s+((?:`[^`]+`\.?)+|[A-Za-z_]\w*\.[A-Za-z_]\w*\b)(?:\s+(?:AS\s+)?([A-Za-z_]\w*))?\s+USING\s*\(([^)]+)\)", re.I)
ON_CLAUSE = re.compile(r"\bON\s+(.+?)(?=\b(?:LEFT|RIGHT|INNER|FULL|CROSS|JOIN|WHERE|GROUP|ORDER|QUALIFY|UNION|LIMIT|WHEN)\b|\)\s*(?:,|$|SELECT)|$)",
                       re.I | re.S)


def unquote(ref: str) -> str:
    return ref.replace("`", "")


def reference_joins(sql: str, names: Names, project: str) -> tuple[set, int]:
    """Direct-table joins in one statement; also returns how many predicates it had to skip."""
    alias = {}
    for m in TABLE_REF.finditer(sql):
        fqn = unquote(m.group(1))
        if fqn.count(".") == 1:
            fqn = f"{project}.{fqn}"          # dataset.table resolves in the job's project
        if fqn.count(".") != 2:
            continue
        a = m.group(2) or fqn.split(".")[-1]
        alias[a.lower()] = names.table(fqn)
    out, skipped = set(), 0
    if re.search(r"\bMERGE\b", sql[:600], re.I):
        return out, 0            # MERGE ... ON is write mechanics, not a join
    for clause in ON_CLAUSE.finditer(sql):
        for m in ON_EQ.finditer(clause.group(1)):
            ta, tb = alias.get(m.group(1).lower()), alias.get(m.group(3).lower())
            if not ta or not tb:
                skipped += 1
                continue
            a, b = names.column(f"{ta}.{m.group(2)}"), names.column(f"{tb}.{m.group(4)}")
            if a and b and m.group(1).lower() != m.group(3).lower():   # two aliases (self-joins allowed)
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
    for j in json.loads((BUILD / "joins.json").read_text()):
        if names.table(j["model"]) in written:
            a, b = names.column(j["left"]), names.column(j["right"])
            if a and b:
                T[pair(a, b)].add("declared-model")
    bi = yaml.safe_load((SPECS / "templates" / "bi.yaml").read_text())
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
    for sql, tr, project, _st in ok.values():
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


# ----------------------------------------------------------- pipeline

def pipeline(cfg: dict):
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]))
    db = n["database"]
    q = lambda cy: drv.execute_query(cy, database_=db).records
    joins = defaultdict(lambda: {"types": set(), "vias": set(), "scopes": set(), "wrapped": False,
                                 "shapes": 0, "jobs": 0})
    for r in q("""MATCH (s:QueryShape {succeeded: true})-[u:USES_JOIN]->(k:JoinKey)
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
    flows = {}
    for r in q("""MATCH (a:Column)-[f:FLOWS]->(b:Column)<-[:HAS_COLUMN]-(t:Table)
                  MATCH (a)<-[:HAS_COLUMN]-(st:Table)
                  RETURN a.id AS a, b.id AS b, st.kind AS src_kind, f.kinds AS kinds"""):
        flows[(r["a"].lower(), r["b"].lower())] = {"src_kind": r["src_kind"], "kinds": r["kinds"]}
    health = {r["status"]: r["n"] for r in q("""MATCH (s:QueryShape {succeeded: true})
                                                 RETURN s.status AS status, count(*) AS n""")}
    drv.close()
    return joins, flows, health


# -------------------------------------------------------------- score

def prf(tp, p, t):
    prec = tp / p if p else 0.0
    rec = tp / t if t else 0.0
    return prec, rec, (2 * prec * rec / (prec + rec) if prec + rec else 0.0)


def main() -> int:
    cfg = yaml.safe_load((ROOT / "pipeline" / "estate.yaml").read_text())
    cat = json.loads((ROOT / "pipeline" / "work" / "catalog.json").read_text())
    wh = json.loads((BUILD / "warehouse.json").read_text())
    names = Names(cat, wh)
    if "--only-m6" in sys.argv:
        m6(cfg, names, wh)
        return 0
    ok = executed(names)
    JT, jmeta = join_truth(names, ok)
    LT = lineage_truth(names, ok, wh)
    PJ, PF, health = pipeline(cfg)

    # joins
    P, T = set(PJ), set(JT)
    tp = P & T
    jp, jr, jf = prf(len(tp), len(P), len(T))
    by_src = {s: (len({p for p in T if s in JT[p]} & P), len({p for p in T if s in JT[p]}))
              for s in ("declared-model", "declared-bi", "reference")}
    extras = sorted(P - T)

    def invisible(p):
        e = PJ[p]
        # the regex reference only sees columns of directly named tables ("direct"):
        # anything traced through a CTE/subquery, a semi-join, or a nested scope is beyond it
        return bool(e["types"] & {"IN", "WHERE"} or e["vias"] - {"direct"} or e["scopes"] - {"main"}
                    or e["wrapped"])
    extra_hidden = [p for p in extras if invisible(p)]
    extra_plain = [p for p in extras if not invisible(p)]
    misses = sorted(T - P)

    # lineage (ingestion lineage from transient staging tables has no spec counterpart)
    PL = {k for k, v in PF.items() if v["src_kind"] != "transient"}
    ingest = len(PF) - len(PL)
    ltp = PL & LT
    lp, lr, lf = prf(len(ltp), len(PL), len(LT))
    lmiss, lextra = sorted(LT - PL), sorted(PL - LT)

    ok_shapes = sum(health.values())
    res = {
        "parse_health": {"successful_shapes": ok_shapes, "status": health,
                         "resolved_rate": health.get("ok", 0) / ok_shapes if ok_shapes else 0},
        "joins": {"pipeline": len(P), "truth": len(T), "true_positive": len(tp), "precision": jp, "recall": jr,
                  "f1": jf, "recall_by_source": by_src, "extras_invisible_to_reference": len(extra_hidden),
                  "extras_plain": len(extra_plain), **jmeta},
        "lineage": {"pipeline": len(PL), "truth": len(LT), "true_positive": len(ltp), "precision": lp,
                    "recall": lr, "f1": lf, "ingestion_edges_not_scored": ingest},
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "M1_SCORE.json").write_text(json.dumps(res, indent=1))
    short = lambda s: ".".join(s.split(".")[1:])
    L = ["# M1 score: evidence graph", "",
         "Graph: Neo4j `semanticlayer`. Keys: usage truth (successful statements in the window only).", "",
         "| | pipeline | truth | matched | precision | recall | F1 |", "|---|---|---|---|---|---|---|",
         f"| Join pairs (column level) | {len(P)} | {len(T)} | {len(tp)} | {jp:.1%} | {jr:.1%} | {jf:.1%} |",
         f"| Lineage edges (column level) | {len(PL)} | {len(LT)} | {len(ltp)} | {lp:.1%} | {lr:.1%} | {lf:.1%} |", "",
         f"Parse health: {health.get('ok', 0):,} of {ok_shapes:,} successful shapes resolved with status ok "
         f"({res['parse_health']['resolved_rate']:.1%}).", "",
         "## Joins", "",
         "Recall by truth source (a pair can come from several):", "",
         "| source | found | in truth |", "|---|---|---|"]
    L += [f"| {s} | {a} | {b} |" for s, (a, b) in by_src.items()]
    L += ["", f"The reference extractor skipped {jmeta['reference_skipped_predicates']:,} predicates it could not "
          f"resolve (CTE or subquery aliases) across {jmeta['statements']:,} successful statements.", "",
          f"Pipeline pairs not in the truth: {len(extras)}. Of these, {len(extra_hidden)} are invisible to the "
          f"reference by construction (semi-joins, joins through CTEs/subqueries or transformed keys); "
          f"{len(extra_plain)} are not, and are listed for inspection:", ""]
    L += [f"- `{short(a)}` = `{short(b)}` ({', '.join(sorted(PJ[(a, b)]['types']))}; "
          f"{PJ[(a, b)]['shapes']} shapes)" for a, b in extra_plain[:30]]
    L += ["", f"Misses (in truth, not in the graph): {len(misses)}", ""]
    L += [f"- `{short(a)}` = `{short(b)}` ({', '.join(sorted(JT[(a, b)]))})" for a, b in misses[:30]]
    L += ["", "Pipeline pairs invisible to the reference extractor (all; checked by hand, see M1 notes):", ""]
    L += [f"- `{short(a)}` = `{short(b)}` ({', '.join(sorted(PJ[(a, b)]['types']))}; via "
          f"{', '.join(sorted(PJ[(a, b)]['vias']))}; scopes {', '.join(sorted(PJ[(a, b)]['scopes']))})"
          for a, b in extra_hidden]
    L += ["", "## Lineage", "",
          f"{ingest:,} ingestion edges (Fivetran staging -> raw) are not scored: raw tables have no model SQL in the spec.", "",
          f"Misses: {len(lmiss)}", ""]
    L += [f"- `{short(a)}` -> `{short(b)}`" for a, b in lmiss[:25]]
    L += ["", f"Extras: {len(lextra)}", ""]
    L += [f"- `{short(a)}` -> `{short(b)}` ({PF[(a, b)]['kinds']})" for a, b in lextra[:25]]
    (OUT / "M1_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"joins    P={jp:.1%} R={jr:.1%} F1={jf:.1%}  ({len(tp)}/{len(T)} truth, {len(P)} found; "
          f"{len(extra_hidden)} extras invisible to reference, {len(extra_plain)} plain extras)")
    print(f"lineage  P={lp:.1%} R={lr:.1%} F1={lf:.1%}  ({len(ltp)}/{len(LT)} truth, {len(PL)} found)")
    print(f"parse    {res['parse_health']['resolved_rate']:.1%} of {ok_shapes:,} successful shapes ok")
    print(f"-> {OUT / 'M1_SCORE.md'}")
    if "--only-m1" in sys.argv:
        return 0
    m2(cfg, names, wh, ok)
    m3(cfg, names, wh)
    m4(cfg, names, wh)
    if "--m5" in sys.argv or (ROOT / "pipeline" / "work" / "emb_cache.json").exists():
        m5(cfg, names, wh)
    if "--m6" in sys.argv or (ROOT / "pipeline" / "work" / "qa_cache").exists():
        m6(cfg, names, wh)
    return 0


# =============================================================== M2 ======

# The role each spec service account plays, in the actor model's vocabulary. Reverse ETL
# (Hightouch) reads on a schedule and writes nothing back to BigQuery, which is all the
# log can show: scheduled_reader is the right answer for it.
EXPECTED_CLASS = {"fivetran-sync": "ingestion", "ga4-export": "ingestion", "file-loader": "ingestion",
                  "amplitude-export": "ingestion", "dbt-prod": "transformation", "composer-legacy": "transformation",
                  "vertex-scoring": "ml", "looker-prod": "bi_service", "tableau-finance": "bi_service",
                  "hightouch-sync": "scheduled_reader", "elementary-dq": "monitor"}
EXPECTED_PURPOSE = {"human": "adhoc", "dq_report": "adhoc", "looker_query": "bi", "tableau": "bi",
                    "looker_trigger": "probe", "dbt_test": "probe", "dbt_freshness": "probe", "dq_monitor": "probe",
                    "looker_pdt": "build", "legacy_dag": "build", "sandbox_ctas": "build", "ingest_merge": "ingest",
                    "hightouch_sync": "extract", "vertex": "ml_read"}
CONSUMING_FAMILIES = {"human", "dq_report", "looker_query", "tableau", "looker_pdt", "legacy_dag", "sandbox_ctas",
                      "hightouch_sync", "vertex", "dbt_build"}


def pairwise(pred: dict, true: dict) -> tuple[float, float, float]:
    """Pairwise precision/recall of 'same group' decisions, and the adjusted Rand index."""
    from math import comb
    items = sorted(set(pred) & set(true))
    tp = fp = fn = 0
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            sp, st = pred[a] == pred[b], true[a] == true[b]
            tp += sp and st
            fp += sp and not st
            fn += st and not sp
    n = len(items)
    cont = Counter((pred[x], true[x]) for x in items)
    sum_ij = sum(comb(v, 2) for v in cont.values())
    sum_a = sum(comb(v, 2) for v in Counter(pred[x] for x in items).values())
    sum_b = sum(comb(v, 2) for v in Counter(true[x] for x in items).values())
    expected = sum_a * sum_b / comb(n, 2) if n > 1 else 0
    ari = (sum_ij - expected) / (0.5 * (sum_a + sum_b) - expected) if (sum_a + sum_b) / 2 != expected else 1.0
    return (tp / (tp + fp) if tp + fp else 0), (tp / (tp + fn) if tp + fn else 0), ari


def m2(cfg, names: Names, wh: dict, ok: dict):
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]))
    q = lambda cy, **kw: [r.data() for r in drv.execute_query(cy, database_=n["database"], **kw).records]
    key = json.loads((BUILD / "answer_key.json").read_text())["findings"]
    res, L = {}, ["# M2 score: actor model, lifecycle and cost findings", "",
                  "Graph: Neo4j `semanticlayer`. Keys: the spec's service-account roles and teams; usage truth from "
                  "`jobs_truth` (successful jobs only); planted findings from `answer_key.json`.", ""]

    # ---------------------------------------------------------- actors
    pcls = {r["id"]: r["cls"] for r in q("MATCH (p:Principal) RETURN p.id AS id, p.class AS cls")}
    exp = {sa["email"]: EXPECTED_CLASS[k] for k, sa in wh["service_accounts"].items() if k in EXPECTED_CLASS}
    teams = wh["teams"].items() if isinstance(wh["teams"], dict) else enumerate(wh["teams"])
    domain = next(e.split("@")[1] for e in pcls if not e.endswith("gserviceaccount.com"))
    true_team = {f"{m}@{domain}": k for k, t in teams for m in t["members"]}
    exp.update({e: "human" for e in true_team})
    right = [e for e in exp if pcls.get(e) == exp[e]]
    wrong = [(e, pcls.get(e), exp[e]) for e in exp if pcls.get(e) != exp[e]]
    res["actors"] = {"correct": len(right), "total": len(exp), "wrong": wrong}
    L += ["## Actor model", "", f"Principal class: **{len(right)} / {len(exp)}** correct."]
    L += [f"- `{e}`: classed {g}, expected {x}" for e, g, x in wrong]
    pred_team = {r["p"]: r["t"] for r in q("MATCH (p:Principal)-[:MEMBER_OF]->(t:Team) RETURN p.id AS p, t.id AS t")}
    t_prec, t_rec, ari = pairwise(pred_team, true_team)
    res["teams"] = {"pairwise_precision": t_prec, "pairwise_recall": t_rec, "ari": ari,
                    "inferred": len(set(pred_team.values())), "true": len(set(true_team.values()))}
    L += ["", f"Teams (people grouped by what they consume): {len(set(pred_team.values()))} inferred vs "
          f"{len(set(true_team.values()))} in the spec; pairwise precision {t_prec:.1%}, recall {t_rec:.1%}, ARI {ari:.2f}."]
    merged = defaultdict(set)
    for p_, t_ in pred_team.items():
        if p_ in true_team:
            merged[t_].add(true_team[p_])
    L += [f"- inferred team = {' + '.join(sorted(v))}" for v in merged.values() if len(v) > 1]

    # shape purpose vs the family that produced its jobs
    text_shape = {}
    for line in gzip.open(ROOT / "pipeline" / "work" / "texts.ndjson.gz", "rt"):
        t = json.loads(line)
        text_shape[t["text_id"]] = t["shape_id"]
    import hashlib
    fam = defaultdict(Counter)
    for sql, tr, _, _st in ok.values():
        sid = text_shape.get(hashlib.sha1(sql.encode()).hexdigest())
        if sid:
            fam[sid][tr["family"]] += 1
    purpose = {r["id"]: (r["p"], r["st"]) for r in q("MATCH (s:QueryShape {succeeded: true, origin: 'log'}) "
                                                      "RETURN s.id AS id, s.purpose AS p, s.statement_type AS st")}
    good = total = 0
    confusion = Counter()
    for sid, (p_, st) in purpose.items():
        if sid not in fam:
            continue
        f_ = fam[sid].most_common(1)[0][0]
        want = "view_definition" if st == "CREATE_VIEW" else ("build" if f_ == "dbt_build" else EXPECTED_PURPOSE.get(f_))
        if want is None:
            continue
        total += 1
        if want == "adhoc" and p_ == "metadata":
            want = "metadata"       # a person's INFORMATION_SCHEMA lookup: a more specific label, not an error
        good += p_ == want
        if p_ != want:
            confusion[(f_, p_, want)] += 1
    res["purpose"] = {"correct": good, "total": total, "confusion": [list(k) + [v] for k, v in confusion.items()]}
    L += ["", f"Shape purpose: **{good} / {total}** successful shapes match the family that ran them ({good / max(total, 1):.1%})."]
    L += [f"- {v} shapes of family `{f_}` classed `{p_}`, expected `{w_}`" for (f_, p_, w_), v in confusion.most_common(8)]

    # ------------------------------------------------ usage truth for liveness
    views = {names.table(t["fqn"]): {names.table(s_) for s_ in t.get("sources") or []}
             for t in wh["tables"] if t.get("materialized") == "view"}

    def expand(t, seen=()):
        out = {t}
        for s_ in views.get(t, ()):
            if s_ not in seen:
                out |= expand(s_, seen + (t,))
        return out
    consumed, written = set(), set()
    for sql, tr, _, _st in ok.values():
        # a CREATE VIEW defines a view and reads no data: it is not consumption of its sources
        if tr["family"] in CONSUMING_FAMILIES and _st != "CREATE_VIEW":
            w_ = {names.table(x) for x in tr["tables_written"]}
            for t in tr["tables_read"]:
                for x in expand(names.table(t)):
                    if x not in w_:
                        consumed.add(x)

    F = defaultdict(list)
    for r in q("""MATCH (f:Finding) OPTIONAL MATCH (f)-[a:ABOUT]->(x)
                  RETURN f.id AS id, f.kind AS kind, f.evidence AS ev, collect({id: x.id, role: a.role}) AS about"""):
        r["ev"] = json.loads(r["ev"] or "{}")
        F[r["kind"]].append(r)
    subj = lambda kind, roles=("subject",): {a["id"] for f in F[kind] for a in f["about"] if a["role"] in roles}
    L += ["", "## Findings", "", "| finding | result | detail |", "|---|---|---|"]

    def row(fid, verdict, detail):
        res[fid] = {"verdict": verdict, "detail": detail}
        L.append(f"| {fid} {key[fid]['title']} | **{verdict}** | {detail} |")

    def verdict(found, total):
        return "pass" if found == total else ("partial" if found else "fail")

    # F19 monitor
    mon_email = wh["service_accounts"]["elementary-dq"]["email"]
    mf = [f for f in F["monitor"] if any(a["id"] == mon_email for a in f["about"])]
    kept = len(mf[0]["ev"].get("kept_alive", [])) if mf else 0
    row("F19", "pass" if pcls.get(mon_email) == "monitor" and mf else "fail",
        f"{mon_email.split('@')[0]} classed `{pcls.get(mon_email)}`; its traffic excluded from consumption "
        f"(it alone would keep {kept} unused tables looking alive)")
    # F06 / F07 unused tables
    unused = subj("dead") | subj("write_only") | {f["ev"].get("physical") for f in F["dead"] if f["ev"].get("physical")}
    planted6 = {names.table(o) if "LR_" not in o else o for o in key["F06"]["objects"]}
    found6 = {o for o in key["F06"]["objects"] if o in unused or names.table(o) in unused}
    true_unused = {t for t in unused if t not in consumed}
    all_tables = {names.table(t["fqn"]) for t in wh["tables"]}
    truth_unused = all_tables - consumed
    missed_unused = sorted(truth_unused - unused)
    row("F06", verdict(len(found6), len(key["F06"]["objects"])),
        f"{len(found6)}/{len(key['F06']['objects'])} planted dead tables flagged unused"
        + (f" (missed: {', '.join(sorted(o.split('.', 1)[1] for o in set(key['F06']['objects']) - found6))})"
           if len(found6) < len(key['F06']['objects']) else "")
        + f"; {len(true_unused)}/{len(unused)} of all flagged-unused tables confirmed unconsumed by usage truth"
        + f"; {len(truth_unused & unused)}/{len(truth_unused)} of all tables usage truth says are unconsumed were flagged"
        + (f" (not flagged: {', '.join(x.split('.', 1)[1] for x in missed_unused[:8])})" if missed_unused else ""))
    wo = subj("write_only")
    found7 = {o for o in key["F07"]["objects"] if o in wo}
    row("F07", verdict(len(found7), len(key["F07"]["objects"])),
        f"{len(found7)}/{len(key['F07']['objects'])} planted write-only tables flagged; "
        f"{len({t for t in wo if t not in consumed})}/{len(wo)} write-only findings confirmed by usage truth")
    # F11 straggler
    v2, v3 = key["F11"]["objects"][0], key["F11"]["objects"][1]
    pdt = names.table(key["F11"]["objects"][2])
    st = {a["id"]: f for f in F["straggler"] for a in f["about"] if a["role"] == "subject"}
    checks = [v2 in st and st[v2]["ev"].get("last_written") == "2026-05-14",
              v2 in st and v3 in st[v2]["ev"].get("successors", []), pdt in st]
    row("F11", verdict(sum(checks), 3), f"v2 stop date {'right' if checks[0] else 'wrong/missing'}; successor v3 "
        f"{'named' if checks[1] else 'missing'}; stale Looker PDT {'flagged' if checks[2] else 'missing'}; "
        f"{len(st)} straggler findings in total")
    # F05 superseded
    sp = {a["id"]: f for f in F["superseded_live"] for a in f["about"] if a["role"] == "subject"}
    o5 = key["F05"]["objects"]
    f5 = sp.get(o5[0])
    checks = [bool(f5), bool(f5) and o5[3] in {a["id"] for a in f5["about"] if a["role"] == "replacement"},
              bool(f5) and {o5[1], o5[2]} <= set(f5["ev"].get("chain", []))]
    row("F05", verdict(sum(checks), 3), f"legacy table {'flagged' if checks[0] else 'missing'}; replacement "
        f"{'named' if checks[1] else 'missing'}; chain to the Tableau report {'traced' if checks[2] else 'missing'}; "
        f"{len(sp)} superseded findings in total")
    # cost findings: planted objects among the finding subjects (and their via tables / example targets)
    ex_targets = {r["t"] for r in q("""MATCH (f:Finding {kind: 'unpruned_scan'})-[:ABOUT {role: 'example'}]->(s:QueryShape)
                                       -[:WRITES]->(t:Table) RETURN DISTINCT t.id AS t""")}
    for fid, kind, roles, extra in (("F09", "unpruned_scan", ("subject", "via"), ex_targets),
                                    ("F20", "star_limit", ("subject",), set()),
                                    ("F21", "probe_cost", ("subject",), set()),
                                    ("F22", "incremental_rescan", ("subject", "source"), set())):
        pool = subj(kind, roles) | extra
        objs = key[fid]["objects"]
        hit = [o for o in objs if names.table(o) in pool or o in pool]
        miss = [o.split(".", 1)[1] for o in objs if o not in hit]
        row(fid, verdict(len(hit), len(objs)), f"{len(hit)}/{len(objs)} planted objects in {len(F[kind])} `{kind}` findings"
            + (f" (missed: {', '.join(miss)})" if miss else ""))
    # F17 literal drift
    lf = [f for f in F["literal_drift"] if f["ev"].get("value") == "ACCT_CLOSE"]
    ok17 = bool(lf) and "2026-06-01" <= lf[0]["ev"]["first_seen"] <= "2026-06-04" and any(
        a["id"] in key["F17"]["objects"] for a in lf[0]["about"])
    row("F17", "pass" if ok17 else "fail",
        (f"'ACCT_CLOSE' on {lf[0]['about'][0]['id'].split('.', 1)[1]} first filtered {lf[0]['ev']['first_seen']}" if lf
         else "not flagged") + f"; {len(F['literal_drift'])} drift findings in total")
    drv.close()
    OUT.mkdir(exist_ok=True)
    (OUT / "M2_SCORE.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "M2_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"actors   {len(right)}/{len(exp)} classes; teams ARI {ari:.2f} (P {t_prec:.0%} R {t_rec:.0%}); purpose {good}/{total}")
    print("findings " + "  ".join(f"{k}={v['verdict']}" for k, v in res.items() if k.startswith("F")))
    print(f"-> {OUT / 'M2_SCORE.md'}")


# =============================================================== M3 ======

def m3(cfg, names: Names, wh: dict):
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]))
    q = lambda cy, **kw: [r.data() for r in drv.execute_query(cy, database_=n["database"], **kw).records]
    key = json.loads((BUILD / "answer_key.json").read_text())["findings"]
    concepts = yaml.safe_load((SPECS / "concepts.yaml").read_text())["concepts"]
    kind_of = {cid: c.get("kind") for cid, c in concepts.items()}
    res, L = {}, ["# M3 score: variables, join confidence, identity", "",
                  "Graph: Neo4j `semanticlayer`. Keys: column concept tags (`concepts.yaml`) and planted findings "
                  "(`answer_key.json`). Only columns the log actually uses are scored - an unused column has no "
                  "evidence to place it.", ""]
    colvar = {r["c"].lower(): r["v"] for r in q("MATCH (c:Column)-[:IS]->(v:Variable) RETURN c.id AS c, v.id AS v")}
    concept = {}
    for t in wh["tables"]:
        for c in t["columns"]:
            if c.get("concept"):
                concept[f"{names.table(t['fqn'])}.{c['name']}".lower()] = c["concept"]
    # dates are a calendar domain, scored with the other domain-level tags
    is_id = lambda k: kind_of.get(k) == "identifier" and not k.startswith("date.")
    ident = {c: concept[c] for c in concept if c in colvar and is_id(concept[c])}
    other = {c: concept[c] for c in concept if c in colvar and not is_id(concept[c])}
    ip, ir, iari = pairwise({c: colvar[c] for c in ident}, ident)
    op_, _, _ = pairwise({c: colvar[c] for c in other}, other)
    consumed_t = {r["t"].lower() for r in q("MATCH (t:Table) WHERE t.consumed_jobs > 0 RETURN t.id AS t")}
    live = {c: k for c, k in ident.items() if c.rsplit(".", 1)[0] in consumed_t}
    lp, lr, lari = pairwise({c: colvar[c] for c in live}, live)
    res["identifier_variables"] = {"columns": len(ident), "pairwise_precision": ip, "pairwise_recall": ir, "ari": iari,
                                   "consumed_columns": len(live), "consumed_precision": lp, "consumed_recall": lr,
                                   "consumed_ari": lari}
    res["other_variables"] = {"columns": len(other), "pairwise_precision": op_}
    L += ["## Variables", "",
          f"- **Identifiers** ({len(ident)} tagged columns used in the log, scored against id-space concepts): "
          f"pairwise precision **{ip:.1%}**, recall **{ir:.1%}**, ARI **{iari:.2f}**.",
          f"- **Identifiers in tables the business consumes** ({len(live)} columns): precision **{lp:.1%}**, "
          f"recall **{lr:.1%}**, ARI **{lari:.2f}**. The rest of the gap is raw columns and their staging views that "
          f"nothing downstream reads (see M2's dead and write-only findings): no join or lineage connects them, so "
          f"usage gives no evidence either way.",
          f"- **Measures, dates, attributes** ({len(other)} columns): purity (pairwise precision) **{op_:.1%}**. "
          f"Their concept tags are domains (`money.balance`, `date.day`), coarser than variables by design, so "
          f"only purity is meaningful: a variable must not straddle two domains, but it may be finer than one.", ""]

    # join confidence vs the id spaces the spec says each side belongs to
    joins = q("""MATCH (k:JoinKey)-[:ON {side:'left'}]->(a:Column), (k)-[:ON {side:'right'}]->(b:Column)
                 WHERE k.confidence IS NOT NULL
                 RETURN a.id AS a, b.id AS b, k.confidence AS c, k.identity AS identity""")
    wrong = [j for j in joins if concept.get(j["a"].lower()) and concept.get(j["b"].lower())
             and kind_of.get(concept[j["a"].lower()]) == "identifier" and kind_of.get(concept[j["b"].lower()]) == "identifier"
             and concept[j["a"].lower()] != concept[j["b"].lower()]
             and j["identity"]]      # DATE_TRUNC(post_date, MONTH) = month_start translates; it does not equate
    flagged = [j for j in joins if j["c"] == "suspect"]
    tp = [j for j in flagged if j in wrong]
    res["suspect_joins"] = {"flagged": len(flagged), "truly_wrong": len(wrong), "true_positive": len(tp)}
    L += ["## Join confidence", "",
          f"Executed joins whose two sides the spec tags as different id spaces: **{len(wrong)}**. "
          f"Flagged suspect: **{len(flagged)}**, of which **{len(tp)}** are truly wrong "
          f"(precision {len(tp) / max(len(flagged), 1):.0%}, recall {len(tp) / max(len(wrong), 1):.0%}).", ""]
    for j in wrong:
        if j not in flagged:
            L.append(f"- missed: `{short(j['a'])}` = `{short(j['b'])}` ({concept[j['a'].lower()]} vs {concept[j['b'].lower()]}; classed {j['c']})")
    for j in flagged:
        if j not in wrong:
            L.append(f"- flagged but not wrong by the tags: `{short(j['a'])}` = `{short(j['b'])}`")
    counts = Counter(j["c"] for j in joins)
    L += ["", f"All join keys by confidence: {dict(counts.most_common())}.", ""]

    F = defaultdict(list)
    for r in q("""MATCH (f:Finding) OPTIONAL MATCH (f)-[a:ABOUT]->(x)
                  RETURN f.id AS id, f.kind AS kind, f.title AS title, f.summary AS summary, f.evidence AS ev,
                         collect({id: x.id, role: a.role}) AS about"""):
        r["ev"] = json.loads(r["ev"] or "{}")
        F[r["kind"]].append(r)
    L += ["## Findings", "", "| finding | result | detail |", "|---|---|---|"]

    def row(fid, verdict, detail):
        res[fid] = {"verdict": verdict, "detail": detail}
        L.append(f"| {fid} {key[fid]['title']} | **{verdict}** | {detail} |")

    def verdict(found, total):
        return "pass" if found == total else ("partial" if found else "fail")

    def var_of(col):
        t, _, c = col.rpartition(".")
        return colvar.get(f"{names.table(t)}.{c}".lower())

    # F01 identity: the customer entity, and the three crosswalks
    cif_var = var_of("fennmoor-raw.core_banking_cdc.CUSTOMER.CIF_NO")
    ent = next((f for f in F["identity_map"] if cif_var in f["ev"].get("identifiers", [])), None)
    xw = set(ent["ev"].get("crosswalks", [])) if ent else set()
    want = {"int_customer_identity": "int_customer_identity", "online_user": "online_user", "aml party": "aml_party"}
    got = {k: any(v in t for t in xw) for k, v in want.items()}
    got["aml party"] = got["aml party"] or any(t.endswith("aml_kyc.party") for t in xw)
    ids_in = {concept.get(c) for c, v in colvar.items() if ent and (v in ent["ev"].get("identifiers", []) or
                                                                    v in ent["ev"].get("linked", []))}
    row("F01", verdict(sum(got.values()), 3),
        f"crosswalks recognized: {', '.join(k for k, v in got.items() if v) or 'none'}"
        f"{'; missing: ' + ', '.join(k for k, v in got.items() if not v) if not all(got.values()) else ''}; "
        f"customer id spaces in or linked to the entity: {', '.join(sorted(x for x in ids_in if x and x.startswith('customer.')))}")
    # F02 synonyms
    objs = key["F02"]["objects"]
    same = [o for o in objs if var_of(o) == cif_var]
    unused = [o for o in objs if var_of(o) is None]
    row("F02", verdict(len(same), len(objs) - len(unused)) if len(same) < len(objs) else "pass",
        f"{len(same)}/{len(objs)} spellings in the CIF variable"
        + (f"; {len(unused)} never used in the window, so no evidence either way ({', '.join(short(o) for o in unused)})" if unused else ""))
    # F03 homonym
    o3 = key["F03"]["objects"]
    v3 = {var_of(o) for o in o3[:5] if var_of(o)}
    sus3 = any(any(a["id"].endswith("bust_out_candidates") and a["role"] == "built_by_it" for a in f["about"]) for f in F["suspect_join"])
    sep = var_of(o3[0]) != var_of(o3[2]) and var_of(o3[0]) != var_of(o3[4])
    row("F03", "pass" if sep and sus3 else ("partial" if sep or sus3 else "fail"),
        f"deposit / card / Salesforce account_id kept apart: {'yes' if sep else 'no'} ({len(v3)} variables); "
        f"the bust_out_candidates join flagged suspect: {'yes' if sus3 else 'no'}")
    # F04 CC
    sus4 = any(any(a["id"].endswith(("CC_ID", "SITE_CD")) for a in f["about"]) for f in F["suspect_join"])
    row("F04", "partial" if sus4 else "fail", "the CC_ID = SITE_CD join flagged suspect: "
        f"{'yes' if sus4 else 'no'}; expanding 'CC' per table is M5 (naming)")
    # F10 competing churn scores
    o10 = key["F10"]["objects"]
    cm = [f for f in F["competing_measures"] if any(var_of(o) in {a["id"] for a in f["about"]} for o in o10)]
    inside = [o for o in o10 if cm and var_of(o) in {a["id"] for a in cm[0]["about"]}]
    sanct = cm and var_of(o10[0]) in {a["id"] for a in cm[0]["about"] if a["role"] == "sanctioned"}
    no_ev = [o for o in o10 if var_of(o) is None]
    row("F10", "pass" if len(inside) == len(o10) - len(no_ev) and sanct else ("partial" if inside else "fail"),
        f"{len(inside)}/{len(o10)} churn columns grouped as competing measures; v3 named sanctioned: "
        f"{'yes' if sanct else 'no'}" + (f"; unused in the window: {', '.join(short(o) for o in no_ev)}" if no_ev else "")
        + ("; not linked: " + ", ".join(short(o) for o in o10 if o not in inside and o not in no_ev)
           if len(inside) < len(o10) - len(no_ev) else ""))
    # F12 units
    ok12 = any(a["id"] == key["F12"]["objects"][0] for f in F["unit_mismatch"] for a in f["about"])
    row("F12", "pass" if ok12 else "fail", f"card_spend_usd traced to amount_cents with no /100: {'yes' if ok12 else 'no'}")
    # F13 wrong join
    f13 = [f for f in F["suspect_join"] if any("user_id" in a["id"] for a in f["about"]) and
           any(a["id"].endswith("cif_number") for a in f["about"])]
    bridge = f13 and any("online_user" in (t or "") for t in f13[0]["ev"].get("bridge") or [])
    built = f13 and any(a["id"].endswith("web_to_branch_journeys") for a in f13[0]["about"])
    row("F13", verdict(bool(f13) + bool(bridge) + bool(built), 3),
        f"GA4 user_id = cif_number flagged: {'yes' if f13 else 'no'}; the online_user bridge named: "
        f"{'yes' if bridge else 'no'}; traced to web_to_branch_journeys: {'yes' if built else 'no'}")
    # F15 hubs
    hubs = {a["id"] for f in F["hub"] for a in f["about"]}
    o15 = key["F15"]["objects"]
    hit = [o for o in o15 if var_of(o) in hubs]
    row("F15", verdict(len(hit), len(o15)), f"{len(hit)}/{len(o15)} planted hubs flagged ({', '.join(short(o) for o in hit)}); "
        f"{len(hubs)} hubs in total; recovering subjects around them is M4"
        + ("; dim_date.date_day is barely joined in this log, so by usage it is not a hub" if var_of(o15[0]) not in hubs else ""))
    # F16 negative control
    claims = [f for k in ("literal_drift", "straggler", "dead", "write_only", "unit_mismatch", "suspect_join")
              for f in F[k] if re.search(r"(?i)pref_?b?r?a?nch|preferred_branch", (f["title"] or "") + (f["summary"] or ""))]
    row("F16", "pass" if not claims and F["limits"] else "fail",
        "no finding claims preferred_branch_id broke; the pipeline states that data-level breakage is not "
        "determinable from usage" if not claims else f"false claims: {[f['title'] for f in claims]}")
    drv.close()
    (OUT / "M3_SCORE.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "M3_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"variables identifiers P {ip:.0%} R {ir:.0%} ARI {iari:.2f} (consumed: P {lp:.0%} R {lr:.0%} ARI {lari:.2f}); "
          f"others purity {op_:.0%}; "
          f"suspect joins {len(tp)}/{len(flagged)} flagged are wrong, {len(tp)}/{len(wrong)} wrong are flagged")
    print("findings " + "  ".join(f"{k}={v['verdict']}" for k, v in res.items() if k.startswith("F")))
    print(f"-> {OUT / 'M3_SCORE.md'}")


# =============================================================== M4 ======

LAYER_OK = {"raw": {"raw", "unwritten"}, "staging": {"staging"}, "intermediate": {"intermediate", "mart"},
            "mart": {"mart", "intermediate"}, "sandbox": {"sandbox", "unwritten"}, "bi": {"bi"}, "ml": {"ml", "mart"}}


def nmi(pred: dict, true: dict) -> float:
    from math import log
    items = [x for x in pred if x in true]
    n = len(items)
    if not n:
        return 0.0
    pa, pb = Counter(pred[x] for x in items), Counter(true[x] for x in items)
    joint = Counter((pred[x], true[x]) for x in items)
    mi = sum(c / n * log((c / n) / ((pa[a] / n) * (pb[b] / n))) for (a, b), c in joint.items())
    ha = -sum(c / n * log(c / n) for c in pa.values())
    hb = -sum(c / n * log(c / n) for c in pb.values())
    return 2 * mi / (ha + hb) if ha + hb else 1.0


def m4(cfg, names: Names, wh: dict):
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]))
    q = lambda cy, **kw: [r.data() for r in drv.execute_query(cy, database_=n["database"], **kw).records]
    key = json.loads((BUILD / "answer_key.json").read_text())["findings"]
    res, L = {}, ["# M4 score: layers, subjects, copies, sensitive data", "",
                  "Graph: Neo4j `semanticlayer`. Keys: `layer`, `subject` and `domain` on each spec table; planted findings.", ""]
    truth = {names.table(t["fqn"]): t for t in wh["tables"]}
    g = {r["t"]: r for r in q("""MATCH (t:Table)-[:IN_SUBJECT]->(s:Subject)
                                 RETURN t.id AS t, t.layer AS layer, s.id AS subject, t.area AS area,
                                        t.subject_baseline AS b, t.area_baseline AS ba""")}
    lay = {r["t"]: r["l"] for r in q("MATCH (t:Table) WHERE t.layer IS NOT NULL RETURN t.id AS t, t.layer AS l")}
    conf = Counter()
    ok = tot = 0
    for t, tr in truth.items():
        if t not in lay:
            continue
        conf[(tr["layer"], lay[t])] += 1
        if tr["layer"] in LAYER_OK:
            tot += 1
            ok += lay[t] in LAYER_OK[tr["layer"]]
    res["layers"] = {"correct": ok, "total": tot}
    L += ["## Layers", "", f"Behavioural layer vs spec layer: **{ok}/{tot}** ({ok / max(tot, 1):.1%}) on the layers "
          "behaviour can define. A table people consume counts as a mart, and one not written in the window as "
          "unwritten (accepted for raw and sandbox). `legacy` and `ops` are history and purpose labels, with no "
          "behavioural definition; they are shown but not scored.", "",
          "| spec layer | " + " | ".join(sorted({b for _, b in conf})) + " |",
          "|---|" + "---|" * len({b for _, b in conf})]
    for a_ in sorted({a for a, _ in conf}):
        L.append(f"| {a_} | " + " | ".join(str(conf.get((a_, b_), "")) for b_ in sorted({b for _, b in conf})) + " |")
    # subjects
    ts = {t: tr for t, tr in truth.items() if t in g}
    s_true, d_true = {t: tr["subject"] for t, tr in ts.items()}, {t: tr["domain"] for t, tr in ts.items()}
    nm = {"subject": nmi({t: g[t]["subject"] for t in ts}, s_true),
          "domain": nmi({t: g[t]["area"] for t in ts}, d_true),
          "subject_baseline": nmi({t: g[t]["b"] for t in ts}, s_true),
          "domain_baseline": nmi({t: g[t]["ba"] for t in ts}, d_true)}
    res["subjects"] = {**nm, "tables": len(ts), "inferred_subjects": len({g[t]["subject"] for t in ts}),
                       "true_subjects": len(set(s_true.values())), "inferred_areas": len({g[t]["area"] for t in ts}),
                       "true_domains": len(set(d_true.values()))}
    L += ["", "## Subjects", "",
          f"{len(ts)} tables. NMI against the spec's labels (1.0 = identical partitions):", "",
          "| level | hubs link subjects (D7) | hubs count like any key | inferred groups | spec groups |", "|---|---|---|---|---|",
          f"| subject | **{nm['subject']:.3f}** | {nm['subject_baseline']:.3f} | {res['subjects']['inferred_subjects']} | {res['subjects']['true_subjects']} |",
          f"| area vs domain | **{nm['domain']:.3f}** | {nm['domain_baseline']:.3f} | {res['subjects']['inferred_areas']} | {res['subjects']['true_domains']} |", ""]
    F = defaultdict(list)
    for r in q("""MATCH (f:Finding) OPTIONAL MATCH (f)-[a:ABOUT]->(x)
                  RETURN f.id AS id, f.kind AS kind, f.evidence AS ev, collect({id: x.id, role: a.role}) AS about"""):
        r["ev"] = json.loads(r["ev"] or "{}")
        F[r["kind"]].append(r)
    L += ["## Findings", "", "| finding | result | detail |", "|---|---|---|"]

    def row(fid, verdict, detail):
        res[fid] = {"verdict": verdict, "detail": detail}
        L.append(f"| {fid} {key[fid]['title']} | **{verdict}** | {detail} |")
    # F08
    o8 = key["F08"]["objects"]
    exp = {a["id"]: f for f in F["pii_exposure"] for a in f["about"] if a["role"] == "exposed"}
    cand = {a["id"] for f in F["pii_candidate"] for a in f["about"]}
    c1 = o8[2] in exp and any(a["id"] == o8[3] for a in exp[o8[2]]["about"] if a["role"] == "source")
    c2 = [o for o in o8[:2] if o in cand or o in exp]
    got = int(c1) + len(c2)
    row("F08", "pass" if got == 3 else ("partial" if got else "fail"),
        f"sandbox copy of the restricted AML party table flagged with its source: {'yes' if c1 else 'no'}; "
        f"legacy SSN columns flagged by name: {len(c2)}/2; restricted datasets found from access-denied errors")
    # F14
    o14 = [names.table(o) for o in key["F14"]["objects"]]
    fam = next((f for f in F["copy_chain"] if set(o14) <= set(f["ev"].get("order", []))), None)
    checks = [bool(fam), bool(fam) and fam["ev"].get("least_used") == o14[3],
              bool(fam) and o14[1] in fam["ev"].get("stale", []), bool(fam) and fam["ev"].get("top_copy") == o14[2]]
    row("F14", "pass" if all(checks) else ("partial" if any(checks) else "fail"),
        f"all four copies in one family: {'yes' if checks[0] else 'no'}; _FIXED least used: {'yes' if checks[1] else 'no'}; "
        f"_v2 a stale snapshot: {'yes' if checks[2] else 'no'}; _final the most used copy: {'yes' if checks[3] else 'no'}")
    # F15 (subjects half)
    better = nm["subject"] > nm["subject_baseline"] and nm["domain"] > nm["domain_baseline"]
    row("F15", "pass" if better else "partial",
        f"with hubs linking subjects NMI is {nm['subject']:.3f} (subject) / {nm['domain']:.3f} (domain), "
        f"vs {nm['subject_baseline']:.3f} / {nm['domain_baseline']:.3f} when hubs vote like any key")
    drv.close()
    (OUT / "M4_SCORE.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "M4_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"layers {ok}/{tot}; subjects NMI {nm['subject']:.3f} (baseline {nm['subject_baseline']:.3f}), "
          f"domains NMI {nm['domain']:.3f} (baseline {nm['domain_baseline']:.3f})")
    print("findings " + "  ".join(f"{k}={v['verdict']}" for k, v in res.items() if k.startswith("F")))
    print(f"-> {OUT / 'M4_SCORE.md'}")


# =============================================================== M5 ======

CC_TRUTH = {"legacy_edw.CC_TXN_HIST": "credit card", "legacy_edw.CC_ACCT_MSTR": "credit card",
            "legacy_edw.CC_CALL_VOL_DLY": "contact center", "legacy_edw.CC_AGENT_DLY": "contact center",
            "sbx_cx_ops.cc_closure_calls_apr_may": "contact center", "sbx_cx_ops.cc_site_scorecard_2026": "contact center",
            "legacy_edw.CC_EXPNS_MTHLY": "cost center", "gl_erp.CC_EXPENSE_SUMMARY": "cost center"}


def m5(cfg, names: Names, wh: dict):
    sys.path.insert(0, str(ROOT / "pipeline"))
    from retrieve import search
    from semantics import Embedder
    from graphdb import Graph as PG
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]), notifications_min_severity="OFF")
    q = lambda cy, **kw: [r.data() for r in drv.execute_query(cy, database_=n["database"], **kw).records]
    key = json.loads((BUILD / "answer_key.json").read_text())
    res, L = {}, ["# M5 score: naming, embeddings, retrieval", "", f"Model: `{cfg['llm']['model']}`; embeddings: "
                  f"`{cfg['embeddings']['deployment']}` at {cfg['embeddings']['dimensions']} dimensions.", ""]
    # validation
    val = {lab: {r["s"]: r["n"] for r in q(f"MATCH (x:{lab}) WHERE x.description_status IS NOT NULL "
                                          f"RETURN x.description_status AS s, count(*) AS n")}
           for lab in ("Table", "Variable", "Subject")}
    boiler = q("""MATCH (x) WHERE (x:Table OR x:Variable OR x:Subject) AND x.description =~ '(?i).*(as an ai|please provide|i understand|^okay|^sure).*'
                  RETURN count(*) AS n""")[0]["n"]
    res["validation"] = {**val, "boilerplate": boiler}
    L += ["## Descriptions", "", "| | ok first time | ok after one retry | failed (recorded, not dropped) |", "|---|---|---|---|"]
    L += [f"| {lab} | {v.get('ok', 0)} | {v.get('retried', 0)} | {v.get('failed', 0)} |" for lab, v in val.items()]
    L += ["", f"Assistant boilerplate in stored descriptions: {boiler}.", ""]
    # F04
    abbr = {r["t"]: [a["expansion"].lower() for a in json.loads(r["a"] or "[]") if a.get("abbr", "").upper() == "CC"]
            for r in q("MATCH (t:Table) RETURN t.id AS t, t.abbreviations AS a")}
    hits, misses = [], []
    for short_t, want in CC_TRUTH.items():
        t = next((x for x in abbr if x.endswith(short_t)), None)
        got = abbr.get(t, [])
        (hits if got and all(want in g for g in got) else misses).append(f"{short_t} ({', '.join(got) or 'none'})")
    sus = q("""MATCH (f:Finding {kind: 'suspect_join'})-[:ABOUT]->(c:Column) WHERE c.name IN ['CC_ID', 'SITE_CD']
               RETURN count(DISTINCT f) AS n""")[0]["n"]
    ok4 = not misses and sus
    res["F04"] = {"verdict": "pass" if ok4 else ("partial" if hits else "fail"), "hits": hits, "misses": misses}
    L += ["## F04: CC means credit card, contact center, or cost center", "",
          f"**{res['F04']['verdict']}**: CC expanded correctly in {len(hits)}/{len(CC_TRUTH)} tables; "
          f"the CC_ID = SITE_CD join flagged suspect (M3): {'yes' if sus else 'no'}.",
          *([f"- wrong: {m}" for m in misses]), ""]
    # retrieval
    G, emb = PG(cfg), Embedder(cfg)
    Qs = key["questions"]

    def evaluate(**kw):
        r5 = r10 = anyhit = avoid = 0
        rows = []
        for qid, qq in Qs.items():
            exp = {names.table(t) for t in qq.get("expected", [])}
            acc = exp | {names.table(t) for t in qq.get("acceptable", [])}
            av = {names.table(t) for t in (qq.get("avoid") or {})}
            got = [x["table"] for x in search(qq["question"], 10, G, emb, **kw)]
            h5, h10 = len(exp & set(got[:5])) / max(len(exp), 1), len(exp & set(got)) / max(len(exp), 1)
            r5 += h5; r10 += h10; anyhit += bool(acc & set(got[:5])); avoid += len(av & set(got))
            rows.append((qid, h5, h10, len(av & set(got)), got[:3]))
        n_ = len(Qs)
        return {"recall@5": r5 / n_, "recall@10": r10 / n_, "hit@5": anyhit / n_, "avoid_in_top10": avoid}, rows
    full, rows = evaluate()
    tables_only, _ = evaluate(use=("table",))
    no_prior, _ = evaluate(prior=False)
    res["retrieval"] = {"full": full, "tables_only": tables_only, "no_usage_prior": no_prior}
    L += ["## Retrieval: the 14 questions -> tables", "",
          "Recall of each question's expected tables in the top 5 / 10; hit@5 = an expected or acceptable table in the "
          "top 5; avoid = tables the key says not to use (traps, frozen copies) that appear in the top 10. Steering "
          "away from those is M6's job, with the findings; here they only show what retrieval alone brings back.", "",
          "| retrieval | recall@5 | recall@10 | hit@5 | avoid in top 10 |", "|---|---|---|---|---|"]
    for name_, r in (("tables + subjects + variables + usage prior", full), ("tables only", tables_only),
                     ("without the usage prior", no_prior)):
        L.append(f"| {name_} | {r['recall@5']:.0%} | {r['recall@10']:.0%} | {r['hit@5']:.0%} | {r['avoid_in_top10']} |")
    L += ["", "| question | recall@5 | recall@10 | avoid | top 3 |", "|---|---|---|---|---|"]
    L += [f"| {qid} | {a:.0%} | {b:.0%} | {c} | {', '.join(x.split('.', 1)[1] for x in top)} |" for qid, a, b, c, top in rows]
    # proposed domains
    dom = {r["t"]: r["d"] for r in q("MATCH (d:Domain)-[:CONTAINS]->(:Subject)<-[:IN_SUBJECT]-(t:Table) RETURN t.id AS t, d.id AS d")}
    truth_dom = {names.table(t["fqn"]): t["domain"] for t in wh["tables"]}
    area = {r["t"]: r["a"] for r in q("MATCH (t:Table) WHERE t.area IS NOT NULL RETURN t.id AS t, t.area AS a")}
    nd, na = nmi(dom, truth_dom), nmi({t: area[t] for t in dom if t in area}, truth_dom)
    res["domains"] = {"nmi_proposed": nd, "nmi_graph_areas": na, "proposed": len(set(dom.values()))}
    L += ["", "## Proposed domains", "",
          f"The LLM's grouping of named subjects into {len(set(dom.values()))} domains (stored as proposed): NMI "
          f"**{nd:.3f}** against the spec's 15 domains, vs {na:.3f} for M4's graph-only areas.", ""]
    # do identifier variable descriptions mean the right concept?
    concepts = yaml.safe_load((SPECS / "concepts.yaml").read_text())["concepts"]
    ids = {k: c for k, c in concepts.items() if c.get("kind") == "identifier" and not k.startswith("date.")}
    colcon = {}
    for t in wh["tables"]:
        for c in t["columns"]:
            if c.get("concept") in ids:
                colcon[f"{names.table(t['fqn'])}.{c['name']}".lower()] = c["concept"]
    vars_ = defaultdict(Counter)
    vdesc = {}
    for r in q("""MATCH (v:Variable {role: 'identifier'})<-[:IS]-(c:Column) WHERE v.description IS NOT NULL
                  RETURN v.id AS v, v.display_name + '. ' + v.description AS d, c.id AS c"""):
        vdesc[r["v"]] = r["d"]
        if r["c"].lower() in colcon:
            vars_[r["v"]][colcon[r["c"].lower()]] += 1
    labelled = {v: c.most_common(1)[0][0] for v, c in vars_.items() if c}
    ckeys = sorted(ids)
    cvec = emb.embed([f"{k}: {ids[k].get('desc', '')}" for k in ckeys])
    vvec = emb.embed([vdesc[v] for v in labelled])
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    right = sum(1 for (v, want), vv in zip(labelled.items(), vvec)
                if ckeys[max(range(len(ckeys)), key=lambda i: dot(vv, cvec[i]))] == want)
    res["naming"] = {"identifier_variables": len(labelled), "nearest_concept_correct": right}
    L += ["## Do the descriptions mean the right thing?", "",
          f"For {len(labelled)} identifier variables with a tagged concept, the concept whose spec description is "
          f"nearest to the variable's generated description (by embedding) is the right one for **{right}** "
          f"({right / max(len(labelled), 1):.0%}), among {len(ckeys)} identifier concepts.", ""]
    G.close()
    drv.close()
    (OUT / "M5_SCORE.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "M5_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"descriptions {val}; F04={res['F04']['verdict']}; retrieval r@5 {full['recall@5']:.0%} r@10 {full['recall@10']:.0%} "
          f"hit@5 {full['hit@5']:.0%} (tables only r@10 {tables_only['recall@10']:.0%}); domains NMI {nd:.3f} "
          f"(graph areas {na:.3f}); naming {right}/{len(labelled)}")
    print(f"-> {OUT / 'M5_SCORE.md'}")


# =============================================================== M6 ======

JUDGE_MODEL = "claude-sonnet-5"
TRIALS = 3
JUDGE_SYSTEM = """You grade answers to data questions about a bank's BigQuery warehouse against an answer key.
For each requirement, decide whether the answer handles it: in its SQL, or by stating it explicitly (summary,
warnings, cannot_tell). A requirement that is a caveat is met if the answer states it or its SQL deals with it.
pass = handled correctly; partial = gestured at but incomplete or imprecise; fail = missing or wrong.
Be strict and literal: do not credit what the answer does not say or do."""
JUDGE_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
    "type": "object", "required": ["requirement", "verdict", "reason"], "properties": {
        "requirement": {"type": "string"}, "verdict": {"type": "string", "enum": ["pass", "partial", "fail"]},
        "reason": {"type": "string"}}}}}}


def judge(client, question: str, answer: dict, must: list[str]) -> list[dict]:
    import hashlib
    body = {k: answer.get(k) for k in ("summary", "tables", "joins", "sql", "warnings", "cannot_tell")}
    user = (f"Question: {question}\n\nRequirements (from the answer key):\n" +
            "\n".join(f"{i + 1}. {m}" for i, m in enumerate(must)) +
            f"\n\nThe answer:\n{json.dumps(body, indent=1)}")
    key = hashlib.sha256(json.dumps([JUDGE_MODEL, JUDGE_SYSTEM, user]).encode()).hexdigest()
    cache = OUT / "judge_cache"
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    resp = client.messages.create(model=JUDGE_MODEL, max_tokens=3000, system=JUDGE_SYSTEM,
                                  tools=[{"name": "grade", "description": "Record the grades.", "input_schema": JUDGE_SCHEMA}],
                                  tool_choice={"type": "tool", "name": "grade"},
                                  messages=[{"role": "user", "content": user}])
    out = next(b.input for b in resp.content if b.type == "tool_use")["items"]
    if isinstance(out, str):            # the model sometimes sends the array as a JSON string
        out = json.JSONDecoder().raw_decode(out.strip())[0]
    path.write_text(json.dumps(out))
    return out


def sql_facts(sql: str) -> dict:
    """Tables and base-column joins of an answer's SQL, from the parser service (the M1 resolver)."""
    import urllib.request
    port = env().get("PARSER_PORT", "8090")
    body = json.dumps({"id": "a", "sql": sql, "project": "fennmoor-dw", "shape_id": "a"}).encode()
    req = urllib.request.Request(f"http://localhost:{port}/v1/resolve", data=body,
                                 headers={"Content-Type": "application/x-ndjson"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rec = json.loads(r.read().decode().splitlines()[0])
    return {"tables": [t["id"] for t in rec.get("tables") or []],
            "joins": [(f"{j['left']['table']}.{j['left']['column']}", f"{j['right']['table']}.{j['right']['column']}")
                      for j in rec.get("joins") or [] if j.get("op", "=") == "="],
            "status": rec.get("status")}


def m6(cfg, names: Names, wh: dict):
    from concurrent.futures import ThreadPoolExecutor
    import anthropic
    sys.path.insert(0, str(ROOT / "pipeline"))
    from answer import Agent
    key = json.loads((BUILD / "answer_key.json").read_text())
    Qs = key["questions"]
    concepts = yaml.safe_load((SPECS / "concepts.yaml").read_text())["concepts"]
    kind_of = {cid: c.get("kind") for cid, c in concepts.items()}
    concept = {f"{names.table(t['fqn'])}.{c['name']}".lower(): c["concept"]
               for t in wh["tables"] for c in t["columns"] if c.get("concept")}
    ds_proj = {}
    for t in wh["tables"]:
        ds_proj[t["dataset"]] = t["project"]

    def canon(x: str) -> str:
        x = x.strip().strip("`").replace("`", "")
        parts = x.split(".")
        if len(parts) == 2 and parts[0] in ds_proj:
            x = f"{ds_proj[parts[0]]}.{x}"
        return names.table(x) if x.count(".") == 2 else x

    client = anthropic.Anthropic(api_key=env()["ANTHROPIC_API_KEY"])
    res, L = {"trials": TRIALS}, ["# M6 score: answering the 14 questions", ""]

    def grade(qid, qq, rec):
        a = rec["answer"] or {}
        exp = {canon(t) for t in qq.get("expected", [])}
        acc = {canon(t) for t in qq.get("acceptable") or []}
        av = {canon(t) for t in qq.get("avoid") or {}}
        sql = (a.get("sql") or "").strip()
        facts = sql_facts(sql) if sql else {"tables": [], "joins": [], "status": None}
        used = set(facts["tables"]) | {canon(t["table"]) for t in a.get("tables") or []}
        wrong = []
        for x, y in facts["joins"]:
            cx, cy = concept.get(x.lower()), concept.get(y.lower())
            if cx and cy and kind_of.get(cx) == "identifier" and kind_of.get(cy) == "identifier" and cx != cy:
                wrong.append(f"{short(x)} = {short(y)} ({cx} vs {cy})")
        dry = (a.get("dry_run") or {}).get("ok")
        grades = judge(client, qq["question"], a, qq.get("must_handle") or []) if a else []
        mh = sum({"pass": 1, "partial": 0.5}.get(g["verdict"], 0) for g in grades) / max(len(grades), 1)
        recall = len(exp & used) / max(len(exp), 1)
        hits = sorted(av & used)
        return {"recall": recall, "missing": sorted(exp - used), "avoid_used": hits,
                "avoid_named": sorted(av & {canon(x["table"]) for x in a.get("avoided") or []}),
                "extra": sorted(used - exp - acc), "wrong_joins": wrong, "joins": len(facts["joins"]),
                "dry_run": dry, "must_handle": mh, "grades": grades,
                "tables_ok": recall == 1 and not hits and not wrong and dry is not False,
                "tool_calls": len(rec["tool_calls"]), "answered": bool(a)}

    n = len(Qs)
    for mode in ("semantic", "baseline"):
        runs = []
        for trial in range(TRIALS):
            agent = Agent(baseline=(mode == "baseline"), cfg=cfg, trial=trial)
            with ThreadPoolExecutor(4) as pool:
                recs = dict(zip(Qs, pool.map(lambda q: agent.ask(Qs[q]["question"]), Qs)))
            rows = {qid: grade(qid, qq, recs[qid]) for qid, qq in Qs.items()}
            runs.append({"questions": rows, "usage": agent.usage, "summary": {
                "tables_ok": sum(r["tables_ok"] for r in rows.values()),
                "expected_recall": sum(r["recall"] for r in rows.values()) / n,
                "avoid_used": sum(len(r["avoid_used"]) for r in rows.values()),
                "wrong_joins": sum(len(r["wrong_joins"]) for r in rows.values()),
                "dry_run_ok": sum(r["dry_run"] is True for r in rows.values()),
                "with_sql": sum(r["dry_run"] is not None for r in rows.values()),
                "must_handle": sum(r["must_handle"] for r in rows.values()) / n,
                "tool_calls": sum(r["tool_calls"] for r in rows.values())}})
        res[mode] = runs
    avoid_total = sum(len(q.get("avoid") or {}) for q in Qs.values())

    # F18 (negative control): the pipeline must not claim the ledger double count; no answer may add AP invoices
    n = cfg["neo4j"]
    drv = GraphDatabase.driver(n["uri"], auth=(n["user"], env()["NEO4J_PASSWORD"]), notifications_min_severity="OFF")
    claims = drv.execute_query("""MATCH (f:Finding) WHERE toLower(f.summary + f.title) CONTAINS 'vendor_invoice'
                                  AND toLower(f.summary + f.title) =~ '.*(double|twice).*' RETURN count(f) AS n""",
                               database_=n["database"]).records[0]["n"]
    limits = drv.execute_query("MATCH (f:Finding {kind: 'limits'}) RETURN count(f) AS n", database_=n["database"]).records[0]["n"]
    drv.close()
    vi = canon("gl_erp.vendor_invoice")
    adds = sum(vi in run["questions"]["Q01"]["avoid_used"] for run in res["semantic"])
    f18 = not claims and limits and not adds
    res["F18"] = {"verdict": "pass" if f18 else "fail", "claims": claims, "limits_stated": bool(limits),
                  "q01_adds_vendor_invoice": adds}

    def agg(mode, key, fmt, total=None):
        v = [run["summary"][key] for run in res[mode]]
        m = sum(v) / len(v)
        f = (lambda x: f"{x:.0%}") if fmt == "%" else (lambda x: f"{x:.1f}".rstrip("0").rstrip("."))
        return f"{f(m)}{'/' + str(total) if total else ''}" + (f" ({f(min(v))}-{f(max(v))})" if min(v) != max(v) else "")

    model = cfg.get("qa", {}).get("model") or cfg["llm"]["model"]
    cost = {m: sum(run["usage"]["in"] for run in res[m]) / 1e6 * 1 + sum(run["usage"]["out"] for run in res[m]) / 1e6 * 5
            for m in ("semantic", "baseline")}
    L += [f"Agent model: `{model}`; must-handle judge: `{JUDGE_MODEL}`. **Semantic** = the tools over this graph "
          "(pipeline/tools.py); **catalog only** = the same model, prompt skeleton and loop with only BigQuery's "
          "catalog (names, columns, types, partitioning, dry runs). Each mode was run "
          f"{TRIALS} times independently; cells show the mean (min-max).", "",
          "| | semantic layer | catalog only |", "|---|---|---|",
          f"| questions fully right: every expected table, no trap, no wrong join, SQL valid | **{agg('semantic', 'tables_ok', 'n', 14)}** | {agg('baseline', 'tables_ok', 'n', 14)} |",
          f"| expected-table recall | {agg('semantic', 'expected_recall', '%')} | {agg('baseline', 'expected_recall', '%')} |",
          f"| trap tables used (the key lists {avoid_total}) | **{agg('semantic', 'avoid_used', 'n')}** | {agg('baseline', 'avoid_used', 'n')} |",
          f"| joins between different id spaces | {agg('semantic', 'wrong_joins', 'n')} | {agg('baseline', 'wrong_joins', 'n')} |",
          f"| SQL that dry-runs clean | {agg('semantic', 'dry_run_ok', 'n', 12)} | {agg('baseline', 'dry_run_ok', 'n', 12)} |",
          f"| must-handle items (judged; pass 1, partial 0.5) | **{agg('semantic', 'must_handle', '%')}** | {agg('baseline', 'must_handle', '%')} |",
          f"| tool calls per run | {agg('semantic', 'tool_calls', 'n')} | {agg('baseline', 'tool_calls', 'n')} |", "",
          f"Agent LLM cost of the uncached calls this scoring made: semantic ${cost['semantic']:.2f}, catalog only "
          f"${cost['baseline']:.2f} (at $1/$5 per million input/output tokens).", "",
          f"**F18** (negative control: the BPO double count needs domain knowledge): **{res['F18']['verdict']}**. "
          f"No finding claims it ({claims}); the `limits` finding says ledger double counts are not determinable from "
          f"usage ({'stated' if limits else 'missing'}); Q01 answers adding `gl_erp.vendor_invoice`: {adds} of {TRIALS}.", ""]
    for mode, title in (("semantic", "Semantic layer"), ("baseline", "Catalog only")):
        L += [f"## {title}: per question, over {TRIALS} runs", "",
              "| Q | fully right | table recall | tables missed (runs) | traps used (runs) | wrong joins | must-handle | calls |",
              "|---|---|---|---|---|---|---|---|"]
        for qid in Qs:
            rs = [run["questions"][qid] for run in res[mode]]
            miss, trap = Counter(x for r in rs for x in r["missing"]), Counter(x for r in rs for x in r["avoid_used"])
            L.append(f"| {qid} | {sum(r['tables_ok'] for r in rs)}/{TRIALS} | {sum(r['recall'] for r in rs) / TRIALS:.0%} | "
                     f"{', '.join(f'{short(x)} ({c})' for x, c in miss.most_common())} | "
                     f"{', '.join(f'{short(x)} ({c})' for x, c in trap.most_common())} | "
                     f"{sum(len(r['wrong_joins']) for r in rs)} | {sum(r['must_handle'] for r in rs) / TRIALS:.0%} | "
                     f"{sum(r['tool_calls'] for r in rs) / TRIALS:.0f} |")
        L += ["", "Must-handle items not passed, with the judge's reason (first run where it happened):", ""]
        for qid, qq in Qs.items():
            for i, m in enumerate(qq.get("must_handle") or []):
                vs = [run["questions"][qid]["grades"][i] if i < len(run["questions"][qid]["grades"]) else None
                      for run in res[mode]]
                verdicts = [v["verdict"] if v else "missing" for v in vs]
                if all(v == "pass" for v in verdicts):
                    continue
                first = next(v for v in vs if v and v["verdict"] != "pass") if any(v and v["verdict"] != "pass" for v in vs) else None
                L.append(f"- {qid} [{'/'.join(verdicts)}] {m[:100]}" + (f" - {first['reason'][:230]}" if first else ""))
        L += [""]
    (OUT / "M6_SCORE.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "M6_SCORE.md").write_text("\n".join(L) + "\n")
    print(f"M6 ({TRIALS} runs) semantic: fully right {agg('semantic', 'tables_ok', 'n', 14)}, recall "
          f"{agg('semantic', 'expected_recall', '%')}, traps {agg('semantic', 'avoid_used', 'n')}, must-handle "
          f"{agg('semantic', 'must_handle', '%')} | catalog only: {agg('baseline', 'tables_ok', 'n', 14)}, recall "
          f"{agg('baseline', 'expected_recall', '%')}, traps {agg('baseline', 'avoid_used', 'n')}, must-handle "
          f"{agg('baseline', 'must_handle', '%')}; F18 {res['F18']['verdict']}")
    print(f"-> {OUT / 'M6_SCORE.md'}")

if __name__ == "__main__":
    sys.exit(main())

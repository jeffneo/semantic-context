#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "sqlglot>=25", "google-cloud-bigquery>=3.25"]
# ///
"""Generate and validate every query template for the Fennmoor query log.

Two sources:
  code   - derived deterministically from specs/build/warehouse.json and
           specs/templates/bi.yaml: dbt builds/tests/freshness, ingestion
           MERGE and LOAD jobs, the legacy Airflow DAG, Vertex scoring, Looker
           (explores, PDT builds, trigger checks), Tableau, Hightouch,
           Elementary monitors, and the sandbox CTAS statements in the spec.
  human  - hand-written ad-hoc SQL in specs/templates/human/*.yaml, per team.

Template syntax (human and bi.yaml SQL):
  {{name}}              parameter, filled per execution (see PARAM KINDS)
  [[opt: text]]         optional clause - both with and without are shapes
  [[alt: a ;; b ;; c]]  alternatives - each is a shape
  Bodies must not contain ']]'.

Every shape is validated by a BigQuery dry run against the deployed fnb_
estate (results cached in build/.dryrun_cache.json), plus local checks:
references resolve to spec tables, humans stay inside their team's dataset
grants (a wildcard never grants a restricted dataset), unqualified names
resolve in the job's project, and nothing but the monitor reads a dead or
write-only table.

Usage: uv run specs/tools/templates.py --project jeffdavis-bq-testproj
           [--config qlsc] [--prefix fnb_] [--no-dry-run] [--workers 16]
Writes build/templates.json and build/TEMPLATES.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import itertools
import json
import os
import random
import re
import subprocess
import sys
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp

SPECS = Path(__file__).resolve().parent.parent
BUILD = SPECS / "build"
TDIR = SPECS / "templates"

errors: list[str] = []
warnings: list[str] = []


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------

@dataclass
class Template:
    id: str
    family: str
    principal: str                    # service-account key or team name
    principal_kind: str               # service_account | human
    job_project: str
    sql: str = ""
    job_type: str = "QUERY"           # QUERY | LOAD
    destination: str | None = None    # LOAD target (logical fqn, may hold {{params}})
    params: dict = field(default_factory=dict)
    schedule: dict = field(default_factory=dict)
    members: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    active_from: str | None = None
    active_until: str | None = None
    labels: dict = field(default_factory=dict)
    validate_sub: list = field(default_factory=list)   # [(regex, replacement)] for dry run only
    source: str = ""
    notes: str = ""


# ----------------------------------------------------------------------------
# Shapes and parameters
# ----------------------------------------------------------------------------

SHAPE = re.compile(r"\[\[(opt|alt):(.*?)\]\]", re.S)
PARAM = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def expand_shapes(t: Template, cap: int = 6) -> list[str]:
    pieces, slots, pos = [], [], 0
    for m in SHAPE.finditer(t.sql):
        pieces.append(t.sql[pos:m.start()])
        kind, body = m.group(1), m.group(2)
        # alternatives are trimmed (they often sit inside identifiers); optional
        # clauses keep their leading whitespace
        slots.append(["", body] if kind == "opt" else [a.strip() for a in body.split(";;")])
        pos = m.end()
    tail = t.sql[pos:]
    if not slots:
        return [t.sql]
    combos = list(itertools.product(*[range(len(s)) for s in slots]))
    if len(combos) > cap:
        rng = random.Random(t.id)
        first, last = combos[0], tuple(len(s) - 1 for s in slots)
        rest = [c for c in combos if c not in (first, last)]
        combos = [first, last] + rng.sample(rest, cap - 2)
    out = []
    for combo in combos:
        sql = "".join(p + slots[i][c] for i, (p, c) in enumerate(zip(pieces, combo))) + tail
        out.append(sql)
    return out


def months_back(d: dt.date, n: int) -> dt.date:
    y, m = d.year, d.month + n
    while m <= 0:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return dt.date(y, m, 1)


def render_param(spec: str, rng: random.Random, run: dt.date) -> str:
    kind, _, arg = str(spec).partition(":")
    lo = hi = 0
    if ".." in arg:
        a, b = arg.split("..")
        lo, hi = int(a), int(b)
    if kind == "date":
        return (run + dt.timedelta(days=rng.randint(lo, hi))).isoformat()
    if kind == "month":
        return months_back(run, rng.randint(lo, hi)).isoformat()
    if kind == "suffix":
        return (run + dt.timedelta(days=rng.randint(lo, hi))).strftime("%Y%m%d")
    if kind == "yyyymm":
        return months_back(run, rng.randint(lo, hi)).strftime("%Y%m")
    if kind == "period":
        return months_back(run, rng.randint(lo, hi)).strftime("%b-%y").upper()
    if kind == "int":
        return str(rng.randint(lo, hi))
    if kind == "choice":
        return rng.choice(arg.split("|"))
    if kind == "cif":
        return f"{rng.randint(1, 2430000):010d}"
    if kind in ("core_account_id", "card_account_id"):
        return str(rng.randint(1000000, 99999999))
    if kind == "uuid":
        return str(uuid.UUID(int=rng.getrandbits(128)))
    if kind == "hex":
        return "".join(rng.choice("0123456789abcdef") for _ in range(int(arg or 8)))
    if kind == "olb_user_id":
        return f"OLB{rng.randint(10000000, 99999999)}"
    if kind == "looker_ctx":
        ctx = {"user_id": rng.randint(40, 400), "history_slug": "".join(rng.choice("0123456789abcdef") for _ in range(13)),
               "instance_slug": "7e3f0c2b9a4d4f1e8c6b5a0d3e2f1a9b"}
        return json.dumps(ctx, separators=(",", ":"))
    raise ValueError(f"unknown param kind {spec!r}")


def render(sql: str, params: dict, rng: random.Random, run: dt.date) -> str:
    def repl(m):
        name = m.group(1)
        if name not in params:
            raise KeyError(name)
        return render_param(params[name], rng, run)
    return PARAM.sub(repl, sql)


# ----------------------------------------------------------------------------
# References
# ----------------------------------------------------------------------------

class Estate:
    def __init__(self, wh: dict):
        self.wh = wh
        self.tables = {t["fqn"]: t for t in wh["tables"]}
        self.by_key = {f"{t['dataset']}.{t['name']}": t for t in wh["tables"]}
        self.datasets = wh["datasets"]
        self.shard_prefixes = {t["fqn"][:-1]: t["fqn"] for t in wh["tables"] if t["fqn"].endswith("*")}
        self.member_team = {m: team for team, d in wh["teams"].items() for m in d["members"]}

    def project_of(self, ds: str) -> str:
        return self.datasets[ds]["project"]

    def logical(self, catalog: str, db: str, name: str, job_project: str) -> str | None:
        proj = catalog or job_project
        fqn = f"{proj}.{db}.{name}"
        if fqn in self.tables:
            return fqn
        for prefix, sharded in self.shard_prefixes.items():
            if fqn.startswith(prefix) and re.fullmatch(r"\*|\d{6}|\d{8}", fqn[len(prefix):]):
                return sharded
        return None


def statement_target(stmt) -> exp.Table | None:
    if isinstance(stmt, (exp.Create, exp.Insert, exp.Merge, exp.Delete, exp.Update)):
        node = stmt.this
        if isinstance(node, exp.Schema):
            node = node.this
        return node if isinstance(node, exp.Table) else None
    return None


def table_refs(sql: str, job_project: str, est: Estate, where: str):
    """(reads, writes) as logical fqns, or None if sqlglot cannot parse."""
    try:
        stmts = [s for s in sqlglot.parse(sql, read="bigquery") if s is not None]
    except Exception:
        return None
    reads, writes = set(), set()
    for stmt in stmts:
        ctes = {c.alias_or_name for c in stmt.find_all(exp.CTE)}
        target = statement_target(stmt)
        for tbl in stmt.find_all(exp.Table):
            if not tbl.db and tbl.name in ctes:
                continue
            if "INFORMATION_SCHEMA" in tbl.sql(dialect="bigquery").upper() or tbl.db.lower().startswith("region-"):
                continue
            if not tbl.db:
                continue                 # UNNEST alias, table function, etc.
            if tbl.db in ("fivetran_staging",):
                continue
            fqn = est.logical(tbl.catalog, tbl.db, tbl.name, job_project)
            if fqn is None:
                err(f"{where}: references {'.'.join(p for p in (tbl.catalog, tbl.db, tbl.name) if p)}, not in the spec")
                continue
            (writes if tbl is target else reads).add(fqn)
    return reads, writes


def err(m):
    errors.append(m)


def warn(m):
    warnings.append(m)


# ----------------------------------------------------------------------------
# Physical rewrite (validation only)
# ----------------------------------------------------------------------------

def make_physical(est: Estate, project: str, prefix: str):
    ds_alt = "|".join(sorted(est.datasets, key=len, reverse=True))
    dbt_q = re.compile(r"`fennmoor-(?:raw|dw|analytics)`\.`([A-Za-z0-9_]+)`\.`([^`]+)`")
    full = re.compile(r"`fennmoor-(?:raw|dw|analytics)\.([A-Za-z0-9_-]+)((?:\.[^`]*)?)`")
    region = re.compile(r"`fennmoor-(?:raw|dw|analytics)`\.`?(region-us)`?")
    bare = re.compile(r"(?<![\w.`-])(`?)(" + ds_alt + r")\.([A-Za-z_][A-Za-z0-9_]*\*?)(`?)")

    def physical(sql: str) -> tuple[str, list[str]]:
        sql = dbt_q.sub(lambda m: f"`{project}.{prefix}{m[1]}.{m[2]}`", sql)
        sql = region.sub(f"`{project}.region-us`", sql)
        sql = full.sub(lambda m: (f"`{project}.{m[1]}{m[2]}`" if m[1].startswith("region-")
                                  else f"`{project}.{prefix}{m[1]}{m[2]}`"), sql)
        unq = []

        def b(m):
            unq.append(m[2])
            return f"`{project}.{prefix}{m[2]}.{m[3]}`"
        # never rewrite inside string literals ('dw_core.dim_customer' as a value)
        parts = re.split(r"('(?:[^'\\]|\\.)*')", sql)
        sql = "".join(p if i % 2 else bare.sub(b, p) for i, p in enumerate(parts))
        return sql, unq
    return physical


# ----------------------------------------------------------------------------
# Code-generated families
# ----------------------------------------------------------------------------

def dbt_quote(sql: str) -> str:
    return re.sub(r"`(fennmoor-[a-z]+)\.([A-Za-z0-9_]+)\.([^`.]+)`", r"`\1`.`\2`.`\3`", sql)


def fq(t: dict) -> str:
    return f"`{t['fqn']}`"


def pk_cols(t: dict) -> list[str]:
    return [c["name"] for c in t["columns"] if c.get("flags", {}).get("pk")]


def part_col(t: dict) -> str | None:
    p = t.get("partition")
    if not p:
        return None
    m = re.fullmatch(r"DATE\((\w+)\)", p)
    return f"DATE({m.group(1)})" if m else p


def dbt_comment(name: str) -> str:
    return ('/* {"app": "dbt", "dbt_version": "1.9.4", "profile_name": "fennmoor", '
            f'"target_name": "prod", "node_id": "model.fennmoor.{name}"}} */\n')


def refresh_schedule(refresh: str | None) -> dict:
    r = refresh or ""
    if "hourly" in r:
        return {"every": "1h"}
    m = re.search(r"(\d{2}):?(\d{2})", r)
    if m:
        return {"cron": f"{int(m.group(2))} {int(m.group(1))} * * *"}
    m = re.search(r"-(\d+)(m|h)$", r)
    if m:
        return {"every": f"{m.group(1)}{m.group(2)}"}
    if "monthly" in r:
        return {"cron": "0 6 2 * *"}
    if "daily" in r:
        return {"cron": "0 5 * * *"}
    return {"cron": "0 2 * * *"}


def gen_dbt(est: Estate) -> list[Template]:
    out = []
    for t in est.wh["tables"]:
        if t.get("writer") != "dbt-prod" or "sql" not in t or t.get("status") == "dead":
            continue
        body = dbt_quote(t["sql"])
        target = dbt_quote(fq(t))
        mat = t["materialized"]
        sched = refresh_schedule(t.get("refresh"))
        labels = {"dbt_invocation_id": "{{invocation}}", "dbt_node": t["name"]}
        head = dbt_comment(t["name"])
        pc = part_col(t)
        if mat == "view":
            sql = f"{head}create or replace view {target}\n  OPTIONS()\n  as {body};\n"
        elif mat == "incremental":
            filt = (f"select * from (\n{body}\n) where {pc} >= date_sub(current_date(), interval 3 day)"
                    if pc else body)
            cols = [c["name"] for c in t["columns"]]
            pks = pk_cols(t)
            if pks:
                on = " and ".join(f"DBT_INTERNAL_SOURCE.{k} = DBT_INTERNAL_DEST.{k}" for k in pks)
                sets = ",\n        ".join(f"`{c}` = DBT_INTERNAL_SOURCE.`{c}`" for c in cols)
                collist = ", ".join(f"`{c}`" for c in cols)
                sql = (f"{head}merge into {target} as DBT_INTERNAL_DEST\n    using (\n{filt}\n    ) as DBT_INTERNAL_SOURCE\n"
                       f"    on ({on})\n\n    when matched then update set\n        {sets}\n\n"
                       f"    when not matched then insert\n        ({collist})\n    values\n        ({collist})\n")
            else:
                cond = (f" and {pc.replace(pc.split('(')[-1].rstrip(')'), 'DBT_INTERNAL_DEST.' + pc.split('(')[-1].rstrip(')'))}"
                        f" >= date_sub(current_date(), interval 3 day)") if pc else ""
                sql = (f"{head}merge into {target} as DBT_INTERNAL_DEST\n      using (\n{filt}\n      ) as DBT_INTERNAL_SOURCE\n"
                       f"      on FALSE\n\n  when not matched by source{cond}\n      then delete\n\n"
                       f"  when not matched then insert row\n")
        else:
            opts = ""
            if t.get("partition"):
                opts += f"\n  partition by {t['partition']}"
            if t.get("cluster"):
                opts += f"\n  cluster by {', '.join(t['cluster'])}"
            sql = f"{head}create or replace table {target}{opts}\n  OPTIONS()\n  as (\n{body}\n  );\n"
        out.append(Template(f"dbt.build.{t['name']}", "dbt_build", "dbt-prod", "service_account",
                            "fennmoor-dw", sql, params={"invocation": "uuid"}, schedule=sched,
                            labels=labels, source="warehouse.json"))
    return out


DBT_TEST_HEAD = ("select\n      count(*) as failures,\n      count(*) != 0 as should_warn,\n"
                 "      count(*) != 0 as should_error\n    from (\n")


def gen_dbt_tests(est: Estate) -> list[Template]:
    out = []
    parents = {"customer.key": "dw_core.dim_customer", "account.key": "dw_core.dim_account"}
    for t in est.wh["tables"]:
        if t.get("writer") != "dbt-prod" or "sql" not in t or t.get("status") == "dead":
            continue
        target = dbt_quote(fq(t))
        pks = pk_cols(t)
        if len(pks) == 1:
            k = pks[0]
            for kind, inner in (
                ("not_null", f"\n\n\nselect {k}\nfrom {target}\nwhere {k} is null\n\n\n\n"),
                ("unique", f"\n\nselect\n    {k} as unique_field,\n    count(*) as n_records\n\nfrom {target}\n"
                           f"where {k} is not null\ngroup by {k}\nhaving count(*) > 1\n\n\n")):
                sql = dbt_comment(f"{kind}_{t['name']}_{k}").replace("model.fennmoor", "test.fennmoor") + \
                      DBT_TEST_HEAD + inner + "    ) dbt_internal_test"
                out.append(Template(f"dbt.test.{kind}.{t['name']}.{k}", "dbt_test", "dbt-prod", "service_account",
                                    "fennmoor-dw", sql, schedule={"cron": "45 2 * * *"}, source="warehouse.json"))
        if t["layer"] != "mart":
            continue
        for c in t["columns"]:
            parent_key = parents.get(c.get("concept"))
            if not parent_key or t["name"] == parent_key.split(".")[1] or c.get("flags", {}).get("pk"):
                continue
            p = est.by_key[parent_key]
            pcol = pk_cols(p)[0]
            inner = (f"\nwith child as (\n    select {c['name']} as from_field\n    from {target}\n"
                     f"    where {c['name']} is not null\n),\n\nparent as (\n    select {pcol} as to_field\n"
                     f"    from {dbt_quote(fq(p))}\n)\n\nselect\n    from_field\n\nfrom child\nleft join parent\n"
                     f"    on child.from_field = parent.to_field\n\nwhere parent.to_field is null\n\n")
            sql = dbt_comment(f"relationships_{t['name']}_{c['name']}").replace("model.fennmoor", "test.fennmoor") + \
                  DBT_TEST_HEAD + inner + "    ) dbt_internal_test"
            out.append(Template(f"dbt.test.relationships.{t['name']}.{c['name']}", "dbt_test", "dbt-prod",
                                "service_account", "fennmoor-dw", sql, schedule={"cron": "45 2 * * *"},
                                source="warehouse.json"))
    return out


def loaded_at_expr(t: dict, mixins: dict) -> str | None:
    for m in t.get("mixins", []) or []:
        e = mixins.get(m, {}).get("loaded_at")
        if e:
            return e.replace("src.", "")
    return None


def gen_ingest(est: Estate, estate_yaml: dict) -> list[Template]:
    out = []
    mixins = estate_yaml.get("mixins", {})
    raw_specs = {}
    for f in sorted((SPECS / "warehouse").glob("1*.yaml")):
        for doc in yaml.safe_load_all(f.read_text()):
            for t in doc.get("tables", []):
                raw_specs[f"{doc['dataset']}.{t['name']}"] = {**doc.get("defaults", {}), **t}
    for key, spec in raw_specs.items():
        t = est.by_key[key]
        mx = spec.get("mixins", []) or []
        refresh = spec.get("refresh", "")
        # dbt source freshness, hourly, for staged sources that carry a loaded-at column
        la = loaded_at_expr(spec, mixins)
        if la and spec.get("stage") is not False and t.get("status") != "dead":
            sql = (f"select max({la}) as max_loaded_at,\n  current_timestamp() as snapshotted_at\n"
                   f"from {dbt_quote(fq(t))}\n")
            out.append(Template(f"dbt.freshness.{key}", "dbt_freshness", "dbt-prod", "service_account",
                                "fennmoor-dw", '/* {"app": "dbt", "node_id": "source.fennmoor.' + key + '"} */\n' + sql,
                                schedule={"cron": "15 * * * *"}, source="warehouse.json"))
        if "fivetran" in mx or "fivetran_salesforce" in mx:
            cols = [c["name"] for c in t["columns"]]
            keys = pk_cols(t) or cols[:1]
            stg = f"`fennmoor-raw.fivetran_staging.{t['dataset']}_{t['name']}_{{{{batch}}}}`"
            on = " AND ".join(f"T.`{k}` = S.`{k}`" for k in keys)
            sets = ", ".join(f"`{c}` = S.`{c}`" for c in cols if c not in keys)
            collist = ", ".join(f"`{c}`" for c in cols)
            vals = ", ".join(f"S.`{c}`" for c in cols)
            sql = (f"MERGE {fq(t)} AS T\nUSING {stg} AS S\nON {on}\n"
                   f"WHEN MATCHED THEN UPDATE SET {sets}\n"
                   f"WHEN NOT MATCHED THEN INSERT ({collist}) VALUES ({vals})")
            out.append(Template(f"ingest.fivetran.{key}", "ingest_merge", "fivetran-sync", "service_account",
                                "fennmoor-raw", sql, params={"batch": "hex:12"}, schedule=refresh_schedule(refresh),
                                labels={"fivetran_connector": t["dataset"]},
                                validate_sub=[(r"`fennmoor-raw\.fivetran_staging\.[^`]+`",
                                               f"(SELECT * FROM {fq(t)} WHERE FALSE)")],
                                source="warehouse.json"))
        elif "sftp_file" in mx:
            out.append(Template(f"ingest.file.{key}", "ingest_load", "file-loader", "service_account",
                                "fennmoor-raw", job_type="LOAD", destination=t["fqn"],
                                schedule=refresh_schedule(refresh), source="warehouse.json"))
        elif "manual_upload" in mx:
            out.append(Template(f"ingest.manual.{key}", "ingest_load", "data_engineering", "human",
                                "fennmoor-raw", job_type="LOAD", destination=t["fqn"],
                                schedule={"cadence": "monthly"}, members=["ben.adeyemi"], source="warehouse.json"))
        elif t["dataset"] == "analytics_312874659":
            out.append(Template(f"ingest.ga4.{t['name']}", "ingest_load", "ga4-export", "service_account",
                                "fennmoor-raw", job_type="LOAD",
                                destination=t["fqn"].rstrip("*") + "{{shard}}",
                                params={"shard": "suffix:-1..-1"}, schedule={"cron": "30 6 * * *"},
                                source="warehouse.json"))
        elif t["dataset"] == "amplitude_mobile":
            out.append(Template(f"ingest.amplitude.{t['name']}", "ingest_load", "amplitude-export",
                                "service_account", "fennmoor-raw", job_type="LOAD", destination=t["fqn"],
                                schedule={"every": "1h"}, source="warehouse.json"))
        # core_banking_cdc: Datastream writes through the Storage Write API - no jobs.
    return out


def gen_legacy(est: Estate) -> list[Template]:
    out = []
    for key, date_col, cron, when in (("legacy_edw.ACCT_DLY_BAL", "b.BAL_DT", "30 5 * * *", "DATE '{{ds}}'"),
                                      ("legacy_edw.EOM_BAL_SNAP", "b.BAL_DT", "0 6 2 * *", "DATE '{{month_end}}'")):
        t = est.by_key[key]
        cols = ", ".join(c["name"] for c in t["columns"])
        target_col = "BAL_DT" if key.endswith("ACCT_DLY_BAL") else "SNAP_MTH"
        del_val = when if key.endswith("ACCT_DLY_BAL") else "DATE_TRUNC(DATE '{{month_end}}', MONTH)"
        params = {"ds": "date:-1..-1"} if "ds" in when else {"month_end": "date:-2..-2"}
        joiner = "\nAND " if "WHERE" in t["sql"] else "\nWHERE "
        out.append(Template(f"legacy.delete.{t['name']}", "legacy_dag", "composer-legacy", "service_account",
                            "fennmoor-analytics", f"DELETE FROM {fq(t)} WHERE {target_col} = {del_val}",
                            params=params, schedule={"cron": cron}, labels={"airflow_dag": "edw_nightly_balances"},
                            source="warehouse.json"))
        out.append(Template(f"legacy.insert.{t['name']}", "legacy_dag", "composer-legacy", "service_account",
                            "fennmoor-analytics", f"INSERT INTO {fq(t)} ({cols})\n{t['sql']}{joiner}{date_col} = {when}",
                            params=params, schedule={"cron": cron}, labels={"airflow_dag": "edw_nightly_balances"},
                            source="warehouse.json"))
    return out


def gen_vertex(est: Estate, window: dict) -> list[Template]:
    cut = next(e["date"] for e in window["events"] if e["id"] == "churn_v3_cutover")
    cut = dt.date.fromisoformat(str(cut))
    before = (cut - dt.timedelta(days=1)).isoformat()
    out = [Template("vertex.read.feat_customer_daily", "vertex", "vertex-scoring", "service_account", "fennmoor-dw",
                    "SELECT * FROM `fennmoor-dw.ml_features.feat_customer_daily` WHERE as_of_date = '{{ds}}'",
                    params={"ds": "date:0..0"}, schedule={"cron": "0 4 * * *"}, source="warehouse.json")]
    for name, frm, until in (("churn_score_v2", None, before), ("churn_score_v3", cut.isoformat(), None),
                             ("next_best_offer", None, None)):
        t = est.by_key[f"ml_scores.{name}"]
        out.append(Template(f"vertex.load.{name}", "vertex", "vertex-scoring", "service_account", "fennmoor-dw",
                            job_type="LOAD", destination=t["fqn"], schedule={"cron": "20 4 * * *"},
                            active_from=frm, active_until=until, source="warehouse.json"))
    return out


def gen_sandbox_ctas(est: Estate, window: dict) -> list[Template]:
    start = dt.date.fromisoformat(str(window["start"]))
    end = start + dt.timedelta(days=window["days"] - 1)
    out = []
    for t in est.wh["tables"]:
        writer = t.get("writer") or ""
        if "sql" not in t or writer not in est.member_team:
            continue
        created = dt.date.fromisoformat(str(t["created"])) if t.get("created") else None
        in_window = created is not None and start <= created <= end
        status = t.get("status", "active")
        sql = f"CREATE OR REPLACE TABLE {fq(t)} AS\n{t['sql']}"
        base = dict(family="sandbox_ctas", principal=est.member_team[writer], principal_kind="human",
                    job_project="fennmoor-analytics", sql=sql, members=[writer], source="warehouse.json")
        if in_window:
            out.append(Template(f"ctas.once.{t['dataset']}.{t['name']}", **base,
                                schedule={"once": created.isoformat()}))
        if status == "active":
            out.append(Template(f"ctas.{t['dataset']}.{t['name']}", **base,
                                schedule={"cadence": t.get("cadence", "monthly")},
                                active_from=created.isoformat() if in_window else None))
    return out


def gen_looker_pdts(est: Estate) -> list[Template]:
    out = []
    for t in est.wh["tables"]:
        if t["dataset"] != "looker_scratch" or "sql" not in t or t.get("status") == "dead":
            continue
        ctx = "-- Looker Query Context '{\"user_id\":null,\"history_slug\":null,\"instance_slug\":\"7e3f0c2b9a4d4f1e8c6b5a0d3e2f1a9b\"}'\n"
        out.append(Template(f"looker.pdt.{t['name']}", "looker_pdt", "looker-prod", "service_account",
                            "fennmoor-analytics", f"{ctx}CREATE OR REPLACE TABLE {fq(t)} AS {t['sql']}",
                            schedule={"cron": "0 6 * * *"}, source="warehouse.json"))
        # datagroup trigger: MAX of the source's date column, checked every 5 minutes
        src = est.tables.get(t["sources"][0]) if t.get("sources") else None
        date_col = None
        if src:
            date_col = (part_col(src) or next((c["name"] for c in src["columns"]
                                               if c.get("concept") == "date.day"), None))
        trig = (f"SELECT MAX({date_col}) FROM {fq(src)}" if date_col else "SELECT CURRENT_DATE()")
        out.append(Template(f"looker.trigger.{t['name']}", "looker_trigger", "looker-prod", "service_account",
                            "fennmoor-analytics", trig, schedule={"every": "5m"}, source="warehouse.json"))
    return out


def gen_hightouch(est: Estate) -> list[Template]:
    return [Template(f"hightouch.sync.{t['name']}", "hightouch_sync", "hightouch-sync", "service_account",
                     "fennmoor-analytics", f"SELECT * FROM {fq(t)}", schedule={"every": "1h"},
                     labels={"hightouch_sync": t["name"]}, source="warehouse.json")
            for t in est.wh["tables"] if t["dataset"] == "reverse_etl" and t.get("status") != "dead"]


MONITORED_LAYERS = {"raw", "staging", "intermediate", "mart", "ml", "legacy"}


def gen_dq(est: Estate, estate_yaml: dict) -> list[Template]:
    mixins = estate_yaml.get("mixins", {})
    raw_specs = {}
    for f in sorted((SPECS / "warehouse").glob("1*.yaml")):
        for doc in yaml.safe_load_all(f.read_text()):
            for t in doc.get("tables", []):
                raw_specs[f"{doc['dataset']}.{t['name']}"] = {**doc.get("defaults", {}), **t}
    out = []
    for t in est.wh["tables"]:
        if t["layer"] not in MONITORED_LAYERS:
            continue
        key = f"{t['dataset']}.{t['name']}"
        pc = part_col(t)
        if t.get("shard"):
            src, filt = fq(t), ("\nWHERE _TABLE_SUFFIX = FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))"
                                 if t["shard"]["suffix"] == "YYYYMMDD" else "")
        else:
            src, filt = fq(t), (f"\nWHERE {pc} >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)" if pc else "")
        lbl = {"elementary_monitor": "volume"}
        out.append(Template(f"dq.volume.{key}", "dq_monitor", "elementary-dq", "service_account",
                            "fennmoor-analytics", f"SELECT COUNT(*) AS row_count FROM {src}{filt}",
                            schedule={"every": "4h"}, labels=lbl, source="warehouse.json"))
        ts = (loaded_at_expr(raw_specs.get(key, {}), mixins)
              or ("_loaded_at" if any(c["name"] == "_loaded_at" for c in t["columns"]) else None)
              or pc)
        if ts:
            out.append(Template(f"dq.freshness.{key}", "dq_monitor", "elementary-dq", "service_account",
                                "fennmoor-analytics", f"SELECT MAX({ts}) AS max_ts FROM {src}",
                                schedule={"every": "4h"}, labels={"elementary_monitor": "freshness"},
                                source="warehouse.json"))
        keys = [c["name"] for c in t["columns"] if c.get("flags", {}).get("pk") or c.get("flags", {}).get("required")][:2]
        if keys:
            sel = ", ".join(f"COUNTIF({k} IS NULL) AS {k}_nulls" for k in keys)
            out.append(Template(f"dq.nulls.{key}", "dq_monitor", "elementary-dq", "service_account",
                                "fennmoor-analytics", f"SELECT {sel}, COUNT(*) AS total_rows FROM {src}{filt}",
                                schedule={"every": "4h"}, labels={"elementary_monitor": "null_rate"},
                                source="warehouse.json"))
    for name, ts in (("elementary_test_results", "detected_at"), ("dbt_run_results", "generated_at"),
                     ("freshness_checks", "checked_at")):
        out.append(Template(f"dq.report.{name}", "dq_report", "data_engineering", "human", "fennmoor-analytics",
                            f"SELECT * FROM `fennmoor-analytics.data_quality.{name}`\n"
                            f"WHERE {ts} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)",
                            schedule={"cron": "0 8 * * 1-5"}, members=["marcus.lindqvist"],
                            notes="`edr report`, run each weekday morning", source="warehouse.json"))
    out.append(Template("dq.write.results", "dq_monitor", "elementary-dq", "service_account", "fennmoor-analytics",
                        "INSERT INTO `fennmoor-analytics.data_quality.elementary_test_results` "
                        "(test_result_id, test_name, model_fqn, column_name, status, failures, severity, detected_at)\n"
                        "VALUES ('{{rid}}', '{{test}}', '{{model}}', NULL, 'pass', 0, 'warn', CURRENT_TIMESTAMP())",
                        params={"rid": "uuid", "test": "choice:volume_anomalies|freshness_anomalies|null_rate",
                                "model": "choice:dw_core.dim_customer|dw_core.fct_card_transactions|dw_contact_center.fct_calls"},
                        schedule={"every": "4h"}, source="warehouse.json"))
    return out


# ----------------------------------------------------------------------------
# bi.yaml (Looker explores, Tableau) and human templates
# ----------------------------------------------------------------------------

def load_yaml_templates(est: Estate) -> list[Template]:
    out = []
    for f in sorted((TDIR / "human").glob("*.yaml")) if (TDIR / "human").exists() else []:
        doc = yaml.safe_load(f.read_text()) or {}
        team = doc["team"]
        if team not in est.wh["teams"]:
            err(f"{f.name}: unknown team {team!r}")
            continue
        for t in doc.get("templates", []):
            members = t.get("by", [])
            for m in members:
                if est.member_team.get(m) != team:
                    err(f"{f.name}:{t['id']}: {m} is not in team {team}")
            act = t.get("active", {}) or {}
            out.append(Template(t["id"], "human", team, "human", "fennmoor-analytics", t["sql"],
                                params=t.get("params", {}) or {},
                                schedule={"weight": t.get("weight", 1), "cadence": t.get("cadence", "adhoc")},
                                members=members, findings=t.get("findings", []) or [],
                                active_from=str(act["from"]) if act.get("from") else None,
                                active_until=str(act["until"]) if act.get("until") else None,
                                source=f.name, notes=t.get("notes", "")))
    bi = TDIR / "bi.yaml"
    if bi.exists():
        out += gen_bi(yaml.safe_load(bi.read_text()), est)
    return out


LOOKER_DATE_FILTER = ("((( {f} ) >= ((DATE_ADD(CURRENT_DATE('America/Chicago'), INTERVAL -{n} DAY))) AND "
                      "( {f} ) < ((DATE_ADD(DATE_ADD(CURRENT_DATE('America/Chicago'), INTERVAL -{n} DAY), INTERVAL {n} DAY)))))")


def looker_sql(explore: dict, name: str, dims: list, measures: list, filters: list, days: int | None,
               sort_desc: bool, limit: int) -> str:
    base = explore["view"]
    sel = [f"    {explore['dimensions'][d]}  AS {base}_{d}" for d in dims]
    sel += [f"    {explore['measures'][m]} AS {base}_{m}" for m in measures]
    where = []
    if days and explore.get("date_field"):
        where.append(LOOKER_DATE_FILTER.format(f=explore["date_field"], n=days))
    where += [explore["filters"][f] for f in filters]
    # Looker only joins the views whose fields the query uses
    used = " ".join(sel + where)
    joins = "".join(f"\n{j}" for j in explore.get("joins", [])
                    if re.search(r"AS (\w+) ON", j) and f"{re.search(r'AS (\w+) ON', j).group(1)}." in used)
    sql = ("-- Looker Query Context '{{ctx}}'\nSELECT\n" + ",\n".join(sel) +
           f"\nFROM `{explore['from']}`  AS {base}{joins}")
    if where:
        sql += "\nWHERE " + " AND ".join(where)
    if dims:
        sql += "\nGROUP BY\n    " + ",\n    ".join(str(i + 1) for i in range(len(dims)))
    if measures:
        sql += f"\nORDER BY\n    {len(dims) + 1} DESC" if sort_desc else ""
    sql += f"\nLIMIT {limit}"
    return sql


def gen_bi(bi: dict, est: Estate) -> list[Template]:
    out = []
    for name, ex in (bi.get("explores") or {}).items():
        rng = random.Random(name)
        users = ex.get("users", [])
        fparams = ex.get("filter_params", {})
        # dashboard tiles: fixed shapes, refreshed on schedule and on view
        for i, tile in enumerate(ex.get("tiles", [])):
            sql = looker_sql(ex, name, tile.get("dims", []), tile["measures"], tile.get("filters", []),
                             tile.get("days", ex.get("default_days")), True, tile.get("limit", 500))
            out.append(Template(f"looker.tile.{name}.{i}", "looker_query", "looker-prod", "service_account",
                                "fennmoor-analytics", sql, params={"ctx": "looker_ctx", **fparams},
                                schedule={"weight": tile.get("weight", 3), "cadence": "dashboard"},
                                members=users, findings=ex.get("findings", []), source="bi.yaml"))
        # explore sessions: sampled combinations of dimensions, measures, filters
        dims, meas, filts = list(ex["dimensions"]), list(ex["measures"]), list(ex.get("filters", {}))
        seen = set()
        for i in range(ex.get("explore_shapes", 0)):
            d = sorted(rng.sample(dims, rng.randint(1, min(3, len(dims)))))
            m = sorted(rng.sample(meas, rng.randint(1, min(3, len(meas)))))
            f = sorted(rng.sample(filts, rng.randint(0, min(2, len(filts))))) if filts else []
            days = None if ex.get("date_optional") and rng.random() < 0.3 else rng.choice([7, 30, 90, 365])
            key = (tuple(d), tuple(m), tuple(f), days)
            if key in seen:
                continue
            seen.add(key)
            finds = list(ex.get("findings", []))
            if days is None and ex.get("unfiltered_finding"):
                finds.append(ex["unfiltered_finding"])
            out.append(Template(f"looker.explore.{name}.{i}", "looker_query", "looker-prod", "service_account",
                                "fennmoor-analytics", looker_sql(ex, name, d, m, f, days, rng.random() < 0.7,
                                                                 rng.choice([500, 500, 5000])),
                                params={"ctx": "looker_ctx", **fparams},
                                schedule={"weight": 1, "cadence": "adhoc"}, members=users, findings=finds,
                                source="bi.yaml"))
    for i, tb in enumerate(bi.get("tableau") or []):
        sql = tb.get("sql")
        if tb.get("extract"):
            t = est.by_key[tb["extract"]]
            a = t["name"]
            proj, ds, name = t["fqn"].split(".")
            cols = ",\n  ".join(f"`{a}`.`{c['name']}` AS `{c['name']}`" for c in t["columns"])
            sql = f"SELECT {cols}\nFROM `{proj}`.`{ds}`.`{name}` `{a}`"
        out.append(Template(f"tableau.{tb['id']}", "tableau", "tableau-finance", "service_account",
                            "fennmoor-analytics", sql, params=tb.get("params", {}) or {},
                            schedule=tb.get("schedule", {"cron": "0 3 * * *"}),
                            findings=tb.get("findings", []) or [], source="bi.yaml"))
    return out


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------

def team_can_read(est: Estate, team: str, ds: str) -> bool:
    grants = est.wh["teams"][team]["reads"]
    restricted = est.datasets.get(ds, {}).get("restricted")
    for g in grants:
        if g == ds:
            return True
        if not restricted and fnmatch.fnmatch(ds, g):
            return True
    return False


class DryRunner:
    def __init__(self, project: str, config: str, enabled: bool):
        self.enabled = enabled
        self.cache_path = BUILD / ".dryrun_cache.json"
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}
        self.client = None
        if enabled:
            sys.path.insert(0, str(SPECS / "tools"))
            from deploy import GcloudCredentials
            from google.cloud import bigquery
            self.bq = bigquery
            self.client = bigquery.Client(project=project, credentials=GcloudCredentials(config), location="US")

    def check(self, sql: str) -> dict:
        h = hashlib.sha256(sql.encode()).hexdigest()
        if h in self.cache:
            return self.cache[h]
        if not self.enabled:
            return {"ok": None}
        try:
            job = self.client.query(sql, job_config=self.bq.QueryJobConfig(dry_run=True, use_query_cache=False))
            r = {"ok": True, "statement_type": job.statement_type}
        except Exception as e:
            r = {"ok": False, "error": getattr(e, "message", str(e)).split("\n")[0][:400]}
        self.cache[h] = r
        return r

    def save(self):
        self.cache_path.write_text(json.dumps(self.cache))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="jeffdavis-bq-testproj")
    ap.add_argument("--config", default="qlsc")
    ap.add_argument("--prefix", default="fnb_")
    ap.add_argument("--no-dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    wh = json.loads((BUILD / "warehouse.json").read_text())
    estate_yaml = yaml.safe_load((SPECS / "warehouse" / "00_estate.yaml").read_text())
    findings = yaml.safe_load((SPECS / "findings.yaml").read_text())["findings"]
    est = Estate(wh)
    window = wh["log_window"]
    run_date = dt.date.fromisoformat(str(window["start"])) + dt.timedelta(days=49)

    templates = (gen_dbt(est) + gen_dbt_tests(est) + gen_ingest(est, estate_yaml) + gen_legacy(est)
                 + gen_vertex(est, window) + gen_sandbox_ctas(est, window) + gen_looker_pdts(est)
                 + gen_hightouch(est) + gen_dq(est, estate_yaml) + load_yaml_templates(est))
    ids = Counter(t.id for t in templates)
    for i, n in ids.items():
        if n > 1:
            err(f"duplicate template id {i}")

    physical = make_physical(est, args.project, args.prefix)
    dry = DryRunner(args.project, args.config, not args.no_dry_run)
    records, jobs = [], []
    for t in templates:
        for f in t.findings:
            if f not in findings:
                err(f"{t.id}: unknown finding {f}")
        if t.job_type == "LOAD":
            records.append({**asdict(t), "variant": 0, "tables_read": [], "tables_written": [
                est.logical(*(t.destination.split(".")[:1] + t.destination.split(".")[1:2]
                              + [re.sub(r"\{\{\w+\}\}", "*", t.destination.split(".")[2])]), t.job_project)
                or t.destination]})
            continue
        for vi, shape in enumerate(expand_shapes(t)):
            where = f"{t.id}#{vi}"
            rng = random.Random(where)
            run = dt.date.fromisoformat(t.active_from) + dt.timedelta(days=3) if t.active_from else run_date
            try:
                rendered = render(shape, t.params, rng, run)
            except KeyError as e:
                err(f"{where}: parameter {e} used but not declared")
                continue
            except ValueError as e:
                err(f"{where}: {e}")
                continue
            refs = table_refs(rendered, t.job_project, est, where)
            if refs is None:
                warn(f"{where}: sqlglot cannot parse (BigQuery may still accept it)")
                reads, writes = set(), set()
            else:
                reads, writes = refs
            rec = {**asdict(t), "variant": vi, "sql": shape, "tables_read": sorted(reads),
                   "tables_written": sorted(writes)}
            # auto-tag findings from the tables a template touches
            for fqn in reads | writes:
                tt = est.tables[fqn]
                for k in ("planted", "trap"):
                    if tt.get(k) and tt[k] not in rec["findings"]:
                        rec["findings"] = rec["findings"] + [tt[k]]
            for fqn in reads:
                tt = est.tables[fqn]
                if tt.get("status") in ("dead", "write_only") and t.family != "dq_monitor":
                    err(f"{where}: reads {tt.get('status')} table {fqn}")
            if t.principal_kind == "human" and t.principal in est.wh["teams"]:
                for fqn in reads:
                    ds = est.tables[fqn]["dataset"]
                    if not team_can_read(est, t.principal, ds):
                        err(f"{where}: team {t.principal} has no read grant on {ds}")
            to_check = rendered
            for pat, repl in t.validate_sub:       # validation-only stand-ins, in logical names
                to_check = re.sub(pat, lambda m, r=repl: r, to_check)
            phys, unq = physical(to_check)
            for ds in unq:
                if est.project_of(ds) != t.job_project:
                    err(f"{where}: unqualified {ds}.* resolves in {t.job_project}, but {ds} is in {est.project_of(ds)}")
            records.append(rec)
            jobs.append((rec, phys, where))

    def do(job):
        rec, phys, where = job
        return rec, where, dry.check(phys)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for rec, where, r in pool.map(do, jobs):
            rec["dry_run"] = r.get("ok")
            if r.get("statement_type"):
                rec["statement_type"] = r["statement_type"]
            if r.get("ok") is False:
                err(f"{where} [{rec['source']}]: BigQuery: {r['error']}")
    dry.save()

    (BUILD / "templates.json").write_text(json.dumps(records, indent=1, default=str))
    write_report(records, est, findings)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    fam = Counter(r["family"] for r in records)
    print(f"\n{len(templates)} templates, {len(records)} shapes, {len(errors)} errors, {len(warnings)} warnings")
    print("  " + ", ".join(f"{k}: {v}" for k, v in fam.most_common()))
    return 1 if errors else 0


def write_report(records, est: Estate, findings):
    L = ["# Query templates", "", "Generated by `specs/tools/templates.py`.", ""]
    fam = defaultdict(lambda: [set(), 0])
    for r in records:
        fam[(r["family"], r["principal"])][0].add(r["id"])
        fam[(r["family"], r["principal"])][1] += 1
    L += ["## By family", "", "| Family | Principal | Templates | Shapes |", "|---|---|---|---|"]
    for (f, p), (ids, n) in sorted(fam.items()):
        L.append(f"| {f} | {p} | {len(ids)} | {n} |")
    humans = [r for r in records if r["family"] == "human"]
    L += ["", "## Human templates by team", "", "| Team | Templates | Shapes | Tables touched |", "|---|---|---|---|"]
    ht = defaultdict(lambda: [set(), 0, set()])
    for r in humans:
        ht[r["principal"]][0].add(r["id"]); ht[r["principal"]][1] += 1; ht[r["principal"]][2] |= set(r["tables_read"])
    for team, (ids, n, tabs) in sorted(ht.items()):
        L.append(f"| {team} | {len(ids)} | {n} | {len(tabs)} |")
    # coverage
    readers = defaultdict(set)
    for r in records:
        for t in r["tables_read"]:
            readers[t].add(r["family"])
    L += ["", "## Read coverage", ""]
    by_status = defaultdict(lambda: [0, 0])
    for fqn, t in est.tables.items():
        st = t.get("status", "active")
        fams = readers.get(fqn, set()) - {"dq_monitor"}
        by_status[st][0] += 1
        by_status[st][1] += 1 if fams else 0
    L += ["| Status | Tables | Read by something other than the monitor |", "|---|---|---|"]
    for st, (n, k) in sorted(by_status.items()):
        L.append(f"| {st} | {n} | {k} |")
    unread = sorted(f for f, t in est.tables.items() if t.get("status", "active") == "active"
                    and not (readers.get(f, set()) - {"dq_monitor"}) and t["layer"] not in ("raw", "staging"))
    if unread:
        L += ["", "Active non-raw tables no template reads (besides the monitor): " + ", ".join(f"`{u}`" for u in unread)]
    frozen_unread = sorted(f for f, t in est.tables.items() if t.get("status") == "frozen"
                           and not (readers.get(f, set()) - {"dq_monitor"}))
    L += ["", f"Frozen tables nobody reads - dead in practice ({len(frozen_unread)}): "
          + ", ".join(f"`{u}`" for u in frozen_unread)]
    # distinct non-monitor shapes per active modeled table: the clustering signal
    shapes = defaultdict(int)
    for r in records:
        if r["family"] not in ("dq_monitor",):
            for t in set(r["tables_read"]):
                shapes[t] += 1
    modeled = [f for f, t in est.tables.items() if t.get("status", "active") == "active"
               and t["layer"] in ("intermediate", "mart", "ml", "sandbox", "bi", "legacy")]
    counts = sorted(shapes.get(f, 0) for f in modeled)
    if counts:
        L += ["", "## Shapes per active modeled table", "",
              f"{len(modeled)} active intermediate/mart/ML/BI/sandbox/legacy tables. Distinct non-monitor "
              f"shapes reading each: min {counts[0]}, median {counts[len(counts) // 2]}, max {counts[-1]}.", "",
              "Fewest (under 3): " + ", ".join(f"`{f}` ({shapes.get(f, 0)})" for f in sorted(modeled, key=lambda f: shapes.get(f, 0))
                                               if shapes.get(f, 0) < 3)]
    # findings
    L += ["", "## Findings carried by templates", "", "| Finding | Human templates | Other templates | Families |", "|---|---|---|---|"]
    fc = defaultdict(lambda: [set(), set(), set()])
    for r in records:
        for f in r["findings"]:
            (fc[f][0] if r["family"] in ("human", "sandbox_ctas") else fc[f][1]).add(r["id"])
            fc[f][2].add(r["family"])
    # carried by the log as a whole rather than by a tag
    emergent = {"F01": "every join on customer identifiers", "F02": "every join on customer identifiers",
                "F06": "absence of reads of status: dead tables",
                "F07": "writes, and absence of reads, of status: write_only tables",
                "F15": "every join on hub keys", "F19": "the dq_monitor family"}
    for fid in findings:
        h, o, fams = fc.get(fid, [set(), set(), set()])
        note = f" (emergent: {emergent[fid]})" if fid in emergent else ""
        L.append(f"| {fid} | {len(h)} | {len(o)} | {', '.join(sorted(fams)) or '-'}{note} |")
    st = Counter(r.get("statement_type") for r in records if r.get("statement_type"))
    L += ["", "## Statement types (from BigQuery dry runs)", ""] + [f"- {k}: {v}" for k, v in st.most_common()]
    (BUILD / "TEMPLATES.md").write_text("\n".join(L) + "\n")
    # usage ground truth for the window: who reads and writes each table
    usage = {}
    for fqn, t in est.tables.items():
        rd = sorted({r["principal"] for r in records if fqn in r["tables_read"] and r["family"] != "dq_monitor"})
        wr = sorted({r["principal"] for r in records if fqn in r["tables_written"]}
                    | ({r["principal"] for r in records if r.get("job_type") == "LOAD"
                        and r["tables_written"] and r["tables_written"][0] == fqn}))
        usage[fqn] = {"status": t.get("status", "active"), "readers": rd, "writers": wr,
                      "monitored": any(fqn in r["tables_read"] for r in records if r["family"] == "dq_monitor"),
                      "live": bool(rd)}
    (BUILD / "usage.json").write_text(json.dumps(usage, indent=1))


if __name__ == "__main__":
    sys.exit(main())

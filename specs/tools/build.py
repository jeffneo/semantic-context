#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "sqlglot>=25"]
# ///
"""Expand and validate the Fennmoor Bank ground-truth warehouse spec.

Reads specs/warehouse/*.yaml + specs/concepts.yaml and writes specs/build/:

  warehouse.json   the answer key: every table and column with subject,
                   concept, status, lineage, and the model SQL
  joins.json       every join predicate the dbt models use (legitimate joins)
  ddl/*.sql        physical BigQuery DDL - schemas only, no ground truth
  models/**.sql    SELECT for every derived table, in logical project ids
  SUMMARY.md       counts and consistency report

Usage:  uv run specs/tools/build.py [--strict]
Exit 1 on validation errors (and on warnings with --strict).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp

SPECS = Path(__file__).resolve().parent.parent
WAREHOUSE = SPECS / "warehouse"
BUILD = SPECS / "build"

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------

@dataclass
class Column:
    name: str
    type: str
    expr: str = ""
    concept: str = ""
    flags: dict = field(default_factory=dict)
    lineage: list = field(default_factory=list)   # ["proj.ds.table.col", ...]

    def to_json(self) -> dict:
        d = {"name": self.name, "type": self.type}
        if self.concept:
            d["concept"] = self.concept
        if self.flags:
            d["flags"] = self.flags
        if self.expr:
            d["expr"] = self.expr
        if self.lineage:
            d["lineage"] = sorted(set(self.lineage))
        return d


@dataclass
class Table:
    dataset: str
    name: str
    spec: dict
    kind: str                     # base | staging | model | copy
    columns: list[Column] = field(default_factory=list)
    project: str = ""
    layer: str = ""
    subject: str = ""
    domain: str = ""
    sql: str = ""
    sources: set = field(default_factory=set)
    source_file: str = ""

    @property
    def shard(self):
        return self.spec.get("shard")

    @property
    def fqn(self) -> str:
        return f"{self.project}.{self.dataset}.{self.name}{'*' if self.shard else ''}"

    @property
    def key(self) -> str:
        return f"{self.dataset}.{self.name}"

    def col(self, name: str) -> Column | None:
        n = name.lower()
        return next((c for c in self.columns if c.name.lower() == n), None)


def parse_flags(text: str) -> dict:
    flags = {}
    for tok in text.split():
        k, _, v = tok.partition("=")
        flags[k] = v if v else True
    return flags


def parse_column(dsl: str, where: str) -> Column:
    parts = [p.strip() for p in dsl.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        err(f"{where}: bad column DSL {dsl!r}")
        return Column(parts[0] if parts else "?", "STRING")
    parts += [""] * (5 - len(parts))
    if len(parts) > 5:
        err(f"{where}: too many '|' fields (exprs must not contain '|'): {dsl!r}")
    name, typ, expr_, concept, flags = parts[:5]
    return Column(name, typ, expr_, concept, parse_flags(flags))


# ----------------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------------

def load():
    estate = yaml.safe_load((WAREHOUSE / "00_estate.yaml").read_text())
    concepts_doc = yaml.safe_load((SPECS / "concepts.yaml").read_text())
    tables: list[Table] = []
    for path in sorted(WAREHOUSE.glob("*.yaml")):
        if path.name == "00_estate.yaml":
            continue
        for doc in yaml.safe_load_all(path.read_text()):
            if not doc:
                continue
            ds = doc["dataset"]
            defaults = doc.get("defaults", {}) or {}
            for t in doc.get("tables", []):
                spec = {**defaults, **t}
                kind = "copy" if "copy_of" in spec else "model" if "from" in spec else "base"
                tbl = Table(ds, spec["name"], spec, kind, source_file=path.name)
                where = f"{path.name}:{tbl.key}"
                tbl.columns = [parse_column(c, where) for c in spec.get("columns", [])]
                tables.append(tbl)
    return estate, concepts_doc, tables


# ----------------------------------------------------------------------------
# Staging generation (dbt staging conventions, deterministic)
# ----------------------------------------------------------------------------

# Multi-token phrases first, then single tokens. Only applied to UPPER_CASE
# source names; snake and camel names are just normalized.
PHRASES = {
    ("CIF", "NO"): "cif_number", ("CIF",): "cif_number",
    ("OPT", "IN"): "opted_in", ("GL", "ACCT"): "gl_account_code",
    ("CRT", "TS"): "created_at", ("LST", "UPD", "TS"): "last_updated_at",
    ("CHG", "TS"): "changed_at", ("CC", "ID"): "cost_center_id",
    ("LST", "NM"): "last_name", ("FRST", "NM"): "first_name", ("MIDL", "NM"): "middle_name",
}
TOKENS = {
    "NO": "number", "TYP": "type", "CD": "code", "NM": "name", "DT": "date", "TS": "at",
    "BRNCH": "branch", "PREF": "preferred", "LANG": "language", "EMP": "employee",
    "SEG": "segment", "RTNG": "rating", "STAT": "status", "CUST": "customer",
    "ADDR": "address", "LN": "line", "ST": "state", "CNTRY": "country", "PRIM": "primary",
    "EFF": "effective", "CNTCT": "contact", "VAL": "value", "VRFD": "verified",
    "ACCT": "account", "PROD": "product", "CLS": "close", "RSN": "reason", "CHNL": "channel",
    "CCY": "currency", "INT": "interest", "RT": "rate", "OD": "overdraft", "LMT": "limit",
    "AMT": "amount", "STMT": "statement", "CYC": "cycle", "REL": "relationship",
    "BAL": "balance", "DLY": "daily", "AVAIL": "available", "COLL": "collected",
    "ACCRD": "accrued", "TXN": "transaction", "POST": "posted", "DR": "debit",
    "CR": "credit", "IND": "indicator", "DESC": "description", "CHK": "check",
    "RUN": "running", "FMLY": "family", "MTHLY": "monthly", "MTHS": "months",
    "ACTV": "active", "MGR": "manager", "RGN": "region", "MKT": "market", "LAT": "latitude",
    "LNG": "longitude", "CHG": "change", "PREV": "previous", "ASSESS": "assessed",
    "WAIVE": "waive", "ACCR": "accrual", "MAT": "maturity", "RENEW": "renewal",
    "OPT": "option", "SCHED": "schedule", "SEQ": "sequence", "TOT": "total",
    "REV": "revolving", "UTIL": "utilization", "NUM": "num", "TRD": "trades",
    "INQ": "inquiries", "DLQ": "delinquent", "BK": "bankruptcy", "MOS": "months",
    "EST": "estimated", "UPD": "updated", "CRT": "created", "LST": "last", "FRST": "first",
    "MIDL": "middle", "SO": "standing_order", "BENE": "beneficiary", "RTG": "routing",
    "FREQ": "frequency", "EXEC": "execution", "LOC": "location", "BUS": "business", "HIST": "history", "PRIN": "principal",
}


def camel_to_snake(s: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s)
    return s.lower()


def expand_upper(name: str) -> str:
    toks = name.split("_")
    out, i = [], 0
    while i < len(toks):
        for n in (3, 2, 1):
            key = tuple(toks[i:i + n])
            if len(key) == n and key in PHRASES:
                out.append(PHRASES[key]); i += n; break
        else:
            out.append(TOKENS.get(toks[i], toks[i].lower())); i += 1
    return "_".join(out)


def normalize_name(name: str) -> str:
    if name.endswith("__c"):
        name = name[:-3]
    if name.isupper() or re.fullmatch(r"[A-Z0-9_]+", name):
        return expand_upper(name)
    return camel_to_snake(name)


def entity_of(table_name: str) -> str:
    n = table_name.rstrip("_")
    n = re.sub(r"_\d+$", "", n)
    return normalize_name(n)


def stage_column(c: Column, entity: str) -> list[Column]:
    """Map one raw column to its staging column(s)."""
    src = f"src.{c.name}"
    flags = {k: v for k, v in c.flags.items() if k not in ("pk", "required", "policy")}
    if c.flags.get("pk"):
        flags["pk"] = True
    if c.name.lower() == "id":
        return [Column(f"{entity}_id", c.type, src, c.concept, flags)]
    name = normalize_name(c.name)
    toks = name.split("_")
    # Y/N flag columns -> BOOL is_*
    if c.name.upper().endswith("_FLG"):
        stem = expand_upper(c.name[:-4]) if c.name.isupper() else name[:-4]
        return [Column(f"is_{stem}", "BOOL", f"{src} = 'Y'", c.concept, flags)]
    pii = c.flags.get("pii")
    if pii == "ssn":
        f = {**flags, "pii": "ssn_hash"}
        return [Column(f"{name}_hash", "STRING", f"TO_HEX(SHA256({src}))", "pii.ssn_hash", f)]
    if pii == "account_number":
        f = {k: v for k, v in flags.items() if k != "pii"}
        return [Column(f"{name}_last4", "STRING", f"RIGHT({src}, 4)", "", f)]
    unit = c.flags.get("unit")
    if unit == "cents":
        new = re.sub(r"_cents$", "", name) or "amount"
        return [Column(new, "NUMERIC", f"CAST({src} AS NUMERIC) / 100", c.concept, {**flags, "unit": "usd"})]
    if unit == "bps":
        new = re.sub(r"_bps$", "_pct", name)
        # INT64 / INT64 is FLOAT64 in BigQuery; cast to keep NUMERIC.
        return [Column(new, "NUMERIC", f"CAST({src} AS NUMERIC) / 100", c.concept, {**flags, "unit": "pct"})]
    expr_ = src if name == c.name else src
    return [Column(name, c.type, expr_, c.concept, flags)]


def generate_staging(estate: dict, tables: list[Table]) -> list[Table]:
    out = []
    mixins = estate.get("mixins", {})
    for t in tables:
        ds = estate["datasets"].get(t.dataset, {})
        if t.kind != "base" or ds.get("layer") != "raw":
            continue
        prefix = t.spec.get("stage")
        if not prefix:
            continue
        name = t.spec.get("stage_name") or f"stg_{prefix}__{entity_of(t.name)}"
        target_ds = "dw_staging_restricted" if ds.get("restricted") else "dw_staging"
        entity = entity_of(t.name)
        mixin_cols, keep, loaded_at, filters = set(), set(), None, []
        for m in t.spec.get("mixins", []):
            mx = mixins.get(m, {})
            mixin_cols |= {c.split("|")[0].strip() for c in mx.get("columns", [])}
            keep |= set(mx.get("keep", []))
            loaded_at = mx.get("loaded_at", loaded_at)
            if mx.get("filter"):
                filters.append(mx["filter"])
        if "stage_columns" in t.spec:
            cols = [parse_column(c, f"{t.key}.stage_columns") for c in t.spec["stage_columns"]]
        else:
            cols = []
            for c in t.columns:
                if c.name in mixin_cols and c.name not in keep:
                    continue
                cols.extend(stage_column(c, entity))
            for c in t.spec.get("stage_add", []):
                cols.append(parse_column(c, f"{t.key}.stage_add"))
        if loaded_at and not any(c.name == "_loaded_at" for c in cols):
            cols.append(Column("_loaded_at", "TIMESTAMP", loaded_at))
        if t.spec.get("stage_where"):
            filters.append(t.spec["stage_where"])
        spec = {
            "name": name,
            "materialized": "view",
            "writer": "dbt-prod",
            "refresh": "view",
            "subject": t.spec.get("subject"),
            "status": "active" if t.spec.get("status", "active") == "active" else t.spec["status"],
            "from": f"ref({t.dataset}.{t.name}) AS src",
            "where": " AND ".join(filters) if filters else None,
            "desc": f"dbt staging model over {t.key}.",
            "grain": t.spec.get("grain"),
        }
        st = Table(target_ds, name, spec, "staging", cols, source_file="(generated)")
        out.append(st)
    return out


# ----------------------------------------------------------------------------
# Resolution
# ----------------------------------------------------------------------------

REF_RE = re.compile(r"\bref\(\s*([A-Za-z0-9_.*\-]+)\s*\)")


class Index:
    def __init__(self, tables: list[Table]):
        self.by_key = {t.key: t for t in tables}
        self.by_name = defaultdict(list)
        for t in tables:
            self.by_name[t.name].append(t)

    def get(self, ref: str, where: str) -> Table | None:
        if ref in self.by_key:
            return self.by_key[ref]
        hits = self.by_name.get(ref, [])
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            err(f"{where}: ref({ref}) is ambiguous; qualify it with the dataset")
        else:
            err(f"{where}: ref({ref}) does not resolve")
        return None


def sub_refs(sql: str, idx: Index, where: str, sources: set) -> str:
    def repl(m):
        t = idx.get(m.group(1), where)
        if not t:
            return "`missing.missing.missing`"
        sources.add(t.fqn)
        return f"`{t.fqn}`"
    return REF_RE.sub(repl, sql)


def table_fqn(node: exp.Table) -> str:
    parts = [p for p in (node.catalog, node.db, node.name) if p]
    return ".".join(parts)


def from_aliases(from_sql: str, fqn_to_table: dict, ctes: dict, where: str):
    """Map alias -> ('table', Table) | ('cte', name) | ('unnest', None)."""
    aliases = {}
    try:
        tree = sqlglot.parse_one(f"SELECT 1 FROM {from_sql}", read="bigquery")
    except Exception as e:
        err(f"{where}: FROM does not parse: {e}")
        return aliases, None
    for node in tree.find_all(exp.Table):
        f = table_fqn(node)
        alias = node.alias_or_name
        if f in fqn_to_table:
            aliases[alias] = ("table", fqn_to_table[f])
        elif f in ctes:
            aliases[alias] = ("cte", ctes[f], f)
        else:
            err(f"{where}: FROM references unknown table {f}")
    for node in tree.find_all(exp.Subquery):
        if node.alias:
            aliases[node.alias] = ("cte", resolve_query(node.this, fqn_to_table, ctes), node.alias)
    for node in tree.find_all(exp.Unnest):
        # BigQuery `UNNEST(x) AS d` is normalized to table alias _t0 with column alias d
        ta = node.args.get("alias")
        names = [node.alias] if node.alias else []
        if ta is not None:
            names += [c.name for c in ta.args.get("columns") or []]
        for n in names:
            aliases[n] = ("unnest", None)
    return aliases, tree


def col_parts(c: exp.Column) -> list[str]:
    return [p for p in (c.catalog, c.db, c.table) if p] + [c.name]


def resolve_expr(expr_sql: str, aliases: dict, where: str) -> list[str]:
    """Validate alias.column refs in an expression; return lineage fqn.col list."""
    try:
        tree = sqlglot.parse_one(expr_sql, read="bigquery")
    except Exception as e:
        err(f"{where}: expression does not parse: {expr_sql!r}: {e}")
        return []
    lineage = []
    for c in tree.find_all(exp.Column):
        parts = col_parts(c)
        in_subquery = c.find_ancestor(exp.Subquery, exp.Select) is not None
        if len(parts) >= 2 and parts[0] in aliases:
            kind, target = aliases[parts[0]][:2]
            if kind == "table":
                root = parts[1]
                col = target.col(root)
                if not col:
                    err(f"{where}: {parts[0]}.{root} is not a column of {target.key}")
                else:
                    lineage.append(f"{target.fqn}.{col.name}")
            elif kind == "cte":
                hit = [lv for n, lv, _ in target if n.lower() == parts[1].lower()]
                if not hit:
                    err(f"{where}: {parts[0]}.{parts[1]} is not an output of CTE/subquery {aliases[parts[0]][2]}")
                else:
                    lineage.extend(hit[0])
        elif len(parts) == 1 and parts[0] in aliases and aliases[parts[0]][0] == "unnest":
            continue
        elif in_subquery:
            continue
        elif len(parts) == 1 and parts[0].lower() in PSEUDO_COLUMNS | {"current_date", "current_timestamp"}:
            continue
        else:
            warn(f"{where}: unqualified or unknown column reference {'.'.join(parts)!r}")
    return lineage


def join_pairs(tree, aliases: dict, index_fqn: dict) -> list[tuple[str, str]]:
    pairs = []
    if tree is None:
        return pairs
    for j in tree.find_all(exp.Join):
        on = j.args.get("on")
        if on is None:
            continue
        for eq in on.find_all(exp.EQ):
            sides = []
            for side in (eq.left, eq.right):
                col = side if isinstance(side, exp.Column) else side.find(exp.Column)
                if col is None:
                    break
                parts = col_parts(col)
                if len(parts) < 2 or parts[0] not in aliases:
                    continue
                kind, target = aliases[parts[0]][:2]
                if kind == "table":
                    c = target.col(parts[1])
                    if c:
                        sides.append((target, c))
                elif kind == "cte":
                    hit = [lv for n, lv, pt in target if n.lower() == parts[1].lower() and pt]
                    if hit and len(set(hit[0])) == 1:
                        fqn, _, cname = hit[0][0].rpartition(".")
                        t = index_fqn.get(fqn)
                        if t and t.col(cname):
                            sides.append((t, t.col(cname)))
            if len(sides) == 2:
                pairs.append(sides)
    return pairs


PSEUDO_COLUMNS = {"_table_suffix", "_partitiontime", "_partitiondate"}


def select_sources(sel: exp.Select, fqn_to_table: dict, ctes: dict) -> dict:
    """alias -> ('table', Table) | ('cte', [(name, leaves)]) for one SELECT's own FROM/JOINs."""
    out = {}
    nodes = []
    frm = sel.args.get("from") or sel.args.get("from_")   # renamed in sqlglot 30
    if frm:
        nodes.append(frm.this)
    nodes += [j.this for j in sel.args.get("joins") or []]
    for n in nodes:
        if isinstance(n, exp.Table):
            f = table_fqn(n)
            if f in fqn_to_table:
                out[n.alias_or_name] = ("table", fqn_to_table[f])
            elif f in ctes:
                out[n.alias_or_name] = ("cte", ctes[f])
        elif isinstance(n, exp.Subquery) and n.alias:
            out[n.alias] = ("cte", resolve_query(n.this, fqn_to_table, ctes))
    return out


def leaves_for(node, sources: dict) -> list[str]:
    leaves = []
    for c in node.find_all(exp.Column):
        parts = col_parts(c)
        if len(parts) >= 2 and parts[0] in sources:
            alias, root = parts[0], parts[1]
        elif len(parts) == 1 and len(sources) == 1:
            alias, root = next(iter(sources)), parts[0]
        else:
            continue
        kind, target = sources[alias]
        if kind == "table":
            col = target.col(root)
            if col:
                leaves.append(f"{target.fqn}.{col.name}")
        else:
            for name, lv, _ in target:
                if name.lower() == root.lower():
                    leaves.extend(lv)
    return leaves


def is_passthrough(e) -> bool:
    """True if a projection returns a source column's value unchanged (safe for join lineage)."""
    node = e.this if isinstance(e, exp.Alias) else e
    if isinstance(node, exp.Column):
        return True
    if isinstance(node, (exp.AnyValue, exp.Min, exp.Max)) and isinstance(node.this, exp.Column):
        return True
    return False


def resolve_query(q, fqn_to_table: dict, ctes: dict) -> list[tuple[str, list[str], bool]]:
    """Ordered output columns of a SELECT / set operation, each with its leaf columns."""
    if isinstance(q, exp.Subquery):
        q = q.this
    if isinstance(q, exp.SetOperation) if hasattr(exp, "SetOperation") else isinstance(q, exp.Union):
        left = resolve_query(q.left, fqn_to_table, ctes)
        right = resolve_query(q.right, fqn_to_table, ctes)
        return [(n, lv + (right[i][1] if i < len(right) else []), pt and (right[i][2] if i < len(right) else True))
                for i, (n, lv, pt) in enumerate(left)]
    if not isinstance(q, exp.Select):
        return []
    sources = select_sources(q, fqn_to_table, ctes)
    out = []
    for e in q.expressions:
        star = e if isinstance(e, exp.Star) else e.this if isinstance(e, exp.Column) and isinstance(e.this, exp.Star) else None
        if star is not None:
            aliases = [e.table] if isinstance(e, exp.Column) and e.table else list(sources)
            for a in aliases:
                kind, target = sources.get(a, (None, None))
                if kind == "table":
                    out += [(c.name, [f"{target.fqn}.{c.name}"], True) for c in target.columns]
                elif kind == "cte":
                    out += list(target)
            continue
        out.append((e.alias_or_name, leaves_for(e, sources), is_passthrough(e)))
    return out


def resolve_copy(t: Table, idx: Index) -> bool:
    """Expand a sandbox copy. Returns False if its source is not ready yet."""
    src_ref = t.spec["copy_of"]
    src = idx.get(src_ref, t.key)
    if not src:
        return True
    if src.kind == "copy" and not src.columns:
        return False
    drop = set(t.spec.get("drop", []))
    rename = t.spec.get("rename", {}) or {}
    for n in list(drop) + list(rename):
        if not src.col(n):
            err(f"{t.key}: copy_of {src.key} has no column {n!r} to drop/rename")
    cols, select = [], []
    for c in src.columns:
        if c.name in drop:
            continue
        new_name = rename.get(c.name, c.name)
        # BigQuery policy tags do not survive CREATE TABLE AS SELECT - a
        # sandbox copy of a protected column is unprotected.
        flags = {k: v for k, v in c.flags.items() if k != "policy"}
        cols.append(Column(new_name, c.type, f"s.{c.name}", c.concept, flags,
                           [f"{src.fqn}.{c.name}"]))
        if c.name in rename:
            select.append(f"s.{c.name} AS {new_name}")
    except_ = sorted(drop | set(rename))
    star = f"s.* EXCEPT ({', '.join(except_)})" if except_ else "s.*"
    aliases = {"s": ("table", src)}
    for dsl in t.spec.get("add", []):
        c = parse_column(dsl, f"{t.key}.add")
        c.lineage = resolve_expr(c.expr, aliases, f"{t.key}.{c.name}") if c.expr else []
        cols.append(c)
        select.append(f"{c.expr} AS {c.name}" if c.expr else f"CAST(NULL AS {c.type}) AS {c.name}")
    t.columns = cols
    t.sources = {src.fqn}
    sql = f"SELECT\n  {star}" + "".join(f",\n  {s}" for s in select) + f"\nFROM `{src.fqn}` AS s"
    if t.spec.get("where"):
        sql += f"\nWHERE {t.spec['where']}"
    t.sql = sql
    t.spec.setdefault("subject", src.spec.get("subject") or src.subject)
    return True


def build_model_sql(t: Table, idx: Index, fqn_to_table: dict):
    where = t.key
    sources: set = set()
    ctes = t.spec.get("with") or {}
    cte_sql, cte_cols = {}, {}
    for n, body in ctes.items():
        cte_sql[n] = sub_refs(body, idx, f"{where}.with.{n}", sources)
        try:
            q = sqlglot.parse_one(cte_sql[n], read="bigquery")
            cte_cols[n] = resolve_query(q, fqn_to_table, cte_cols)
        except Exception as e:
            err(f"{where}.with.{n}: does not parse: {e}")
            cte_cols[n] = []
    from_sql = sub_refs(t.spec["from"], idx, where, sources)
    aliases, tree = from_aliases(from_sql, fqn_to_table, cte_cols, where)
    for c in t.columns:
        if not c.expr:
            err(f"{where}: derived column {c.name!r} has no expression")
            continue
        c.lineage = resolve_expr(c.expr, aliases, f"{where}.{c.name}")
    for clause in ("where", "qualify", "having"):
        if t.spec.get(clause):
            resolve_expr(t.spec[clause], aliases, f"{where}.{clause}")
    select = []
    for c in t.columns:
        bare = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.([A-Za-z_][A-Za-z0-9_]*)", c.expr or "")
        select.append(c.expr if bare and bare.group(1) == c.name else f"{c.expr} AS {c.name}")
    sql = ""
    if cte_sql:
        sql = "WITH " + ",\n".join(f"{n} AS (\n{s.strip()}\n)" for n, s in cte_sql.items()) + "\n"
    sql += "SELECT\n  " + ",\n  ".join(select) + f"\nFROM {from_sql.strip()}"
    if t.spec.get("where"):
        sql += f"\nWHERE {t.spec['where']}"
    gb = t.spec.get("group_by")
    if gb:
        sql += "\nGROUP BY " + ("ALL" if gb == "all" else ", ".join(map(str, gb)))
    if t.spec.get("having"):
        sql += f"\nHAVING {t.spec['having']}"
    if t.spec.get("qualify"):
        sql += f"\nQUALIFY {t.spec['qualify']}"
    t.sql = sql
    t.sources = sources
    try:
        sqlglot.parse_one(sql, read="bigquery")
    except Exception as e:
        err(f"{where}: generated SQL does not parse: {e}")
    return join_pairs(tree, aliases, fqn_to_table)


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------

BASE_TYPES = {"STRING", "INT64", "NUMERIC", "BIGNUMERIC", "FLOAT64", "BOOL", "DATE",
              "DATETIME", "TIMESTAMP", "TIME", "JSON", "BYTES", "GEOGRAPHY", "INTERVAL"}
RESERVED_COLUMN_PREFIX = re.compile(
    r"(_PARTITION|_TABLE_|_FILE_|_ROW_TIMESTAMP|__ROOT__|_COLIDENTIFIER)", re.I)
STATUSES = {"active", "deprecated", "frozen", "dead", "write_only", "stale"}
MATERIALIZATIONS = {"table", "view", "incremental", "pdt", "ctas", "snapshot", "external"}


def valid_type(t: str) -> bool:
    t = t.strip()
    if t in BASE_TYPES:
        return True
    if t.startswith("ARRAY<") and t.endswith(">"):
        return valid_type(t[6:-1])
    if t.startswith("STRUCT<") and t.endswith(">"):
        body, depth, cur, fields = t[7:-1], 0, "", []
        for ch in body:
            if ch == "<": depth += 1
            if ch == ">": depth -= 1
            if ch == "," and depth == 0:
                fields.append(cur); cur = ""
            else:
                cur += ch
        fields.append(cur)
        return all(len(f.strip().split(None, 1)) == 2 and valid_type(f.strip().split(None, 1)[1])
                   for f in fields)
    return False


def validate(estate, concepts, tables: list[Table], idx: Index):
    subjects = {s: d for d, subs in estate["subjects"].items() for s in subs}
    untagged_ids = defaultdict(list)
    seen = set()
    for t in tables:
        w = t.key
        if t.fqn.lower() in seen:
            err(f"{w}: duplicate table")
        seen.add(t.fqn.lower())
        s = t.spec
        if s.get("status", "active") not in STATUSES:
            err(f"{w}: bad status {s.get('status')!r}")
        if t.kind != "base" and s.get("materialized", "table") not in MATERIALIZATIONS:
            err(f"{w}: bad materialized {s.get('materialized')!r}")
        if not t.subject:
            err(f"{w}: no subject")
        elif t.subject not in subjects:
            err(f"{w}: unknown subject {t.subject!r}")
        if not t.columns:
            err(f"{w}: no columns")
        names = Counter(c.name.lower() for c in t.columns)
        for n, k in names.items():
            if k > 1:
                err(f"{w}: duplicate column {n!r} (BigQuery names are case-insensitive)")
        for c in t.columns:
            cw = f"{w}.{c.name}"
            if RESERVED_COLUMN_PREFIX.match(c.name):
                err(f"{cw}: BigQuery reserves this column-name prefix")
            if not valid_type(c.type):
                err(f"{cw}: invalid type {c.type!r}")
            if c.concept and c.concept not in concepts:
                err(f"{cw}: unknown concept {c.concept!r}")
            kind = concepts.get(c.concept, {}).get("kind")
            if c.flags.get("pii") and c.concept and kind != "pii":
                err(f"{cw}: pii flag but concept {c.concept} is kind {kind}")
            if kind == "pii" and not c.flags.get("pii") and c.concept not in ("pii.ssn_hash",):
                warn(f"{cw}: PII concept {c.concept} without pii= flag")
            if "contains" in c.flags:
                cid = c.flags["contains"].split("@")[0]
                if cid not in concepts:
                    err(f"{cw}: contains unknown concept {cid!r}")
            if (not c.concept and not c.flags.get("pii") and t.kind == "base"
                    and re.search(r"(_id|_ID|Id|_NO|_no|Number)$", c.name)):
                untagged_ids[c.name.lower()].append(cw)
        part = s.get("partition")
        if part:
            m = re.fullmatch(r"DATE\((\w+)\)", part)
            pcol = t.col(m.group(1) if m else part)
            if not pcol:
                err(f"{w}: partition column {part!r} not found")
            elif m and pcol.type not in ("TIMESTAMP", "DATETIME"):
                err(f"{w}: DATE({pcol.name}) needs TIMESTAMP/DATETIME, is {pcol.type}")
            elif not m and pcol.type not in ("DATE", "TIMESTAMP", "DATETIME"):
                err(f"{w}: partition column {pcol.name} is {pcol.type}")
        cl = s.get("cluster") or []
        if len(cl) > 4:
            err(f"{w}: more than 4 cluster columns")
        for cn in cl:
            cc = t.col(cn)
            if not cc:
                err(f"{w}: cluster column {cn!r} not found")
            elif cc.type.split("<")[0] in ("ARRAY", "STRUCT", "JSON", "FLOAT64"):
                err(f"{w}: cannot cluster on {cc.type}")
    # An untagged id-like name in 2+ tables is a join key with no concept.
    for name, where_ in sorted(untagged_ids.items()):
        if len(where_) > 1:
            warn(f"untagged join key {name!r} in {len(where_)} tables: {', '.join(where_)}")
    for cid, cdef in concepts.items():
        home = cdef.get("home")
        if not home:
            continue
        ds, tb, *rest = home.split(".")
        t = idx.by_key.get(f"{ds}.{tb.rstrip('*')}")
        if not t:
            err(f"concept {cid}: home table {ds}.{tb} not found")
        elif rest and not t.col(rest[0]):
            err(f"concept {cid}: home column {home} not found")


def resolve_object(ref: str, idx: Index):
    """'dataset.table' or 'dataset.table.column' -> (Table, Column|None) or None."""
    parts = ref.split(".")
    t = idx.by_key.get(".".join(parts[:2]))
    if not t:
        return None
    if len(parts) == 2:
        return t, None
    c = t.col(parts[2])
    return (t, c) if c else None


def validate_answer_keys(tables: list[Table], idx: Index):
    findings = yaml.safe_load((SPECS / "findings.yaml").read_text())["findings"]
    questions = yaml.safe_load((SPECS / "questions.yaml").read_text())["questions"]
    for fid, f in findings.items():
        for ref in f.get("objects", []):
            if not resolve_object(ref, idx):
                err(f"findings {fid}: object {ref!r} does not exist")
    # every planted/trap tag on a table must name a real finding
    for t in tables:
        for k in ("planted", "trap"):
            v = t.spec.get(k)
            if v and v not in findings:
                err(f"{t.key}: {k}: {v} is not in findings.yaml")
    for qid, q in questions.items():
        for section in ("expected", "acceptable"):
            for ref in q.get(section, []) or []:
                if not resolve_object(ref, idx):
                    err(f"questions {qid}.{section}: {ref!r} does not exist")
        for ref in (q.get("avoid") or {}):
            r = resolve_object(ref, idx)
            if not r:
                err(f"questions {qid}.avoid: {ref!r} does not exist")
        overlap = set(q.get("expected", []) or []) & set(q.get("avoid") or {})
        if overlap:
            err(f"questions {qid}: {sorted(overlap)} both expected and avoided")
    return findings, questions


def write_answer_keys(findings, questions, tables, idx, joins):
    """Resolve answer-key references to fully-qualified names for scoring."""
    def fq(ref):
        r = resolve_object(ref, idx)
        if not r:
            return ref
        t, c = r
        return f"{t.fqn}.{c.name}" if c else t.fqn
    out = {"findings": {}, "questions": {}}
    for fid, f in findings.items():
        out["findings"][fid] = {**f, "objects": [fq(o) for o in f.get("objects", [])],
                                "tagged_tables": sorted(t.fqn for t in tables
                                                        if fid in (t.spec.get("planted"), t.spec.get("trap")))}
    for qid, q in questions.items():
        out["questions"][qid] = {**q,
                                 "expected": [fq(r) for r in q.get("expected", []) or []],
                                 "acceptable": [fq(r) for r in q.get("acceptable", []) or []],
                                 "avoid": {fq(r): why for r, why in (q.get("avoid") or {}).items()}}
    (BUILD / "answer_key.json").write_text(json.dumps(out, indent=1, default=str))


# ----------------------------------------------------------------------------
# Emit
# ----------------------------------------------------------------------------

def shard_suffixes(shard: dict, estate: dict) -> list[str]:
    start = date.fromisoformat(str(estate["log_window"]["start"]))
    end = start + timedelta(days=estate["log_window"]["days"] - 1)
    to = end.isoformat() if shard["to"] == "log_end" else str(shard["to"])
    if shard["suffix"] == "YYYYMMDD":
        d, e, out = date.fromisoformat(str(shard["from"])), date.fromisoformat(to), []
        while d <= e:
            out.append(d.strftime("%Y%m%d")); d += timedelta(days=1)
        return out
    y, m = map(int, str(shard["from"]).split("-"))
    ey, em = map(int, to.split("-")[:2])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y}{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def ddl_for(t: Table, estate: dict) -> list[str]:
    cols = ",\n".join(
        f"  `{c.name}` {c.type}{' NOT NULL' if c.flags.get('required') else ''}" for c in t.columns)
    tail = ""
    if t.spec.get("partition"):
        tail += f"\nPARTITION BY {t.spec['partition']}"
    if t.spec.get("cluster"):
        tail += f"\nCLUSTER BY {', '.join(t.spec['cluster'])}"
    # Only what a real estate would plausibly carry. Ground truth never leaks.
    if t.spec.get("bq_description"):
        tail += f"\nOPTIONS (description = {json.dumps(t.spec['bq_description'])})"
    names = [f"{t.name}{sfx}" for sfx in shard_suffixes(t.shard, estate)] if t.shard else [t.name]
    if t.kind == "staging" or t.spec.get("materialized") == "view":
        return [f"CREATE OR REPLACE VIEW `{t.project}.{t.dataset}.{t.name}` AS\n{t.sql};"]
    return [f"CREATE TABLE IF NOT EXISTS `{t.project}.{t.dataset}.{n}` (\n{cols}\n){tail};"
            for n in names]


def main() -> int:
    strict = "--strict" in sys.argv
    estate, concepts_doc, tables = load()
    concepts = concepts_doc["concepts"]
    tables += generate_staging(estate, tables)

    # project / layer / mixin columns
    mixins = estate.get("mixins", {})
    for t in tables:
        ds = estate["datasets"].get(t.dataset)
        if not ds:
            err(f"{t.key}: dataset {t.dataset!r} not declared in 00_estate.yaml")
            continue
        t.project, t.layer = ds["project"], ds["layer"]
        if t.kind == "base":
            present = {c.name for c in t.columns}
            for m in t.spec.get("mixins", []):
                if m not in mixins:
                    err(f"{t.key}: unknown mixin {m!r}")
                    continue
                t.columns += [parse_column(c, f"mixin {m}") for c in mixins[m]["columns"]
                              if c.split("|")[0].strip() not in present]

    idx = Index(tables)
    fqn_to_table = {t.fqn: t for t in tables}

    # copies depend on their source's columns: resolve in waves
    pending = [t for t in tables if t.kind == "copy"]
    for _ in range(10):
        pending = [t for t in pending if not resolve_copy(t, idx)]
        if not pending:
            break
    for t in pending:
        err(f"{t.key}: copy_of chain did not resolve")

    subjects = {s: d for d, subs in estate["subjects"].items() for s in subs}
    for t in tables:
        t.subject = t.spec.get("subject", "")
        t.domain = subjects.get(t.subject, "")

    joins = []
    for t in tables:
        if t.kind in ("staging", "model"):
            for (lt, lc), (rt, rc) in build_model_sql(t, idx, fqn_to_table):
                joins.append({"model": t.fqn, "writer": t.spec.get("writer"),
                              "left": f"{lt.fqn}.{lc.name}", "right": f"{rt.fqn}.{rc.name}",
                              "left_concept": lc.concept, "right_concept": rc.concept})
        for ref in t.spec.get("upstream", []) or []:
            u = idx.get(ref, f"{t.key}.upstream")
            if u:
                t.sources.add(u.fqn)

    # Production models are correct by construction: a cross-id-space join
    # there is a spec bug. In human-written tables it is a planted trap, and
    # must be declared as one (trap: <finding id>) so it is intentional.
    production = {"dbt-prod", "composer-legacy", "vertex-scoring", "looker-prod"}
    for j in joins:
        lc, rc = concepts.get(j["left_concept"], {}), concepts.get(j["right_concept"], {})
        model = fqn_to_table[j["model"]]
        if lc.get("id_space") and rc.get("id_space") and lc["id_space"] != rc["id_space"]:
            j["trap"] = model.spec.get("trap")
            if j["writer"] in production or not model.spec.get("trap"):
                err(f"{j['model']}: joins {j['left']} ({j['left_concept']}) to "
                    f"{j['right']} ({j['right_concept']}) - different id spaces")
        elif not (j["left_concept"] and j["right_concept"]):
            warn(f"{j['model']}: join on untagged column {j['left']} = {j['right']}")

    validate(estate, concepts, tables, idx)
    findings, questions = validate_answer_keys(tables, idx)
    emit(estate, concepts_doc, tables, joins)
    write_answer_keys(findings, questions, tables, idx, joins)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(tables)} logical tables, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors or (strict and warnings) else 0


def emit(estate, concepts_doc, tables: list[Table], joins: list[dict]):
    concepts = concepts_doc["concepts"]
    # Start clean: renamed or removed models must not leave stale files behind.
    for sub in ("ddl", "models"):
        shutil.rmtree(BUILD / sub, ignore_errors=True)
    BUILD.mkdir(exist_ok=True)
    (BUILD / "ddl").mkdir(exist_ok=True)
    (BUILD / "models").mkdir(exist_ok=True)
    layer_order = ["raw", "staging", "intermediate", "mart", "ml", "legacy", "bi", "ops", "sandbox"]
    order = sorted(tables, key=lambda t: (layer_order.index(t.layer) if t.layer in layer_order else 99,
                                          t.project, t.dataset, t.name.lower()))

    wh = {
        "org": estate["org"], "log_window": estate["log_window"],
        "projects": estate["projects"], "datasets": estate["datasets"],
        "teams": estate["teams"], "service_accounts": estate["service_accounts"],
        "subjects": estate["subjects"],
        "tables": [], "concepts": concepts, "glossary": concepts_doc.get("glossary", {}),
    }
    ddl = defaultdict(list)
    for t in order:
        s = t.spec
        entry = {
            "fqn": t.fqn, "project": t.project, "dataset": t.dataset, "name": t.name,
            "layer": t.layer, "kind": t.kind, "domain": t.domain, "subject": t.subject,
            "status": s.get("status", "active"),
            "materialized": "base" if t.kind == "base" else s.get("materialized", "table"),
            "writer": s.get("writer"), "refresh": s.get("refresh"),
            "desc": s.get("desc"), "grain": s.get("grain"), "rows": s.get("rows"),
            "partition": s.get("partition"), "cluster": s.get("cluster"),
            "shard": s.get("shard"), "sources": sorted(t.sources),
            "restricted": bool(estate["datasets"].get(t.dataset, {}).get("restricted")),
            "columns": [c.to_json() for c in t.columns],
        }
        for k in ("copy_of", "created", "superseded_by", "supersedes", "owner", "notes", "trap",
                  "planted", "upstream", "bq_description", "cadence"):
            if k in s:
                entry[k] = s[k]
        if t.sql:
            entry["sql"] = t.sql
            mdir = BUILD / "models" / t.project / t.dataset
            mdir.mkdir(parents=True, exist_ok=True)
            (mdir / f"{t.name}.sql").write_text(t.sql + "\n")
        wh["tables"].append({k: v for k, v in entry.items() if v not in (None, [], {})})
        ddl[(t.project, t.dataset)].extend(ddl_for(t, estate))

    (BUILD / "warehouse.json").write_text(json.dumps(wh, indent=1, default=str))
    (BUILD / "joins.json").write_text(json.dumps(joins, indent=1))
    for i, ((proj, ds), stmts) in enumerate(ddl.items()):
        head = f"CREATE SCHEMA IF NOT EXISTS `{proj}.{ds}` OPTIONS (location = 'US');\n\n"
        (BUILD / "ddl" / f"{i:03d}_{proj}.{ds}.sql").write_text(head + "\n\n".join(stmts) + "\n")
    write_summary(estate, concepts, tables, joins)


def write_summary(estate, concepts, tables: list[Table], joins):
    L = []
    phys = sum(len(shard_suffixes(t.shard, estate)) if t.shard else 1 for t in tables)
    L += ["# Fennmoor Bank warehouse - build summary", "",
          f"Generated by `specs/tools/build.py`. {len(tables)} logical tables, {phys} physical "
          f"(sharded tables expand to one table per shard).", ""]
    L += ["## Tables by project and layer", "", "| Project | Layer | Datasets | Tables |", "|---|---|---|---|"]
    by = defaultdict(lambda: [set(), 0])
    for t in tables:
        by[(t.project, t.layer)][0].add(t.dataset); by[(t.project, t.layer)][1] += 1
    for (p, l), (dss, n) in sorted(by.items()):
        L.append(f"| {p} | {l} | {len(dss)} | {n} |")
    L += ["", "## Status", ""]
    L += [f"- **{k}**: {v}" for k, v in Counter(t.spec.get("status", "active") for t in tables).most_common()]
    L += ["", "## Tables per domain", "", "| Domain | Subjects used | Tables |", "|---|---|---|"]
    dom = defaultdict(lambda: [set(), 0])
    for t in tables:
        dom[t.domain][0].add(t.subject); dom[t.domain][1] += 1
    for d, (subs, n) in sorted(dom.items()):
        L.append(f"| {d} | {len(subs)} | {n} |")

    # identifier spellings
    spell = defaultdict(set)
    homonyms = defaultdict(set)
    for t in tables:
        for c in t.columns:
            k = concepts.get(c.concept, {}).get("kind")
            if k == "identifier":
                spell[c.concept].add(c.name)
                homonyms[c.name.lower()].add(c.concept)
    L += ["", "## Identifier spellings", "",
          "Distinct column names carrying each identifier concept - what the pipeline must unify.", "",
          "| Concept | # names | Names |", "|---|---|---|"]
    for cid, names in sorted(spell.items(), key=lambda kv: -len(kv[1])):
        if len(names) > 1:
            L.append(f"| `{cid}` | {len(names)} | {', '.join(f'`{n}`' for n in sorted(names))} |")
    L += ["", "## Homonyms", "",
          "One column name, several identifier concepts - what the pipeline must NOT unify.", "",
          "| Column name | Concepts |", "|---|---|"]
    for n, cs in sorted(homonyms.items()):
        if len(cs) > 1:
            L.append(f"| `{n}` | {', '.join(f'`{c}`' for c in sorted(cs))} |")

    # PII outside restricted datasets
    L += ["", "## PII inventory", "",
          "Unprotected = neither in a restricted dataset nor behind a column policy tag.", "",
          "| Concept | Tables | Unprotected |", "|---|---|---|"]
    pii = defaultdict(lambda: [set(), set()])
    for t in tables:
        restricted = estate["datasets"].get(t.dataset, {}).get("restricted")
        for c in t.columns:
            if concepts.get(c.concept, {}).get("kind") == "pii" or c.flags.get("pii"):
                key = c.concept or f"pii={c.flags.get('pii')}"
                pii[key][0].add(t.key)
                if not restricted and c.flags.get("policy") != "restricted":
                    pii[key][1].add(t.key)
    for k, (all_, open_) in sorted(pii.items()):
        L.append(f"| `{k}` | {len(all_)} | {len(open_)} |")
    raw_ssn = sorted(pii.get("pii.ssn", [set(), set()])[1])
    if raw_ssn:
        L += ["", "Unprotected raw SSN: " + ", ".join(f"`{x}`" for x in raw_ssn)]

    # CC ambiguity
    L += ["", "## `CC` ambiguity", "", "Tables or columns whose name contains the token CC, by domain.", ""]
    cc = defaultdict(set)
    tok = re.compile(r"(^|_)cc(_|$)", re.I)
    for t in tables:
        if tok.search(t.name):
            cc[t.domain].add(t.key)
        for c in t.columns:
            if tok.search(c.name):
                cc[t.domain].add(f"{t.key}.{c.name}")
    for d, items in sorted(cc.items()):
        L.append(f"- **{d}**: " + ", ".join(f"`{i}`" for i in sorted(items)))

    L += ["", "## Joins used by models", "",
          f"{len(joins)} join predicates across the dbt models (the legitimate-join answer key).", ""]
    jc = Counter(j["left_concept"] or j["right_concept"] or "(untagged)" for j in joins)
    L += [f"- `{k}`: {v}" for k, v in jc.most_common(15)]
    L += ["", "## Validation", "", f"- errors: {len(errors)}", f"- warnings: {len(warnings)}"]
    (BUILD / "SUMMARY.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())

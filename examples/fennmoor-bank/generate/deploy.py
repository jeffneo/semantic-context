"""Deploy the Fennmoor estate to BigQuery EMPTY, and validate every model.

Reads build/warehouse.json (run generate/build.py first). Nothing is billed:
tables are created empty, views validate their SQL on creation, and every
other model is checked with a dry run whose returned schema is diffed against
the spec. Each derived table is then created empty with its declared schema so
the models built on it can be validated in turn.

Logical projects (fennmoor-raw/-dw/-analytics) map onto one physical project;
every dataset is prefixed (default fnb_) so it cannot collide with anything.

Usage:
  uv run examples/fennmoor-bank/generate/deploy.py [--project P] [--config C]   (defaults: estate.yaml warehouse)
      [--prefix fnb_] [--all-shards] [--workers 12]

Credentials: an access token from `gcloud auth print-access-token` under the
named gcloud configuration (which impersonates the qlsc-bq service account).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import bigquery

from qlsc.warehouse.bigquery import client as bigquery_client

EXAMPLE = Path(__file__).resolve().parents[1]
SPEC, BUILD = EXAMPLE / "spec", EXAMPLE / "build"


# ---------------------------------------------------------------------------
# Naming and types
# ---------------------------------------------------------------------------

LOGICAL_FQN = re.compile(r"`fennmoor-(?:raw|dw|analytics)\.([A-Za-z0-9_]+)\.([^`]+)`")


def physical(sql: str, project: str, prefix: str) -> str:
    return LOGICAL_FQN.sub(lambda m: f"`{project}.{prefix}{m.group(1)}.{m.group(2)}`", sql)


BQ_TYPE = {"INTEGER": "INT64", "FLOAT": "FLOAT64", "BOOLEAN": "BOOL", "RECORD": "STRUCT"}


def norm_spec_type(t: str) -> str:
    t = t.strip()
    if t.startswith("ARRAY<"):
        return "ARRAY<" + norm_spec_type(t[6:-1]) + ">"
    if t.startswith("STRUCT<"):
        return "STRUCT"
    return t


def norm_bq_field(f) -> str:
    base = BQ_TYPE.get(f.field_type, f.field_type)
    return f"ARRAY<{base}>" if f.mode == "REPEATED" else base


def schema_diff(spec_cols: list[dict], fields) -> list[str]:
    got = {f.name.lower(): (f.name, norm_bq_field(f)) for f in fields}
    want = {c["name"].lower(): (c["name"], norm_spec_type(c["type"])) for c in spec_cols}
    diffs = []
    for k, (n, t) in want.items():
        if k not in got:
            diffs.append(f"missing column {n}")
        elif got[k][1] != t:
            diffs.append(f"{n}: spec {t}, BigQuery {got[k][1]}")
    for k, (n, t) in got.items():
        if k not in want:
            diffs.append(f"extra column {n} ({t})")
    return diffs


def shard_suffixes(shard: dict, window: dict, all_shards: bool) -> list[str]:
    start = dt.date.fromisoformat(str(window["start"]))
    end = start + dt.timedelta(days=window["days"] - 1)
    to = end.isoformat() if shard["to"] == "log_end" else str(shard["to"])
    if shard["suffix"] == "YYYYMMDD":
        d0, d1 = dt.date.fromisoformat(str(shard["from"])), dt.date.fromisoformat(to)
        days = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days + 1)]
        if not all_shards:  # first shard + the last 14: enough for wildcard SQL to resolve
            days = days[:1] + days[-14:]
        return [d.strftime("%Y%m%d") for d in days]
    y, m = map(int, str(shard["from"]).split("-"))
    ey, em = map(int, to.split("-")[:2])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def create_table_ddl(t: dict, name: str, project: str, prefix: str) -> str:
    cols = ",\n".join(
        f"  `{c['name']}` {c['type']}{' NOT NULL' if c.get('flags', {}).get('required') else ''}"
        for c in t["columns"]
    )
    ddl = f"CREATE OR REPLACE TABLE `{project}.{prefix}{t['dataset']}.{name}` (\n{cols}\n)"
    if t.get("partition"):
        ddl += f"\nPARTITION BY {t['partition']}"
    if t.get("cluster"):
        ddl += f"\nCLUSTER BY {', '.join(t['cluster'])}"
    if t.get("bq_description"):
        ddl += f"\nOPTIONS (description = {json.dumps(t['bq_description'])})"
    return ddl


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------


def levels(tables: list[dict]) -> list[list[dict]]:
    by_fqn = {t["fqn"]: t for t in tables}
    depth = {}

    def d(t):
        if t["fqn"] in depth:
            return depth[t["fqn"]]
        depth[t["fqn"]] = 0  # cycle guard
        depth[t["fqn"]] = 1 + max((d(by_fqn[s]) for s in t.get("sources", []) if s in by_fqn), default=-1)
        return depth[t["fqn"]]

    for t in tables:
        d(t)
    out = defaultdict(list)
    for t in tables:
        out[depth[t["fqn"]]].append(t)
    return [out[k] for k in sorted(out)]


def main() -> int:
    ap = argparse.ArgumentParser()
    wh_cfg = yaml.safe_load((EXAMPLE / "estate.yaml").read_text())["warehouse"]
    ap.add_argument("--project", default=wh_cfg["project"])
    ap.add_argument("--config", default=wh_cfg["gcloud_config"])
    ap.add_argument("--prefix", default="fnb_")
    ap.add_argument("--all-shards", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    wh = json.loads((BUILD / "warehouse.json").read_text())
    client = bigquery_client(args.project, args.config, "US")
    project, prefix = args.project, args.prefix
    results: dict[str, dict] = {}
    started = time.time()

    def run(sql: str, dry: bool = False):
        cfg = bigquery.QueryJobConfig(dry_run=dry, use_query_cache=False)
        job = client.query(sql, job_config=cfg)
        if not dry:
            job.result()
        return job

    # 1. datasets
    for ds, meta in wh["datasets"].items():
        d = bigquery.Dataset(f"{project}.{prefix}{ds}")
        d.location = "US"
        d.labels = {"qlsc": "fennmoor", "layer": meta.get("layer", "")}
        client.create_dataset(d, exists_ok=True)
    print(f"datasets: {len(wh['datasets'])} ready")

    def ensure_type(table_id: str, want: str):
        """CREATE OR REPLACE cannot switch TABLE <-> VIEW. Drop a mismatched object,
        but only an empty one in a dataset this tool manages (e.g. a placeholder
        left by an earlier failed run)."""
        try:
            existing = client.get_table(table_id)
        except GoogleAPICallError:
            return
        if existing.table_type == want:
            return
        if not existing.dataset_id.startswith(prefix) or (existing.num_rows or 0) > 0:
            raise RuntimeError(f"refusing to replace non-empty/unmanaged {table_id}")
        client.delete_table(table_id)

    def deploy(t: dict) -> dict:
        r = {
            "fqn": t["fqn"],
            "kind": t["kind"],
            "materialized": t["materialized"],
            "status": "ok",
            "diffs": [],
            "error": None,
            "physical": [],
        }
        name = t["name"]
        try:
            if t["kind"] == "base":
                names = (
                    [f"{name}{s}" for s in shard_suffixes(t["shard"], wh["log_window"], args.all_shards)]
                    if t.get("shard")
                    else [name]
                )
                for n in names:
                    run(create_table_ddl(t, n, project, prefix))
                r["physical"] = names
                return r
            sql = physical(t["sql"], project, prefix)
            target = f"`{project}.{prefix}{t['dataset']}.{name}`"
            ensure_type(
                f"{project}.{prefix}{t['dataset']}.{name}", "VIEW" if t["materialized"] == "view" else "TABLE"
            )
            if t["materialized"] == "view":
                run(f"CREATE OR REPLACE VIEW {target} AS\n{sql}")
                fields = client.get_table(f"{project}.{prefix}{t['dataset']}.{name}").schema
            else:
                fields = run(sql, dry=True).schema
                run(create_table_ddl(t, name, project, prefix))
            r["physical"] = [name]
            r["diffs"] = schema_diff(t["columns"], fields)
            if r["diffs"]:
                r["status"] = "schema_mismatch"
        except GoogleAPICallError as e:
            r["status"], r["error"] = "error", getattr(e, "message", str(e))
            # Placeholder with the declared schema so downstream models still validate.
            try:
                run(create_table_ddl(t, name, project, prefix))
            except GoogleAPICallError:
                pass
        return r

    for i, level in enumerate(levels(wh["tables"])):
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for r in pool.map(deploy, level):
                results[r["fqn"]] = r
        bad = sum(1 for t in level if results[t["fqn"]]["status"] != "ok")
        print(f"level {i}: {len(level)} tables, {bad} problems  ({time.time() - started:.0f}s)")

    write_report(wh, results, project, prefix, time.time() - started)
    counts = Counter(r["status"] for r in results.values())
    print(f"\n{dict(counts)} - report: build/deploy_report.md")
    return 0 if counts.get("error", 0) == 0 and counts.get("schema_mismatch", 0) == 0 else 1


def write_report(wh, results, project, prefix, secs):
    src = {t["fqn"]: t for t in wh["tables"]}
    counts = Counter(r["status"] for r in results.values())
    phys = sum(len(r["physical"]) for r in results.values())
    L = [
        "# Deploy report",
        "",
        f"Project `{project}`, dataset prefix `{prefix}`, {secs:.0f}s. "
        f"{len(results)} logical tables, {phys} physical objects created.",
        "",
        "| Result | Tables |",
        "|---|---|",
    ]
    L += [f"| {k} | {v} |" for k, v in counts.most_common()]
    errs = [r for r in results.values() if r["status"] == "error"]
    mism = [r for r in results.values() if r["status"] == "schema_mismatch"]
    if errs:
        L += ["", "## Errors", ""]
        for r in sorted(errs, key=lambda r: r["fqn"]):
            L += [f"- `{r['fqn']}` ({src[r['fqn']].get('materialized')}): {r['error']}"]
    if mism:
        L += ["", "## Schema mismatches (spec vs what BigQuery computes)", ""]
        for r in sorted(mism, key=lambda r: r["fqn"]):
            L += [f"- `{r['fqn']}`: " + "; ".join(r["diffs"])]
    (BUILD / "deploy_report.md").write_text("\n".join(L) + "\n")
    (BUILD / "deploy_report.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    sys.exit(main())

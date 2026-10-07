"""Write the demo UI's picture of the Fennmoor warehouse -> ui/src/examples/fennmoor/warehouse.json.

The tables the page draws are what BigQuery holds, as qlsc's extract snapshotted it (`work/catalog.json`: tables, views and date-sharded
families with their columns, partitioning and clustering). Two things come from the spec because the catalog does not hold them: a dataset's
source system and layer (for its label), and the scenario's size (teams, service accounts). Nothing of the answer key is written: no traps,
statuses or concepts. The physical project the estate is deployed to is not written either: the page speaks of the logical Fennmoor projects, so the
view definitions' references are rewritten to them (the catalog's aliases say how).

Run `qlsc extract` and `generate/build.py` first. Deterministic. Usage: uv run examples/fennmoor-bank/generate/ui_warehouse.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
CATALOG = EXAMPLE / "work" / "catalog.json"
SPEC = EXAMPLE / "build" / "warehouse.json"
LOG = EXAMPLE / "build" / "log" / "jobs.ndjson.gz"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "warehouse.json"

KINDS = {"TABLE": "table", "VIEW": "view", "WILDCARD": "sharded"}
PROJECTS = [
    "fennmoor-raw",
    "fennmoor-dw",
    "fennmoor-analytics",
]  # the order the page draws them in: sources, then the warehouse, then its users' space


def main() -> None:
    catalog = json.loads(CATALOG.read_text())
    spec = json.loads(SPEC.read_text())
    # `physical.dataset.` -> `logical.dataset.`, longest first so no alias is a prefix of another
    aliases = sorted(
        ((f"{physical}.", f"{logical}.") for physical, logical in catalog["aliases"].items()),
        key=lambda a: -len(a[0]),
    )

    def logical(sql: str) -> str:
        for physical_name, logical_name in aliases:
            sql = sql.replace(physical_name, logical_name)
        return sql

    datasets: dict[tuple[str, str], list[dict]] = {}
    for fqn, t in sorted(catalog["tables"].items()):
        project, dataset, name = fqn.split(".", 2)
        entry = {
            "name": name,
            "kind": KINDS[t["kind"]],
            "columns": [[c, ty] for c, ty in t["columns"].items()],
        }
        if t.get("partition"):
            entry["partition"] = t["partition"]
        if t.get("cluster"):
            entry["cluster"] = t["cluster"]
        if t.get("view_sql"):
            entry["sql"] = logical(t["view_sql"])
        if t.get("shards"):
            entry["shards"] = len(t["shards"])
        datasets.setdefault((project, dataset), []).append(entry)

    projects = []
    for project in PROJECTS:
        rows = []
        for (p, dataset), tables in sorted(datasets.items()):
            if p != project:
                continue
            meta = spec["datasets"][dataset]
            rows.append(
                {"name": dataset, "layer": meta["layer"], "source": meta.get("source"), "tables": tables}
            )
        projects.append({"name": project, "datasets": rows})

    physical_project = next(iter(catalog["aliases"])).split(".")[0]
    assert physical_project not in json.dumps(projects), "a view still names the physical project"

    with gzip.open(LOG, "rt") as f:
        jobs = sum(1 for _ in f)

    out = {
        "org": spec["org"]["name"],
        "log": {"start": spec["log_window"]["start"], "days": spec["log_window"]["days"], "jobs": jobs},
        "teams": len(spec["teams"]),
        "serviceAccounts": len(spec["service_accounts"]),
        "projects": projects,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n")
    n = sum(len(d["tables"]) for p in projects for d in p["datasets"])
    print(
        f"{OUT.relative_to(ROOT)}: {len(projects)} projects, {sum(len(p['datasets']) for p in projects)} datasets, {n} tables, {jobs:,} jobs"
    )


if __name__ == "__main__":
    main()

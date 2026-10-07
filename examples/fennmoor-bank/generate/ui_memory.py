"""Write the demo UI's picture of promotion to memory -> ui/src/examples/fennmoor/memory/memory.json.

Memory keeps what a Virtual Graph read fetched (qlsc/memory.py): an entity's context, its facts and their dimensions, each fact held for its table's
write cadence, every node carrying where it came from. This keeps what a page needs to show it, from the evaluations' own results and the layer:
  templates     what is fetched for each anchor label: qlsc.memory.template over the generated model, so hop 0 is the node, hop 1 the relationships
                touching it (the facts into it windowed and capped) and hop 2 their to-one ends
  contexts      the eight customers remembered in results/memory.json: nodes, relationships, and how many each read fetched
  provenance    what one remembered node carries (the memory database; the fields that name a person or the physical project are not written)
  holds         how long a fact of each catalog table holds, from its write cadence in the log (qlsc.memory.cadence_days): a number of days, `frozen`
                for good, or `none` where the log shows no cadence (a view: the default hold applies)
  session       results/economics.json: fifty questions about five customers, each as SQL in BigQuery and from memory, and what a fetch costs
  checks        results/memory.json: contexts read back as fetched, the same rows as the virtual graph, freshness, a batch
  entitlements  results/memory_entitlements.json: each principal's recall of each anchor against the warehouse as the oracle, and the broken reads caught
Nothing of the spec's answer key is read. Deterministic. Run `qlsc virtualize` and the memory evaluations first (results/ is committed).
Usage: uv run examples/fennmoor-bank/generate/ui_memory.py
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ui_queries import query

from qlsc import config, memory
from qlsc.graph import Graph

EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
RESULTS = EXAMPLE / "results"
SCHEMA = EXAMPLE / "work" / "virtual" / "schema.json"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "memory" / "memory.json"

MIB = 1024 * 1024
ANCHOR = "8322097816940277129"  # the customer whose remembered node's provenance is shown: the largest context in the evaluation

HOLDS = query("memory", "holds")
PROVENANCE = query("memory", "provenance")


def templates(s) -> tuple[dict, dict]:
    """memory.template for every label: the real function, over a model of the generated schema (it reads only the relationships and each node's partition)."""
    schema = json.loads(SCHEMA.read_text())["entities"]
    with Graph(s) as G:
        partition = {r["label"]: r["partition"] for r in G.rows(memory.TABLES, all=False)}
    model = SimpleNamespace(
        nodes={n["label"]: {"partition": partition.get(n["label"])} for n in schema["nodes"]},
        rels=[
            {
                "type": r["label"],
                "start": r["start"]["targetEntity"],
                "end": r["end"]["targetEntity"],
                "fk": r["end"]["keys"][0]["relationshipColumn"],
            }
            for r in schema["relationships"]
        ],
    )
    hops = s["memory"]["hops"]
    out = {}
    for anchor in sorted(model.nodes):
        out[anchor] = [
            {
                "hop": r.hop,
                "name": r.name,
                "label": r.label,
                "type": r.type,
                "start": r.start,
                "end": r.end,
                "inward": r.inward,
                "windowed": bool(r.window),
            }
            for r in memory.template(model, anchor, hops)
        ]
    return out, {k: s["memory"][k] for k in ("hops", "window_quarters", "cap", "unknown_hold_days")}


def principal_names(s) -> dict[str, str]:
    """A service account's address -> the principal it stands for (the config names them), so no address is written."""
    return {v: k for k, v in s["entitlements"]["principals"].items()}


def provenance(s) -> dict:
    with Graph(s, {"database": s["memory"]["database"]}) as M:
        r = M.rows(PROVENANCE, key=ANCHOR)[0]
    return {
        "fetchedAt": r["fetched_at"].isoformat(),
        "holdsUntil": r["holds_until"].isoformat(),
        "fetchedBy": principal_names(s).get(r["fetched_by"], "the data source"),
        "read": r["fetched_with"],
    }


def holds(s) -> dict[str, float | str]:
    """Each catalog table's hold, by the log's write cadence."""
    out = {}
    with Graph(s) as G:
        for r in G.rows(HOLDS):
            cadence = memory.cadence_days(r["write_days"])
            out[r["id"]] = "frozen" if r["frozen"] else "none" if cadence is None else cadence
    return out


def contexts() -> list[dict]:
    m = json.loads((RESULTS / "memory.json").read_text())
    out = []
    for key, c in m["customers"].items():
        f = c["fetched"]
        out.append(
            {
                "key": key,
                "nodes": f["nodes"],
                "edges": f["edges"],
                "reads": f["reads"],
                "capped": f["capped"],
                "seconds": f["seconds"],
            }
        )
    return sorted(out, key=lambda c: c["nodes"])


def session() -> dict:
    e = json.loads((RESULTS / "economics.json").read_text())
    fetches = {
        name: {
            "customers": f["customers"],
            "seconds": f["seconds"],
            "mibPerCustomer": round(f["billed per customer"] / MIB, 1),
            "breakEven": round(e["summary"]["break-even questions per customer"][name], 2),
        }
        for name, f in e["fetches"].items()
    }
    s = e["summary"]
    batch = e["fetches"]["a batch of 5 (the session's)"]["seconds"]
    return {
        "questions": [
            {"sql": q["sql"]["seconds"], "memory": q["memory"]["seconds"], "same": q["memory"]["same"]}
            for q in e["questions"]
        ],
        "fetchSeconds": batch,
        "fetches": fetches,
        "sqlMedian": s["sql latency"]["median"],
        "memoryMedian": s["memory latency"]["median"],
        "secondsWithout": round(s["without memory"]["seconds"], 1),
        "secondsWith": round(s["with memory"]["seconds"], 1),
        "mibWithout": round(s["without memory"]["billed"] / MIB),
        "mibWith": round(s["with memory"]["billed"] / MIB),
        "sameAnswer": s["same answer"],
        "fromMemory": s["from memory"],
    }


def checks() -> dict:
    m = json.loads((RESULTS / "memory.json").read_text())
    cs = list(m["customers"].values())
    questions = [
        q["verdict"] for c in cs for q in c["questions"].values()
    ]  # the same Cypher on memory and on the virtual graph: same, or capped (left out)
    return {
        "contexts": len(cs),
        "contextsSame": sum(not c["differences"] for c in cs),
        "questions": {v: questions.count(v) for v in ("same", "capped")}
        | {"different": len(questions) - questions.count("same") - questions.count("capped")},
        "freshness": {name: bool(v["ok"]) for name, v in m["freshness"].items()},
        "batch": {
            "customers": m["batch"]["customers"],
            "seconds": m["batch"]["seconds"],
            "oneAtATime": m["batch"]["seconds one at a time"],
        },
        "latency": {k: v["median"] for k, v in m["latency"].items()},
        "idempotent": bool(m["idempotence"]["same"]),
    }


def entitlements() -> dict:
    e = json.loads((RESULTS / "memory_entitlements.json").read_text())
    anchors = [f"{label} {key}" for label, key in e["anchors"]]
    principals = list(e["runs"])
    grid = [[e["runs"][p].get(a, {}).get("verdict", "") for a in anchors] for p in principals]
    incidents = sum(len(r.get("incidents", [])) for p in e["runs"].values() for r in p.values())
    return {
        "anchors": [{"label": label, "key": key} for label, key in e["anchors"]],
        "principals": principals,
        "verdicts": grid,
        "recalls": sum(len(row) for row in grid),
        "served": sum(1 for row in grid for v in row if v == "ok"),
        "incidents": incidents,
        "controls": [{"name": name, "caught": bool(c["caught"])} for name, c in e["controls"].items()],
    }


def main() -> None:
    s = config.load(EXAMPLE / "estate.yaml")
    tmpl, settings = templates(s)
    out = {
        "settings": settings,
        "templates": tmpl,
        "contexts": contexts(),
        "provenance": provenance(s),
        "holds": holds(s),
        "session": session(),
        "checks": checks(),
        "entitlements": entitlements(),
    }
    text = json.dumps(out, separators=(",", ":"), sort_keys=True)
    assert "jeffdavis" not in text and "fnb_" not in text, (
        "the physical project or its dataset prefix is named"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n")
    print(
        f"{OUT.relative_to(ROOT)}: {len(tmpl)} templates, {len(out['contexts'])} contexts, {len(out['holds'])} tables, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()

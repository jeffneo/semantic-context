"""Write the demo UI's picture of row-level security passed through -> ui/src/examples/fennmoor/security/security.json.

The warehouse is the rulebook (qlsc/entitle.py): what a principal may read is whatever BigQuery says they may, and the gateway never re-implements it.
Through the JDBC pass-through (vg-passthrough/) the same holds for Cypher over the Virtual Graph: every query carries a signed token naming whom it is for,
and the driver verifies it and runs the SQL as that principal. This keeps what a page needs to show it, from the evaluation's own results and cache:
  principals   for each test principal what the warehouse lets them read: the tables, the columns hidden by a policy tag, the tables a row access policy
               filters (the principal's allowlist, work/allowlists/), and how many canaries the oracle looked for in what the gateway told them
  cases        the same question asked as each principal (work/entitlements/): the query written, and what came back (the rows of a count, never a
               person's values: a question about names and emails keeps only its columns and its row count)
  driver       the pass-through reached directly, with no token, a forged one and an expired one: each refused, and why (results/entitlements.json)
  evaluation   each principal's twenty questions: schema leaks, row incidents, what was answered by each route
  controls     gateways broken on purpose, and the check that caught each
Nothing of the spec's answer key is read, and no service account's address or the physical project is written (a principal is its short name).

Run the entitlement evaluation first (eval/entitlements.py; results/ is committed, work/ is the run's). Deterministic.
Usage: uv run examples/fennmoor-bank/generate/ui_security.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from qlsc import config

EXAMPLE = Path(__file__).resolve().parents[1]
PROJECT = config.load(EXAMPLE / "estate.yaml")["warehouse"][
    "project"
]  # the physical project: never in what is written
ROOT = EXAMPLE.parents[1]
RESULTS = EXAMPLE / "results" / "entitlements.json"
WORK = EXAMPLE / "work"
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "security" / "security.json"

# What each test principal stands for, as entitlements/setup.py sets them up in the warehouse.
RULES = {
    "marketing": "Marketing and core customer data. The identifier columns are hidden by a policy tag.",
    "risk": "Fraud, lending and core data, with the identifiers. Customers in two states only, by a row access policy.",
    "contact-center": "Contact-center data only.",
}
# The questions the page puts side by side (eval/entitlements.py PROBES), and which of an answer's rows may be kept: a count by state, never a person's values.
CASES = {"P1": True, "P2": False}
QUESTIONS = {
    "P1": "How many customers do we have in each state?",
    "P2": "List the names and email addresses of our affluent customers.",
}


def answer(raw: dict | str, keep_rows: bool) -> dict:
    """What one route did with a question as one principal: the query, the size of what came back, or why nothing did."""
    v = json.loads(raw) if isinstance(raw, str) else raw
    out: dict = {}
    query = v.get("cypher") or v.get("sql")
    if v.get("declined"):
        out["declined"] = v["declined"]
    elif query and v.get("result"):
        r = v["result"]
        out |= {"query": query, "total": r.get("total", 0), "columns": r.get("columns", [])}
        if keep_rows and r.get("rows"):
            out["rows"] = [list(row.values()) for row in r["rows"]]
        if v.get("fallback") and not r.get("total"):
            out["why"] = v["fallback"]
    return out


def principals(s) -> list[dict]:
    res = json.loads(RESULTS.read_text().replace("<project>", PROJECT))["runs"]
    out = []
    for name, who in s["entitlements"]["principals"].items():
        allow = json.loads(
            (WORK / "allowlists" / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', who)}.json").read_text()
        )
        out.append(
            {
                "name": name,
                "rule": RULES[name],
                "readable": sorted(allow["tables"]),
                "hidden": sorted(allow["hidden"]),
                "tagged": len(allow["tagged"]),
                "rowFiltered": sorted(allow["rows"]),
                "canaries": res[name]["oracle"]["canaries"],
            }
        )
    return out


def cases(s) -> list[dict]:
    out = []
    for qid, keep in CASES.items():
        by = {}
        for name in s["entitlements"]["principals"]:
            a = json.loads((WORK / "entitlements" / f"{name}_{qid}.json").read_text())["answers"]
            by[name] = {"cypher": answer(a["cypher"], keep), "sql": answer(a["sql"], keep)}
        out.append({"id": qid, "text": QUESTIONS[qid], "as": by})
    return out


def evaluation() -> list[dict]:
    runs = json.loads(RESULTS.read_text().replace("<project>", PROJECT))["runs"]
    out = []
    for name, r in runs.items():
        qs = {k: v for k, v in r.items() if k != "oracle"}
        out.append(
            {
                "principal": name,
                "questions": len(qs),
                "schemaLeaks": sum(
                    len(q["schema"][k]) for q in qs.values() for k in ("sql", "cypher", "prompts")
                ),
                "rowIncidents": sum(
                    q["rows"][k]["verdict"] not in ("ok", "no answer")
                    for q in qs.values()
                    for k in ("sql", "cypher")
                ),
                "sqlAnswered": sum(bool(q["sql"]["answered"]) for q in qs.values()),
                "cypherAnswered": sum(bool(q["cypher"]["answered"]) for q in qs.values()),
                "routedToCypher": sum(q["route"] == "cypher" for q in qs.values()),
                "oracleAgrees": bool(r["oracle"]["agrees"]),
            }
        )
    return out


def main() -> None:
    s = config.load(EXAMPLE / "estate.yaml")
    res = json.loads(RESULTS.read_text().replace("<project>", PROJECT))
    out = {
        "principals": principals(s),
        "cases": cases(s),
        "driver": [
            {"name": k, "refused": bool(v["refused"]), "why": v["why"]} for k, v in res["driver"].items()
        ],
        "evaluation": evaluation(),
        "controls": [
            {
                "name": name,
                "principals": [x["principal"] for x in runs],
                "caught": all(x["caught"] for x in runs),
                "by": runs[0]["by"],
            }
            for name, runs in res["controls"].items()
        ],
    }
    text = json.dumps(out, separators=(",", ":"), sort_keys=True)
    assert PROJECT not in text and "fnb_" not in text and "iam.gserviceaccount" not in text, (
        "the physical project or an address is named"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text + "\n")
    print(
        f"{OUT.relative_to(ROOT)}: {len(out['principals'])} principals, {len(out['cases'])} cases, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()

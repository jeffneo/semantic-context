#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate a synthetic data-catalog export for Fennmoor (spec side) -> designed/catalog.json.

A stand-in for what a real catalog (Dataplex, Collibra, Alation) would export: a business
glossary bound to columns, and descriptions of tables and columns. It is someone's design,
so it is written from the spec with the flaws real catalogs have:

  partial      terms for 80% of the concepts; descriptions for ~70% of source, staging, mart,
               intermediate and ML tables; sandboxes, BI caches and most legacy tables uncurated
  stale        a few dead or frozen legacy tables still described and marked certified
  orphans      terms the bank defined that no data carries
  wrong        three bindings that repeat the business's own confusions (the traps in the log):
               the GA4 user id bound as the customer number, the card account id as the core
               account id, and the legacy cost-center id as the contact-center site

The pipeline reads the export like any other input (pipeline/align.py); it never reads specs/.
Deterministic (seeded). Usage: uv run specs/tools/make_catalog.py
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import yaml

SPECS = Path(__file__).resolve().parents[1]
ROOT = SPECS.parent
OUT = ROOT / "designed" / "catalog.json"
CURATED = {"raw", "staging", "mart", "intermediate", "ml"}
ORPHANS = [
    ("safe_deposit_box", "Safe Deposit Box", "A box rented to a customer in a branch vault, identified by box number and branch."),
    ("wire_transfer", "Wire Transfer", "A same-day funds transfer to or from another bank over Fedwire or SWIFT."),
    ("mortgage_escrow", "Mortgage Escrow Balance", "Funds held with a mortgage to pay property tax and insurance."),
    ("trust_account", "Trust Account", "An account held by a trustee for the benefit of another party."),
    ("overdraft_protection", "Overdraft Protection Enrollment", "Whether a checking account is enrolled to cover overdrafts from a linked account."),
    ("insurance_product", "Credit Insurance Product", "Credit life or disability insurance sold with a loan or card."),
]
WRONG = [  # (column, concept its term claims) - mirrors the planted wrong joins
    ("fennmoor-dw.dw_staging.stg_ga4__events.user_id", "customer.cif"),
    ("fennmoor-dw.dw_core.fct_card_transactions.card_account_id", "deposit_account.id"),
    ("fennmoor-analytics.legacy_edw.CC_EXPNS_MTHLY.CC_ID", "cc_site.id"),
]


def term_name(cid: str, desc: str) -> str:
    """A glossary name in business words: the description up to its first clause."""
    head = re.split(r" - |\. |\(|;|:", desc, maxsplit=1)[0].strip().rstrip(".")
    if len(head.split()) > 8 or len(head) < 4:
        head = cid.split(".", 1)[-1].replace("_", " ")
    return head[:1].upper() + head[1:]


def main() -> int:
    rnd = random.Random(20260925)
    concepts = yaml.safe_load((SPECS / "concepts.yaml").read_text())["concepts"]
    wh = json.loads((SPECS / "build" / "warehouse.json").read_text())
    kept = sorted(c for c in concepts if not c.startswith("date.") and rnd.random() < 0.8)
    terms = {c: {"id": c, "name": term_name(c, concepts[c].get("desc", c)), "definition": concepts[c].get("desc", ""),
                 "status": "approved", "columns": []} for c in kept}
    assets = []
    for t in wh["tables"]:
        curated = t["layer"] in CURATED and rnd.random() < 0.7
        stale = t["layer"] == "legacy" and t["status"] in ("dead", "frozen") and rnd.random() < 0.3
        if not (curated or stale):
            continue
        cols = {}
        for c in t["columns"]:
            cid = c.get("concept")
            fq = f"{t['fqn']}.{c['name']}"
            if cid in terms and rnd.random() < 0.75:
                terms[cid]["columns"].append(fq)
                cols[c["name"]] = concepts[cid].get("desc", "")
        assets.append({"table": t["fqn"], "description": t.get("desc", ""), "certified": bool(stale or rnd.random() < 0.4),
                       "columns": cols})
    for col, cid in WRONG:
        assert cid in terms, f"wrong binding needs the term {cid}"
        if col not in terms[cid]["columns"]:
            terms[cid]["columns"].append(col)
    for oid, name, definition in ORPHANS:
        terms[f"orphan.{oid}"] = {"id": f"orphan.{oid}", "name": name, "definition": definition, "status": "approved",
                                  "columns": []}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"source": "Fennmoor Data Catalog - synthetic export (generated from the spec with "
                                         "deliberate gaps, stale entries and three wrong bindings)",
                               "glossary": sorted(terms.values(), key=lambda x: x["id"]), "assets": assets}, indent=1))
    bound = sum(len(t["columns"]) for t in terms.values())
    print(f"{len(terms)} glossary terms ({len(ORPHANS)} orphans), {bound} column bindings ({len(WRONG)} wrong), "
          f"{len(assets)} described tables -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The row pool the process corpus is matched against: one read of the warehouse, kept locally.

Phase 2 of plans/2026-10-05-process-corpus.md. The pool is every `dw_contact_center.fct_calls` row with what a story can
point at: the customer's unwaived fees in the 60 days before a closure or payment call, the card purchases in the 30 days before
a card call, and the same customer's next call about the same thing within two weeks (a callback). It is written to
`build/corpus/pool.ndjson.gz` (gitignored, like the rest of `build/`), so the sampler runs offline and the warehouse is read once.

    uv run examples/fennmoor-bank/generate/corpus.py --pool

Nothing is written to the warehouse. The scan is about a gigabyte.
"""

from __future__ import annotations

import gzip
import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from qlsc import config
from qlsc.warehouse.bigquery import client

EXAMPLE = Path(__file__).resolve().parents[1]
POOL = EXAMPLE / "build" / "corpus" / "pool.ndjson.gz"
MAX_BYTES = 20 * 10**9

FEE_DAYS, PURCHASE_DAYS, CALLBACK_DAYS = 60, 30, 14

SQL = """
WITH calls AS (
  SELECT conversation_id, conversation_start, conversation_date, media_type, direction, customer_key, cif_number,
         queue_id, queue_name, queue_site_id, agent_user_id, agent_site_id, site_id, ivr_auth_result, ivr_intent,
         wrapup_code_name, is_account_closure_call, talk_sec, hold_sec, acw_sec, handle_sec, was_transferred,
         is_abandoned, is_authenticated
  FROM `{p}.{x}dw_contact_center.fct_calls`
),
fees AS (
  SELECT c.conversation_id,
         ARRAY_AGG(STRUCT(f.fee_id, f.fee_type, f.fee_amount, f.assessed_date, f.product_code)
                   ORDER BY f.assessed_date DESC LIMIT 3) AS fees
  FROM calls c
  JOIN `{p}.{x}dw_core.fct_fees` f
    ON f.customer_key = c.customer_key AND NOT f.is_waived AND NOT f.is_reversed
   AND f.assessed_date BETWEEN DATE_SUB(c.conversation_date, INTERVAL {fee_days} DAY) AND c.conversation_date
  WHERE c.ivr_intent IN ('CLOSE_ACCOUNT', 'PAYMENT')
  GROUP BY 1
),
buys AS (
  SELECT c.conversation_id,
         ARRAY_AGG(STRUCT(t.settlement_id, t.merchant_id, t.merchant_name, t.mcc_category_group, t.amount, t.post_date)
                   ORDER BY t.post_date DESC LIMIT 3) AS purchases
  FROM calls c
  JOIN `{p}.{x}dw_core.fct_card_transactions` t
    ON t.customer_key = c.customer_key AND t.is_purchase AND t.merchant_name IS NOT NULL
   AND t.post_date BETWEEN DATE_SUB(c.conversation_date, INTERVAL {purchase_days} DAY) AND c.conversation_date
  WHERE c.ivr_intent = 'CARD'
  GROUP BY 1
),
nxt AS (
  SELECT conversation_id, next_id, gap_days, next_answered
  FROM (
    SELECT conversation_id,
           LEAD(conversation_id) OVER w AS next_id,
           TIMESTAMP_DIFF(LEAD(conversation_start) OVER w, conversation_start, HOUR) / 24 AS gap_days,
           LEAD(agent_user_id IS NOT NULL) OVER w AS next_answered
    FROM calls
    WINDOW w AS (PARTITION BY cif_number, ivr_intent ORDER BY conversation_start)
  )
  WHERE gap_days BETWEEN 0 AND {callback_days}
)
SELECT c.*, f.fees, b.purchases, n.next_id, n.gap_days AS next_gap_days, n.next_answered
FROM calls c
LEFT JOIN fees f USING (conversation_id)
LEFT JOIN buys b USING (conversation_id)
LEFT JOIN nxt n USING (conversation_id)
ORDER BY c.conversation_start, c.conversation_id
"""


def plain(v):
    """JSON-ready: dates and decimals, nested through the arrays of structs."""
    if isinstance(v, datetime | date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [plain(x) for x in v]
    return v


def extract(settings) -> dict:
    """Read the pool from the warehouse and write it. Returns what it holds."""
    w = settings["warehouse"]
    sql = SQL.format(
        p=w["project"],
        x=w["dataset_prefix"],
        fee_days=FEE_DAYS,
        purchase_days=PURCHASE_DAYS,
        callback_days=CALLBACK_DAYS,
    )
    from google.cloud import bigquery

    bq = client(w["project"], w["gcloud_config"], w["location"])
    job = bq.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES))
    POOL.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(POOL, "wt") as out:
        for row in job.result():
            out.write(json.dumps(plain(dict(row.items())), sort_keys=True) + "\n")
            n += 1
    return {"rows": n, "bytes_billed": job.total_bytes_billed}


def load_pool(path: Path = POOL) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"{path} does not exist: run corpus.py --pool first")
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle]


def describe(pool: list[dict]) -> str:
    """A few lines on what the pool holds, for the first look and the manifest."""
    answered = [r for r in pool if r["agent_user_id"]]
    lines = [f"{len(pool):,} conversations, {len(answered):,} answered by an agent"]
    by_intent = Counter(r["ivr_intent"] for r in pool)
    for intent, n in sorted(by_intent.items()):
        rows = [r for r in pool if r["ivr_intent"] == intent]
        lines.append(
            f"  {intent:<14} {n:>7,}  answered {sum(1 for r in rows if r['agent_user_id']):>6,}"
            f"  fee {sum(1 for r in rows if r['fees']):>5,}  purchase {sum(1 for r in rows if r['purchases']):>5,}"
            f"  callback {sum(1 for r in rows if r['next_id']):>5,}"
        )
    return "\n".join(lines)


def settings():
    return config.load(EXAMPLE / "estate.yaml")

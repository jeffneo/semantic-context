SELECT
  src.dispute_id,
  src.settlement_id,
  src.account_id,
  src.opened_date,
  src.reason_code,
  CAST(src.dispute_amount_cents AS NUMERIC) / 100 AS dispute_amount,
  src.status,
  src.resolution,
  src.resolved_date,
  src.chargeback_flag,
  CAST(src.provisional_credit_cents AS NUMERIC) / 100 AS provisional_credit,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.dispute` AS src

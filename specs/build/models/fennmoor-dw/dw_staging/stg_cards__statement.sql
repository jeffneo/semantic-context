SELECT
  src.account_id,
  src.statement_date,
  CAST(src.closing_balance_cents AS NUMERIC) / 100 AS closing_balance,
  CAST(src.min_due_cents AS NUMERIC) / 100 AS min_due,
  src.due_date,
  CAST(src.interest_charged_cents AS NUMERIC) / 100 AS interest_charged,
  CAST(src.fees_charged_cents AS NUMERIC) / 100 AS fees_charged,
  CAST(src.purchases_cents AS NUMERIC) / 100 AS purchases,
  CAST(src.payments_cents AS NUMERIC) / 100 AS payments,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.statement` AS src

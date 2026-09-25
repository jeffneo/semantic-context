SELECT
  s.*
FROM `fennmoor-dw.dw_core.fct_daily_account_balances` AS s
WHERE s.balance_date >= '2026-03-01'

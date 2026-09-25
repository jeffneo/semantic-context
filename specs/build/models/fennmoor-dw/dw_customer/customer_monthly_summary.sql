SELECT
  DATE_TRUNC(b.balance_date, MONTH) AS month_start,
  b.customer_key,
  SUM(b.ledger_balance) / COUNT(DISTINCT b.balance_date) AS avg_daily_total_balance,
  MAX(b.ledger_balance) AS max_daily_total_balance,
  COUNT(DISTINCT b.account_key) AS accounts_with_balance
FROM `fennmoor-dw.dw_core.fct_daily_account_balances` b
GROUP BY ALL

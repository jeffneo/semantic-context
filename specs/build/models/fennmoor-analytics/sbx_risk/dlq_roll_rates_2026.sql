SELECT
  DATE_TRUNC(d.snapshot_date, MONTH) AS month_start,
  d.bucket,
  COUNT(DISTINCT d.account_key) AS loans,
  SUM(d.past_due_amount) AS past_due_amount
FROM `fennmoor-dw.dw_risk.fct_delinquency_daily` d
WHERE d.snapshot_date >= '2026-01-01'
GROUP BY ALL

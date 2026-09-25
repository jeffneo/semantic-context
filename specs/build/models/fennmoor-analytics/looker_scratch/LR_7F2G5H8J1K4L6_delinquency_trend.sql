SELECT
  d.snapshot_date,
  d.bucket,
  COUNT(*) AS loans,
  SUM(d.past_due_amount) AS past_due_amount
FROM `fennmoor-dw.dw_risk.fct_delinquency_daily` d
GROUP BY ALL

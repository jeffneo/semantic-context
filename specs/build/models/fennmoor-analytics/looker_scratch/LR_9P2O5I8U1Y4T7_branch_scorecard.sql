SELECT
  DATE_TRUNC(t.posted_date, MONTH) AS month_start,
  t.branch_id,
  b.branch_name,
  b.region,
  COUNT(*) AS txn_count,
  SUM(IF(t.signed_amount > 0, t.signed_amount, 0)) AS deposit_amount
FROM `fennmoor-dw.dw_core.fct_deposit_transactions` t
JOIN `fennmoor-dw.dw_core.dim_branch` b ON b.branch_id = t.branch_id
GROUP BY ALL

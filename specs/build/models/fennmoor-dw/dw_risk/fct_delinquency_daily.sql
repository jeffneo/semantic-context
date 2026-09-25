SELECT
  d.snapshot_date,
  a.account_key,
  a.customer_key,
  d.loan_number,
  a.product_code,
  d.dpd,
  d.bucket,
  d.past_due_amount
FROM `fennmoor-dw.dw_staging.stg_los__delinquency_snapshot` d
JOIN `fennmoor-dw.dw_core.dim_account` a ON a.loan_number = d.loan_number

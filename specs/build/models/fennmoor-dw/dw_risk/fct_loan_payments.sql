SELECT
  p.payment_id,
  p.payment_date,
  a.account_key,
  p.loan_number,
  p.amount,
  p.principal_portion AS principal,
  p.interest_portion AS interest,
  p.fee_portion AS fee,
  p.is_late,
  p.returned_flag AS is_returned
FROM `fennmoor-dw.dw_staging.stg_los__loan_payment` p
LEFT JOIN `fennmoor-dw.dw_core.dim_account` a ON a.loan_number = p.loan_number

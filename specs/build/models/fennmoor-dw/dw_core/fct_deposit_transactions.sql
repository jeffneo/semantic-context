SELECT
  t.transaction_id,
  t.posted_date,
  t.account_id AS core_account_id,
  a.account_key,
  a.customer_key,
  t.transaction_type_code AS transaction_type,
  t.transaction_amount AS amount,
  IF(t.debit_credit_indicator = 'D', -t.transaction_amount, t.transaction_amount) AS signed_amount,
  t.channel_code AS channel,
  t.branch_id,
  t.is_reversal
FROM `fennmoor-dw.dw_staging.stg_core__deposit_transaction` t
LEFT JOIN `fennmoor-dw.dw_core.dim_account` a ON a.core_account_id = t.account_id

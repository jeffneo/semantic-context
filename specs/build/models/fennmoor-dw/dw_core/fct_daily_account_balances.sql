SELECT
  b.balance_date,
  a.account_key,
  b.account_id AS core_account_id,
  a.customer_key,
  a.product_code,
  b.ledger_balance_amount AS ledger_balance,
  b.available_balance_amount AS available_balance,
  b.accrued_interest_amount AS accrued_interest
FROM `fennmoor-dw.dw_staging.stg_core__account_balance_daily` b
JOIN `fennmoor-dw.dw_core.dim_account` a ON a.core_account_id = b.account_id

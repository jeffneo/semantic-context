SELECT
  FARM_FINGERPRINT(u.account_natural_key) AS account_key,
  u.account_natural_key,
  u.account_family,
  u.core_account_id,
  u.card_account_id,
  u.loan_number,
  FARM_FINGERPRINT(u.primary_cif_number) AS customer_key,
  u.primary_cif_number,
  u.product_code,
  p.product_name,
  p.product_family,
  u.branch_id,
  u.open_date,
  u.close_date,
  u.close_reason,
  u.status_code,
  u.open_channel,
  u.close_date IS NULL AS is_open
FROM `fennmoor-dw.dw_intermediate.int_accounts_unioned` u
LEFT JOIN `fennmoor-dw.dw_core.dim_product` p ON p.product_code = u.product_code

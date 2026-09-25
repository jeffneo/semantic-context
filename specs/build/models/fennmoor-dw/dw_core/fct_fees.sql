SELECT
  f.fee_id,
  f.assessed_date,
  a.account_key,
  a.customer_key,
  a.product_code,
  f.fee_type_code AS fee_type,
  f.fee_amount,
  f.is_waived,
  f.is_reversed,
  IF(f.is_waived OR f.is_reversed, 0, f.fee_amount) AS net_fee
FROM `fennmoor-dw.dw_staging.stg_core__fee_assessed` f
LEFT JOIN `fennmoor-dw.dw_core.dim_account` a ON a.core_account_id = f.account_id

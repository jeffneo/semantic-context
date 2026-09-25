SELECT
  a.account_key,
  a.customer_key,
  c.cif_number,
  c.account_family,
  c.product_code,
  c.close_date,
  c.close_reason,
  c.is_voluntary,
  DATE_DIFF(c.close_date, a.open_date, DAY) AS tenure_days
FROM `fennmoor-dw.dw_intermediate.int_account_closures` c
JOIN `fennmoor-dw.dw_core.dim_account` a ON a.account_natural_key = c.account_natural_key

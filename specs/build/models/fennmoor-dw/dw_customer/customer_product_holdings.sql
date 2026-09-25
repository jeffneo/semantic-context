SELECT
  a.customer_key,
  a.product_code,
  p.product_family,
  p.product_line,
  COUNTIF(a.is_open) AS open_accounts,
  MIN(a.open_date) AS first_open_date,
  MAX(a.close_date) AS last_close_date
FROM `fennmoor-dw.dw_core.dim_account` a
JOIN `fennmoor-dw.dw_core.dim_product` p ON p.product_code = a.product_code
GROUP BY ALL

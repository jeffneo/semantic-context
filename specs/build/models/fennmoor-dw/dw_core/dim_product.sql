SELECT
  p.product_code,
  p.product_name,
  p.product_family_code AS product_family,
  p.product_type_code AS product_type,
  p.monthly_fee_amount,
  p.interest_rate,
  p.term_months,
  p.is_active,
  ph.product_line,
  ph.product_group,
  ph.reporting_category,
  UPPER(TRIM(ph.fee_bearing)) = 'Y' AS is_fee_bearing
FROM `fennmoor-dw.dw_staging.stg_core__product` p
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__product_hierarchy` ph ON ph.prod_cd = p.product_code

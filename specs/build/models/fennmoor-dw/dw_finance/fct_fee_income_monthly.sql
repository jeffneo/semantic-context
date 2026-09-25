SELECT
  DATE_TRUNC(f.assessed_date, MONTH) AS month_start,
  f.product_code,
  f.fee_type,
  SUM(f.fee_amount) AS gross_fees,
  SUM(IF(f.is_waived, f.fee_amount, 0)) AS waived_fees,
  SUM(f.net_fee) AS net_fees
FROM `fennmoor-dw.dw_core.fct_fees` f
GROUP BY ALL

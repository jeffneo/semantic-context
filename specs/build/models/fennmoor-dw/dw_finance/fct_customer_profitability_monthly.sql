WITH fees AS (
SELECT f.customer_key, DATE_TRUNC(f.assessed_date, MONTH) AS month_start, SUM(f.net_fee) AS fee_revenue
FROM `fennmoor-dw.dw_core.fct_fees` f
GROUP BY 1, 2
),
ic AS (
SELECT t.customer_key, DATE_TRUNC(t.post_date, MONTH) AS month_start, SUM(t.interchange) AS interchange_revenue
FROM `fennmoor-dw.dw_core.fct_card_transactions` t
GROUP BY 1, 2
)
SELECT
  s.customer_key,
  s.month_start,
  s.avg_daily_total_balance AS avg_balance,
  COALESCE(fees.fee_revenue, 0) AS fee_revenue,
  COALESCE(ic.interchange_revenue, 0) AS interchange_revenue,
  s.avg_daily_total_balance * 0.021 / 12 AS deposit_margin,
  COALESCE(fees.fee_revenue, 0) + COALESCE(ic.interchange_revenue, 0) + s.avg_daily_total_balance * 0.021 / 12 AS total_revenue
FROM `fennmoor-dw.dw_customer.customer_monthly_summary` s
LEFT JOIN fees ON fees.customer_key = s.customer_key AND fees.month_start = s.month_start
LEFT JOIN ic ON ic.customer_key = s.customer_key AND ic.month_start = s.month_start

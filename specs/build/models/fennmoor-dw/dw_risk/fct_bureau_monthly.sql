SELECT
  b.archive_date AS archive_month,
  c.customer_key,
  b.fico_08,
  b.vantage_4,
  b.utilization_pct,
  b.total_revolving_balance,
  b.num_delinquent_30_24m,
  b.estimated_income
FROM `fennmoor-dw.dw_staging.stg_bureau__consumer_attributes_monthly` b
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = b.cif_number

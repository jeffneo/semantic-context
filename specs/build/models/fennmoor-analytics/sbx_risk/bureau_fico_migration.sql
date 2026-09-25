SELECT
  b.archive_month,
  CASE WHEN b.fico_08 >= 740 THEN '740+' WHEN b.fico_08 >= 670 THEN '670-739' WHEN b.fico_08 >= 580 THEN '580-669' ELSE '<580' END AS fico_band,
  COUNT(*) AS customers
FROM `fennmoor-dw.dw_risk.fct_bureau_monthly` b
GROUP BY ALL

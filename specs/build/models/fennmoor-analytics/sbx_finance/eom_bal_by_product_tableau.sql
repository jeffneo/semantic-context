SELECT
  e.SNAP_MTH AS snap_month,
  p.reporting_category,
  SUM(e.EOM_BAL_AMT) AS eom_balance
FROM `fennmoor-analytics.legacy_edw.EOM_BAL_SNAP` e
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__product_hierarchy` p ON p.prod_cd = e.PROD_CD
GROUP BY ALL

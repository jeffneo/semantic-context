SELECT
  e.FISC_PRD AS fiscal_period,
  e.CC_ID AS cc_id,
  SUM(e.ACTL_AMT) AS expense,
  SUM(v.CALLS_HNDLD) AS calls
FROM `fennmoor-analytics.legacy_edw.CC_EXPNS_MTHLY` e
JOIN `fennmoor-analytics.legacy_edw.CC_CALL_VOL_DLY` v ON v.SITE_CD = e.CC_ID
GROUP BY ALL

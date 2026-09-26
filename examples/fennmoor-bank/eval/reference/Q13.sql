-- Q13: the CC tables and their three meanings of CC: credit card (CC_TXN_HIST, CC_ACCT_MSTR), contact
-- center (CC_CALL_VOL_DLY, CC_AGENT_DLY), cost center (CC_EXPNS_MTHLY, CC_EXPENSE_SUMMARY).
SELECT 'legacy_edw.CC_TXN_HIST' AS table_, 'credit card transactions' AS meaning, COUNT(*) AS rows_,
       CAST(MIN(TXN_DT) AS STRING) AS first_, CAST(MAX(TXN_DT) AS STRING) AS last_
FROM `fennmoor-analytics.legacy_edw.CC_TXN_HIST`
UNION ALL SELECT 'legacy_edw.CC_ACCT_MSTR', 'credit card accounts', COUNT(*), CAST(MIN(OPEN_DT) AS STRING), CAST(MAX(OPEN_DT) AS STRING)
          FROM `fennmoor-analytics.legacy_edw.CC_ACCT_MSTR`
UNION ALL SELECT 'legacy_edw.CC_CALL_VOL_DLY', 'contact center call volume', COUNT(*), CAST(MIN(CALL_DT) AS STRING), CAST(MAX(CALL_DT) AS STRING)
          FROM `fennmoor-analytics.legacy_edw.CC_CALL_VOL_DLY`
UNION ALL SELECT 'legacy_edw.CC_AGENT_DLY', 'contact center agent activity', COUNT(*), CAST(MIN(CALL_DT) AS STRING), CAST(MAX(CALL_DT) AS STRING)
          FROM `fennmoor-analytics.legacy_edw.CC_AGENT_DLY`
UNION ALL SELECT 'legacy_edw.CC_EXPNS_MTHLY', 'cost center expense (legacy)', COUNT(*), MIN(FISC_PRD), MAX(FISC_PRD)
          FROM `fennmoor-analytics.legacy_edw.CC_EXPNS_MTHLY`
UNION ALL SELECT 'gl_erp.CC_EXPENSE_SUMMARY', 'cost center expense (GL)', COUNT(*), MIN(PERIOD_NAME), MAX(PERIOD_NAME)
          FROM `fennmoor-raw.gl_erp.CC_EXPENSE_SUMMARY`

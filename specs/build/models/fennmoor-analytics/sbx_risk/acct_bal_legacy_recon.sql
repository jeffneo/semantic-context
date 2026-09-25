SELECT
  l.BAL_DT AS balance_date,
  a.ACCT_ID AS core_account_id,
  l.LDGR_BAL_AMT AS legacy_balance,
  f.ledger_balance AS dw_balance,
  l.LDGR_BAL_AMT - f.ledger_balance AS diff
FROM `fennmoor-analytics.legacy_edw.ACCT_DLY_BAL` l
JOIN `fennmoor-raw.core_banking_cdc.ACCOUNT` a ON a.ACCT_NO = l.ACCT_NBR
JOIN `fennmoor-dw.dw_core.fct_daily_account_balances` f ON f.core_account_id = a.ACCT_ID AND f.balance_date = l.BAL_DT

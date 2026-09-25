SELECT
  src.PERIOD_NAME AS period_name,
  src.CC_ID AS cost_center_id,
  src.GL_ACCT AS gl_account_code,
  src.ACTUAL_AMT AS actual_amount,
  src.BUDGET_AMT AS budget_amount,
  src.VARIANCE_AMT AS variance_amount,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.CC_EXPENSE_SUMMARY` AS src
WHERE NOT src._fivetran_deleted

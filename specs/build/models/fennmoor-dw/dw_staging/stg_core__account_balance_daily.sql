SELECT
  src.ACCT_ID AS account_id,
  src.BAL_DT AS balance_date,
  src.LEDGER_BAL_AMT AS ledger_balance_amount,
  src.AVAIL_BAL_AMT AS available_balance_amount,
  src.COLL_BAL_AMT AS collected_balance_amount,
  src.AVG_MTD_BAL_AMT AS avg_mtd_balance_amount,
  src.ACCRD_INT_AMT AS accrued_interest_amount,
  src.HOLD_AMT AS hold_amount,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_BALANCE_DLY` AS src

SELECT
  src.ACCT_ID AS account_id,
  src.ACCR_DT AS accrual_date,
  src.ACCR_AMT AS accrual_amount,
  src.RT AS rate,
  src.BAL_AMT AS balance_amount,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.INTEREST_ACCRUAL` AS src

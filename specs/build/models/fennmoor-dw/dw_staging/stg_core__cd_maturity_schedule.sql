SELECT
  src.ACCT_ID AS account_id,
  src.MAT_DT AS maturity_date,
  src.TERM_MTHS AS term_months,
  src.RENEW_OPT_CD AS renewal_option_code,
  src.PRIN_AMT AS principal_amount,
  src.RT AS rate,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CD_MATURITY_SCHED` AS src

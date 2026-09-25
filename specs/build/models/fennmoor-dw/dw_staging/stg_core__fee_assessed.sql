SELECT
  src.FEE_ID AS fee_id,
  src.ACCT_ID AS account_id,
  src.FEE_TYP_CD AS fee_type_code,
  src.FEE_AMT AS fee_amount,
  src.ASSESS_DT AS assessed_date,
  src.WAIVED_FLG = 'Y' AS is_waived,
  src.WAIVE_RSN_CD AS waive_reason_code,
  src.WAIVED_BY_USER_ID AS waived_by_user_id,
  src.REVERSED_FLG = 'Y' AS is_reversed,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.FEE_ASSESSED` AS src

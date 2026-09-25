SELECT
  src.ACCT_ID AS account_id,
  src.STAT_CD AS status_code,
  src.PREV_STAT_CD AS previous_status_code,
  src.CHG_TS AS changed_at,
  src.CHG_RSN_CD AS change_reason_code,
  src.CHG_USER_ID AS change_user_id,
  src.CHG_CHNL_CD AS change_channel_code,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_STATUS_HIST` AS src

SELECT
  src.ACCT_ID AS account_id,
  RIGHT(src.ACCT_NO, 4) AS account_number_last4,
  src.PROD_CD AS product_code,
  src.BRNCH_ID AS branch_id,
  src.ACCT_STAT_CD AS account_status_code,
  src.OPEN_DT AS open_date,
  src.CLS_DT AS close_date,
  src.CLS_RSN_CD AS close_reason_code,
  src.OPEN_CHNL_CD AS open_channel_code,
  src.CCY_CD AS currency_code,
  src.INT_RT AS interest_rate,
  src.OD_LMT_AMT AS overdraft_limit_amount,
  src.STMT_CYC_CD AS statement_cycle_code,
  src.ESCHEAT_FLG = 'Y' AS is_escheat,
  src.CRT_TS AS created_at,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT` AS src

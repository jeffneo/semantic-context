SELECT
  src.PROD_CD AS product_code,
  src.PROD_NM AS product_name,
  src.PROD_FMLY_CD AS product_family_code,
  src.PROD_TYP_CD AS product_type_code,
  src.MIN_BAL_AMT AS min_balance_amount,
  src.MTHLY_FEE_AMT AS monthly_fee_amount,
  src.INT_RT AS interest_rate,
  src.TERM_MTHS AS term_months,
  src.ACTV_FLG = 'Y' AS is_active,
  src.EFF_DT AS effective_date,
  src.END_DT AS end_date,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.PRODUCT` AS src

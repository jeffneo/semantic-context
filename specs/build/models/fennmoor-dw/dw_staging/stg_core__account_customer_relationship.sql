SELECT
  src.ACCT_ID AS account_id,
  src.CIF_NO AS cif_number,
  src.REL_TYP_CD AS relationship_type_code,
  src.REL_EFF_DT AS relationship_effective_date,
  src.REL_END_DT AS relationship_end_date,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_CUSTOMER_REL` AS src

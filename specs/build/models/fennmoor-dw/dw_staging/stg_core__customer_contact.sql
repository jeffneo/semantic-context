SELECT
  src.CIF_NO AS cif_number,
  src.CNTCT_SEQ_NO AS contact_sequence_number,
  src.CNTCT_TYP_CD AS contact_type_code,
  src.CNTCT_VAL AS contact_value,
  src.VRFD_FLG = 'Y' AS is_verified,
  src.PRIM_FLG = 'Y' AS is_primary,
  src.OPT_IN_FLG = 'Y' AS is_opted_in,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER_CONTACT` AS src

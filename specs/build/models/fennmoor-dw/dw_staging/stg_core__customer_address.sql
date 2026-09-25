SELECT
  src.CIF_NO AS cif_number,
  src.ADDR_SEQ_NO AS address_sequence_number,
  src.ADDR_TYP_CD AS address_type_code,
  src.ADDR_LN_1 AS address_line_1,
  src.ADDR_LN_2 AS address_line_2,
  src.CITY_NM AS city_name,
  src.ST_CD AS state_code,
  src.ZIP_CD AS zip_code,
  src.CNTRY_CD AS country_code,
  src.PRIM_FLG = 'Y' AS is_primary,
  src.EFF_DT AS effective_date,
  src.END_DT AS end_date,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER_ADDRESS` AS src

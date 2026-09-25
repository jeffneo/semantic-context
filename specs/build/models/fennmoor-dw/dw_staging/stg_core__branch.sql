SELECT
  src.BRNCH_ID AS branch_id,
  src.BRNCH_NM AS branch_name,
  src.BRNCH_TYP_CD AS branch_type_code,
  src.ADDR_LN_1 AS address_line_1,
  src.CITY_NM AS city_name,
  src.ST_CD AS state_code,
  src.ZIP_CD AS zip_code,
  src.RGN_CD AS region_code,
  src.MKT_CD AS market_code,
  src.MGR_EMP_ID AS manager_employee_id,
  src.CC_ID AS cost_center_id,
  src.OPEN_DT AS open_date,
  src.CLS_DT AS close_date,
  src.LAT AS latitude,
  src.LNG AS longitude,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.BRANCH` AS src

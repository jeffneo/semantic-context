SELECT
  src.zip,
  src.state,
  src.msa_name,
  src.fennmoor_region,
  src.market_cd,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.zip_region_map` AS src

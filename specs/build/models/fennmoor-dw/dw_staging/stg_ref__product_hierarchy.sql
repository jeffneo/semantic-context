SELECT
  src.prod_cd,
  src.product_line,
  src.product_group,
  src.reporting_category,
  src.fee_bearing,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.product_hierarchy_FINAL_v3` AS src

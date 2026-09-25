SELECT
  src.mcc,
  src.description,
  src.category_group,
  src.irs_reportable,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.mcc_code` AS src

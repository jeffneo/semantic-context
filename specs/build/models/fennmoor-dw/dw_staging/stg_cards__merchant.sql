SELECT
  src.merchant_id,
  src.merchant_name,
  src.dba_name,
  src.mcc,
  src.city,
  src.state,
  src.country,
  src.postal_code,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.merchant` AS src

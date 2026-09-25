SELECT
  src.card_token,
  src.account_id,
  src.change_ts,
  src.old_status,
  src.new_status,
  src.reason,
  src.channel,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.card_status_change` AS src

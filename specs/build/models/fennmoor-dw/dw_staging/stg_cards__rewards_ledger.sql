SELECT
  src.account_id,
  src.activity_date,
  src.points,
  src.activity_type,
  src.settlement_id,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.rewards_ledger` AS src

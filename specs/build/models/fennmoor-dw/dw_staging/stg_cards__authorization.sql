SELECT
  src.auth_id,
  src.card_token,
  src.account_id,
  src.auth_ts,
  CAST(src.amount_cents AS NUMERIC) / 100 AS amount,
  src.currency_code,
  src.merchant_id,
  src.mcc,
  src.pos_entry_mode,
  src.channel,
  src.response_code,
  src.decline_reason,
  src.vendor_fraud_score,
  src.avs_result,
  src.cvv_result,
  src.is_recurring,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.authorization` AS src

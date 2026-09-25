SELECT
  src.card_token,
  src.account_id,
  src.card_role,
  src.pan_last4,
  src.expiry_yyyymm,
  src.issue_date,
  src.activation_date,
  src.status,
  src.replacement_reason,
  src.embossed_name,
  src.is_virtual,
  src.digital_wallet,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.card` AS src

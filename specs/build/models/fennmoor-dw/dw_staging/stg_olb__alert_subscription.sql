SELECT
  src.olb_user_id,
  src.alert_type,
  src.channel,
  src.threshold_amount,
  src.enabled,
  src.updated_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.alert_subscription` AS src
WHERE NOT src._fivetran_deleted

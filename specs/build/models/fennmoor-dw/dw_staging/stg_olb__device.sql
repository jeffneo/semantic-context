SELECT
  src.device_id,
  src.olb_user_id,
  src.platform,
  src.model,
  src.os_version,
  src.registered_at,
  src.last_seen_at,
  src.trusted,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.device` AS src
WHERE NOT src._fivetran_deleted

SELECT
  src.rule_id,
  src.rule_version,
  src.rule_name,
  src.channel,
  src.active,
  src.threshold,
  src.created_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.rule` AS src
WHERE NOT src._fivetran_deleted

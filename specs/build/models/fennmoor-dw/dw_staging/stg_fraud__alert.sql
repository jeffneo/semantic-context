SELECT
  src.alert_id,
  src.alert_ts,
  src.entity_type,
  src.entity_ref,
  src.cif_number,
  src.rule_id,
  src.model_score,
  src.alert_status,
  src.priority,
  src.channel,
  src.amount,
  src.disposition,
  src.dispositioned_at,
  src.analyst_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.alert` AS src
WHERE NOT src._fivetran_deleted

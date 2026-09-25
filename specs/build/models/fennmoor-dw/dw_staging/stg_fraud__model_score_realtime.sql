SELECT
  src.score_id,
  src.scored_at,
  src.entity_type,
  src.entity_ref,
  src.model_name,
  src.model_version,
  src.score,
  src.reason_codes,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.model_score_realtime` AS src
WHERE NOT src._fivetran_deleted

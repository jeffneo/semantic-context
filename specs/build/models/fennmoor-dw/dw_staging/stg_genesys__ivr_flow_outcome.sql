SELECT
  src.conversation_id,
  src.flow_id,
  src.flow_name,
  src.outcome_id,
  src.outcome_name,
  src.outcome_value,
  src.outcome_start,
  src.outcome_end,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.ivr_flow_outcome` AS src
WHERE NOT src._fivetran_deleted

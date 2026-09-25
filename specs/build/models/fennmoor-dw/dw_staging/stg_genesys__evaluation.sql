SELECT
  src.evaluation_id,
  src.conversation_id,
  src.agent_id,
  src.evaluator_id,
  src.form_name,
  src.total_score,
  src.critical_score,
  src.released_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.evaluation` AS src
WHERE NOT src._fivetran_deleted

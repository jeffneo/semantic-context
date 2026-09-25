SELECT
  src.survey_id,
  src.conversation_id,
  src.agent_user_id,
  src.sent_at,
  src.completed_at,
  src.csat_score,
  src.nps_score,
  src.verbatim,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.survey_response` AS src
WHERE NOT src._fivetran_deleted

SELECT
  src.id AS queue_id,
  src.name,
  src.division_id,
  src.description,
  src.acw_timeout_ms,
  src.skill_evaluation_method,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.queue` AS src
WHERE NOT src._fivetran_deleted

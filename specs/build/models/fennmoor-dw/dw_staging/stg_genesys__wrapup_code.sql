SELECT
  src.id AS wrapup_code_id,
  src.name,
  src.description,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.wrapup_code` AS src
WHERE NOT src._fivetran_deleted

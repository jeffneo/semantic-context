SELECT
  src.id AS canvas_id,
  src.name,
  src.created_at,
  src.tags,
  src.archived,
  src.enabled,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.canvas` AS src
WHERE NOT src._fivetran_deleted

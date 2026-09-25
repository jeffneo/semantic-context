SELECT
  src.id AS campaign_id,
  src.name,
  src.created_at,
  src.channels,
  src.tags,
  src.archived,
  src.first_sent,
  src.last_sent,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.campaign` AS src
WHERE NOT src._fivetran_deleted

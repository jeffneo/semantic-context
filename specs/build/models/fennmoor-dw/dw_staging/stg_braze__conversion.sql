SELECT
  src.id AS conversion_id,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.conversion_behavior,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.conversion` AS src
WHERE NOT src._fivetran_deleted

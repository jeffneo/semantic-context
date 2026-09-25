SELECT
  src.id AS push_event_id,
  src.event_type,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.platform,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.push_event` AS src
WHERE NOT src._fivetran_deleted

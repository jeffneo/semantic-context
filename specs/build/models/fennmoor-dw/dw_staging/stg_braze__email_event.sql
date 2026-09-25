SELECT
  src.id AS email_event_id,
  src.event_type,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.dispatch_id,
  src.email_address,
  src.url,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.email_event` AS src
WHERE NOT src._fivetran_deleted

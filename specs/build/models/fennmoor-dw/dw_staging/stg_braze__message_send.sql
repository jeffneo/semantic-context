SELECT
  src.id AS message_send_id,
  src.user_id,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.canvas_step_id,
  src.channel,
  src.sent_at,
  src.message_variation_id,
  src.dispatch_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.message_send` AS src
WHERE NOT src._fivetran_deleted

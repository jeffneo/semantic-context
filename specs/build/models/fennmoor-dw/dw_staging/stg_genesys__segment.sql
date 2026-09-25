SELECT
  src.segment_id,
  src.conversation_id,
  src.participant_id,
  src.segment_type,
  src.segment_start,
  src.segment_end,
  src.queue_id,
  src.wrap_up_code,
  src.wrap_up_note,
  src.disconnect_type,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.segment` AS src
WHERE NOT src._fivetran_deleted

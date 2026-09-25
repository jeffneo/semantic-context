SELECT
  src.conversation_id,
  src.conversation_start,
  src.conversation_end,
  src.originating_direction,
  src.media_type,
  src.division_id,
  src.ani_hash,
  src.dnis,
  src.external_tag,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.conversation` AS src
WHERE NOT src._fivetran_deleted

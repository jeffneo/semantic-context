SELECT
  src.participant_id,
  src.conversation_id,
  src.purpose,
  src.user_id,
  src.queue_id,
  src.participant_name,
  src.start_time,
  src.end_time,
  src.attributes,
  JSON_VALUE(src.attributes, '$.cif') AS cif_number,
  JSON_VALUE(src.attributes, '$.ivr_auth') AS ivr_auth_result,
  JSON_VALUE(src.attributes, '$.intent') AS intent,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.participant` AS src
WHERE NOT src._fivetran_deleted

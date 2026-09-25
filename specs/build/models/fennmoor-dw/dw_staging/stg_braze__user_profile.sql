SELECT
  src.external_id,
  src.braze_id,
  src.email,
  src.phone,
  src.first_name,
  src.email_subscribe,
  src.push_subscribe,
  src.custom_attributes,
  src.updated_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.user_profile` AS src
WHERE NOT src._fivetran_deleted

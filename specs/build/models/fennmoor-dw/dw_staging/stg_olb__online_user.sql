SELECT
  src.olb_user_id,
  src.cif_number,
  src.ga4_user_id,
  src.username,
  src.enrolled_at,
  src.enrollment_channel,
  src.status,
  src.mfa_method,
  src.last_login_at,
  src.is_business,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.online_user` AS src
WHERE NOT src._fivetran_deleted

SELECT
  src.id AS user_id,
  src.name,
  src.email,
  src.username,
  src.profile_id,
  src.user_role_id,
  src.is_active,
  src.employee_number,
  src.department,
  src.division,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.user` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted

SELECT
  src.id AS user_id,
  src.name,
  src.email,
  src.department,
  src.title,
  src.manager_id,
  src.location_name,
  src.employee_id,
  src.state,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.user` AS src
WHERE NOT src._fivetran_deleted

SELECT
  src.cost_center_id,
  src.cost_center_name,
  src.department_code,
  src.owner_worker_id,
  src.region,
  src.is_active,
  src.effective_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.cost_center` AS src
WHERE NOT src._fivetran_deleted

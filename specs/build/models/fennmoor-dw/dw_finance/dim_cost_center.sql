SELECT
  c.cost_center_id,
  c.cost_center_name,
  c.department_code,
  c.region,
  c.is_active,
  c.owner_worker_id
FROM `fennmoor-dw.dw_staging.stg_gl__cost_center` c

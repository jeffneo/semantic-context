SELECT
  b.branch_id,
  b.branch_name,
  b.branch_type_code AS branch_type,
  b.city_name AS city,
  b.state_code,
  b.zip_code,
  COALESCE(z.fennmoor_region, b.region_code) AS region,
  b.market_code,
  z.msa_name,
  b.cost_center_id,
  b.manager_employee_id,
  b.open_date,
  b.close_date,
  b.close_date IS NULL AS is_open
FROM `fennmoor-dw.dw_staging.stg_core__branch` b
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__zip_region_map` z ON z.zip = b.zip_code

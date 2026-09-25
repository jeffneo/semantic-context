SELECT
  u.user_id AS agent_user_id,
  u.name AS agent_name,
  u.employee_id,
  u.location_name,
  CASE WHEN STRPOS(u.location_name, 'Tulsa') > 0 THEN 'TUL' WHEN STRPOS(u.location_name, 'Spokane') > 0 THEN 'SPK' WHEN STRPOS(u.location_name, 'Manila') > 0 THEN 'MNL' END AS site_id,
  u.employee_id IS NULL AS is_bpo,
  w.hire_date,
  DATE_DIFF(CURRENT_DATE(), w.hire_date, MONTH) AS tenure_months,
  w.job_profile,
  u.manager_id AS manager_user_id
FROM `fennmoor-dw.dw_staging.stg_genesys__user` u
LEFT JOIN `fennmoor-dw.dw_staging_restricted.stg_wd__worker` w ON w.worker_id = u.employee_id

SELECT
  src.worker_id,
  src.legal_name,
  src.preferred_name,
  src.work_email,
  src.hire_date,
  src.termination_date,
  src.job_profile,
  src.job_family,
  src.management_level,
  src.cost_center_id,
  src.location,
  src.supervisor_worker_id,
  src.worker_status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.worker` AS src
WHERE NOT src._fivetran_deleted

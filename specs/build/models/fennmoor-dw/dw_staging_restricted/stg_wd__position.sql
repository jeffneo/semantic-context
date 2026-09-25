SELECT
  src.position_id,
  src.worker_id,
  src.job_profile,
  src.effective_date,
  src.fte,
  src.scheduled_hours,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.position` AS src
WHERE NOT src._fivetran_deleted

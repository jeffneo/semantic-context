SELECT
  src.id AS task_id,
  src.who_id,
  src.what_id,
  src.subject,
  src.type,
  src.status,
  src.activity_date,
  src.call_duration_in_seconds,
  src.call_disposition,
  src.owner_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.task` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted

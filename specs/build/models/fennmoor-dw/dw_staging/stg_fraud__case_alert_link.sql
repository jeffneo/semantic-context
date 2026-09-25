SELECT
  src.case_id,
  src.alert_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.case_alert_link` AS src
WHERE NOT src._fivetran_deleted

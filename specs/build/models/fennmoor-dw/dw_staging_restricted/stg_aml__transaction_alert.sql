SELECT
  src.alert_id,
  src.party_id,
  src.scenario_code,
  src.alert_date,
  src.total_amount,
  src.status,
  src.assigned_to,
  src.closed_date,
  src.escalated_to_case,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.transaction_alert` AS src
WHERE NOT src._fivetran_deleted

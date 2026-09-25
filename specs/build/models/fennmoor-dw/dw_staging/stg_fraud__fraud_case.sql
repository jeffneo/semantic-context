SELECT
  src.case_id,
  src.opened_at,
  src.closed_at,
  src.case_type,
  src.status,
  src.cif_number,
  src.total_loss_amount,
  src.recovered_amount,
  src.confirmed_fraud,
  src.fraud_type,
  src.assigned_analyst,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.fraud_case` AS src
WHERE NOT src._fivetran_deleted

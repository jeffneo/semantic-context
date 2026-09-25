SELECT
  a.alert_id,
  a.alert_date,
  a.party_id,
  p.customer_key,
  a.scenario_code,
  a.total_amount,
  a.status,
  a.escalated_to_case
FROM `fennmoor-dw.dw_staging_restricted.stg_aml__transaction_alert` a
LEFT JOIN `fennmoor-dw.dw_compliance.dim_aml_party` p ON p.party_id = a.party_id

SELECT
  a.alert_id,
  DATE(a.alert_ts, 'America/Chicago') AS alert_date,
  c.customer_key,
  a.cif_number,
  a.entity_type,
  a.rule_id,
  a.model_score,
  a.channel,
  a.amount,
  a.disposition,
  l.case_id,
  COALESCE(fc.confirmed_fraud, FALSE) AS is_confirmed_fraud,
  fc.fraud_type,
  fc.total_loss_amount AS loss_amount
FROM `fennmoor-dw.dw_staging.stg_fraud__alert` a
LEFT JOIN `fennmoor-dw.dw_staging.stg_fraud__case_alert_link` l ON l.alert_id = a.alert_id
LEFT JOIN `fennmoor-dw.dw_staging.stg_fraud__fraud_case` fc ON fc.case_id = l.case_id
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = a.cif_number

SELECT
  s.*
FROM `fennmoor-dw.dw_risk.fct_fraud_alerts` AS s
WHERE s.fraud_type = 'P2P_SCAM' AND s.alert_date >= '2026-01-01'

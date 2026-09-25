SELECT
  s.* EXCEPT (card_txn_count_90d, churn_risk_band, closure_calls_90d, contacts_90d, web_sessions_30d)
FROM `fennmoor-dw.dw_customer.customer_360` AS s
WHERE s.segment IN ('affluent', 'private')

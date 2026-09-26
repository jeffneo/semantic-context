-- Q07: share of fraud alerts confirmed as fraud, by channel. An alert without a case is not confirmed.
SELECT channel, COUNT(*) AS alerts, COUNTIF(is_confirmed_fraud) AS confirmed,
       ROUND(SAFE_DIVIDE(COUNTIF(is_confirmed_fraud), COUNT(*)), 4) AS confirmed_share
FROM `fennmoor-dw.dw_risk.fct_fraud_alerts`
GROUP BY channel
ORDER BY alerts DESC

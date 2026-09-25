SELECT
  s.* EXCEPT (churn_probability),
  s.churn_probability AS churn_risk
FROM `fennmoor-analytics.sbx_customer_analytics.customer_360_v2` AS s

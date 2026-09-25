SELECT
  c.segment,
  COUNT(*) AS customers,
  AVG(c.total_deposit_balance) AS avg_balance,
  AVG(c.churn_probability) AS avg_churn
FROM `fennmoor-dw.dw_customer.customer_360` c
GROUP BY ALL

-- Q02: churn risk of customers with $50,000+ in deposits, from customer_360 (the current v3 score, as of
-- its latest score date), not the retired v2 score or a sandbox copy.
SELECT segment, COUNT(*) AS customers, ROUND(AVG(churn_probability), 3) AS avg_churn_probability,
       COUNTIF(churn_probability >= 0.6) AS high_risk
FROM `fennmoor-dw.dw_customer.customer_360`
WHERE total_deposit_balance >= 50000
GROUP BY segment
ORDER BY customers DESC

-- compare: cif_number, churn_probability
-- Q02, the other reading: the high-balance customers themselves, each with their current churn score,
-- rather than a summary by segment. "High-balance" is $50,000+ in deposits, production's own threshold
-- (reverse_etl.aud_high_value_churn_risk); the score is the current v3 score in customer_360.
SELECT cif_number, segment, total_deposit_balance, churn_probability
FROM `fennmoor-dw.dw_customer.customer_360`
WHERE total_deposit_balance >= 50000
ORDER BY total_deposit_balance DESC

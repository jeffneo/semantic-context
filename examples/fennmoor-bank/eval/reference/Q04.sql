-- Q04: card spend by merchant category and customer segment, last quarter (2026 Q2), purchases only,
-- filtered on the partition column.
SELECT c.segment, t.mcc_category_group, ROUND(SUM(t.amount), 2) AS spend, COUNT(*) AS purchases
FROM `fennmoor-dw.dw_core.fct_card_transactions` t
JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.customer_key = t.customer_key
WHERE t.post_date BETWEEN '2026-04-01' AND '2026-06-30' AND t.is_purchase
GROUP BY 1, 2
ORDER BY 1, 3 DESC

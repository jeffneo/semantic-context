-- BigQuery, in the graph's table names. Customers in each state.
-- Run as risk: the warehouse's row access policy on dim_customer leaves two states.
SELECT state_code, COUNT(*) AS customers
FROM dw_core.dim_customer
GROUP BY state_code
ORDER BY customers DESC

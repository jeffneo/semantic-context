-- BigQuery, in the graph's table names. A reference query: customers in each segment.
SELECT segment, COUNT(*) AS customers
FROM dw_core.dim_customer
GROUP BY segment
ORDER BY customers DESC

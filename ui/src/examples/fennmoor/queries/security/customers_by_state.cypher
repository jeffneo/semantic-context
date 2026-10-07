// Database: the Virtual Graph (rows). The gateway adds its signature; each row is read live from BigQuery.
// Customers in each state. Run as risk: the warehouse's row access policy on dim_customer leaves two states.
MATCH (c:Customer)
RETURN c.state_code AS state, count(DISTINCT c.customer_key) AS customers
ORDER BY customers DESC

// Database: the Virtual Graph (rows). The gateway adds its signature; each row is read live from BigQuery.
// Ten customers, as rows of dim_customer.
MATCH (c:Customer)
RETURN c.customer_key AS customer_key, c.segment AS segment, c.state_code AS state
LIMIT 10

// Database: the Virtual Graph (rows). The gateway adds its signature; each row is read live from BigQuery.
// Names and email addresses of the affluent customers. Marketing has no right to the identifier columns: the warehouse refuses them.
MATCH (c:Customer {segment: 'affluent'})
RETURN c.customer_key AS customer_key, c.full_name AS full_name, c.primary_email AS email
LIMIT 10

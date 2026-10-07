// Database: the Virtual Graph (rows). The gateway adds its signature; each row is read live from BigQuery.
// A customer's neighbourhood, drawn: accounts held, and the product each offers.
MATCH p = (c:Customer)<-[:HELD_BY]-(a:Account)-[:OFFERS]->(pr:Product)
RETURN p LIMIT 25

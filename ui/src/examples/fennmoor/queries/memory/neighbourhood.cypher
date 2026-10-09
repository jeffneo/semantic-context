// Database: memory (what Virtual Graph reads fetched)
// The remembered customer's neighbourhood, drawn: the accounts held, and the product each offers.
MATCH p = (c:Customer {cif_number: $customer})<-[:HELD_BY]-(a:Account)-[:OFFERS]->(pr:Product)
RETURN p LIMIT 25

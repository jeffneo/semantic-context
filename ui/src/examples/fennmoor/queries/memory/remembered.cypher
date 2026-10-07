// Database: memory (what Virtual Graph reads fetched)
// Is this customer remembered? 0 until a recall fetches them.
MATCH (c:Customer {cif_number: '0001000033'})
RETURN count(c) AS remembered

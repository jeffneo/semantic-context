// Database: bigquery (the semantic layer)
// Each Variable (the real-world thing joined columns share) with every column that is one, and the table it is in.
MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table)
RETURN v.id AS id, v.name AS name, v.description AS description, t.id AS table, c.name AS column
ORDER BY id, table, column

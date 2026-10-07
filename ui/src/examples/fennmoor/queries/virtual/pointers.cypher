// Database: bigquery (the semantic layer)
// Each column the model made a relationship type: the type, its table, the column that points, and the Variable it holds.
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE c.graph_relationship IS NOT NULL
OPTIONAL MATCH (c)-[:IS]->(v:Variable)
RETURN c.graph_relationship AS type, t.id AS table, c.name AS column, v.name AS variable

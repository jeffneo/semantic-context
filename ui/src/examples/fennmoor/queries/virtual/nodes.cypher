// Database: bigquery (the semantic layer)
// Each table the Virtual Graph model made a node label: its label, its key column, and the Variable that column holds.
MATCH (t:Table) WHERE t.graph_label IS NOT NULL
OPTIONAL MATCH (t)-[:HAS_COLUMN]->(k:Column {graph_key: true})
OPTIONAL MATCH (k)-[:IS]->(v:Variable)
RETURN t.id AS table, t.graph_label AS label, k.name AS key, v.name AS variable

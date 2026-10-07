// Database: bigquery (the semantic layer)
// The paths the Virtual Graph model was derived from: a relationship type is a column that holds another node's key, and both are one Variable.
MATCH p = (s:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable)<-[:IS]-(k:Column {graph_key: true})<-[:HAS_COLUMN]-(e:Table)
WHERE c.graph_relationship IS NOT NULL AND s.graph_label IS NOT NULL AND e.graph_label IS NOT NULL AND e <> s
RETURN p

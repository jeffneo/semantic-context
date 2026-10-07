// Database: bigquery (the semantic layer)
// The same as a table: label, relationship type, label, and the evidence for it.
MATCH (a:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable)<-[:IS]-(k:Column {graph_key: true})<-[:HAS_COLUMN]-(b:Table)
WHERE c.graph_relationship IS NOT NULL AND b.graph_label IS NOT NULL AND a <> b
RETURN a.graph_label AS start, c.graph_relationship AS type, b.graph_label AS end,
       a.name + '.' + c.name AS column, v.name AS variable, v.size AS columns_in_variable, v.tables AS tables_in_variable,
       count{ (c)<-[:ON]-(j:JoinKey)-[:ON]->(k) WHERE j.confidence IN ['production', 'corroborated', 'single'] } AS direct_trusted_joins
ORDER BY start, type

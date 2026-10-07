// Database: bigquery (the semantic layer)
// Every catalog column with the level-1 group that holds it: itself or, when it is joined, its variable.
// `read` is whether any query referenced the table.
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog
OPTIONAL MATCH (c)-[:IS]->(v:Variable)
WITH t, coalesce(v, c) AS u
OPTIONAL MATCH (u)-[:IN_SEMANTIC]->(g:Semantic {level: 1})
RETURN t.id AS table, g.id AS group, EXISTS { (:QueryShape)-[:REFERENCES]->(t) } AS read

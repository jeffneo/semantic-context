// Database: bigquery (the semantic layer)
// Every Semantic node (level 3 the broad areas, 2 the areas, 1 the groups read together) with its name, what it is, its size and the one it sits under.
MATCH (s:Semantic)
OPTIONAL MATCH (s)-[:IN_SEMANTIC]->(p:Semantic)
RETURN s.id AS id, s.level AS level, s.name AS name, s.description AS description, s.tables AS tables, s.size AS size,
       s.stability AS stability, p.id AS parent
ORDER BY level DESC, tables DESC, id

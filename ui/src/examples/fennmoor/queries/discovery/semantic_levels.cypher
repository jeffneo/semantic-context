// Database: bigquery (the semantic layer)
// The groups at each level: the broad areas (3), the areas (2) and the groups of what is read together (1).
MATCH (s:Semantic)
RETURN s.level AS level, count(*) AS groups
ORDER BY level DESC

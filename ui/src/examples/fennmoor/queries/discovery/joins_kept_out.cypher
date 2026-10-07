// Database: bigquery (the semantic layer)
// Joins kept out of the variables: suspect (production keeps the two id spaces apart) or not identity-preserving. `confidence_reason` says why.
MATCH p = (ta:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)<-[:HAS_COLUMN]-(tb:Table)
WHERE (k.confidence = 'suspect' OR NOT k.identity) AND a.id < b.id
RETURN p

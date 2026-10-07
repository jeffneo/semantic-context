// Database: bigquery (the semantic layer)
// The joins that were not allowed to merge anything: two id spaces production keeps apart (suspect), and joins that relate things without
// identifying them (not identity-preserving). `why` says which.
MATCH (ta:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)<-[:HAS_COLUMN]-(tb:Table)
WHERE (k.confidence = 'suspect' OR NOT k.identity) AND a.id < b.id
RETURN ta.id + '.' + a.name AS a, tb.id + '.' + b.name AS b, k.confidence AS confidence, k.identity AS identity, k.confidence_reason AS why
ORDER BY confidence, a, b

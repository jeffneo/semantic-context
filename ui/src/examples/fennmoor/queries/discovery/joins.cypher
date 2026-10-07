// Database: bigquery (the semantic layer)
// The joins whose two columns are one variable, with the queries that made them: how much the join is trusted, by how many people, in how many query shapes and jobs.
MATCH (v:Variable)<-[:IS]-(a:Column)<-[:ON]-(k:JoinKey)-[:ON]->(b:Column)-[:IS]->(v) WHERE a.id < b.id
OPTIONAL MATCH (q:QueryShape)-[:USES_JOIN]->(k)
RETURN v.id AS variable, a.id AS a, b.id AS b, k.confidence AS confidence, k.people AS people, count(DISTINCT q) AS shapes, coalesce(sum(q.jobs), 0) AS jobs
ORDER BY variable, a, b

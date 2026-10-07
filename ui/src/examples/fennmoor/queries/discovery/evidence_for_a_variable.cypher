// Database: bigquery (the semantic layer)
// The evidence for one variable: each join predicate behind it ("a = b" some query ran), and the query shapes that ran it.
MATCH (v:Variable {name: 'Account Key'})<-[:IS]-(c:Column)
MATCH p = (c)<-[:ON]-(k:JoinKey)-[:ON]->(:Column)
OPTIONAL MATCH q = (k)<-[:USES_JOIN]-(:QueryShape)
RETURN p, q, v

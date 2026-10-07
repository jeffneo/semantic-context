// Database: bigquery (the semantic layer)
// From meaning down to data: one group, the variables and columns in it, the tables they sit in, and the queries that read them.
MATCH (:Table {name: 'cc_site_scorecard_2026'})-[:HAS_COLUMN]->(:Column)-[:IS]->{0,1}()-[:IN_SEMANTIC]->(g:Semantic {level: 1})
WITH g, count(*) AS n ORDER BY n DESC LIMIT 1
MATCH p = (:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(g)
WHERE u:Variable OR u:Unjoined
OPTIONAL MATCH q = (:Principal)-[:RAN]->(:QueryShape)-[:READS]->(c)
RETURN p, q

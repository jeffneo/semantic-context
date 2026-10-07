// Database: bigquery (the semantic layer)
// The five groups nearest to the one that holds the contact-center site scorecard, by embedding (the vector index), with the area each is in.
MATCH (:Table {name: 'cc_site_scorecard_2026'})-[:HAS_COLUMN]->(:Column)-[:IS]->{0,1}()-[:IN_SEMANTIC]->(s:Semantic {level: 1})
WITH s, count(*) AS n ORDER BY n DESC LIMIT 1
CALL db.index.vector.queryNodes('semantic_embedding', 6, s.embedding) YIELD node, score
WITH s, node, score WHERE node <> s
OPTIONAL MATCH p = (node)-[:IN_SEMANTIC]->(:Semantic)
RETURN s, node, score, p

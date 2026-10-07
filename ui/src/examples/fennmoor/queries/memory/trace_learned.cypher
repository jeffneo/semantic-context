// Database: memory
// Parameter: $id, a conversation's id.
// What was learned in each message: the facts (and what each replaced) and the things it named, with who said so.
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(m:Message)<-[:FROM]-(f:Fact)
OPTIONAL MATCH (f)-[sup:SUPERSEDES]->(old:Fact)
OPTIONAL MATCH (f)-[:ABOUT]->(a)
OPTIONAL MATCH (f)-[:MENTIONS]->(e:Entity)
RETURN m.id AS message, f.predicate AS predicate, f.value AS value, f.origin AS origin, head(labels(a)) AS about, e.name AS entity, e.type AS entity_type,
       sup.because AS because, old.value AS replaced
ORDER BY m.seq, f.recorded_at

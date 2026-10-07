// Database: memory
// Parameter: $id, a conversation's id.
// Its messages in order, who said each, and the task each user message started.
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(m:Message)
OPTIONAL MATCH (t:Task)-[:FROM]->(m)
RETURN m.id AS id, m.seq AS seq, m.role AS role, m.text AS text, t.id AS task
ORDER BY m.seq

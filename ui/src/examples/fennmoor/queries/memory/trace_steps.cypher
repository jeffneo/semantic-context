// Database: memory
// Parameter: $id, a conversation's id.
// The tool calls of each of its tasks, in order: the tool, what it was asked, what came back, how long it took, and the layer's tables and computations it read.
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(t:Task)<-[:PART_OF]-(s:Step)
OPTIONAL MATCH (s)-[:READ]->(r)
WITH t, s, collect(DISTINCT {label: head(labels(r)), name: coalesce(r.name, r.label)}) AS reads
RETURN t.id AS task, s.seq AS seq, s.tool AS tool, s.arguments AS arguments, s.result AS result, s.status AS status, s.duration_ms AS ms, reads
ORDER BY t.recorded_at, s.seq

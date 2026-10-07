// Database: memory (what Virtual Graph reads fetched, and what agents did)
// An audit question: which agents read a table of the warehouse, for whom, and what did they ask.
// Change the table to audit another.
MATCH (t:Table)<-[:READ]-(s:Step)-[:PART_OF]->(task:Task)-[:PART_OF]->(c:Conversation)
WHERE t.name = 'fct_card_transactions'
RETURN c.title AS conversation, c.owner AS acting_for, s.tool AS tool, left(task.request, 80) AS request, s.status AS status, s.duration_ms AS ms
ORDER BY c.recorded_at DESC

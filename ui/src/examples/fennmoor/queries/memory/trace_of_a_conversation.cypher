// Database: memory (what Virtual Graph reads fetched, and what agents did)
// A conversation, whole: its messages, the task each request started, the tool calls of each task, the facts learned from its messages, and each decision with what it rests on.
// Its latest recording by title; change the title to read another.
MATCH (c:Conversation {title: 'Card offer for customer 8322097816940277129'})
WITH c ORDER BY c.recorded_at DESC LIMIT 1
CALL {
  WITH c
  MATCH p = (c)<-[:PART_OF*1..2]-() RETURN p
  UNION
  WITH c
  MATCH p = (c)<-[:PART_OF]-(:Task)<-[:PART_OF]-(:Decision)-[:BASED_ON]->() RETURN p
  UNION
  WITH c
  MATCH p = (c)<-[:PART_OF]-(:Message)<-[:FROM]-(:Fact) RETURN p
}
RETURN p

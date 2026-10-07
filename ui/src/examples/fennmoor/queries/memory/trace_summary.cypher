// Database: memory (what Virtual Graph reads fetched, and what agents did)
// Every conversation the memory holds, who it acted for, and how much of it there is: messages, tasks, tool calls, and decisions.
MATCH (c:Conversation)
RETURN c.title AS conversation, c.owner AS acting_for, c.started_at AS started,
       count { (c)<-[:PART_OF]-(:Message) } AS messages,
       count { (c)<-[:PART_OF]-(:Task) } AS tasks,
       count { (c)<-[:PART_OF]-(:Task)<-[:PART_OF]-(:Step) } AS tool_calls,
       count { (c)<-[:PART_OF]-(:Task)<-[:PART_OF]-(:Decision) } AS decisions
ORDER BY started DESC

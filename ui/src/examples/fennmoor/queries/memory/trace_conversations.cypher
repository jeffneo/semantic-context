// Database: memory (what Virtual Graph reads fetched, and what agents did)
// Parameter: $titles, the conversations to show, by title.
// Each one's latest recording: who it acted for, when it began, and how much it holds.
UNWIND $titles AS title
MATCH (c:Conversation {title: title})
WITH title, c ORDER BY c.recorded_at DESC
WITH title, head(collect(c)) AS c
RETURN c.id AS id, c.title AS title, c.owner AS owner, c.started_at AS started_at

// Database: memory
// Parameter: $id, a conversation's id.
// Each decision: the choice and why, what else was weighed, and what it rests on: the facts and the tool calls it was based on, and how it turned out.
MATCH (c:Conversation {id: $id})<-[:PART_OF]-(t:Task)<-[:PART_OF]-(d:Decision)
OPTIONAL MATCH (d)-[:BASED_ON]->(b)
OPTIONAL MATCH (o:Fact)-[:ABOUT]->(d)
WITH t, d, collect(DISTINCT {label: head(labels(b)), what: coalesce(b.predicate, b.tool), value: b.value}) AS based_on, collect(DISTINCT o.value) AS outcome
RETURN t.id AS task, d.choice AS choice, d.rationale AS rationale, d.alternatives AS alternatives, based_on, outcome

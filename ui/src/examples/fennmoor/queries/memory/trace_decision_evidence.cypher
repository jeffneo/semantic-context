// Database: memory (what Virtual Graph reads fetched, and what agents did)
// Why an agent decided what it did: each decision, who it is about, the facts and tool calls it was based on, the tables and computations those read, and how it turned out.
MATCH (d:Decision)-[based:BASED_ON]->(basis)
OPTIONAL MATCH (d)-[:ABOUT]->(subject)
OPTIONAL MATCH (basis)-[read:READ]->(layer)
OPTIONAL MATCH (outcome:Fact)-[:ABOUT]->(d)
RETURN d, based, basis, subject, read, layer, outcome

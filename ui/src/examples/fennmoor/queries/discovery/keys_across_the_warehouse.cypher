// Database: bigquery (the semantic layer)
// The keys the whole warehouse joins on: the variables that span five tables or more, with their columns and tables.
MATCH p = (v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(:Table)
WHERE v.tables >= 5
RETURN p

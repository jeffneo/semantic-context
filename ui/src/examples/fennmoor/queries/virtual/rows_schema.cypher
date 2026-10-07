// Database: fennmoor (the composite), reaching the Virtual Graph's `rows`
// The Virtual Graph's schema: its node labels and relationship types. The graph stores nothing; this is the model it translates Cypher with.
USE fennmoor.rows
CALL db.schema.visualization()

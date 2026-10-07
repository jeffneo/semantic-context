// Database: bigquery (the semantic layer)
// The map of the business: each area (level 2) under the broad area (level 3) it belongs to.
MATCH p = (:Semantic {level: 2})-[:IN_SEMANTIC]->(:Semantic {level: 3})
RETURN p

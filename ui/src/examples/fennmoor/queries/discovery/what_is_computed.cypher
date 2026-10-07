// Database: bigquery (the semantic layer)
// What the business computes again and again, written as its queries write it: the five most-run measures.
MATCH (c:Computation {kind: 'measure', trusted: true})
RETURN c.name AS name, c.expression AS expression, c.jobs AS jobs
ORDER BY jobs DESC LIMIT 5

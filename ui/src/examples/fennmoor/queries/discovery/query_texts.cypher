// Database: bigquery (the semantic layer)
// The distinct query texts the log held (a view's definition has none).
MATCH (q:QueryShape {origin: 'log'}) RETURN sum(q.texts)

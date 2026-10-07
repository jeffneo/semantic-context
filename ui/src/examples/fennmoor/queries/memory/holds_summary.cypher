// Database: bigquery (the semantic layer)
// How often each table is written, as the log shows it: the days it was written on in 90, and whether it is frozen. This sets how long a fact of it holds.
MATCH (t:Table) WHERE t.in_catalog AND t.write_days IS NOT NULL
RETURN t.id AS table, size(t.write_days) AS days_written, t.frozen AS frozen
ORDER BY days_written DESC, table LIMIT 20

// Database: bigquery (the semantic layer)
// Each catalog table's write days in the log, and whether it is frozen: what sets how long a fact of it holds in memory (qlsc.memory.cadence_days).
MATCH (t:Table) WHERE t.in_catalog
RETURN t.id AS id, t.write_days AS write_days, t.frozen AS frozen
ORDER BY id

// Database: memory (what Virtual Graph reads fetched)
// Where a remembered customer came from: who fetched it, when, and until when it holds (set by how often the table is written).
MATCH (c:Customer {cif_number: $customer})
RETURN c.source AS source, c.fetched_by AS fetched_by, c.fetched_at AS fetched_at, c.holds_until AS holds_until

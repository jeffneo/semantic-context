// Database: memory (what Virtual Graph reads fetched)
// Parameter: $key, a Customer's key.
// What a remembered node carries about where it came from: when it was fetched, until when it holds, by whom and with which read.
// Its name, email and every other column are left behind.
MATCH (c:Customer {customer_key: toInteger($key)})
RETURN c.fetched_at AS fetched_at, c.holds_until AS holds_until, c.fetched_by AS fetched_by, c.fetched_with AS fetched_with

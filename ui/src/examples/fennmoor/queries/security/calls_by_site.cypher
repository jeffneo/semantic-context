// Database: the Virtual Graph (rows). The gateway adds its signature; each row is read live from BigQuery.
// Calls handled at each contact-center site. Run as marketing: the warehouse refuses the table. Untick "Sign it" to see the pass-through refuse an unsigned query.
MATCH (c:Call)-[:PROCESSED_AT]->(s:ContactCenterSite)
RETURN s.site_name AS site, count(c) AS calls
ORDER BY calls DESC

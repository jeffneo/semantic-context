# designed/

Designed models: what someone decided the data means. qlsc never builds the semantic layer from these
(the query log is the ground truth); `qlsc align` links them to what the log produced and reports where
design and usage agree and disagree (`work/ALIGNMENT.md`). The config names them (`designed:`).

| File | What |
|---|---|
| `catalog.json` | A data-catalog export (glossary terms bound to columns, table and column descriptions, certification), in the shape a Dataplex, Collibra or Alation export would have. **Synthetic**: generated from the spec by `generate/make_catalog.py` with deliberate gaps, stale certified tables, orphan terms and three wrong bindings |
| `ontology.ttl` | A small retail-banking ontology (58 OWL classes, labels, SKOS definitions, subclass hierarchy), FIBO-inspired, written by hand. Imported as RDF with [rdflib-neo4j](https://github.com/neo4j-labs/rdflib-neo4j): classes become `(:Resource:Class {uri, label, definition})`, the hierarchy `subClassOf` |

For a real estate, replace these with the organization's own catalog export and ontology (for an
insurer, ACORD or its enterprise data model).

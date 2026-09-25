// =====================================================================================
// Demo queries: visualizing the semantic layer built from the query log.
// Database: bigquery      (in Neo4j Browser:  :use bigquery )
// Each query returns nodes and relationships, so Browser / Explore draws it as a graph.
// Sizes are noted so you know what to expect on screen. Table ids are
// project.dataset.table (e.g. fennmoor-dw.dw_contact_center.fct_calls), and t.name is the table name.
// =====================================================================================


// -------------------------------------------------------------------------------------
// 1. THE PHYSICAL LAYER: what the query log and the catalog show directly
// -------------------------------------------------------------------------------------

// 1.1 The estate: projects, datasets, tables                              (~370 nodes)
MATCH p = (:Project)<-[:IN_PROJECT]-(:Dataset)<-[:IN_DATASET]-(t:Table)
WHERE t.in_catalog
RETURN p;

// 1.2 Table lineage across the warehouse: raw -> staging -> marts -> reports (~290 nodes)
//     A statement read the one table and wrote the other.
MATCH p = (a:Table)-[:DERIVED_FROM]->(b:Table)
WHERE a.in_catalog AND b.in_catalog
RETURN p;

// 1.3 Where one table's data comes from, all the way to the raw feeds      (~50 nodes)
//     fct_contacts_all unions the new Genesys calls with the legacy Avaya records.
MATCH p = (:Table {name: 'fct_contacts_all'})-[:DERIVED_FROM*1..6]->(:Table)
RETURN p;

// 1.4 Column lineage: how one number is computed, back to the source columns (~8 nodes)
MATCH p = (:Table {name: 'fct_cc_site_cost_monthly'})-[:HAS_COLUMN]->(:Column {name: 'total_expense'})
          <-[:FLOWS*1..4]-(:Column)
RETURN p;

// 1.5 Who uses a table: people, dashboards and pipelines, and the queries they run (~120 nodes)
MATCH p = (:Principal)-[:RAN]->(:QueryShape)-[:REFERENCES]->(:Table {name: 'fct_calls'})
RETURN p;

// 1.6 One query shape in full: who ran it, what it reads, filters, joins and writes (~20 nodes)
//     The most-run query reading the site-cost table.
MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(:Table {name: 'fct_cc_site_cost_monthly'})
WITH s ORDER BY s.jobs DESC LIMIT 1
MATCH p = (s)-[:READS|FILTERS|WRITES|REFERENCES]->()
OPTIONAL MATCH r = (:Principal)-[:RAN]->(s)
OPTIONAL MATCH j = (s)-[:USES_JOIN]->(:JoinKey)-[:ON]->(:Column)
RETURN p, r, j;


// -------------------------------------------------------------------------------------
// 2. THE JOIN-VARIABLE STRUCTURE: columns the business joins are one Variable
// -------------------------------------------------------------------------------------

// 2.1 Every variable, its columns and their tables                    (~360 nodes)
MATCH p = (:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(:Table)
RETURN p;

// 2.2 The keys the whole warehouse joins on: variables spanning 5+ tables (~150 nodes)
MATCH p = (v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(:Table)
WHERE v.tables >= 5
RETURN p;

// 2.3 The evidence for one variable: the join predicates behind it          (~25 nodes)
//     Each JoinKey is an "a = b" some query ran, and WCC over them made the variable.
MATCH (v:Variable {name: 'Account Key'})<-[:IS]-(c:Column)
MATCH p = (c)<-[:ON]-(k:JoinKey)-[:ON]->(:Column)
OPTIONAL MATCH q = (k)<-[:USES_JOIN]-(:QueryShape)
RETURN p, q, v, [(c)-[i:IS]->(v) | i] AS is;

// 2.4 Table-to-table network, drawn through the variables they share       (~120 tables, ~660 links)
//     A virtual relationship per table pair, labelled with the shared variables (APOC).
MATCH (a:Table)-[:HAS_COLUMN]->(:Column)-[:IS]->(v:Variable)<-[:IS]-(:Column)<-[:HAS_COLUMN]-(b:Table)
WHERE a.id < b.id AND a.in_catalog AND b.in_catalog
WITH a, b, collect(DISTINCT v.name) AS via
RETURN a, b, apoc.create.vRelationship(a, 'SHARES', {via: via, variables: size(via)}, b) AS shares;

// 2.5 Variables whose columns look like different things (joined by mistake) (~10 nodes)
MATCH p = (v:Variable {coherent: false})<-[:IS]-(:Column)<-[:HAS_COLUMN]-(:Table)
RETURN p;


// -------------------------------------------------------------------------------------
// 3. THE SEMANTIC LAYER: communities of usage, then of meaning
// -------------------------------------------------------------------------------------

// 3.1 The whole hierarchy: every Semantic node and what it sits under       (~130 nodes)
//     Level 1: groups of what the business reads together, levels 2 and 3 the broader areas.
MATCH p = (:Semantic)-[:IN_SEMANTIC]->(:Semantic)
RETURN p;

// 3.2 The top two levels only: the map of the business                      (~21 nodes)
MATCH p = (:Semantic {level: 2})-[:IN_SEMANTIC]->(:Semantic {level: 3})
RETURN p;

// 3.3 One area, top to bottom: area -> groups -> variables and columns -> tables (~340 nodes, dense)
MATCH p = (:Table)-[:HAS_COLUMN]->(:Column)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(:Semantic)
          -[:IN_SEMANTIC]->(:Semantic {name: 'Card Products And Transactions'})
WHERE u:Variable OR u:Unjoined
RETURN p;

// 3.4 The similarity graph the next level was built from (level 1)        (~110 nodes)
//     K_SIM links each group to its 5 best matches (score = usage + meaning).
MATCH p = (:Semantic {level: 1})-[:K_SIM]->(:Semantic {level: 1})
RETURN p;

// 3.5 Nearest neighbours of one group by embedding (vector index)          (~10 nodes)
MATCH (s:Semantic {name: 'Contact Center Site Monthly Performance'})
CALL db.index.vector.queryNodes('semantic_embedding', 8, s.embedding) YIELD node, score
WITH s, node, score WHERE node <> s
OPTIONAL MATCH p = (node)-[:IN_SEMANTIC]->(:Semantic)
RETURN s, node, score, p;

// 3.6 From meaning down to data: one group, its members and the tables they sit in,
//     plus the queries that read them                                       (~35 nodes)
MATCH (g:Semantic {level: 1, name: 'Contact Center Site Monthly Performance'})
MATCH p = (:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->{0,1}(u)-[:IN_SEMANTIC]->(g)
WHERE u:Variable OR u:Unjoined
OPTIONAL MATCH q = (:Principal)-[:RAN]->(:QueryShape)-[:READS]->(c)
RETURN p, q;

# qlsc: a semantic layer from the query log

qlsc builds a semantic layer for a data warehouse from **how the business actually uses it**: the query
log. A Neo4j graph records which columns queries join, read together and derive from one another.
Columns joined to each other become one Variable; communities of what is read together become business
areas, level above level; an LLM names them. A question in plain English then walks down from those
areas to the tables and columns that answer it.

It also finds what the business **computes**: every measure, derived dimension and population the log's
queries compute, as Computation nodes, named and linked to the columns they read. Those publish as an
**Open Knowledge Format** bundle (OKF v0.2), for any agent or catalog to read.

The semantic layer also writes a **Neo4j Virtual Graph** model of the warehouse, so the warehouse's
rows can be queried as a graph without copying them. Its nodes and relationships come from the log's
trusted joins, and the joins the log shows to be suspect are left out. A **composite database** puts
the two side by side: one Cypher query reads what the layer knows about a table (its business area,
its Variables, which column a relationship comes from) together with the live rows from BigQuery.

The premise: ERDs, catalogs and ontologies are someone's design; the query log is what the business
runs. So usage is the ground truth, and designed models are aligned afterwards, never used as inputs
([docs/design.md](docs/design.md)).

```mermaid
flowchart TD
    L[warehouse: query log + catalog] --> P[parse: SQL service, sqlglot]
    P --> B["bottom layer (Neo4j)<br/>Project, Dataset, Table, Column,<br/>Principal, QueryShape, JoinKey"]
    B --> V["Variables<br/>WCC over trusted joins"]
    V --> S1["Semantic level 1<br/>Leiden over co-reads + lineage"]
    B --> CP["Computations<br/>measures, dimensions, populations"]
    CP --> OKF["okf: an Open Knowledge Format bundle"]
    CP --> Q
    S1 --> SH["Semantic levels 2..n<br/>embed, K_SIM kNN, Leiden per level"]
    SH --> A["align: catalog + ontology<br/>Concept, MEANS, the diff"]
    SH --> Q["ask: question -> vector search -><br/>walk down -> tables -> SQL or Cypher -> answer"]
    SH --> VG["virtualize: a Virtual Graph model<br/>from trusted joins, views in the warehouse"]
    VG --> C["composite database: the semantic layer<br/>and the warehouse's rows, in one Cypher query"]
    SH --> C
```

## Try it

The worked example is **Fennmoor Bank**, a synthetic US retail bank on BigQuery with a 90-day query log
of 315,729 jobs, planted traps, a data catalog and an ontology. The tutorial walks through it end to
end: [examples/fennmoor-bank/](examples/fennmoor-bank/README.md).

What it finds there: 50 variables built only from trusted joins; semantic levels of 109 → 16 → 5
groups (median group stability 0.95); every join and lineage edge in the answer key recovered; all
three planted wrong catalog bindings surfaced by the alignment.

## Use it

Prerequisites: Docker; [uv](https://docs.astral.sh/uv/); access to the warehouse's query log and
catalog (BigQuery today: `gcloud`); an Anthropic API key and an Azure OpenAI `text-embedding-3-large`
deployment; Neo4j Enterprise and GDS license files (not included).

```bash
cp .env.example .env                  # passwords, keys, and QLSC_CONFIG: your estate's config file
docker compose up -d neo4j parser     # add --profile nes for Enterprise Studio
uv sync
```

Write a config for your estate, following
[examples/fennmoor-bank/estate.yaml](examples/fennmoor-bank/estate.yaml): the warehouse connector and
where its log is, how to normalize volatile table names, the Neo4j database, and optionally a catalog
export and an ontology. Then:

```bash
uv run qlsc extract                   # the aggregated log and the catalog snapshot, from the warehouse
uv run qlsc build                     # parse, load, variables, computations, cluster, hierarchy, align
uv run qlsc ask "How many customers use the mobile app each week?"   # the router's query, dry-run
uv run qlsc ask --run "..."           # and run it: the answer, billed up to a cap
uv run qlsc ask --sql --run "..."     # the SQL route only; --cypher: Cypher over the virtual graph only
uv run qlsc okf                       # the Computations as an OKF bundle, in <work>/okf
```

Each stage also runs on its own (`uv run qlsc --help`). A full LLM naming pass costs under $0.50 with
Claude Haiku 4.5, and every call is cached by its request, so rebuilds are free and reproduce the graph
exactly.

## How well `ask` answers

Three answer keys in the Fennmoor example, each scored on the answer's rows, not on the SQL. With the
compiler (`navigate.writer: compiled`) and Sonnet 5.5 writing the requests (2026-09-28):

| Answer key | SQL route | Cypher route (virtual graph) | Routed (`ask`'s default) |
|---|---|---|---|
| 10 gold questions, hand-written references | 6 | 3 (it declines 6 whose data isn't in the virtual graph) | 6 |
| 176 questions written from the log's own queries, each with its query as the reference | 133 (76%) | 38 | 133 |
| 10 graph-shaped questions: neighbourhoods, several hops, shared neighbours | 5 | 8 | 8 |

The free writer with Sonnet 5, before the compiler: 7, 129 and 5 on the SQL route; 3, 41 and 7 on
Cypher.
- **The compiler** writes 88% of the SQL answers deterministically (154 of 176), 79% of them right. The
  LLM fills a typed request; code writes the joins and the definitions.
- **The router** takes compiled SQL when the question compiles, otherwise free Cypher when it answers,
  otherwise free SQL. It scores the better route on each answer key.

- **Aggregate questions:** SQL is ahead, and Cypher over the virtual graph adds a second translation
  step and no reach.
- **Relationship questions:** Cypher is ahead, because the virtual graph's relationships are the trusted
  joins.
- **How the Cypher route is checked:**
  - Virtual Graph's subset is linted before `EXPLAIN`.
  - Relationship directions and every label, type and property are checked against the model.
  - The writer declines rather than guess.
  - Answers are streamed and capped.

The evaluations, and what moved each number, are in
[plans/2026-09-26-accuracy.md](plans/2026-09-26-accuracy.md), [the compiler plan](plans/2026-09-28-compiler.md)
and [its second step](plans/2026-09-28-compiler-2.md).

## What the business computes: Computations and OKF

`qlsc computations` reads every successful query in the log with the parser, and in each query scope
over physical tables finds three kinds of Computation:
- **measures**, aggregates with the filters that come with them: card purchase spend is
  `SUM(amount)` over `is_purchase`;
- **derived dimensions**, such as a week from a call date, or a tenure band from months;
- **populations**, filters the business applies together, such as affluent and private customers.

Each is written over base columns, so the same computation in two queries is one Computation. A filter
whose value changes from run to run is a question's parameter, not part of the definition, and is left
out. Haiku names each from its expression and the names queries give it. Health checks (one ungrouped
row of aggregates) are flagged, and equivalents over the same tables are merged.

On the Fennmoor example this finds 1,182 Computations, of which 614 are business ones.

`qlsc okf` writes them as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
bundle:
- each Computation is an `Attested Computation` concept, filed under its business area, with an
  `index.md` per area;
- each table it reads is a `BigQuery Table` concept, with its schema, joins and Computations;
- provenance (the queries that compute it, their runs, who ran them) and lifecycle (`stable` if
  production computes it, `draft` if only people do) come from the log.

`qlsc ask` can give the closest Computations to the query writer as the business's definitions
(`navigate.computations`). It can also break a question into its measures, groupings, filters and
entities and navigate from each (`navigate.anchors: parts`). Both are off by default while they're
being measured ([plans/2026-09-26-accuracy.md](plans/2026-09-26-accuracy.md)).

## The warehouse as a graph: Virtual Graph and the composite database

`qlsc virtualize` turns the semantic layer into a model for
[Neo4j Virtual Graph](https://neo4j.com/docs/virtual-graph/) (preview). Virtual Graph answers Cypher by
translating it to SQL for the warehouse, so there's no copy of the data to keep in sync.
- **Nodes:** each is a table that a Variable's trusted joins converge on, or that production's pipelines
  MERGE on.
- **Relationships:** each is a column holding another node's key.
- **Names:** from the LLM.
- **Output:** one view per node table, in a dataset of its own, and a report of the evidence for every
  choice.

A composite database, `fennmoor`, on the Virtual Graph instance has two constituents:
- `fennmoor.semantic`: the semantic layer;
- `fennmoor.rows`: the virtual graph.

So a query can put what the layer knows beside the rows it describes:

```cypher
CALL () {                                   // the semantic layer: where this relationship comes from
  USE fennmoor.semantic
  MATCH (t:Table {graph_label: 'Call'})-[:HAS_COLUMN]->(c:Column {graph_relationship: 'SERVICED_AT'}),
        (c)-[:IS]->(v:Variable)-[:IN_SEMANTIC]->(g:Semantic)
  RETURN g.name AS business_area, v.name AS variable, t.name + '.' + c.name AS column
}
CALL () {                                   // the warehouse: live rows, through Virtual Graph
  USE fennmoor.rows
  MATCH (call:Call)-[:SERVICED_AT]->(s:ContactCenterSite)
  WHERE call.is_account_closure_call = true
  RETURN s.site_name AS site, count(call) AS closure_calls
}
RETURN business_area, variable, column, site, closure_calls ORDER BY closure_calls DESC
```

On the Fennmoor example this returns three rows in about 3 seconds, one per site, each showing:
- the business area (Contact Center Call Operations);
- the Variable (Contact Center Site);
- the column the relationship comes from (`fct_calls.site_id`);
- that site's closure calls since the Genesys cutover (October 2025), counted in BigQuery (3,005 at
  Tulsa, 2,548 at Manila, 1,838 at Spokane).

```bash
uv run qlsc virtualize                          # the model, the views, and MODEL.md, in the work directory
docker compose --profile vg up -d neo4j-vg      # Virtual Graph on bolt 7692, Browser on 7478
```

Setup, credentials and the composite's aliases: [docker/nvg/README.md](docker/nvg/README.md).

Virtual Graph is in preview, and three limits apply today:
- **Remote aliases only.** Both constituents are remote aliases, so both Neo4j instances serve bolt
  TLS ([docker/tls/README.md](docker/tls/README.md)). A local alias to the virtual graph fails silently.
- **No values across constituents.** A subquery can't pass a value from the semantic layer into the
  virtual graph; send it as a parameter on a second query instead.
- **A Cypher subset.** Virtual Graph has no `OPTIONAL MATCH` and no variable-length paths.

`qlsc ask --cypher` uses the virtual graph as a second route to an answer. The semantic trace is
the same, and it names the labels to query: the cohort's tables that are labels in the virtual graph,
plus one hop around them.

The findings are in [plans/2026-09-26-virtual-graph-spike.md](plans/2026-09-26-virtual-graph-spike.md).

## What an agent looked up, kept: memory

`qlsc recall <label> <key>` returns an entity's context: the node, its relationships and their
dimensions. It reads memory while the context holds, and fetches it from the virtual graph otherwise
([plan](plans/2026-09-27-agentic-memory.md)).
- **Where memory lives:** a `memory` database beside the semantic layer, joined to the composite as
  `fennmoor.memory`. It uses the virtual graph's labels and keys, with a `source` on each node, so the
  same Cypher runs on either.
- **Provenance:** every fact records when it was fetched, until when it holds (its table's write
  cadence in the log), by whom, with which read, and a link to a stub of the layer's Table.

```bash
uv run qlsc recall Customer cif_number=0001000025    # first time: 15 reads from BigQuery, ~4 s
uv run qlsc recall Customer cif_number=0001000025    # again: from memory, ~0.05 s
```

Over 20 customers (`eval/memory.py`), every context read back from memory was exactly the one fetched.
Six context questions gave the same rows on memory as on the virtual graph, 110 of 110, in 6 ms against
1.4 s. A stale fact is never read.

## Who may see what: the entitlement gateway

`qlsc ask --as <principal>` answers on a principal's behalf, from only what the warehouse lets them read
([plan](plans/2026-09-27-entitlements.md)). The warehouse stays the rulebook: the gateway asks BigQuery, as
the principal, which tables they may read, which columns their policy tags hide, and which tables filter
rows per reader.
- **Navigation shows only what they may read:**
  - the cohort and its columns;
  - joins and Computations;
  - examples whose every table and column they read, with who ran them as a kind, not a name;
  - never a tagged column's values.

  A group they can only partly read is shown without its name.
- **SQL runs as them,** so BigQuery enforces the tables, columns and rows itself.
- **Cypher over the virtual graph runs as them too.** The gateway signs each query for its principal. A
  JDBC driver in Virtual Graph's JVM (`vg-passthrough/`, [plan](plans/2026-09-28-jdbc-passthrough.md))
  verifies the signature and runs the SQL as that principal. An unsigned query, from anyone who reaches
  the virtual graph directly, is refused. Build it with `vg-passthrough/build.sh` before starting
  `neo4j-vg`.

The example's three test principals (marketing, risk and contact-center service accounts) are set up by
`examples/fennmoor-bank/entitlements/setup.py`. `eval/entitlements.py` checks the gateway with the
warehouse as the oracle. Over 60 questions it finds no leaks and no rows a principal may not read. Every
Cypher answer ran as its principal, by BigQuery's job log.

## Repository

| Path | What |
|---|---|
| `src/qlsc/` | The pipeline, one module per stage, and the `qlsc` command |
| `src/qlsc/defaults.yaml` | Every model and method parameter, in one place |
| `src/qlsc/warehouse/` | Warehouse connectors: the only code that talks to a warehouse (BigQuery) |
| `parser/` | The SQL parse service (sqlglot, compiled), one image for docker-compose, Cloud Run or Lambda, with golden tests |
| `prompts/` | Every LLM prompt, one file each ([prompts/README.md](prompts/README.md)) |
| `docs/design.md` | The principle, the graph model, the method, the parameters and their sensitivity |
| `examples/fennmoor-bank/` | The worked example: the bank's spec, its generators, designed models, evaluations, demo queries |
| `tests/` | `uv run pytest`: the tool/example boundary, prompts, config, the method's pure parts, the demo queries |
| `plans/` | Agreed plans for work in progress ([plans/README.md](plans/README.md)) |
| `CLAUDE.md` | Standing context for AI coding agents: principles, conventions, commands, safety rules |
| `vg-passthrough/` | The JDBC pass-through: Virtual Graph reads BigQuery as each query's principal (Java, JDK only; `build.sh`) |
| `docker/`, `docker-compose.yml` | Neo4j Enterprise with GDS and APOC, the parse service, optionally Enterprise Studio and a Virtual Graph instance (`--profile vg`) |

To add a warehouse, subclass `Warehouse` in `src/qlsc/warehouse/` and list it in `CONNECTORS`; the
parser resolves BigQuery SQL only so far.

# Improving the query-log semantic-layer demo

Assessment and plan, based on the restored `querylog` graph
(10,529 nodes / 71,316 relationships, restored from the previous project's backup in `old/`, which is not in the repository).

The premise is sound and the hard part is already right: deriving a semantic layer from
*observed usage* rather than from declared metadata is the correct idea, and the two-tier
`Column -> Joined -> Component -> Schema` model is a good abstraction. What needs work is
the extraction layer feeding it, the clustering, and the corpus it runs on.

---

## 1. Warehouse choice: stay on BigQuery

**Recommendation: keep BigQuery as the primary target. Abstract the extractor so Snowflake
is a config change, and build the Snowflake adapter second.**

The instinct to reconsider is right, because on raw data availability BigQuery is *not* the
best warehouse for this. Ranked by what the platform hands you for free:

| Warehouse | Usage log | Lineage it gives you free |
|---|---|---|
| Snowflake | `ACCOUNT_USAGE.QUERY_HISTORY` (365d) | `ACCESS_HISTORY`: `direct_objects_accessed`, `base_objects_accessed`, `objects_modified` — **column-level**, plus `OBJECT_DEPENDENCIES` |
| Databricks | `system.query.history` | Unity Catalog `system.access.table_lineage` and **`column_lineage`** |
| BigQuery | `INFORMATION_SCHEMA.JOBS` (180d) | `referenced_tables` — **table-level only** |
| Redshift | `SYS_QUERY_HISTORY` / `STL_QUERY` | Nothing structured; text is chunked and needs reassembly |

Snowflake is the strongest source. That is exactly why it is the weaker demo.

If you demo on Snowflake, a competent data architect asks in the first five minutes: *"why do
I need this? `ACCESS_HISTORY` already gives me column-level read/write lineage, and
`OBJECT_DEPENDENCIES` gives me the graph."* You then have to argue value on top of lineage
they already own — a harder pitch, in the customer's own words, on their turf.

BigQuery leaves a real, defensible gap:

- `referenced_tables` stops at the table. There is no column-level lineage in
  `INFORMATION_SCHEMA`, so the column graph genuinely has to be parsed out of `query` text.
- There is no notion of *which columns joined to which* anywhere in the platform. The
  join-key topology — the actual substance of this demo — cannot be obtained any other way.
- `INFORMATION_SCHEMA.JOBS` is retained ~180 days and is per-project/per-region, so
  estate-wide topology means stitching across projects yourself.

So on BigQuery the pitch is simply: *the warehouse tells you which tables were touched; it
cannot tell you what they mean, which ones are duplicates, or how they are actually wired
together.* That is true, checkable, and it lands.

Two caveats to carry into customer conversations so you are not surprised:

1. **GCP does have a lineage product.** Dataplex Universal Catalog's Data Lineage API covers
   BigQuery with table- and some column-level lineage. It is partial, GCP-managed, and does
   not do semantic grouping, deduplication, or topology — but do not claim BigQuery has *no*
   lineage story. Position against it deliberately: it answers "what flowed where," not
   "what does this mean and what is redundant."
2. **The value proposition must be what sits above lineage**, not lineage itself. Lineage is
   becoming table stakes on every platform. Semantic consolidation — "these 6 tables mean the
   same thing, this key has 5 spellings, this column is read by 40 queries and written by
   none" — is not.

**Therefore: make the warehouse a pluggable source, not an assumption.** Define one internal
normalized log record and write per-warehouse adapters:

```
job_id, principal, principal_type, started_at, statement_type, sql_text,
bytes_processed, slot_ms/credits, cache_hit, error, referenced_tables[], destination_table
```

BigQuery and Snowflake adapters both populate that. Snowflake's adapter can *skip* SQL
parsing for table lineage and read `ACCESS_HISTORY` instead — which becomes a selling point
("on Snowflake we use your native lineage and only parse for join topology") rather than a
duplicate code path. First customer question will be "we're on Snowflake, does this work?"
The answer should be a config flag.

---

## 2. Fix the extraction layer (P0)

This is the highest-leverage work. Everything downstream inherits these errors.

### 2.1 Replace naive SQL extraction with a real parser

Roughly 25–30 of the 110 `Table` nodes are not tables: single-letter aliases (`a` on 31
queries, `p` on 13, plus `d`, `e`, `f`, `t`, `psr`, `efl`, `efp`, `em`, `etp`, `fcs`, `ml`,
`pbt`, `psi`, `rf`, `stc`), CTE and derived-table names (`MaintenanceCTE`, `RevenueCTE`,
`TradeCTE`, `BudgetSummary`, `ForecastData`, `ProjectBudget`, `monthly_totals`,
`yearly_totals`), an empty string `""`, Oracle's `DUAL`, and the placeholder
`another_table`. 25 columns have no parent table at all.

Use **`sqlglot`**, which has a BigQuery dialect and solves exactly this:

```python
import sqlglot
from sqlglot.optimizer.qualify import qualify

ast = sqlglot.parse_one(sql, dialect="bigquery")
ast = qualify(ast, schema=warehouse_schema)   # resolves aliases, scopes CTEs, expands *
```

`qualify()` with a schema turns `a.PLANT_ID` into `project.dataset.PROD_METRICS_2022.plant_id`
and makes CTE scopes explicit, which removes the alias and CTE leakage by construction. Also
gives `statement_type` and join predicates structurally instead of by regex.

### 2.2 Make unresolved references visible instead of silently real

Never let an unresolved identifier become a `Table`. Add an `:Unresolved` label and a
reconciliation step against `INFORMATION_SCHEMA.TABLES`/`COLUMNS`. Assert as a load-time
invariant: every `Table` has at least one `HAS_COLUMN`, and every `Table` exists in the
catalog. Anything else is a parse failure to triage, and its count is a pipeline health
metric.

### 2.3 Introduce a canonical column concept

`plant_id` exists as 64 separate `Column` nodes, plus 4 case variants (`PLANT_ID`,
`Plant_ID`, `plant_ID`, `Plant_id`). Keeping physical columns distinct is correct for
provenance, but there is no node representing the *concept*.

Add `(:Column)-[:MEANS]->(:Concept {name})` on a normalized name. This is the primitive the
whole semantic layer wants, and it converts the case-drift problem into a demo asset: *"here
are five spellings of the same join key across 68 tables."*

### 2.4 Validate join semantics

One nonsense predicate — `ON a.PLANT_ID = b.prod_line` — is replicated across **96 queries**,
forging a strong false edge that helps fuse the giant cluster. Add a plausibility check on
join predicates (type compatibility, name/concept distance, cardinality if sampled) and keep
a `confidence` on the `JOIN` edge rather than treating every observed predicate as truth.
Low-confidence joins stay in the graph but are excluded from cluster formation. Surfacing
"this join looks wrong and runs 96 times a day" is itself a finding customers care about.

---

## 3. Fix the clustering (P0)

### 3.1 WCC is the wrong algorithm here

`plant_id` carries 261 join edges. Because WCC computes transitive closure, one hub fuses
everything: the largest `Joined` group holds **85 of the 188** join-participating columns
(45%) and is labelled "Manufacturing Plant Operations" — which just means "the warehouse."
Only 31% of columns participate in any join at all, so WCC is being asked to organise a third
of the graph and failing on that third.

Fixes, in order of effort:

1. **Weight `JOIN` edges** by support (distinct queries) *and* specificity — an IDF-style
   penalty on hub keys, so `plant_id` is discounted the way a stopword is. Persist a
   `hub_score` per concept.
2. **Run weighted Leiden instead of WCC** for group formation (GDS is already deployed; pass
   `relationshipWeightProperty`). Keep WCC only as a coarse pre-partition.
3. **Exclude keys above a degree percentile** from cluster *formation* while keeping them as
   navigable edges. A universal key is infrastructure, not a topic.
4. **Better: promote the join predicate to a node.** Model `(:JoinKey)` so
   `plant_id = plant_id` across 64 tables is one object, then cluster *tables* by shared join
   keys via a bipartite projection. This matches how a data modeller actually thinks and
   sidesteps hub collapse entirely.

### 3.2 Give the 69% of columns that never join a better home

Non-joining columns currently attach straight to a `Component`, so their grouping is driven
entirely by whatever their table's joining columns did. Use co-occurrence in `SELECT` lists
as a second signal — columns repeatedly projected together are related even when they never
appear in an `ON` clause. That is a genuine usage signal the warehouse cannot give you, and
it triples the evidence base.

---

## 4. Fix the description and embedding layer (P0)

### 4.1 Validate LLM output before it is persisted

`Schema` 8's description is raw assistant boilerplate that was written into the graph *and
embedded*:

> "Okay, I understand. Please provide the list of concepts, variables, or entities related to
> \"Plant Production and Downtime Analysis\" and I will infer their meaning and provide a
> short description."

Reject on pattern (`Okay`, `Sure`, `Certainly`, `Please provide`, `I understand`, `As an AI`),
on length bounds, and on the assertion that a parent's description is not merely a
concatenation of its children's. `Component` 12 fails that last check today — its description
is `Joined` 44's label plus `Joined` 80's label with the summarisation step silently skipped.

### 4.2 Enforce a structured output contract

Use structured output / JSON schema with a fixed shape:

```json
{ "name": "2-5 words", "description": "1-2 sentences", "confidence": 0.0 }
```

Descriptions currently range from `"Total Costs"` (11 chars) to a 445-char paragraph, all
compared inside one vector index. Embed `name` and `description` into **separate** indexes so
you are never comparing a two-word label's vector against a paragraph's.

### 4.3 Give the model enough context to not guess

`Component` 12 says "Monthly **Engagement** Forecast" — `MTHLY_ENG_FORECAST` with `ENG`
mis-expanded; it is Energy. The fix is context, not a better model: pass the member column
names, their tables, sibling table names, sample values, and a domain statement. Mine an
abbreviation glossary from the corpus itself (`monthly_energy_yield` co-occurring with
`MTHLY_ENG_FORECAST` resolves `ENG` immediately) and put it in the prompt.

This is worth calling out in the demo narrative: a semantic layer exists to prevent exactly
this class of error, so it must not commit it.

### 4.4 Make the embeddings discriminate

Every `Component` pair sampled sits at cosine **0.94–0.97** (top pair 0.966). The corpus
occupies a tiny cone, so vector search over `Component` cannot rank. Four fixes:

1. **Embed a structured document**, not prose — include column and table names. Names carry
   the discriminating signal; generic domain prose does not.
2. **Use asymmetric task types**: Vertex `text-embedding-004` supports `task_type`
   (`RETRIEVAL_DOCUMENT` at index time, `RETRIEVAL_QUERY` at search time). The current
   pipeline appears to use one undifferentiated embedding.
3. **Center the vectors** — subtract the corpus mean before comparison. Standard fix for
   single-domain corpora and it restores usable spread.
4. **Measure it.** Build a small labelled set of "this question should retrieve that cluster"
   and track recall@k. There is currently no way to know whether the vector index helps.

### 4.5 Record failures instead of dropping nodes

`Schema` ids skip 2, 3, 5, 7, 9, 15, 16; `Component` ids skip 1, 13, 16, 21, 22. Nodes were
lost with no record. Always create the cluster node; set `description_status: failed` when
generation fails so coverage is auditable.

### 4.6 Fix or drop `Query.num`

It is the distinct-user fan-out, and it matches the actual `MADE` degree for only 83% of
queries — the error grows with the count (at 3 users, 561/958). An undocumented field that
reads as authoritative and is wrong 17% of the time should be recomputed at load time or
removed.

---

## 5. Make the corpus realistic (P1)

The synthetic *schema* is genuinely good and should be kept — version chaos
(`MTHLY_ENG_Forecast_v1` vs `MTHLY_ENG_FORECAST_v2`, `supplier_contracts_v1` vs
`supplier_contracts_vFinal`), preserved typos (`Suppler_Details_Table_v1`,
`fuel_purchse_records`, `prod_matrics_22`), date/plant sharding, casing drift. That is what a
real estate looks like and it is the reason the demo exists.

The *queries* are the weak half.

### 5.1 Generate against a ground-truth schema, not the other way round

Today the queries imply the schema, which is how aliases polluted the table list and how
`PLANT_ID = prod_line` became possible. Invert it: define the warehouse first — tables,
columns, types, real PK/FK relationships, deliberate duplicates and deprecated copies — then
generate queries that respect it.

Two payoffs: every join is valid by construction, and you get an **answer key**. You can then
*prove* the clustering works ("recovered 17 of 19 known topic groups, merged two, split one")
instead of asserting it. For a demo that claims to infer meaning, having a measurable ground
truth is the difference between a nice picture and a credible product.

### 5.2 Make the SQL actually BigQuery

Current corpus has zero BigQuery idioms across 9,627 queries — no `ARRAY_AGG`, `UNNEST`,
`QUALIFY`, `SAFE_CAST`, `FORMAT_DATE`, `DATE_DIFF`, `EXTRACT(`, `_PARTITIONTIME` — while
containing MySQL and T-SQL (`GROUP_CONCAT` outnumbers `STRING_AGG` 7:4; `JSON_OBJECT` 16,
`JSON_ARRAYAGG` 8, `NOW()` 14, `CURDATE` 7, `DATEDIFF` 4, `GETDATE` 3, plus `DUAL` and an
`XML` function). `DELETE psr FROM ... psr` is MySQL multi-table DELETE and is illegal in
BigQuery.

- Fully-qualified, backticked `` `project.dataset.table` `` everywhere.
- Partition filters on date columns — the single most characteristic feature of real BQ SQL.
- Window functions, `QUALIFY`, `ARRAY_AGG`/`UNNEST`, real multi-CTE chains. Currently only 18
  queries use a CTE and 75 use a window function.
- **Gate every generated query through `sqlglot.parse_one(sql, dialect="bigquery")` and
  discard failures.** Cheap, and it makes an entire class of embarrassment impossible.
- Length distribution reaching 2–5k characters. Today the longest query in the whole corpus is
  549 characters and the median is 199; real analytics SQL is far longer.
- Delete the `-- SELECT with HAVING Clause Query` comment tags. There are ~600 tag variants
  for maybe 60 intents, including `(if supported)` and `(if applicable)` hedges that only a
  language model would write. Replace with dbt-style job comments —
  `/* {"app": "dbt", "node_id": "model.core.fct_shift_output"} */` — which are realistic *and*
  give the graph free provenance metadata.

### 5.3 Fix the principal mix

`User.email` holds a bare UUID; zero of 128 contain `@`. Query counts are near-uniform
(median 118, max 404, only 3.4x the median) and users touch a median of 9 tables with no team
clustering. Real logs are the opposite on every axis.

- Real principals: `firstname.lastname@customer.com` for humans, and service accounts like
  `dbt-prod@proj.iam.gserviceaccount.com`, `composer-airflow@...`, `looker@...`, `fivetran@...`.
- Realistic shape: a handful of service accounts issue 60–80% of all jobs with near-identical
  recurring SQL on a schedule; humans issue bursty, exploratory, messy queries.
- Humans cluster on their team's 3–5 tables.

This one change makes several demo questions meaningful that currently are not — most notably
*"which tables are only ever touched by ad-hoc human queries and never by a production job?"*
which is a deprecation shortlist.

### 5.4 Add time, and make it load-bearing

`Query` has exactly three properties: `string`, `num`, `join_criteria`. No timestamps at all,
which rules out recency weighting, deprecation detection, and drift — several of the best
reasons to build this from logs rather than from `INFORMATION_SCHEMA.COLUMNS`.

Generate 90–180 days with weekday/business-hour seasonality, scheduled jobs at fixed cron
times, and **a mid-window migration event**: `_v2` appears, `_v1` traffic decays but never
quite reaches zero. That last detail is what makes "which deprecated table is still load
bearing?" demoable.

### 5.5 Add cost

No `total_bytes_processed`, `total_slot_ms`, duration, or `cache_hit`. Adding them with a
realistic long tail lets you weight the topology by spend, which converts the graph from
interesting to budgeted. To a warehouse owner this is the most compelling single addition:
*"this join path costs you $4k/month and terminates in a table nobody has read in 60 days."*

### 5.6 Correct the statement mix

~780 queries are INSERT/UPDATE/DELETE including `INSERT ... VALUES`, which is not what a BigQuery
analytics estate looks like. Real mix is SELECT-dominated plus `MERGE` and
`CREATE OR REPLACE TABLE ... AS SELECT` from ELT — which is what dbt emits. Carry
`statement_type` through to the graph so reads and writes are distinguishable; that is what
makes "read by 40 queries, written by none" answerable.

### 5.7 Scale up

110 tables and 612 columns is a toy, and the customers being targeted have thousands of
tables. Target 2–5k tables, 50k columns, 500k–1M job records. That is the size where graph
traversal visibly beats SQL self-joins, where the visualisation gets impressive, and where
the claim "this works on your estate" becomes credible. Neo4j handles it easily; the current
size proves nothing about scale.

---

## 6. Make the demo compelling (P1)

### 6.1 Plant the findings deliberately

A demo should have known payoffs it *discovers*. Seed the ground-truth schema with:

- two tables 95% column-identical under unrelated names;
- a column read by 40 queries and written by nothing;
- a `_vFinal` chain where the newest copy is the *least* used;
- one join key with five spellings across dozens of tables;
- an expensive query path terminating in a table with no recent reads;
- a cluster that only service accounts touch, and one only humans touch.

Then the demo is "watch it find these," not "here is a graph."

### 6.2 Lead with questions that are painful in SQL

The Neo4j argument is multi-hop and variable-length traversal, so foreground queries the
warehouse is bad at:

- blast radius — "what breaks if I drop this column," to arbitrary depth;
- shortest join path between two columns someone wants to combine;
- semantic duplicate detection via the vector index, *then* traversal to confirm structural
  overlap — the GraphRAG story, concretely;
- "find the cheapest existing join path that already connects these two concepts."

Each is a few lines of Cypher and genuinely awkward as recursive SQL. That contrast is the
pitch.

### 6.3 Close the loop to something actionable

End on generated output, not a visualisation: emit a dbt `schema.yml` with inferred
descriptions, or a semantic-layer/metrics definition, or a ranked deprecation list with
supporting evidence. "Here is the artifact you would have spent two quarters writing by hand"
is a stronger close than a graph, however pretty.

---

## 7. Suggested sequence

| Phase | Work | Why first |
|---|---|---|
| 1 | `sqlglot` extraction; `:Unresolved`; load-time invariants | Everything downstream inherits these errors |
| 2 | Ground-truth schema + regenerated BigQuery-valid corpus with time, cost, real principals | Gives an answer key, so phase 3 is measurable |
| 3 | Weighted Leiden / `JoinKey` modelling; hub-key handling; `:Concept` | Fixes the degenerate 85-column cluster |
| 4 | LLM output contract, validation, glossary; split embeddings; retrieval eval | Makes the semantic layer trustworthy and searchable |
| 5 | Scale to thousands of tables; seeded findings; Bloom/NES dashboards; generated dbt output | Demo polish, once the substance is right |
| 6 | Snowflake adapter over the normalized log record | Answers "we're on Snowflake" in config, not code |

Phases 1 and 2 are the ones that matter. The current bugs are all downstream of naive SQL
extraction and a corpus with no ground truth; fix those two and most of the rest becomes
straightforward.

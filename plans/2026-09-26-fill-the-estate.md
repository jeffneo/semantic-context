# Fill the Fennmoor estate with rows

Status: agreed (2026-09-26); slice 1 done (see Slice 1, as built).

## Why

The estate is deployed empty: every table exists in BigQuery with the spec's schema, and every model
dry-runs, but no table holds a row. That was enough for inferring the semantic layer, which reads only
the log and the catalog. It is not enough for what comes next:

- **Virtual Graph** returns rows, so over empty tables it returns nothing.
- **Answers, not just queries.** `qlsc ask` can validate its SQL but not run it. With rows, the gold
  questions get reference answers, and the evaluation can measure execution accuracy (the right
  result), not only table recall.
- **Context around one customer** (the Redis Context Retriever comparison) needs that customer's
  accounts, transactions and calls to exist.

**Invariant.** qlsc reads nothing a fill changes: the log is the simulated one, and the catalog
(names, types, partitioning, view SQL) is unchanged. After the fill, `qlsc extract` must produce the
same catalog version and `qlsc build` the same graph (`eval/fingerprint.py`). Rows matter only to
Virtual Graph and to the evaluations.

## What is generated, and what BigQuery computes

| Tables | How they get rows |
|---|---|
| 104 raw tables and 23 other base tables (legacy EDW, ML scores, data-quality results, one sandbox extract) | **Generated** by `generate/fill.py` from the spec, loaded with BigQuery load jobs (free) |
| 85 dbt models and 19 copies | **Computed** by running their own SQL (`build/models/`) in BigQuery, in dependency order |
| 93 staging views | Nothing: they read the raw tables |

Only the base tables are generated. Everything derived is computed by the model SQL the spec already
validates, so lineage and join semantics in the data are correct by construction. For example, a mart's
`customer_key` is what `int_customer_identity` actually produced, not what a generator guessed.

## Design

`generate/fill.py`, configured by a new `spec/data.yaml` (scale, seed, the value domains the spec's
comments don't already give). Deterministic and seeded like the other generators: the same spec gives
the same rows, byte for byte.

1. **Populations per id space.** Each identifier concept in `concepts.yaml` has a home column (its
   system of record) and a format. A population is generated once per id space at its home: CIFs
   (10-digit zero-padded), core account ids, card-processor account ids (their own space),
   Salesforce contact ids (18 characters), online-banking logins. Every other column carrying the
   concept samples from that population, with a skew so some customers are busy and most are not.
2. **Crosswalks follow the spec's rules.** Each customer has 0 to 2 online logins. `ga4_user_id` is the
   SHA-256 hex of the login, as the spec says. The card processor keeps its own account ids, and
   core banking maps them to core accounts. The generator writes the mappings the dbt crosswalk models
   read, and the models compute the rest.
3. **Code values the log actually uses.** Status, type and reason codes come from the spec's column
   comments (`CUST_STAT_CD: A active, I inactive, C closed, D deceased`), from literals in the query
   templates (`build/templates.json`: SQL literals and parameter pools), and from the findings. So the
   log's queries find the values they filter on, in plausible proportions.
4. **Time.**
   - History runs before the log window (2026-04-01 to 06-29), and events run through it with daily
     and weekly seasonality.
   - The dated events land in the data:
     - `PREF_BRNCH_ID` is null on rows updated after 2026-04-20;
     - closure calls are coded `ACCT_MAINT` before 2026-06-02 and `ACCT_CLOSE` after;
     - `churn_score_v2` stops at 2026-05-15.
   - Frozen tables stop before the window, dead tables earlier still, and write-only tables have rows
     nobody reads.
5. **Source conventions, same underlying facts.** The card processor stores money in cents and core
   banking in dollars: one set of amounts, two encodings. GA4 keeps its nested records and one table per
   day for the window's days. Legacy EDW tables get the legacy names, codes and gaps.
6. **Traps behave like traps.** A planted wrong join must return plausible wrong rows, not an obvious
   empty set. Card-processor and core account ids overlap in range, so joining one to the other
   silently matches unrelated accounts. The legacy cost-center ids (`CC_ID`) and site codes
   (`SITE_CD`) share values. GA4 user ids are hex, so joining them to a CIF returns nothing, as the spec
   describes.
7. **Synthetic PII only.** Names and addresses come from seeded lists, not real people. Tax ids use
   ranges no real SSN has (9xx). Emails use `example.com`.
8. **Row counts follow the grain.**
   - Entity tables scale from the spec's `rows` (default 1%: about 24,000 customers, 34,000 accounts).
   - Event tables scale further (default 0.1%, capped at 5 million).
   - Tables whose grain includes a date (daily balances) are entities × days.
   - Total at the defaults: about 41 million generated rows, a few GB.

## Loading and computing

- **Output:** `build/data/<dataset>.<table>.ndjson.gz` (gitignored, like the rest of `build/`).
- **Loading:** each file loads with `WRITE_TRUNCATE` into its physical table, using deploy's name
  mapping (`fnb_<dataset>`). Load jobs are free.
- **Shards:** sharded tables get every day or month of the window. The deploy created only a
  representative subset, so the fill creates the rest first, which costs nothing.
- **Models:** run in `deploy.py`'s dependency levels as `TRUNCATE TABLE` then `INSERT INTO <table>
  <model SQL>`. The deployed DDL, with its partitioning and clustering, stays as it is. An incremental
  model's first run is a full build.
- **Cost:**
  - Storage: under $1 a month.
  - Model runs scan roughly tens of GB in total, cents at on-demand prices.
  - The project's custom quota (10 GiB of queries a day, set in `gcp-setup.md`) may be exceeded by a
    full fill. Either fill slice by slice across days, or raise it for the fill.

## Validation

1. **Structure.**
   - Every `pk` column is unique and every `required` column is non-null.
   - Every identifier value exists at its home, except the planted orphans.
   - Row counts are within 10% of the target.
2. **Log replay.** Take a sample of distinct successful SELECT texts from the simulated log, rewrite
   them to physical names, and run them with a bytes-billed cap. At least 90% should return rows;
   the rest are listed with the reason.
3. **Findings in the data.** The profiling-detectable findings are visible: the always-null column
   after 04-20, the new wrap-up code after 06-02, the cents-vs-dollars pairs.
4. **qlsc unchanged.** `qlsc extract` into a scratch directory gives the same catalog version.
   `eval/fingerprint.py` is identical before and after a rebuild.
5. **Evaluation, afterwards.** Each gold question gets a hand-written reference SQL. Its result
   becomes the answer key for execution accuracy.

## Priority order

Each slice ends with the validation above, so the estate is usable after the first.

| Slice | Base tables to generate | Tables with rows after the models run | What it unlocks |
|---|---|---|---|
| **1. Customer context** | 29 raw and 1 base (`churn_score_v3`) | 80 | The Virtual Graph spike and "context around this customer" (see below) |
| **2. Gold questions** | 21 more raw and 12 more base (fraud, lending, marketing, GA4, legacy contact-center costs, `churn_score_v2`) | 160 | Execution accuracy on the 14 gold questions, for `qlsc ask` and the Cypher alternative |
| **3. Everything else** | The remaining 54 raw and 10 base | 324 | The whole estate |
| **4. Mess at depth** | Longer history for legacy, sandbox and copy tables; dead tables' earlier life; every shard, not only the window | 324 | Realism for lifecycle and migration stories |

Slice 1's raw tables, by source:
- **core banking:** `CUSTOMER`, `CUSTOMER_ADDRESS`, `CUSTOMER_CONTACT`, `ACCOUNT`, `ACCOUNT_CUSTOMER_REL`,
  `ACCOUNT_BALANCE_DLY`, `DEPOSIT_TXN`, `BRANCH`, `PRODUCT`;
- **card processor:** `card`, `card_account`, `settlement`, `merchant`, `mcc_code`;
- **online banking:** `online_user`;
- **Salesforce:** `contact`;
- **Genesys:** `conversation`, `participant`, `segment`, `queue`, `user`, `wrapup_code`;
- **reference data:** `contact_center_site`, `product_hierarchy_FINAL_v3`, `zip_region_map`;
- **others:** `braze.user_profile`, `loan_origination.loan`, `workday.worker`, `gl_erp.cost_center`.

These are the upstream closure of the customer marts:
- dimensions: `dim_customer`, `dim_account`, `dim_card`, `dim_branch`, `dim_product`;
- facts: `fct_card_transactions`, `fct_deposit_transactions`, `fct_account_closures`;
- the crosswalks and profile: `int_customer_identity`, `int_account_holders`, `customer_360`;
- the contact-center marts: `fct_calls`, `dim_agent`, `dim_queue`, `dim_cc_site`.

Slice 1 contains three of the five suspect joins: card-processor account ids joined as core account ids
(`dim_account.core_account_id = fct_card_transactions.card_account_id`, and twice in staging). So the
traps are part of the first demo. The GA4 and legacy cost-center traps arrive with slice 2.

## From rows to a virtual graph (slice 1)

This part belongs to the Virtual Graph plan that follows this one. It is here so the data is shaped for
it. Everything below is read from the semantic layer, not the spec; the spec only checks it.

**Nodes: one per entity, on the table where its identifier is the key.** A Variable is not a node, and
nothing is pre-joined. The Variable says which column identifies an entity, and which columns in other
tables point at it. The node's backing table is the one where the Variable's column is the key.
Usage shows which. It is the side that the Variable's trusted joins converge on (`dim_customer.customer_key` has 23
production joins, from 23 tables), and for incremental facts it is the dbt model's MERGE key.

| Label | Backing table | Key | Evidence from the log |
|---|---|---|---|
| `Customer` | `dim_customer` (1:1 with `customer_360`; see views) | `customer_key` | Customer Key variable (26 columns); 23 production joins |
| `Account` | `dim_account` | `account_key` | Account Key variable; 6 production joins |
| `Product` | `dim_product` | `product_code` | Product Code variable; 6 trusted joins |
| `Branch` | `dim_branch` | `branch_id` | Branch variable; 2 trusted joins |
| `Merchant` | `dim_merchant` | `merchant_id` | Merchant Identifier; joined by 10 people |
| `CardTransaction` | `fct_card_transactions` | `settlement_id` | the model's MERGE key |
| `DepositTransaction` | `fct_deposit_transactions` | `transaction_id` | the model's MERGE key |
| `Call` | `fct_calls` | `conversation_id` | the model's MERGE key |
| `Agent`, `Queue`, `ContactCenterSite` | `dim_agent`, `dim_queue`, `dim_cc_site` | `agent_user_id`, `queue_id`, `site_id` | trusted joins from `fct_calls` |

`dim_card` is not a node. No query in the log joins `card_token` to anything, so usage gives it no
identity and no relationships. A model generated from declared keys or column names would include it;
one generated from usage leaves out what the business does not use.

With data, a key is also checked before it goes into the model (`COUNT(DISTINCT key) = COUNT(*)`).
Virtual Graph requires unique keys, and the estate declares none. The check is a safety test, not a
source of meaning, but it is a small extension of "designed models and profiling are not inputs". It
needs agreeing.

**Relationships: one per trusted, identity-preserving join from a fact or dimension to a node's key.**
The backing table is the one holding the pointing column. `fct_card_transactions` is both a node
(`CardTransaction`) and the table behind its relationships.

| Relationship | Backing table, column | Join confidence in the log |
|---|---|---|
| `(Account)-[:HELD_BY]->(Customer)` | `dim_account.customer_key` | production, 3 people |
| `(Account)-[:OF_PRODUCT]->(Product)` | `dim_account.product_code` | production |
| `(Account)-[:OPENED_AT]->(Branch)` | `dim_account.branch_id` | corroborated, 3 people |
| `(CardTransaction)-[:CHARGED_TO]->(Account)` | `fct_card_transactions.account_key` | production |
| `(CardTransaction)-[:MADE_BY]->(Customer)` | `fct_card_transactions.customer_key` | production, 5 people |
| `(CardTransaction)-[:AT_MERCHANT]->(Merchant)` | `fct_card_transactions.merchant_id` | corroborated, 10 people |
| `(DepositTransaction)-[:POSTED_TO]->(Account)` | `fct_deposit_transactions.account_key` | production |
| `(DepositTransaction)-[:AT_BRANCH]->(Branch)` | `fct_deposit_transactions.branch_id` | production |
| `(Call)-[:WITH_CUSTOMER]->(Customer)` | `fct_calls.customer_key` | production, 7 people |
| `(Call)-[:HANDLED_BY]->(Agent)`, `[:IN_QUEUE]->(Queue)`, `[:AT_SITE]->(ContactCenterSite)` | `fct_calls` | production and corroborated |

Virtual Graph requires each relationship type to be unique across the model. That's why a card
transaction is `CHARGED_TO` an account and a deposit is `POSTED_TO` one: the names are chosen per pair,
and generated names are checked for collisions.

**What stays out.**
- **The suspect join.** `dim_account.core_account_id = fct_card_transactions.card_account_id` is
  suspect: one person's join, contradicted by production, which translates card accounts to core
  accounts through `dim_account`. It is not a relationship, so no Cypher query can make that mistake.
  The correct link, `CardTransaction` to `Account` through `account_key`, is in the model.
- **Joins that don't preserve identity.** `post_date = month_start` relates two dates; it doesn't
  make them one thing.
- **Date hubs.** The Balance Date variable joins facts' dates to `dim_date` and to each other. As a node
  it would connect everything to everything, so dates stay properties.

**Views: a thin layer, not a merge.** Virtual Graph reads one BigQuery dataset, so qlsc writes one view
per mapped table into a dataset of its own (`fnb_graph`). Most views are a plain projection: the
properties to expose, renamed. Three kinds of views do a little more:
- **1:1 merges.** Two tables with the same key Variable as their unique key merge into one node view.
  `dim_customer` and `customer_360` both have one row per `customer_key`, so `Customer` carries the
  profile too.
- **Key translation.** A table that points at an entity through a different id space gets the node's
  key added by a lookup along the crosswalk production uses. `online_user` holds a `cif_number`; its view
  adds `customer_key` through `dim_customer`, so `(OnlineUser)-[:LOGIN_OF]->(Customer)` joins on
  the node's key. Arrays (`int_customer_identity.olb_user_ids`) are flattened the same way.
- **Graph ids.** GDS needs one integer id below 2^50 per row. A view can add it for tables whose key is a
  string (`conversation_id`).

**Context around one customer.** This is the shape the Redis comparison needs. Virtual Graph has no
`OPTIONAL MATCH`, so a customer with no calls would drop out of a single pattern that includes calls.
The context is therefore a handful of small queries, one per relationship around the customer (accounts
and products, recent card transactions, calls). A tool runs them and assembles one answer. Which
relationships belong in "context" can come from usage too: the join paths the log's principals take
most often from `dim_customer`.

## Out of scope here

The Virtual Graph service and spike, `qlsc virtualize`, `qlsc ask --cypher` and the router each get
their own plan once slice 1 has rows.

## Slice 1, as built (2026-09-26)

- **Scope was larger than planned:** 92 tables, not 80. The plan's closure followed column lineage only,
  while models also read tables through `sources` without any column flowing into their output
  (`FEE_ASSESSED`, `login_event`). 31 base tables were generated in Python. `churn_score_v3` was
  generated in BigQuery from `dim_customer`, since its keys are the warehouse's. 28 models were computed.
- **GA4 is deferred** with the other sharded tables. The two GA4 session models are empty until slice 2.
- **Checks:**
  - every key is unique and every required column is filled;
  - every identifier resolves at its home table, 100% across 120 columns;
  - closure calls switch from `ACCT_MAINT` (with the IVR intent) to `ACCT_CLOSE` on 2026-06-02 at all
    three sites.
- **Cost:** about 1.8 GiB of queries billed for the model runs. The loads are free.
- **Implementation:** `generate/fill.py`, configured by `spec/data.yaml`.

## Decisions (2026-09-26)

1. **Scale:** the defaults, 1% of entities and 0.1% of events (capped at 5 million rows a table).
2. **First pass:** slice 1 only, then the Virtual Graph spike; the other slices follow.
3. **Key checks:** allowed. Usage proposes every key; a `COUNT(DISTINCT)` check on the data confirms it is
   unique before it enters a virtual graph model. This is a safety check, not a source of meaning, and
   docs/design.md records it as such.
4. **Virtual Graph authentication** (for the spike): try a gcloud application-default credentials file
   first; fall back to a service-account key.
5. Shards and the query quota wait for slice 2: slice 1 has no sharded tables and fits in the quota.

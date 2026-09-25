# M4: layers, subjects, copies, sensitive data

Status: complete, 2026-09-24. Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Stages 5a and 5d).
Code: `pipeline/topology.py`. Scorer: `specs/tools/score.py` (M4 section). Output: `work/TOPOLOGY.md`.
`pipeline/run.sh` rebuilds M1–M4 from `work/` and scores them in under a minute.

## Layers: from who writes a table, never from dataset names

| Layer | Rule |
|---|---|
| raw | written by ingestion (Fivetran merges, file loads) |
| unwritten | exists, but nothing wrote or fed it in the window |
| staging | a transformation view over source tables, with at least half of its columns passed through |
| mart | built by a transformation and consumed by people, BI or ML |
| intermediate | built by a transformation and consumed only by other builds |
| bi / sandbox / ml | written by a BI service / by people / loaded by an ML job |

## Subjects (decision D7: hubs link subjects)

- **Grouping.** Tables are grouped by the non-hub variables they share, each weighted by
  rarity (`log(1 + N / tables containing it)`) and by role: identifiers count 3×.
  Clustering is GDS Leiden, single-threaded and seeded, so runs are reproducible.
- **Hubs don't vote.** Customer, account, product, branch and date variables do not count
  toward membership. Each subject records the hubs it is keyed by (`KEYED_BY`).
- **Entity subjects.** A hub's own tables form that hub's entity subject: the dimension it is
  homed in (`dim_customer`, `dim_account`, `dim_date`) and its crosswalks.
- **Links.** `(:Subject)-[:LINKED {via, joins}]` records which variables connect two subjects.
- **Baseline.** A partition where hubs count like any other key is stored alongside
  (`Table.subject_baseline`), so the effect of D7 can be measured.

## Copies (F14)

A table is a copy when it holds most of the original, and most of it comes from the
original, in both directions: 80% or more each way. The evidence is one of:
- **lineage** in the window;
- **schema**, for copies made before the window: 90% or more identical columns.

Copy families are reported only for copies made by people, BI tools or unknown writers. dbt
promoting a model from one layer to the next is modelling, not sprawl. Each family is
ranked by actual use: the original, the most used copy, the least used, and stale snapshots.

## Sensitive data (F08)

- **Restricted datasets:** access-denied errors from 2 or more people (found: `aml_kyc`,
  `workday`).
- **Sensitive columns:** columns production hashes (`SHA256`, `MD5`). The business itself
  treats them as sensitive.
- **Exposure:**
  - an unhashed lineage path from a sensitive column into an unrestricted dataset; or
  - a schema copy: 80% or more of an unprotected table's columns exist in a restricted table.
    CTAS drops policy tags.
- **Candidates:** columns named like an SSN or tax id outside the restricted zone, never
  hashed. The column itself isn't read, so there is no usage evidence either way.

## Score (2026-09-24)

| | Result |
|---|---|
| Layers | **288 / 296 (97.3%)** on the layers behaviour defines. `legacy` and `ops` are history and purpose labels, reported but not scored |
| Subjects vs. the spec's 89 | NMI **0.889**, against **0.817** when hubs vote like any key |
| Areas vs. the spec's 15 domains | NMI **0.682**, against 0.621 (see below) |
| F08 | **pass**: `kyc_review_extract.tax_id` is a 100% column copy of the restricted `aml_kyc.party`, read by a risk analyst; the legacy `CUST_MSTR` SSN columns are flagged by name |
| F14 | **pass**: `customer_360 → _v2` (schema) `→ _final → _final_FIXED` (lineage); `_final` is the most used copy, `_FIXED` the least used, `_v2` a stale snapshot |
| F15 | **pass**: D7 beats counting hubs at both levels |
| F05 | **pass** (M2: `ACCT_DLY_BAL`, its replacement, and the chain to the Tableau report) |

Beyond the key, copy families also found:
- `ACCT_DLY_BAL_OLD`;
- `tom_test` / `tom_test2`, dead copies of `dim_customer`;
- a Looker PDT that is a full copy of `customer_360`.

## Known weak spot: the coarse level

Areas are only Leiden's top level: 77 groups against 15 domains. Many subjects are a raw
table plus its unused staging view, and nothing joins them to anything, so no usage evidence
groups them.

One attempt grouped subjects by lineage and shared source systems. It made the result worse
(NMI 0.563): core banking feeds so many subjects that it glues unrelated areas together. It
was reverted rather than tuned.

Grouping subjects into domains is better left to M5. There, an LLM names subjects from
their variables and sample SQL, and can propose the grouping, for a person to confirm.

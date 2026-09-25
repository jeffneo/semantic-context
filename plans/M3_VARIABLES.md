# M3: variables, join confidence, identity

Status: complete, 2026-09-24. Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Stages 5b and 5c).
Code: `pipeline/variables.py`. Scorer: `specs/tools/score.py` (M3 section). Output: `work/VARIABLES.md`.
Run everything: `pipeline/run.sh` rebuilds the graph from `work/` in about 40 seconds.

## Decisions (with the user, 2026-09-24)

- **D7: hub keys link subjects; they are never discounted.** Customer, account, product and
  branch are first-class variables, and the strongest identity evidence there is
  (`customer_key` is joined across 26 tables). In subject clustering (M4) they do not vote on
  which subject a table belongs to. Instead, each subject records which hubs it is keyed by,
  and a hub's own tables form an entity subject.
- **D8: one entity, several ids.** Each id space is its own identifier variable, because the
  values differ and cannot be joined directly. An `Entity` groups them, linked by the
  crosswalks the business actually uses.

## Variables

Two columns are the same variable when the business treats them as interchangeable. That
happens in three ways:
- **A join**, but only one whose keys are unchanged or only reformatted (`CAST`, `TRIM`,
  `LPAD`, `LOWER`). A join through `DATE_TRUNC`, `SUBSTR` or `SHA256` relates two variables;
  it does not make them one.
- **Lineage that passes the value through:** a copy, a rename, a format change, or a
  value-picking aggregate. `MAX(user_id)` is still a user id. `MAX(balance)` is a different
  measure, so numbers are picked only when they are used as keys. `CONCAT('DEP-', id)` is a
  new id space.
- **Never through a control column.** In `ARRAY_AGG(queue_id ORDER BY start_time)`,
  `start_time` picks the row but is not the value. The parser now marks such origins
  `control` in lineage.

Every variable gets a role from how it is used: `identifier` (joined), `time`, `measure`
(summed or averaged), `category` (grouped or filtered), or `attribute`.

**Hubs** are keys joined across many tables *and* used by at least half of the inferred
teams. This yields 8. `conversation_id` is joined in 6 tables but only by the contact-center
team, so it is that area's own key.

## Join confidence (usage only)

| Class | Rule |
|---|---|
| `production` | made by a dbt model, a BI model or a scheduled pipeline |
| `corroborated` | two or more people independently; contradicted by nothing |
| `single` | one person; contradicted by nothing |
| `suspect` | equates two id spaces that production keeps as **separate columns of one table and translates between** (for example `dim_account` holds both deposit and card account ids) |
| `self` | the same column on both sides: says nothing about identity |

How the rule is applied:
- **Separation needs positive evidence.** Two id spaces that never happened to meet are not
  separate. That rule removed a false alarm on Braze campaign ids.
- **Judged against everything else.** Each person's join is checked against production plus
  the other people's joins accepted so far, but never against itself. The process is
  iterated.
- **The first pass uses production alone,** so wrong joins cannot vouch for each other. The
  three wrong `account_id` joins did exactly that until this was added.
- **A column production never touches** is placed by its exact name among the established id
  spaces that use that name.
- **Suspect joins stay in the graph, with evidence.** They do not merge variables.

## Identity

| Link | Evidence | Merges into one Entity? |
|---|---|---|
| Two ids homed in one dimension | CIF and `customer_key` in `dim_customer` | yes |
| A table built keyed on one id that picks the others per key | `int_customer_identity`: `GROUP BY cif_number` with `ANY_VALUE(contact_id)` and `ARRAY_AGG(olb_user_id)`; its output must be mostly carried ids, which excludes fact builds like `int_calls_enriched` | yes |
| A translation hop: joined in on one id, another carried out, nothing else read | `online_user`, `dim_aml_party`, `case_alert_link` | no, reported as a link |

The log cannot tell a crosswalk from an association table (cases to alerts). That takes
cardinality, which profiling would supply. The finding says so rather than guessing.

## Other findings

| Finding | Rule |
|---|---|
| `homonym` | one column name used by identifiers that production keys on separately |
| `synonym` | one identifier with 4 or more spellings |
| `unit_mismatch` | a dollar-named column whose lineage reaches a cents column with no `/100` |
| `competing_measures` | measures that people correlate with each other (`CORR`, `COVAR`); the sanctioned one is the measure production or BI uses most broadly. Subtraction does not count: debit minus credit combines complementary measures |
| `limits` | an explicit statement that data-level breakage (a column going null, F16) is not determinable from usage |

## Score (2026-09-24)

| | Result |
|---|---|
| Identifier variables vs. id-space tags | precision **99%**, recall 53%, ARI 0.68 |
| Identifiers in tables the business consumes | precision **99%**, recall **71%**, ARI **0.83** |
| Measure, date and attribute variables | purity **100%** |
| Suspect joins vs. joins between different tagged id spaces | **5/5** precision, **5/5** recall |
| F01, F02, F03, F12, F13, F15, F16 | **pass** |
| F04 | partial: the `CC_ID = SITE_CD` join is flagged; expanding "CC" per table is M5 naming |
| F10 | partial: v3, v2 and marketing's model are grouped, with v3 named sanctioned. `CHURN_SCR` is never used in the window, and the sandbox `churn_risk` was copied before the window, so no lineage exists |

Notes on the gaps:
- **Recall.** Almost all of the remaining gap is raw columns and their staging views that
  nothing downstream reads: M2's dead and write-only tables. No join or lineage connects
  them, so usage gives no evidence either way.
- **The one precision error.** `fct_contacts_all.contact_id` is a `UNION ALL` of Genesys
  conversation ids and legacy Avaya call ids. The business's own model says they are one
  variable (a contact); the spec tags two id spaces. This is left as is, because the same
  construct correctly unifies CIF across deposits, cards and loans in `int_accounts_unioned`.

## Parser additions for M3

- **Lineage function lists** now include scaling constants (`/100`, `*0.01`).
- **`comparisons`:** columns compared in one expression (`CORR(a, b)`, `a - b`, `a > b`),
  loaded as `COMPARED` edges.
- **Lineage origins** carry `control` when they only steer the value.

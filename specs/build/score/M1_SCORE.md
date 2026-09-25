# M1 score: evidence graph

Graph: Neo4j `semanticlayer`. Keys: usage truth (successful statements in the window only).

| | pipeline | truth | matched | precision | recall | F1 |
|---|---|---|---|---|---|---|
| Join pairs (column level) | 156 | 123 | 123 | 78.8% | 100.0% | 88.2% |
| Lineage edges (column level) | 1887 | 1887 | 1887 | 100.0% | 100.0% | 100.0% |

Parse health: 1,194 of 1,194 successful shapes resolved with status ok (100.0%).

## Joins

Recall by truth source (a pair can come from several):

| source | found | in truth |
|---|---|---|
| declared-model | 79 | 79 |
| declared-bi | 4 | 4 |
| reference | 91 | 91 |

The reference extractor skipped 524 predicates it could not resolve (CTE or subquery aliases) across 119,622 successful statements.

Pipeline pairs not in the truth: 33. Of these, 33 are invisible to the reference by construction (semi-joins, joins through CTEs/subqueries or transformed keys); 0 are not, and are listed for inspection:


Misses (in truth, not in the graph): 0


Pipeline pairs invisible to the reference extractor (all; checked by hand, see M1 notes):

- `sbx_marketing.card_spend_by_segment.month_start` = `dw_core.fct_card_transactions.post_date` (INNER; via direct, transform; scopes main)
- `sbx_marketing.card_spend_by_segment.segment` = `dw_core.dim_customer.segment` (INNER; via direct, passthrough; scopes main)
- `dw_compliance.fct_aml_alerts.customer_key` = `dw_core.dim_customer.customer_key` (LEFT; via rename; scopes subquery)
- `dw_contact_center.dim_cc_site.cost_center_id` = `gl_erp.journal_line.cost_center_id` (IN, INNER; via direct, passthrough; scopes main)
- `dw_contact_center.fct_calls.customer_key` = `dw_core.fct_account_closures.customer_key` (INNER; via direct, passthrough; scopes main)
- `dw_core.dim_account.account_key` = `dw_core.fct_card_transactions.account_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_account.account_key` = `dw_core.fct_daily_account_balances.account_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_account.account_key` = `dw_core.fct_deposit_transactions.account_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_account.account_key` = `dw_core.fct_fees.account_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_account.branch_id` = `dw_core.dim_account.branch_id` (LEFT; via passthrough; scopes main)
- `dw_core.dim_account.branch_id` = `dw_core.dim_branch.branch_id` (LEFT; via direct, passthrough; scopes main)
- `dw_core.dim_account.customer_key` = `dw_core.fct_account_closures.customer_key` (LEFT; via passthrough; scopes main)
- `dw_core.dim_account.product_code` = `dw_core.dim_account.product_code` (LEFT; via passthrough; scopes main)
- `dw_core.dim_customer.customer_key` = `dw_core.fct_account_closures.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_customer.customer_key` = `dw_marketing.fct_campaign_attribution.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_customer.customer_key` = `dw_marketing.fct_campaign_sends.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_customer.customer_key` = `dw_risk.fct_bureau_monthly.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_customer.customer_key` = `dw_risk.fct_delinquency_daily.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_customer.customer_key` = `dw_risk.fct_fraud_alerts.customer_key` (LEFT; via rename; scopes subquery)
- `dw_core.dim_date.date_day` = `dw_core.fct_daily_account_balances.balance_date` (INNER; via direct, passthrough; scopes main)
- `dw_core.fct_account_closures.customer_key` = `dw_core.fct_fees.customer_key` (LEFT; via passthrough; scopes main)
- `dw_core.fct_account_closures.customer_key` = `ml_features.feat_customer_daily.customer_key` (LEFT; via passthrough; scopes main)
- `dw_core.fct_account_closures.customer_key` = `ml_scores.churn_score_v3.customer_key` (LEFT; via passthrough; scopes main)
- `dw_core.fct_card_transactions.post_date` = `dw_customer.customer_monthly_summary.month_start` (LEFT; via direct, transform; scopes subquery)
- `dw_core.fct_fees.assessed_date` = `dw_customer.customer_monthly_summary.month_start` (LEFT; via direct, transform; scopes subquery)
- `dw_intermediate.int_account_holders.account_id` = `dw_intermediate.int_account_holders.account_id` (IN; via direct, passthrough; scopes main)
- `dw_risk.fct_bureau_monthly.archive_month` = `ml_scores.churn_score_v3.score_date` (INNER; via direct; scopes main)
- `dw_risk.fct_delinquency_daily.account_key` = `dw_risk.fct_delinquency_daily.account_key` (LEFT; via passthrough; scopes main)
- `dw_staging.stg_genesys__participant.queue_id` = `dw_staging.stg_genesys__queue.queue_id` (LEFT; via aggregate, direct; scopes subquery)
- `dw_staging.stg_genesys__segment.wrap_up_code` = `dw_staging.stg_genesys__wrapup_code.wrapup_code_id` (LEFT; via aggregate, direct; scopes subquery)
- `ml_scores.churn_score_v2.customer_key` = `ml_scores.churn_score_v3.customer_key` (INNER; via passthrough; scopes main)
- `gl_erp.journal_line.accounting_date` = `gl_erp.vendor_invoice.invoice_date` (LEFT; via transform; scopes main)
- `gl_erp.journal_line.cost_center_id` = `gl_erp.vendor_invoice.cost_center_id` (LEFT; via passthrough; scopes main)

## Lineage

763 ingestion edges (Fivetran staging -> raw) are not scored: raw tables have no model SQL in the spec.

Misses: 0


Extras: 0


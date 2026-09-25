# M5 score: naming, embeddings, retrieval

Model: `claude-haiku-4-5-20251001`; embeddings: `text-embedding-3-large` at 512 dimensions.

## Descriptions

| | ok first time | ok after one retry | failed (recorded, not dropped) |
|---|---|---|---|
| Table | 322 | 1 | 0 |
| Variable | 1358 | 28 | 0 |
| Subject | 100 | 0 | 0 |

Assistant boilerplate in stored descriptions: 0.

## F04: CC means credit card, contact center, or cost center

**pass**: CC expanded correctly in 8/8 tables; the CC_ID = SITE_CD join flagged suspect (M3): yes.

## Retrieval: the 14 questions -> tables

Recall of each question's expected tables in the top 5 / 10; hit@5 = an expected or acceptable table in the top 5; avoid = tables the key says not to use (traps, frozen copies) that appear in the top 10. Steering away from those is M6's job, with the findings; here they only show what retrieval alone brings back.

| retrieval | recall@5 | recall@10 | hit@5 | avoid in top 10 |
|---|---|---|---|---|
| tables + subjects + variables + usage prior | 51% | 72% | 100% | 16 |
| tables only | 51% | 72% | 100% | 16 |
| without the usage prior | 37% | 56% | 93% | 15 |

| question | recall@5 | recall@10 | avoid | top 3 |
|---|---|---|---|---|
| Q01 | 0% | 67% | 1 | dw_contact_center.rpt_site_cost_per_contact, sbx_cx_ops.cc_closure_calls_apr_may, sbx_finance.cc_cost_per_call_fy25 |
| Q02 | 0% | 100% | 4 | reverse_etl.aud_high_value_churn_risk, ml_scores.churn_score_v3, sbx_marketing.attrition_propensity_2025 |
| Q03 | 50% | 50% | 1 | dw_digital.fct_account_opening_funnel, dw_digital.fct_web_sessions, dw_staging.stg_ga4__events |
| Q04 | 50% | 50% | 2 | sbx_marketing.card_spend_by_segment, looker_scratch.LR_{id}_card_spend_by_mcc, dw_core.fct_card_transactions |
| Q05 | 50% | 50% | 3 | sbx_finance.eom_bal_by_product_tableau, legacy_edw.EOM_BAL_SNAP, legacy_edw.ACCT_DLY_BAL |
| Q06 | 20% | 40% | 0 | dw_intermediate.int_customer_identity, aml_kyc.screening_hit, aml_kyc.party |
| Q07 | 100% | 100% | 1 | dw_risk.fct_fraud_alerts, fraud_platform.alert, dw_staging.stg_fraud__alert |
| Q08 | 0% | 100% | 1 | dw_risk.fct_credit_applications, reverse_etl.aud_card_upsell_q2_2026, ml_scores.next_best_offer |
| Q09 | 33% | 33% | 1 | sbx_risk.dlq_roll_rates_2026, dw_risk.fct_delinquency_daily, loan_origination.delinquency_snapshot |
| Q10 | 100% | 100% | 1 | dw_contact_center.fct_csat, genesys_cloud.survey_response, dw_contact_center.dim_agent |
| Q11 | 100% | 100% | 0 | dw_digital.fct_app_sessions, sbx_digital.app_screen_paths, amplitude_mobile.EVENTS_318842 |
| Q12 | 100% | 100% | 1 | sbx_marketing.email_list_affluent_apr26, dw_intermediate.int_customer_contact_points, dw_customer.customer_360 |
| Q13 | 17% | 17% | 0 | dw_contact_center.dim_cc_site, dw_contact_center.fct_cc_site_cost_monthly, legacy_edw.CC_EXPNS_MTHLY |
| Q14 | 100% | 100% | 0 | dw_intermediate.int_account_closures, dw_core.fct_account_closures, dw_core.fct_deposit_transactions |

## Proposed domains

The LLM's grouping of named subjects into 21 domains (stored as proposed): NMI **0.760** against the spec's 15 domains, vs 0.683 for M4's graph-only areas.

## Do the descriptions mean the right thing?

For 49 identifier variables with a tagged concept, the concept whose spec description is nearest to the variable's generated description (by embedding) is the right one for **43** (88%), among 57 identifier concepts.


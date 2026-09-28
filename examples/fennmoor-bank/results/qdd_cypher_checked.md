# Quick A/B: cypher_checked

Overrides: {'writer': 'compiled'}. Cypher route.

Gold questions: 3 of 10 correct. Log questions (every 6th): 9 of 30.

Compiled 13 of 40 (10 correct); fell back to free writing for 20.

| question | verdict |
|---|---|
| Q01 | declined: The graph has ContactCenterSite with cost_center_id/cost_center_name but no cost or expense figures, and Call data only lets us count account-closure calls, not actual operating cost |
| Q02 | declined: The graph exposes only Customer, Account, Branch, Call, CardTransaction and DepositTransaction with no churn scoring information (no churn_probability, churn_score, or risk_band fiel |
| Q04 | correct: matches on segment, mcc_category_group, spend=card_spend |
| Q05 | declined: The question needs month-end ledger/account balances (e.g., fct_daily_account_balances / EOM_BAL_SNAP with ledger_balance per balance_date), but no such balance table or property is  |
| Q07 | not covered: none of the cohort's tables is in the virtual graph |
| Q08 | declined: The graph exposes no marketing campaign or attribution data (no dim_campaign / fct_campaign_attribution tables, nor any campaign-related node/relationship), and no credit card applic |
| Q09 | declined: The delinquency rate requires the fct_delinquency_daily table (with DPD/snapshot_date/bucket fields) which is not part of the provided graph — only Account, Product, Branch, Customer |
| Q11 | declined: The graph exposes no node/label for mobile app sessions (the underlying table dw_digital.fct_app_sessions used in the sample SQL isn't part of the provided graph). None of the given  |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures=n |
| L000c43e2 | wrong: 3 rows, not 4 |
| L0a42f6cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L15e6e25c | not covered: none of the cohort's tables is in the virtual graph |
| L21259f73 | wrong: 11 rows, not 10 |
| L31b89126 | correct: matches on fct_card_transactions_post_month=month, fct_card_transactions_segment=segment, fct_card_transactions_cardholders=cardholders, fct_card_transactions_txn_count=transact |
| L3b82445b | declined: The graph provided has no node/relationship for fee data (the fct_fees table referenced in the SQL example, with FEE_TYPE 'OD'/'NSF' and ASSESSED_DATE) nor an account-closure e |
| L4115df4b | correct: matches on period=month, customers_with_ach_credit |
| L4379b829 | wrong: 90 rows, not 120 |
| L4dee27ab | declined: The graph provided has no node label or relationship representing web sessions, landing pages, or page_view events (the fct_web_sessions / analytics events tables referenced in |
| L56b51129 | correct: matches on fct_calls_media_type=media_type, fct_calls_wrapup=wrapup_code, fct_calls_transfers=transferred_calls |
| L5e47c60f | declined: The provided graph schema does not include a Fee/fct_fees node label or relationship, even though the reference SQL queries against fct_fees show it exists in the warehouse. Wi |
| L6505b2e4 | declined: The provided graph schema does not include the fct_credit_applications table (or a corresponding node label) which holds credit application data such as submitted_date, final_o |
| L6b9d5aa5 | wrong: 4445 rows, not 629 |
| L6fe9ce4c | declined: The graph provided doesn't include a CSAT survey node/table (the SQL examples reference `fct_csat` with csat_score, conversation_date, etc.), and there's no relationship expose |
| L771678fa | not covered: none of the cohort's tables is in the virtual graph |
| L7ccb76ec | not covered: none of the cohort's tables is in the virtual graph |
| L83fe5e7b | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_cardholders=cardholders, fct_card_tran |
| L8f767484 | wrong: 26 rows, not 28 |
| L9bedbbe0 | declined: The provided graph schema has no node label or relationship representing the ml_scores.churn_score_v2 table (churn_score, score_date, customer_key), which the reference SQL rel |
| La6c932d6 | correct: matches on segment, callers=distinct_customers, contacts=total_calls |
| Lb04a395e | not covered: none of the cohort's tables is in the virtual graph |
| Lb94b1361 | declined: The graph exposes only raw call, agent, site, customer, and queue data — there is no cost or expense field anywhere (e.g., total_expense used in the bank's rpt_site_cost_per_co |
| Lc38c81cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=merchant_category_group, fct_card_transactions_post_date=post_date, fct_card_tra |
| Lcf63b774 | correct: matches on fct_card_transactions_segment=segment, fct_card_transactions_cardholders=cardholders |
| Ld9c8c1f0 | not covered: none of the cohort's tables is in the virtual graph |
| Ldf622140 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_segment=segment, fct_card_transactions |
| Le6d5789b | declined: The graph has no entity or property representing account closure events with a closure date or a voluntary-closure flag — Customer has no closure-related fields, and Call only  |
| Lecec1d54 | declined: The example SQL queries against a fct_account_closures table with an is_voluntary flag and close_reason, but the provided graph only exposes Account with close_date and close_r |
| Lef98f427 | declined: The provided graph only exposes ContactCenterSite and Call nodes; there is no node/relationship for the monthly cost/expense table (fct_cc_site_cost_monthly) or the GL/vendor i |
| Lfba52c1e | not covered: none of the cohort's tables is in the virtual graph |

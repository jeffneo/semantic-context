# Quick A/B: parts_definitions

Overrides: {'anchors': 'parts', 'computations': '6', 'computation_tables': 'false'}. SQL route.

Gold questions: 6 of 10 correct. Log questions (every 6th): 21 of 30.

| question | verdict |
|---|---|
| Q01 | wrong: no column holds closure_contacts, expense_2025 (1 of 3 match) |
| Q02 | empty: no rows |
| Q04 | correct: matches on segment=customer_segment, mcc_category_group, spend=card_spend |
| Q05 | correct: matches on month=month_end, product_line, month_end_balance=total_deposit_balance |
| Q07 | correct: matches on channel, confirmed_share=confirm_rate |
| Q08 | wrong: no column holds card_applications (1 of 2 match) |
| Q09 | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | correct: matches on week=week_start, customers |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures |
| L000c43e2 | correct: matches on closure_calls=acct_maint_calls, site_id~site_name (relabeled) |
| L0a42f6cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L15e6e25c | correct: matches on event_date, channel, success_rate, attempts=total_attempts |
| L21259f73 | correct: matches on period=week_start, customers_with_ach_credit |
| L31b89126 | wrong: no column holds fct_card_transactions_txn_count (3 of 4 match) |
| L3b82445b | wrong: no column holds later_closed (1 of 2 match) |
| L4115df4b | correct: matches on period=txn_month, customers_with_ach_credit=distinct_customers |
| L4379b829 | wrong: 90 rows, not 120 |
| L4dee27ab | correct: matches on landing_page, customers=customers_visited, also_contacted_us=customers_also_contacted_90d |
| L56b51129 | correct: matches on fct_calls_media_type=media_type, fct_calls_wrapup=wrapup_code, fct_calls_transfers=transferred_call_count |
| L5e47c60f | correct: matches on FEE_TYPE=fee_type, FEES=total_fees, NET=total_net_fee_amount |
| L6505b2e4 | correct: matches on PRODUCT_LINE=product_line, AVG_APPROVED=avg_approved_amount, AVG_APR=avg_approved_apr, N=num_applications |
| L6b9d5aa5 | wrong: 4445 rows, not 629 |
| L6fe9ce4c | correct: matches on segment=customer_segment, csat=avg_csat_score, surveys |
| L771678fa | correct: matches on fct_campaign_engagement_clicks=clicks, fct_campaign_engagement_campaign_name~campaign_name (relabeled), fct_campaign_engagement_event_date~event_date (relabeled), fct |
| L7ccb76ec | correct: matches on traffic_medium, logged_in_share, sessions |
| L83fe5e7b | wrong: no column holds fct_card_transactions_cardholders, fct_card_transactions_interchange (2 of 4 match) |
| L8f767484 | wrong: 416 rows, not 32 |
| L9bedbbe0 | wrong: no column holds avg_churn, high_risk (1 of 3 match) |
| La6c932d6 | correct: matches on segment=customer_segment, callers=distinct_customers, contacts=total_calls |
| Lb04a395e | correct: matches on app_version, platform, sessions |
| Lb94b1361 | correct: matches on site_name, avg_cost_per_contact, closure_calls=total_closure_calls |
| Lc38c81cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=merchant_category_group, fct_card_transactions_post_date=transaction_date, fct_c |
| Lcf63b774 | correct: matches on fct_card_transactions_segment=segment, fct_card_transactions_cardholders=distinct_cardholders |
| Ld9c8c1f0 | correct: matches on channel, cut=country, attempts |
| Ldf622140 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_segment=customer_segment, fct_card_tra |
| Le6d5789b | wrong: 3 rows, not 4 |
| Lecec1d54 | correct: matches on period=week, account_family, close_reason, closures |
| Lef98f427 | correct: matches on month_start, total_expense, payroll_expense, vendor_expense, site_id~site_name (relabeled) |
| Lfba52c1e | empty: no rows |

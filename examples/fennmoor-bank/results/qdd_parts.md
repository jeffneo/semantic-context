# Quick A/B: parts

Overrides: {'anchors': 'parts', 'computations': '0'}. SQL route.

Gold questions: 7 of 10 correct. Log questions (every 6th): 23 of 30.

| question | verdict |
|---|---|
| Q01 | wrong: no column holds closure_contacts, expense_2025 (1 of 3 match) |
| Q02 | empty: no rows |
| Q04 | correct: matches on segment, mcc_category_group, spend=total_spend |
| Q05 | correct: matches on month, product_line, month_end_balance=eom_balance |
| Q07 | correct: matches on channel, confirmed_share=confirm_rate |
| Q08 | correct: matches on campaign_name, card_applications=card_application_conversions |
| Q09 | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | correct: matches on week=week_start, customers |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures |
| L000c43e2 | correct: matches on closure_calls=acct_maint_calls, site_id~site_name (relabeled) |
| L0a42f6cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L15e6e25c | correct: matches on event_date, channel, success_rate, attempts=total_attempts |
| L21259f73 | correct: matches on period=week_start, customers_with_ach_credit |
| L31b89126 | wrong: no column holds fct_card_transactions_txn_count (3 of 4 match) |
| L3b82445b | correct: matches on heavy_fee_customers=heavy_fee_customer_count, later_closed=heavy_fee_customers_who_later_closed |
| L4115df4b | correct: matches on period=txn_month, customers_with_ach_credit=distinct_customers |
| L4379b829 | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_site_name=site_name, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_transfers=transferred_calls |
| L4dee27ab | correct: matches on landing_page, customers=distinct_customers, also_contacted_us=customers_also_contacted_90d |
| L56b51129 | correct: matches on fct_calls_media_type=media_type, fct_calls_wrapup=wrapup_code, fct_calls_transfers=transferred_calls |
| L5e47c60f | correct: matches on FEE_TYPE=fee_type, FEES=total_fees, NET=total_net_fee_amount |
| L6505b2e4 | correct: matches on PRODUCT_LINE=product_line, AVG_APPROVED=avg_approved_amount, AVG_APR=avg_approved_apr, N=num_applications |
| L6b9d5aa5 | wrong: 4445 rows, not 629 |
| L6fe9ce4c | correct: matches on segment=customer_segment, csat=avg_csat_score, surveys |
| L771678fa | correct: matches on fct_campaign_engagement_clicks=clicks, fct_campaign_engagement_campaign_name~campaign_name (relabeled), fct_campaign_engagement_event_date~event_date (relabeled), fct |
| L7ccb76ec | correct: matches on traffic_medium, logged_in_share, sessions |
| L83fe5e7b | wrong: no column holds fct_card_transactions_cardholders, fct_card_transactions_interchange (2 of 4 match) |
| L8f767484 | wrong: no column holds fct_calls_agent_name, fct_calls_conversation_week, fct_calls_site_name, fct_calls_avg_handle_time, fct_calls_closure_calls, fct_calls_count (0 of 6 match) |
| L9bedbbe0 | wrong: no column holds avg_churn, high_risk (1 of 3 match) |
| La6c932d6 | correct: matches on segment=customer_segment, callers=distinct_customers, contacts=total_calls |
| Lb04a395e | correct: matches on app_version, platform, sessions |
| Lb94b1361 | correct: matches on site_name, avg_cost_per_contact, closure_calls=total_closure_calls |
| Lc38c81cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=merchant_category_group, fct_card_transactions_post_date=txn_date, fct_card_tran |
| Lcf63b774 | correct: matches on fct_card_transactions_segment=segment, fct_card_transactions_cardholders=distinct_cardholders |
| Ld9c8c1f0 | correct: matches on channel, cut=country, attempts |
| Ldf622140 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_segment=customer_segment, fct_card_tra |
| Le6d5789b | wrong: no column holds closers_who_called (1 of 2 match) |
| Lecec1d54 | correct: matches on period=week, account_family, close_reason, closures |
| Lef98f427 | correct: matches on month_start, total_expense, payroll_expense, vendor_expense, site_id~site_name (relabeled) |
| Lfba52c1e | empty: no rows |

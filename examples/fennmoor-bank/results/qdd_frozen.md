# Quick A/B: frozen

Overrides: {'writer': 'compiled'}. SQL route.

Gold questions: 6 of 10 correct. Log questions (every 6th): 23 of 30.

Compiled 36 of 40 (27 correct); fell back to free writing for 4.

Query model, over the 40 questions it wasn't cached for (41 calls): 2.5 s per question in the API, 6,416 tokens in and 309 out per question.

| question | verdict |
|---|---|
| Q01 | wrong: 4 rows, not 3 |
| Q02 | wrong: 1 rows, not 5 |
| Q04 | correct: matches on segment=customer_segment, mcc_category_group=merchant_category_group, spend=card_purchase_spend |
| Q05 | wrong: no column holds month_end_balance (2 of 3 match) |
| Q07 | correct: matches on channel, confirmed_share=confirmed_fraud_rate |
| Q08 | correct: matches on campaign_name=campaign, card_applications |
| Q09 | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | correct: matches on week, customers |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures |
| L000c43e2 | correct: matches on closure_calls=acct_maint_calls, site_id~site (relabeled) |
| L0a42f6cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L15e6e25c | correct: matches on event_date=day, channel, success_rate=login_success_rate, attempts=login_attempts |
| L21259f73 | correct: matches on period=week, customers_with_ach_credit |
| L31b89126 | correct: matches on fct_card_transactions_post_month=month, fct_card_transactions_segment=segment, fct_card_transactions_cardholders=cardholders, fct_card_transactions_txn_count=card_tra |
| L3b82445b | correct: matches on heavy_fee_customers, later_closed=heavy_fee_customers_closed_account |
| L4115df4b | correct: matches on period=month, customers_with_ach_credit |
| L4379b829 | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_site_name=site_name, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_transfers=transferred_calls |
| L4dee27ab | correct: matches on landing_page, customers=customers_visited, also_contacted_us=customers_also_contacted_90d |
| L56b51129 | correct: matches on fct_calls_media_type=media_type, fct_calls_wrapup=wrapup_code, fct_calls_transfers=transferred_calls |
| L5e47c60f | correct: matches on FEE_TYPE=fee_type, FEES=fee_count, NET=total_net_fee |
| L6505b2e4 | wrong: 7 rows, not 5 |
| L6b9d5aa5 | wrong: 3310 rows, not 629 |
| L6fe9ce4c | correct: matches on segment, csat=avg_csat, surveys |
| L771678fa | correct: matches on fct_campaign_engagement_clicks=clicks, fct_campaign_engagement_campaign_name~campaign_name (relabeled), fct_campaign_engagement_event_date~event_date (relabeled), fct |
| L7ccb76ec | correct: matches on traffic_medium, logged_in_share, sessions |
| L83fe5e7b | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_cardholders=cardholders, fct_card_tran |
| L8f767484 | wrong: 416 rows, not 28 |
| L9bedbbe0 | wrong: no column holds avg_churn, high_risk (1 of 3 match) |
| La6c932d6 | wrong: 6 rows, not 5 |
| Lb04a395e | correct: matches on app_version, platform, sessions |
| Lb94b1361 | correct: matches on site_name, avg_cost_per_contact=cost_per_contact, closure_calls |
| Lc38c81cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=category_group, fct_card_transactions_post_date=post_date, fct_card_transactions |
| Lcf63b774 | correct: matches on fct_card_transactions_segment=segment, fct_card_transactions_cardholders=cardholders |
| Ld9c8c1f0 | correct: matches on channel, cut=country, attempts=login_attempts |
| Ldf622140 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_segment=segment, fct_card_transactions |
| Le6d5789b | wrong: no column holds closers_who_called (1 of 2 match) |
| Lecec1d54 | correct: matches on period=week, account_family, close_reason, closures |
| Lef98f427 | correct: matches on month_start=month, total_expense, payroll_expense, vendor_expense, site_id~site (relabeled) |
| Lfba52c1e | wrong: no column holds PERIOD_NAME (4 of 5 match) |

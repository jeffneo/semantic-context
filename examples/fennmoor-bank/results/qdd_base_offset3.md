# Quick A/B: base_offset3

Overrides: {'computations': '0'}. SQL route.

Gold questions: 7 of 10 correct. Log questions (every 6th): 25 of 29.

| question | verdict |
|---|---|
| Q01 | wrong: no column holds closure_contacts (2 of 3 match) |
| Q02 | wrong: 1 rows, not 5 |
| Q04 | correct: matches on segment, mcc_category_group, spend=total_spend |
| Q05 | correct: matches on month=month_end, product_line, month_end_balance=balance |
| Q07 | correct: matches on channel, confirmed_share=confirm_rate |
| Q08 | correct: matches on campaign_name, card_applications=card_application_conversions |
| Q09 | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | correct: matches on week=week_start, customers |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures |
| L05fc9f83 | correct: matches on queue_site_id, agent_site_id, calls |
| L0ecb0a57 | correct: matches on fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardholders=distinct_cardholders, fct_card_transacti |
| L1ab5b4f7 | correct: matches on digital_wallet, cards, customers |
| L2d53a09b | correct: matches on PROD_CD=product_code, balance=total_ledger_balance |
| L37d38fdd | correct: matches on fct_card_transactions_post_month=txn_month, fct_card_transactions_segment=customer_segment, fct_card_transactions_interchange=total_interchange |
| L3d84d777 | correct: matches on fct_calls_site_name=site_name, fct_calls_conversation_week=call_week, fct_calls_abandon_rate=abandon_rate |
| L42c41a99 | correct: matches on wk=conversation_week, aht=avg_handle_sec, site_id~site_name (relabeled) |
| L49555283 | correct: matches on grp=reporting_category, accounts, balance |
| L5330bf47 | correct: matches on fct_calls_site_name=site_name, fct_calls_abandon_rate=abandon_rate |
| L5bac0ee7 | wrong: no column holds DLQ, RATE (3 of 5 match) |
| L5ed9db67 | correct: matches on cif_number, full_name, conversation_date, wrapup_code_name |
| L67c545c8 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_txn_type=txn_type, fct_card_transactions_interchange=total_interchange, fct_card_transactions_total |
| L6d2aee92 | correct: matches on category_group=mcc_category_group, m=month_start, spend=total_spend |
| L74cd39cb | correct: matches on fct_calls_media_type=media_type, fct_calls_abandon_rate=abandon_rate, fct_calls_closure_calls=distinct_closure_calls, fct_calls_count=distinct_total_calls |
| L78ae7fd3 | wrong: no column holds n (1 of 2 match) |
| L800eda03 | correct: matches on campaign_name, delivered, opens, clicks, ctr |
| L87ee24ce | correct: matches on posted_date, transaction_type, n=txn_count |
| L97629e25 | wrong: no column holds SNAPSHOT_DATE (3 of 4 match) |
| L9dfa7691 | correct: matches on as_of_date, balance=avg_30d_avg_balance, logins=avg_30d_login_count, contacts=avg_90d_contact_count |
| Laedcf94e | correct: matches on account_family, close_reason, n=closures |
| Lb7adf6c4 | correct: matches on grp=product_family, accounts=distinct_accounts, balance=total_ledger_balance |
| Lba99d5e4 | correct: matches on fct_calls_agent_name=agent_name, fct_calls_media_type=media_type, fct_calls_site_name=site_name, fct_calls_avg_handle_time=avg_handle_sec, fct_calls_count=conversatio |
| Lccd8d6b4 | wrong: no column holds fct_card_transactions_interchange, fct_card_transactions_txn_count (1 of 3 match) |
| Ld49d2be4 | correct: matches on sends_per_customer=send_count, customers=customer_count |
| Ldc27f830 | correct: matches on wk=week_start, channel, sends |
| Le50954e7 | correct: matches on fct_calls_is_outsourced=is_outsourced, fct_calls_closure_calls=closure_calls |
| Lea0a11f5 | correct: matches on unsubscribes, bounces, wk~event_week (relabeled) |
| Lee760ebe | correct: matches on m=enrollment_month, enrollment_channel, enrollments |
| Lf3aa1fe7 | correct: matches on fct_calls_count=conversation_count, fct_calls_wrapup~wrapup_code (relabeled) |

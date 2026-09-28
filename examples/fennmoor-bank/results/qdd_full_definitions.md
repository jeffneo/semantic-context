# Quick A/B: full_definitions

Overrides: {'computations': '5', 'computation_tables': 'false'}. SQL route.

Gold questions: 7 of 10 correct. Log questions (all): 130 of 176.

| question | verdict |
|---|---|
| Q01 | empty: no rows |
| Q02 | wrong: 1 rows, not 5 |
| Q04 | correct: matches on segment=customer_segment, mcc_category_group, spend=total_spend |
| Q05 | correct: matches on month=month_start, product_line, month_end_balance=eom_balance |
| Q07 | correct: matches on channel, confirmed_share=confirm_rate |
| Q08 | correct: matches on campaign_name, card_applications=card_application_conversions |
| Q09 | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | correct: matches on week=week_start, customers |
| Q12 | correct: matches on cif_number (as Q12.alt) |
| Q14 | correct: matches on account_family, closures |
| L000c43e2 | correct: matches on closure_calls=acct_maint_call_count, site_id~site_name (relabeled) |
| L02b0fb2f | correct: matches on name=wrapup_code_name, n=segment_count |
| L04bfef55 | wrong: no column holds ach_credits, atm_txns, outflows (1 of 4 match) |
| L05fc9f83 | correct: matches on queue_site_id, agent_site_id, calls |
| L09cde242 | correct: matches on period, account_family, close_reason, closures |
| L0a171fb1 | correct: matches on month_start, site_id, is_outsourced, contacts=total_contacts, closure_calls, total_expense, cost_per_contact |
| L0a42f6cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L0b88eeab | wrong: no column holds product_name, open_card_accounts (0 of 2 match) |
| L0c593d42 | correct: matches on session_date, device_category, sessions, avg_engaged_sec, logged_in_share |
| L0ecb0a57 | correct: matches on fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardholders=cardholders, fct_card_transactions_total |
| L11f336b4 | correct: matches on channel, cut=result, attempts |
| L12addf1d | wrong: no column holds fct_campaign_engagement_event_date, fct_campaign_engagement_event_week (2 of 4 match) |
| L15e6e25c | correct: matches on event_date, channel, success_rate, attempts=total_attempts |
| L18561859 | correct: matches on site_id=SITE_CD, disposition_code=DISPOSITION_CD, calls |
| L1aaabd76 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_segment=segment, fct_card_transactions_total_spend=total_spend |
| L1ab5b4f7 | correct: matches on digital_wallet, cards, customers |
| L1b1d58d4 | correct: matches on WK=application_week, CUT=channel, APPS=applications |
| L1ee476f0 | correct: matches on merchant_name, category_group=mcc_category_group, spend=total_purchase_spend |
| L21259f73 | correct: matches on period=week_start, customers_with_ach_credit |
| L21959863 | correct: matches on grp=product_line, accounts, balance=ledger_balance |
| L2d424059 | correct: matches on decidedBy=decision_maker, outcome, n=decision_count |
| L2d53a09b | correct: matches on PROD_CD=product_code, balance=total_ledger_balance |
| L30b11cd6 | wrong: 28 rows, not 86 |
| L30bb45da | correct: matches on channel, alerts, confirmed=confirmed_alerts, confirm_rate=confirmation_rate |
| L31b89126 | correct: matches on fct_card_transactions_post_month=txn_month, fct_card_transactions_segment=customer_segment, fct_card_transactions_cardholders=distinct_cardholders, fct_card_transacti |
| L3392c50f | correct: matches on fct_campaign_engagement_unsubscribes=unsubscribes, fct_campaign_engagement_event_week~wk (relabeled) |
| L359c74a0 | wrong: 100 rows, not 62 |
| L37d38fdd | correct: matches on fct_card_transactions_post_month=txn_month, fct_card_transactions_segment=customer_segment, fct_card_transactions_interchange=total_interchange |
| L3949aa11 | correct: matches on PROD_CD=product_code, balance=total_eom_balance |
| L3a388091 | correct: matches on period, account_family, close_reason, closures |
| L3b82445b | correct: matches on heavy_fee_customers=heavy_fee_customer_count, later_closed=heavy_fee_customers_later_closed |
| L3ca155d7 | correct: matches on fct_calls_site_name=site_name, fct_calls_count=total_calls, fct_calls_closure_calls=closure_calls |
| L3cb32f46 | correct: matches on fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_post_month=post_month, fct_card_transactions_txn_type=txn_type, fct_card_transactions_cardhol |
| L3d84d777 | correct: matches on fct_calls_site_name=site_name, fct_calls_conversation_week=call_week, fct_calls_abandon_rate=abandon_rate |
| L3e70fccd | correct: matches on PROD_CD=product_code, ACCTS=account_count, AVG_OD_LIMIT=avg_overdraft_limit_amount |
| L41064b12 | correct: matches on fct_calls_conversation_week=call_week, fct_calls_ivr_intent=ivr_intent, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_closure_calls=closure_calls, fct_call |
| L4115df4b | correct: matches on period=txn_month, customers_with_ach_credit=distinct_customers_with_ach_credit |
| L41fd18a8 | correct: matches on screen=screen_name, views |
| L42795751 | empty: no rows |
| L42c41a99 | wrong: no column holds wk, site_id, aht (0 of 3 match) |
| L42fc491a | wrong: no column holds distinct_mcc (4 of 5 match) |
| L435dac23 | correct: matches on account_family, avg_tenure_days, tenure_quartiles~tenure_days_quartile_breakpoints (relabeled) |
| L4379b829 | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_site_name=site_name, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_transfers=transferred_calls |
| L4540fe70 | wrong: 31 rows, not 30 |
| L469ef255 | wrong: 92 rows, not 91 |
| L49555283 | correct: matches on grp=reporting_category, accounts, balance=total_ledger_balance |
| L4b4d230a | wrong: no column holds fct_calls_agent_name, fct_calls_queue_name, fct_calls_wrapup, fct_calls_transfers (1 of 5 match) |
| L4cc2c24f | correct: matches on cif_number, app_sessions, screens=total_screens |
| L4dee27ab | correct: matches on landing_page, customers=distinct_customers, also_contacted_us=customers_also_contacted_90d |
| L4e0f44e9 | correct: matches on fct_calls_conversation_week=week_start, fct_calls_wrapup=wrapup_code_name, fct_calls_abandon_rate=abandon_rate |
| L4f929b5b | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_conversation_week=conversation_week, fct_calls_ivr_intent=ivr_intent, fct_calls_count=call_count, fct_calls_t |
| L5330bf47 | wrong: no column holds fct_calls_abandon_rate (1 of 2 match) |
| L5515d30a | correct: matches on campaign_name, conversions, avg_hours_to_convert=avg_hours_to_conversion |
| L55c0e195 | correct: matches on fct_card_transactions_post_month=post_month, fct_card_transactions_interchange=total_interchange_income |
| L56b51129 | correct: matches on fct_calls_media_type=media_type, fct_calls_wrapup=wrapup_code_name, fct_calls_transfers=transferred_calls |
| L57c08ff2 | correct: matches on SITE_CD=site_id, DISPOSITION_CD=disposition_code, calls |
| L582f3941 | correct: matches on fct_calls_wrapup=wrapup_code_name, fct_calls_closure_calls=account_closure_calls, fct_calls_transfers=transferred_calls |
| L5bac0ee7 | wrong: no column holds DLQ, RATE (3 of 5 match) |
| L5cbff83a | correct: matches on segment=customer_segment, apps=applications_submitted, approved=applications_approved |
| L5d233427 | correct: matches on fct_card_transactions_is_foreign=is_foreign_txn, fct_card_transactions_merchant_name=merchant_name, fct_card_transactions_segment=customer_segment, fct_card_transacti |
| L5e47c60f | correct: matches on FEE_TYPE=fee_type, FEES=total_fees, NET=total_net_fee |
| L5e63b8a9 | wrong: 1 rows, not 5 |
| L5eadc021 | correct: matches on m=month, interest=total_accrued_interest |
| L5ed9db67 | correct: matches on cif_number, full_name, conversation_date, wrapup_code_name |
| L5f5e344a | correct: matches on fct_calls_queue_name=queue_name, fct_calls_abandon_rate=abandonment_rate, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_count=distinct_conversations |
| L62fdbc12 | wrong: no column holds fct_campaign_engagement_campaign_name, fct_campaign_engagement_delivered, fct_campaign_engagement_open_rate (2 of 5 match) |
| L6505b2e4 | wrong: 7 rows, not 5 |
| L66b70456 | wrong: no column holds fct_calls_is_outsourced, fct_calls_count (3 of 5 match) |
| L66ee1a03 | correct: matches on fct_calls_conversation_week=conversation_week, fct_calls_site_name=site_name, fct_calls_wrapup=wrapup_code, fct_calls_avg_handle_time=avg_handle_time_sec |
| L67c545c8 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_txn_type=txn_type, fct_card_transactions_interchange=total_interchange, fct_card_transactions_total |
| L684ffcba | correct: matches on productCode=product_code, N=num_loans, CHARGED_OFF=total_charged_off_amount |
| L69a33e9e | correct: matches on period=closure_month, account_family, close_reason, closures |
| L6b9d5aa5 | wrong: 4445 rows, not 629 |
| L6ce6e9c3 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_txn_type=txn_type, fct_card_transactions_interchange=total_interchange, fct_card_transactions_total |
| L6d29ff82 | correct: matches on site_id, m=month_start, total_site_cost |
| L6d2aee92 | correct: matches on category_group=mcc_category_group, m=month_start, spend=total_purchase_spend |
| L6e2cd931 | correct: matches on fct_calls_is_outsourced=is_outsourced, fct_calls_wrapup=wrapup_code, fct_calls_abandon_rate=abandon_rate, fct_calls_transfers=transferred_calls |
| L6f55e765 | correct: matches on fct_campaign_engagement_campaign_name=campaign_name, fct_campaign_engagement_delivered=messages_delivered, fct_campaign_engagement_opens=messages_opened, fct_campaign |
| L6fe9ce4c | correct: matches on segment=customer_segment, csat=avg_csat_score, surveys |
| L73371e91 | wrong: no column holds inflows, outflows (2 of 4 match) |
| L74224b5f | correct: matches on state_code, segment, n=active_customers |
| L74cd39cb | correct: matches on fct_calls_media_type=media_type, fct_calls_abandon_rate=abandon_rate, fct_calls_closure_calls=account_closure_calls, fct_calls_count=total_calls |
| L754091da | wrong: no column holds logins (2 of 3 match) |
| L75ea7f97 | wrong: 9 rows, not 6 |
| L771678fa | correct: matches on fct_campaign_engagement_clicks=clicks, fct_campaign_engagement_campaign_name~campaign_name (relabeled), fct_campaign_engagement_event_date~event_date (relabeled), fct |
| L784cf2bf | wrong: no column holds payroll_cost (1 of 2 match) |
| L788679b6 | wrong: no column holds fct_campaign_engagement_campaign_name, fct_campaign_engagement_opens (2 of 4 match) |
| L78ae7fd3 | wrong: no column holds n (1 of 2 match) |
| L78f9c15c | wrong: 2 rows, not 4 |
| L7ac9ed17 | correct: matches on m=month, product_line, balance=total_ledger_balance |
| L7ccb76ec | correct: matches on traffic_medium, logged_in_share, sessions |
| L7e87d30b | wrong: no column holds avg_score (2 of 3 match) |
| L7f4db61e | correct: matches on wk=open_week, open_channel, new_accounts |
| L800eda03 | correct: matches on campaign_name, delivered, opens, clicks, ctr |
| L808ab45e | correct: matches on platform, screen_quartiles=screen_count_quartiles, avg_events=avg_events_per_session |
| L839f551b | correct: matches on queue_name, calls=call_count |
| L83fe5e7b | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_cardholders=distinct_cardholders, fct_ |
| L8634c1ea | correct: matches on fct_card_transactions_post_month=txn_month, fct_card_transactions_cardholders=cardholders, fct_card_transactions_total_spend=total_purchase_spend |
| L873d32ca | correct: matches on yr=contact_year, site_id, contacts=total_contacts |
| L87ee24ce | correct: matches on posted_date, transaction_type, n=txn_count |
| L8bc8a936 | wrong: no column holds agent_user_id (3 of 4 match) |
| L8ee70d9a | correct: matches on fct_calls_site_name=site_name, fct_calls_abandon_rate=call_abandon_rate |
| L8f767484 | wrong: 418 rows, not 32 |
| L8f9a7871 | correct: matches on campaign_name, delivered, opens=opened, clicks=clicked, ctr |
| L97338912 | correct: matches on fct_calls_is_outsourced=is_outsourced, fct_calls_ivr_intent=ivr_intent, fct_calls_media_type=media_type, fct_calls_abandon_rate=abandon_rate |
| L97629e25 | empty: no rows |
| L986ea342 | wrong: no column holds avg_churn, high_risk (1 of 3 match) |
| L9890546d | correct: matches on decile, n=customers, closed_rate=voluntary_close_share, avg_p=avg_churn_probability |
| L9bedbbe0 | wrong: no column holds avg_churn, high_risk (1 of 3 match) |
| L9c385afd | correct: matches on PRODUCT_LINE=product_line, BUCKET=bucket, LOANS=loans |
| L9d80def1 | wrong: no column holds inflows, outflows (2 of 4 match) |
| L9dfa7691 | correct: matches on as_of_date, balance=avg_30d_balance, logins=avg_30d_logins, contacts=avg_90d_contacts |
| La0ef9034 | wrong: no column holds closed_within_12m (2 of 3 match) |
| La5545641 | wrong: 4 rows, not 9 |
| La6c932d6 | correct: matches on segment=customer_segment, callers=distinct_customers_called, contacts=total_calls |
| La7769de1 | wrong: 777 rows, not 36 |
| Laae51758 | correct: matches on fct_calls_queue_name=queue_name, fct_calls_abandon_rate=abandon_rate, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_transfers=transferred_calls |
| Laedcf94e | correct: matches on account_family, close_reason, n=closures |
| Laf86f8c8 | correct: matches on month_start, total_expense, payroll_expense, vendor_expense, site_name~site_id (relabeled) |
| Lb012a03c | correct: matches on conversation_date, abandon_rate |
| Lb04a395e | correct: matches on app_version, platform, sessions |
| Lb680ccfe | wrong: 3149 rows, not 2683 |
| Lb79256f9 | wrong: no column holds devices (3 of 4 match) |
| Lb7adf6c4 | correct: matches on grp=product_family, accounts=distinct_accounts, balance=total_ledger_balance |
| Lb8a36f12 | correct: matches on platform, customers=distinct_customers, avg_screens=avg_screens_per_session |
| Lb93bfbd1 | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_count=voice_conversation_count |
| Lb94b1361 | correct: matches on site_name, avg_cost_per_contact, closure_calls=total_closure_calls |
| Lba47b53e | correct: matches on customer_key, sessions=web_sessions, page_views=total_page_views, help_sessions |
| Lba494fec | empty: no rows |
| Lba99d5e4 | correct: matches on fct_calls_agent_name=agent_name, fct_calls_media_type=media_type, fct_calls_site_name=site_name, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_count=conver |
| Lbed96252 | correct: matches on WK, CUT=PRODUCT_CODE, APPS |
| Lc3266632 | correct: matches on digital_wallet, cut=card_role, cards=active_cards |
| Lc38c81cf | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_post_date=txn_date, fct_card_transacti |
| Lc3f3abff | correct: matches on wk=week_start, channel, sends |
| Lc9bd1a0b | wrong: 14 rows, not 98 |
| Lccd8d6b4 | correct: matches on fct_card_transactions_post_month=txn_month, fct_card_transactions_interchange=total_interchange, fct_card_transactions_txn_count=distinct_settlements |
| Lcd902824 | correct: matches on site_id, csat=avg_csat_score, net_promoters=net_promoter_count, surveys=survey_count |
| Lce8f8c9f | correct: matches on score_band=score_band_start, alerts, confirmed=confirmed_fraud |
| Lcf63b774 | correct: matches on fct_card_transactions_segment=segment, fct_card_transactions_cardholders=distinct_cardholders |
| Lcf746f33 | correct: matches on fct_calls_is_outsourced=is_outsourced, fct_calls_wrapup=wrapup_reason, fct_calls_avg_handle_time=avg_handle_time_sec, fct_calls_transfers=transferred_calls |
| Ld0463faf | correct: matches on party_type, risk_rating, parties=party_count |
| Ld49d2be4 | correct: matches on sends_per_customer=num_sends, customers=num_customers |
| Ld5366f8d | wrong: no column holds accounts_without_primary (0 of 1 match) |
| Ld63381a3 | wrong: 12 rows, not 9 |
| Ld9c8c1f0 | correct: matches on channel, cut=country, attempts=login_attempts |
| Ldb7eb3ce | correct: matches on rank_agreement=correlation, n=n_customers |
| Ldc0a459b | correct: matches on cif_number=customer_id, full_name, primary_email |
| Ldc27f830 | correct: matches on wk=week_start, channel, sends |
| Ldd1130d2 | correct: matches on page=page_location, views |
| Ldf5bcf3a | correct: matches on closure_calls, contacts=total_calls, site_id~site_name (relabeled) |
| Ldf622140 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_segment=customer_segment, fct_card_tra |
| Ldfe49bfa | correct: matches on segment=customer_segment, fee_type, net=total_net_fee_amount, gross=total_gross_fee_amount, waived=waived_fee_count |
| Le166be49 | correct: matches on month_start, site_id, contacts, closure_calls, aht_min=avg_handle_time_minutes |
| Le50954e7 | correct: matches on fct_calls_is_outsourced=is_outsourced, fct_calls_closure_calls=closure_calls |
| Le5559ed6 | correct: matches on channel=send_channel, conversion_behavior, conversions |
| Le59b2970 | correct: matches on fct_card_transactions_is_foreign=is_foreign_txn, fct_card_transactions_post_month=txn_month, fct_card_transactions_txn_type=txn_type, fct_card_transactions_txn_count= |
| Le6d5789b | wrong: no column holds closers_who_called (1 of 2 match) |
| Le85ab9f9 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_post_date=txn_date, fct_card_transactions_cardholders=cardholders |
| Le8c70805 | empty: no rows |
| Lea0a11f5 | correct: matches on unsubscribes, bounces, wk~event_week (relabeled) |
| Lea731b4b | correct: matches on m=txn_month, transaction_type, amount=total_amount |
| Leb26b397 | correct: matches on wk=week_start, csat=avg_csat_score, nps=avg_nps_score |
| Lecec1d54 | correct: matches on period=week, account_family, close_reason, closures |
| Led874c20 | correct: matches on fct_card_transactions_is_foreign=is_foreign, fct_card_transactions_mcc_category_group=mcc_category_group, fct_card_transactions_txn_type=txn_type, fct_card_transactio |
| Ledff3723 | correct: matches on fct_calls_conversation_date=conversation_date, fct_calls_count=call_count, fct_calls_avg_handle_time=avg_handle_time_sec |
| Lee760ebe | correct: matches on m=enrollment_month, enrollment_channel, enrollments |
| Leea58714 | correct: matches on FICO_BAND=fico_band, APPS=num_applications, APPROVAL_RATE=approval_rate |
| Leeca746a | correct: matches on rule_id, alerts=total_alerts, confirmed=confirmed_fraud_count, losses=total_loss_amount |
| Lef98f427 | correct: matches on month_start, total_expense, payroll_expense, vendor_expense, site_id~site_name (relabeled) |
| Lefe10343 | empty: no rows |
| Lf24da50d | wrong: no column holds sends (1 of 2 match) |
| Lf3aa1fe7 | correct: matches on fct_calls_wrapup=wrapup_code_name, fct_calls_count=conversation_count |
| Lf431cd40 | correct: matches on m=month, fraud_type, losses=total_loss_amount |
| Lf6331a08 | correct: matches on digital_wallet, cards=active_cards, customers=active_customers |
| Lfba52c1e | wrong: no column holds PERIOD_NAME (4 of 5 match) |
| Lff8ef74e | correct: matches on band=risk_score_band_start, logins=total_logins, failed=failed_logins |

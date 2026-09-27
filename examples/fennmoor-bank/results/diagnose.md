# Diagnosis: finding the tables, or writing the query?

The SQL route on each gold question scored by value, with the cohort navigation finds and with the answer key's own tables (expected and acceptable).

Correct: navigated 6 of 10, oracle tables 6 of 10.

| question | expected tables navigation missed | navigated | oracle tables |
|---|---|---|---|
| Q01 | fennmoor-dw.dw_contact_center.fct_contacts_all | empty: no rows | wrong: no column holds closure_contacts (2 of 3 match) |
| Q02 | fennmoor-dw.dw_customer.customer_360 | empty: no rows | wrong: no column holds customers (1 of 2 match) |
| Q04 | - | correct: matches on segment=customer_segment, mcc_category_group, spend=total_spend | correct: matches on segment=customer_segment, mcc_category_group=merchant_category, spend=total_spend |
| Q05 | - | correct: matches on month=month_start, product_line, month_end_balance | correct: matches on month=month_start, product_line, month_end_balance=deposit_balance |
| Q07 | - | correct: matches on channel, confirmed_share=confirm_rate | correct: matches on channel, confirmed_share=confirm_rate |
| Q08 | - | correct: matches on campaign_name, card_applications | correct: matches on campaign_name, card_applications=card_applications_attributed |
| Q09 | - | wrong: no column holds delinquency_rate (2 of 3 match) | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q11 | - | correct: matches on week=week_start, customers=mobile_app_customers | correct: matches on week=week_start, customers |
| Q12 | - | wrong: 1149 rows, not 1566 | wrong: 1149 rows, not 1566 |
| Q14 | - | correct: matches on account_family, closures | correct: matches on account_family, closures |

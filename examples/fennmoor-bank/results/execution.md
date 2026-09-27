# Execution accuracy

Each gold question through `qlsc ask`, by both routes, against its reference answer (`results/answers.md`). **correct** = the same rows on the columns the reference compares; **not covered** = none of the cohort's tables is in the virtual graph.

| route | correct | wrong | empty | failed | not covered | of scored |
|---|---|---|---|---|---|---|
| sql | 6 | 2 | 2 | 0 | 0 | 10 |
| cypher | 3 | 4 | 1 | 1 | 1 | 10 |

Either route correct (an oracle router's score): 7 of 10.

| question | sql | cypher |
|---|---|---|
| Q01. Which contact centers see the most account cancellations, and what did each cost to run last year? | empty: no rows | empty: no rows |
| Q02. What is the churn risk of our high-balance customers? | empty: no rows | failed: 42NG1: Unsupported syntax: `Aggregating WITH clause is not supported`. (line 3, column 1 (offset: 108)) |
| Q03. Which web pages do customers visit before they call us? | not scored: 15 rows | not scored: 50 rows |
| Q04. Card spend by merchant category and customer segment, last quarter. | correct: matches on segment=customer_segment, mcc_category_group, spend=total_spend | correct: matches on segment, mcc_category_group, spend=total_spend |
| Q05. Month-end deposit balances by product line. | correct: matches on month=month_start, product_line, month_end_balance | wrong: 1 rows, not 12 |
| Q06. Where do we store Social Security numbers, raw or hashed? | not scored: 6 rows | not scored: 100 rows |
| Q07. What share of fraud alerts are confirmed fraud, by channel? | correct: matches on channel, confirmed_share=confirm_rate | not covered: none of the cohort's tables is in the virtual graph |
| Q08. Which marketing campaigns drove credit card applications? | correct: matches on campaign_name, card_applications | wrong: 1 rows, not 5200 |
| Q09. Loan delinquency rate by product and branch. | wrong: no column holds delinquency_rate (2 of 3 match) | wrong: no column holds delinquency_rate (2 of 3 match) |
| Q10. Does customer satisfaction vary with agent tenure? | not scored: 3 rows | not scored: 3 rows |
| Q11. How many customers use the mobile app each week? | correct: matches on week=week_start, customers=mobile_app_customers | wrong: 1 rows, not 14 |
| Q12. Contact details for an email campaign to affluent customers. | wrong: 1149 rows, not 1566 | correct: matches on cif_number (as Q12.alt) |
| Q13. What is in the tables whose names start with CC? | not scored: 41 rows | not scored: 3 rows |
| Q14. Account closures by reason, deposits versus cards. | correct: matches on account_family, closures | correct: matches on account_family, closures=n |

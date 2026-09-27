# Execution accuracy

Each gold question through `qlsc ask`, by both routes, against its reference answer (`results/answers.md`). **correct** = the same rows on the columns the reference compares; **not covered** = none of the cohort's tables is in the virtual graph.

| route | correct | wrong | empty | failed | not covered | of scored |
|---|---|---|---|---|---|---|
| sql | 6 | 2 | 2 | 0 | 0 | 10 |
| cypher | 3 | 1 | 2 | 3 | 1 | 10 |

Either route correct (an oracle router's score): 7 of 10.

| question | sql | cypher |
|---|---|---|
| Q01. Which contact centers see the most account cancellations, and what did each cost to run last year? | empty: no rows | empty: no rows |
| Q02. What is the churn risk of our high-balance customers? | empty: no rows | failed: unknown properties: a.current_balance (Account has no current_balance) |
| Q03. Which web pages do customers visit before they call us? | not scored: 15 rows | not scored: 1 rows |
| Q04. Card spend by merchant category and customer segment, last quarter. | correct: matches on segment=customer_segment, mcc_category_group, spend=total_spend | correct: matches on segment, mcc_category_group, spend=total_spend |
| Q05. Month-end deposit balances by product line. | correct: matches on month=month_start, product_line, month_end_balance | failed: 42NG1: Unsupported syntax: `Aggregating WITH clause is not supported`. (line 3, column 1 (offset: 175)) |
| Q06. Where do we store Social Security numbers, raw or hashed? | not scored: 6 rows | not scored: 25 rows |
| Q07. What share of fraud alerts are confirmed fraud, by channel? | correct: matches on channel, confirmed_share=confirm_rate | not covered: none of the cohort's tables is in the virtual graph |
| Q08. Which marketing campaigns drove credit card applications? | correct: matches on campaign_name, card_applications | empty: no rows |
| Q09. Loan delinquency rate by product and branch. | wrong: no column holds delinquency_rate (2 of 3 match) | correct: matches on product_code=productCode, branch_name=branchName, delinquency_rate=delinquentLoans |
| Q10. Does customer satisfaction vary with agent tenure? | not scored: 3 rows | not scored: 3 rows |
| Q11. How many customers use the mobile app each week? | correct: matches on week=week_start, customers=mobile_app_customers | failed: Invalid input 'UNKNOWN': expected 'ALTER', 'ORDER BY', 'CALL', 'CREATE', 'LOAD CSV', 'START DATABASE', 'STOP DATABASE', 'DEALLOCATE', 'DELETE', 'DENY', 'DETACH' |
| Q12. Contact details for an email campaign to affluent customers. | wrong: 1149 rows, not 1566 | wrong: 1149 rows, not 1566 |
| Q13. What is in the tables whose names start with CC? | not scored: 41 rows | not scored: 3 rows |
| Q14. Account closures by reason, deposits versus cards. | correct: matches on account_family, closures | correct: matches on account_family, closures=n |

# Graph-shaped questions

10 hand-written questions natural over the virtual graph (`eval/graph_questions.yaml`), through `qlsc ask` by both routes. Directional: ten questions.

| route | correct | wrong | empty | failed | declined | not covered | of |
|---|---|---|---|---|---|---|---|
| sql | 5 | 3 | 2 | 0 | 0 | 0 | 10 |
| cypher | 8 | 2 | 0 | 0 | 0 | 0 | 10 |
| routed | 7 | 3 | 0 | 0 | | | 10 |

| question | sql | cypher |
|---|---|---|
| G01. What accounts does customer 0001000025 hold? For each, the product name and the name of the branch it is maintained at. | wrong: 15 rows, not 16 | correct: matches on account_key, product_name, branch_name |
| G02. Which agents handled calls from customer 0001000025, and how many of that customer's calls did each handle? | wrong: 76 rows, not 78 | correct: matches on agent_user_id, calls=call_count |
| G03. Which merchants has customer 0001000025 bought from that customer 0001000021 has also bought from? | correct: matches on merchant_id | wrong: 265 rows, not 191 |
| G04. Customers who bought at Main Street Pharmacy (merchant MID000100000) bank at which branches? Count the distinct customers by the name of the branch where their accounts are maintained. | empty: no rows | wrong: no column holds customers (1 of 2 match) |
| G05. For calls from private-segment customers, which queues were they routed through and which sites serviced them? Count the calls by queue name and site name. | wrong: 258 rows, not 257 | correct: matches on queue_name, site_name, calls |
| G06. Which other agents also handled calls from the customers that agent 9143e7f7-8e11-6904-c98e-fb076ea611a1 served? For each other agent, how many of those customers they share. | correct: matches on agent_user_id, shared_customers | correct: matches on agent_user_id=other_agent_id, shared_customers |
| G07. For customers who called the Tulsa Contact Center, which product lines do their accounts belong to? Count distinct customers by product line. | empty: no rows | correct: matches on product_line, customers |
| G08. For all deposit transactions, of every type, on accounts owned by affluent customers, what is the total transaction amount by the product line of the account? | correct: matches on product_line, total_amount=total_transaction_amount | correct: matches on product_line, total_amount |
| G09. Customers who made card purchases at Main Street Pharmacy (merchant MID000100000) and also called the contact center about closing an account — how many are there, by customer segment? | correct: matches on segment=customer_segment, customers | correct: matches on segment, customers |
| G10. For card purchases made by customer 0001000025, which merchants were they at, and on which of the customer's accounts were they charged? Give the merchant name, the account's product name and the number of purchases. | correct: matches on merchant_name, product_name, purchases | correct: matches on merchant_name, product_name, purchases |

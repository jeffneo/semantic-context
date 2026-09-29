# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** each customer's context is fetched once. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 49 of 49 compiled questions; 49 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.027 s, p95 0.072 s. The SQL's: median 0.795 s, p95 1.369 s.
- **The session's query time:** 42.5 s without memory, 29.6 s with it (5 context fetches included).
- **The session's bytes billed:** 2,104 MiB without memory, 2,934 MiB with it (the fetches included, a median 606 MiB each; 142 jobs, 0 answered by BigQuery's result cache).
- **Compiling a question** (common to both): median 7.72 s.

Why a question didn't go to memory:

- (every compiled question did)

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -9209255889542210479 | How many accounts does the customer with customer_key … hold, by product line? | 1.387 | 20 | 42 | yes |
| -9209255889542210479 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.795 | 70 | 28 | yes |
| -9209255889542210479 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.856 | 93 | 88 | yes |
| -9209255889542210479 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.251 | 99 | 45 | yes |
| -9209255889542210479 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.729 | 20 | 70 | yes |
| -9209255889542210479 | Calls from the customer with customer_key … last quarter, by contact center site | 1.014 | 20 | 28 | yes |
| -9209255889542210479 | Total card spend of the customer with customer_key … in June 2026 | 0.633 | 18 | 26 | yes |
| -9209255889542210479 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.541 | 20 | 23 | yes |
| -9209255889542210479 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.063 | 10 | 22 | yes |
| -9209255889542210479 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.806 | 83 | 22 | yes |
| -9204744811355892139 | How many accounts does the customer with customer_key … hold, by product line? | 0.643 | 20 | 22 | yes |
| -9204744811355892139 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.986 | 70 | 23 | yes |
| -9204744811355892139 | Number of card purchases by merchant for the customer with customer_key …, last quarter | - | - | - | - |
| -9204744811355892139 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.842 | 99 | 22 | yes |
| -9204744811355892139 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.608 | 10 | 22 | yes |
| -9204744811355892139 | Calls from the customer with customer_key … last quarter, by contact center site | 0.993 | 20 | 32 | yes |
| -9204744811355892139 | Total card spend of the customer with customer_key … in June 2026 | 0.647 | 18 | 33 | yes |
| -9204744811355892139 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.815 | 20 | 25 | yes |
| -9204744811355892139 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.73 | 10 | 28 | yes |
| -9204744811355892139 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.992 | 83 | 78 | yes |
| -9203156349125013757 | How many accounts does the customer with customer_key … hold, by product line? | 0.798 | 20 | 30 | yes |
| -9203156349125013757 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.765 | 70 | 56 | yes |
| -9203156349125013757 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.925 | 55 | 43 | yes |
| -9203156349125013757 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.903 | 99 | 22 | yes |
| -9203156349125013757 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.569 | 10 | 32 | yes |
| -9203156349125013757 | Calls from the customer with customer_key … last quarter, by contact center site | 2.404 | 20 | 23 | yes |
| -9203156349125013757 | Total card spend of the customer with customer_key … in June 2026 | 1.338 | 18 | 22 | yes |
| -9203156349125013757 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.682 | 20 | 24 | yes |
| -9203156349125013757 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.768 | 10 | 34 | yes |
| -9203156349125013757 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.098 | 83 | 72 | yes |
| -9201348598340979897 | How many accounts does the customer with customer_key … hold, by product line? | 0.597 | 20 | 26 | yes |
| -9201348598340979897 | Card spend by merchant category for the customer with customer_key …, last quarter | 1.061 | 70 | 25 | yes |
| -9201348598340979897 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.959 | 93 | 24 | yes |
| -9201348598340979897 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.369 | 99 | 27 | yes |
| -9201348598340979897 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.796 | 20 | 25 | yes |
| -9201348598340979897 | Calls from the customer with customer_key … last quarter, by contact center site | 0.735 | 20 | 24 | yes |
| -9201348598340979897 | Total card spend of the customer with customer_key … in June 2026 | 0.636 | 18 | 22 | yes |
| -9201348598340979897 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.585 | 20 | 20 | yes |
| -9201348598340979897 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.695 | 10 | 20 | yes |
| -9201348598340979897 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.727 | 83 | 55 | yes |
| -9200277586793693173 | How many accounts does the customer with customer_key … hold, by product line? | 0.657 | 20 | 23 | yes |
| -9200277586793693173 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.68 | 70 | 41 | yes |
| -9200277586793693173 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.696 | 93 | 50 | yes |
| -9200277586793693173 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.81 | 99 | 46 | yes |
| -9200277586793693173 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.734 | 10 | 22 | yes |
| -9200277586793693173 | Calls from the customer with customer_key … last quarter, by contact center site | 0.756 | 20 | 46 | yes |
| -9200277586793693173 | Total card spend of the customer with customer_key … in June 2026 | 0.6 | 18 | 27 | yes |
| -9200277586793693173 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 1.114 | 20 | 23 | yes |
| -9200277586793693173 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.762 | 10 | 34 | yes |
| -9200277586793693173 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.924 | 83 | 66 | yes |

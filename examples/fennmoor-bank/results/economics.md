# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** the 5 customers' contexts are fetched together, in one batch. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 48 of 49 compiled questions; 48 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.044 s, p95 0.095 s. The SQL's: median 0.782 s, p95 1.47 s.
- **The session's query time:** 42.6 s without memory, 7.7 s with it (the batch fetch included).
- **The session's bytes billed:** 2,078 MiB without memory, 620 MiB with it (the batch fetch included).
- **Compiling a question** (common to both): median 7.46 s.

## What a fetch costs, per customer (a question's SQL bills 42 MiB on average)

| fetched | customers | seconds | MiB billed | MiB per customer | break-even: questions per customer | jobs | cached | not reported |
|---|---|---|---|---|---|---|---|---|
| one at a time | 5 | 15.0 | 2,800 | 560 | 13.2 | 56 | 10 | 10 |
| a batch of 5 (the session's) | 5 | 4.7 | 620 | 124 | 2.9 | 14 | 1 | 2 |
| a batch of 50 | 50 | 15.0 | 633 | 13 | 0.3 | 18 | 1 | 2 |

A job BigQuery answered from its result cache (a dimension read whose keys recur), or whose bytes it didn't report (it reads a row-policied table), is counted at the minimum a first read bills: 10 MiB per table it references. 0 of the questions' SQL jobs weren't reported.

Why a question didn't go to memory:

- it reads a table memory doesn't hold for this reader

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -8864593635057074308 | How many accounts does the customer with customer_key … hold, by product line? | 1.624 | 20 | 58 | yes |
| -8864593635057074308 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.703 | 70 | 135 | yes |
| -8864593635057074308 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.837 | 93 | 82 | yes |
| -8864593635057074308 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.782 | 99 | 95 | yes |
| -8864593635057074308 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.764 | 10 | 21 | yes |
| -8864593635057074308 | Calls from the customer with customer_key … last quarter, by contact center site | 0.806 | 20 | 24 | yes |
| -8864593635057074308 | Total card spend of the customer with customer_key … in June 2026 | 0.74 | 18 | 63 | yes |
| -8864593635057074308 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.688 | 20 | 41 | yes |
| -8864593635057074308 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.616 | 10 | 28 | yes |
| -8864593635057074308 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.986 | 85 | 61 | yes |
| -8863959794512937727 | How many accounts does the customer with customer_key … hold, by product line? | 0.723 | 0 | - | - |
| -8863959794512937727 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.971 | 70 | 110 | yes |
| -8863959794512937727 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.872 | 55 | 70 | yes |
| -8863959794512937727 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.47 | 99 | 54 | yes |
| -8863959794512937727 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.831 | 10 | 50 | yes |
| -8863959794512937727 | Calls from the customer with customer_key … last quarter, by contact center site | 1.088 | 20 | 19 | yes |
| -8863959794512937727 | Total card spend of the customer with customer_key … in June 2026 | 0.683 | 18 | 56 | yes |
| -8863959794512937727 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.698 | 20 | 22 | yes |
| -8863959794512937727 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.681 | 10 | 22 | yes |
| -8863959794512937727 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.194 | 83 | 81 | yes |
| -8862237541954954756 | How many accounts does the customer with customer_key … hold, by product line? | 0.708 | 20 | 23 | yes |
| -8862237541954954756 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.743 | 70 | 86 | yes |
| -8862237541954954756 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 1.142 | 93 | 49 | yes |
| -8862237541954954756 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.155 | 99 | 28 | yes |
| -8862237541954954756 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.792 | 10 | 18 | yes |
| -8862237541954954756 | Calls from the customer with customer_key … last quarter, by contact center site | 0.691 | 20 | 19 | yes |
| -8862237541954954756 | Total card spend of the customer with customer_key … in June 2026 | 0.759 | 18 | 64 | yes |
| -8862237541954954756 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.824 | 20 | 70 | yes |
| -8862237541954954756 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.592 | 10 | 21 | yes |
| -8862237541954954756 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.638 | 83 | 39 | yes |
| -8853488810474542660 | How many accounts does the customer with customer_key … hold, by product line? | 1.007 | 20 | 39 | yes |
| -8853488810474542660 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.73 | 70 | 56 | yes |
| -8853488810474542660 | Number of card purchases by merchant for the customer with customer_key …, last quarter | - | - | - | - |
| -8853488810474542660 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.932 | 99 | 33 | yes |
| -8853488810474542660 | How many calls did the customer with customer_key … make last quarter, by queue? | 2.256 | 10 | 17 | yes |
| -8853488810474542660 | Calls from the customer with customer_key … last quarter, by contact center site | 0.756 | 20 | 54 | yes |
| -8853488810474542660 | Total card spend of the customer with customer_key … in June 2026 | 0.639 | 18 | 47 | yes |
| -8853488810474542660 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.627 | 20 | 63 | yes |
| -8853488810474542660 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.847 | 10 | 23 | yes |
| -8853488810474542660 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.749 | 85 | 63 | yes |
| -8852658124648369036 | How many accounts does the customer with customer_key … hold, by product line? | 0.649 | 20 | 17 | yes |
| -8852658124648369036 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.824 | 70 | 48 | yes |
| -8852658124648369036 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.731 | 93 | 84 | yes |
| -8852658124648369036 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.982 | 99 | 32 | yes |
| -8852658124648369036 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.896 | 20 | 25 | yes |
| -8852658124648369036 | Calls from the customer with customer_key … last quarter, by contact center site | 0.865 | 20 | 25 | yes |
| -8852658124648369036 | Total card spend of the customer with customer_key … in June 2026 | 0.74 | 18 | 36 | yes |
| -8852658124648369036 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.593 | 20 | 21 | yes |
| -8852658124648369036 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.928 | 10 | 23 | yes |
| -8852658124648369036 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.999 | 83 | 55 | yes |

# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** the 5 customers' contexts are fetched together, in one batch. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 50 of 50 compiled questions; 50 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.045 s, p95 0.079 s. The SQL's: median 0.709 s, p95 1.278 s.
- **The session's query time:** 40.4 s without memory, 7.6 s with it (the batch fetch included).
- **The session's bytes billed:** 2,128 MiB without memory, 605 MiB with it (the batch fetch included).
- **Compiling a question** (common to both): median 7.83 s.

## What a fetch costs, per customer (a question's SQL bills 43 MiB on average)

| fetched | customers | seconds | MiB billed | MiB per customer | break-even: questions per customer | jobs | cached | not reported |
|---|---|---|---|---|---|---|---|---|
| one at a time | 5 | 19.5 | 2,705 | 541 | 12.7 | 49 | 10 | 5 |
| a batch of 5 (the session's) | 5 | 5.3 | 605 | 121 | 2.8 | 13 | 1 | 1 |
| a batch of 50 | 50 | 15.0 | 613 | 12 | 0.3 | 17 | 1 | 1 |

A job BigQuery answered from its result cache (a dimension read whose keys recur), or whose bytes it didn't report (it reads a row-policied table), is counted at the minimum a first read bills: 10 MiB per table it references. 0 of the questions' SQL jobs weren't reported.

Why a question didn't go to memory:

- (every compiled question did)

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -8184759929530132369 | How many accounts does the customer with customer_key … hold, by product line? | 1.252 | 20 | 79 | yes |
| -8184759929530132369 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.674 | 71 | 74 | yes |
| -8184759929530132369 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.763 | 55 | 54 | yes |
| -8184759929530132369 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.688 | 100 | 26 | yes |
| -8184759929530132369 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.703 | 10 | 44 | yes |
| -8184759929530132369 | Calls from the customer with customer_key … last quarter, by contact center site | 0.85 | 20 | 80 | yes |
| -8184759929530132369 | Total card spend of the customer with customer_key … in June 2026 | 0.624 | 19 | 62 | yes |
| -8184759929530132369 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.557 | 20 | 48 | yes |
| -8184759929530132369 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.278 | 10 | 58 | yes |
| -8184759929530132369 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.768 | 84 | 68 | yes |
| -8184693656158152476 | How many accounts does the customer with customer_key … hold, by product line? | 0.631 | 20 | 82 | yes |
| -8184693656158152476 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.724 | 71 | 57 | yes |
| -8184693656158152476 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.808 | 55 | 60 | yes |
| -8184693656158152476 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.276 | 100 | 24 | yes |
| -8184693656158152476 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.637 | 10 | 20 | yes |
| -8184693656158152476 | Calls from the customer with customer_key … last quarter, by contact center site | 0.656 | 20 | 23 | yes |
| -8184693656158152476 | Total card spend of the customer with customer_key … in June 2026 | 0.669 | 19 | 22 | yes |
| -8184693656158152476 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.689 | 20 | 56 | yes |
| -8184693656158152476 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.754 | 10 | 49 | yes |
| -8184693656158152476 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.96 | 126 | 63 | yes |
| -8180704299001469721 | How many accounts does the customer with customer_key … hold, by product line? | 0.618 | 20 | 24 | yes |
| -8180704299001469721 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.777 | 71 | 34 | yes |
| -8180704299001469721 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.706 | 55 | 66 | yes |
| -8180704299001469721 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.022 | 100 | 22 | yes |
| -8180704299001469721 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.637 | 10 | 33 | yes |
| -8180704299001469721 | Calls from the customer with customer_key … last quarter, by contact center site | 0.692 | 20 | 70 | yes |
| -8180704299001469721 | Total card spend of the customer with customer_key … in June 2026 | 0.617 | 19 | 23 | yes |
| -8180704299001469721 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.676 | 20 | 74 | yes |
| -8180704299001469721 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.157 | 10 | 61 | yes |
| -8180704299001469721 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.927 | 84 | 66 | yes |
| -8176191375513896444 | How many accounts does the customer with customer_key … hold, by product line? | 0.534 | 20 | 23 | yes |
| -8176191375513896444 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.654 | 71 | 25 | yes |
| -8176191375513896444 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.859 | 55 | 46 | yes |
| -8176191375513896444 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.712 | 100 | 22 | yes |
| -8176191375513896444 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.762 | 10 | 49 | yes |
| -8176191375513896444 | Calls from the customer with customer_key … last quarter, by contact center site | 0.626 | 20 | 30 | yes |
| -8176191375513896444 | Total card spend of the customer with customer_key … in June 2026 | 0.705 | 19 | 20 | yes |
| -8176191375513896444 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.727 | 20 | 24 | yes |
| -8176191375513896444 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.627 | 10 | 21 | yes |
| -8176191375513896444 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.377 | 84 | 66 | yes |
| -8167080191698440242 | How many accounts does the customer with customer_key … hold, by product line? | 0.818 | 20 | 22 | yes |
| -8167080191698440242 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.698 | 71 | 31 | yes |
| -8167080191698440242 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.648 | 94 | 65 | yes |
| -8167080191698440242 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.13 | 100 | 32 | yes |
| -8167080191698440242 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.674 | 10 | 23 | yes |
| -8167080191698440242 | Calls from the customer with customer_key … last quarter, by contact center site | 0.724 | 20 | 27 | yes |
| -8167080191698440242 | Total card spend of the customer with customer_key … in June 2026 | 0.872 | 19 | 25 | yes |
| -8167080191698440242 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.774 | 20 | 59 | yes |
| -8167080191698440242 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.692 | 10 | 24 | yes |
| -8167080191698440242 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.014 | 86 | 64 | yes |

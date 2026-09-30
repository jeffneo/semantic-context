# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** the 5 customers' contexts are fetched together, in one batch. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 49 of 49 compiled questions; 49 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.052 s, p95 0.085 s. The SQL's: median 0.861 s, p95 1.329 s.
- **The session's query time:** 44.0 s without memory, 7.7 s with it (the batch fetch included).
- **The session's bytes billed:** 2,096 MiB without memory, 583 MiB with it (the batch fetch included).
- **Compiling a question** (common to both): median 7.505 s.

## What a fetch costs, per customer (a question's SQL bills 43 MiB on average)

| fetched | customers | seconds | MiB billed | MiB per customer | break-even: questions per customer | jobs | cached | not reported |
|---|---|---|---|---|---|---|---|---|
| one at a time | 5 | 18.8 | 2,885 | 577 | 13.5 | 62 | 9 | 10 |
| a batch of 5 (the session's) | 5 | 5.0 | 583 | 117 | 2.7 | 13 | 1 | 2 |
| a batch of 50 | 50 | 17.5 | 633 | 13 | 0.3 | 18 | 1 | 2 |

A job BigQuery answered from its result cache (a dimension read whose keys recur), or whose bytes it didn't report (it reads a row-policied table), is counted at the minimum a first read bills: 10 MiB per table it references. 0 of the questions' SQL jobs weren't reported.

Why a question didn't go to memory:

- (every compiled question did)

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -8698917731471622356 | How many accounts does the customer with customer_key … hold, by product line? | 1.329 | 20 | 82 | yes |
| -8698917731471622356 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.921 | 71 | 111 | yes |
| -8698917731471622356 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.871 | 55 | 78 | yes |
| -8698917731471622356 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.681 | 100 | 38 | yes |
| -8698917731471622356 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.811 | 10 | 44 | yes |
| -8698917731471622356 | Calls from the customer with customer_key … last quarter, by contact center site | 0.976 | 20 | 68 | yes |
| -8698917731471622356 | Total card spend of the customer with customer_key … in June 2026 | 0.572 | 19 | 85 | yes |
| -8698917731471622356 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 1.098 | 20 | 57 | yes |
| -8698917731471622356 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.864 | 10 | 51 | yes |
| -8698917731471622356 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.835 | 126 | 77 | yes |
| -8693743404495887281 | How many accounts does the customer with customer_key … hold, by product line? | 0.586 | 20 | 68 | yes |
| -8693743404495887281 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.881 | 71 | 82 | yes |
| -8693743404495887281 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.79 | 55 | 75 | yes |
| -8693743404495887281 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.031 | 100 | 46 | yes |
| -8693743404495887281 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.802 | 10 | 22 | yes |
| -8693743404495887281 | Calls from the customer with customer_key … last quarter, by contact center site | 0.78 | 20 | 83 | yes |
| -8693743404495887281 | Total card spend of the customer with customer_key … in June 2026 | 0.734 | 19 | 85 | yes |
| -8693743404495887281 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.861 | 20 | 61 | yes |
| -8693743404495887281 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.964 | 10 | 21 | yes |
| -8693743404495887281 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.865 | 84 | 77 | yes |
| -8689411027624036127 | How many accounts does the customer with customer_key … hold, by product line? | 0.596 | 20 | 22 | yes |
| -8689411027624036127 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.833 | 71 | 66 | yes |
| -8689411027624036127 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.836 | 55 | 75 | yes |
| -8689411027624036127 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.044 | 100 | 37 | yes |
| -8689411027624036127 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.93 | 10 | 51 | yes |
| -8689411027624036127 | Calls from the customer with customer_key … last quarter, by contact center site | 0.798 | 20 | 36 | yes |
| -8689411027624036127 | Total card spend of the customer with customer_key … in June 2026 | 0.715 | 19 | 48 | yes |
| -8689411027624036127 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.778 | 20 | 48 | yes |
| -8689411027624036127 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.01 | 10 | 22 | yes |
| -8689411027624036127 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.554 | 84 | 67 | yes |
| -8685410779539150475 | How many accounts does the customer with customer_key … hold, by product line? | 0.685 | 20 | 35 | yes |
| -8685410779539150475 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.886 | 71 | 81 | yes |
| -8685410779539150475 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 1.076 | 55 | 70 | yes |
| -8685410779539150475 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.767 | 100 | 36 | yes |
| -8685410779539150475 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.753 | 20 | 58 | yes |
| -8685410779539150475 | Calls from the customer with customer_key … last quarter, by contact center site | 1.069 | 20 | 30 | yes |
| -8685410779539150475 | Total card spend of the customer with customer_key … in June 2026 | 0.658 | 19 | 52 | yes |
| -8685410779539150475 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.704 | 20 | 37 | yes |
| -8685410779539150475 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.906 | 10 | 44 | yes |
| -8685410779539150475 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.746 | 128 | 86 | yes |
| -8684472241523961282 | How many accounts does the customer with customer_key … hold, by product line? | 0.675 | 20 | 34 | yes |
| -8684472241523961282 | Card spend by merchant category for the customer with customer_key …, last quarter | 1.326 | 71 | 67 | yes |
| -8684472241523961282 | Number of card purchases by merchant for the customer with customer_key …, last quarter | - | - | - | - |
| -8684472241523961282 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.94 | 100 | 38 | yes |
| -8684472241523961282 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.954 | 20 | 23 | yes |
| -8684472241523961282 | Calls from the customer with customer_key … last quarter, by contact center site | 1.081 | 20 | 23 | yes |
| -8684472241523961282 | Total card spend of the customer with customer_key … in June 2026 | 0.64 | 19 | 46 | yes |
| -8684472241523961282 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.645 | 20 | 57 | yes |
| -8684472241523961282 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.813 | 10 | 26 | yes |
| -8684472241523961282 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.296 | 84 | 80 | yes |

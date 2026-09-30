# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** the 5 customers' contexts are fetched together, in one batch. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 50 of 50 compiled questions; 50 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.031 s, p95 0.075 s. The SQL's: median 0.815 s, p95 1.711 s.
- **The session's query time:** 45.0 s without memory, 8.0 s with it (the batch fetch included).
- **The session's bytes billed:** 2,263 MiB without memory, 563 MiB with it (the batch fetch included).
- **Compiling a question** (common to both): median 7.52 s.

## What a fetch costs, per customer (a question's SQL bills 45 MiB on average)

| fetched | customers | seconds | MiB billed | MiB per customer | break-even: questions per customer | jobs | cached | not reported |
|---|---|---|---|---|---|---|---|---|
| one at a time | 5 | 30.6 | 2,795 | 559 | 12.4 | 58 | 9 | 5 |
| a batch of 5 (the session's) | 5 | 6.0 | 563 | 113 | 2.5 | 12 | 1 | 1 |
| a batch of 50 | 50 | 19.3 | 613 | 12 | 0.3 | 17 | 2 | 1 |

A job BigQuery answered from its result cache (a dimension read whose keys recur), or whose bytes it didn't report (it reads a row-policied table), is counted at the minimum a first read bills: 10 MiB per table it references. 0 of the questions' SQL jobs weren't reported.

Why a question didn't go to memory:

- (every compiled question did)

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -8522553548344015653 | How many accounts does the customer with customer_key … hold, by product line? | 1.298 | 20 | 80 | yes |
| -8522553548344015653 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.875 | 71 | 72 | yes |
| -8522553548344015653 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 1.865 | 94 | 46 | yes |
| -8522553548344015653 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.086 | 100 | 22 | yes |
| -8522553548344015653 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.965 | 20 | 58 | yes |
| -8522553548344015653 | Calls from the customer with customer_key … last quarter, by contact center site | 0.838 | 20 | 50 | yes |
| -8522553548344015653 | Total card spend of the customer with customer_key … in June 2026 | 0.805 | 19 | 47 | yes |
| -8522553548344015653 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 1.112 | 20 | 52 | yes |
| -8522553548344015653 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.738 | 10 | 51 | yes |
| -8522553548344015653 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.813 | 84 | 86 | yes |
| -8516827658002167965 | How many accounts does the customer with customer_key … hold, by product line? | 0.684 | 20 | 22 | yes |
| -8516827658002167965 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.915 | 71 | 28 | yes |
| -8516827658002167965 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.774 | 55 | 49 | yes |
| -8516827658002167965 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.665 | 100 | 26 | yes |
| -8516827658002167965 | How many calls did the customer with customer_key … make last quarter, by queue? | 1.711 | 10 | 70 | yes |
| -8516827658002167965 | Calls from the customer with customer_key … last quarter, by contact center site | 0.83 | 20 | 27 | yes |
| -8516827658002167965 | Total card spend of the customer with customer_key … in June 2026 | 0.666 | 19 | 28 | yes |
| -8516827658002167965 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.677 | 20 | 60 | yes |
| -8516827658002167965 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.804 | 10 | 21 | yes |
| -8516827658002167965 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.05 | 84 | 64 | yes |
| -8515986546922041322 | How many accounts does the customer with customer_key … hold, by product line? | 0.683 | 20 | 74 | yes |
| -8515986546922041322 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.882 | 71 | 55 | yes |
| -8515986546922041322 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.725 | 94 | 54 | yes |
| -8515986546922041322 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.681 | 100 | 20 | yes |
| -8515986546922041322 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.817 | 10 | 44 | yes |
| -8515986546922041322 | Calls from the customer with customer_key … last quarter, by contact center site | 0.941 | 20 | 63 | yes |
| -8515986546922041322 | Total card spend of the customer with customer_key … in June 2026 | 0.84 | 19 | 25 | yes |
| -8515986546922041322 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.647 | 20 | 21 | yes |
| -8515986546922041322 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.79 | 10 | 21 | yes |
| -8515986546922041322 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.81 | 126 | 66 | yes |
| -8510083905847458547 | How many accounts does the customer with customer_key … hold, by product line? | 0.612 | 20 | 22 | yes |
| -8510083905847458547 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.693 | 71 | 28 | yes |
| -8510083905847458547 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.664 | 94 | 29 | yes |
| -8510083905847458547 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.724 | 100 | 30 | yes |
| -8510083905847458547 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.718 | 20 | 22 | yes |
| -8510083905847458547 | Calls from the customer with customer_key … last quarter, by contact center site | 0.836 | 20 | 28 | yes |
| -8510083905847458547 | Total card spend of the customer with customer_key … in June 2026 | 0.67 | 19 | 20 | yes |
| -8510083905847458547 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.691 | 20 | 64 | yes |
| -8510083905847458547 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.807 | 10 | 20 | yes |
| -8510083905847458547 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.088 | 84 | 24 | yes |
| -8506285815963027694 | How many accounts does the customer with customer_key … hold, by product line? | 0.989 | 20 | 31 | yes |
| -8506285815963027694 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.853 | 71 | 34 | yes |
| -8506285815963027694 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.738 | 94 | 75 | yes |
| -8506285815963027694 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.618 | 100 | 44 | yes |
| -8506285815963027694 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.875 | 10 | 49 | yes |
| -8506285815963027694 | Calls from the customer with customer_key … last quarter, by contact center site | 0.9 | 20 | 25 | yes |
| -8506285815963027694 | Total card spend of the customer with customer_key … in June 2026 | 0.7 | 19 | 22 | yes |
| -8506285815963027694 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.596 | 20 | 20 | yes |
| -8506285815963027694 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.932 | 10 | 16 | yes |
| -8506285815963027694 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.302 | 84 | 21 | yes |

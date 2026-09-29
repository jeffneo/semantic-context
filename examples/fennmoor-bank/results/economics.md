# Memory's economics: a simulated session, with and without memory

Check 2 of plans/2026-09-27-agentic-memory.md (phase 5): 50 questions, 10 about each of 5 customers, as the data source.

- **Without memory,** each question's compiled SQL runs in BigQuery (its cache off, as a first-time query).
- **With memory,** each customer's context is fetched once. Each question then goes to memory when the router's memory route finds memory holds its whole answer, and to the same SQL otherwise.

Compiling a question (the LLM's typed request) is common to both, so it's reported apart.

- **Answered from memory:** 49 of 49 compiled questions; 49 of them gave the same rows as the SQL.
- **Latency, from memory:** median 0.028 s, p95 0.06 s. The SQL's: median 0.909 s, p95 1.724 s.
- **The session's query time:** 47.3 s without memory, 22.1 s with it (5 context fetches included).
- **The session's bytes billed:** 2,183 MiB without memory, 2,807 MiB with it (the fetches included, a median 557 MiB each; 57 jobs; 11 answered by BigQuery's result cache, counted at the minimum a first read bills).
- **Break-even:** a fetch bills what 12.5 questions' SQL does (a question bills 45 MiB on average).
- **Bytes BigQuery didn't report:** 10 of the fetches' jobs and 0 of the questions' read a row-policied table, and are counted at BigQuery's minimum (10 MiB per table referenced).
- **Compiling a question** (common to both): median 7.855 s.

Why a question didn't go to memory:

- (every compiled question did)

| customer | question | SQL s | MiB billed | memory ms | same |
|---|---|---|---|---|---|
| -9167234590988767838 | How many accounts does the customer with customer_key … hold, by product line? | 1.724 | 20 | 35 | yes |
| -9167234590988767838 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.805 | 70 | 54 | yes |
| -9167234590988767838 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.796 | 93 | 52 | yes |
| -9167234590988767838 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.94 | 99 | 33 | yes |
| -9167234590988767838 | How many calls did the customer with customer_key … make last quarter, by queue? | 1.036 | 10 | 23 | yes |
| -9167234590988767838 | Calls from the customer with customer_key … last quarter, by contact center site | 0.935 | 20 | 33 | yes |
| -9167234590988767838 | Total card spend of the customer with customer_key … in June 2026 | 1.024 | 18 | 38 | yes |
| -9167234590988767838 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.767 | 20 | 30 | yes |
| -9167234590988767838 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.842 | 10 | 41 | yes |
| -9167234590988767838 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.958 | 83 | 40 | yes |
| -9166543141958061385 | How many accounts does the customer with customer_key … hold, by product line? | 1.279 | 20 | 56 | yes |
| -9166543141958061385 | Card spend by merchant category for the customer with customer_key …, last quarter | 1.88 | 70 | 33 | yes |
| -9166543141958061385 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.924 | 93 | 46 | yes |
| -9166543141958061385 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.801 | 99 | 24 | yes |
| -9166543141958061385 | How many calls did the customer with customer_key … make last quarter, by queue? | 1.011 | 10 | 17 | yes |
| -9166543141958061385 | Calls from the customer with customer_key … last quarter, by contact center site | 0.878 | 20 | 20 | yes |
| -9166543141958061385 | Total card spend of the customer with customer_key … in June 2026 | 0.798 | 18 | 28 | yes |
| -9166543141958061385 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.733 | 20 | 48 | yes |
| -9166543141958061385 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.944 | 10 | 21 | yes |
| -9166543141958061385 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.83 | 124 | 28 | yes |
| -9161644862445682949 | How many accounts does the customer with customer_key … hold, by product line? | 0.723 | 20 | 17 | yes |
| -9161644862445682949 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.876 | 70 | 52 | yes |
| -9161644862445682949 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.837 | 93 | 39 | yes |
| -9161644862445682949 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.052 | 99 | 24 | yes |
| -9161644862445682949 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.916 | 10 | 28 | yes |
| -9161644862445682949 | Calls from the customer with customer_key … last quarter, by contact center site | 0.909 | 20 | 27 | yes |
| -9161644862445682949 | Total card spend of the customer with customer_key … in June 2026 | 0.745 | 18 | 27 | yes |
| -9161644862445682949 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.941 | 20 | 21 | yes |
| -9161644862445682949 | Average call handle time in seconds for the customer with customer_key …, last quarter | 1.072 | 10 | 18 | yes |
| -9161644862445682949 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.861 | 83 | 28 | yes |
| -9159597936804468552 | How many accounts does the customer with customer_key … hold, by product line? | 0.784 | 20 | 16 | yes |
| -9159597936804468552 | Card spend by merchant category for the customer with customer_key …, last quarter | 0.869 | 70 | 23 | yes |
| -9159597936804468552 | Number of card purchases by merchant for the customer with customer_key …, last quarter | - | - | - | - |
| -9159597936804468552 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 0.873 | 99 | 25 | yes |
| -9159597936804468552 | How many calls did the customer with customer_key … make last quarter, by queue? | 1.099 | 20 | 28 | yes |
| -9159597936804468552 | Calls from the customer with customer_key … last quarter, by contact center site | 2.274 | 20 | 30 | yes |
| -9159597936804468552 | Total card spend of the customer with customer_key … in June 2026 | 0.687 | 18 | 21 | yes |
| -9159597936804468552 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.836 | 20 | 26 | yes |
| -9159597936804468552 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.93 | 10 | 21 | yes |
| -9159597936804468552 | Monthly deposit totals for the customer with customer_key …, last quarter | 1.095 | 83 | 27 | yes |
| -9156933861656243150 | How many accounts does the customer with customer_key … hold, by product line? | 0.702 | 20 | 20 | yes |
| -9156933861656243150 | Card spend by merchant category for the customer with customer_key …, last quarter | 1.35 | 70 | 31 | yes |
| -9156933861656243150 | Number of card purchases by merchant for the customer with customer_key …, last quarter | 0.933 | 93 | 38 | yes |
| -9156933861656243150 | Deposit amounts by transaction type for the customer with customer_key …, last quarter | 1.008 | 99 | 44 | yes |
| -9156933861656243150 | How many calls did the customer with customer_key … make last quarter, by queue? | 0.784 | 20 | 89 | yes |
| -9156933861656243150 | Calls from the customer with customer_key … last quarter, by contact center site | 0.846 | 20 | 68 | yes |
| -9156933861656243150 | Total card spend of the customer with customer_key … in June 2026 | 0.752 | 18 | 28 | yes |
| -9156933861656243150 | How many of the accounts of the customer with customer_key … are maintained at each branch? | 0.677 | 20 | 60 | yes |
| -9156933861656243150 | Average call handle time in seconds for the customer with customer_key …, last quarter | 0.992 | 10 | 22 | yes |
| -9156933861656243150 | Monthly deposit totals for the customer with customer_key …, last quarter | 0.996 | 83 | 34 | yes |

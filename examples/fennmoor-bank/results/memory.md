# Memory: remembered contexts against the virtual graph

Phase 1 of plans/2026-09-27-agentic-memory.md: `qlsc remember` fetches a customer's context from the virtual graph (the node, its relationships, their dimensions; facts from the last 90 days, since 2026-04-02, at most 200 per relationship) into the `memory` database; `qlsc recall` reads it back while it holds. Read as the data source.

## Correctness

- **Contexts:** 20 of 20 read back from memory exactly as fetched: the same nodes, properties and relationships.
- **The same Cypher on both:** 110 of 110 context questions gave the same rows on memory and on the virtual graph; 10 were left out, over a capped relationship.
- **Idempotence:** remembering three contexts again left memory's counts unchanged (5296 nodes, 15863 relationships).

| customer | nodes | relationships | capped | fetch s | recall s | context | questions same / different / capped |
|---|---|---|---|---|---|---|---|
| 8322097816940277129 | 749 | 1397 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 5.39 | 0.16 | same | 4 / 0 / 2 |
| 4406449607907749601 | 776 | 1455 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 4.67 | 0.09 | same | 4 / 0 / 2 |
| -9222608688654483010 | 189 | 279 | - | 3.91 | 0.11 | same | 6 / 0 / 0 |
| -9222574476215892105 | 313 | 640 | - | 5.69 | 0.12 | same | 6 / 0 / 0 |
| -9221063171405116986 | 279 | 412 | - | 3.54 | 0.08 | same | 6 / 0 / 0 |
| -9220903335120281561 | 73 | 187 | - | 4.34 | 0.07 | same | 6 / 0 / 0 |
| -9220075890278552624 | 235 | 345 | - | 6.11 | 0.06 | same | 6 / 0 / 0 |
| -9218325325162838369 | 4 | 3 | - | 2.80 | 0.01 | same | 6 / 0 / 0 |
| -9216095296547614735 | 70 | 191 | - | 3.49 | 0.03 | same | 6 / 0 / 0 |
| -9216064251564302656 | 213 | 612 | Customer<-INITIATED_BY-DepositTransaction | 4.02 | 0.07 | same | 5 / 0 / 1 |
| -9216038908868225893 | 655 | 1264 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 3.98 | 0.11 | same | 4 / 0 / 2 |
| -9215880595133743573 | 221 | 324 | - | 5.07 | 0.03 | same | 6 / 0 / 0 |
| -9215851634835918659 | 147 | 408 | - | 3.10 | 0.04 | same | 6 / 0 / 0 |
| -9213494396892120001 | 225 | 629 | Customer<-INITIATED_BY-DepositTransaction | 3.60 | 0.05 | same | 5 / 0 / 1 |
| -9212503573550955222 | 251 | 669 | Customer<-INITIATED_BY-DepositTransaction | 3.56 | 0.04 | same | 5 / 0 / 1 |
| -9211824707822917825 | 196 | 289 | - | 3.44 | 0.03 | same | 6 / 0 / 0 |
| -9211253863716575344 | 4 | 3 | - | 3.35 | 0.02 | same | 6 / 0 / 0 |
| -9210257275411290315 | 172 | 251 | - | 3.22 | 0.03 | same | 6 / 0 / 0 |
| -9210223701290079287 | 537 | 1093 | Customer<-INITIATED_BY-DepositTransaction | 3.51 | 0.07 | same | 5 / 0 / 1 |
| -9210042244721558210 | 46 | 127 | - | 3.50 | 0.02 | same | 6 / 0 / 0 |

## Freshness

| check | result |
|---|---|
| within its lifetime | ok |
| past it | ok |
| a stale fact | ok |
| a refetch removes it | ok |
| a changed template | ok |

## Latency (seconds)

| | median | p95 |
|---|---|---|
| fetch | 3.575 | 5.69 |
| recall | 0.053 | 0.118 |
| question on the virtual graph | 1.371 | 2.547 |
| question on memory | 0.006 | 0.048 |

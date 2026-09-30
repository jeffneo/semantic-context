# Memory: remembered contexts against the virtual graph

Phase 1 of plans/2026-09-27-agentic-memory.md: `qlsc remember` fetches a customer's context from the virtual graph (the node, its relationships, their dimensions; facts since 2026-04-01, at most 200 per relationship) into the `memory` database; `qlsc recall` reads it back while it holds. Read as the data source.

## Correctness

- **Contexts:** 20 of 20 read back from memory exactly as fetched: the same nodes, properties and relationships.
- **The same Cypher on both:** 110 of 110 context questions gave the same rows on memory and on the virtual graph; 10 were left out, over a capped relationship.
- **Idempotence:** remembering three contexts again left memory's counts unchanged (98503 nodes, 312297 relationships).

| customer | nodes | relationships | capped | fetch s | recall s | context | questions same / different / capped |
|---|---|---|---|---|---|---|---|
| 8322097816940277129 | 752 | 1401 | Customer<-EXECUTED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 6.87 | 0.06 | same | 4 / 0 / 2 |
| 4406449607907749601 | 776 | 1455 | Customer<-EXECUTED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 5.33 | 0.06 | same | 4 / 0 / 2 |
| -9222608688654483010 | 195 | 286 | - | 4.15 | 0.04 | same | 6 / 0 / 0 |
| -9222574476215892105 | 317 | 652 | - | 4.82 | 0.05 | same | 6 / 0 / 0 |
| -9221063171405116986 | 279 | 412 | - | 3.64 | 0.03 | same | 6 / 0 / 0 |
| -9220903335120281561 | 75 | 193 | - | 3.98 | 0.04 | same | 6 / 0 / 0 |
| -9220075890278552624 | 235 | 345 | - | 4.15 | 0.04 | same | 6 / 0 / 0 |
| -9218325325162838369 | 4 | 3 | - | 3.93 | 0.02 | same | 6 / 0 / 0 |
| -9216095296547614735 | 71 | 194 | - | 5.55 | 0.02 | same | 6 / 0 / 0 |
| -9216064251564302656 | 213 | 612 | Customer<-EXECUTED_BY-DepositTransaction | 3.53 | 0.04 | same | 5 / 0 / 1 |
| -9216038908868225893 | 655 | 1264 | Customer<-EXECUTED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 4.72 | 0.05 | same | 4 / 0 / 2 |
| -9215880595133743573 | 225 | 330 | - | 3.69 | 0.04 | same | 6 / 0 / 0 |
| -9215851634835918659 | 147 | 408 | - | 3.79 | 0.11 | same | 6 / 0 / 0 |
| -9213494396892120001 | 225 | 629 | Customer<-EXECUTED_BY-DepositTransaction | 3.89 | 0.03 | same | 5 / 0 / 1 |
| -9212503573550955222 | 253 | 673 | Customer<-EXECUTED_BY-DepositTransaction | 3.52 | 0.03 | same | 5 / 0 / 1 |
| -9211824707822917825 | 198 | 292 | - | 3.69 | 0.03 | same | 6 / 0 / 0 |
| -9211253863716575344 | 4 | 3 | - | 4.80 | 0.02 | same | 6 / 0 / 0 |
| -9210257275411290315 | 174 | 254 | - | 3.60 | 0.03 | same | 6 / 0 / 0 |
| -9210223701290079287 | 543 | 1102 | Customer<-EXECUTED_BY-DepositTransaction | 7.05 | 0.04 | same | 5 / 0 / 1 |
| -9210042244721558210 | 46 | 127 | - | 5.52 | 0.03 | same | 6 / 0 / 0 |

## Freshness

| check | result |
|---|---|
| within its lifetime | ok |
| past it | ok |
| a stale fact | ok |
| a refetch rewrites a relationship from its column | ok |
| a changed template | ok |

## A batch

The 20 remembered together, in one batch: each got the context it got alone (nodes, properties, relationships, and each read's keys, rows and cap), and read back from memory as that. 11.55 s together, against 90.22 s one at a time.

## Latency (seconds)

| | median | p95 |
|---|---|---|
| fetch | 4.064 | 6.872 |
| recall | 0.035 | 0.063 |
| question on the virtual graph | 1.588 | 3.062 |
| question on memory | 0.009 | 0.035 |

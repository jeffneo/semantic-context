# Memory: remembered contexts against the virtual graph

Phase 1 of plans/2026-09-27-agentic-memory.md: `qlsc remember` fetches a customer's context from the virtual graph (the node, its relationships, their dimensions; facts from the last 92 days, since 2026-03-31, at most 200 per relationship) into the `memory` database; `qlsc recall` reads it back while it holds. Read as the data source.

## Correctness

- **Contexts:** 20 of 20 read back from memory exactly as fetched: the same nodes, properties and relationships.
- **The same Cypher on both:** 110 of 110 context questions gave the same rows on memory and on the virtual graph; 10 were left out, over a capped relationship.
- **Idempotence:** remembering three contexts again left memory's counts unchanged (11738 nodes, 34400 relationships).

| customer | nodes | relationships | capped | fetch s | recall s | context | questions same / different / capped |
|---|---|---|---|---|---|---|---|
| 8322097816940277129 | 752 | 1401 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 3.37 | 0.08 | same | 4 / 0 / 2 |
| 4406449607907749601 | 776 | 1455 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 3.08 | 0.08 | same | 4 / 0 / 2 |
| -9222608688654483010 | 195 | 286 | - | 2.14 | 0.04 | same | 6 / 0 / 0 |
| -9222574476215892105 | 317 | 652 | - | 3.00 | 0.06 | same | 6 / 0 / 0 |
| -9221063171405116986 | 279 | 412 | - | 2.26 | 0.04 | same | 6 / 0 / 0 |
| -9220903335120281561 | 75 | 193 | - | 2.20 | 0.03 | same | 6 / 0 / 0 |
| -9220075890278552624 | 235 | 345 | - | 2.65 | 0.04 | same | 6 / 0 / 0 |
| -9218325325162838369 | 4 | 3 | - | 2.12 | 0.02 | same | 6 / 0 / 0 |
| -9216095296547614735 | 71 | 194 | - | 2.35 | 0.03 | same | 6 / 0 / 0 |
| -9216064251564302656 | 213 | 612 | Customer<-INITIATED_BY-DepositTransaction | 2.27 | 0.04 | same | 5 / 0 / 1 |
| -9216038908868225893 | 655 | 1264 | Customer<-INITIATED_BY-DepositTransaction, Customer<-MADE_BY-CardTransaction | 2.54 | 0.07 | same | 4 / 0 / 2 |
| -9215880595133743573 | 225 | 330 | - | 2.73 | 0.04 | same | 6 / 0 / 0 |
| -9215851634835918659 | 147 | 408 | - | 2.66 | 0.04 | same | 6 / 0 / 0 |
| -9213494396892120001 | 225 | 629 | Customer<-INITIATED_BY-DepositTransaction | 2.57 | 0.05 | same | 5 / 0 / 1 |
| -9212503573550955222 | 253 | 673 | Customer<-INITIATED_BY-DepositTransaction | 2.26 | 0.04 | same | 5 / 0 / 1 |
| -9211824707822917825 | 198 | 292 | - | 3.30 | 0.04 | same | 6 / 0 / 0 |
| -9211253863716575344 | 4 | 3 | - | 3.54 | 0.01 | same | 6 / 0 / 0 |
| -9210257275411290315 | 174 | 254 | - | 2.86 | 0.03 | same | 6 / 0 / 0 |
| -9210223701290079287 | 543 | 1102 | Customer<-INITIATED_BY-DepositTransaction | 2.70 | 0.08 | same | 5 / 0 / 1 |
| -9210042244721558210 | 46 | 127 | - | 2.94 | 0.03 | same | 6 / 0 / 0 |

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
| fetch | 2.655 | 3.372 |
| recall | 0.038 | 0.082 |
| question on the virtual graph | 0.919 | 1.355 |
| question on memory | 0.007 | 0.011 |

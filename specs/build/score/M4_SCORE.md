# M4 score: layers, subjects, copies, sensitive data

Graph: Neo4j `semanticlayer`. Keys: `layer`, `subject` and `domain` on each spec table; planted findings.

## Layers

Behavioural layer vs spec layer: **288/296** (97.3%) on the layers behaviour can define. A table people consume counts as a mart, and one not written in the window as unwritten (accepted for raw and sandbox). `legacy` and `ops` are history and purpose labels, with no behavioural definition; they are shown but not scored.

| spec layer | bi | intermediate | mart | ml | raw | sandbox | staging | unwritten |
|---|---|---|---|---|---|---|---|---|
| bi | 7 |  |  |  |  |  |  |  |
| intermediate |  |  | 9 |  |  |  |  |  |
| legacy |  |  | 2 |  |  |  |  | 18 |
| mart |  |  | 47 |  |  |  |  |  |
| ml |  | 1 | 1 | 3 |  |  |  |  |
| ops |  |  | 4 |  |  |  |  | 3 |
| raw |  |  |  |  | 81 | 5 |  | 18 |
| sandbox |  |  |  |  |  | 21 |  | 10 |
| staging |  | 1 | 1 |  |  |  | 91 |  |

## Subjects

297 tables. NMI against the spec's labels (1.0 = identical partitions):

| level | hubs link subjects (D7) | hubs count like any key | inferred groups | spec groups |
|---|---|---|---|---|
| subject | **0.889** | 0.817 | 100 | 89 |
| area vs domain | **0.682** | 0.621 | 77 | 15 |

## Findings

| finding | result | detail |
|---|---|---|
| F08 Raw SSNs outside the restricted zone | **pass** | sandbox copy of the restricted AML party table flagged with its source: yes; legacy SSN columns flagged by name: 2/2; restricted datasets found from access-denied errors |
| F14 The _final_FIXED chain | **pass** | all four copies in one family: yes; _FIXED least used: yes; _v2 a stale snapshot: yes; _final the most used copy: yes |
| F15 Hub keys | **pass** | with hubs linking subjects NMI is 0.889 (subject) / 0.682 (domain), vs 0.817 / 0.621 when hubs vote like any key |

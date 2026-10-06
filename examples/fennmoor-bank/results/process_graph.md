# Process graph: is it the planted process?

2032 conversations, 19360 turns, one graph built from all of them (`qlsc process build`), scored against the answer key. Parameters: similarity 0.9, resolution 1.0, State text both, chosen on the first 600 conversations by id (the first 100 in phase 3, then 100 to 600 at scale in phase 4). The **holdout** is the other 1432: the parameters were never tuned on them. Arms: **graph** (the build), **raw text** (the same embedder and grouping over the unannotated turns), **oracle** (the planted labels as the elements).

## The holdout

1432 conversations.

| | graph | raw text | oracle |
|---|---|---|---|
| elements touched (States / Actions) | 2251 / 815 | 2716 / 2765 | 450 / 64 |
| turns in singleton elements (States / Actions) | 25% / 6% | 32% / 34% | 1% / 0% |
| Action: homogeneity / completeness / V | 0.95 / 0.65 / **0.77** | 1.00 / 0.47 / **0.64** | 1.00 / 1.00 / **1.00** |
| State vs the planted State key: h / c / V | 0.85 / 0.71 / **0.77** | 0.76 / 0.59 / **0.67** | 1.00 / 1.00 / **1.00** |
| State vs the coarse key (domain, stage, verified) | 0.91 / 0.51 / **0.65** | 0.81 / 0.42 / **0.55** | 1.00 / 0.67 / **0.80** |
| stage purity of States | 89% | 97% | 100% |
| transition fidelity: Pearson / Spearman / MAE | 0.91 / 0.95 / 0.071 (270 pairs) | 0.96 / 0.94 / 0.071 (270 pairs) | 0.99 / 0.99 / 0.009 (270 pairs) |
| diagnostic: turns with a recommendation | 75% | 66% | 99% |
| diagnostic: the likeliest next Action asks the clue's question | 7% (102/1441; 6%-9%) | 5% (65/1263; 4%-7%) | 7% (142/1899; 6%-9%) |

The diagnostic test: 1923 customer turns where a discriminating clue is true, perceived and not yet said, and a question in the procedure elicits it; success is the next Action being that question (leave one conversation out).

| | success |
|---|---|
| the graph's likeliest next Action | 7% (102/1441; 6%-9%) |
| the same turns, what the rep actually did | 10% (147/1441; 9%-12%) |
| the rep, over all 1923 turns | 9% (178/1923; 8%-11%) |
| the best single question, chosen with hindsight | 19% (367/1923; 17%-21%) |
| the most frequent next Action overall | 0% (0/1923; 0%-0%) |
| chance (a random action of the procedure) | 6% |
| the oracle's likeliest next Action | 7% (142/1899; 6%-9%), covering 99% |
| the raw-text arm's | 5% (65/1263; 4%-7%), covering 66% |

Unauthenticated callers flagged when no Action on the path verifies identity, against the planted breach:

| arm | found | false alarms | missed | correctly clear |
|---|---|---|---|---|
| graph | 46 | 13 | 0 | 261 |
| raw text | 46 | 13 | 0 | 261 |
| oracle | 46 | 13 | 0 | 261 |

## The tuning conversations

The first 600, which the parameters were chosen on, in the larger graph.

| | graph | raw text | oracle |
|---|---|---|---|
| elements touched (States / Actions) | 1163 / 505 | 1420 / 1329 | 312 / 63 |
| turns in singleton elements (States / Actions) | 25% / 7% | 33% / 33% | 1% / 0% |
| Action: homogeneity / completeness / V | 0.96 / 0.67 / **0.79** | 1.00 / 0.51 / **0.67** | 1.00 / 1.00 / **1.00** |
| State vs the planted State key: h / c / V | 0.87 / 0.71 / **0.78** | 0.81 / 0.62 / **0.70** | 1.00 / 1.00 / **1.00** |
| State vs the coarse key (domain, stage, verified) | 0.92 / 0.52 / **0.67** | 0.84 / 0.44 / **0.58** | 1.00 / 0.69 / **0.81** |
| stage purity of States | 90% | 97% | 100% |
| transition fidelity: Pearson / Spearman / MAE | 0.90 / 0.92 / 0.079 (219 pairs) | 0.95 / 0.94 / 0.083 (219 pairs) | 1.00 / 1.00 / 0.007 (219 pairs) |
| diagnostic: turns with a recommendation | 74% | 62% | 99% |
| diagnostic: the likeliest next Action asks the clue's question | 8% (54/711; 6%-10%) | 5% (31/589; 4%-7%) | 6% (61/948; 5%-8%) |

The diagnostic test: 955 customer turns where a discriminating clue is true, perceived and not yet said, and a question in the procedure elicits it; success is the next Action being that question (leave one conversation out).

| | success |
|---|---|
| the graph's likeliest next Action | 8% (54/711; 6%-10%) |
| the same turns, what the rep actually did | 9% (66/711; 7%-12%) |
| the rep, over all 955 turns | 9% (88/955; 8%-11%) |
| the best single question, chosen with hindsight | 18% (174/955; 16%-21%) |
| the most frequent next Action overall | 0% (0/955; 0%-0%) |
| chance (a random action of the procedure) | 6% |
| the oracle's likeliest next Action | 6% (61/948; 5%-8%), covering 99% |
| the raw-text arm's | 5% (31/589; 4%-7%), covering 62% |

Unauthenticated callers flagged when no Action on the path verifies identity, against the planted breach:

| arm | found | false alarms | missed | correctly clear |
|---|---|---|---|---|
| graph | 7 | 8 | 0 | 100 |
| raw text | 7 | 8 | 0 | 100 |
| oracle | 7 | 8 | 0 | 100 |

## All

All 2032.

| | graph | raw text | oracle |
|---|---|---|---|
| elements touched (States / Actions) | 3044 / 1017 | 3724 / 3752 | 481 / 64 |
| turns in singleton elements (States / Actions) | 25% / 6% | 32% / 34% | 1% / 0% |
| Action: homogeneity / completeness / V | 0.95 / 0.64 / **0.77** | 1.00 / 0.46 / **0.63** | 1.00 / 1.00 / **1.00** |
| State vs the planted State key: h / c / V | 0.84 / 0.69 / **0.76** | 0.75 / 0.57 / **0.65** | 1.00 / 1.00 / **1.00** |
| State vs the coarse key (domain, stage, verified) | 0.91 / 0.49 / **0.64** | 0.81 / 0.41 / **0.54** | 1.00 / 0.67 / **0.80** |
| stage purity of States | 88% | 97% | 100% |
| transition fidelity: Pearson / Spearman / MAE | 0.92 / 0.93 / 0.066 (293 pairs) | 0.96 / 0.95 / 0.066 (293 pairs) | 0.99 / 0.99 / 0.008 (293 pairs) |
| diagnostic: turns with a recommendation | 75% | 64% | 99% |
| diagnostic: the likeliest next Action asks the clue's question | 7% (156/2152; 6%-8%) | 5% (96/1852; 4%-6%) | 7% (203/2847; 6%-8%) |

The diagnostic test: 2878 customer turns where a discriminating clue is true, perceived and not yet said, and a question in the procedure elicits it; success is the next Action being that question (leave one conversation out).

| | success |
|---|---|
| the graph's likeliest next Action | 7% (156/2152; 6%-8%) |
| the same turns, what the rep actually did | 10% (213/2152; 9%-11%) |
| the rep, over all 2878 turns | 9% (266/2878; 8%-10%) |
| the best single question, chosen with hindsight | 19% (541/2878; 17%-20%) |
| the most frequent next Action overall | 0% (0/2878; 0%-0%) |
| chance (a random action of the procedure) | 6% |
| the oracle's likeliest next Action | 7% (203/2847; 6%-8%), covering 99% |
| the raw-text arm's | 5% (96/1852; 4%-6%), covering 64% |

Unauthenticated callers flagged when no Action on the path verifies identity, against the planted breach:

| arm | found | false alarms | missed | correctly clear |
|---|---|---|---|---|
| graph | 53 | 21 | 0 | 361 |
| raw text | 53 | 21 | 0 | 361 |
| oracle | 53 | 21 | 0 | 361 |

The stored `num` of every transition equals a recount from the turns: True.

# Process abstraction, phase 3: the grid on the tuning conversations

## good_rating: the rating that best separates the planted high favourability

| rating at least | accuracy | precision | recall |
|---|---|---|---|
| 3 | 0.878 | 0.868 | 0.939 |
| 4 | 0.882 | 0.944 | 0.852 |
| 5 | 0.705 | 0.995 | 0.508 |

Chosen: **4**.

## prior: Brier against the planted label, all checkpoints, per estimator

| prior | empirical | chain |
|---|---|---|
| 0 | 0.2059 | 0.2076 |
| 1 | 0.2054 | 0.2096 |
| 2 | 0.2052 | 0.2108 |
| 5 | 0.2054 | 0.2127 |
| 10 | 0.2065 | 0.2145 |
| 20 | 0.2089 | 0.2169 |

The global rate scores 0.2406. Best prior: empirical **2**, chain **0**.

Empirical minus chain, paired over conversations: **-0.0035 ± 0.0031**. The interval excludes zero: **empirical** is better.

## min_support: Brier of empirical (prior 2), against the coverage

| min_support | Brier | coverage |
|---|---|---|
| 1 | 0.1999 | 74% |
| 3 | 0.2038 | 65% |
| 5 | 0.2052 | 62% |
| 10 | 0.2095 | 58% |
| 20 | 0.2130 | 53% |

Best of 3, 5 and 10: 0.2038; the smallest within 0.002 of it: **3**.

## The settings the rules choose

`process.absorb.good_rating: 4`, `prior: 2`, `estimator: empirical`, `process.min_support: 3`.

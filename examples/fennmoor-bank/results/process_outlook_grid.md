# Process abstraction, phase 4: the grid on the tuning conversations

## (states, temperature): Brier for the odds of ending well, pooled, at checkpoints

| states | temperature 0 | temperature 0.02 | temperature 0.05 | temperature 0.1 | temperature 0.3 | temperature 1 |
|---|---|---|---|---|---|
| 1 | 0.2038 | 0.2038 | 0.2038 | 0.2038 | 0.2038 | 0.2038 |
| 3 | 0.2038 | 0.2010 | 0.1975 | 0.1958 | 0.1914 | 0.1910 |
| 5 | 0.2038 | 0.2012 | 0.1987 | 0.1945 | 0.1895 | 0.1889 |
| 10 | 0.2038 | 0.2012 | 0.1977 | 0.1915 | 0.1917 | 0.1927 |
| 20 | 0.2038 | 0.2009 | 0.1949 | 0.1926 | 0.1956 | 0.1968 |

The global rate scores 0.2406 and the State the build assigned 0.2038. Best: **5 States at temperature 1** (0.1889).

## (level, prior): the share of all decision points where the recommendation is useful

| level | prior 1 | prior 5 | prior 20 | prior 50 | prior 200 |
|---|---|---|---|
| 1 | 18.9% (covered 89%) | 17.9% (covered 89%) | 18.6% (covered 89%) | 18.3% (covered 89%) | 18.1% (covered 89%) |
| 2 | 18.4% (covered 91%) | 19.6% (covered 91%) | 21.8% (covered 91%) | 22.1% (covered 91%) | 21.7% (covered 91%) |

Best: **level 2, prior 50** (22.1%).

## The settings the rules choose

`process.outlook.states: 5`, `temperature: 1`, `level: 2`, `prior: 50`.

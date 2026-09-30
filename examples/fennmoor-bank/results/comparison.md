# The comparison: qlsc against naive approaches

**Log questions**

| method | right | delivered | tokens p50 / p90 | seconds p50 / p90 | $ per request | $ per right answer |
|---|---|---|---|---|---|---|
| naive-schema | 116 of 176 (66%) | 0 (0%) | 43,872 / 44,032 | 4.4 / 5.5 | 0.012 | 0.018 |
| naive-agent | 108 of 176 (61%) | 17 (10%) | 50,304 / 127,053 | 22.4 / 42.8 | 0.060 | 0.098 |
| layer | 132 of 176 (75%) | 132 (75%) | 6,667 / 9,804 | 4.4 / 8.2 | 0.017 | 0.023 |
| agent | 158 of 176 (90%) | 153 (87%) | 10,667 / 47,220 | 9.0 / 40.8 | 0.042 | 0.047 |

**Gold questions**

| method | right | delivered | tokens p50 / p90 | seconds p50 / p90 | $ per request | $ per right answer |
|---|---|---|---|---|---|---|
| naive-schema | 3 of 10 (30%) | 0 (0%) | 43,879 / 44,109 | 5.2 / 6.5 | 0.012 | 0.041 |
| naive-agent | 6 of 10 (60%) | 0 (0%) | 81,758 / 181,217 | 33.3 / 54.7 | 0.077 | 0.128 |
| layer | 6 of 10 (60%) | 6 (60%) | 6,187 / 7,241 | 5.7 / 7.2 | 0.015 | 0.024 |
| agent | 9 of 10 (90%) | 9 (90%) | 43,513 / 70,802 | 46.6 / 62.2 | 0.094 | 0.105 |

**The agent's exchanges** (186): right at once 96; right, rejected by the agent 65; accepted wrong 10; never right 9; right, past the targets 5; right after corrections 1.

First answers by route: sql 97 (75 right); precedent 89 (86 right). Consumer's own spend: $2.29.

Targets: {'tokens': 20000, 'seconds': 30}. Every LLM call live: measured.

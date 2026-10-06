# Process abstraction, phase 1: the levels above the first

2032 conversations, one hierarchy built from all of them (`qlsc process abstract`), scored against the answer key by level. Parameters: {"kinds": ["action"], "neighbours": 10, "similarity": 0.8, "gamma": 4.0, "transition_weight": 0.6, "shrink": 0.85, "min_nodes": 12, "max_levels": 5}. The tuning slice is the first 600 conversations by id, where the parameters were chosen; the holdout is the rest.

## The holdout

| level | States | Actions | Action h / c / V | State V (key) | State V (coarse) | stage purity | singleton turns (S / A) | fidelity r | turns with a recommendation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2251 | 815 | 0.95 / 0.65 / **0.77** | 0.77 | 0.65 | 89% | 25% / 6% | 0.91 | 75% |
| 2 | 2251 | 300 | 0.90 / 0.76 / **0.83** | 0.77 | 0.65 | 89% | 25% / 2% | 0.86 | 75% |

## The tuning conversations

| level | States | Actions | Action h / c / V | State V (key) | State V (coarse) | stage purity | singleton turns (S / A) | fidelity r | turns with a recommendation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1163 | 505 | 0.96 / 0.67 / **0.79** | 0.78 | 0.67 | 90% | 25% / 7% | 0.90 | 74% |
| 2 | 1163 | 209 | 0.91 / 0.78 / **0.84** | 0.78 | 0.67 | 90% | 25% / 2% | 0.84 | 74% |

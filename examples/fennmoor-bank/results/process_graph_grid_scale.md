# Process graph: the grouping parameters, by the score

The grouping is over all 19360 annotated turns; the score is over conversations 100 to 600 (by id), 500 of them. Sorted by Action V + State V (against the planted State key). Grouping only: no naming, no folding.

| State text | similarity | resolution | States | Actions | Action V (completeness) | State V (key) | State V (coarse) | stage purity | fidelity r | diag covered | diag success |
|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 0.9 | 1.0 | 1081 | 493 | 0.78 (0.66) | 0.79 | 0.67 | 91% | 0.90 | 67% | 43/517 |
| both | 0.93 | 1.0 | 1913 | 593 | 0.77 (0.64) | 0.79 | 0.63 | 99% | 0.98 | 36% | 21/277 |
| both | 0.85 | 1.0 | 213 | 337 | 0.80 (0.69) | 0.75 | 0.72 | 76% | 0.73 | 96% | 49/741 |
| both | 0.75 | 1.0 | 57 | 164 | 0.81 (0.72) | 0.73 | 0.71 | 70% | 0.64 | 100% | 43/772 |
| both | 0.7 | 1.0 | 54 | 129 | 0.81 (0.73) | 0.73 | 0.71 | 70% | 0.67 | 100% | 33/772 |
| both | 0.8 | 1.0 | 77 | 232 | 0.80 (0.71) | 0.73 | 0.72 | 71% | 0.72 | 100% | 48/769 |

# Process abstraction, phase 3: the odds on a State

Estimates are leave-one-conversation-out (the AUC tables, in 20 folds: see below); a State with fewer than 3 conversations left carries none, and the global rate is used in its place (the coverage says how often). Ended well: the outcome call's rating at least 4 (the fitting) and the planted favourability high (the score). Prior 2.0 pseudo-conversations for every arm but the chain, which scored best with 0. Tuning slice: the first 600 by id; holdout: the rest (1432). The estimator stored on the graph is **empirical**.

## Holdout: Brier score against the planted label (lower is better; the difference from the global rate, with a 95% interval)

| arm | 1st (n=1432) | 2nd (n=1432) | 3rd (n=1374) | 4th (n=1092) | 6th (n=372) | the last (n=1432) | all (n=7134) |
|---|---|---|---|---|---|---|---|
| global rate | 0.237 | 0.237 | 0.234 | 0.229 | 0.240 | 0.237 | 0.236 |
| by domain | 0.215 (-0.023 ± 0.007) | 0.215 (-0.023 ± 0.007) | 0.214 (-0.019 ± 0.007) | 0.223 (-0.006 ± 0.008) | 0.258 (+0.018 ± 0.011) | 0.215 (-0.023 ± 0.007) | 0.218 (-0.023 ± 0.007) |
| by position | 0.237 (+0.000 ± 0.000) | 0.237 (+0.000 ± 0.000) | 0.230 (-0.004 ± 0.001) | 0.222 (-0.008 ± 0.002) | 0.261 (+0.021 ± 0.010) | 0.237 (+0.000 ± 0.000) | 0.235 (-0.001 ± 0.000) |
| by planted State | 0.214 (-0.023 ± 0.007) | 0.200 (-0.037 ± 0.007) | 0.202 (-0.032 ± 0.008) | 0.202 (-0.027 ± 0.010) | 0.261 (+0.021 ± 0.022) | 0.135 (-0.103 ± 0.008) | 0.194 (-0.050 ± 0.007) |
| empirical | 0.224 (-0.013 ± 0.008) | 0.211 (-0.026 ± 0.006) | 0.193 (-0.041 ± 0.008) | 0.185 (-0.044 ± 0.009) | 0.228 (-0.012 ± 0.013) | 0.179 (-0.058 ± 0.009) | 0.201 (-0.039 ± 0.005) |
| chain | 0.225 (-0.012 ± 0.003) | 0.213 (-0.025 ± 0.004) | 0.193 (-0.041 ± 0.006) | 0.182 (-0.048 ± 0.007) | 0.219 (-0.021 ± 0.010) | 0.178 (-0.059 ± 0.008) | 0.200 (-0.038 ± 0.004) |

Coverage (checkpoints in a State with at least 3 other conversations): empirical **66%**, chain **66%**.

### Holdout: Brier against the text's own label (what the odds were fitted to)

- global rate: 0.244
- by domain: 0.207
- by position: 0.243
- by planted State: 0.186
- empirical: 0.194
- chain: 0.201

### Holdout: AUC for telling the cases that end well, at each checkpoint (in 20 folds of conversations, each taken out whole, and averaged over folds: leaving one conversation out moves a rate against its own label, which makes a constant rate read below one half)

| arm | 1st | 2nd | 3rd | 4th | 6th | the last | all |
|---|---|---|---|---|---|---|---|
| global rate | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| by domain | 0.64 | 0.64 | 0.64 | 0.61 | 0.51 | 0.64 | 0.63 |
| by position | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.52 |
| by planted State | 0.64 | 0.69 | 0.70 | 0.69 | 0.60 | 0.83 | 0.73 |
| empirical | 0.64 | 0.64 | 0.69 | 0.71 | 0.63 | 0.78 | 0.69 |
| chain | 0.60 | 0.60 | 0.71 | 0.74 | 0.67 | 0.80 | 0.69 |

## Tuning: Brier score against the planted label (lower is better; the difference from the global rate, with a 95% interval)

| arm | 1st (n=600) | 2nd (n=600) | 3rd (n=579) | 4th (n=474) | 6th (n=182) | the last (n=600) | all (n=3035) |
|---|---|---|---|---|---|---|---|
| global rate | 0.242 | 0.242 | 0.239 | 0.237 | 0.244 | 0.242 | 0.241 |
| by domain | 0.211 (-0.030 ± 0.011) | 0.211 (-0.030 ± 0.011) | 0.211 (-0.028 ± 0.011) | 0.224 (-0.013 ± 0.012) | 0.258 (+0.014 ± 0.017) | 0.211 (-0.030 ± 0.011) | 0.216 (-0.030 ± 0.011) |
| by position | 0.242 (+0.000 ± 0.000) | 0.242 (+0.000 ± 0.000) | 0.237 (-0.002 ± 0.002) | 0.233 (-0.004 ± 0.003) | 0.258 (+0.014 ± 0.015) | 0.242 (+0.000 ± 0.000) | 0.240 (-0.000 ± 0.001) |
| by planted State | 0.210 (-0.031 ± 0.011) | 0.206 (-0.036 ± 0.011) | 0.205 (-0.034 ± 0.013) | 0.219 (-0.018 ± 0.016) | 0.251 (+0.007 ± 0.032) | 0.135 (-0.107 ± 0.013) | 0.197 (-0.051 ± 0.010) |
| empirical | 0.220 (-0.022 ± 0.011) | 0.214 (-0.028 ± 0.009) | 0.197 (-0.042 ± 0.010) | 0.197 (-0.040 ± 0.013) | 0.236 (-0.009 ± 0.020) | 0.181 (-0.061 ± 0.012) | 0.204 (-0.042 ± 0.007) |
| chain | 0.230 (-0.012 ± 0.003) | 0.213 (-0.028 ± 0.007) | 0.201 (-0.038 ± 0.009) | 0.196 (-0.041 ± 0.010) | 0.223 (-0.021 ± 0.015) | 0.180 (-0.062 ± 0.012) | 0.205 (-0.039 ± 0.006) |

Coverage (checkpoints in a State with at least 3 other conversations): empirical **65%**, chain **65%**.

### Tuning: Brier against the text's own label (what the odds were fitted to)

- global rate: 0.249
- by domain: 0.208
- by position: 0.249
- by planted State: 0.187
- empirical: 0.204
- chain: 0.210

### Tuning: AUC for telling the cases that end well, at each checkpoint (in 20 folds of conversations, each taken out whole, and averaged over folds: leaving one conversation out moves a rate against its own label, which makes a constant rate read below one half)

| arm | 1st | 2nd | 3rd | 4th | 6th | the last | all |
|---|---|---|---|---|---|---|---|
| global rate | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| by domain | 0.65 | 0.65 | 0.66 | 0.61 | 0.49 | 0.65 | 0.64 |
| by position | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.52 |
| by planted State | 0.66 | 0.67 | 0.69 | 0.67 | 0.61 | 0.84 | 0.72 |
| empirical | 0.67 | 0.66 | 0.71 | 0.73 | 0.62 | 0.79 | 0.70 |
| chain | 0.57 | 0.66 | 0.70 | 0.75 | 0.67 | 0.81 | 0.70 |

Holdout, empirical minus chain (Brier, paired over conversations): **-0.0004 ± 0.0023**.
Holdout, empirical minus by planted State (Brier, paired over conversations): **+0.0113 ± 0.0058**.
Holdout, chain minus by planted State (Brier, paired over conversations): **+0.0117 ± 0.0061**.

## Holdout: calibration of the stored estimator (empirical)

| predicted | checkpoints | mean predicted | ended well |
|---|---|---|---|
| 0.0 to 0.2 | 238 | 0.08 | 0.18 |
| 0.2 to 0.4 | 314 | 0.28 | 0.59 |
| 0.4 to 0.6 | 4219 | 0.54 | 0.55 |
| 0.6 to 0.8 | 809 | 0.72 | 0.76 |
| 0.8 to 1.0 | 1554 | 0.92 | 0.93 |

Expected calibration error: **0.025**.

## Holdout: mean empirical prediction by planted favourability (does the odds separate the cases as they unfold?)

| planted favourability | 1st | 2nd | 3rd | 4th | 6th | the last |
|---|---|---|---|---|---|---|
| high | 0.61 | 0.64 | 0.69 | 0.71 | 0.62 | 0.75 |
| medium | 0.52 | 0.54 | 0.58 | 0.57 | 0.54 | 0.59 |
| low | 0.51 | 0.52 | 0.42 | 0.48 | 0.55 | 0.41 |
| very-low | 0.47 | 0.53 | 0.53 | 0.51 | 0.55 | 0.55 |

103 seconds for both slices.

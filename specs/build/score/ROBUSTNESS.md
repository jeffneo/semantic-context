# Robustness: noise and parameters

Clean level 1: 107 groups, NMI vs spec subjects 0.855 (gamma 4.0). NMI = agreement of the table partition with the spec; ARI vs clean = how much of the clean grouping survives (1 = identical). Noise rows average two seeds.

## 1. Noisy queries (random cross-estate co-reads)

| noise, share of real statements | groups | ARI vs clean | NMI vs spec subjects |
|---|---|---|---|
| 5% (34) | 105 | 0.95 | 0.855 |
| 10% (69) | 104 | 0.96 | 0.851 |
| 25% (173) | 105 | 0.92 | 0.851 |
| 50% (347) | 104 | 0.89 | 0.847 |
| 100% (695) | 103 | 0.88 | 0.847 |

## 2. Wrong joins that get past the confidence check (random id merges)

| merges | groups | ARI vs clean | NMI vs spec subjects |
|---|---|---|---|
| 5 | 108 | 0.92 | 0.857 |
| 10 | 107 | 0.91 | 0.858 |
| 25 | 105 | 0.89 | 0.855 |
| 50 | 104 | 0.86 | 0.851 |

## 3. Level-1 gamma (Leiden over co-reads and lineage)

| gamma | groups | NMI vs subjects | NMI vs domains | stability across seeds (ARI) |
|---|---|---|---|---|
| 1 | 82 | 0.825 | 0.645 | 1.00 |
| 2 | 94 | 0.842 | 0.651 | 0.96 |
| 3 | 98 | 0.852 | 0.646 | 0.99 |
| 4 | 107 | 0.856 | 0.650 | 0.97 |
| 6 | 122 | 0.868 | 0.650 | 0.99 |
| 8 | 132 | 0.872 | 0.654 | 0.99 |

## 4. Level 1 -> level 2 (K_SIM kNN + Leiden)

| k | gamma | level-2 groups | NMI vs domains | stability across seeds (ARI) |
|---|---|---|---|---|
| 3 | 1.5 | 11 | 0.681 | 0.95 |
| 3 | 3 | 16 | 0.703 | 0.97 |
| 3 | 4.5 | 21 | 0.701 | 1.00 |
| 5 | 1.5 | 10 | 0.672 | 1.00 |
| 5 | 3 | 15 | 0.720 | 1.00 |
| 5 | 4.5 | 18 | 0.697 | 1.00 |
| 8 | 1.5 | 9 | 0.680 | 1.00 |
| 8 | 3 | 14 | 0.705 | 1.00 |
| 8 | 4.5 | 19 | 0.719 | 1.00 |

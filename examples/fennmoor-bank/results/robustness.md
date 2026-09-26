# Robustness: noise and parameters

Clean level 1: 109 groups, NMI vs spec subjects 0.852 (gamma 4.0). NMI = agreement of the table partition with the spec; ARI vs clean = how much of the clean grouping survives (1 = identical). Noise rows average two seeds.

## 1. Noisy queries (random cross-estate co-reads)

| noise, share of real statements | groups | ARI vs clean | NMI vs spec subjects |
|---|---|---|---|
| 5% (34) | 108 | 0.97 | 0.853 |
| 10% (69) | 107 | 0.94 | 0.852 |
| 25% (173) | 103 | 0.91 | 0.852 |
| 50% (347) | 103 | 0.89 | 0.850 |
| 100% (695) | 102 | 0.87 | 0.850 |

## 2. Wrong joins that get past the confidence check (random id merges)

| merges | groups | ARI vs clean | NMI vs spec subjects |
|---|---|---|---|
| 5 | 108 | 0.97 | 0.851 |
| 10 | 108 | 0.96 | 0.850 |
| 25 | 106 | 0.88 | 0.843 |
| 50 | 104 | 0.88 | 0.843 |

## 3. Level-1 gamma (Leiden over co-reads and lineage)

| gamma | groups | NMI vs subjects | NMI vs domains | stability across seeds (ARI) |
|---|---|---|---|---|
| 1 | 83 | 0.833 | 0.653 | 0.96 |
| 2 | 93 | 0.844 | 0.653 | 1.00 |
| 3 | 103 | 0.849 | 0.646 | 0.98 |
| 4 | 110 | 0.853 | 0.647 | 0.96 |
| 6 | 121 | 0.867 | 0.654 | 0.99 |
| 8 | 131 | 0.870 | 0.653 | 0.99 |

## 4. Level 1 -> level 2 (K_SIM kNN + Leiden)

| k | gamma | level-2 groups | NMI vs domains | stability across seeds (ARI) |
|---|---|---|---|---|
| 3 | 1.5 | 12 | 0.689 | 0.97 |
| 3 | 3 | 16 | 0.705 | 1.00 |
| 3 | 4.5 | 21 | 0.707 | 1.00 |
| 5 | 1.5 | 11 | 0.683 | 0.87 |
| 5 | 3 | 16 | 0.708 | 1.00 |
| 5 | 4.5 | 18 | 0.708 | 1.00 |
| 8 | 1.5 | 10 | 0.663 | 0.98 |
| 8 | 3 | 15 | 0.698 | 1.00 |
| 8 | 4.5 | 19 | 0.705 | 1.00 |

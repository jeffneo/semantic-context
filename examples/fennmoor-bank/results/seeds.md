# Seeds: how much depends on Leiden's random seed

Level 1 and the levels above rebuilt with 11 seeds (both Leiden runs use the same seed); the configured seed is 42. NMI: the table partition against the spec's subjects (level 1) and domains (level 2). Navigation: the 14 gold questions, groups combined, round robin.

| seed | levels | stability | NMI subjects | NMI domains | reached | recall | hit | traps |
|---|---|---|---|---|---|---|---|---|
| 1 | 110 → 14 → 4 | 0.95 | 0.865 | 0.738 | 75% | 63% | 13/14 | 5 |
| 2 | 110 → 14 → 4 | 0.95 | 0.864 | 0.730 | 68% | 54% | 13/14 | 5 |
| 3 | 108 → 16 → 5 | 0.95 | 0.861 | 0.716 | 79% | 63% | 13/14 | 6 |
| 4 | 110 → 15 → 4 | 0.95 | 0.866 | 0.709 | 65% | 50% | 13/14 | 6 |
| 5 | 109 → 16 → 4 | 0.95 | 0.863 | 0.701 | 78% | 65% | 14/14 | 6 |
| 6 | 108 → 16 → 4 | 0.95 | 0.860 | 0.708 | 79% | 63% | 13/14 | 6 |
| 7 | 109 → 17 → 4 | 0.95 | 0.863 | 0.708 | 78% | 68% | 14/14 | 6 |
| 8 | 110 → 15 → 4 | 0.95 | 0.865 | 0.704 | 65% | 50% | 13/14 | 6 |
| 9 | 110 → 15 → 5 | 0.95 | 0.865 | 0.725 | 65% | 50% | 13/14 | 7 |
| 10 | 109 → 16 → 4 | 0.95 | 0.863 | 0.701 | 78% | 65% | 14/14 | 6 |
| 42 (configured) | 109 → 16 → 5 | 0.95 | 0.864 | 0.708 | 72% | 54% | 13/14 | 6 |

| | mean | sd | min | max |
|---|---|---|---|---|
| nmi_subjects | 0.863 | 0.002 | 0.860 | 0.866 |
| nmi_domains | 0.713 | 0.012 | 0.701 | 0.738 |
| reached | 73% | 6% | 65% | 79% |
| recall | 59% | 7% | 50% | 68% |
| hit | 13.3 | 0.5 | 13.0 | 14.0 |
| traps | 5.9 | 0.5 | 5.0 | 7.0 |

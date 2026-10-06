# Process graph, phase 4: the stages with no LLM, against the size of the corpus

The scale set's placeholder text stands in for annotations (see the script); it is repetitive, so only the time means anything. Database `processscale`, elements numbered, no naming.

| conversations | turns | embed s | neighbours s | group s | lift s | write s | total s | seconds per 1,000 turns |
|---|---|---|---|---|---|---|---|---|
| 2,000 | 17,493 | 3.6 | 27.2 | 2.2 | 2.0 | 0.4 | 35.7 | 2.0 |
| 10,000 | 87,059 | 15.2 | 133.1 | 12.7 | 16.1 | 0.7 | 178.7 | 2.1 |
| 21,161 | 162,221 | 16.8 | 269.4 | 27.0 | 39.2 | 0.6 | 354.3 | 2.2 |

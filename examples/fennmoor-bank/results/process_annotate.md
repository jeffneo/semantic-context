# Process graph, phase 1: one call per turn, or one per conversation

25 conversations, 225 turns, annotated by claude-haiku-4-5-20251001. Reference: one call per turn from the turns so far. Candidate: one call per conversation, told to annotate each turn from the turns up to it.

| | per turn | per conversation |
|---|---|---|
| calls | 222 | 25 |
| cost for these | $0.18 | $0.07 |
| projected, 2,032 conversations | $15 | $6 |
| wall seconds (concurrency 6) | 46.3 | 19.5 |
| turns with an unresolved problem | 0 | 4 |
| median words in a State | 36 | 22 |

## Do the two units describe a turn the same way?

Cosine between the two descriptions of the same turn (text-embedding-3-large, 512 dimensions): Actions median 0.840 (lowest tenth 0.587), States median 0.845 (lowest tenth 0.734).

## Does the future leak into a State?

Share of States that use a word (five letters or more) which is in no turn up to theirs and is in a later turn:

| | States | with a future word | share |
|---|---|---|---|
| per turn | 115 | 32 | 28% |
| per conversation | 115 | 24 | 21% |

## Do the descriptions tell the planted labels apart?

The chance that two descriptions with the same planted label are more alike than two with different labels (0.5 is chance, 1 perfect).

| | per turn | per conversation | same-label pairs |
|---|---|---|---|
| action vs the planted action | 0.887 | 0.911 | 557 |
| state vs the planted domain | 0.840 | 0.747 | 1904 |
| state vs the planted stage | 0.579 | 0.619 | 1521 |

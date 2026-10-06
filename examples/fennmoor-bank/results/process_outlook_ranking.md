# Process abstraction, phase 4: three attempts to fix the ranking, none kept

The outlook's recommendation (the Action whose cases ended best after it) was right 24% of the time where it had a recommendation, against 26% for the
rep and 20% for what reps most often did, and **16% where a true clue was still waiting to be asked** (below chance). Three changes were tried, on the
**tuning conversations** (the first 600 by id, 2,318 decision points, Actions at level 2, prior 50), and each is a worse or no better ranking. None was
chosen, so none was run on the holdout. The code for them was taken out again; this is the record. "Useful": a remedy that fixes the real cause, or a
question for a clue that is true and not yet said. "Waiting" and "no clue waiting" are the answer key's view of the point, which the tool never sees.

| change | useful, of all points | where the graph had a recommendation | | |
|---|---|---|---|---|
| | | all | a clue waiting | no clue waiting |
| **as built** (best ending after) | **22%** | **24%** | 16% | 30% |
| **1. value the best follow-up, not the average one** (the chain with a maximum where it has an average, so an Action that opens the way to a good follow-up is worth that; a follow-up counts if reps took it 3 or 10 times from the State) | 19% (both) | not recorded | 14% (of all points; as built: 14%) | 23% (as built: 27%) |
| **2. recommend only an Action taken often enough from here** (3, 10, 20, 40, 80 pooled cases) | 22%, 17%, 15%, 12%, 5% | 24%, 22%, 23%, 25%, 35% | 16%, 19%, 19%, 27%, 32% | 30%, 24%, 26%, 23%, 38% |
| **3. where reps mostly ask from here, recommend the best question, else the best remedy** (asking verbs Ask, Check, Review; the share of the pooled next Actions that ask: 0.5 / 0.3 / 0.7) | 18% / 20% / 19% | 20% / 22% / 21% | 16% / 22% / 12% | 23% / 21% / 27% |
| 3, with Verify and Confirm counted as asking (0.5) | 14% | 15% | 15% | 16% |

(Coverage falls as the support asked for rises: 91%, 75%, 65%, 47% and 16% of points for change 2. The rep's own useful share over the covered points was
24%, 26%, 27%, 29% and 35%: at every threshold it is at least the graph's. At 80 the graph is simply what reps most often did.)

## Why none works

- **Change 1** gave questions no more value than closers: by Action type the value of the best continuation is 0.72 for questions against 0.84 for offers,
  0.87 for answers and 0.80 for verification. A text-rated ending is as good after a confident wrong fix (the customer takes the refund and stays) as
  after a right one, so a closer's ending is high whatever the cause, and asking buys nothing in those numbers.
- **The confounder is the cause the rep knows and the State does not say.** A rep who offers a fee refund usually knows the customer's problem is a fee;
  the cases where it was offered ended well because of the cases it was offered in. Pooled at a State whose text does not tell the causes apart, that
  success is credited to every case there (under change 1 `ACT-OFFER-FEE-REFUND` was the recommendation at 135 of the 955 points where a clue was waiting). No weighting of what was observed can
  undo a variable that was never recorded; what could is the cause, which is exactly what asking finds out.
- **Change 2** only walks back to what reps most often did, and **change 3** swaps one weak signal for another: the share of reps' next Actions that ask
  does not say whether a clue is waiting (at 0.3 it helps where one is and hurts where none is, and the sum is lower).

So the finding stands as phase 4 reported it: the outlook is a good picture of where a case stands and how cases like it ended, a poor guide to the single
best next Action, and a recommendation from it should not be offered as advice.

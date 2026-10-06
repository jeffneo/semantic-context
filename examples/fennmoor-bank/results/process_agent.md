# Process abstraction, phase 5: does the outlook help an agent choose?

200 decision points, one per holdout conversation, half where a true clue is waiting and half where none is. Each is put to claude-sonnet-5-5 with the call so far and the menu of the procedure's actions, with different things beside it. Useful: a remedy that fixes the real cause, or a question for a true, unsaid clue (the answer key's view; the agent never sees it). The outlook and the context are what the tool and the warehouse hold with the conversation taken out; the knowledge is the world's own tables as a designed ontology (an experiment).

| | all points (n=200) | a clue is waiting (n=100) | no clue waiting (n=100) |
|---|---|---|---|
| alone | 12% [9%, 18%] | 14% [9%, 22%] | 11% [6%, 19%] |
| outlook | 11% [7%, 16%] | 13% [8%, 21%] | 9% [5%, 16%] |
| call record | 31% [25%, 38%] | 35% [26%, 45%] | 27% [19%, 36%] |
| fees and purchases | 13% [9%, 18%] | 13% [8%, 21%] | 13% [8%, 21%] |
| context (both) | 33% [27%, 40%] | 38% [29%, 48%] | 28% [20%, 37%] |
| knowledge | 18% [13%, 23%] | 22% [15%, 31%] | 13% [8%, 21%] |
| context + knowledge | 30% [24%, 36%] | 32% [24%, 42%] | 27% [19%, 36%] |
| all three | 28% [22%, 35%] | 34% [25%, 44%] | 22% [15%, 31%] |
| the rep | 28% [22%, 35%] | 29% [21%, 39%] | 27% [19%, 36%] |
| the typical rep | 22% [17%, 28%] | 26% [18%, 35%] | 18% [12%, 27%] |
| the graph's best ending | 24% [18%, 30%] | 18% [12%, 27%] | 29% [21%, 39%] |
| chance, among the procedure's actions | 13% | 16% | 9% |
| the best single action, with hindsight | 15% (ASK-REASON-FOR-CLOSING) | 30% (ASK-REASON-FOR-CLOSING) | 14% (GIVE-BALANCE) |

What each arm chooses, as a share of all points:

| class | alone | outlook | call record | fees and purchases | context (both) | knowledge | context + knowledge | all three | the rep | the typical rep | the graph's best ending |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fixes the cause | 8% | 7% | 16% | 8% | 16% | 8% | 16% | 13% | 18% | 12% | 21% |
| asks for a true, unsaid clue | 5% | 4% | 15% | 5% | 16% | 10% | 13% | 15% | 10% | 10% | 2% |
| partly fixes it | 0% | 2% | 0% | 0% | 0% | 0% | 0% | 0% | 2% | 2% | 3% |
| does nothing for it | 0% | 4% | 0% | 0% | 0% | 0% | 0% | 2% | 3% | 2% | 18% |
| makes it worse | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 2% | 0% | 2% |
| asks for nothing new | 14% | 15% | 32% | 13% | 33% | 24% | 40% | 38% | 17% | 11% | 5% |
| verifies identity | 67% | 67% | 26% | 68% | 25% | 55% | 24% | 26% | 20% | 42% | 17% |
| hands off | 4% | 0% | 6% | 4% | 5% | 4% | 3% | 2% | 10% | 2% | 2% |
| other | 2% | 2% | 4% | 1% | 3% | 1% | 3% | 4% | 18% | 12% | 21% |

Paired against the agent alone (points where one is useful and the other is not; two-sided sign test):

| arm | better | worse | p |
|---|---|---|---|
| outlook | 4 | 7 | 0.549 |
| call record | 44 | 7 | 0.000 |
| fees and purchases | 3 | 2 | 1.000 |
| context (both) | 48 | 7 | 0.000 |
| knowledge | 12 | 2 | 0.013 |
| context + knowledge | 43 | 9 | 0.000 |
| all three | 43 | 12 | 0.000 |
| the rep | 49 | 18 | 0.000 |

1600 calls, 1000 made and 600 from the cache, $5.32, 412 s.

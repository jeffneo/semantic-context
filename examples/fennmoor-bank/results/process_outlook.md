# Process abstraction, phase 4: the outlook

The 5 nearest States by the vector index, weighted by exp(-distance / 1.0); Actions read at level 2, pulled toward their own rate by 50 pseudo-transitions; a pool under 3 conversations carries no odds. Every number takes the conversation scored out of the counts first. Holdout: the 1432 conversations after the first 600 by id.

## Nearness: Brier score for the odds of ending well, at checkpoints (planted favourability; the difference from the global rate, 95%)

| arm | 1st (n=1432) | 2nd (n=1432) | 3rd (n=1374) | 4th (n=1092) | 6th (n=372) | the last (n=1432) | all (n=7134) |
|---|---|---|---|---|---|---|---|
| global rate | 0.237 | 0.237 | 0.234 | 0.229 | 0.240 | 0.237 | 0.236 |
| the State the build assigned | 0.224 (-0.013 ± 0.008) | 0.211 (-0.026 ± 0.006) | 0.193 (-0.041 ± 0.008) | 0.185 (-0.044 ± 0.009) | 0.228 (-0.012 ± 0.013) | 0.179 (-0.058 ± 0.009) | 0.201 (-0.039 ± 0.005) |
| the nearest State by the index | 0.225 (-0.013 ± 0.008) | 0.211 (-0.026 ± 0.005) | 0.194 (-0.040 ± 0.007) | 0.187 (-0.043 ± 0.009) | 0.231 (-0.009 ± 0.014) | 0.182 (-0.055 ± 0.008) | 0.202 (-0.037 ± 0.005) |
| the pool of the nearest States | 0.217 (-0.020 ± 0.010) | 0.198 (-0.040 ± 0.008) | 0.184 (-0.050 ± 0.011) | 0.175 (-0.055 ± 0.012) | 0.212 (-0.028 ± 0.022) | 0.142 (-0.095 ± 0.011) | 0.185 (-0.058 ± 0.008) |

Coverage: the State the build assigned **66%**, the nearest State by the index **63%**, the pool of the nearest States **100%**.
Paired, the pool of the nearest States minus the State the build assigned: **-0.0198 ± 0.0057**.
Paired, the pool of the nearest States minus global rate: **-0.0584 ± 0.0083**.

## Validity: is the Action the graph recommends one that works? (holdout)

Useful: a remedy that fixes the real cause, or a question for a clue that is true and not yet said.

| | all decision points (n=5264) | a clue is waiting (n=1923) | no clue waiting (n=3341) |
|---|---|---|---|
| **the graph: best ending after**: useful | 22% [21%, 24%] | 15% [13%, 16%] | 27% [26%, 29%] |
| the graph: has a recommendation (supported) | 92% [91%, 93%] | 92% [91%, 93%] | 92% [91%, 93%] |
| the graph: what reps most often did: useful | 19% [17%, 20%] | 26% [24%, 28%] | 14% [13%, 16%] |
| the rep: useful | 25% [24%, 26%] | 26% [24%, 28%] | 24% [23%, 26%] |
| chance, among the procedure's actions | 11% | 16% | 9% |
| the best single action, with hindsight | 11% (ASK-WHAT-HAPPENED) | 31% (ASK-WHAT-HAPPENED) | 10% (PROCESS-CLOSURE) |
| some useful action existed in the procedure | 100% | 100% | 100% |

Where the graph had a recommendation, the same points, the rep against the graph (useful):

| | all decision points (n=4841) | a clue is waiting (n=1767) | no clue waiting (n=3074) |
|---|---|---|---|
| the graph: best ending after | 24% [23%, 26%] | 16% [14%, 18%] | 29% [28%, 31%] |
| the graph: what reps most often did | 20% [19%, 21%] | 28% [26%, 30%] | 16% [14%, 17%] |
| the rep | 26% [24%, 27%] | 27% [25%, 29%] | 25% [23%, 26%] |

What each arm's action is, at all decision points where the graph had a recommendation:

| class | the graph: best ending after | the graph: what reps most often did | the rep |
|---|---|---|---|
| fixes the cause | 23% | 12% | 19% |
| asks for a true, unsaid clue | 1% | 8% | 7% |
| partly fixes it | 3% | 1% | 1% |
| does nothing for it | 20% | 3% | 3% |
| makes it worse | 3% | 0% | 1% |
| asks for nothing new | 5% | 21% | 20% |
| verifies identity | 16% | 36% | 20% |
| hands off | 1% | 1% | 4% |
| other | 26% | 17% | 25% |

Agreement: graph = rep 39%; graph = what reps most often did 39%; rep = what reps most often did 53%.

Where reps took the Action the graph recommends and where they did not, how the conversations ended (planted favourability high; observational: reps who differ from the graph may be in harder cases, and the points of one conversation are not independent):

| the rep | points | ended well |
|---|---|---|
| took the graph's recommendation | 1898 | 75% [73%, 77%] |
| took something else | 2943 | 61% [59%, 63%] |

## Confounding: by the rep's archetype

| rep | points | the graph (useful) | what reps most often did | the rep | graph = most-common |
|---|---|---|---|---|---|---|
| Methodical | 1734 | 23% [21%, 25%] | 20% [18%, 22%] | 26% [24%, 28%] | 37% |
| Rushed and queue-driven | 825 | 22% [19%, 25%] | 18% [16%, 21%] | 24% [21%, 28%] | 40% |
| Follows the script | 1442 | 26% [23%, 28%] | 22% [20%, 25%] | 27% [24%, 29%] | 40% |
| Warm but imprecise | 1263 | 27% [24%, 29%] | 19% [17%, 21%] | 25% [23%, 27%] | 42% |

## by the customer's archetype

| customer | points | the graph (useful) | what reps most often did | the rep | graph = most-common |
|---|---|---|---|---|---|---|
| Angry, wants a manager | 747 | 24% [21%, 27%] | 19% [16%, 22%] | 23% [20%, 27%] | 43% |
| Clear and observant | 1089 | 28% [25%, 31%] | 19% [17%, 22%] | 26% [24%, 29%] | 39% |
| Not paying close attention | 807 | 24% [22%, 28%] | 19% [16%, 22%] | 25% [22%, 28%] | 40% |
| Sure they know the cause, and wrong | 938 | 22% [19%, 24%] | 20% [17%, 23%] | 24% [21%, 27%] | 39% |
| Plain-spoken | 1683 | 24% [22%, 26%] | 22% [20%, 24%] | 27% [25%, 29%] | 38% |

## Cost of a live outlook

30 outlooks at random turns of holdout conversations: median **3.4 s**, at most 3.7 s, with the turn's annotation answered from the cache (0 calls, 30 cached). A turn the build had not seen costs one Haiku call: about 1.1 s and $0.0008, from the build's own record. The service ceiling is 30 s and 20,000 tokens.

105 seconds for the scoring.

# Process graph, phase 5: the context a call is about, as of the call

100 conversations (40 Fee, 40 Merchant, 20 neither); a group is what the answer key says the conversation names. Each context is fetched as of the call's day: 5.4 s median, 15 minutes for all.

## Retrieval: is the row the call is about in the context?

- 0 reads were retried after the virtual graph refused them once.
- 6 of the 100 calls had no customer on them (nobody was identified): no context to fetch.
- As of the call: **80 of 80** named rows were in the context (merchants from the virtual graph, fees from the warehouse).
- Memory's ordinary window would have put **13,609 facts into the contexts that postdate their calls** (6,253 CardTransaction, 7,137 DepositTransaction, 219 Call), of 32,165 nodes: what the warehouse did not yet hold when the call was made.

## Linking: of the rows retrieved, are the right ones found from the words? (precision / recall)

| | Merchant (by amount and name) | Fee (by amount) |
|---|---|---|
| the turns alone | 100% / 98% (39 found, 0 wrong, 1 missed) | 100% / 100% (40 found, 0 wrong, 0 missed) |
| the turns and the after-call note | 100% / 100% (40 found, 0 wrong, 0 missed) | 100% / 100% (40 found, 0 wrong, 0 missed) |

The control conversations (the answer key names neither) are in the precision: a link there is a wrong one.

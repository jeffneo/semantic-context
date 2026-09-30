# Memory: the agent's side, in the Context Memory model

The example's conversations (`conversations/*.yaml`), recorded with `qlsc converse`, and the graph they left, checked (plans/2026-09-29-context-memory-model.md). The labels are Conversation, Message, Task, Step, Decision, Fact and Entity. The warehouse facts `remember` keeps are the long-term memory, under their own labels.

**26 of 26 checks passed.**

| check | result |
|---|---|
| marketing-1: messages, in order | ok |
| marketing-1: a task per request, its steps in order | ok |
| marketing-1: step 1 (recall, from memory) | ok |
| marketing-1: step 2 (ask) | ok |
| marketing-1: mentions are the warehouse's Customer | ok |
| marketing-2: messages, in order | ok |
| marketing-2: a task per request, its steps in order | ok |
| marketing-2: step 1 (recall, from memory) | ok |
| marketing-2: mentions are the warehouse's Customer | ok |
| risk-1: messages, in order | ok |
| risk-1: a task per request, its steps in order | ok |
| risk-1: step 1 (recall, from memory) | ok |
| risk-1: mentions are the warehouse's Customer | ok |
| marketing-1: the decision, ABOUT the customer, BASED_ON two facts and the ask | ok |
| marketing-2 finds marketing-1's notes | ok |
| changed: the new preference closes the old, and the decision based on it is to revisit | ok |
| an outcome is a fact about its decision | ok |
| corrected: the old fact never held | ok |
| marketing-1: every node it wrote is its principal's, and private | ok |
| marketing-2: every node it wrote is its principal's, and private | ok |
| risk-1: every node it wrote is its principal's, and private | ok |
| the data source sees nothing of marketing's notes | ok |
| marketing sees nothing of risk's notes on a Kansas customer | ok |
| risk sees its own | ok |
| risk can't note a customer outside its rows | ok |
| a refetch leaves them attached | ok |

## What recall noted

Before marketing-2:

    noted: interested in: a travel rewards card (since 2026-09-30)
    noted: prefers contact channel: email, not phone (since 2026-09-30)
    noted: Ana (person), daughter of
    decided: offer a travel rewards card, by email (on 2026-09-30)
    in 1 conversation, the last 2026-09-30: Card offer for customer 8322097816940277129

After marketing-2:

    noted: interested in: a travel rewards card (since 2026-09-30)
    noted: prefers contact channel: phone, mornings (since 2026-09-30)
    noted: Ana (person), daughter of
    decided: offer a travel rewards card, by email (on 2026-09-30; outcome: accepted; revisit: prefers contact channel: email, not phone is now phone, mornings)
    in 2 conversations, the last 2026-09-30: Travel card follow-up for customer 8322097816940277129

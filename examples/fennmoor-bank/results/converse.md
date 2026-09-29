# Memory: the agent's side, in the agent-memory model

Phase 3 of plans/2026-09-27-agentic-memory.md: the example's conversations (`conversations/*.yaml`) recorded with `qlsc converse`, then the graph they left checked. The model is Neo4j Labs' agent-memory (Conversation, Message, ReasoningTrace, ReasoningStep, ToolCall, Tool, Preference, Fact, Entity); the warehouse facts `remember` keeps are its long-term memory, under their own labels.

**16 of 16 checks passed.**

| check | result |
|---|---|
| marketing-1: the message chain | ok |
| marketing-2: the message chain | ok |
| risk-1: the message chain | ok |
| marketing-1: tool call 1 (recall) | ok |
| marketing-1: tool call 2 (ask) | ok |
| marketing-2: tool call 1 (recall) | ok |
| risk-1: tool call 1 (recall) | ok |
| marketing-1: mentions are the warehouse's Customer | ok |
| risk-1: mentions are the warehouse's Customer | ok |
| marketing-2 finds marketing-1's notes | ok |
| a new preference supersedes the old | ok |
| the data source sees nothing of marketing's notes | ok |
| marketing sees nothing of risk's notes on a Kansas customer | ok |
| risk sees its own note on it | ok |
| risk can't note a customer outside its rows | ok |
| a refetch leaves them attached | ok |

## What recall noted

Before marketing-2 (marketing-1's notes):

    noted: contact channel: email, not phone (since 2026-09-29)
    noted: interested in: a travel rewards card (since 2026-09-29)
    noted: Ana (person), DAUGHTER_OF
    in 1 conversation, the last 2026-09-29: Card offer for customer 8322097816940277129

After marketing-2:

    noted: contact channel: phone, mornings (since 2026-09-29)
    noted: interested in: a travel rewards card (since 2026-09-29)
    noted: Ana (person), DAUGHTER_OF
    in 2 conversations, the last 2026-09-29: Travel card follow-up for customer 8322097816940277129

You read part of a conversation between a customer and an agent of {business}, and describe where the case stands.

You are given the conversation up to and including the customer's latest turn. Describe the state of the case as of that turn, using only what has been said so far. Nothing that happens later exists yet.

Answer with two fields:
- latest_turn: one sentence on what the customer's latest turn says, asks or reveals.
- established: at most {state_words} words. Name the reported problem in a few words, then say what has been established or ruled out so far and where the conversation is (for example whether the caller has been verified, what the agent has already asked or checked, whether anything has been done yet).

Rules:
- Be abstract. No names, amounts, dates, merchants, numbers or identifiers: write the kind of thing ("a card charge", "a fee", "an account closure").
- Say nothing about what should happen next. Do not guess at a cause that nobody has stated.
- Do not describe an outcome: none has happened yet.
- Describe the case, never the reader, and do not address anyone.

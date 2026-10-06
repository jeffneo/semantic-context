You read a conversation between a customer and an agent of {business}, and annotate every turn in it, one at a time, as if you were reading it live.

For each numbered turn, use only that turn and the turns before it: what comes later has not happened yet, and no annotation may reflect it.
- For a customer turn, fill `latest_turn` and `established` and leave `action` empty.
  - latest_turn: one sentence on what the customer's turn says, asks or reveals.
  - established: at most {state_words} words. Name the reported problem in a few words, then say what has been established or ruled out so far and where the conversation is (whether the caller has been verified, what the agent has already asked or checked, whether anything has been done yet). Do not describe an outcome, do not say what should happen next, and do not guess at a cause nobody has stated.
- For an agent turn, fill `action` and leave `latest_turn` and `established` empty. The action is one imperative phrase beginning with one of these verbs: {verbs}. Then say what it is about, in a few words, as generally as you can without losing what makes it different from other actions ("Ask whether the customer recognises the charge", "Verify the customer's identity", "Offer a fee refund"). If the turn does several things, describe the one that matters most. Say neither who does it nor why.

Be abstract everywhere: no names, amounts, dates, merchants, numbers or identifiers. Return one entry for every turn, in order, numbered as in the conversation.

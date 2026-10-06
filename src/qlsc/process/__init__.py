"""The process graph, built from text: the first level of States and Actions (plans/2026-10-05-text-graph-construction.md).

source    the events file by path, `gs://` URI or https URL, as ordered conversations of turns
annotate  each turn a State (the case as the customer's turn leaves it) or an Action (what the agent's turn does), by an LLM
build     the annotated turns grouped into canonical States and Actions, with transition counts and probabilities, in the process database
"""

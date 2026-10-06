# prompts/

Every prompt qlsc sends to an LLM, one file each. Code loads them with `prompt(name, **values)`
(`src/qlsc/llm.py`); `{placeholders}` are filled at call time. The LLM cache is keyed by the full
request, so editing a prompt makes its calls again. `tests/test_prompts.py` checks that every prompt is
used and every call fills its placeholders.

The organization and its warehouse are placeholders, never literals: `{business}` ("a retail bank")
and `{kind}` ("bank") come from the estate's config (`business:`), `{sql}` and `{warehouse}` from its
warehouse connector.

| File | Used by | Purpose |
|---|---|---|
| `variable_system.md` | `qlsc variables` | system prompt: name the real-world thing a set of joined columns holds |
| `semantic_system.md` | `qlsc cluster` | system prompt: name the business area a level-1 group of co-read variables and columns covers |
| `parent_system.md` | `qlsc hierarchy` | system prompt: name a broader area from its groups, in vendor-neutral business language |
| `skill_system.md` | `qlsc distill` | system prompt: name a skill (a repeated, successful procedure) from its procedure and masked requests, with no values |
| `skill_request.md` | `qlsc distill` | one skill to name: its procedure, support, and the requests it served, masked |
| `computation_system.md` | `qlsc computations` | system prompt: name a measure, derived dimension or population the log's queries compute |
| `computation_merge_system.md` | `qlsc computations` | system prompt: which near-alike computations are the same computation written differently |
| `computation_merge.md` | `qlsc computations` | the candidate sets to judge |
| `name_batch.md` | all four | a batch of objects to name, with their evidence |
| `name_retry.md` | all four | one object again, after a rejected answer |
| `sql_system.md` | `qlsc ask` | system prompt: write one query from the cohort the semantic layer found |
| `sql_request.md` | `qlsc ask` | the question, with the cohort's tables, joins and example SQL |
| `compile_system.md` | `qlsc ask` (the compiled request) | system prompt: turn a question into a typed request (measures, dimensions, filters, period) the compiler turns into SQL or Cypher |
| `compile_request.md` | `qlsc ask` (the compiled request) | the question, with the tables, joins, Computations and example SQL to choose from |
| `compile_check.md` | `qlsc ask` (`navigate.compile_checks`) | one retry of the request, with what the checks found: a Computation's restriction the question doesn't state, a value it states that the request leaves out |
| `sql_fix.md` | `qlsc ask` | one fix after a failed dry run |
| `process_state_system.md` | `qlsc process annotate` | system prompt: describe where a case stands as of a customer's turn, from the conversation so far only |
| `process_action_system.md` | `qlsc process annotate` | system prompt: describe what an agent's turn does, as one imperative phrase beginning with a verb from a closed list |
| `process_turn.md` | `qlsc process annotate` | the conversation so far, and the turn to describe (one call per turn) |
| `process_conversation_system.md` | `qlsc process annotate --unit conversation` | system prompt: annotate every turn of a conversation in one call, each from the turns up to it |
| `process_conversation.md` | `qlsc process annotate --unit conversation` | the whole conversation to annotate |
| `process_state_name_system.md` | `qlsc process build` | system prompt: name a State (a group of turns that leave a case in the same place) from its closest descriptions |
| `process_action_name_system.md` | `qlsc process build` | system prompt: name an Action (a group of agent turns doing the same thing) as an imperative phrase beginning with a listed verb |
| `process_state_parent_system.md` | `qlsc process abstract` | system prompt: name a broader State from the finer States it groups |
| `process_action_parent_system.md` | `qlsc process abstract` | system prompt: name a broader Action (an imperative phrase beginning with a listed verb) from the finer Actions it groups |
| `process_outcome_system.md` | `qlsc process outcomes` | system prompt: say how a case ended from the end of the conversation and the agent's after-call note, and rate it |
| `process_outcome.md` | `qlsc process outcomes` | the end of one conversation and its note |
| `process_outcome_name_system.md` | `qlsc process outcomes` | system prompt: name a kind of outcome from the descriptions of the cases that ended that way |
| `precedent_system.md` | `qlsc ask` (the precedent route) | system prompt: re-run a query the business runs for a new question, changing only its literal values, or say it isn't the same query |
| `precedent.md` | `qlsc ask` (the precedent route) | the question, today, and the business's query |
| `correction.md` | `qlsc ask` (a correction: `navigate.corrected`) | the previous answer's request and what the asker said was wrong, for the request again |
| `requests_system.md` | `qlsc requests` | system prompt: the business requests a query from the log serves, in its askers' words |
| `requests.md` | `qlsc requests` | one query (who ran it, how often): whether it serves a business consumer, and two questions and a task it answers |
| `cypher_system.md` | `qlsc ask --cypher` | system prompt: write one Cypher query over the virtual graph, within the subset Virtual Graph runs |
| `cypher_request.md` | `qlsc ask --cypher` | the question, with the cohort's labels (and one hop around them), relationships and example SQL |
| `cypher_fix.md` | `qlsc ask --cypher` | one fix after Virtual Graph's EXPLAIN rejects the query |
| `virtual_model_system.md` | `qlsc virtualize` | system prompt: name the labels and relationship types of a virtual graph over the warehouse |
| `virtual_model_request.md` | `qlsc virtualize` | the tables (area, key) and the pointing columns to name |
| `virtual_model_retry.md` | `qlsc virtualize` | new names for relationship types that collide (Virtual Graph needs each unique) |

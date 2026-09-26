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
| `name_batch.md` | all three | a batch of objects to name, with their evidence |
| `name_retry.md` | all three | one object again, after a rejected answer |
| `sql_system.md` | `qlsc ask` | system prompt: write one query from the cohort the semantic layer found |
| `sql_request.md` | `qlsc ask` | the question, with the cohort's tables, joins and example SQL |
| `sql_fix.md` | `qlsc ask` | one fix after a failed dry run |

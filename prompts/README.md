# prompts/

Every prompt the pipeline sends to an LLM, one file each. Code loads them with `pipeline/llm.py`
`prompt(name, **values)`; `{placeholders}` are filled at call time. Changing a file changes the request,
so the call is made again (the caches are keyed by the full request).

| File | Used by | Purpose |
|---|---|---|
| `variable_system.md` | `pipeline/variables.py` | system prompt: name the real-world thing a set of joined columns holds |
| `variable_batch.md`, `variable_retry.md` | `pipeline/variables.py` | a batch of variables; one retry after a rejected answer |
| `semantic_system.md` | `pipeline/cluster.py` | system prompt: name the business area a Leiden group of co-read variables and columns covers |
| `semantic_batch.md`, `semantic_retry.md` | `pipeline/cluster.py` | a batch of groups; one retry |
| `parent_system.md` | `pipeline/hierarchy.py` | system prompt: name a broader area from its child Semantic groups |
| `parent_batch.md`, `parent_retry.md` | `pipeline/hierarchy.py` | a batch of areas; one retry |
| `describe_system.md` | `pipeline/semantics.py` (previous model) | system prompt for table / variable / subject names and descriptions |
| `describe_batch.md`, `describe_retry.md` | `pipeline/semantics.py` | a batch of objects; one retry |
| `abbreviation_sense.md` | `pipeline/semantics.py` | what an ambiguous abbreviation (CC) means in one table |
| `domains.md` | `pipeline/semantics.py` | propose business domains over subjects |
| `answer_common.md`, `answer_semantic.md`, `answer_baseline.md` | `pipeline/answer.py` (previous model) | the question-answering agent; common contract plus semantic-layer or catalog-only instructions |

The must-handle judge prompt in `specs/tools/score.py` is part of the scorer, not the pipeline, and stays there.

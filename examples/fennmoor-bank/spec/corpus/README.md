# spec/corpus: the world the process corpus is generated from

The answer key for the unstructured process corpus ([plan](../../../../plans/2026-10-05-process-corpus.md)). Nothing
here is read by `src/qlsc/`; the generator (`generate/corpus.py`) and the scorer read it, and the process graph is later
scored against it.

The model is a causal chain, as in the call-transcripts demo it follows. What is actually going on (a **cause**) shows up
in the world as **manifestations**; a customer **perceives** some of them (salience, scaled by attentiveness) and
**volunteers** some of those unprompted (scaled by how forthcoming they are); a rep **elicits** the rest only by asking.
The rep walks a **procedure** (stages of **actions**), a sampled **archetype** decides how well; each committing action
has an **efficacy** against the real cause, and the **outcome** is derived from the walk, never sampled.

| File | What it holds |
|---|---|
| `domains.yaml` | the five areas, with the share of the corpus each gets |
| `causes.yaml` | what is actually going on, with the manifestations each produces and what the warehouse must hold for it to be drawn |
| `manifestations.yaml` | what is perceivable: salience, whether volunteered, whether it separates causes |
| `actions.yaml` | everything a rep can do |
| `efficacy.yaml` | whether an action addresses the real cause (sparse: unlisted means no effect) |
| `procedures.yaml` | which intents enter each procedure, the causes it can consider, its stages |
| `policies.yaml` | gates a rep can skip; a skipped gate is a recorded breach |
| `outcomes.yaml` | derived outcomes, in evaluation order, with recurrence |
| `reps.yaml`, `customers.yaml` | archetypes, and the site effects planted on the contact-center sites |

Check it with `uv run examples/fennmoor-bank/generate/corpus.py --validate-world` (no data, no warehouse).

There are no expression templates in v1: the realiser (phase B) is given a manifestation's label and the customer's
archetype and chooses the words itself, and the validator checks the text against the plan.

Check a written corpus with `corpus.py --audit` (it reads the outputs back against the plans, the rows and the world, and spends
nothing). What the text knowledge-graph builder may read, and what it is scored against, is in the plan's hand-off section.

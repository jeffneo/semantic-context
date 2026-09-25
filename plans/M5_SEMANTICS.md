# M5: naming, embeddings, retrieval

Status: complete, 2026-09-24. Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Stage 6).
Code: `pipeline/semantics.py` (naming and embeddings), `pipeline/retrieve.py` (question → tables).
Scorer: `specs/tools/score.py` (M5 section).

## Models (D4)

- **Naming: `claude-haiku-4-5-20251001`, no extended thinking.** The user asked for "Claude
  Haiku 5", which this account does not have. The models listing shows Opus 5.5, Fable 5.1,
  Sonnet 5, Opus 5 and Fable 5, and Haiku 4.5 is the newest Haiku. It is one line in
  `estate.yaml` (`llm.model`).
  The SDK does not accept `temperature` for these models, so determinism comes from the
  cache, keyed by input hash.
- **Embeddings: Azure OpenAI `text-embedding-3-large` at 512 dimensions.** The deployment
  name was found by listing deployments.
- **Cost:**
  - LLM, from scratch: about $1.70.
  - LLM, this whole iterative session: about $4.60.
  - Embeddings: negligible.
  - A graph rebuild with unchanged evidence: $0, because every call is cached.

## What the LLM is allowed to do

It names structure usage already established (tables, then variables, then subjects), from
the evidence the graph holds for each:
- columns with their variables and roles;
- where the data comes from;
- tables it is queried with;
- who uses it;
- relevant findings, including findings on its columns;
- a sample query.

The single exception: it **proposes** domains, grouping subjects. These are stored as
`(:Domain {status: 'proposed'})` for a person to confirm.

- **Abbreviations.**
  - A glossary is mined from the business's own renames: 82 abbreviations, including
    initialisms, for example `CC_ID → cost_center_id`. It is shown as "how other tables rename
    it; may not apply here".
  - Abbreviations in object names that the estate expands more than one way get a focused
    per-object question, and the object is then re-described with the answer as a fact.
    Six were found: CC, CD, CDR, FCT, KYC and P2P.
  - Without that pass, `CC_EXPNS_MTHLY` was read as contact center, because it is queried
    with call-volume tables, although its own `CC_ID` belongs to the cost-center id space.
- **Contract.** Output is forced through a tool schema. Before anything is stored, it is
  validated:
  - a name of 1–6 words;
  - a description of 20–400 characters that says more than the name;
  - no boilerplate;
  - no identifiers outside the evidence;
  - the name and its abbreviation list agree (plural-tolerant, applied to the object's own
    name tokens).

  A failure gets one retry with the error. A second failure is recorded, never dropped.
- **Embeddings.** One structured document per node (name, description, id, subject,
  columns), mean-centered per label and normalized, in a cosine vector index. The means are
  on `(:EmbeddingSpace)`.

## Retrieval

The question is centered the same way and searched against tables, subjects and variables.
A table inherits its subject's and columns' matches, discounted, taking the best of the
three. A small usage prior is added: `0.03 × log(1 + principals consuming it)`.

## Score (2026-09-24)

| | Result |
|---|---|
| Descriptions | Tables 322 + 1 retried; variables 1,358 + 28 retried; subjects 100. **0 failed, 0 boilerplate** |
| F04 | **pass**: CC expanded correctly in 8/8 tables (credit card, contact center, cost center); the `CC_ID = SITE_CD` join flagged (M3) |
| Retrieval (14 questions) | **hit@5 100%**, recall@10 **72%**, recall@5 51% |
| without the usage prior | recall@10 56%: what the business uses is a strong signal |
| tables only | the same as the full combination: subject and variable matches add nothing under the max-combination (left untuned) |
| Traps in the top 10 | 16 (for example, Q05's top 3 is the whole deprecated legacy balance chain). Steering away from them with the findings is M6 |
| Proposed domains | NMI **0.760** against the spec's 15 domains (M4's graph-only areas: 0.683) |
| Descriptions mean the right thing | for 43/49 (88%) identifier variables, the nearest spec concept to the generated description is the right one, among 57 |

Q13 ("what is in the tables whose names start with CC?") retrieves poorly by meaning (17%).
It is a question about names, which M6 should answer with a name match, not a vector search.

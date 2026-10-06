# Process abstraction: levels, where a case ends, and what to do next

Status: agreed (2026-10-06, every recommendation taken); phases 1 and 2 built and measured. The third of the process work's plans, after [the corpus](2026-10-05-process-corpus.md) and
[extraction and construction](2026-10-05-text-graph-construction.md) (both built). It starts from the first-level State-Action graph those
produced and supersedes the phases of [the earlier process plan](2026-10-03-business-process-graph.md) that read event rows (its
retrieval, governance and evaluation ideas are carried here; its structured-source miner stays parked). Phases 1 (levels) and 2 (outcomes) are built; the rest is not.

## What this plan is for

The first-level graph is **faithful and fine**: 3,044 States and 1,017 Actions from 19,360 turns, with transition counts and probabilities
that correlate 0.91 with the planted ones. It is not yet **useful**, for three measured reasons:

| What the first level showed (holdout of 1,432 conversations) | What it means |
|---|---|
| About 800 Action elements for 64 planted actions (completeness 0.65); a quarter of State turns sit in a State no other turn shares | Too fine to reason over, and too sparse to recommend from. Needs **coarser levels**. |
| Nothing says where a case ends: `ends` counts turns after which nothing followed, but a closing line ("thanks, bye") ends a good call and a bad one alike | Needs **outcomes**: how likely a State is to end well, and in what. |
| The likeliest next Action asks the discriminating question 7% of the time, the reps 10%, the oracle graph 7%, the best single question chosen with hindsight 19% | A graph of what people usually do can only match the reps. To beat them it must rank Actions by **where they lead**. |

So the plan has three parts, in this order, and an end-to-end test of whether they add up to something an agent can use:

1. **Levels:** a hierarchy over the States and over the Actions, built from the first level's own embeddings, with the transitions lifted to
   each level.
2. **Where a case ends:** an outcome for each conversation, found from the text, and from it the **absorbing probabilities on States**
   (your earlier idea, in place of a separate Resolution label): how likely a State is to end well, and in what.
3. **What to do next:** at a State, the next Actions ranked by the outcome they lead to, with the evidence behind each, put beside the
   customer's context as of the call (phase 5 of the last plan). Offered as `qlsc process outlook` and as agent tools beside `ask` and
   `recall`.

## What is taken from what exists

- **Levels** follow `qlsc/hierarchy.py`, which builds the semantic layer's levels 2 and up: embed each node, link each to its k nearest
  (`K_SIM`), seeded single-threaded Leiden at a resolution that falls with the level (`gamma / (L - 1)`), name each community in general
  language, stop when a level would not be smaller. There is no usage signal here (that layer's level 1 is built from usage), so the score is
  text alone, and the transitions themselves can stand in for usage: two Actions that follow the same States, or two States that
  lead to the same Actions, are alike. Whether that helps is measured (phase 1), not assumed.
- **The graph's stored vectors.** Every element already carries the mean embedding of its turns; levels above embed from those and from
  their members' names, so no turn is annotated or embedded again.
- **The scorer** (`eval/process_graph.py`): three arms (graph, raw text, oracle), the holdout (conversations 600 and up by id; parameters are
  chosen below that), Wilson intervals, V-measure by planted label, leave-one-conversation-out. It gains a level axis and the outcome
  metrics below.
- **The context** (`qlsc process context`): the customer's rows as of the call, and the rows the words are about. The outlook sits beside it.
- **What the earlier plan designed and is kept:** locate, outlook, compare actions, simulate; suppress thin cells; label observational advice
  as observational; governance by the allowlist. Its stage and outcome shard model for structured logs is replaced by the model below.

## Design

### 1. Levels

- **Model.** The same two labels. Elements gain a `level` (1 for what exists) and a parent relationship `(:State {level: L-1})-[:PART_OF]->
  (:State {level: L})`, the same for Actions. Level 1 is never rewritten by this stage: `qlsc process abstract` adds and replaces
  levels 2 and up only, so a rebuild of the first level is followed by a rebuild of the levels, and not the other way round.
- **Transitions at a level** are lifted by assignment, as at level 1: the pairs of consecutive turns whose elements' ancestors at that level
  are the two ends. `SELECTS` and `LEADS_TO` join nodes of one level, and every read names a level, so a level-3 State never leads to a
  level-1 Action.
- **Each parent is named** by the LLM from its children's names and descriptions (Sonnet; a few hundred calls, about a dollar), under the
  same checks as a first-level name (an Action's name begins with a listed verb).
- **How many levels, and which one serves retrieval,** is chosen by score on the tuning conversations and judged on the holdout: completeness
  and V-measure by level against the planted labels, stage purity (a coarser State must not mix stages: it is 97% for raw text and 89% at
  level 1, and falls further if levels merge across stages), the share of turns in a shared State, and transition fidelity. The levels are an
  answer to the first-level numbers above, so they are judged against them.

### 2. Where a case ends

- **An outcome for each conversation, found from its text.** One cheap call per conversation (Haiku, about $3 for 2,032) reads the last turns
  and the agent's after-call note (the note the State annotation deliberately never saw, because it summarises the call) and describes the
  outcome in a sentence or two: what was done, whether the customer's problem was settled, retained, escalated or abandoned. The descriptions are
  embedded, grouped by the same neighbours-and-Leiden step and named, so **the vocabulary of outcomes is discovered, not given**, and is scored
  against the planted outcomes (14 in the world, with a favourability) afterwards.
- **"Ends well."** Each outcome type carries a favourability, from the same read of the text (a rating the model gives from a fixed scale,
  checked against the planted favourability, which only the scorer sees).
- **Absorbing probabilities on States.** A conversation's last State is where it was absorbed into its outcome. With the lifted chain (the
  transient elements, the transitions, the `ends` and their outcomes) two estimates are computed for every State and level, and scored against
  each other:
  - **chain:** solve the absorbing chain (sparse iteration; no dense matrix over 3,000 elements). It generalises across paths a State
    has never been seen on, and assumes the past does not matter.
  - **empirical:** of the conversations that passed through the State, how many ended in each outcome. It respects history, and is thin where a
    State is rare.
  A State then carries `end_well` (the probability its cases end well) and its likeliest outcomes with probabilities, with the support count
  beside them. Where support is under `process.min_support` it carries none, and says so.
- **Stored on the State, not as a new label** (decision 1): a few properties on the State node, with the outcome vocabulary in the build
  record and as a small list property at the graph level. The alternative, an `Outcome` node, is what the previous project had; this keeps
  the model at two labels and puts the odds where an agent reads them.

### 3. What to do next

- **Locate.** From a live conversation up to turn N: annotate the prefix as a State exactly as the build does (one cached call), embed it,
  and find the nearest States by a vector index on `State.embedding` at the chosen level. Several States, not one, with their similarity: a
  case between two is said to be.
- **Outlook.** For the nearest State: the next Actions with their probability and support, the odds of each outcome, and the share that
  ends well. The payload is small and metered (`qlsc/meter.py`) so an agent can see how much to trust it.
- **Compare actions.** For each Action open at the State, the end-well odds *after* it (the absorbing probability of the State it leads to,
  one step on), with the support behind each. This is observational: the reps who escalate may be handling harder cases. The payload says so,
  and the evaluation includes the confounding the world plants (rep archetype and customer type shape what is done; the hidden cause shapes
  how it ends).
- **With the context.** The outlook is returned beside the customer's context as of the call (the rows the words are about, the
  recent card activity, a fee), so one call gives an agent where the case stands, what usually follows, and what the warehouse holds.
- **Exposed** as `qlsc process abstract`, `outlook`, and agent tools beside `ask` and `recall`. A router route for "what usually happens
  next" waits for the measurement (decision 6).

## How it is judged

All on the holdout (conversations 600 and up), with parameters chosen below; against raw text and the oracle where they apply; Wilson
intervals; leave-one-conversation-out wherever a number is built from the conversations it is scored on.

1. **Levels:** V-measure, completeness, stage purity, coverage and fidelity at each level, against level 1 (the table above).
2. **Outcomes:** the recovered outcome types against the planted outcomes (V-measure, and a table of what each type holds); favourability
   against the planted favourability.
3. **End-well odds:** at each State, the predicted probability that the case ends well against what happened: Brier score and calibration, at
   several checkpoints in a conversation's life (after the opener, after verification, after the first question, ...). Baselines: the global
   rate; the rate for the conversation's domain; and the oracle (planted State key as the State). Chain against empirical.
4. **Recommendation validity,** which needs no simulation because the world records what works: for each recommended Action, mapped to its
   planted label, is it an action that **fixes the real cause** (the world's efficacy table: fixes, partial, no effect, makes worse) when it
   is a remedy, or that **elicits a clue that is true and unsaid** when it is a question. Against what the rep did, the best fixed
   action chosen with hindsight, and chance. **This is where the graph can beat the reps:** the first level's likeliest-next-Action test
   (7% against 10%) cannot, by construction; ranking by outcome can.
5. **Optional, only if (4) shows promise: replay in the world.** The sampler's walk takes a policy, so a recommended Action is taken at the
   decision point and the case plays out under the world's own causes; the outcomes are compared with the reps'. This is the proper
   counterfactual, and costs a refactor of `Sampler.walk` (decision 5).
6. **Confounding:** the same tests split by rep archetype and customer type: does the graph recommend what rushed reps do (the most
   common), or what works?
7. **Cost and time of an outlook** (tokens, seconds, bytes), against the service targets in `defaults.yaml`.
8. **Gates, not thresholds:** a rebuild of the levels from the same first level makes no calls and writes the same graph; the first level is
   untouched; every stage's output is present after it.

Thresholds for the quality numbers are set after the first measurement, as before, and results are reported as they come, including where
the graph does worse than a baseline.

## Phases

0. **Decisions below, and this plan agreed.**
1. **Levels.** Embeddings and neighbours from the stored vectors (with and without a transition-similarity term), Leiden per level, naming,
   lifted transitions, `qlsc process abstract`; scored by level on the tuning conversations, then the holdout. Cost: about $1 of naming.
   **Phase 1 as built and measured (2026-10-06).** `qlsc process abstract` (`src/qlsc/process/abstract.py`; two parent-naming prompts; the
   `process.levels` parameters; 4 tests; `eval/process_levels.py`, `results/process_levels.md` and `process_levels_grid.md`, with round 1 kept as
   `process_levels_grid_round1.md`). The grouping is the first level's own (GDS kNN over the stored vectors, then seeded Leiden at
   `gamma / (L - 1)`), with a transition-similarity term; a node nobody grouped is carried up unchanged; a parent's id is a hash of its
   children's; level 1 is untouched (its 8,230 transitions, and now a `level` property on every node and transition). The first level
   was rebuilt once, to add `level: 1`, with no calls.
   - **The grid and the rule.** Two rounds, 42 whole hierarchies (24, then 18) (similarity 0.70 to 0.90, resolution 1 to 4, transition weight 0 to 0.6, and a
     position-in-conversation term that was **tried and removed**: it lowered stage purity), scored on conversations 0 to 600. The rule was set
     before looking: at level 2, States' stage purity at least 0.85 and Actions' homogeneity at least 0.90, then the best Action V + State V.
   - **Actions pass; States do not.** For Actions, a level at similarity 0.80, resolution 4, transition weight 0.6 keeps homogeneity at 0.91 and
     raises completeness from 0.67 to 0.78 (V 0.79 to 0.84), taking 505 elements to 209 on the tuning slice. **For States, no coarser
     level passes:** every setting that coarsened them mixed stages (purity 70% to 80%), and the one that came closest, changing little
     (862 of 1,163 elements), reached 83% against the first level's 90% and the gate's 85%. So `process.levels.kinds` is `[action]`: States
     stay at their first level, and that is a **finding, not a setting**: text-alike States of different stages are the same problem, and
     only the stage tells them apart. (The gate is applied per kind, which is how I read it; it was written as one rule.)
   - **On the 1,432 conversations nobody tuned on:** Actions 815 elements to 300; completeness 0.65 to 0.76, homogeneity 0.95 to 0.90, V
     0.77 to **0.83** (0.84 on the tuning slice: little was overfitted); singleton Action turns 6% to 2%; transition fidelity 0.91 to 0.86,
     the price of coarser Action labels. States are as before (V 0.77, stage purity 89%, 25% of turns in a singleton).
   - **A rebuild** from the same first level makes no calls and writes the identical levels (the same hash across three runs). 131 Action
     parents ($0.15, 13 Sonnet calls); two were refused a name twice by the verb check and took their largest child's, and say so.
   - **What this means for the rest of the plan.** Retrieval cannot lean on coarse States for coverage: 25% of State turns still sit in a
     State no other turn shares. The way to cover them is not a coarser State but **a nearer one**: locate by similarity to several first-level
     States and pool their outcome odds, weighted by how near each is (phase 4), which keeps stages apart where merging does not. That is
     decision 9.

   **Revised the same day: the neighbours come from the vector index and are kept.** Phase 1 first used GDS kNN over scratch nodes, and kept
   nothing. You asked for the neighbour links to be persisted, and whether Cypher's vector search should replace GDS kNN. Measured on the 3,044
   first-level States, against exact brute-force neighbours:

   | | time | recall@10 | the same answer on a rerun? |
   |---|---|---|---|
   | Cypher vector index (`db.index.vector.queryNodes`; the `SEARCH` clause the same) | 1.4 s | **99.98%** | yes |
   | GDS kNN, one thread (the build's setting) | 1.7 s | 98.5% | yes, with a seed |
   | GDS kNN, four threads | 1.0 s | 98.4% | **no** (a different set each run) |

   So for **elements** (which are nodes) the index is as fast, more exact, repeatable and needs no scratch nodes; GDS's parallelism was never
   in use, because determinism forces one thread. For **turns** (not nodes: decision 1 of the last plan) GDS kNN stays. Built: a cosine vector
   index on `State.embedding` and one on `Action.embedding` (`process_state_embedding`, `process_action_embedding`, created by `qlsc process
   build`, every level's nodes in the one index), the levels' neighbours from it, Leiden projected from the real nodes, and **`K_SIM` kept at
   every level, the first included**: `(:State|Action)-[:K_SIM {score, rank, level, transitions}]->(:State|Action)`, 44,240 links (30,400 State,
   10,200 Action at level 1, 3,600 Action at level 2). A kind whose level did not change has no `K_SIM` at that level. `qlsc process abstract`
   writes them (and so must follow `build`, which deletes the nodes they hang on). The grouping is unchanged (the same 131 Action parents), the
   result is identical across three reruns including every `K_SIM` link, and the grid now runs the real stage instead of a separate path.
   The same index is how a live conversation enters the graph in phase 4: `CALL db.index.vector.queryNodes('process_state_embedding', 5, $vec)`.

2. **Outcomes.** *Built and measured (2026-10-06).* `qlsc process outcomes [--limit N]` (`src/qlsc/process/outcomes.py`; three prompts; the
   `process.outcomes` parameters; `source.notes`; 4 tests; `eval/process_outcomes.py`, `results/process_outcomes.md` and `_grid.md`).
   One Haiku call per conversation (2,032: **$1.68, nine minutes, none failed**) reads the last six turns and the agent's after-call note and
   says how the case ended in a sentence or two, with a 1 to 5 rating; the descriptions are embedded and grouped by the first level's own
   neighbours and Leiden, kinds under five conversations folded into the nearest, and Sonnet names each kind ($0.06). The vocabulary is
   **discovered, not given**: 28 kinds, in `work/process/outcome_types.json`, with `outcomes.ndjson` beside it. A grid of 20 settings gave a
   V-measure that is flat from 0.45 to 0.48 (the rule, set beforehand: the highest within 15 to 40 kinds, picked similarity 0.80, resolution 0.5).
   **On the 1,432 conversations nobody tuned on:**

   | | kinds | against the planted outcomes (h / c / V) | against what the text can show (h / c / V) |
   |---|---|---|---|
   | described (the build) | 28 | 0.67 / 0.35 / **0.46** | 0.87 / 0.30 / **0.44** |
   | raw after-call note, no description | 29 | 0.42 / 0.23 / **0.30** | 0.51 / 0.18 / **0.27** |
   | planted outcomes (ceiling) | 12 | 1.00 / 1.00 / 1.00 | 1.00 / 0.65 / 0.79 |

   - **The rating is the strong result: Spearman 0.75 against the planted favourability (0.79 on the tuning slice), and an AUC of 0.92 for
     telling the cases that ended well from the rest** (mean rating by planted favourability: high 4.3, medium 2.8, low 2.1). It was given
     without seeing any planted vocabulary.
   - **The kinds are less clean than the rating, and why is the finding.** The recovered kinds read as a bank's own outcomes, and several are
     exact (retained by an offer: 106 of 108; transferred: 121 of 121; hung up: 66 of 66; escalated: 95 of 98). But they mix *what was done*
     with *how it ended* (a kind is "Address updated, customer satisfied" or "Account balance provided"), so a planted outcome is spread over
     many kinds (completeness 0.35), and **the outcomes the world hides are not found by construction**: a fix that did not fix, and a skipped
     verification, read as "resolved" (the kinds "Payment reapplied" and "Fee waiver denied, repeat charge" hold 20 and 15 of the 62 false
     resolutions, rated a point lower than their neighbours: the only trace). The ceiling for what the text can show is 0.79, not 1.
   - **The LLM description buys 16 points of V over clustering the note itself** (0.46 against 0.30), as annotation bought over raw turns.
   - **For phase 3 this means:** `end_well` (from the rating) is the property to lean on, and the kinds give "in what" at a coarse grain;
     the hidden outcomes are a limit to report, not to fix. Two kinds share a topic and differ in rating, which is the information.

3. **Absorbing probabilities.** *Built and measured (2026-10-06).* `qlsc process absorb` (`src/qlsc/process/absorb.py`; the `process.absorb`
   parameters and `process.min_support`; 8 tests; `eval/process_absorb.py`, `results/process_absorb.md` and `_grid.md`). No LLM, under a second.
   Both estimates, per element at every level, scored by Brier, AUC and calibration against baselines, leave-one-conversation-out.
   - **What is stored.** On each State and Action, as properties (decision 1): `support` (the conversations through it), `end_well`, and
     `likely_outcomes` / `likely_odds` (the three likeliest kinds of outcome with their odds). An element under `process.min_support`
     carries `support` and no odds. A node takes its values from the chain at its own level (the first level's for States and for Actions no
     level groups; level 2's for the Actions it made). "Ended well" is a rating of at least 4. The vocabulary of kinds stays in
     `outcome_types.json`: I did not add a graph-level list property, since there is no graph-level node to hold it (that would be a third label), and
     every element names its kinds inline.
   - **Chosen on the tuning conversations, by rules set first** (`process_absorb_grid.md`): `good_rating` 4 (accuracy 0.882 against the planted
     favourability, 0.878 at 3, 0.705 at 5); `prior` 2 pseudo-conversations for the empirical estimate (the chain scores best with none and
     worsens with it); the estimator `empirical`; `min_support` 3 (3, 5 and 10 within 0.002 of each other: 0.2038, 0.2052, 0.2095; the rule takes the
     smallest, **where the plan recommended 5**).
   - **Scored at checkpoints (after the customer's 1st, 2nd, 3rd, 4th, 6th turn and at the last), on the 1,432 conversations nobody tuned on.**
     Brier against the planted favourability being high (lower is better):

     | | 1st | 2nd | 3rd | 4th | 6th | last | all |
     |---|---|---|---|---|---|---|---|
     | global rate | 0.237 | 0.237 | 0.234 | 0.229 | 0.240 | 0.237 | 0.236 |
     | by domain | 0.215 | 0.215 | 0.214 | 0.223 | 0.258 | 0.215 | 0.218 |
     | by planted State (oracle) | 0.214 | 0.200 | 0.202 | 0.202 | 0.261 | 0.135 | 0.194 |
     | **empirical** | 0.224 | 0.211 | **0.193** | **0.185** | 0.228 | 0.179 | **0.201** |
     | **chain** | 0.225 | 0.213 | **0.193** | **0.182** | 0.219 | 0.178 | **0.200** |

   - **What it says.** The odds on States are informative and modest. They cut the Brier score by 16% against the global rate (−0.039 ± 0.005),
     and discriminate (AUC, in 20 folds: 0.64 at the opening State, 0.69 at the third, 0.71 to 0.74 at the fourth, 0.78 at the last; 0.69 overall).
     Position alone (the turn count) adds nothing (0.235), and the conversation's domain alone is −0.023. By the third State the graph's States beat
     the planted oracle State's (the answer key's domain, stage and verified, which says nothing of what has been said): they hold what was said.
     At the opening State they only match the domain, as they should: nothing has happened yet. At the last State the oracle is far ahead (0.135):
     its key says the customer hung up, which the outcome text reads only as one of many endings.
   - **The two estimates are level.** The paired difference between them on the holdout is −0.0004 ± 0.0023, so decision 4's fallback applies:
     `empirical` is stored (no assumption; says "thin" honestly). The chain is a little better where States are thin and conversations are deep (4th
     and 6th turn: 0.182 and 0.219 against 0.185 and 0.228), and a little worse early. A hybrid (the chain where an element is under a support
     of, say, 10) is the obvious next try; it is a tuning on top of two estimates, so I did not build it unasked.
   - **Calibration is good where there is support and poor where there is not.** Expected calibration error 0.025. The two extreme bins
     under-state the truth: States predicted 0.2 to 0.4 ended well 59% of the time. A State with three conversations all unhappy is not
     doomed, and a prior of 2 does not shrink it enough to say so; the Brier grid preferred 2.
   - **Coverage is the limit.** With `min_support` 3, **66% of the checkpoints** sit in a State with odds, but only **298 of 3,044 States
     (10%)** do: the few big States hold most of the turns, and the long tail is thin (decision 9: States stay at their first level). Locating a
     case by nearness and pooling the odds of its nearest States, weighted by how near each is, is what phase 4 does about the other third.
   - **Hidden outcomes are a ceiling.** Mean prediction by planted favourability at the last State: high 0.75, medium 0.59, low 0.41, very-low
     0.55: the very-low cases (false resolution, wrong fix, skipped verification) look like the rest because they read as resolved. A prediction
     from text cannot get past them, and the recommendation test of phase 4 will have to say so.
4. **Outlook and compare actions.** *Built and measured (2026-10-06).* `qlsc process outlook CONVERSATION [--turn N] [--with-context]`
   (`src/qlsc/process/outlook.py`; the `process.outlook` parameters; 8 tests; `eval/process_outlook.py`, `results/process_outlook.md` and `_grid.md`).
   - **How it works.** The customer's latest turn is annotated as a State exactly as the build does (one Haiku call, cached when the build saw it),
     embedded, and looked up in the State vector index. The nearest 5 States' *counts* are pooled (weighted by nearness) into the case's odds of ending
     well and in what, and for each Action reps took next: how often, and how the cases that took it ended (pulled toward that Action's own rate, so a pair
     seen twice is not its two cases). The payload names the Action with the best ending after and the one reps took most often, and says it is
     observational. `absorb` now also stores the raw counts pooling needs (`support_good`, `outcome_kinds` and `outcome_counts` on elements; `num_good` on
     transitions), so the graph alone answers it. `--with-context` adds the customer's context as of the call (needs a fresh `qlsc` gcloud login; not
     re-run this session, the context read itself was measured in text-graph phase 5).
   - **Chosen on the tuning conversations by rules set first** (`process_outlook_grid.md`): 5 States, weights flat (temperature 1: 0.3 and 1 are level,
     so pooling is what helps and nearness weighting adds little), Actions at **level 2** (22% of recommendations useful against 18 to 19% at level 1: the
     level built in phase 1 earns its keep here), and a prior of 50 pseudo-transitions (20 to 200 level). That prior is large: **the ranking is mostly the
     Action's own overall ending, the State choosing which Actions are open**, and that is why the recommendation below fails where the case is still
     being diagnosed.
   - **Nearness works (holdout, 1,432 conversations).** The odds of ending well at checkpoints, Brier against the planted favourability: the State
     the build assigned 0.201, the nearest State by the index alone 0.202, **the pool of the nearest 5: 0.185** (paired, against the assigned State
     −0.0198 ± 0.0057; against the global rate 0.236, −0.058 ± 0.008). **Coverage goes from 66% to 100%**: the thin States no longer carry nothing. At the
     last State 0.142 against 0.179.
   - **Recommendation validity (5,264 decision points; 92% have a supported recommendation).** Useful means a remedy that fixes the real cause (the
     world's efficacy table) or a question for a clue that is true and not yet said. Of the points where the graph made a recommendation:

     | | all | a true clue is waiting (1,767) | no clue waiting (3,074) |
     |---|---|---|---|
     | **the graph, best ending after** | 24% | **16%** | **29%** |
     | the graph, what reps most often did | 20% | 28% | 16% |
     | the rep, what was done | 26% | 27% | 25% |
     | chance among the procedure's actions, over all points | 11% | 16% | 9% |
     | the best single action, with hindsight | 11% | 31% (ask what happened) | 10% |

     **Ranking by outcome beats ranking by frequency where it should, and loses where it should not:** where no clue is waiting and the job is to fix, it
     recommends a remedy that fixes the cause 29% of the time against the reps' 25% and a frequency ranking's 16%; where a true clue is waiting it asks
     for it **1%** of the time (the reps 7%) and is no better than chance, because an Action that closes a case ends well far more often than one that
     asks a question, whatever the case. **It recommends a remedy that does nothing for the cause 20% of the time (the reps 3%) and one that makes it
     worse 3% (1%):** a State's text cannot say which cause a case has, and the Actions that end best are the confident ones. So the graph beats the
     typical rep at a State (what reps most often did) but **not the rep with the real case in front of them** (24% against 26%), and it is a hazard in the
     clue-waiting half. The outcome by agreement says why this is observational: where the rep took the graph's recommendation 75% of the cases ended well,
     else 61%, and that gap is the cases, not the advice.
   - **Confounding.** The graph is better than what reps most often did for every rep archetype (22 to 27% against 18 to 22%) and every customer
     archetype, and agrees with that most-common Action only 37 to 42% of the time (37% for the methodical reps' points, 40% for the rushed, 42% for the
     warm but imprecise): it does not just mirror what rushed reps do. It is best for the clear, observant customers (28%) and worst for the ones sure of a wrong cause (22%).
   - **Cost.** A live outlook takes a median 3.4 s with the annotation answered from the cache, and a turn the build had not seen adds one Haiku call
     (about 1.1 s and $0.0008): inside the service targets of 30 s and 20,000 tokens by a wide margin.
   - **Three attempts to fix the ranking, none kept** (`results/process_outlook_ranking.md`, tuning conversations; the code was taken out again).
     (1) Valuing an Action by the best follow-up instead of the average one: 19% useful against 22%, because a text-rated ending is as high after a
     confident wrong fix as after a right one, so questions gain no value (0.72 against 0.84 for offers). (2) Recommending only an Action taken often
     enough from here: the graph converges on what reps most often did and never passes the rep. (3) Recommending the best question where reps mostly ask
     and the best remedy where they mostly act: better where a clue waits (22%, from 16%), worse where none does (21%, from 30%), 20% overall.
     **The cause is a confounder the data never recorded:** a rep who offers a fee refund usually knows the problem is a fee, so the cases it was offered
     in ended well because of the cases; pooled at a State whose text does not tell the causes apart, that success is credited to all of them. No
     reweighting of what was observed undoes it; the cause is what asking finds out. So the outlook is a good picture of where a case stands and how cases
     like it ended, and **its "best ending after" should not be presented as advice**.
   - **Decision 5 (replay) is not built, and I would not build it yet.** The plan said to replay only if validity showed promise. It shows some where
     the job is to fix and a failure where it is to ask. A replay would confirm the failure and cost the sampler's refactor. The fix to try first is
     in the ranking, not the evaluation (below).
5. **Tools, the write-up.** *Built and measured (2026-10-06).* `outlook` as a tool beside `recall` and `ask` (`Conversation.outlook` in
   `qlsc/converse.py`: a live transcript as [{role, text}], or a stored conversation's id, in; the nearest States, the odds with their support, what
   reps did next and how those cases ended, and the caution, out, recorded as a Step; refused to a reader `process.readers` does not admit;
   `source.live`; `conversations/support-1.yaml`; 4 tests). The tool does **not** return its recommendation (computed for the evaluation, no better
   than the typical rep). Not run end to end this session: it needs the `qlsc` gcloud login, which had lapsed; its steps are tested with a stand-in.

   **The agent-side test (`eval/process_agent.py`, `results/process_agent.md`).** The plan's arm "does an agent that has the outlook resolve cases
   better in the world" needs a replay of the world, which was not built. What could be measured: an LLM agent (Sonnet 5.5) is shown a call part-way
   through and the menu of the procedure's actions, and picks the next one; 200 holdout decision points, half with a true clue waiting; each choice is
   scored by the efficacy table (a remedy that fixes the real cause, or a question for a clue that is true and not yet said, is useful). Eight arms:
   what the agent is shown beside the call.

   | | useful (all) | clue waiting | no clue waiting | against alone (better / worse, sign test) |
   |---|---|---|---|---|
   | the call alone | 12% | 14% | 11% | |
   | + the outlook | 11% | 13% | 9% | 4 / 7, p = 0.55 |
   | + the phone system's record of the call | **31%** | 35% | 27% | 44 / 7, p < 0.001 |
   | + the account's fees and card purchases | 13% | 13% | 13% | 3 / 2 |
   | + both (the warehouse context) | **33%** | 38% | 28% | 48 / 7, p < 0.001 |
   | + the process's tables as a designed ontology | 18% | 22% | 13% | 12 / 2, p = 0.013 |
   | + context and ontology | 30% | 32% | 27% | 43 / 9 |
   | + the outlook, context and ontology | 28% | 34% | 22% | 43 / 12 |
   | *the rep, what was done* | 28% | 29% | 27% | |
   | *the typical rep* | 22% | 26% | 18% | |
   | *chance; the best single action with hindsight* | 13%; 15% | 16%; 30% | 9%; 14% | |

   - **The outlook did not help the agent**, as phase 4 would predict; with everything else beside it, it lowered the choices a little (28% against 30%).
   - **Customer and call context did.** All of the gain is the phone system's record of the call: the agent alone verifies the caller's identity in
     67% of its choices because the transcript does not show the caller was already authenticated, and with the record it does so in 26% and asks or
     acts instead. That is a plain piece of warehouse context, and it lifts the agent to the rep's level (31% against 28%) and above what the typical
     rep does (22%). **Caveat:** a repeated verification is not harmful in this world, only unproductive, so this is efficiency in reaching the
     substantive step, not a better outcome by itself. The fees and purchases added nothing: only a few causes depend on them, and a menu choice is
     not sensitive to them.
   - **The designed ontology helped a little** (18%, 12 better and 2 worse), and added nothing once the context was there. The agent's wrong
     questions ("asks for nothing new": 24 to 40% of its choices) are the remaining loss: it asks, and does not know which clue is true.

   **What phase 5 found, in sum: what we have shown and what we have not.**
   - *Shown:* a process graph can be built from text and scored against an answer key (structure V 0.77 to 0.83; outcome rating Spearman 0.75, AUC
     0.92; odds of ending well Brier 0.185 against 0.236 and AUC 0.65 to 0.78); a live case can be located by nearness with every case covered;
     the warehouse's context as of the call can be fetched and linked; and an agent given that context chooses better.
   - *Not shown:* that any of it lifts a process over the historical baseline. The next-Action recommendation is no better than the typical rep and is
     confounded; the agent test scores one decision, not a case played out; and the world's headroom is in a place the graph does not reach. **Measured
     on the whole corpus: the true cause alone predicts a good ending barely better than nothing (Brier 0.195 against 0.236), and the planted
     action's efficacy against the cause predicts it almost perfectly (0.049).** Two thirds of the cases already get an Action that fixes the cause;
     the one third that do not is the headroom, and reaching it needs the cause and what fixes what.
   - *What would show an uplift:* (1) **the cause**, inferred from what a call shows and from the context (the world's causes name warehouse
     facts they need: an unwaived fee, a card purchase); (2) **what fixes what**, a designed efficacy ontology aligned afterwards and used as a
     prior for recommendations, not an input to the build (it cuts across "usage is the ground truth", so it is a decision for you; the agent test
     says it is worth a little, and the efficacy numbers say it is the missing half); (3) **an outcome the action does not colour:** a repeat call
     in the warehouse within days (the pool already carries the next call), not a rating read from the same conversation (a confident wrong fix reads
     as resolved, and 80% of those recur); (4) **a counterfactual:** the replay of decision 5, or an experiment. Until then the outlook is a picture,
     not advice.

## What does not change

The first-level graph and its build, the semantic layer, memory, the virtual graph and its model, the router's routes, and the rule that
`src/qlsc/` and `prompts/` know nothing of any estate: the outcome and parent prompts say "{business}", and field names live in the config.
The structured-event miner of the earlier plan stays parked: it reads rows, which the design's principle admits only as aggregates, and it
is not needed to answer this plan's question.

## Governance

Carried from the earlier plan, as they apply to text: the process database is read through the allowlist of the sources it was built from
(for the corpus: synthetic, no identifiers; for a real one, the events file is a source with its own access rules, and a State built from
restricted text is not shown to a reader who may not read it); thin cells are suppressed (`process.min_support`); agents and customers appear
as counts and kinds, never names; AML and SAR text stays out of estate-wide builds unless an estate enables it.

## Decisions

1. **Where outcomes live.** *Recommend properties on States* (`end_well`, the likeliest outcomes with probabilities, the support), a
   vocabulary in the build record, and no `Outcome` or `Resolution` label: the model stays at two labels, and the odds sit where an agent
   reads them. The alternative is an `Outcome` node with `ENDS_IN` edges, as the previous project had Resolutions: simpler to query a
   path to an outcome, one more label, and a second place the vocabulary can drift. *You said to come back to this: this is the place.*
2. **Where the outcome is read from.** *Recommend the last turns and the after-call note.* The note names what was done and how it ended,
   and State annotation never saw it, so no State leaks its own outcome. Text-only outcomes (no note) would be noisier and are the fallback if
   an estate has no note.
3. **How levels are stored.** *Recommend a `level` property and `PART_OF`,* as the semantic layer does (`Semantic.level`, `IN_SEMANTIC`): no
   new label, one place to read a level. The alternative is a label per level, which makes a query that crosses levels awkward.
4. **Which absorbing estimate serves.** *Recommend deciding by phase 3's score* and storing the better one per level, with the other
   in the evaluation only; if they are level, the empirical one (it needs no assumption, and says "thin" honestly). *Settled by phase 3: they
   are level (paired difference −0.0004 ± 0.0023 on the holdout), so `empirical`.*
5. **Replay in the world.** *Recommend yes, but only after recommendation validity (phase 4) shows something to replay.* It is a refactor of
   the sampler's walk so a policy can choose the next Action; it turns a lookup into a counterfactual. If validity is no better than the
   reps', replay would only confirm it.
6. **Tools, then a route.** *Recommend tools only* (the earlier plan's decision 6), a route once the outlook's accuracy and cost are
   measured.
7. **A vector index on `State.embedding`,** one per level or one with a level filter. *Recommend one index and a `level` filter,* so the
   composite and the Cypher stay simple. *Settled in phase 4: one index per label (every level's nodes share it), and States have the one level, so
   a filter was never needed.*
8. **`process.min_support`.** *Recommend 5 conversations to start,* tuned on the tuning slice, never on the holdout. *Tuned: 3 (the smallest
   of 3, 5 and 10 whose Brier is within 0.002 of the best). The curve is flat there; 5 costs 0.0014 of Brier and 3 points of coverage.*

9. **States stay at their first level; coverage comes from nearness, not coarseness.** *Accepted 2026-10-06.*  The alternative is to relax
   the stage-purity gate (to 0.80, say) and build a coarse State level: it would cover every turn and answer with States that mix verification
   and diagnosis. The trade is in `process_levels_grid.md`: sim 0.85 gives 236 States at 80% purity (against 1,163 at 90%), sim 0.80 gives 79
   at 73%. *This is yours to relax; I have not.*

## Risks

- **Observational data is not causal.** The reps who ask the discriminating question may be the careful ones, whose cases end better for
  other reasons. The plan tests it with the archetype splits and, if built, the replay; the payload labels it either way.
- **Merging across stages.** A coarse State that mixes verification and diagnosis answers neither. Stage purity is gated by level, and the
  transition-similarity term is there to keep stages apart.
- **Sparse outcomes.** About 5% of conversations are retentions and 7% carry a serious breach; an outcome type with few cases has noisy
  odds. Support is carried, and a type below the threshold is folded into its nearest.
- **Leakage through the note.** The outcome is read from text that states it; the State used to predict it must not have seen the note, and
  the leave-one-out must take the conversation out of the counts. Both are checked as gates.
- **The world flatters the method.** The planted structure is easier to find than a real process; results here bound what the method
  can do on this corpus, not on yours. The corpus plan says so, and so does every table.

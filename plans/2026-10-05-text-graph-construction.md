# Building the State-Action graph from text: extraction and construction

Status: agreed (2026-10-05, every recommendation taken); all five phases built and measured. The second of the process work's plans, after [the corpus](2026-10-05-process-corpus.md) (built) and
before [process abstraction](2026-10-03-business-process-graph.md) (hierarchies, outcome odds, retrieval, agents). The decisions at the end were
taken on 2026-10-05.

## What this plan is, and is not

**It is:** reading the events file, annotating each turn as a State or an Action with an LLM, turning those observations into a
small set of canonical States and Actions with counted, probabilistic transitions, writing them to a `process` shard, and
scoring what came out against the corpus's answer key. Fast, deterministic, cached, resumable, measured.

**It is not:** the hierarchy (GDS clustering of States and Actions into levels), where a case ends (Resolution as a node or as
an absorbing probability on a State), path odds, or the agents that use them. Those are process abstraction. This plan ends at the
first level, which is where the previous project ended its build; what it calls a process element is a canonical State or Action
here.

## What the previous project teaches (read 2026-10-05; `~/Desktop/demos/call-transcripts-automation`)

Taken: the shape (per turn, a customer turn gives a State and a rep turn an Action, each described from the conversation so far
and never from what comes later); the observation-to-element split; naming elements with a per-kind prompt; lifting observation
sequences to `num` and `probability` by assignment (an earlier `+1` tripled counts); the graph as the record of progress, so a
rerun asks "what is not done" and a no-op rerun costs seconds; the rate limiter, request timeouts and retry layers; scoring with
V-measure, edge-probability fidelity and a leave-one-out diagnostic test, with Wilson intervals.

What it found wrong, which this plan is built around:

| Finding there | What this plan does |
|---|---|
| The headline claim was false: the graph's top next action asked the discriminating question 3.6% of the time, against 16.9% for the reps; the in-sample 14.4% was leakage | Score **leave-one-conversation-out** from the first run, with the baselines beside it |
| A State described the problem, not the stage: 27% of multi-turn State elements mixed verification and diagnosis turns | The State prompt carries the latest turn and **what has been established or ruled out so far**, which includes the stage; scored by stage purity |
| 98% of State elements were singletons at a 0.98 cosine cut, so the graph recommended what that call's own rep did | Report the singleton share as a first-class number; choose the cut by the score, not by carrying 0.98 over |
| A 0.98 observation cut and a 0.94 name merge, tuned to a 512-dimension model, fragmented actions ("Ask for" and "Request" at 0.973) | **Canonicalise the action's verb upstream**, in the prompt; thresholds are parameters measured on this corpus and this embedder (`text-embedding-3-large`) |
| The projection compared every pair of observations (about 144 million at 12,000) | **Nearest neighbours, not all pairs** (a vector index or GDS kNN), so cost grows with N, not N squared |
| Ids were random; element ids were GDS community numbers that change per build | Observation id is the event's own id (deterministic already); an element's id is a hash of its kind and canonical name |
| Embeddings drift (0.996 for identical text), flipping clusters near the cut | Embeddings are cached by request (`llm.Embedder`), so a rebuild reads the same vectors |
| A hung request stopped throughput at zero while the pass looked alive; a bad Cypher write after the LLM spend persisted nothing | Timeouts and retries as there; **each stage asserts that its output landed**, and progress watches the artifact, not the calls |
| A content filter killed pass 2 (one 400) | A failed turn is recorded as attempted and skipped, never retried forever and never allowed to end the pass |
| Schemas all optional, instructions in `title` | Strict schemas (`llm.strict`), every field required, instructions in descriptions |

## The design

**Input.** The events file by path or URI: `process.events` in the estate config, with a field map (`conversation_id`, `ts`, `role`,
`channel`, `text`) and a map from role to kind (customer gives States, agent gives Actions); channels excluded from the
sequence are named (`case_note`, `system_log`). The tool reads only that and the catalog; it never reads the answer key, and
`src/qlsc/` names nothing about Fennmoor (`tests/test_boundary.py` holds). A source path may be a local file, a `gs://` URI, or an
https URL: reading a bucket belongs in a connector beside the warehouse's, with `google-cloud-storage` as an optional extra and the
estate's gcloud configuration for credentials (the example's `corpus_store.py` does the same for the generators, reading a public
bucket by https and a private one by `gcloud storage cat`).

**Stages**, each a pure function of its inputs and cached or recorded so a rerun does only what is missing:

1. **Read and order.** Group events by conversation, order by `seq`; a conversation's turns are the unit of everything after.
2. **Annotate.** For each customer turn a State description, for each agent turn an Action phrase, from the turns up to and
   including it. The State is `latest_turn` plus `established` (what is known or ruled out, the stage, which policies are met),
   as the previous project's repaired prompt does; the Action is an imperative phrase from a canonical verb set, with no motive
   and no actor. Both are strict structured outputs; prompts are files in `prompts/`.
3. **Embed** each description once (cached by request).
4. **Group.** A sparse similarity graph from nearest neighbours of the same kind, a seeded single-threaded Leiden over a
   sorted projection (`Graph.project_pairs`), each community one canonical State or Action. Parameters in `defaults.yaml`
   with why they have their values.
5. **Name** each element (one call per element, shared across the conversations that reach it; a per-kind prompt with the
   members' descriptions) and fold elements whose names are near-duplicates, greedily, largest first, by *stored* name vectors so
   the fold is idempotent.
6. **Lift.** Observation sequences become `SELECTS` (State to the Action chosen next) and `LEADS_TO` (Action to the State that
   follows) with `num` and `probability`, by assignment, after the fold.
7. **Write** the `process` database on the semantic layer's instance (as memory's is), joined to the composite as an alias,
   rebuilt only by its own command.

**The graph model stays small: two labels, `State` and `Action`.** A State has `name`, `description`, `count` and `embedding`; an
Action the same; the two relationships carry `num` and `probability`. Observations are **not** nodes: the per-turn mapping (event
id to element) is the stage's record, kept as a file beside the build, and each element carries a capped sample of event ids as
`examples` so a case can be shown real wording from where it stands. (The previous project's comment and observation layers were
plumbing; a State vector index finds "where is this case" without them, since the elements are hundreds, not millions.)
Outcomes are deliberately absent: the conversation-level outcome is the process abstraction plan's question, and the corpus
records it so either design can be scored.

**Entities** (merchants, fees, amounts the text names) are linked by **lookup, not extraction**: the corpus names a merchant as
the warehouse does and states real fee amounts, so a deterministic match against `dim_merchant` and the fee rows replaces the
previous project's one LLM call per document (about 34,000 there), and is scored against the sidecar's `mentions`. Last phase.

## Scoring (`eval/process_graph.py`, against `truth.ndjson.gz` and the plans)

The answer key records, per event, the plan step, its stage, the planted action and the rep's belief; the plans add which clues had
surfaced by each step. From those, a scorer computes:

- **Abstraction:** homogeneity, completeness and V-measure of Action elements against the planted action; of State elements
  against the planted *State key*, which is (stage, clues established so far, authenticated) and **not** the rep's belief: the text
  never states the belief, so it can only be inferred through what the rep then does, and scoring against it alone would
  measure something the builder could not see. (Belief is still scored, as the harder second target.) Singleton share and
  stage purity are reported beside it.
- **Fidelity:** Pearson, Spearman and MAE between the planted and the discovered edge probabilities, and a recount of the stored `num`.
- **Diagnostic value, leave-one-conversation-out:** at a State where the clue was perceived, unvolunteered and elicitable,
  how often the graph's top next action is the question that elicits it, against the reps' actual rate, a fixed question, the most
  frequent action and chance; counted over the points where the test is meaningful, with Wilson 95% intervals.
- **Misdiagnosis and breaches:** whether elements separate a rep who misread the cause (a wrong-fix action sequence), and
  whether a conversation that skipped a gate lands in different States from one that did not.
- **Baselines:** (a) **no LLM annotation**: cluster the raw turn text with the same embedder and grouping, to see what the
  annotation buys; (b) the planted structure itself, as the ceiling.
- **Structural gates** (pass or fail, no thresholds invented): the same inputs give the same graph; a second run does no LLM calls and
  rewrites nothing; a killed run resumes to the same graph; every stage's output is present after it.

Thresholds for the quality numbers are set after the first measurement, as the corpus's gates were, and recorded with why.

## Phases

0. **Settle the decisions below; add `process:` to the config and a text-source reader** (path, `gs://`, https), with tests.
   *Built (2026-10-05).* `process:` in `defaults.yaml` (`events`, `fields`, `kinds`, `skip_channels`, each with its reason) and the
   estate's `process.events`; `src/qlsc/process/source.py` reads the events as conversations of ordered turns (a missing field, a
   repeated event id or a bad role map is an error); `qlsc process read` summarises (the demo corpus: 2,032 conversations and 19,360
   turns, 9,746 States and 9,614 Actions; the 2,032 case notes and 182 hang-up lines are not turns). **The bucket reader is
   `src/qlsc/warehouse/gcs.py`, with no new dependency** (decision 5 was a connector with an optional `gcs` extra; a media download
   with the named gcloud configuration's token needs no library, and the boundary test now allows the two connectors under
   `warehouse/`). It reads as the configuration's service account and fails if that account may not read: no other identity is
   tried. Read from the bucket and from the local file, the corpus is identical. 9 tests.
1. **Annotate, measured at 25 conversations.** *Built and measured (2026-10-05).* `qlsc process annotate --unit turn|conversation
   [--limit N] [--model]` (`src/qlsc/process/annotate.py`; five prompts in `prompts/`; the verb list and the State line length are
   parameters; 7 tests; the comparison is `eval/process_annotate.py`, results in `results/process_annotate.md`). Haiku 4.5 on the
   same 25 conversations (225 turns), read as well as measured:

   | | one call per turn | one call per conversation |
   |---|---|---|
   | calls / cost for the 25 | 222 / $0.18 | 25 / $0.07 |
   | projected, 2,032 conversations | **$15** (about an hour at concurrency 6) | **$6** (about 25 minutes) |
   | turns still failing after a retry | 0 | 4 (1.8%: the wrong field filled, a bad verb) |
   | median words in a State | 36 | 22 |
   | Action separation by the planted action (AUC) | 0.887 | 0.911 |
   | State separation by the planted domain (AUC) | **0.840** | 0.747 |
   | State separation by the planted stage (AUC) | 0.579 | 0.619 |
   | States using a word found only in later turns | 28% | 21% |

   The two units agree only moderately (cosine of the two descriptions of one turn: Actions median 0.84, States 0.85). **No sign that
   the one-call unit leaks the future** (the per-turn unit, which cannot, scores higher on the proxy: it is a crude test, and the
   prompt's own words account for some hits), **but its States separate the problem worse** (0.75 against 0.84), and States are what
   the graph is built on. Actions are slightly better in one call. **Decision 2 is therefore settled for the per-turn unit** (a
   difference of $9 for the corpus does not buy a worse State), with the one-call unit kept as the cheap option if a later corpus is
   larger and the State prompt is improved. Read by eye, both give consistent Actions ("Verify the customer's identity", "Waive the
   insufficient-funds fee", "Ask whether the customer recognises the flagged transactions"), and a State line that names the problem,
   whether the caller is verified and what was checked. Two things for the next phases: the per-turn State line is long and carries the
   turn's own wording (`latest_turn`), which will make elements more specific than wanted, so **what is embedded (the established
   line alone, or both) is a parameter chosen by the phase 3 score**; and the stage is weakly separated by either unit, which is a
   reason to score States on the State key and not on the stage alone.
2. **Group, name, fold, lift, write** on 100 conversations; the shard and its composite alias. **The `process` database is created
   here, and you are told when.** *Built and run on 100 conversations (2026-10-05).* `qlsc process build`
   (`src/qlsc/process/build.py`; two naming prompts; ten parameters under `process:` in `defaults.yaml`, each marked a first pass where
   phase 3 will tune it; 7 tests of the pure parts). The `process` database was **created on the semantic layer's instance on
   2026-10-05, when the first grouping experiment ran**, and holds the result of the build. What it did:
   - **983 turns became 65 States and 124 Actions with 418 transitions** (213 `SELECTS`, 205 `LEADS_TO`), for **$0.58 of Haiku
     annotation and $0.19 of Sonnet naming**; the 100-conversation annotation took 2 minutes. 28 of the 65 States and 66 of the 124
     Actions are singletons (6% and 14% of their turns). Folding names merged one element of each kind (at a cosine of 0.92 it barely acts;
     "Greet the customer" and "Greet the customer and ask how to help" stay apart).
   - **The grouping was chosen by looking, not carried over.** A grid over the cosine cut and the Leiden resolution against the
     planted labels (on the 100): at 0.70 actions merge (57 groups, 79% pure), at 0.90 they shatter (197 groups, 141 singletons),
     at **0.80 they are 95% pure in 125 groups**. The cut and the resolution stay first-pass parameters; phase 3's score tunes them.
     kNN needed one fact learned by measuring: GDS reports `(1 + cosine) / 2`, so the cut is converted both ways.
   - **Read by eye**, the elements are good: Actions "Verify the customer's identity" (59 turns), "Ask whether anyone else uses
     the card", "Process the account closure"; States "Account closure requested, not yet verified", "Unrecognized transactions,
     one-time code provided", "Disputed fee handled, customer closing". The likeliest Action after the biggest State is processing the closure
     (12%), then the questions that probe it. **The one concern for phase 3:** the biggest State, "Account closure, reasons probed,
     customer resisting" (48 turns), is a union of several stages (fees ruled out, an offer declined, relocation), which is the
     previous project's finding again (a State that mixes stages); stage purity is the score to watch, and `state_embeds` and the
     cut are the levers.
   - **A rerun makes no calls and gives the identical graph** (the same hash of every node, count, example and edge across three
     builds), and the build found its own bug on the second run: scratch observation nodes shared the elements' labels, so a
     second build grouped the first build's elements too. Scratch nodes now have labels of their own, and the stage asserts none
     are left behind.
   - **What is stored:** each element's name, description, `count`, `ends`, mean `embedding` and five `examples` (event ids);
     the event-to-element mapping is `work/process/observations.ndjson`, not graph. No outcomes, no hierarchy, and **no composite
     alias yet** (phase 5).
3. **Score** (the scorer and the baselines) on 100, then tune the cut and the neighbour count by the score, not by the previous
   project's numbers. *Built and run on the 100 (2026-10-05).* `eval/process_graph.py` scores three arms the same way, so only the
   grouping differs: **graph** (the build), **raw text** (the same embedder and grouping over the unannotated turns: what the LLM
   buys) and **oracle** (the planted labels as elements: the most a graph over these conversations could show); `--grid` scores
   the grouping parameters without naming (`results/process_graph.md`, `results/process_graph_grid.md`; 4 tests of the statistics).
   Parameters were **tuned on the same 100 they are scored on**, so these numbers are optimistic; phase 4 scores the other 1,900
   conversations with the parameters fixed. After tuning (similarity 0.85, resolution 1.0, both State lines; 210 States, 152
   Actions, 625 transitions; $0.37 of Sonnet naming):

   | | graph | raw text | oracle |
   |---|---|---|---|
   | Action V-measure (homogeneity / completeness) | **0.86** (0.97 / 0.76) | 0.78 (1.00 / 0.64) | 1.00 |
   | State V against the planted State key | **0.83** | 0.79 | 1.00 |
   | State V against the coarse key (domain, stage, verified) | **0.73** | 0.67 | 0.84 |
   | stage purity of States | 84% | **98%** | 100% |
   | transition fidelity, Pearson / Spearman / MAE | 0.88 / 0.90 / 0.105 | **0.91** / 0.89 / **0.101** | 0.99 / 0.99 / 0.012 |
   | turns in singleton elements (States / Actions) | 29% / 20% | 51% / 46% | 14% / 2% |
   | turns with a recommendation, leave-one-out | 69% | 43% | 87% |

   **What this says, plainly.**
   - **The LLM annotation buys something modest, not everything.** It gives better Actions (V 0.86 against 0.78: it joins what raw
     text keeps apart, "Ask whether anyone else uses the card" in many wordings) and half the singletons. It does **not** give purer
     stages (raw text is purer, 98% against 84%: a customer's reply "Sure, it's [REDACTED]" is the verification stage in any
     words) and its transition fidelity is no better. The previous project's problem (a State that mixes stages) is reduced by the
     two-line State prompt and the finer cut, but not gone.
   - **Granularity is the trade.** V-measure against a fine key rewards fragmentation, and fragmentation costs coverage and makes
     singletons, which is the leakage the leave-one-out test punishes. At 0.80, States covered 94% of turns and mixed stages (71%
     pure); at 0.85, 69% and 84% pure. The grid is in the results; the choice is a judgement, recorded in `defaults.yaml`. With 20
     times the conversations the shared States should grow, which phase 4 tests.
   - **The diagnostic test is not one a likeliest-next-Action graph can pass, and it should not be read as the graph failing at
     its job.** On 183 turns where a discriminating clue was true, perceived and unsaid: the graph's top Action asked the clue's
     question 5% of the time (2-10%), what the reps did there 9%, the best single question chosen with hindsight 15%, chance 6%,
     and **the oracle graph, with the planted labels as elements, 9%**. A graph of what people usually do recommends what people usually
     do, so its ceiling is the reps' own rate: exactly the previous project's finding ("the graph recommends the most frequent action,
     not the rarely asked one"). What can beat the reps is ranking next Actions by where they lead (outcome odds), which is the
     abstraction plan's absorbing probabilities; this number is the baseline that plan has to improve. (The points cluster within
     conversations, so the intervals are narrower than the data deserve.)
   - **Breach detection from the path cannot be judged at 100:** one planted authentication breach among 17 unauthenticated callers,
     found by every arm (the oracle too), with one false alarm each.
   - The stored `num` of every transition equals a recount from the turns.
4. **The full corpus (2,032 conversations) and speed.** Calls per conversation, wall time per stage, dollars per thousand
   conversations, a no-op rerun, a resume after a kill. The scale set (21,161 conversations, placeholder text) times the
   non-LLM stages (embedding, neighbours, grouping, lifting) at ten times the size; its text is repetitive by construction, so it
   says nothing about quality. *Built and measured (2026-10-05).* `qlsc process annotate` and `build` over all 2,032 conversations
   (19,360 turns; the `process` database now holds 3,039 States, 1,017 Actions and 8,228 transitions), the scorer's holdout mode,
   and `eval/process_scale.py` (`results/process_graph.md`, `process_graph_grid_scale.md`, `process_scale.md`).
   - **Annotation:** 19,360 turns, 0 failing after a retry (31 needed a second attempt), **about 0.8 calls per turn, $0.00082 a
     turn, about $0.74 per 1,000 turns of Haiku 4.5** (the resumed run: 15,873 calls, 9.8 million tokens in, $12.83, 47 minutes at
     concurrency 6; with the 100 conversations done earlier and the part killed first, about $16 for the corpus). **Resume:** the
     run was killed after 3 minutes and restarted; the first 200 conversations came back from the cache in no time and the run went on
     from there with nothing paid twice. A request the API refuses now fails that turn, not the pass (tested).
   - **Build, cold (every cache empty):** embedding 169 s (19,360 turns, in batches of 64), kNN 31 s, Leiden 3 s, **naming 456 s**
     (422 Sonnet calls, $5.00 at the kept parameters: 3,039 States are a lot to name), folding 130 s, lift 1 s, write 5 s; **a
     no-op rerun takes 46 seconds, makes no calls and writes the identical graph** (the same hash of every node, count, example and
     edge across three builds), of which kNN is 31. Folding by name vectors is quadratic in the elements and is the stage to watch
     if elements grow into the tens of thousands.
   - **Scale, the stages with no LLM** (placeholder text standing in for annotations, a database of its own, since dropped): **2.0 to
     2.2 seconds per 1,000 turns from 17,000 turns to 162,000**, so linear in practice: 162,221 turns (21,161 conversations) in 354
     seconds, of which kNN is 269 (76%), Leiden 27, lift 39, embedding 17, write under 1. Nothing stopped scaling. Naming and
     annotation are the cost: at the demo's $0.74 per 1,000 turns the scale set would cost about $120 to annotate.
   - **A determinism bug only the full run could show.** The first no-op rerun produced 542 States where the first build made 544,
     and called the model 47 times: GDS numbers nodes in the order they arrive, and kNN's tie-breaking among near-duplicate turns
     follows it; a native projection takes Neo4j's internal ids, which recreated scratch nodes do not get in the same order. (At
     100 conversations three builds had agreed by luck.) The kNN projection is now built from a query sorted by id, as
     `Graph.project_pairs` already was for Leiden, and three builds agree.
   - **The parameters did not transfer from 100 conversations to 2,000, so they were chosen again at scale, on a different slice, and
     judged on conversations nobody tuned on.** The 100-conversation choice (similarity 0.85) gave, on the 1,932 conversations that
     remained: 630 Action elements for 64 planted actions (Action V 0.79 against raw text's 0.71), stage purity 74% and transition
     fidelity 0.76 against raw text's 0.94. A grid on conversations 100 to 600, grouping all the turns, ranked 0.90 first by the
     criterion set beforehand (Action V + State V), with stage purity 91% (against 76%) and fidelity 0.90 (against 0.73), and with
     less coverage (67%, against 96%): the States are finer. **0.90 is now the default**, judged on the other **1,432**:

   | holdout, 1,432 conversations | graph | raw text | oracle |
   |---|---|---|---|
   | Action V-measure (homogeneity / completeness) | **0.77** (0.95 / 0.65) | 0.64 (1.00 / 0.47) | 1.00 |
   | State V against the planted State key | **0.77** | 0.67 | 1.00 |
   | State V against the coarse key | **0.65** | 0.55 | 0.80 |
   | stage purity of States | 89% | **97%** | 100% |
   | transition fidelity, Pearson / Spearman / MAE | 0.91 / **0.95** / 0.071 | **0.96** / 0.94 / 0.071 | 0.99 / 0.99 / 0.009 |
   | turns in singleton elements (States / Actions) | 25% / 6% | 32% / 34% | 1% / 0% |
   | turns with a recommendation, leave-one-out | 75% | 66% | 99% |

   The same graph on the 600 conversations the parameters were chosen on scores Action V 0.79 and State V 0.78, so **the gap
   between tuned and untuned is about two points: little was overfitted**.

   **What this says.**
   - **On a holdout the LLM annotation is worth about ten points of V-measure on both Actions and States** (0.77 against 0.64, and
     0.77 against 0.67), and it makes far fewer singleton Actions (6% against 34%): reworded questions join. It does not win on stage purity
     (raw text is purer, 97% against 89%), and the transition fidelity is level (0.91 against 0.96 Pearson, 0.95 against 0.94
     Spearman).
   - **The structural limit is Action completeness (0.65): about 800 Action elements for 64 planted actions.** The annotation is
     specific ("Ask whether the customer recognises the flagged transactions", "Ask about offers from other banks"), and the
     planted label is the family. That is not a defect of the cut; **it is what the hierarchy is for**, and it is the case for
     the abstraction plan: the first level is faithful and fine, the second must merge.
   - **Coverage is the price of the finer States.** 25% of State turns are in a State no other turn shares. At 0.85 States were
     coarser, covered 96% of turns and mixed stages. A coarse level over the fine one is the way to have both.
   - **The diagnostic number is unchanged in meaning:** the graph's likeliest next Action asks the clue's question 7% of the time (6-9%),
     the reps 10% (9-12%), the oracle 7%, chance 6%, the best single question chosen with hindsight 19%. A graph of what
     people usually do can only match the reps; to beat them it must rank Actions by where they lead (the abstraction plan).
   - **Breach detection from the path saturates:** 46 found, 13 false alarms, 0 missed, **identically for all three arms, the oracle
     included**, so it does not tell the arms apart (a planted breach is by definition a path with no verification, so any arm
     that finds the verification Action finds it). It is dropped as a discriminator; the false alarms are conversations where
     the plan does not require the gate.
   - **Spend, phase 4:** annotation about $16 (above), naming $7.6 across four full builds, of which $5.0 is the kept graph and
     $2.6 was spent on graphs a later fix or parameter change replaced (the non-deterministic rerun, the 0.85 parameters). Total
     about $23.
5. **Alignment with the warehouse, then the write-up.** *Built and measured (2026-10-05).* Entity linking by lookup, the composite alias, the
   three gaps, and the documentation. `qlsc process context <conversation> [--turn N] [--as-of DAY]` (`src/qlsc/process/context.py`; 22 new
   tests; `eval/process_context.py`; `results/process_context.md`; `demo.py process`).
   - **As of the moment:** memory's reads gained an `as_of` (the facts' window ends on the call's day and starts `memory.window_quarters`
     before it; `memory.cypher(until=)`, `run_batch(as_of=)`, `window_start(day)`), read and never remembered. The ordinary read is
     byte-identical (tested). **Memory's ordinary window would have put 13,609 facts that did not exist yet into 94 contexts (42% of
     32,165 nodes)**: that is the case for as-of.
   - **Fees:** `process.context.also` names tables the virtual graph's model does not serve; the table's customer column is the one
     the semantic layer says holds the same Variable as the subject's key, its date the table's partition column, and the read is the same
     window, the most recent `memory.cap` rows, through the connector's `run`. Fees are `dw_core.fct_fees`, found with no estate knowledge in
     the tool beyond the table's name in the estate's config.
   - **Mentions, by lookup:** a merchant by its name and its purchase's amount together (**several merchant ids share a name**: "Blue Plate
     Diner" is three ids in one customer's context, so the name alone is no link), a fee by its amount, written or said ("$7.65", "seven
     sixty-five", "eleven dollars and six cents", "a hundred seventeen fourteen"). Candidates are the customer's own rows as of the call.
   - **Scored against the answer key's `mentions`, on 100 conversations** (40 that name a fee, 40 a merchant, 20 that name neither; 6 of
     the 100 had no customer on the call, nobody having been identified, so no context): **all 80 named rows were in the context**
     (merchants from the virtual graph, fees from the warehouse); linking is **100% precise** with the controls in (0 wrong links) and **100% / 98% recall
     for merchants and 100% / 100% for fees from the turns alone**, 100% for both with the agent's after-call note. About 5 seconds a context.
   - **The composite alias `fennmoor.process` was created on 2026-10-05** (`process.composite` in the estate; `qlsc process build` joins the
     database and `fennmoor.process` answers: 3,044 States and 1,017 Actions through the composite). Each element keeps its examples'
     conversation ids, which is the warehouse's key for a call: a State reaches its calls' rows by a second query on `fennmoor.rows` (the
     composite cannot pass a value between constituents inside one query). `demo.py process` runs it: the busiest State, its calls, their live
     rows, one call's context as of the call.
   - **Two bugs found on the way.** (1) **The Virtual Graph (preview) answers a read silently wrong when sent parameters its query text does
     not use:** `keys` plus `since`, `until` and `limit` returned another customer's row whatever `keys` held (a matrix of parameter
     sets: only that combination failed; once as "Unsupported parameter type List"). Memory's ordinary reads sent fewer and escaped; the
     as-of reads sent one more, and 40 merchant contexts came back empty before the cause was found. A read is now sent only the parameters its
     text names (`memory.used`; tested). (2) Folding near-duplicate names was quadratic in Python (84 s at 3,044 States); a C dot product
     over unit vectors makes it 17 s and moved 5 elements (3,044 States for 3,039), after which the scores were rerun and are unchanged
     to the digit.
   - **Documentation:** README (a section), `docs/design.md` (the decisions and the limits), `CLAUDE.md` (the commands), the example's
     README, and `prompts/README.md`.

## Aligning the graph with the warehouse (the demonstration)

The requirement was that the context relevant to a call, at a given moment, can be fetched from BigQuery. It can (phase 5): a conversation's
id is the key of its `Call` in the virtual graph; that reaches its customer; the customer's context is fetched as of the call; fees, which
the virtual graph's model does not serve, are read from the warehouse by the column the layer says holds the customer's key; and the turns'
words are linked to those rows by lookup. The three gaps this section first listed (as-of, fees, mentions in context) are closed, and
scored against the answer key's `mentions`: "the right rows were retrieved at this turn" is measured, not asserted (see phase 5).

## What does not change

The semantic, virtual graph and memory shards, and `qlsc build`'s log-only path. The warehouse and its datasets are untouched; the
extract reads only datasets starting with `dataset_prefix` (`fnb_`), so **a dataset for the events outside that prefix is invisible to
it, and nothing is regenerated.** Putting the events in BigQuery is therefore optional and independent of this plan: the builder reads
the file or the bucket. It is worth doing only to show the text joining `fct_calls` in SQL, in a dataset such as `fennmoor_process`,
never `fnb_`-prefixed (a prefixed one would be swept into the catalog at the next extract, and the semantic layer and the virtual
graph schema, which are rebuilt rather than updated, would need a rebuild), and never with the answer key in it.

## Risks

- **Leakage again.** Singleton States make a graph that replays the call it was built from. Leave-one-out and the singleton share
  are the guard; if the share is high, the cut is wrong or the State description is too specific.
- **The corpus's own difficulty.** Servicing is near-scripted (a control), and a closing is repeated 200 times: States made of
  closings will be large and uninformative. Reported, not hidden.
- **Cost of per-turn annotation.** About 19,000 turns in the demo corpus; at the previous project's roughly 12 calls per
  conversation that is a few tens of thousands of calls. The cost is **measured at 25 before it is estimated**, and prompt
  caching of the conversation prefix is the first lever.
- **The planted State is partly unobservable.** The rep's belief is not in the text; the plan scores the observable State key
  first and says so.
- **Embedder and thresholds.** Thresholds tuned to one embedder do not carry; every cut is a parameter with its measurement.

## Decisions

1. **Observations as nodes or not.** *Recommend not:* two labels, `State` and `Action`, with the event-to-element mapping as a
   build record and a capped `examples` list on each element. The alternative keeps the previous project's observation layer in
   the graph (more to store and explain; nothing in this plan needs it).
2. **The annotation unit.** *Recommend deciding by the phase 1 measurement:* per turn from the prefix is the reference; per
   conversation is adopted only if it agrees closely and does not see the outcome.
3. **Models.** *Recommend Haiku 4.5 for annotation, Sonnet 5.5 for naming,* the realiser's lesson inverted (the volume is in
   annotation, the judgement in naming), confirmed on the 25. A per-turn short structured answer is what Haiku does well.
4. **Where the code lives.** *Recommend `src/qlsc/process/`* (generic, reads the config's field map, knows no example), the
   prompts in `prompts/`, the parameters in `defaults.yaml`, the scorer in the example's `eval/`.
5. **A bucket reader in the tool.** *Taken, and built without a new dependency* (see phase 0): a connector, `warehouse/gcs.py`.
6. **Events in BigQuery.** *Recommend not now.* Not needed to build or score; when a SQL demo wants it, a dataset outside the
   `fnb_` prefix in the same project (so no rebuild), the answer key kept out.
7. **Case notes.** *Recommend excluding them from States and Actions* (they summarise the whole call, so they would leak the
   outcome into every State) and holding them for the abstraction plan, where they are the natural evidence for where a call ended.
8. **The State key as the primary target.** *Recommend yes* (stage, clues established, authenticated), with the rep's belief as the
   harder second target. The corpus's sidecar already has what is needed; no change to the corpus.

# A business process graph, and simulation-style retrieval over it

Status: proposed (2026-10-03); revised 2026-10-05 after the first decisions (below). Nothing here is built.

**The abstraction work is now drafted as [process abstraction](2026-10-06-process-abstraction.md)**, which supersedes this plan's phases and
model; this file is kept as the record of the original design (its retrieval, governance and evaluation ideas are carried there).

**This is now the second of three plans**, split on 2026-10-05: [the process corpus](2026-10-05-process-corpus.md) (built), then
[extraction and construction](2026-10-05-text-graph-construction.md) (the first level of States and Actions, from text), then
**this one, process abstraction**: the hierarchy over that graph (GDS clustering of States and Actions into levels), where a case
ends (Resolution as a node or as an absorbing probability on a State), path and outcome odds, discovery from usage, the
entitlement gate, and the agents. Its phases below that read event rows or build the first level are superseded by the two plans
before it; what remains here starts from the State-Action graph they produce.

## Decisions of 2026-10-05

- **A separate shard: yes** (decision 2). `process` joins the composite beside semantic, rows and memory.
- **The source is an unstructured corpus,** not the warehouse's event tables. The aim is to show an unstructured source
  joining the context layer and fast knowledge-graph construction from text, with the other project's code as the starting
  point. This **supersedes decisions 1, 4 and 5 below** as written:
  - Event *rows* are no longer the input, so the question of admitting row data (decision 1) falls away for now. The
    log-only build stays untouched; the text source is read like the estate's other sources, by a path in its config.
  - The process is planted in generated text (decision 4), by the plan in
    [the process corpus](2026-10-05-process-corpus.md), bound to existing `fct_calls` rows rather than refilling tables.
  - The LLM now does the extraction (decision 5), as in the other project, so what "high performance" means (calls per
    conversation, no quadratic projection, a vector index, caching) becomes the next plan's centre.
- The structured-event miner (this plan's "Mine") is kept as an optional later source, not dropped.
- **The process abstraction keeps the State-Action model** of the previous project (a State is where a case is, an Action is
  what is done, and the lifted graph carries the transition counts and probabilities). The separate Resolution label
  may not be needed: where a case ends can be an **absorbing probability on a State** (how likely each State is to end well,
  and in what), which the absorbing-chain odds in this plan already compute. To be settled when we reach process abstraction,
  not before. The corpus's ground truth records the planted State at every step (the rep's leading hypothesis and how sure
  they are, per stage) so the discovered States can be scored against it.
- Still open: decisions 3, 6 and 7. [Extraction and construction](2026-10-05-text-graph-construction.md) is split off and takes the first level; these stay here, for abstraction.

## Why

The semantic layer says what the warehouse _means_, the virtual graph gives the live rows, and memory keeps what an agent
fetched. None of them say how the business's work _behaves_: what usually happens to a fraud alert after two days in
review, how long a loan decision takes, which way a call goes after a transfer, and how often each ends well. An agent
holding a case needs that to reason about procedure: where is this case, what are its likely next steps, and what does each
choice do to the odds and the time.

The `call-transcripts-automation` project shows the idea working on call transcripts: a graph of **States**,
**Actions** and **Resolutions** with transition counts and probabilities, and agents that locate a live call in it and
reason over the paths that lead onward. This plan brings that capability in here, built from the warehouse's own event data
rather than from transcripts, and kept consistent with how qlsc works (usage as ground truth, deterministic, measured,
governed by the warehouse).

## What the other project does (read 2026-10-03)

**Build (`kg-builder/`, LangGraph, three order-dependent passes).**

1. _Ingest:_ transcripts become `Call`, `Comment`, `Customer`, `Representative`, chained in time order and embedded.
2. _Process discovery:_ an LLM annotates each turn: a customer turn gives a **State** description, a rep turn an
   **Action**, the end of the call a **Resolution** (about 2,200 LLM calls on the 100-call corpus). Observations are embedded
   (512 dimensions), linked in sequence, and clustered with GDS (a similarity projection computed on the fly, then PageRank
   and Leiden). Each community becomes a canonical `ProcessElement`; an LLM names it; near-duplicate names are folded; the
   sequence edges between observations are _lifted_ to `ACTION_SELECTION`, `TRANSITION` and `PROCESS_END` with `num` and
   `probability`.
3. _Ontology:_ entities are extracted from comments, observations and elements, deduplicated against a vector index,
   and linked back with the supporting quote.

**Use (`ui/`, three LangGraph.js agents).** All start the same way: embed the latest comment, vector-search similar
historical comments, jump to the process element their state belongs to (`lib/processMap.js`, `PATHS_FROM_STATE`). Then:
take the highest-probability next action, find paths to every reachable resolution with `shortestPath`, and rank them by the
product of their edge probabilities. The recommendation agent turns the top paths into advice; the suggested-response agent
writes three replies, each steering toward a different projected outcome, grounded in real rep comments from that state;
the simulator plays the customer.

**What it taught (their own docs, `IMPROVEMENTS.md`, `corpus/README.md`):**

- _Plant the world, then render it._ The corpus samples a causal path first (fault, what the customer noticed, what the
  rep asked, the action, its efficacy, the outcome) and an LLM only chooses the words. That gives ground truth, and a scorer
  (`corpus/score.py`) measures what the graph recovered: edge probabilities correlate 0.924 with the planted frequencies
  (mean error 0.013), Action elements are 0.977 homogeneous.
- _The scorer found the demo's claim false._ Where a customer had noticed a discriminating clue without mentioning it, the
  graph's top next action asked about it 3.6% of the time against 16.9% for the reps it was built from. Cause: States
  described _what the problem is_, not _how far the diagnosis had got_, and 79% of State elements were single observations.
- _Process by LLM annotation and clustering is fragile._ Thresholds need retuning with every change of embedding width;
  the same text embeds at cosine 0.996 across requests, so clusters near a threshold move between rebuilds; the similarity
  projection is quadratic (about 144M pairs at 12,000 observations); observations were created with random ids, so a
  re-annotated call duplicated its observations (they had to add run checkpoints for correctness).
- _Retrieval gaps they list:_ a `k=7` comment search can fill with scripted rep lines and return nothing; `shortestPath`
  gives the shortest route to each resolution, not the most probable one, and the first step is a single `LIMIT 1` action.

## What differs here, and what that buys

- **Our process data is already structured.** Status histories, decision sequences, alert dispositions and call segments
  have a case key, an activity and a timestamp. States need no embedding and no clustering, and the quadratic projection
  and the threshold go away. The mining is a warehouse aggregate; the LLM only names things (tens of calls, not thousands).
- **The log tells us where the processes are.** qlsc's principle is that usage is the ground truth. Which tables are
  process logs, and which columns are the case, the activity and the time, is visible in how the business queries them
  (decision 1 below).
- **Zero copy holds.** Only aggregates are stored: stages, transitions with counts, probabilities and durations. No case
  rows leave the warehouse.
- **Retrieval can be done properly.** Absorption probabilities and the most probable paths come from the transition
  matrix, instead of `shortestPath` ranked by a product.

## The fit with Fennmoor today, and the gap

Four filled tables hold process-shaped events: `genesys_cloud.segment` (call segments: type, start, end, wrap-up code,
disconnect type), `loan_origination.decision` (`decisionSeq`, outcome, `decidedAt`), `fraud_platform.alert` and `fraud_case`
(status, disposition, `dispositioned_at`, analyst, loss), with `case_alert_link`.

**But the generator plants no process.** `spec/data.yaml` gives `segment_type` a fixed cycle, `[interact, hold, interact,
wrapup]`, and wrap-up codes are drawn independently of what happened before. A miner run on that finds a straight line.
This is exactly the corpus problem the other project hit and fixed: there is nothing to recover. So the example needs a
**process world** whose dynamics are planted, with ground truth, before any miner can be scored (phase 1).

## Architecture

```
warehouse event tables ──(usage evidence from the layer)──> process discovery: candidate sources, proposed for a person
                                                                       │ approved
                                      one aggregate SQL per source <───┘
                       (transitions, durations, outcomes; bytes capped; run by the connector)
                                                                       │
                                  process shard (Neo4j): Process, Stage, Action, Outcome  <── LLM names only
                                       │   absorption odds, expected time, k most probable paths, per stage
                                       │
      composite: semantic · rows · memory · process ──> agents: locate a live case, outlook, compare actions
```

**A fourth shard, `process`.** It is stored, refreshed on the data's cadence rather than the log's, and governed
differently (aggregates over possibly restricted data), so it is not part of the semantic layer. It joins the composite as
`process`. It keeps stubs of the layer's Table and Column nodes by id, as memory does, so it survives a rebuild.

### The model (four labels, evidence on properties)

```
(:Process {id, name, description, tables, case_key, activity, time, window, cases, built_at, holds_until, status})
(:Process)-[:HAS_STAGE]->(:Stage {id, name, value, cases, dwell_p50_s, dwell_p90_s,
                                  expected_remaining_s, outcome_odds, rework})
(:Stage)-[:TRANSITION {n, p, p50_s, p90_s}]->(:Stage)
(:Stage)-[:ENDS_IN {n, p, p50_s}]->(:Outcome {id, name, value, cases, favourable})
(:Stage)-[:TAKES {n, p}]->(:Action {name})-[:LEADS_TO {n, p, p50_s}]->(:Stage|:Outcome)   // only where an actor or action column exists
```

`value` is the source column's value the stage stands for (the link to rows). Ids are hashes of process and value, never
random, so a rerun reproduces the graph. Counts are assigned from the aggregate, never incremented. `outcome_odds` and
`expected_remaining_s` are computed once per build from the transition matrix (absorbing Markov chain), sorted and
deterministic.

## Build

**Discover** (`qlsc process discover`, part of `qlsc build`, deterministic, no row reads). Score every table in the layer as a
process log from usage evidence, and write candidates as `Process` nodes with `status: proposed`; a person approves
(`qlsc process --approve`), as for skills. The evidence:

- a _case key_: a Variable shared with other tables, not unique in this one (`unique(table, column)` false), so the same
  case appears on several rows;
- a _time_ column: a timestamp, the partition column, or one the log orders or windows by (`READS` carries the roles
  `order` and `window`);
- an _activity_ column: a categorical text column whose values the log filters or groups on (`FILTERS` values);
- usage shaped like process analysis: window functions over the case key, funnel and conversion Computations, status counts;
- a table a production process writes (CDC history), which suggests the history is the system's record.

An estate may name sources in its config instead (`process.sources`), as `virtualize.tables` does.

**Mine** (`qlsc process mine`, a data refresh: not in the log-only build, its own `built_at`). For each approved source the
tool renders one aggregate query (sqlglot, in the warehouse's dialect, so no warehouse code in the tool) and the connector
runs it under the byte cap. The query takes consecutive events per case (`LEAD` over the case key ordered by time, or old
and new status where the table has both) and returns, per (activity, next activity): count, median and 90th-percentile gap.
Terminal activities become Outcomes. A column that unpivots to milestones (opened, closed) and a sequence number are adapters
over the same shape. Strata (priority, channel, segment) are optional extra group-by columns, kept off the stored graph (see
retrieval).

**Name** (the only LLM step, `prompts/process_*.md`): a process, a stage and an outcome each get a business name and a
sentence from their values and counts, cached like every other call. A person-readable `MODEL.md` lists what was mined.

**Drift.** A process changes (the Genesys cutover in October 2025 is one). Mining windows are versioned: a changed
transition structure between windows becomes a new `Process` version linked `SUCCEEDS`-style to the old one, so an
outlook never averages two regimes.

## Retrieval: the simulation-style queries

The in-context payload is small and measured (`qlsc/meter.py`): the stage, the next-step distribution with typical times,
the outcome odds, the few most probable paths with probabilities and durations, and the evidence counts, so an agent can
see how much to trust it.

1. **Locate.** Find the stage. From a live case, read its current activity through the virtual graph (two round trips: the
   composite can't pass a value between constituents) and match it to a Stage by `value`. From a description, match a stage
   name by embedding, a fallback only.
2. **Outlook.** For a stage: `TRANSITION` and `ENDS_IN` out of it, absorption probabilities per Outcome, expected time
   remaining, and the k most probable paths (best-path search over the matrix, not `shortestPath`).
3. **Compare actions.** For each next step open to the case, the outcome odds and expected time if taken: the "what
   happens if we..." question. It is observational: the analysts who escalate may be handling harder cases. The payload says
   so, and the evaluation includes a planted confounder to test it (below).
4. **Simulate.** Sample continuations from a stage for a chosen number of runs, to give a distribution of outcomes and
   times, optionally conditioned on strata. A conditioned run asks the warehouse for those aggregates, as the same query with
   a `WHERE`, and suppresses any cell with fewer than `process.min_cases` cases.

Exposed as `qlsc process outlook | compare | simulate`, and as agent tools beside `ask` and `recall`. Whether a "process
question" becomes a router route is a later step (decision 6): the compiled and precedent routes answer _what happened_;
this answers _what usually happens next_.

## Governance

- **Aggregates carry their sources' access rules.** A principal sees a Process only if the warehouse lets them read every
  table and column it mines (the allowlist, `entitle.py`). The process shard is read through that gate.
- **Row-policied sources are not stored.** A table with a row access policy has reader-dependent data; its aggregates are
  computed on demand as the principal and never kept in the shared shard, as memory treats a row-policied node.
- **Small cells are suppressed** (`process.min_cases`), and actors appear as counts, never names.
- **Restricted domains** (AML, SAR filing: the existence of a filing is itself sensitive) are excluded from estate-wide
  mining by default and enabled per estate, per source.

## Evaluation (before the miner)

The other project's lesson, taken whole: build the answer key and the scorer first, and measure.

**Phase 1 plants the world.** `spec/processes.yaml` (the answer key, never read by the tool) defines, per process, stages,
transition probabilities, durations, outcomes and planted traps. A sampler draws each case's path first and writes rows into
the existing tables, so everything downstream still flows. Ground truth goes to `build/process_truth.json`. Traps:
a rework loop, a bottleneck stage, a dead-end, a fast path that depends on a covariate, an outcome that depends on a _hidden_
covariate the stage doesn't show (the analogue of the 3.6% finding), a confounded intervention, a regime change mid-window,
and a negative control (a table with the same columns and shuffled order, which must yield no structure).

**Metrics** (`eval/process.py`, committed under `results/`):

1. _Discovery:_ did it find the planted process logs, with the right case, activity and time columns? Precision and recall,
   and no proposal on the negative control.
2. _Recovery:_ transition-edge precision and recall; probability error and correlation (their 0.924 as the yardstick);
   duration error; outcome-odds error (total variation distance).
3. _Decision value, on held-out cases:_ next-step accuracy against a global-frequency baseline and an LLM with no graph;
   outcome prediction by Brier score and calibration at several checkpoints in a case's life; the compare-actions answer
   against the planted optimum, with and without the planted confounder; whether the hidden-covariate trap is detected as
   uncertainty rather than answered confidently.
4. _Cost:_ tokens and seconds of each outlook, against the service targets.

Results are reported as they come, including the ones that show the graph doing worse than a baseline.

## Phases

0. **Decisions** (below), and this plan agreed.
1. **The world and the scorer.** `spec/processes.yaml` for call handling (the closest to the reference demo; the segment
   table is filled), the sampler, `process_truth.json`, `eval/process.py` with the baselines. No miner yet.
2. **Mine and model.** The event-log adapter, the aggregate query, the `process` shard, absorption and best paths,
   `qlsc process mine | outlook`, tests (the pure parts), scores against phase 1.
3. **Discover from usage.** Candidate scoring, proposals and approval, the entitlement gate, the composite alias, the
   design doc and README sections.
4. **More domains and adapters.** Fraud alert to case (milestones, actors, loss: the richest outcomes), then loan decisions
   (sequence numbers).
5. **Agents.** The tools beside `ask` and `recall`; the comparison harness gains an arm with the outlook and one without.
6. **Optional: processes from text.** Where a source has text only (case notes, transcripts), the other project's LLM
   annotation route, carrying its fixes (stage in the state description, deterministic ids, a stored embedding for idempotent
   merges).

## What does not change

The semantic layer's build, the virtual graph's model, the router's existing routes, memory's model, and the rule that
`src/qlsc/` and `prompts/` know nothing of any estate. The log-only build stays log-only: mining is a separate, labelled
refresh.

## Decisions needed

1. **A new admissible input: event traces.** `docs/design.md` says row data is not an input, with one exception (a safety
   check). Mining reads rows, as aggregates. _Recommend yes,_ with discovery from usage evidence, aggregates only, a separate
   command and `built_at`, and a design-doc update. The alternative (leave process models to the estate's config) loses the
   automatic discovery that is the point.
2. **A fourth shard or part of the semantic layer.** _Recommend a separate shard:_ different refresh cadence, different
   governance, and it matches the three-shard picture. The cost is another composite alias and stubs by id.
3. **Order of domains.** _Recommend call handling first_ (it mirrors the reference demo and the table is filled), then fraud
   alert to case, then loan decisions. AML and SAR stay out unless you want them.
4. **Plant the process in the example's generator.** _Recommend yes:_ without it nothing can be scored, and the current data
   is a fixed cycle. It changes the generator and the filled data for those tables, so a refill of them is needed.
5. **LLM role.** _Recommend naming only_ in phases 1 to 5; text-derived processes as the optional last phase.
6. **Router route or tools only.** _Recommend tools only_ at first; add a route once the outlook's accuracy and cost are
   measured.
7. **The suppression threshold** `process.min_cases`, and whether row-policied sources are excluded or computed on demand
   (recommended: on demand).

## Risks

- **Observational data is not causal.** "What happens if we escalate" can mislead where choices follow case difficulty. The
  plan tests it with a planted confounder and labels it in the payload.
- **Sparse stages.** The other project had 79% single-observation states. Structured stages should not, but rare statuses
  will; the payload carries counts and the suppression rule applies.
- **Hidden state.** The next best step often depends on something the stage doesn't show. Covariate strata and an explicit
  uncertainty statement are the mitigation; the planted trap measures it.
- **Process drift** across a cutover; handled by versioned windows, and tested by the planted regime change.
- **Warehouse cost.** One aggregate query per source, a handful of columns each; capped by `maximum_bytes_billed`, and the
  refresh is on the source's write cadence.

# Efficacy as traversal: question spaces below, rules above

Status: proposed (2026-10-06, revised the same day). Nothing here is built, and every item that changes the model or the method waits on your
decision (the last section). It follows [the process abstraction plan](2026-10-06-process-abstraction.md), whose phase 5 ended on the finding
below, and it depends on [the layered refactor assessment](2026-10-06-question-spaces-and-traversal.md), which says how much of the code this touches.

**What changed in this revision.** The first draft put "what fixes what" into a designed ontology of causes, clues and actions that sat beside the
graph. A customer conversation (2026-10-06) gave a better cut, and this revision follows it. **I had the layers the wrong way round for "ought".**
The cut is:

- **A lower ontology is a question space, and it is governed by *is*.** It holds what can be asked and what can be done in one region of the
  business: the datasets, measures and joins of a semantic view, and the actions and skills the business has actually executed. Nothing is in it
  that the historical record does not show the business doing. Automation adds actions to it from that record.
- **An upper ontology is a traversal, and it is governed by *ought*.** It maps a request, or a case, to a lower ontology and to a path through it:
  which space, which question first, which action, under which gates. **To change what the business does, you change the traversal.** It is
  authored and stewarded by people.

So efficacy (what *should* fix a cause) is a **traversal rule**, not a fact in the lower layer, and the lower layer's numbers are evidence about what
happened, never a recommendation. That is the structural answer to the confounding we hit: our "best ending after" tried to derive *ought* from
*is* inside the lower layer.

## Why

The process graph says what reps did and how cases ended. It cannot say what *should* be done, because the success of an Action is confounded by
the cause the rep knew and the State does not say (three fixes to the ranking failed: `results/process_outlook_ranking.md`). Measured on the whole
corpus (2,032 conversations, leave-one-out, Brier against the planted favourability):

| what predicts a good ending | Brier |
|---|---|
| nothing (the base rate) | 0.236 |
| the true cause alone | 0.195 |
| our graph's States | 0.19 to 0.20 |
| **the committed action's efficacy against the cause** | **0.049** |

The ending is decided by whether the Action fits the cause. Two thirds of cases already get an Action that fixes the cause; the other third is the
headroom. Reaching it needs **the cause** (inferred from what a call shows and from the customer's context) and **a rule for what to do about it**
(knowledge no log holds). In the agent test (`results/process_agent.md`), giving an LLM agent the process's own tables lifted it from 12% to 18% useful
choices and the warehouse's call record lifted it to 31%: both help, neither is the whole answer.

## The two layers

### The lower ontology: a question space ("is")

A **question space** is a region of what the business asks and does. For analytic questions it is what we already build: a business area of the
semantic layer with its Variables, tables, trusted joins, Computations (measures, derived dimensions, populations), the Requests the business
makes of it, the precedents (its own queries) and the virtual graph's slice. That is exactly what a semantic view is in a warehouse product, and
the semantic layer is what scopes it: the customer scoped Snowflake semantic views by question spaces defined from an earlier version of our layer.

For a process (a contact centre) a question space adds **what can be done**: the Actions reps take and the skills agents follow, bound to the
space. **Automation adds them:** an Action element or a skill enters a space when the record supports it (enough conversations, enough distinct
people, stable across rebuilds, the entitlement to read what it reads), with the evidence beside it. They leave when the record stops showing them.

- **Governed by evidence.** An object is in the lower ontology because the log, the conversations or the agents' traces show it, and each carries
  that evidence (runs, distinct authors, window, conflicts, stability; for an Action also its outcomes, labelled observational).
- **It includes what should not be repeated.** The record holds wrong remedies and policy breaches; "the business can do it" is not "the business
  should". Telling them apart is the upper layer's job, which is why the two are separate.
- **A skill is a bundle:** its slice of the space, a procedure, and worked examples (precedent queries, question and answer pairs from the request
  bank, traces), masked of values, shown only to readers who may read what it reads (`distill.py` already does the masking and the entitlement test).

### The upper ontology: a traversal ("ought")

A **traversal** takes a *request* (a question, or a case: an intent, the context's facts, the State so far) and decides, as a set of rules:

1. **which space** it belongs to (a question to a business area; a case to a procedure and its hypotheses),
2. **what to do there:** which question to ask first, which action or skill to take, in what order,
3. **under which gates:** verify identity when the phone system has not authenticated the caller; never offer what costs money before a clue is in.

A rule has a name, a steward, a status, a date to be reviewed, and what it rests on. **Efficacy is a rule:** "for this hypothesis, this action", with
the strength a person asserts (`fixes`, `partial`, `worse`). **The diagnosis is a traversal step:** cases are classified into hypotheses from the
clues established and the context's facts. The hypotheses and clues are the upper layer's vocabulary (`Concept`, as `qlsc align` already holds
designed terms).

- **The default traversal is what we already do:** similarity to the semantic layer, then the router's ladder of routes. Making it an explicit,
  inspectable object changes nothing until a rule overrides it.
- **Changing behaviour is editing a rule,** reviewed and tested before it is active (the agent test and, later, the replay), and it never
  edits the lower layer's evidence.
- **Automation may propose a rule, never activate one.** Proposed rules (from usage, or drafted by an LLM from sample conversations) wait for a
  steward.

### The evidence layer beneath both

What `qlsc` builds from the log and the conversations. Its records have a **kind**, ranked: usage (it was run), observational outcome (it was run and
this followed: confounded), experiment or replay (the action was chosen at random or by a policy under known causes). An efficacy rule shown with
only observational evidence says so. The disagreement between a rule and its evidence (a remedy taken for a cause the rule says it does not
address; a clue nobody asks; a rule nothing in the record has ever exercised) is a product, like `ALIGNMENT.md` for the semantic layer.

## Mapping to what exists

| This plan | In the code today |
|---|---|
| Question space | a `Semantic` node (level 2 or 3), with its Variables, tables, Computations, Requests; the OKF bundle already files Computations by area |
| Actions and skills in a space | process `Action` elements (the `process` database) and `Skill` nodes (memory), neither yet tied to a space |
| Evidence | `MEANS {score, status}`, OKF provenance (runs, authors, `draft` or `stable`, no `verified`), `support`, `K_SIM`, group stability |
| Default traversal | `navigate.cohort` and `navigate.route`: similarity, then memory, precedent, compiled SQL, Cypher, free SQL |
| Upper vocabulary | `Concept` (catalog terms, ontology classes) |
| New | a `Rule` label (the traversal rule), with `APPLIES_IN`, `WHEN`, `THEN`; evidence records on lower objects |

Few labels, each meaning something to a business reader: a **question space** is a business area; a **rule** is a policy. No label for a "fragment".

## Phases

0. **Decisions below, and this plan agreed.**
1. **Question spaces.** Choose which Semantic level is a space (by stability and by how well navigation scoped to it does), name them, and give each its
   scope: tables, joins, Computations, Requests, precedents. Also discover the **process spaces**: group the States and Actions by what they share
   (transitions and the abstraction levels already built) and score them against the planted procedures. First measurement: navigation scoped to a space
   against the current navigation, on the 186 questions (the refactor assessment's H1). No LLM beyond naming.
2. **Actions into spaces.** Promote Action elements and skills into their spaces by the gates above, with evidence records. Scored against the planted
   action of each element and the planted procedure of each space: accuracy, and the diff of what is outside every space.
3. **The upper vocabulary and rules.** `qlsc process ontology import`: a YAML file of hypotheses, clues and rules (the schema is ours, the content the estate's),
   checked (no dangling reference; effects one of three; probabilities in range; every hypothesis reachable by a question or a context fact; every
   rule's action in some space), written as `Concept` and `Rule` nodes. Generic: `src/qlsc/` knows nothing of any estate.
4. **Diagnose and advise, as a traversal.** The posterior over hypotheses from the clues established (aligned from each State by one cheap call), the
   questions asked and denied, and the context's facts (a hypothesis whose needed fact is absent is excluded; the facts are Computations in the lower
   layer: the binding to check). The prior is the ontology's, or, where support exists, the observed mix of hypotheses at the nearest States: the
   ontology says how a hypothesis shows, usage says how often. Then the rules: gates first, expected effect, and for a question the value of
   information against the cost of a turn. The output is a short list with the posterior, the rules it used and their status and evidence, the reps' observed practice beside it,
   and where they differ. Scored as phase 4 of the abstraction plan scored recommendations (a remedy that fixes the real cause, or a question for a true
   unsaid clue; against the rep, the typical rep, the old ranking, chance, hindsight), then in the agent test with the advice beside the call.
5. **Change the behaviour by editing a rule.** The test of the upper layer's reason to exist: edit one rule (for example, ask the open question before any
   remedy; or never offer a costly action before a clue) and show the agent test and the replay move as intended and nothing else moves. Also the reverse: a
   rule that is wrong, and the evidence layer saying so.
6. **Degrade it, draft it, replay it.** The result of 4 in this example is **an upper bound, not evidence** (see Risks): the rules come from the generator's
   world. Damage them in controlled ways and plot the lift (rules dropped 10, 30, 50%, flipped, probabilities perturbed, a hypothesis missing). Draft a second
   set **from usage**: an LLM reads sample conversations, States and endings and proposes hypotheses, clues and rules; a person (here, the scorer)
   ratifies. And the replay (decision 5 of the abstraction plan): the sampler's walk takes a traversal as its policy, the advice is taken at the
   decision point, the case plays out under the world's own causes, and the outcomes are compared with the reps'. The only test that can show an uplift
   over the historical baseline.

## How it is judged

On the holdout (conversations 600 and up), leave-one-out wherever a number is built from the conversations scored, Wilson intervals, parameters set on
the tuning slice:

1. **Spaces:** navigation scoped against current (accuracy, tokens, seconds, wrong-table rate); process-space V-measure against the planted procedures.
2. **Lower ontology:** action accuracy against the answer key; what is promoted and what is not; every object with its evidence record.
3. **Diagnosis:** log-loss and top-k accuracy of the cause by checkpoint, against the prior and against an LLM reading the call; calibration.
4. **Advice:** the useful share of choices against the rep (28%), the typical rep (22%), the old ranking (24%) and chance (13%); wrong or harmful remedies;
   by clue waiting or not, and by rep and customer archetype.
5. **Agent:** the agent test with the advice beside the call, against the call alone (12%), with the call record (31%) and with the process's tables as text
   (18%): does a structured rule beat the same knowledge as prose?
6. **Behaviour change:** a rule edit moves the outcome in the intended direction and leaves the other spaces' results unchanged.
7. **Robustness:** the degradation curve; the drafted rules.
8. **Gates, not thresholds:** a rebuild leaves rules and their alignments intact or flags them stale; no figure of the graph changes when rules are
   imported (additive); every advice names the rules it used; nothing automation adds is active as a rule.

Thresholds for the quality numbers are set after the first measurement, and results are reported as they come, including where the rules do no better
than the agent reading the same text.

## What does not change

The build, the levels, the outcomes, the odds and the outlook's observed numbers; `qlsc align` for the semantic layer; the entitlement gateway; the rule
that `src/qlsc/` and `prompts/` know nothing of any estate; the principle that usage is the ground truth for the lower layer and the evidence under the
upper one.

## Governance

A rule is an opinion with a name on it. It is versioned, carries who vouched for it and when, and is edited only by the principals the estate names
(`process.ontology.stewards`); a changed rule is recorded, never edited in place, as memory records a changed fact. Rules that automation or an LLM
proposes are never active until a steward confirms them, except in a clearly labelled preview. What enters the lower layer from the record is gated by
evidence and entitlement, and a steward can retire it. Advice is readable only by the readers who may use the outlook (`process.readers`).

## Decisions

1. **Adopt the two-layer reading: lower is *is* (a question space and the actions the record shows), upper is *ought* (a traversal that is changed to
   change behaviour)?** *Recommend yes.* It resolves the placement the first draft got wrong, and the principle (usage is the ground truth) holds for the
   lower layer and becomes the evidence under the upper one. The alternative is the first draft: one ontology beside the graph.
2. **Is a question space a `Semantic` node?** *Recommend yes, at a level chosen in phase 1 by measurement,* so no label is added and a space is already
   something a business reader recognises. The alternative is a new `QuestionSpace` label that references Semantic nodes, which adds a layer of indirection
   and a place for the two to drift.
3. **How are rules represented?** *Recommend a YAML file stewards edit and version, imported to `Rule` nodes,* so a change is a reviewed diff. The
   alternative is nodes edited in place through a tool.
4. **Who may add an action to the lower layer?** *Recommend automation, gated by evidence and entitlement,* with a steward's retire. Nobody adds a rule
   automatically.
5. **How the example gets rules.** The world's spec is already such a set, and using it is a closed loop. *Recommend three:* the spec as the upper bound;
   the spec degraded; and a set drafted from usage and ratified. Say if you would rather have an independently authored one.
6. **Evidence kinds** (usage, observational outcome, experiment). *Recommend recording the kind on every evidence record from the start,* so a rule's
   support is never shown as more than it is.
7. **The weights** (`fixes` 1, `partial` 0.5, `worse` -1, an extra -0.2 for an action that costs money, a turn costing 0.05). *Recommend setting them on the
   tuning slice;* they are policy, so a steward may override them.
8. **Negative evidence** (a clue asked about and denied). *Recommend including it from the start.*
9. **Does the advice come back into the tool?** *Recommend yes, only after phase 4 meets its gate* (better than the typical rep where a clue is waiting,
   and a wrong remedy under the reps' 3%); until then the outlook stays a picture.
10. **The replay here, as phase 6.** *Recommend here,* since its only job is to test a traversal.

## Risks

- **The closed loop.** The example's rules are its generator. Phases 4 and 5 will look good for that reason and must be reported as an upper bound. The
  degradation curve, the drafted rules and, most of all, a real estate are the evidence.
- **Space boundaries.** A table can belong to several spaces, and Semantic levels 2 and 3 are 15 and 4 groups in the example: too coarse or too fine
  for a space is an empirical question (phase 1), not an assumption.
- **What the record shows is not what is allowed.** The lower layer will contain breaches and wrong remedies. The upper layer, and the entitlement
  gateway, are where "should not" lives; promoting an action must not read as endorsing it.
- **Alignment errors compound.** A wrong Action alignment mis-assigns a rule; a missed clue changes a posterior. Each step is scored before the next uses it,
  and a confidence floor keeps unsure alignments out of advice.
- **Calibration.** A rule's strength is a person's guess. The observed mix of hypotheses at the nearest States is the check; a large disagreement is a
  finding about the rule, not something to average away.
- **Rules age.** Review dates and the contradiction flags exist for this; a stale rule is shown as stale.
- **Authority.** "The ontology says" can outrank a rep's judgment it should not. It is offered as a prior with its working shown, and the agent test
  measures whether the advice helps, not whether it is believed.
- **Wrong causes in the observed data.** Where reps misdiagnosed, the observed mix of hypotheses is the reps' belief. The corpus records `believed_cause`
  beside `cause`, so the evaluation can say how much of a posterior's error is the reps'.
- **A borrowed vocabulary.** "Upper" and "lower" ontology mean something else in the literature (general concepts above domain ones). Our documents say
  *question space* and *traversal*; the customer's words are a gloss, and the customer should be asked whether they mean the same.

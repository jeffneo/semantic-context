# The process corpus: generating unstructured event objects for the Fennmoor estate

Status: agreed (2026-10-05: you accepted its recommendations), then **revised the same day after the warehouse was measured**
(the next section). It is the first phase of [the business process graph](2026-10-03-business-process-graph.md) as revised by your
decisions of 2026-10-05: a separate `process` shard, built from **text**. All five phases are built (the world and its validator; the row pool, the sampler and the matcher; the realiser, its checks and its gates; the full corpus; the audit and the hand-off note).

## Why

The process graph's source is now an unstructured corpus, so the corpus is the thing to get right first. Three jobs:
1. **Show an unstructured source joining the context layer.** The text must name things the warehouse knows (conversations,
   customers, agents, queues, sites, products, merchants), so what is read from it can be tied to live rows.
2. **Give the knowledge-graph construction something real to recover, and a way to score it.** The other project learned
   this the hard way: its first corpus had no outcome variance and no diagnostic content, so there was nothing to discover,
   and its scorer later showed the demo's headline claim was false. Plant the world first, with ground truth.
3. **Support a performance claim.** "High-performance KG construction from text" needs a corpus big enough to time, cheaply.

## What we reuse from the other project, and what we don't

`~/Desktop/demos/call-transcripts-automation/corpus/` is the model (its `SPEC.md` and `CORPUS-DESIGN.md`). Taken whole:
- **Two phases with a hard boundary.** Phase A (free, seeded, no LLM) decides everything causal: what is actually wrong, what
  the customer noticed and said, what the rep asked, concluded and did, whether it worked, and the outcome. Phase B (an LLM,
  one call per conversation) only chooses words, and its output is validated back against the plan.
- **The causal chain** (fault, manifestation, perception, expression, diagnosis, action, efficacy, outcome, recurrence), with
  its central mechanic: a clue reaches the text only if the customer *perceived* it **and** the rep *asked*. The discriminating
  clues have low salience, which is what gives a question value.
- **The rep is sampled from a profile, not improvised.** An LLM playing a rep is a uniformly good rep, so bad behaviour has
  to be injected deliberately. Archetypes shift probabilities and never dictate outcomes; outcomes are derived from the walk.
- **Ground truth as a sidecar** the builder never reads, with a scorer; diversity gates, calibrated on a real run; a free
  `--dry-run` for tuning distributions; per-conversation seeding so conversation 40 is the same however many you generate.

Changed:
- **The world is a bank's, and it is bound to the estate** (below), where theirs was a telecom's, free-standing.
- **The output is an event log, not a transcript file.** Each utterance, note or message is an event object with a
  conversation key, so a process can span channels and days.
- **Ground truth also lists the warehouse entities each event mentions,** so entity linking can be scored, which theirs
  (entities extracted and merged by name) could not.

## What the warehouse gives us, measured (2026-10-05)

The question was whether the warehouse can support credible process event logs. Measured against BigQuery: **it has the skeleton,
and none of the dynamics.**

**The skeleton is good.** 238,700 conversations from 2025-10-01 to 2026-06-29 (voice 78%, chat 15%, email 4%, callback 3%), 24,006
customers (8.9 calls each; 41% of calls come within 7 days of the customer's previous one), 1,450 agents (median 66 calls each),
86 queues, three sites (Tulsa, Spokane, the Manila BPO), 2.09 million segments, 26,331 CSAT responses. And things a story can point at:
24% of closure calls have an unwaived fee in the 60 days before (about 1,900 calls), 14.7% of `CARD` calls have a card purchase with a
merchant in the 30 days before (about 6,100), 43,000 merchants, 1.85 million card purchases, 610,000 fees.

**The dynamics are absent.** Every behavioural column is independent of everything it should depend on:

| Measured | Result |
|---|---|
| Every intent | transferred 57-58%, abandoned 39%, handle about 4,030 s. The same for chat, email and callback as for voice (an email handled in 67 minutes). |
| The three sites | Tulsa and Manila identical (63% transferred); no BPO effect. Spokane abandons slightly less. |
| Wrap-up code | 57 codes spread evenly for every intent except closures (3 codes). |
| CSAT | 3.0 for every intent and every outcome, including abandoned calls. |
| FRAUD calls and fraud alerts | 25.2% of FRAUD callers have an alert within 7 days, the same as BALANCE callers (24.9%). |
| Alert dispositions | about 78% false positive, 11% confirmed, whatever the model score, rule, channel or priority; 84 hours to disposition for all. |
| Alert and case states | contradictory: `FALSE_POSITIVE` alerts that are `ESCALATED`; `OPEN` cases with a `closed_at`; 1,466 cases recovering more than they lost. |
| Segment notes | five strings, assigned at random. |
| Empty tables | `salesforce.case`, `task`, `case_history`, `card_processor.dispute`, `genesys_cloud.ivr_flow_outcome`, `evaluation`: 0 rows. |
| Closures | 8,967 closure calls (3.8%) by 6,382 customers; the closure table has 3,849 rows; 1,060 customers are in both. |

Some rows are also unusable as a story: 39% of conversations are abandoned yet average 27 minutes of talk with no agent, 43,863 are both
abandoned and transferred, and the median handle time is 65 minutes.

So two things follow. A process miner pointed at these rows would find noise (a fair finding, and worth a line in the demo). And the
flags can't be hard constraints on the text, as this plan first said: honouring them would write a corpus in which most calls are
abandoned and the typical one lasts over an hour.

Corrections to the first draft: `salesforce.case` is empty, so the after-call note isn't in the warehouse and is generated; closure calls
are 3.8% (8,967, all answered, 8,081 coded `ACCT_MAINT` before 2026-06-02 and 886 `ACCT_CLOSE` after), while the `CLOSE_ACCOUNT` intent is
6.1% because 5,496 of them were never answered and have no wrap-up; the fraud platform's own disposition for a confirmed alert is `CONFIRMED`.

## Binding the text to the estate: select to fit

**The generator plans first and then picks a real row that fits the plan.** Phase A samples the conversation (procedure, cause, rep,
path, outcome) from the world's probabilities, then selects a matching row from the 238,700: the right intent (or the closure flag),
media, authenticated or not, site and agent (which carry the archetype and the site effect), abandoned and transferred as planned, a
handle time in range for the length of the plan, and, for causes that need one, a customer who has the fee or the card purchase.

- **Nothing in the warehouse is refilled,** as decided: no gold answer can move. Every event joins to its row by `conversation_id`.
- **The corpus is a sample, not a replica.** Its rates of transfer, abandonment and handle time are the plan's, not the warehouse's; the
  difference is reported rather than hidden, and is itself the point about the structured data.
- **Real facts get mentioned.** A fee-shock cause is only drawn for a customer with an unwaived fee, and the text names its type and
  amount; a dispute is only drawn with a real purchase, and names the merchant and the amount. Mentions resolve to rows.
- **Timestamps** stay inside the row's start and handle time; the number of turns follows the plan, not the duration.
- **The fraud platform and the closure table** are not joined for outcomes (the platform's are noise; decision 4). The fraud procedure
  borrows the platform's disposition vocabulary (`CUSTOMER_VERIFIED`, `FALSE_POSITIVE`, `CONFIRMED`, `INCONCLUSIVE`) for the ground truth.

## The world (v1: five procedures, from the estate's own vocabulary)

The procedures follow the IVR intents and wrap-up codes the estate already has, and the fraud dispositions it already uses.

| Procedure | Entered by (what the customer presents) | Hidden cause (the "fault") | What the rep can elicit | Commits to | Outcomes |
|---|---|---|---|---|---|
| **Retention** | intent `CLOSE_ACCOUNT` (the closure calls) | fee shock, a better rate elsewhere, relocation, life event, service failure, no longer needed | the reason, the fee on the statement, the competing offer, the move | fee refund, rate improvement, product change, or process the closure | retained with offer, retained without, closed after a save attempt, closed with none (a policy breach), escalated to the retention desk, abandoned |
| **Card dispute** | intent `CARD`, a charge named | merchant error or duplicate, true fraud, a subscription not cancelled, goods not received, buyer's remorse | when and where the card was used, whether the customer recognises the merchant, contact with the merchant | provisional credit and chargeback, advise the merchant first, route to fraud, decline with an explanation | resolved, partial, escalated, lost-and-disputed |
| **Fraud callback** | intent `FRAUD`, an alert | legitimate (travel, a large purchase), card compromise, account takeover | recent travel, other recent transactions, who else has the card | verify and release, block and reissue, open a case | uses the fraud platform's own dispositions: customer verified, false positive, confirmed, inconclusive |
| **Payment and fees** | intent `PAYMENT` | payment misapplied, autopay failed, hardship, a fee waiver due | the payment date and method, prior waivers | waive, arrange, escalate hardship | resolved, resolved with a breach, callback |
| **Servicing** | intents `BALANCE`, `ADDRESS`, `OTHER` | none (low-variance, scripted) | not applicable | answer, update | resolved |

Servicing is the **control family**: little variance, so a pipeline that finds rich structure there is inventing it.

**Policies** (gates a rep can skip, recorded as breaches): disclose account detail only after authentication (this ties to
`is_authenticated`); attempt a save before processing a closure; check the dispute window; verify identity on a fraud
callback; waive at most one fee a year. **Rep archetypes** (methodical, rushed, empathetic but imprecise, as theirs), assigned
by the estate's agents, with **site effects** planted on top: the BPO site transfers more, offers less and abandons more.

### Planted truths the text must carry (what the later scorer will test)

1. **The closure code, resolved by text.** Closure conversations before 2026-06-02 are coded `ACCT_MAINT`; the text shows they
   are closures. What the structured data hides, the text reveals.
2. **Elicitation has value.** A retention offer that matches the hidden driver retains far more than a generic one; a rep who
   asks the reason first does better. A discriminating clue (the competing rate, the move) is perceived but usually
   unvolunteered: the analogue of the other project's diagnostic finding.
3. **Right outcome, wrong process.** A fix that skipped a serious gate (an unauthenticated caller who was served anyway) is a breach
   the structured data calls a success: 4% of conversations, about 95 in 2,000, across every procedure. (As first written, a
   *save* that skipped authentication, this is too rare to carry the truth: 2 in 2,000.)
4. **A site effect and a misroute chain:** transfer, a second hold, abandonment.
5. **Recurrence.** A false resolution brings a callback from the same `cif_number` within days, linked in ground truth.
6. **Outcomes only the text holds.** Retained versus closed after a save attempt is not in `fct_calls`; it exists only in the
   conversation (and, for dispute and fraud, partly in the platforms).
7. **The control family and a verbatim-filler problem.** Servicing is near-scripted; closings like "have a great day" repeat,
   as in the other corpus, to keep the clustering honest.

## The event object

```jsonc
{ "event_id": "…", "conversation_id": "…",       // the join key to fct_calls and salesforce.case
  "seq": 3, "ts": "2026-02-02T11:13:40Z",
  "channel": "voice_turn | chat_message | case_note | email | callback_note",
  "role": "customer | agent | supervisor | system",
  "agent_user_id": "…",                          // an existing genesys user, for agent roles
  "text": "…" }
```

Conversation-level metadata stays in the warehouse. The text carries only facts a person would say: no names, emails or
other PII columns are copied from the estate (they carry policy tags there). Mentions are of products, merchants, branches
and amounts, which the later linking step resolves against `dim_product`, `dim_merchant`, `dim_branch`. Channels in v1: voice
and chat turns, plus the agent's after-call **case note**, which the empty `salesforce.case` would have held. It gives each
conversation a second, shorter, differently worded account of the same event.

## Ground truth (the sidecar, never read by the builder)

Per conversation: procedure, hidden cause, what was perceived, volunteered, elicited and missed, the stages with the
leading hypothesis at each (the planted state, as theirs), actions, policy breaches, efficacy, outcome and its
favourability, recurrence link, rep and archetype, site effect applied, and the **warehouse entities mentioned** with their
keys. Per event: the plan step it realises, its stage and its intended action. Written to `build/process_corpus_truth.json`
beside the estate's other answer keys. The tool never reads it; the evaluation does.

## Where it lives

- The world: `examples/fennmoor-bank/spec/corpus/*.yaml` (the answer key).
- The generator: `examples/fennmoor-bank/generate/corpus.py` (Phase A, Phase B, gates), `--validate-world`, `--dry-run`,
  `--stub`, as theirs.
- The output: `examples/fennmoor-bank/build/corpus/events.ndjson` (not in git, reproducible byte for byte for the planned
  part), plus the truth sidecar and a manifest. The estate's config names the events file; the text knowledge-graph builder
  (`src/qlsc/`, a later plan) reads only that path and the catalog, and knows nothing of Fennmoor.

## Size

- **The demo corpus:** 2,000 conversations plus about 200 callbacks, realised by an LLM (about 10 events each, 22,000 events). Their 1,000 conversations
  realised concurrently; cost measured at 25 (see phase 3).
- **The scale set:** 20,000 conversations, realised from templates (`--stub`) so it costs nothing, about 240,000 events. It
  is expected to fail the diversity gates by construction, and exists to time the builder at ten times the demo's size, with
  the text it will see in production (much of it repetitive).

## Validation (before anyone builds a graph from it)

1. **The world:** every cause reachable from some procedure, every procedure can end, every action has an efficacy row for
   the causes it can meet, every outcome reachable.
2. **The plan distributions**, by `--dry-run`: shares of procedures, causes, outcomes, breaches and recurrences against the
   targets above, before any spend.
3. **Consistency with the warehouse:** every event's `conversation_id` is in `fct_calls`; transfer, abandonment, authentication,
   media, site and agent agree with the row (they were selected to); timestamps fall inside the row; every fee or purchase named exists.
4. **Realisation:** each plan step appears exactly once and in order; no unelicited clue mentioned; no plan identifier or
   jargon in the text; failures regenerate once, then hard-fail with a reason.
5. **Diversity gates**, calibrated on the first real run (their spec asked for 97% unique messages; the real corpus measured
   65% of all messages and 82% of the substantive ones, because closings are legitimately repeated, so the gates were
   recalibrated).
6. **Mentions:** every mention in ground truth names a real row's key.

## Phases

0. Decisions (below).
1. **The world and its validator.** *Built (2026-10-05).* `spec/corpus/*.yaml`: 5 procedures, 32 causes, 41 manifestations, 67 actions,
   27 efficacy rows, 5 policies, 14 outcomes, 4 rep and 5 customer archetypes, with the planted site effect. `generate/corpus.py
   --validate-world` (code in `corpus_world.py`, tests in `tests/test_corpus_world.py`) checks references, that every cause can be
   fixed, every discriminator asked and every gate satisfied, that the control family has nothing to find, and that the shares sum;
   the shipped world passes with 0 errors and 0 warnings (it caught two causes with no way to open the call while it was written).
   Expression templates are left out of v1: the realiser is given a manifestation's label and the customer's archetype and
   chooses the words, and its output is validated against the plan. No data was touched.
2. **Bind and sample (Phase A).** *Built (2026-10-05).* `corpus.py --pool` reads the warehouse once (0.25 GB scanned) into
   `build/corpus/pool.ndjson.gz`; `--dry-run` samples plans against the world's targets with no warehouse; `--plan` matches each plan
   to a row (`generate/corpus_pool.py`, `corpus_plan.py`, `corpus_report.py`; tests in `tests/test_corpus_plan.py`). What it found, and
   what changed because of it:
   - **The walk works as designed.** At 2,000 conversations (2,216 with callbacks) every outcome is reached, a rep who asks learns
     the driver, and misdiagnosis follows the rep (methodical 17%, rushed 29%, scripted 22%, warm 25%) without dictating it. The
     dry run found the world too hard at first (31% for methodical reps): a customer closing an account was being modelled as
     unaware of their own reason. The fix is a `own` flag on a manifestation (the customer's own situation or act is noticed
     whatever their attentiveness); what varies is whether they say it.
   - **Targets were recalibrated, with reasons in the files.** The first guesses (policy compliance 0.70 to 0.85, favorability
     52/22/17/9) were made before the mechanics existed; they now follow the rep mix and the sampled outcomes. They catch breakage;
     they do not certify realism. One outcome the first dry run showed unreachable (`UNRESOLVED-KNOWN`, since a rep always acts on
     what they believe fixes the cause) was removed.
   - **Matching needs no compromise at this size.** 0 violations of the row's own facts (intent, site, authentication, rep archetype
     through the agent, transfer, handle time, a real fee or purchase) across seeds; at most 3 plans in 2,000 resampled; no row used
     twice. Rerunning is byte for byte identical.
   - **Callbacks are the one thing the pool limits.** 387 plans planned a callback within two weeks; 216 found a same-customer,
     same-intent, answered, untransferred next call to carry it, and the other 171 keep their outcome and lose the callback
     (recorded as unrealised). Follow-ups are plans in their own right, conditioned on their row.
   - **The corpus is a sample, not a replica,** and the difference is the point: against the warehouse it has 8% of calls hung up
     before an agent (50% in the warehouse) and 9% of answered calls transferred (68%), with authentication (79% vs 80%) and
     voice (78% vs 78%) kept. The warehouse's own flags carry no process, so none of them could constrain the story.
   - **Mechanics are in a file, not the code** (`spec/corpus/mechanics.yaml`): how many questions a rep asks, when a customer hangs
     up, what a callback window is. Each has a reason, and none is fitted to a result.
   - **The ground truth already carries the planted State at every step** (the rep's leading hypothesis and its confidence, per
     stage), for scoring discovered States later (see the process graph plan's State-Action note).
3. **Realise (Phase B).** *Built, and measured at 25 (2026-10-05).* `corpus.py --realise [--limit N] [--model haiku|sonnet] [--stub]`
   (`generate/corpus_text.py`, `corpus_check.py`; prompts and per-slot wording in `generate/prompts/`, the example's own folder as
   `eval/prompts/` is; tests in `tests/test_corpus_text.py`). The boundary is structural: Python computes the exact skeleton
   (who speaks, in what order, carrying which fact) and the model only fills numbered slots, so it cannot add a turn, resolve
   anything the plan does not, or say what was not brought up. A conversation that never reached an agent is a system line,
   written without a model. What the trial found:
   - **Both models work; Sonnet 5.5 reads better.** On the same 25 plans (24 reach an agent): Haiku 4.5 $0.07, Sonnet 5.5 $0.21.
     Sonnet's turns are longer (17 words against 12 for voice), more varied in voice, with notes in real agent shorthand
     ("Cust called re alert on acct activity"); Haiku repeats openings more ("Hi there, thanks for calling" 7 times in 25) and
     writes flatter. Unique messages 94% (Sonnet) and 85% (Haiku) of all, 97% and 95% of those of six words or more.
     **At the full size (about 2,200 conversations, 8% of them system lines) that is about $19 for Sonnet and $6 for Haiku;
     Sonnet is recommended** (decision 7). The Haiku run took about 20 seconds for 25 at the configured concurrency of 6; Sonnet
     was not timed.
   - **The checks earned their keep.** Reading the first 25 found what the checks did not yet catch, and each became a check or a
     fix: a verification written in anyway (which would have erased the planted breach: the lexicon is now broader, and for an
     unauthenticated caller any talk of verifying is rejected); a customer denying flatly a thing that was true and unnoticed
     (now a different slot, "has not noticed", not "no"); a general question that invented a topic that sounded like a cause
     (a `topics` list on the manifestation, one drawn per conversation); a customer's last line raising a new question
     (rejected); an email that stopped mid-sentence (a "stop mid-thought" closing style caused it, and was removed); and a
     "late fee" scenario written around a real overdraft fee (the world's wording is now "a fee").
   - **Retries are cheap and mostly unneeded:** 24 of 25 accepted first time with either model; the retry drops the register
     (a customer who interrupts was the cause of the one failure that survived a plain retry) and says what was wrong.
     Rejected text is kept in the sidecar for diagnosis.
   - **The planted breach shows.** A conversation planned as "unauthenticated caller served anyway" contains no verification, and
     the case note does not mention one; the agent's note records what the customer said and what was done, never the
     rep's guess at the cause, so a misdiagnosis is visible only in the actions, as it would be.
   - **Each conversation is a set of event objects** (`event_id`, `conversation_id`, `seq`, `ts`, `channel`, `role`,
     `agent_user_id`, `text`), time moving forward inside the row's span (the case note after it), the agent only on the row's own
     agent, a channel for the row's media (voice, chat, email, or a system line). The ground truth sidecar (`truth.ndjson.gz`)
     has per event the step it realises, its stage and belief, and the fee or merchant it mentions with the key. Outputs are in
     `build/corpus/sample*/` (events, truth, manifest, and `sample.txt`, the conversations as a person reads them under what
     really happened). Reruns are free (the model's answers are cached by request).
4. **The corpus.** *Built (2026-10-05).* `corpus.py --realise --model sonnet --out build/corpus/full` (2,219 plans: 2,000 plus
   their callbacks), and `--plan --n 20000 --plans build/corpus/scale/plans.ndjson.gz` then `--realise --stub --plans ...` for
   the scale set (21,161 conversations, 183,382 events, placeholder text; for timing the builder, not for reading). Results on
   Sonnet 5.5, **about $20 and 32 minutes** (concurrency 6): 2,214 of 2,219 conversations written (5 dropped for a customer's
   last line asking something new, a fee amount never stated, and one offer), 21,574 events, 2,070 accepted first time and 144
   after one regeneration. Messages 21,392, **73% unique** (84% of those of six words or more); words per message: case note 33,
   email 25, voice 15, chat 13. The most repeated lines are the natural ones ("no." 308 times, 3% of customer turns; "great,
   thanks. bye." 199; the greeting 170). What the full run found, beyond the 25:
   - **A skeleton bug, not a model fault.** Two actions that only check the account (the dispute window and the waiver
     history) were typed `verify`, so the skeleton told the agent to ask the customer to verify who they are and the customer
     to hand over details: conversations contained invented verification, which would have erased planted breaches or planted
     them where the plan had none. The checker had been waving it through for the same reason. They are now type `check`
     (agent says what they are checking; the customer acknowledges), and the verification check reads identity from the
     actions the authentication policies name, not from a type. About 190 conversations were regenerated ($1.85). After it,
     **0 of the 45 planted authentication breaches contain verification talk**.
   - **A first drop of 38 was biased, not random:** half were the planted-breach conversations, because the lexicons matched
     "account details" (an informational answer), "marked the activity as verified" (releasing a fraud hold) and a customer's
     "better rate" quoted in a case note. Lexicons narrowed (an offer is judged on what the agent said, or on "offered" and
     "waived" in a note), and the rerun was free (answers are cached by request). Lesson: **read what each check rejects before
     trusting a drop rate**; a rejection that correlates with a planted truth is a bias in the corpus.
   - **Planted rates survive realisation:** misdiagnosed 22.3%, serious breach 7.4%, retained 5.3% among the written
     conversations (the plan's own rates, over written ones). Every conversation's id is a real warehouse `conversation_id`, every
     agent is the row's own, and event ids are unique.
   - **Known weakness: a bare "no."** An open question ("what were you expecting?") sometimes gets a flat "no." because the
     slot for an absent clue says "says no". Not fixed: the plan decides the answer, the model chose the question's form. A
     slot wording that asks for a yes/no question would fix it, at the price of regenerating most of the corpus (about $15).
5. **Check and hand off.** *Built (2026-10-05).* `corpus.py --audit [--out build/corpus/full]` (`generate/corpus_audit.py`; tests in
   `tests/test_corpus_audit.py`) reads a written corpus back and trusts nothing the run said about itself, because a bug in the
   skeleton once passed every check made at generation time. It spends nothing and writes `audit.txt` beside the corpus; it
   exits 1 if a hard check or a gate fails. **Fourteen hard checks all pass on the full corpus:** every conversation is in the
   warehouse's calls and each plan's row is the warehouse's row, field for field; every plan has a truth record; events are
   contiguous, forward in time, inside the row's span, the row's own agent and channel; event ids are unique; every fee and
   merchant named (1,300 mentions) is a real row of that customer's (a callback names what its anchor was about, so the test is
   the customer's, not the one call's); 219 callbacks are the same customer, later, inside the window; no plan vocabulary or
   identifier in any text; every plan step realised, in order; no verification or offer the plan did not take; none of the 45
   planted authentication breaches carries verification talk. Recall is 1,335 of 1,337 for the converse (the plan verifies the
   caller and the text says so). **Four gates**, now thresholds in `spec/corpus/mechanics.yaml` (`gate_*`), set below the
   measured run: unique messages 73.2% of all (at least 65%) and 83.6% of those of six words or more (at least 80%), 0.2% dropped
   (at most 2%), 93.5% accepted first time (at least 85%). **Reproducible:** replanning and rerealising from the cache gives
   plans, events and truth identical to the byte. The audit found nothing wrong in the corpus; the two failures it first showed
   were bugs in the audit (hang-ups read as drops, a retention lexicon applied to every procedure), and a third apparent one
   (callbacks naming their anchor's merchant) was the check's scope, not the data. The audit's tests tamper with a stub corpus
   and check that the right check goes red.

## Where the corpus is kept

`build/` is gitignored, so the corpus is backed up in the project's bucket, **`gs://fennmoor-corpus`** (`corpus.py --push`, `--pull`;
`generate/corpus_store.py`, tests in `tests/test_corpus_store.py`): `full/` and `scale/` (events, manifest, and for `full` the audit
and the readable sample), `<set>/answer-key/` (the truth and the plans, under their own prefix so they can be restricted without touching the
corpus), and `inputs/` (the warehouse extract the plans are matched against, and the realiser's cached model answers: with them a
rerun is free and byte-identical, without them the corpus costs about $20 again). Uploaded 2026-10-05 and read back as the `qlsc` configuration's service account (it was granted access to the bucket; a call it may not
make fails, with no fallback to another identity). The bucket was **not public** when uploaded: only the project's owners, editors and
viewers could read it, and `open_text` falls back to `gcloud storage cat` as that service account when a plain https read is refused. Making it public is the owner's setting to change.

## Hand-off: what the text knowledge-graph builder is read against

[The next plan](2026-10-05-text-graph-construction.md) builds the first level of the State-Action graph from the **text**; this is what it may read, and what it is scored against.

**It reads** `build/corpus/full/events.ndjson.gz` (the event object above: 21,574 events in 2,214 conversations; voice 15,722,
chat 2,940, case notes 2,032, email 698, hang-up system lines 182) and the catalog; the estate's config will name the events
file (a `process_events` path, not yet in `estate.yaml`: a decision for that plan), and `src/qlsc/` reads only that, knowing
nothing of Fennmoor. **It must never read** `truth.ndjson.gz`, `plans.ndjson.gz`, `spec/corpus/` or the pool: they are the answer
key. A conversation that the checks dropped (5, listed in `manifest.json`) has a truth record and no events; a scorer skips it.
182 conversations are a one-line system record of a caller who hung up in the queue: they carry no process, and are the
control for "no agent, no steps".

**It is scored against `truth.ndjson.gz`**, one record per conversation (`cause`, `outcome`, `procedure`, `rep`, `site`,
`breaches`, `retained`, `recurrence`, the plan's `world`, and per event `step`, `stage`, `action`, `belief` and `mentions`). What
each planted truth lets a scorer ask, with its size in what was written:

| Truth | What the builder should find | Sidecar field | Size |
|---|---|---|---|
| 1. The closure code | text shows 350 closure calls coded `ACCT_MAINT` before 2026-06-02 are closures (and 65 coded `ACCT_CLOSE` after) | row `wrapup_code_name`, `intent` | 359 + 67 |
| 2. Elicitation has value | a fitting offer retains (98 of 98), a mismatched one rarely (37%), none never (0 of 123); asking the reason first helps | `retained`, `final_action`, `efficacy`, `save_attempted` | 416 retention conversations |
| 3. Right outcome, wrong process | a fix that skipped a serious gate: the text has no verification, the outcome says resolved | `breaches` (serious) | 94 (4.2%); 45 authentication |
| 4. The site effect | Manila transfers 17.0% against 4.3% and 6.3%, hangs up in the queue 12.9% against 5.5% and 5.7%, retains 17.9% against about 30% | `site`, row `was_transferred`, `outcome` | MNL 790, SPK 563, TUL 861 |
| 5. Recurrence | a false resolution brings a callback from the same customer within 14 days | `recurrence`, `follow_up_of` | 387 plans, 219 callbacks |
| 6. Outcomes only the text holds | retained against closed after a save attempt is in no warehouse table | `retained`, `save_attempted` | 416 (108 retained) |
| 7. The control | servicing is near-scripted, 97.9% resolved at first contact; repeated closings keep clustering honest | `procedure`, `outcome` | 389 |
| State | the rep's leading hypothesis and its confidence at each step, a misreading rep, a customer who does not say | `belief` per event, `misdiagnosed`, `believed_cause` | 22% misdiagnosed overall (methodical 17%, rushed 29%) |
| Action | what the rep did at each step, in order | `action`, `stage`, `step` per event | 21,392 events |
| Entities | the fee or merchant a conversation is about, linkable to `dim_merchant` and the fee rows | `mentions` | 1,300 |

**What a scorer must know about the corpus' limits.**
- It is a *sample chosen to carry the planted truths*, not a replica: its transfer and abandonment rates are not the warehouse's
  (the warehouse's flags are independent noise), and it says so in the dry-run's "against the warehouse" table.
- Its wording is Sonnet 5.5's, in the registers `styles.yaml` offers: 73% unique, closings repeat, and customers sometimes
  answer an open question with a bare "no." (3% of customer turns), which a clustering step will see as a very large cluster.
- The planted state is the rep's *belief*, which is sometimes wrong; "scoring a State" means scoring against `belief.leader`,
  and a misdiagnosed conversation is the case where the State the text supports and the cause differ.
- Resolution as a node versus an absorbing probability on a State is still undecided (the process graph plan); the sidecar
  records the outcome and `p` at each step, so either can be scored.
- `build/corpus/scale/` is the same plans with placeholder text, for timing the builder at ten times the size (21,161
  conversations, 183,382 events); it is not for reading and fails the diversity gates by construction.

## Decisions (accepted 2026-10-05; the measured findings above are why the binding changed)

1. **Warehouse-first binding.** *Accepted, as select to fit:* each plan is matched to a real `fct_calls` row, so nothing is
   refilled and every event joins to rows. The alternative is a free-standing corpus with invented ids, which loses the
   integration story. (The first draft bound the plan to the row's flags; measurement showed they are noise.)
2. **Channels in v1.** *Recommend voice, chat and the after-call case note.* Email, secure messages and fraud analyst notes
   come later if the first three work.
3. **The random wrap-up codes.** *Recommend leaving them alone.* Regenerating wrap-up codes from the plan would be a refill
   that could move the reference answers of the contact-center gold questions. The text-derived outcome becomes the better
   record, which is itself part of the demonstration. The one place the rows are coherent (closures) carries the planted
   truth.
4. **Account closure rows.** `dw_core.fct_account_closures` isn't tied to the calls. *Recommend not aligning it now:* "closed
   after a save attempt" stays a text-only fact. Aligning would be a second refill, worth doing only if the demo wants the
   text outcome and the balance in one query.
5. **Size.** *Recommend 2,000 realised and 20,000 stubbed.*
6. **The world's content.** The five procedures above are my draft from the estate's own intents, codes and dispositions;
   they are the thing most worth your edit before phase 1.

7. **The model for the realiser.** *Recommend Sonnet 5.5* (about $19 for the corpus, against $6 for Haiku 4.5): the text is what
   everything downstream reads, and the difference in naturalness and variety is visible at 25. The first 500 can be Haiku
   if you want to see the diversity gates calibrated cheaply.

## Risks

- **The rows don't fit most plans.** The flags are independent of intent and of each other, so a plan has to find a compatible row
  among 238,700; rare combinations (a short, unauthenticated, answered closure call at the BPO) may run out. The match rate is a
  number to watch, and a plan that can't be matched is resampled, never forced.
- **Leakage.** The realiser may write the plan's vocabulary into the text. The validators check for it, and the leak rate is
  reported.
- **A uniformly good rep.** Mitigated as theirs: behaviour is sampled from profiles, never improvised.
- **Cost and rate limits.** One LLM call per conversation, concurrent; a rate limiter was needed in the other project at this
  scale.
- **Closing-line repetition.** Real, and wanted, but it makes the diversity gates a judgement call.

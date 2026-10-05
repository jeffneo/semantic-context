# The process corpus: generating unstructured event objects for the Fennmoor estate

Status: proposed (2026-10-05). It is the first phase of [the business process graph](2026-10-03-business-process-graph.md)
as revised by your decisions of 2026-10-05: a separate `process` shard, built from **text**. Nothing is built.

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

## Binding the text to the estate: the warehouse is the skeleton

Fennmoor's contact center is in the warehouse already: `dw_contact_center.fct_calls` has, per conversation, `conversation_id`,
`cif_number`, `media_type`, `ivr_intent`, `ivr_auth_result`, `is_authenticated`, `queue_id`/`queue_name`, `site_id`,
`agent_user_id`, `talk_sec`, `hold_sec`, `handle_sec`, `was_transferred`, `is_abandoned`, `wrapup_code_name` and
`is_account_closure_call` (about 238,700 conversations from 2025-10-01 to 2026-06-29; voice 78%, chat 15%, email 4%,
callback 3%; three sites: Tulsa, Spokane and the Manila BPO). `salesforce.case` even carries `genesys_conversation_id__c`
and a free-text `description`.

**So the generator takes a conversation from the warehouse and writes the text that fits its facts.** A conversation's plan
is conditioned on the row: the intent picks the procedure; the authentication result, the transfer and abandonment flags
and the durations are hard constraints (an abandoned call ends with no resolution; a long hold appears as a hold; the number
of turns follows the talk time); the agent, queue and site pick the rep archetype and its site effect. Nothing in the
warehouse is refilled, and every event can be joined back to rows by `conversation_id`.

**One thing the rows won't give us.** Outside the closure calls, `wrapup_code_name` is drawn at random in the filler
(`fill.py`: 5% `ACCT_MAINT`, the rest uniform over the other codes), independent of the IVR intent. So the code can't be
treated as a constraint. Closure conversations are the exception: 6% by a stable hash, with the intent `CLOSE_ACCOUNT` and
the code `ACCT_MAINT` before 2026-06-02 and `ACCT_CLOSE` after (the planted finding about the code that changed).
Decision 3 below says what to do about the rest.

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
3. **Right outcome, wrong process.** A save that skipped authentication is a breach that the structured data calls a success.
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
and chat turns, plus the agent's after-call **case note**, which is exactly the Salesforce `description` field's content,
and which gives each conversation a second, shorter, differently worded account of the same event.

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

- **The demo corpus:** 2,000 conversations, realised by an LLM (about 12 events each, 24,000 events). Their 1,000 conversations
  realised concurrently; cost to be measured at 25 first, as they did.
- **The scale set:** 20,000 conversations, realised from templates (`--stub`) so it costs nothing, about 240,000 events. It
  is expected to fail the diversity gates by construction, and exists to time the builder at ten times the demo's size, with
  the text it will see in production (much of it repetitive).

## Validation (before anyone builds a graph from it)

1. **The world:** every cause reachable from some procedure, every procedure can end, every action has an efficacy row for
   the causes it can meet, every outcome reachable.
2. **The plan distributions**, by `--dry-run`: shares of procedures, causes, outcomes, breaches and recurrences against the
   targets above, before any spend.
3. **Consistency with the warehouse:** every event's `conversation_id` is in `fct_calls`; transfer, abandonment,
   authentication, site and agent agree; the number of events follows the durations.
4. **Realisation:** each plan step appears exactly once and in order; no unelicited clue mentioned; no plan identifier or
   jargon in the text; failures regenerate once, then hard-fail with a reason.
5. **Diversity gates**, calibrated on the first real run (their spec asked for 97% unique messages; the real corpus measured
   65% of all messages and 82% of the substantive ones, because closings are legitimately repeated, so the gates were
   recalibrated).
6. **Mentions:** every mention in ground truth names a real row's key.

## Phases

0. Decisions (below).
1. **The world and its validator.** `spec/corpus/*.yaml` for the five procedures; `--validate-world`. No data.
2. **Bind and sample (Phase A).** Read a sample of `fct_calls`, check the conditional distributions the plan relies on
   (BigQuery's login has lapsed, so this has not been done), sample plans, `--dry-run` to the targets.
3. **Realise (Phase B).** The realiser, the validators and the gates at 25 conversations, then 500.
4. **The corpus.** 2,000 realised, 20,000 stubbed, the sidecar, the manifest.
5. **Check and hand off.** The consistency checks, and a short note on what the text knowledge-graph builder must be scored
   against (the planted truths above), which is the next plan.

## Decisions needed

1. **Warehouse-first binding.** *Recommend yes:* the text is written to fit existing `fct_calls` rows, so nothing is refilled
   and every event joins to rows. The alternative is a free-standing corpus with invented ids, which loses the integration
   story.
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

## Risks

- **The rows constrain the story.** Durations, transfers and abandonment flags were generated independently, so some
  combinations are odd (a two-minute call that was transferred and held). The sampler must pick a coherent plan for each, or
  skip the row; the skip rate is a number to watch.
- **Leakage.** The realiser may write the plan's vocabulary into the text. The validators check for it, and the leak rate is
  reported.
- **A uniformly good rep.** Mitigated as theirs: behaviour is sampled from profiles, never improvised.
- **Cost and rate limits.** One LLM call per conversation, concurrent; a rate limiter was needed in the other project at this
  scale.
- **Closing-line repetition.** Real, and wanted, but it makes the diversity gates a judgement call.

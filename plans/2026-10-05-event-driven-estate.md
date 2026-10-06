# Generating the estate from events: a causal basis for process data

Status: proposed (2026-10-05), **to revisit later**. Nothing here is built, and nothing here is on the path of the process corpus
([plan](2026-10-05-process-corpus.md)), which goes ahead on the estate as it is.

## Why this is here

Measuring the warehouse for the process corpus showed it has the skeleton of a contact center and none of its behaviour (the
measurements are in that plan): every intent has the same transfer, abandonment and handle-time rates, there is no site effect,
CSAT is 3.0 for every outcome, fraud alert dispositions ignore the model score, and several tables are empty. You asked whether
the data generation itself was event-driven, and what we could have done differently.

**It was not.** `generate/fill.py`, driven by `spec/data.yaml`, generates each table from its own column rules, then lets the
models' SQL derive the rest (the plan in [fill the estate](2026-09-26-fill-the-estate.md)). The Genesys tables show it plainly:

- a conversation's start is uniform over the window;
- each has 2 to 5 participants in a fixed order (customer, ivr, acd, agent, agent), each with 1 to 4 segments in a fixed order
  (interact, hold, interact, wrapup);
- the intent and the authentication result are attributes drawn on their own; the wrap-up code is drawn with a closure rate and a
  switch date; the transfer flag comes from a segment's disconnect type, drawn on its own (`fct_calls` derives abandoned as "voice
  and no agent leg", transferred as "any segment disconnected by transfer", and durations from the segment types).

What the generator plants well are **findings**: dated facts such as the wrap-up code that changed on 2026-06-02, the column that
went null on 2026-04-20, the cents-versus-dollars pairs, the wrong joins. What it has no way to express is a **cause**: a fee that
makes a customer call, a call that ends in a closure, an alert that becomes a case. So the warehouse can support questions about
what is where, and cannot be a source for how the business behaves.

## What a better generation must not lose

The estate is used in many ways, and each is checked today. A new approach has to keep all of them (the checks are the fill plan's
five validations, plus the evaluations):

| Quality | Why it matters | Checked by |
|---|---|---|
| Referential integrity, id spaces and crosswalks | the virtual graph, memory and every join | fill validation 1 |
| The code values the log's queries filter on | the log replays: at least 90% of sampled queries return rows | validation 2 |
| Planted findings in the data (the wrap-up switch, the null column, the encodings) | questions about what changed | validation 3 |
| Traps that behave like traps (card and core ids overlap, `CC_ID` and `SITE_CD` share values) | the planted wrong joins | the fill plan, design item 6 |
| qlsc sees nothing changed (catalog version, `fingerprint.py`) | the tool's invariant | validation 4 |
| Seeded, byte-for-byte reproducible | CLAUDE.md | the generators |
| The 14 gold questions' reference answers | execution accuracy | `eval/answers.py` |
| The same columns and tags, so the entitlements hold | policy tags and row policies, tested with BigQuery as the oracle | `entitlements/setup.py` |
| The shape of a customer's context (rows per customer, per table) | memory, the virtual graph, the economics figures | `eval/memory.py`, `economics.py` |
| Synthetic PII only; the scale (about 41 million rows); skew (some customers busy, most not) | realism and cost | the fill plan |

## The idea they all share

**Make a canonical event log first, and treat each source system's tables as a projection of it.** An event is a small record:
when, which customer, what kind (fee assessed, alert raised, contact started, case closed, account closed), references to the
rows it concerns, and, hidden, its cause. Each source system has a *projector* that writes its own tables in its own
conventions, so one cause leaves consistent footprints in every system it touches. The models' SQL stays the only derivation.

Two things make this cheaper for us than it would be in general:

- **The causal part is already written.** The corpus world (`spec/corpus/*.yaml`) and its sampler are exactly a generator of
  causes, walks and outcomes. Rows and text would then be two projections of the same plan, so they agree by construction, and
  the contradictions the select-to-fit matching has to work around (an email handled in 67 minutes, an abandoned call with 27
  minutes of talk) disappear.
- **The contract with the models is concrete.** `int_calls_enriched` reads the customer participant's attributes (intent,
  authentication result, CIF), the segments' types and times (talk, hold, after-call), their disconnect types (transfer) and the
  final wrap-up code, and a call is abandoned when it is a voice call with no agent leg. `int_account_closures` reads the core
  account's `close_date` and `close_reason`, whose values (`FEES`, `COMPETITOR`, `MOVED`, `DECEASED`, `DORMANT`, `CUST_REQ`) are
  already the estate's words for the retention causes in the world. `fct_fraud_alerts` reads the alert's disposition and its case.

## The approaches

**1. Projection from the corpus plans, row first (the smallest step).** For every existing conversation, sample a plan
conditioned on what the row already fixes (intent, the agent's site and archetype, authentication, media, and the customer's
facts: fees, card purchases, alerts), and write the plan's behaviour into the raw rows: the segments and their disconnect types,
the hold and talk times, the wrap-up code (with the same noise a real center has), the note, the survey score, and the disposition
of any fraud alert linked to the call. Keys, counts, start times, customers, queues and everything outside the slice stay as they
are, so most of the qualities above hold untouched. Causes are tied to facts through the world's priors (a fee in the 60 days
before raises fee shock, a card purchase is needed for a dispute), so links exist without re-timing anything.
It does not give causal *timing*: a fee does not cause the call that follows it; the plan is conditioned on facts that happen to
precede it.

**2. Event-driven for the interaction slice, anchored on the existing facts.** Simulate each customer's timeline: contacts arise
from events (a fee, an alert, a dispute, an intention to leave), their outcomes feed back (a waiver sets `is_waived`; a closure
sets the account's `close_date` and `close_reason`; an alert becomes a case), and recurrence is a consequence rather than a
column. To keep the cost down, **do not generate the financial facts again**: keep every existing fee, purchase and balance as
given, and generate the contacts, alerts, disputes and closures as their consequences. This is the version that makes the
warehouse a real source of process data. It is also the largest change: counts per customer and their timing regenerate, so the
memory and economics figures move.

**3. A sibling dataset, nothing touched.** A new dataset of structured process events keyed by the existing conversation and
customer ids. Nothing in the estate moves, so no evaluation can regress; but `fct_calls` still says what it says, so there are two
truths. It is the structured source the process-graph plan lists as optional, and it can be built from the same plans.

**4. Per-column correlations in `data.yaml` (the fallback).** Make transfer depend on intent and site, CSAT on outcome, and so on.
Cheap, and enough to give a question like Q07 a shape. It cannot express a sequence or a reason, and every correlation is another
hand-tuned number, so it is the thing to do if only the aggregates matter.

| | 1 Projection | 2 Events, anchored | 3 Sibling | 4 Correlations |
|---|---|---|---|---|
| Fixes the independence | yes | yes | not in `fct_calls` | partly |
| Process sequences in the warehouse | within a call | across calls and systems | in the new tables | no |
| Cross-system consistency | per call | by construction | within the new tables | no |
| Risk to existing evaluations | the five gold questions that touch it | those, and customer contexts | none | the same five |
| Reuses the corpus world | yes | yes | yes | no |
| Effort | moderate | largest | small | small |

## Recommendation

Do **1**, behind a switch in `data.yaml` (`contact_center: independent | causal`) so the current estate stays reproducible and
every old result can be rerun. Then extend it toward **2** only where the demonstration needs it: first closures (the closure
reasons already match the causes, and the 3,849 closure rows today bear little relation to the 8,967 closure calls), then disputes
and fraud cases. Take **3** if a structured source is wanted before any of that. Leave **4** as the answer to "just give Q07 a
shape". The full customer-life simulation is not needed to get most of the value.

## What changes downstream

- **Gold questions.** Five of the fourteen read the affected tables: Q01 (closures by site, with costs), Q03 (pages before a call),
  Q07 (confirmed fraud share by channel), Q10 (satisfaction against agent tenure) and Q14 (closures by reason). Their reference
  answers change, so the evaluations that quote them are rerun (the comparison is about $25 and 15 minutes, the log accuracy run
  about $6 and an hour) and the numbers in the README, the example's README and `docs/design.md` updated. State the expected
  movement of each first, so a change is a prediction confirmed and not a surprise.
- **Log-derived questions.** How many of the 176 touch the slice is not known; counting them from the templates is the first,
  cheap step.
- **The process corpus** needs no select-to-fit matching, and the structured and the unstructured sources tell one story.

## Checks, beyond the five

- Every table outside the slice is row-hash identical before and after.
- Every table inside it keeps its schema, keys, tags and row policies, and (for projection) its row counts.
- **Recoverability:** the planted structure can be found from the structured tables alone, scored with the same planted truths as
  the corpus (the site effect in transfers, outcome by cause, CSAT by outcome, recurrence). If it cannot, the projector is wrong.
- A table of the five gold questions: old answer, predicted answer, new answer.
- The entitlement oracle suite, the log replay, `fingerprint.py`, and the size of a customer's context, all as today.

## Risks and unknowns

- **The data would encode our assumptions.** The planted dynamics become what the gold answers say, in a synthetic bank. That
  is acceptable and must be said; the noise (wrap-up codes, survey scores) stays so the warehouse is not cleaner than a real one.
- **Too clean favours the method.** If the process is easier to find in the warehouse than a real one would let it be, a result
  there overstates. Keep the corpus's difficulty (a rep who misreads, a customer who doesn't say).
- **Call density per customer** is part of the memory and economics tests, and has to be kept (8.9 calls a customer, 41% within a
  week of the last).
- **Unknown:** how much of `fill.py`'s Genesys handling can be reused as the base of the projector, and whether the fraud and
  Salesforce tables (the latter empty today) are in scope for the first cut.

## Decisions for when we revisit

1. Approach 1 alone, or 1 then 2.
2. Whether to align closures, disputes and fraud cases (rows in core banking, the card processor and the fraud platform), which
   moves more than the contact center.
3. A switch so the current estate stays reproducible (recommended), or replacing it.
4. Whether the shape of Q07 and Q10 is planted on purpose (for example, a higher confirmed-fraud share on card-not-present) as a
   data-spec decision, or left to fall out of the causes.
5. When: after the text knowledge graph and the process graph run on the estate as it is (recommended; they do not depend on this).

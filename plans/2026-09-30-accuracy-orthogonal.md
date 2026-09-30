# Accuracy from other directions: precedent, the data, and a fair ruler (2026-09-30)

Status: adopted (2026-09-30). The exploration below led to the method now in the tool: the request bank (`qlsc requests`), the precedent route, corrections, remembered answers and per-request measurement. It is reproduced by `examples/fennmoor-bank/eval/comparison/` (README there). The exploration's own code is at commit 1578fa6; what follows is its record.

Today `qlsc ask` answers 128 of the log's 176 questions by SQL (73%), gold 7 of 10 and graph-shaped 7 of 10
routed. Every lever tried since the compiler (definitions, the ontology's terms, decomposition, request
checks) moved the log score by one to three questions. This plan looks for a factor the pipeline doesn't
use yet, rather than a better version of one it does. Everything below is measured on the example, today,
unless marked as an estimate.

## What the 48 misses are

I read every SQL miss next to its reference query. Each is in exactly one row, by its main cause; the ids
are there so the reading can be checked.

| cause | n | questions |
|---|---|---|
| **The ruler or the question, not the answer** | 17 | |
| - the question's period is a day off: a Looker window `[d − 30, d)` written as "to d" | 5 | L4540fe70, L469ef255, L4b4d230a, L62fdbc12, L788679b6 |
| - the question's dates are wrong ("2026-07-01 to 2027-06-29") | 1 | Lefe10343 |
| - a `LIMIT` cuts through tied values, so the top N is arbitrary | 2 | L12addf1d, L66b70456 |
| - the reference outputs a column the question filters to one value (site SPK, period MAR-26) | 3 | L8ee70d9a, L97629e25, Lfba52c1e |
| - a sum over no rows: the reference's `COALESCE(…, 0)` against SQL's NULL | 1 | Led874c20 |
| - the question lost what the reference did (wallet type as "has a wallet"; a reversal filter the writer flagged as unstated) | 2 | L78f9c15c, L73371e91 |
| - the reference groups by a name that isn't unique (merchants), the answer by the merchant | 1 | L359c74a0 |
| - a stale reference: "the most recent churn scores" is v2's, written before the v3 cutover; today it's v3 | 2 | L986ea342, L7e87d30b |
| **Which source** | 8 | |
| - the data would decide: an empty table, a table that doesn't cover the period, a version that stopped | 4 | Lba494fec, La5545641, L7ac9ed17, L9bedbbe0 |
| - raw, staging or a derived table in place of the reference's, with no signal in the data | 4 | Lf24da50d, L6b9d5aa5, Ld63381a3, L6d29ff82 |
| **A dimension the cohort didn't reach** (line of business, segment, product line, agent name, branch) | 8 | L30b11cd6, L42795751, L5e63b8a9, L6505b2e4, L0b88eeab, L5bac0ee7, Ld5366f8d, Lb680ccfe |
| **The request can't say it, or said it wrong** (HAVING with OR, minutes, a boolean from a count, cohort windows, a filter put in a measure) | 7 | Lb79256f9, Le166be49, Le8c70805, La0ef9034, Le6d5789b, L8f767484, L754091da |
| **A column or value** ('ATM' is in two columns; a JSON key; a Computation's filter over-applied; the week) | 6 | L04bfef55, L78ae7fd3, L8bc8a936, L42c41a99, L9d80def1, Lccd8d6b4 |
| **The join type** (an outer join's null group) | 2 | La6c932d6, Ldfe49bfa |

About a third of the misses are the measurement. The answer key needs fixing before a gain of three is
worth claiming.

## Two directions that don't pay, measured today

- **More samples and a vote.** The two full runs (before and after Phase 2) agree on 127 answers. Either
  run is correct on 134, one more than the better run. The errors are systematic, not noise, so sampling
  more doesn't reach new answers. (It could still give a confidence signal, below.)
- **The asker's own history.** The reference's author has other queries on the reference's tables for
  81% of correct answers and 71% of wrong ones. Among the misses, their history argues against the table
  the answer used in 3 of 48. Many shapes are shared by several people: the churn authors ran both v2 and
  v3.

## The orthogonal factor: precedent

**The business mostly re-asks.**
- **People:** 99% of their jobs (49,337 of 49,866) ran a query shape that was run with more than one set
  of values.
- **All traffic:** 308,241 jobs over 1,100 successful shapes, 280 per shape.

A question a business user asks is, most of the time, a query someone already runs, with a different
date or code.

**`ask` doesn't use this, and the evaluation hides it.**
- **What `ask` does:** it treats every question as new. The log's queries are examples for writing a new
  query, never answers to reuse.
- **What the evaluation does:** it leaves each question's own shape out (rightly, for novel questions)
  and weights every shape the same. So it measures only the rare case, the novel shape, and scores the
  common case, the re-ask, not at all.

**The proposal: a precedent route.** Answer a re-ask by running the business's own query with the
question's values.
- **The shape is a template already.** The parser takes each literal out as a numbered slot, and load
  knows which filter each slot is and which values it was run with (`FILTERS.values`). Filling the slots
  gives back the business's exact query: its joins, its definitions, its Looker explore, its conventions
  (Monday weeks, reversals excluded or not).
- **A question bank finds the precedent.** The LLM writes one or two questions for each trusted shape,
  as `eval/log_questions.py` already does for 176 of them. Each is embedded with its shape and a line
  per slot ("the start date", "the site"). A question is matched to the bank's questions, question to
  question, rather than question to SQL, as the examples are today.
- **The route:** the closest bank question, above a similarity floor. The LLM then decides whether it's
  the same query with other values and returns the slots' values (typed, from the calendar and the
  column's values), or says it isn't. The shape's own text runs with those literals.
  - It comes after memory and before the compiled request: memory, precedent, compiled SQL, free Cypher,
    free SQL.
  - Only shapes production runs, or that were run repeatedly, and never one reading a sandbox or frozen
    table.
  - As the gateway allows, through the same checks as examples (`entitle.readable_shapes`).
- **What the answer says:** "the query the ops dashboard runs, 1,240 times in the window, with site SPK
  and the week of June 23".

**The same bank serves novel questions.** Its questions become the compiler's examples: the closest bank
questions, each with its shape's SQL, instead of the SQL closest to the question.
- **Today:** an example reads exactly the reference's tables for 94 of 176 questions. Those answer 85%
  right; the rest 59%.
- **Offline, with a bank of only the 176 eval questions** (the real bank would hold every trusted shape):
  question-to-question retrieval finds such an example for 103. For 16 of the 82 that today's examples
  miss, it finds one.
- **Estimate, not measured:** that correlation suggests about 4 more right answers. The eight "a dimension
  the cohort didn't reach" misses are partly the same problem.

**Measured by a second answer key: re-asked questions.**
- Shapes run with at least two different sets of values. The question is written from one held-out set,
  and the reference is that text's own result.
- The route may use the shape, but never the held-out text's literals.
- Reported beside the novel questions, and weighted by jobs, so the headline number describes what the
  business actually asks.

## The data as evidence and as verifier

The layer is built from the log and the catalog. The rows themselves are never consulted, and four
misses turn on them:
- **`fct_loan_payments` has no rows.** The history is in legacy `LN_PMT_HIST` (2024-03 to 2025-02). The
  answer ran on the empty table and returned nothing.
- **`EOM_BAL_SNAP` covers April and May 2026 only,** but was chosen for February to May. It's gold Q05's
  trap too.
- **Churn v2 is scored until 2026-05-14 and v3 from 2026-05-15,** so "the most recent" can only mean v3.
- **`fct_calls` starts 2025-10-01,** so "June, any year" needs the legacy CDRs.

**The proposal:**
- **A profile of each table the layer holds,** computed once at build and bounded by a byte budget:
  - its row count;
  - the range of its partition or date column;
  - each column's null share and distinct count;
  - the top values of short text columns;
  - the keys found in JSON columns (L78ae7fd3's `$.intent`).

  It's the same kind of physical fact as the catalog, not a designed model. A column behind a policy
  tag is never profiled for values.
- **Used before running:**
  - The request's options show each table's coverage and flag an empty one, as frozen tables are.
  - A period the fact table doesn't cover sends the request back once, as the request checks do now.
  - A quoted value the question names ('ATM', 'SPK') finds the columns that hold it, from the profile
    and the log's filter values.
- **Used after running:** the answer is checked against the data.
  - **The checks:** an empty answer, an all-NULL measure, or one row where groups were asked.
  - **When one fires:** the request goes back once with what was found. The answer has already run, so
    this costs no bytes.

## Fixing the ruler first

Each change is a test in `tests/test_match.py` first. Each only accepts an answer that is the same
table of facts; nothing loosens what counts as a wrong value.
- **The question writer resolves a Looker window to its real days** (sqlglot folds
  `DATE_ADD(DATE '2026-06-30', INTERVAL -30 DAY)`) and writes an exclusive end as the last day included.
  The six questions are rewritten, and their answers asked again.
- **A `LIMIT` over tied values:** the answer's rows must match the reference's above the tie, and come
  from the tie at the cut.
- **A compared column the question fixes to one value** (a filter on it, one value in the reference) may
  be absent from the answer.
- **A sum over no rows:** NULL and 0 are equal.
- **A question whose writer flagged an unstated filter** is rewritten to state it, or dropped.
- **Stale references** (a version that stopped before the question's "most recent") are rewritten to
  name the version.

The saved answers are rescored without asking again (`log_accuracy.py --report`), except the rewritten
questions. The run-to-run band is about ±3 on 176 (7 discordant answers between the two runs). A change
is reported with its discordant pairs, not just the net.

## Also, not orthogonal but measured

- **One hop of dimensions.** Eight misses need an attribute of a dimension that a cohort fact joins to by
  a trusted join, but that navigation didn't bring in (line of business is on `dim_queue`, product line
  on `dim_product`). The request's options add each cohort fact's trusted-join dimensions, their
  columns only, within a column budget.
- **The request language, measured by the log.**
  - **The test:** every trusted shape is turned into a request and compiled, and its result is compared
    with the shape's own.
  - **What it gives:** the share reproduced is how much of what the business computes the compiler can
    express, and the failures rank the missing features by how many queries need them (HAVING with OR,
    arithmetic on a measure, a boolean dimension from a comparison, a date difference, month of year).
  - **What it replaces:** the eval's seven misses of this kind, as a way to pick the next compiler
    features.

## Later: learning from use

`qlsc converse` already records every ask as a step, with the user's rating and any correction. An ask
rated right becomes a bank entry, and a corrected one becomes the correction's. The bank then grows with
use, so the system gets better the more it's used, which nothing in the build can do.

It can be tested before anyone uses it. The references of half the questions are fed in as an analyst's
corrections, and the other half is measured.

## The plan

**Phase 0: the ruler.** Small; no LLM calls, except re-asking the rewritten questions.
- **Checked by:** a corrected baseline for all three answer keys, with the band.

**Phase 1: precedent** (the decision below).
- **The work:**
  - the question bank (`qlsc bank`: its questions, their embeddings, and each shape's slots);
  - the precedent route in `ask`;
  - the re-asked answer key (`eval/reask_questions.py`, `eval/reask_accuracy.py`).
- **Checked by:** re-asked accuracy (target 90%+, since the business's own query does the work), and the
  novel set unchanged or better.

**Phase 2: the bank's questions as the compiler's examples.**
- **Checked by:** the novel set, gold and graph-shaped. Gold matters most here: its questions are
  hand-written, so a gain there isn't the bank's style matching the eval's.

**Phase 3: the data** (the decision below).
- **The work:** `qlsc profile`, coverage and values in the request's options, and the result checks.
- **Checked by:** the four "the data would decide" misses, gold Q05, and the full set.

**Phase 4: one hop of dimensions, and the request language measured by the log.**
- **The work:** the dimensions first. Then the top features the compile-back test finds, one at a time,
  each with a quick test.

Every step gets a quick test (`eval/qdd.py`) first. The full runs are about an hour each, and I'll ask
before each one.

**A rough expectation, to be measured, not promised:**
- **The novel set:** from 128 to about 140 when the ruler is fair. Then a few questions each from the
  data, the dimensions and the request language. Somewhere near 150 (85%) is plausible.
- **Re-asked questions:** they would be answered by the business's own queries, which is where most of
  the real traffic is.

## Decisions

1. **The precedent route:** answering a re-ask by running the business's own query with the question's
   values. It's a new route, with the business's query as the answer's provenance.
2. **The data's physical facts as evidence** (row counts, coverage, null shares, distinct counts, top
   values of short text columns, JSON keys). It extends "the catalog's physical facts". Values of
   tagged columns are never profiled.
3. **The ruler's changes, and reporting novel and re-asked questions separately,** with a usage-weighted
   number. This changes the headline numbers in the README.
4. **The bank's questions written by the LLM from every trusted shape.**
   - **Cost:** about 1,100 query-model calls, about $5 once, and cached.
   - **Style:** a different prompt from the eval's question writer, so the bank's phrasing doesn't match
     the eval's.

## Risks

- **The bank and the eval come from one family of writers.** A gain on the log's questions could be
  style. Gold (hand-written) and a different bank prompt are the checks.
- **Deciding "same query, other values" wrongly** gives a confident, well-provenanced wrong answer. The
  similarity floor and the LLM's check start strict, and the re-asked key measures the false matches (a
  question whose shape wasn't the match).
- **Profiles cost bytes on a real estate.** A byte budget, sampling for large tables, and a dry-run
  estimate before the pass.
- **Overfitting to the example.** Every rule above comes from a kind of miss, not a particular question.
  The tool still knows nothing about any estate (`tests/test_boundary.py`).

## The tests (2026-09-30)

The user asked for each idea to be tested on its own before any change to the method, quick and
directional (a QDD each), in parallel. Code: `examples/fennmoor-bank/eval/explore*.py`, prompts in
`eval/prompts/explore_*.md`; results in `<work>/qdd/explore/` (`report.md` side by side).

**The probe set** (`eval/explore_probe.yaml`), 90 questions answered the same way by every test:
- the 10 scored gold questions;
- the 48 SQL misses of the last full run, each tagged with its cause from the table above (ruler 17,
  source 8, dimension 8, request 7, column 6, join 2);
- every fourth of the 128 it got right (32), to catch a test that breaks what works.

The log questions keep their leave-one-out (their own shape is never an example). The ruler is
`match.py`'s, unchanged, so the 17 "ruler" misses can only be matched by accident, or by knowing
the reference's conventions.

**The noise:** the baseline twice, each with its own cache: 43 and 45 of 90. Two questions either way
is noise.

### What each test did

1. **Opus 5.5 and Fable 5.1, with reasoning.**
   - **The swap:** the query model only (`llm.query_model`), adaptive thinking at high effort (Opus 5.5
     defaults to medium), for every query-model call: the request, its check retry, free SQL.
   - **The control:** Sonnet 5.5 with the same reasoning, which separates the model from the reasoning.
   - **No refusal fallback,** so a refusal would count as a failure. None happened.
2. **Iterated context from the graph** (`explore_agent.py`).
   - **The loop:** the compiled request becomes a loop of up to twelve turns, with the same model and
     thinking as the baseline. It starts from the baseline's own prompt, so submitting at once is the
     baseline's answer.
   - **Tools over the semantic layer only** (the rows are a separate factor):
     - `find_columns`: embedding search over 3,307 column documents (column, type, Variable, area, the
       log's filter values);
     - `describe_table`: columns, liveness, write days, readers, trusted joins, which opens the table;
     - `find_computations` and `similar_queries`;
     - `check_request`: compiles a draft, with the dry run and the request checks' notes, no rows;
     - `submit`.
3. **The confirmation loop** (`explore_confirm.py`).
   - **The true failure mode:** a wrong answer the consumer accepts ("silent wrong"). A wrong first
     answer that is caught and converges within two corrections is recovered. A right answer wrongly
     rejected and then broken is a failure too.
   - **What the answer shows:**
     - its assumptions, from the typed request: measures and their definitions, groupings and grains,
       filters, period, having, order, and the outer joins that keep unmatched rows;
     - a preview of eight rows and the total.
   - **The personas:**
     - *agent*: an automated agent that asked for a task. It knows only the question, and reads the
       assumptions, the SQL and the preview.
     - *analyst*: a copilot user who knows what they meant. They get an intent card written from the
       reference in business words (no table or column names, no numbers), and read the assumptions and
       the preview.
     - *terse*: the same person, busy: at most one short symptom, no fix.
   - **A leak guard:** the reference's identifiers are masked out of feedback. This fired 56 times for
     the agent persona, which quotes the answer's own SQL (the same names); twice for the analyst; never
     for the terse user.
   - **Found while building it:** the compiler's week rule overrode a correct correction (Monday weeks
     reset after the model, twice). The rule defers only to the question's own words, so a correction
     now becomes part of the question, as it would in a conversation. Any retry loop must treat a
     consumer's clarification as the question.
4. **Precedent, as Request nodes** (`explore_precedent.py`).
   - **A small bank for the probe set:** 332 shapes. For each question: the 8 closest by SQL (as
     examples are found), and the 5 most-run over the reference's tables, standing in for a full bank.
     Plus one round of successors from the whole log.
   - **The Request nodes:** 381 `(:Request)-[:FROM]->(:QueryShape)`, with a question Haiku wrote (a
     different writer and prompt from the eval's), the typed request compiled back from the shape's SQL,
     and `verified` when that request reproduces the shape's own result: **171 of 381 (45%)**.
   - **Between Requests:**
     - `SUCCEEDS`: 2, one of them the churn cutover (v2 → v3, one day apart, the same people), one a
       false positive (a v2 query that dropped a join);
     - `VARIANT_OF`: 19.
   - **Four variants:**
     - *precedent*: the closest verified Requests (a successor followed, the closest one's variants
       beside it) as examples for the compiled request. Never the question's own shape.
     - *precedent-reask*: the same, where the log ran the question's own query with other values too (49
       questions). The precedent may be that query, from another of its texts, never the question's own
       text.
     - *precedent-route*: the route as planned. The business's own query, with only its literals set from
       the question by the query model; run when the parser's fingerprint says it's still that shape,
       else the compiled request. Given the question's own query.
     - *precedent-route-retrieved*: the route choosing among the three closest Requests by question
       similarity. *precedent-route-novel*: the same, with the question's own query out of reach.

### What they found

| test | right, of 90 | misses recovered (of 48) | baseline's right broken (of 43) | cost |
|---|---|---|---|---|
| baseline, two samples | 43, 45 | 4, 6 | 0 | $1.16 |
| Sonnet 5.5, reasoning | 45 | 7 | 1 (gold Q05) | $1.76 |
| Opus 5.5, reasoning | 46 | 7 | 1 (gold Q14) | $3.47 |
| Fable 5.1, reasoning | 45 | 6 | 0 | $9.22 |
| iterated graph context | 44 | 5 | 1 | about $4 |
| precedent as examples | 46 | 6 | 0 | small |
| confirmation: agent | 44 | 7 | 2 | small |
| confirmation: analyst | 53 | 15 | 2 | small |
| confirmation: terse | 55 | 15 | 1 | small |

The re-asked questions (49, whose query the log also ran with other values; the baseline gets 22):

| test | right, of 49 |
|---|---|
| baseline | 22 (24 in its second sample) |
| precedent as examples | 26 |
| **precedent route, given the question's own query** | **46** |
| **precedent route, retrieving it** | **44** (43 of them through the question's own query, which it chose for 44) |
| precedent route, own query out of reach (all 90) | 36 of 90, against 43: it broke 8 |

**1. A stronger model, or reasoning, doesn't move it.** Opus 5.5 and Fable 5.1 at high effort land
within the noise of the baseline. So does Sonnet with reasoning on. The misses aren't a lack of thinking.
This agrees with the two full runs' systematic errors.

**2. Iterated context finds the information, and still misses.** The agent explored on 42 of 90
questions and nearly every miss, and usually found the right piece: line of business on `dim_queue`,
the balance on `customer_360`, churn v3. It then answered a slightly different question:
- "flagged high risk" as a score threshold, not `risk_band`;
- the site from the call, not the queue;
- a branch by name where names aren't unique.

The remaining misses are mostly ambiguity. More context resolves what the layer knows, not what the
asker meant.

**3. A consumer who knows the intent is the biggest lever for novel questions.**
- **With intent:** the analyst and terse personas take 43 right to 53 and 55, recovering 15 misses
  each, including ruler cases whose conventions the asker knows (an exclusive period end).
- **Without intent:** the automated agent adds one.
- **The true failure mode stays large.** Wrong answers accepted: 30 for the agent persona, 17 for the
  analyst, 15 for the terse user. The first answer's stated assumptions aren't enough for a reviewer
  to see what's wrong.
- **The loop has a cost.** 15 to 19 answers were never accepted within two corrections: the
  consumer's expectation and the request language don't meet (a derived boolean, minutes, a MAX-date
  filter).

**4. Precedent is decisive for re-asks, and only as a route.**
- **As examples,** the business's own query is a hint the request writer half-uses: +4 on re-asks, +3
  on the probe.
- **As the route** (the business's own SQL with the question's values, checked by its fingerprint), it
  answers 44 to 46 of 49 re-asks where the baseline answers 22. It even gets the ruler cases, because
  the business's query carries the reference's conventions.
- **Retrieval by question similarity found the question's own query, and chose it, for 44 of 49.**
- **Its failure is a false match.** With the own query out of reach, the slot filler still called 16
  other queries "the same query". Only 4 were right, where the baseline had 11, and similarity scores
  don't separate the two cases (0.80 to 0.91 taken, up to 0.94 not taken).

  **The route needs a better "same question?" decision before it can be trusted.** Candidates:
  - a stricter judge;
  - comparing the question's asked outputs with the query's outputs;
  - asking the consumer, which ties to finding 3.

**5. The compile-back test works as a measure of the request language.** On this bank, a typed request
reproduces 45% of the shapes. The rest are the request language's gaps (a MAX subquery, derived
booleans, HAVING with OR) or verification noise (ties, relative dates). Worth running on the whole log
to rank the compiler's missing features.

**Costs:** the probe set cost about $1.20 on the baseline model. Fable cost 8 times that, and Opus 3
times, for no gain.

### What this suggests (for the decisions)

- **Keep Sonnet 5.5 as the query model.** Reasoning and larger models aren't the unlock here.
- **Build the precedent route for re-asks,** with the "same question?" decision as its central,
  measured piece. Build the re-asked answer key with it, and report accuracy weighted by use. Most of
  the business's traffic is re-asks.
- **Make answers state their assumptions and accept corrections.** The consumer's corrections must
  reach every deterministic rule (the week rule showed why). Then measure silent-wrong as the headline
  failure, beside accuracy.
- **Don't pursue** iterated graph context or bigger models for accuracy on their own. The agent's tools
  are still worth keeping as the way a correction gets resolved ("I meant by line of business" needs
  `find_columns`).
- **Open question for the user** (answered, next section): whether "silent wrong" becomes a reported
  number, and which consumer to design for.

## Measurement, and a consumer that knows its process (2026-09-30, second round)

The user's answers to the open questions:

- **The consumer is an AI agent that knows the state of the business process it is in.** Not a
  person, and not an agent that knows only its question.
- **Failure modes, for the service:**
  - a wrong answer the consumer accepts;
  - an exchange that doesn't converge: no right answer, or a right one only after the exchange has
    cost more than the service-level targets allow. Back-and-forth without end is not success.
- **Not the service's failure:** a right answer the consumer rejects. Whatever follows (another
  answer accepted, or the process failing), the service delivered.
- **The ideal:** right in one or two interactions.
- **Tokens and latency are measured for every request,** however it is answered, from the request to
  the final answer.

### The measurement component (`src/qlsc/meter.py`)

- **What is measured.** Every request, whichever route answers it:
  - the seconds from the request to its final answer;
  - LLM tokens: input (cache reads and writes included) plus output, thinking included;
  - beside them: LLM calls (live and cached), cost at list price, warehouse queries and bytes billed,
    texts embedded, seconds waiting out rate limits, and the service's answers in the exchange.
- **How.** `LLM.call`, `Embedder.embed` and `Warehouse.run`/`dry_run` report to every meter open in
  their thread. A context variable keeps parallel requests apart, and a meter inside another reports
  to both.
- **The consumer's share.** `meter.aside(consumer)` sets it apart: the time and tokens a consumer
  spends reading an answer and writing its correction are its own, not the service's.
- **Targets.** A ceiling on any measured quantity, `service.targets` in defaults.yaml.
  - Tokens and seconds for now: 20,000 tokens and 30 s.
  - Provisional: about three of the baseline's one-shot answers (median about 6,600 tokens and 5 s),
    so two or three answers fit and an open-ended exchange doesn't.
  - `meter.check`, `within` and `summary` give per-target verdicts, percentiles and the share within
    target.
- **Where it shows.** `qlsc ask` ends with a `MEASURED` line against the targets. Every explore run
  records each answer's measurement.
- **Delivered.** An answer counts as delivered when it is right *and* within the targets. For an
  exchange, that is the first right answer, with what the exchange had cost the service by then.
- **Fresh runs.** A run measured this way has its own LLM cache (`--fresh=TAG`), so every call is
  live. A call answered from the cache costs nothing and takes no time, so an unfresh run's numbers
  aren't a measurement.
  - A first attempt shared one fresh cache across runs. The stateful consumer's first answers then
    came from the baseline's cache and cost nothing. They were caught (the cached-call count) and
    rerun, each run with its own cache.
- **Caveats on latency.** Runs went four questions at a time, up to eight runs at once: latency is
  measured under load. No rate-limit waits were recorded. Question embeddings and BigQuery results
  were mostly cached from earlier runs, which shortens latency a little. The 30 s target is well
  clear of both effects.

### The stateful consumer

- **Its state** (`explore_confirm.py prep states`) is written once per question, from the reference
  query, in the business's words, with no table or column names:
  - the process and its goal;
  - the step, and what it needs the data for;
  - what the process has settled (the period, the definitions it uses, the population);
  - the next step, and what that step needs from the result (one row per what, which figures, which
    rows are kept).

  Identifiers are masked; none needed it. An example (Q02): "Churn risk is the current version 3
  score as of its latest score date, not the retired version 2 score"; "one row per customer
  segment".
- **The exchange.**
  - The consumer reads each answer's assumptions, SQL and preview against its state. It accepts, or
    says what is wrong in its process's terms.
  - At most four answers.
  - A correction adds everything said so far to the question, and the previous request plus the
    feedback to the prompt.
  - The consumer's corrections are masked of the reference's identifiers. This is conservative: of
    the 143 masked names in the state-context run, 133 were in the answer's own SQL.
- **Three variants:**
  - `state`: the agent asks its bare question.
  - `state --retrace`: each correction is navigated again, not only compiled again.
  - `state-context --retrace`: the agent writes its own first request, the question plus what from
    its state the service needs.

### Results (fresh, measured; 90 questions)

Delivered = right within the targets. Tokens and seconds are the service's share: median / p90 over
the whole exchange.

| test | right (of 90) | delivered | tokens | seconds | $ |
|---|---|---|---|---|---|
| baseline | 44 | 44 | 6,643 / 9,875 | 5 / 9 | 1.55 |
| Sonnet 5.5, reasoning (high) | 46 | 46 | 6,863 / 10,683 | 6 / 13 | 1.77 |
| Opus 5.5, reasoning (high) | 46 | 46 | 6,839 / 10,589 | 9 / 18 | 3.52 |
| Fable 5.1, reasoning (high) | 45 | 43 | 6,998 / 10,752 | 14 / 26 | 9.50 |
| iterated graph context (agent) | 44 | 28 | 20,637 / 48,565 | 13 / 26 | 3.56 |
| stateful consumer, bare question | 62 | 57 | 15,421 / 40,175 | 13 / 33 | 4.67 |
| the same, corrections re-navigated | 65 | 58 | 16,265 / 40,274 | 11 / 37 | 4.73 |
| stateful consumer, its own request | 71 | 64 | 18,621 / 43,407 | 15 / 38 | 4.86 |
| precedent route, re-asks (49) | 44 of 49 | 44 of 49 | 786 / 1,532 | 4 / 7 | 0.25 |
| precedent route, own query out of reach | 37 | 37 | 8,022 / 11,705 | 8 / 12 | 1.66 |

The $ column includes the consumer's own calls in the three consumer runs (about $1 of each).

The stateful runs' outcomes, for the service:

| outcome | bare | re-navigated | own request |
|---|---|---|---|
| right at once, accepted | 12 | 12 | 29 |
| right after corrections, accepted | 7 | 10 | 1 |
| right, rejected by the consumer (theirs) | 38 | 36 | 34 |
| **delivered** | **57** | **58** | **64** |
| right, but past the targets (not converged) | 5 | 7 | 7 |
| no right answer, never accepted (not converged) | 11 | 8 | 8 |
| wrong, accepted (silent wrong) | 17 | 17 | 11 |
| first right answer: at the 1st / 2nd / 3rd+ | 44 / 16 / 2 | 43 / 19 / 3 | 61 / 6 / 4 |

What this says:

1. **Context in the request is the biggest lever measured.** The same pipeline, given the agent's
   request (the question plus the period, definitions and shape its state holds), answers 61 of 90
   right at once, against 44. Every cause gains, the ruler misses too (8 of 17 delivered), because the
   context carries the reference's conventions. With the context in the first request, corrections
   add little: 3 more delivered.
2. **Corrections work when the first request is bare.** 44 right at once; 16 to 19 more on the second
   answer; almost nothing after. Re-navigating a correction helps slightly (+3 second-answer
   recoveries), within noise.
3. **The two-interaction ideal and the targets agree.** Every delivered answer came at the first or
   second answer. None of the 9 right third or fourth answers was within 20,000 tokens.
4. **The consumer is the weak judge, both ways.** It rejects a right answer 34 to 38 times in 90 (over
   the ruler's leniency, or details its state fixes that the ruler doesn't score: rounding, ordering,
   a proxy column). It accepts a wrong one 11 to 17 times. Rejected right answers aren't the service's
   failure, but they run the exchange on: they are about half the exchanges past the token target
   (17 of 39, 18 of 38, 26 of 44).
5. **The median exchange is past the token target** (15 to 19 thousand, p90 about 40 thousand).
   Measured to the first right answer, the median is about 7,000. About half the overrun is the
   consumer continuing after a right answer, the rest exchanges that never converge.
6. **Reasoning and larger models cost latency, not tokens, and don't help.** Thinking adds few tokens
   here; Opus doubles latency and Fable triples it (6 of Fable's 90 past 30 s).
7. **The agent (iterated graph context) spends three times the tokens for the same answers.** 48 of
   its 90 answers are past the token target, so it delivers 28 where the baseline delivers 44.
8. **The precedent route is the cheapest route by far:** under 1,000 tokens and 4 s, because it fills
   slots in the business's SQL instead of writing a request.

**Caveat.** The state is written from the reference query, so it is the best a process-aware agent
could know: an upper bound on this consumer, as the intent cards were for the analyst.

### Iterated graph context, step by step (explore_agent.py)

1. **Navigate, as the baseline does** (`navigate.trace`):
   - embed the question and find the closest Semantic nodes;
   - walk down to the level-1 groups, and from them to the cohort of tables;
   - add the log's closest queries (never the question's own) and the tables they read, then the
     joins between them.
2. **The baseline's options** (`navigate.request_options`): the prompt the baseline's single call
   gets.
   - The cohort's tables and columns, with the log's filter values, and which are frozen.
   - The trusted joins.
   - The closest Computations.
   - The example SQL.
3. **The loop:** Sonnet 5.5, the same thinking setting as the baseline, prompt caching, at most 12
   model turns. The system prompt says to submit at once when the options hold what the question
   asks, and otherwise to look things up. The tools:
   - `find_columns(words)`: the 12 columns closest to the words, over 3,307 column documents (table,
     column, type, Variable, business area, filter values), with liveness, and whether the column is
     already in the options.
   - `describe_table(table)`: from the Table node, its columns and Variables, whether it is frozen or
     a sandbox, its write days, how many principals read it and whether production does, and its
     trusted joins. The table is then added to the options the compiler may use.
   - `find_computations(words)`: the closest trusted Computations. They and their tables are added
     to the options.
   - `similar_queries(words)`: the log's four closest queries, with their tables and run counts.
   - `check_request(draft)`: compile a draft against the options as they stand. It returns the SQL
     or why it doesn't compile, the warehouse's dry-run verdict, and the request checks' notes against
     the question's words. **It returns no rows.**
   - `submit(request)`.
4. **After submit, as the baseline:** the week rule, compile, dry run, run. A request that doesn't
   compile falls back to free SQL.

**What it did.**
- 5 questions submitted at once.
- 42 called `check_request` once and submitted: the baseline's answer, checked.
- About 43 explored, mostly `describe_table` (112 calls) and `find_columns` (46).
- In the first run, 34 of its 90 final SQLs were identical to the baseline's.

**Why it doesn't pay:**
- **The information it gathers is the information the baseline already had,** one hop further. It
  finds the candidates (line of business on `dim_queue`, the v3 churn table), and the misses are
  choices between plausible candidates that nothing in the layer settles. The state-context run shows
  what settles them: the consumer's context, and the same pipeline then gets 61.
- **It can't see the data.** `check_request` has no rows, so an empty or implausible result (the
  "source" misses: a table that stopped being written, "no rows") looks like success.
- **It is confident.** The instruction to submit when the options suffice meets a model that thinks
  they do.

**If it's worth another test:**
- a `check_request` that returns the row count and a preview (the plan's "data as verifier"), aimed
  at the source misses;
- the tools used only to resolve a consumer's correction, where the words name something the options
  don't have.

### What this suggests

- **Design the request for context.** An agent in a process knows the period, definitions and shape
  it needs. The service should ask for them and use them: a request with an optional context
  (settled definitions, period, population, the shape the next step takes), passed to navigation and
  to the compiler.
  - This is the largest measured gain: +17 at once, within the targets.
  - It needs no model change.
- **Keep the correction loop, capped by the targets.** Two answers is the budget. Corrections reach
  navigation and every rule.
- **Report, for every method:** delivered (right within the targets), silent wrong, not converged, and
  tokens and seconds (median and p90). Rejected-right answers are reported, not counted against the
  service.
- **Put precedent first for re-asks.** It is right 44 of 49 at a tenth of the tokens, still pending
  the "same question?" decision.
- **Don't pursue** bigger models or iterated graph context: no gain, and they are past the targets
  more often.

## The shape (2026-09-30, third round)

The user's direction: design for AI agent consumers. **Precedent plus the consumer's stated context is
the best combination so far, and interactive retries must be supported.**

- **Tokens and seconds are per request.** A request is a question and its corrections, up to its final
  answer. They count the service's LLM tokens and processing time over every answer in the exchange.
  They don't count the consuming agent's own tokens and time, spent reading answers and writing
  corrections.

### Remembered answers, in memory (built)

A handled request goes in the Context Memory model as it already stands (converse.py), with no new
labels.

- **The request is a Task, each answer an `ask` Step.**
- **The step keeps its answer whole** (up to `memory.answer_rows`), until the first table it read is
  written again: `holds_until`, by the table's write cadence, the rule memory's facts already follow.
- **The same request again is answered from memory while that holds.** "The same" means the same
  words, day, query model and reader grants (`asked`).
  - The new step is `-[:SAME_AS]->` the one that answered, with no LLM or warehouse call.
  - Private to its owner, as every step is.
- **The asker's verdict is a Fact about the step, from their message:**
  - `accept()`: accepted;
  - `correct(question, feedback)`: rejected, with what was wrong, and the request asked again in the
    same Task with the correction in the question.
  - A rejected answer is never given again, directly or through a step that repeated it.
- **Checked live:**
  - the first ask: 10.9 s, 7,281 tokens;
  - the same again: 0.1 s, no LLM or warehouse call;
  - after a rejection, the rejected answer isn't reused.

**Next, with the precedent route:**
- An accepted answer is a verified precedent. The route should look in two places: the log's Request
  nodes (the business's, shared) and the asker's accepted answers in memory (private, recent).
- A correction's SAME_AS and SUCCEEDS paths are the Request -> Request relationships.
- The Request nodes are still experimental, in the layer database only; a rebuild wipes them.

### The state representation

- **What it is.** One card per question, written once by Sonnet 5.5 from the question and its
  reference query, in the business's words. Prompts: `eval/prompts/explore_state*.md`.
- **Its fields:**
  - `process`: the business process and its goal;
  - `step`: the step the agent is on, and what it needs the data for;
  - `established`: what the process has settled: the period, the definitions, the population;
  - `next_step`: the step that uses the result;
  - `needs`: the result's shape: one row per what, the figures, which rows are kept, the order.
- **The agent's own first request.** `explore_state_request.md` asks the agent to add what from its
  state the service needs. Examples are in the session's reply; the states are in
  `<work>/qdd/explore/states.json`.
- **Caveat: the cards are generous.** Written from the reference query, they carry some of its
  physical choices, in business words:
  - the source ("the contact centre's pre-aggregated monthly summary", "the customer 360 view");
  - the join semantics ("only customers in both the customer master and the 360 view").

  That is the upper bound of a process-aware agent. A process designed around the business's assets
  knows some of this, but not all of it.

### The request bank across the log (built, experimental)

`eval/explore_bank.py` replaces the precedent test's small bank.

**Which shapes:**
- The candidates are every successful SELECT shape from the log that isn't a dbt test and reads no
  sandbox or frozen table: 466.
- Haiku judged 364 of them business. The 102 left out are freshness checks, data-quality checks,
  metadata lookups and staging row counts.

**The requests:** three per business shape, 1,092 in all:
- two questions, by different roles;
- one task: a process step, as an agent carrying out that process would ask for it.
- The requests' answer is the shape's own SQL.

**The model:**
- `(:Request {text, kind, who, bank: 'shapes', embedding})-[:FROM]->(:QueryShape)`, with the vector
  index `request_embedding`.
- `(:QueryShape)-[:SUCCEEDS]->(:QueryShape)` (2) and `(:QueryShape)-[:VARIANT_OF]->(:QueryShape)`
  (550): shape-level, so a Request reaches another through its shape.

### Probe: states without source or join hints

The user's rule: the consumer knows its process, not the business's data, so it never says how to get
the data.

- `prep states-plain` (`explore_state_plain.md`) writes states with no source, extract or system and
  no matching or joins. The other fields are as before: definitions, period, population in business
  terms, and the result's shape.
- The run: `state-context --retrace --cards=states-plain`, fresh and measured, 90 questions, $4.87.

| | baseline | generous states | plain states |
|---|---|---|---|
| right at the first answer | 44 | 61 | 51 |
| delivered (right within the targets) | 44 | 64 | 56 |
| misses delivered (of 48) | 5 | 24 | 17 |
| right ones kept (of 32) | 32 | 32 | 31 |
| accepted wrong | – | 11 | 17 |
| right, rejected by the consumer | – | 34 | 23 |
| tokens, median / p90 | 6,643 / 9,875 | 18,621 / 43,407 | 15,659 / 47,154 |

- **About a third of the generous cards' gain was the source and join hints.** Without them, the
  context still adds 7 right at the first answer and 12 delivered.
- **A consumer that knows less catches less.** It rejects fewer right answers but accepts more wrong
  ones.
- **Projected to the full 176** (the right ones kept at 31 of 32, 17 of the 48 misses delivered):
  about 141, or 80%, give or take a few points. The line, not clearly over it.

## Naive baselines and the full test (2026-09-30)

**What ran:** every scored gold question and every kept log question, 186 in all (`--set=full`),
fresh and measured.

**The naive baselines** (`eval/explore_naive.py`) have only what the warehouse says about itself: the
catalog snapshot's 323 tables, their columns and types. No log, Variables, joins, Computations, examples
or filter values. Both use Sonnet 5.5.
- `schema`: the whole schema in the prompt, one query, one fix after a failed dry run.
- `agent`: a generic tool-using agent (list_tables, describe_table, run_sql with rows, submit), at most
  15 turns.

**The combined method:**
- The consumer is the plain-state agent: its own first request, no source or join hints.
- The service tries precedent first (`explore_precedent.serve_precedent`):
  - retrieve over the request bank's 1,092 Requests;
  - the three closest shapes, slot-filled, checked by the parser's fingerprint;
  - the question's own shape only through another of its texts (other literals), never the text the
    question was written from;
  - else the compiled request.
- At most four answers. A correction is navigated again, and a rejected precedent isn't offered again.

Log questions (176), service's share per request:

| method | right | delivered | tokens p50 / p90 | seconds p50 / p90 | $ per request |
|---|---|---|---|---|---|
| naive, schema in the prompt | 115 (65%) | 0 | 43,864 / 44,044 | 4.8 / 6.3 | 0.112 (about 0.012 cached, see below) |
| naive, generic agent | 107 (61%) | 22 | 50,501 / 118,976 | 22.7 / 40.3 | 0.058 |
| the layer, one shot (baseline) | 132 (75%) | 132 | 6,689 / 9,463 | 4.6 / 8.5 | 0.017 |
| layer + precedent + context + retries | **160 (91%)** | **155 (88%)** | 9,745 / 41,193 | 12.4 / 52.4 | 0.038 (the consumer's own, 0.012 more) |

Gold (10): naive schema 2, naive agent 4, baseline 6, combined 9 (8 delivered).

**What the combination did:**
- **86 of the 186 questions had a precedent:** the business ran the same query with other values.
  - Precedent answered first for all 86, and 85 were right at once.
  - Median 869 tokens and 6.7 s to the first answer.
  - The baseline got 64 of those 86.
- **The other 100 went to the compiled request**, with the agent's context. 74 were right at once, at
  a median of 9,541 tokens and 11.9 s. Trying three precedents first costs tokens and time on a novel
  question.
- **Outcomes over 186:**
  - right at once 104; right after corrections 4;
  - right, rejected by the consumer 55 (its failure: those exchanges run on to four answers, and they
    are most of the p90 tokens and latency);
  - right, but past the targets 6; never right 8; accepted wrong 9.
- **One question the baseline got right was lost.**

**Caveats:**
- **The naive schema run's prompt cache never hit.** The cache breakpoint sat after the question, so
  every call wrote the cache and none read it. Its token count stands; with the breakpoint after the
  schema, its cost would be about $0.012 per request. It delivers none, because every request is past
  the 20,000-token target.
- **The re-ask share is a property of this set.** The log questions are written from the log's own
  queries. The bank's Requests were written from the same sample SQL the questions were, which makes
  finding the question's own shape easier than it would be in production. The values always come from
  the question, into another text of the query.
- **The states are plain, but still written from the reference query.**
- **The latency p90 is mostly the consumer rejecting right answers,** plus precedent attempts before
  the compiled request.

## Reproduced through the committed code (2026-09-30)

The four methods were rerun, every LLM call live, through `eval/comparison/run.py` (the method in the tool:
`qlsc requests`, the precedent route in the router, `navigate.corrected`, `qlsc/meter.py`). The numbers
reproduce the exploration's: log questions, naive schema 116 (66%), naive agent 108 (61%), the layer one shot
132 (75%), the agent 158 (90%, 153 delivered); gold 3, 6, 6, 9 of 10. The schema's prompt cache now hits (its
breakpoint sits after the schema): $0.012 a request, the cheapest per right answer (1.8 cents, against 2.3
for the layer and 4.7 for the agent). The value of the layer is accuracy, tokens and latency, not dollars.
Results: [eval/comparison/README.md](../examples/fennmoor-bank/eval/comparison/README.md).

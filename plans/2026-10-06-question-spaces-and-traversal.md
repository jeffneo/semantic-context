# Question spaces and traversal: how big a refactor, how we know it is better, how we migrate

Status: proposed (2026-10-06). An assessment, not a build: nothing here is changed, and every step that changes the model or the method waits on your
decision (the last section). It exists because a customer conversation gave us a cleaner cut of the architecture than the one the code grew into, and
the temptation is to redesign from the ground up. This plan says what the cut is, what it would touch, how to tell whether it is better, and a migration
that can be stopped at every step. The process-side consequences are in [the efficacy plan](2026-10-06-efficacy-ontology.md).

## The cut

A practitioner's view, relayed by you, which I have restated in our words:

- **A lower ontology is a question space.** It is what can be asked and done in one region of the business: a semantic view's datasets, relationships,
  fields and metrics, and the actions and skills the business has executed. It is governed by **is**: nothing is in it that the historical record does
  not show. Automation adds actions to it from that record. He scopes semantic views to question spaces defined from the discovered semantic layer.
- **An upper ontology is a traversal.** It maps a request to a lower ontology and to a path through it. It is governed by **ought**: to change what the
  business does, change the traversal.

Our documents say *question space* and *traversal*, because "upper" and "lower" mean something else in the ontology literature; the customer's words
are a gloss, and we should confirm they mean this.

## What the code is today, against the cut

| The cut | What exists | Gap |
|---|---|---|
| Question space | `Semantic` (levels 1 to 3: 109, 15 and 4 groups in the example), each with Variables, tables, joins, Computations, Requests, precedents; the OKF bundle already files Computations by area | A space is implicit: nothing names a level as "the space", scopes an answer to one, or exports one |
| Actions in a space | `process` `Action` elements, with evidence (support, outcomes); `Skill` nodes in memory | Neither is tied to a space; no gates for entering one |
| Evidence | `MEANS {score, status}`, OKF provenance, `support`, stability | Scattered; no kind (usage, observational, experiment) and no single record |
| Traversal | `navigate.cohort` (embed, walk the Semantic hierarchy, cohort of tables) and `navigate.route` (memory, precedent, compiled, Cypher, free SQL), a ladder chosen by cost | Implicit, similarity-driven, and **closed**: nothing a steward can set ("fraud cases go to the fraud space whatever they resemble") |
| Rules ("ought") | none; the only ought in the repo is `entitle` (what a principal may read) and the router's costs | The whole upper layer |

The finding that matters: **the lower layer is mostly built, and the upper layer is mostly absent.** The refactor is an addition above the build, not a
change to it.

## How big

Sizing by what the code is (lines, with the test and evaluation suites that guard it):

| | Lines | What happens |
|---|---|---|
| Parser, extract, parse, load, joins, variables, computations, cluster, hierarchy, requests, health, names, graph, config, llm, meter | about 4,600 | **Untouched** |
| Compile, virtualize, entitle, the warehouse connectors | about 2,600 | **Untouched** (the gateway is the precedent for a governed layer, not something to rewrite) |
| `process/` (annotate, build, abstract, outcomes, absorb, context, outlook) | about 2,600 | **Untouched**, plus one new stage (promotion into spaces) |
| `navigate`, `memory`, `converse`, `distill`, `okf`, `align`, `cli` | about 4,300 | **Extended in parts**, perhaps 1,000 to 1,400 lines touched: navigation records and honours a space; memory gains expiry; skills carry bindings and examples; OKF writes a bundle per space; align gains evidence records |
| New: `spaces.py`, `traversal.py`, `evidence.py`, an Ossie exporter | about 1,800 to 2,500 | Spaces (select, name, scope); the rule loader, evaluator and default policy; evidence records; the exporter |
| Tests and evaluations | 3,600 and 8,200 | **The asset that decides the approach** (below) |

So about **70% of the code is untouched; another 30% sits in modules that are extended in parts (7 to 10% of all lines change); and the new code is roughly 15%** of what exists. A ground-up redesign would
rewrite code that the cut does not question.

**Why not ground up.** What the repository holds that a rewrite would throw away or have to re-earn:

- **Measured baselines.** The 186-question comparison (qlsc used by an agent: 90% right against 61 to 66% for the same model given only the schema),
  the entitlement checks (0 incidents, negative controls caught), memory's economics and freshness, the navigation scores, the process evaluations. They
  are the only thing that can say a change is not worse.
- **Hard-won correctness in the parts the cut ignores:** the SQL parser, the trusted-join logic, the compiler's no-row-multiplication proofs, the Virtual
  Graph's quirks and signed pass-through, the entitlement gateway.
- **Determinism:** seeded builds, sorted projections, cached LLM calls, the `fingerprint.py` check that a refactor changed nothing.

A rewrite is justified only if the first migration steps show the cut does not fit the existing layers (for example, if no Semantic level works as a
space, or if traversal cannot be made explicit without changing what navigation returns). That is a decision point, below, not an assumption.

## How we make sure it is better

"Better" is stated as hypotheses with a metric, a baseline and a kill criterion, set before any code. Each is measured on the harnesses we already have.

| | Hypothesis | Measured by | Baseline | Succeeds if | Stops if |
|---|---|---|---|---|---|
| H1 | **Scoping to a space helps navigation:** a narrower cohort at no loss of accuracy | the 186-question comparison, `layer` and `agent` arms | 75% and 90% right, 6,667 and 10,667 tokens (p50) | accuracy not lower (Wilson intervals overlap) and tokens or wrong-table errors fall | accuracy falls by more than the noise, or no gain |
| H2 | **Behaviour changes by editing the upper layer,** with nothing else moving | `process_agent.py`, and the replay once built: edit one rule, measure the choices | the arms in `results/process_agent.md` | the edit moves choices as intended in the tested cases; other spaces' results are unchanged | a rule edit has effects it should not, or none |
| H3 | **Evidence separates authority from use:** every lower object carries an evidence record, and the diff between rules and evidence is useful | coverage of objects with a record; the diff read by a person on the example | none (scattered today) | a reviewer can see, for any rule, what the record does and does not show | the records are not read or add noise |
| H4 | **The efficacy rules beat the typical rep** | `process_outlook.py` validity classes, the agent test, the replay | typical rep 22%, rep 28%, old ranking 24% | the efficacy plan's gate | below the typical rep |
| H5 | **A space exports as a semantic view** that a warehouse product accepts, round trip | an Ossie and OKF validator; a round trip against a Snowflake semantic model | the OKF bundle (validated today) | validates and round trips | the spec cannot carry what we need (provenance) |
| H6 | **No regression:** determinism, cost, the existing guarantees | `fingerprint.py` before and after; the comparison, entitlement, memory and process evaluations | their current results | identical where nothing was meant to change | any unexplained difference |

Parity is checked first and always: **a step that is meant to change nothing must produce the identical fingerprint and the same answers** (the repo's
rule for a refactor: run `eval/fingerprint.py` before and after).

## The migration

Every step is additive, behind a switch, and can be stopped; none rewrites a stored layer, and `qlsc build` stays idempotent. The order puts the cheapest
test of the central claim first.

- **M0. Freeze the baselines.** Record the current results as golden (`results/*.json` are already committed; record the fingerprint and the 186-question
  routes). Agree H1 to H6 and their thresholds. *Small.*
- **M1. Spaces as a read-only view.** `qlsc spaces`: pick the Semantic level (by stability and size), name each space, scope it (tables, joins, Computations,
  Requests, precedents); write the OKF bundle per space. No behaviour changes. *Exit:* fingerprint unchanged; spaces readable by a person; the level
  chosen. *Rollback:* delete the view. *Small.*
- **M2. Scoped navigation behind a switch** (`navigate.scope: none | space`, default none). Record the space a question resolved to in its trace
  (already implicit in the Semantic walk). **First test of H1.** *Exit:* H1 measured on the comparison harness. *Rollback:* the switch. *Small to medium.*
- **M3. The default traversal made explicit.** Express what navigation and the router do today as a default policy object: same decisions, now
  inspectable, with a hook for rules. *Exit:* **identical answers and routes on the 186 questions** with the hook empty. This is the delicate step and the
  **decision point**: if parity cannot be had without changing what navigation returns, stop and reconsider the cut before building the upper layer. *Medium.*
- **M4. Rules and evidence for the process.** The efficacy plan's phases 3 to 5: the vocabulary and rules, diagnosis and advice as a traversal, a rule
  edit that changes behaviour. Evidence records on lower objects (extending `MEANS` and the OKF provenance). **Tests H2, H3 and H4.** *Large; it is the
  efficacy plan.*
- **M5. Lower actions, skill bundles, expiry, export.** Promote Actions and skills into spaces by gate, with evidence; skills carry bindings and masked
  examples; fetched-context memory gains an expiry (lazy on read, swept in the background, per-class, with facts, decisions and skills left bi-temporal);
  an Ossie exporter beside OKF. **Tests H5.** *Medium.*

**Stop rules.** After M2, if H1 is not met: spaces stay a read-only view and the traversal work continues only for the process, where the case does not
depend on H1. After M3, if parity fails: stop and reconsider the cut. After M4, if H2 and H4 fail: the upper layer is not earning its keep and the
outlook stays a picture.

**What does not migrate.** Stored data is not rewritten: new labels and properties are additive (a `Rule` label, evidence properties, a space marker on
existing `Semantic` nodes, an `expires_at` on fetched-context nodes). Configuration keys are kept, with new ones added in `defaults.yaml` with their reasons
(the repo's rule). The documents change last: `README.md`, `docs/design.md`, the glossary and the deck use *question space* and *traversal* once the steps
that justify them have run.

## Risks

- **The cut is one practitioner's view.** It fits our evidence well, which is a reason to test it and not to trust it; M1 and M2 are the cheap test.
- **Spaces overlap.** A table (for example the customer dimension) belongs to many areas; a space is a scoped view, not a partition, and the scoping must
  tolerate shared members.
- **An explicit traversal can be worse than an implicit one.** Similarity is robust to wording; rules are brittle. Rules override similarity only where a
  steward has set one, and the default stays as it is.
- **Rules can encode wrong policy.** The upper layer is where "ought" lives and so where an error does the most harm; hence stewards, review dates,
  replay before activation, and the evidence diff.
- **Scope creep.** Three things are bundled by the conversation (the cut, memory expiry, the interchange format). They are independent: expiry and the
  exporter can ship without the cut and should not wait for it.
- **Interchange is a draft.** Apache Ossie (incubating, formerly the Open Semantic Interchange) is at an early draft (0.2.0.dev0) and says its names may
  change; the exporter is experimental and sits behind OKF.

## What I would ask the customer

Whether his "upper" and "lower" mean what we have written; how he defines a question space's boundary (a business area, a role, a data product); who
authors and approves traversal changes in his practice; how he separates what the record shows from what is allowed; what he does for expiry (absolute
or sliding, and which eviction policy); and which of his semantic-view artifacts he treats as the interchange.

## Decisions

1. **Adopt the cut as the direction,** to be tested by M1 and M2 before it is adopted in the documents? *Recommend yes.*
2. **Incremental migration, not a redesign.** *Recommend incremental, with M3 as the point where we decide whether the cut fits.*
3. **A space is a `Semantic` node at a level chosen by measurement,** or a new label? *Recommend the former* (see the efficacy plan).
4. **Parity gate at M3:** identical answers and routes on the 186 questions. *Recommend yes,* since "no change" is the only claim a refactor step makes.
5. **Ship expiry and the exporter independently of the cut,** when we resume functional dev. *Recommend yes.*
6. **Order:** M0, M1, M2 first (a few days of work, tens of dollars of evaluation (the comparison harness is about $25), and they test the central claim), then decide on M3. *Recommend this.*
7. **Where the work sits relative to the efficacy plan:** M4 *is* the efficacy plan's phases 3 to 5, so one plan's gate is the other's. *Recommend running
   them as one programme in this order.*

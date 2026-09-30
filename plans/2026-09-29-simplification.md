# A smaller, coherent qlsc: what's sediment, and what to cut (2026-09-29)

Status: agreed 2026-09-29, all of it (decision (c) as clarified: memory keeps its relationships as edges, rewritten from their start node's key column when it's written). Phase 1 done; phases 2 and 3 next.

An assessment of the whole repository: `src/qlsc/` (9,800 lines), `parser/` (2,200), `vg-passthrough/`,
`tests/` (1,400), and the example's `eval/` (4,600). The question is where the code serves the system
model, and where it serves cases that stopped mattering: failed experiments still wired in, one concept
computed two ways, state kept twice, and heuristics fitted to the example. Nothing here has been
changed yet. Items marked **decision** change the model or the method, and wait for a yes.

## The system model, as the code means it

1. **Evidence.** The log and the catalog, parsed once. The bottom layer holds what they show.
2. **Inference.** The joins are judged; Variables, Semantic levels and Computations are built; the
   designed models are aligned afterwards.
3. **Use.** A question goes to a cohort and its examples. A writer produces a query: a compiled
   request, else free SQL or Cypher. A route runs it (memory, SQL or the virtual graph), on a
   principal's behalf through the gateway.
4. **Memory.** An entity's context is fetched from the virtual graph and kept with provenance,
   freshness and entitlements. The agent's record is kept beside it, and skills are distilled from that.

The inference core is in good shape and should be left alone:
- `joins.py`, `variables.py`, `cluster.py` and `hierarchy.py`;
- the compiler's plan and render;
- the parser's resolver;
- vg-passthrough's token check.

The sediment is at the edges. It sits where features were tried and kept, where one idea gained a second
implementation, and where fixes for particular eval misses became permanent rules.

## Findings

### 1. Failed experiments that are still live code paths

`navigate.py` carries four experiments. Each was measured, found not to help, and switched off, but
still has its own code, settings and prompts:

| experiment | measured | still in the code |
|---|---|---|
| `anchors: parts` (decompose the question) | about even (7 vs 7 gold, 23 vs 22) | `decompose`, `merge_cohorts`, `VALUE_COLUMNS`, the `parts` branch of `trace`, 4 `anchor_*` settings, `prompts/decompose_system.md` |
| `computations` > 0 (definitions for the writer) | a wash (129 vs 130) | `DEFINITIONS` in `trace`, `definitions_text`, `computation_tables`, and a `definitions` slot in both free prompts |
| `concepts` > 0 (the glossary) | +3 on 176, "an experiment" | `GLOSSARY`, `glossary_text`, and a `glossary` slot in both free prompts |
| `examples_by: runs` | superseded by similarity | `QUERIES`, and the `else` branch of `trace` |

A similar case is `llm.query_effort` ("high effort gained nothing").

`mode` and `rank` are different: `eval/navigation.py` sweeps them, and `results/navigation.md` reports
the sweep. So they're ablations with a reader. Keep them, or drop the sweep with them.

**Proposal (decision):** delete the four experiments. The plans record their results, and git keeps the
code. That's about 250 lines, 10 settings and one prompt out of navigate, and the free prompts lose two
always-empty slots.

### 2. One concept, two implementations

- **The router rule exists twice, and the two versions already differ.**
  - `answer_routed` (the live router) tries memory first and runs Cypher with the free writer.
  - `pick` (used by `execution`, `log_accuracy`, `graph_accuracy` and `entitlements` to score "routed")
    doesn't.
  - `test_route.py` tests `pick`, and its compiled-wins branch is never reached by the live router.
  - **Fix:** one rule over candidate answers, called lazily by `ask` and on precomputed answers by the
    evals.
- **An answer is a bag of optional keys.** It may carry any of `skipped`, `declined`, `refused`,
  `error`, `fallback`, `check.error`, `result.ok` and `not_memory`, which is why `answered()` probes
  six places. An answer also doesn't say which tables it read, so:
  - `converse.read_tables` regex-scrapes them back out of the SQL or the Cypher;
  - `entitle.refused` regex-scrapes labels out of the Cypher.

  **Fix:** one small answer record with the fields route, writer, query, tables, check, and result or
  reason. A compiled plan knows its tables; for free SQL the parser, running in-process (§6), gives them.
- **Memory's read conditions** (source, freshness, row-policy visibility) are written twice: in
  `memory.cypher()` and in `memory.Guard`. **Fix:** `cypher()` uses the Guard.
- **"Frozen" and "sandbox" tables are defined twice, and the definitions differ.**
  - `navigate.FROZEN` filters on the table's kind and follows `DERIVED_FROM` through views.
  - `memory.FROZEN` does neither.
  - `navigate.PERSONAL` is used by navigate and computations. OKF has its own status rules.

  **Fix:** load computes `Table.frozen` and `Table.sandbox` once, from the log, and every stage reads
  the flags.
- **Canonical table names are computed twice.** `extract.build_catalog` has its own shard regex and
  rules loop, and `Catalog.__init__` canonicalizes again. On the real catalog the second pass changes
  0 of 323 names.
  - Being transient is signalled by a `{` in a rule's replacement, tested in five places.
  - **Fix:** one `canonical()`, and `Catalog.transient()`.
- **Settings have two namespaces.** `llm`, `memory`, `distill`, `entitlements` and `parser` sit at the
  top level (`s["memory"]`). `navigate`, `cluster` and the rest sit under `parameters`
  (`s.params["navigate"]`). **Fix:** one namespace.
- **The LLM has two call modes.** A forced tool is used for Haiku, a structured output for Sonnet 5.5,
  and which one a model needs is discovered at runtime in a mutable class-level set. That threads a
  `tool=` argument through every call, plus a repair for nested arrays that arrive as strings.
  - **Proposal (verify first):** if Haiku 4.5 takes structured outputs, use them for both. The cache is
    keyed by request, not by mode, so no cached answer is lost.

### 3. State kept twice in memory (decision)

`qlsc virtualize` writes every relationship as a key column of its start node's own table, by
construction (`virtualize.py:312-330`). So a relationship in memory is a function of its start node's
properties. Memory nonetheless keeps each relationship as state of its own:
- its own `fetched_at`, `holds_until`, `fetched_by` and `fetched_with`;
- its own freshness condition in every read, and in `Guard.relationship`;
- entitlement-aware pruning (`PRUNE_INTO`, `PRUNE_OUT_OF`, with `$open` and `$visible`);
- on the virtual graph, two read forms: keyed, and a traversal kept only for hop-1 reads out of the
  anchor. With them come `via_window`, `foreign_key()`'s five checks and `keyed()`.

**Proposal:** one read form on both targets: the nodes of label L whose property P is in `$keys`. That
covers the anchor by its key, the facts by their foreign key and the dimensions by their key.
- **Relationships are derived when a node is written.** A written node's outgoing relationships of each
  type are replaced from its key column, with no state of their own.
- **Pruning becomes local and needs no entitlement logic.** A relationship to a node the reader can't
  see reveals only the key value they already read.
- **"One Cypher, two targets" becomes literally true again.** The design doc still claims it, but it
  stopped being true with keyed reads.
- **The cost:** hop 0 runs before hop 1 (about one more round trip per fetch; batches amortize it).
- **Size:** about 150 lines out of `memory.py`, and the relationship guard out of `compile.render_cypher`.
- **Checks:** `memory_entitlements` and `memory` must rerun.

### 4. Two security configurations, one of them unsafe (decision)

`virtualize.passthrough: false` ("option A") is a second entitlement path for the virtual graph:
`check_cypher` refuses row-policied tables and dry-runs probes. The example doesn't use it, and it has
two hazards.
- **Memory never consults it.** Without the pass-through, `recall --as` would fetch a row-policied
  table's rows as the virtual graph's own identity. It would then file them as read by the principal:
  a latent leak.
- **Enforcement is set in three places.**
  - the estate's `virtualize.passthrough`;
  - the container's `QLSC_PASSTHROUGH` environment variable;
  - the `VG_JDBC_JAR` driver swap.

  A mismatch between them fails open.

**Proposal:**
- The pass-through is required for any virtual-graph read on a principal's behalf. Without it, Cypher
  and memory refuse `--as`.
- Delete option A, and the `QLSC_PASSTHROUGH` switch; the jar is the one switch.
- The gateway checks once that an unsigned statement is refused, so enforcement fails closed.

### 5. Rules fitted to eval misses

The compiler's checks on the request (`compile.py:347-502`) were added after particular misses:
- **`open_period`** leaves a period ending today open. It exists because the example's filled data runs
  past its pinned "today" (2026-07-13 against 2026-07-01). That's a property of the fixture, not of
  questions. **Proposal (decision):** delete it, and pin `today` at the data's end.
- **`week_usage` and `weeks`** regex the log's SQL text for `DATE_TRUNC(..., WEEK...)`. The parser
  already extracts date-truncation dimensions as Computations. **Proposal:** read the week convention
  from them.
- **`check`** (a Computation's filter value the question doesn't say, or a value the question says that
  the request leaves out) was measured at +3 of 59. Keep it, but test its behaviour, not the wording of
  its notes.

### 6. The parser service doesn't earn its boundary (decision)

- **The tool already imports `qlsc_parse` in-process in six modules.** Computations already run through
  it in-process over every shape. Only `parse.run` goes over HTTP.
- **What exists only because of the boundary:**
  - the service and its batch mode;
  - `__main__.py`, which nothing calls;
  - the Dockerfile and the compose service;
  - the HTTP client;
  - the catalog-version handshake;
  - three `parser.*` settings.
- **The boundary is also a hazard.** Edit `resolve.py` without rebuilding the image, and resolve (in
  docker) and computations (in-process) run two different parsers. Nothing detects it.
- **Speed isn't a reason.** In-process fingerprinting measured 0.64 ms a text, against 0.82 ms in the
  service. A process pool matches today's 17 s.
- **Proposal:** `parse.run` uses a process pool (`parser.workers`), and the service goes. About 250
  lines and a container. It drops the untested Cloud Run story.

The parser's own sediment, which needs no decision:
- **Computations re-parse and re-qualify every shape.** That's a third copy of the parse, it swallows
  every error unrecorded, and it guesses the default project differently from resolve.
  **Fix:** compute them inside resolve's record. This changes results slightly, so the evals rerun.
- **`resolve.py` duplication:**
  - two join recorders;
  - an ON clause retagged after the fact;
  - `origin_of` repeating `_derived`;
  - "names from the first leaf" written three times;
  - table-kind classification in five places;
  - dead compatibility code under the pinned sqlglot.
- **Outputs nothing reads:** `family_id`, `output.columns`, `root_from` and the fingerprint's
  `annotations`. Annotations reach the graph only for a shape's representative text, so they can't
  serve author counting as plumbed.

### 7. The bottom layer holds what nothing reads

Loaded and never read by the tool, the evals, the demo queries or the tests:
- **the `COMPARED` relationship**, which isn't in the design doc's bottom layer either;
- **on QueryShape:** `family_id`, `root_from`, `output_columns`, `week_jobs`, `week_bytes`, `slot_ms`,
  `select_star`, `limit`, `annotations`;
- **on Table:** `physical_names`, `cluster_columns`;
- **on FILTERS:** `value_first_seen`, `value_last_seen`;
- **on USES_JOIN:** `scopes`.

**Proposal (decision):** load what the model uses or a reader of the graph would ask about. Drop the
rest from load and from the parser record.

### 8. Tests that specify implementation

Of 123 test functions, 88 earn their place: the parser's 45 golden tests (their dicts are load's
input), the boundary, config and prompt guards, the Cypher lints, and the core compiler rules.

The rest:
- **16 pin exact representations.** Examples: whole Cypher strings, CTE names, an internal
  `per_fct_balance_account_key`, `"\nWHERE (branch.ok) AND (r0.ok)"`, and an ORDER BY standing in for
  per-anchor paging. The requirements behind them are that zeros stay, outer joins keep their null
  group, nothing fans out, a SUM of no values is NULL, and a timestamp period is a half-open range.
  **Fix:** assert those on rows. Run compiled SQL through `sqlglot.executor` (already a dependency) over
  tiny tables, and the guarded Cypher on a scratch database.
- **9 are regressions for historical bugs.** Keep the cheap parser ones; delete `test_extract.py:40`, a
  circular round-trip.
- **4 test private helpers** (`within`, `DSU`), **4 are duplicates** (the router test twice), and
  **2 are edge cases** with no requirement behind them.

What's missing matters more:
- **No unit test covers the method's central rule:** `joins.suspects`, `IdSpaces` and `confidence`,
  all pure functions.
- **Untested:** `memory.run_batch` (a fake target would do), the five conditions in
  `memory.answerable`, and the live router.
- **No fixture estate is built twice** to test "builds are deterministic". The no-LLM paths make it
  possible.
- **`execution.py`'s matcher** (210 lines of pure functions that decide every accuracy number) has no
  tests.

### 9. The eval harness

- **The baselines are the wrong way round.**
  - The default writer is `compiled`, and the README's accuracy table comes from the
    `*_writer_compiled` files.
  - The unsuffixed `execution.md`, `log_accuracy.md` and `graph_accuracy.md` are old free-writer runs.
  - `docs/design.md:164` still gives `navigate.writer` as `free`.
  - The cause is that `common.overrides` adds a suffix even for a value equal to the default.
- **`robustness.py` runs level-2 Leiden on its own projection, with weights floored at 1e-3.** The tool
  uses the raw score, so the sweep reports on a weighting the tool doesn't use.
  **Fix:** call `hierarchy.communities`.
- **`memory_entitlements`' `Rulebook` re-derives each label's table, key and foreign key from the same
  `schema.json` the tool reads.** So that part of the oracle isn't independent.
- **Obsolete:**
  - `diagnose.py`, `diagnose_cypher.py` and `agreement.py`: one-off diagnoses whose conclusions are in
    the accuracy plan; 290 lines and 6 result files;
  - 56 `qdd_*` result files, named for code states, with no commit recorded.
- **Duplicated across scripts:**
  - the verdict chain, the route loop and the report table (`execution.py`, `log_accuracy.py`,
    `graph_accuracy.py`, `qdd.py`), which could be one `accuracy.py`;
  - three override parsers;
  - LLM usage counted by monkeypatching `LLM.__init__`;
  - three ways of comparing rows;
  - two readers of BigQuery's job log;
  - seven "customers active in the window" queries;
  - hard-coded CIFs, states, branch 101 and LLM-named labels.

In all, about 700 of the eval's 4,600 lines, and about 70 result files.

### 10. Bugs found along the way

These are fixed regardless of the decisions above.
- **DELETE and UPDATE filters use a second classifier** (`resolve.py:845`). It records ops as `LT` and
  `EQ` where a SELECT's are `<` and `=`, and it drops negation.
- **`physical_sql` takes a Looker PDT's "newest generation" by sorting names**
  (`warehouse/__init__.py:175`). Real PDT ids aren't ordered by time; the test's fixture names make it
  look right.
- **Computations swallow parse errors silently** (§6).
- **The robustness sweep measures a weighting the tool doesn't use** (§9).
- **The memory leak without the pass-through** (§4).
- **`LLM.cost()` prices every model at Haiku's rate.**

### 11. Docs

- **`docs/design.md`'s parameter table records history,** each experiment's measurements included.
  Once the experiments go, it can say what each setting is and why, and link the plans for how it was
  found.
- **The table also needs these corrections:** "One Cypher, two targets" (§3) and `navigate.writer`
  (§9).

## What stays

- **The connector boundary**, a stated principle. Its registry is tiny, and keeps BigQuery's libraries
  optional.
- **`health.py`'s cross-check** against the warehouse's own references.
- **The Cypher lints for the free writer.** Virtual Graph returns silently empty answers otherwise.
- **The compiler's plan and render.**
- **The agent-side model.**
- **`rdflib-neo4j`**, which alignment needs.

## Plan

1. **Phase 1: refactors that change no results.**
   - **The work:**
     - dead code;
     - the router rule once, and the answer record;
     - the Guard used by `cypher()`;
     - one settings namespace;
     - one canonicalization;
     - `resolve.py`'s duplication;
     - the eval's shared code, the baseline rename, and the obsolete scripts and results gone;
     - the tests: implementation-pinning ones rewritten or deleted, the missing core tests added.
   - **Checked by:** `eval/fingerprint.py` around `qlsc build` shows no difference, and the fast evals
     repeat their numbers.
2. **Phase 2: the decisions,** each checked by the evals it touches, with results updated:
   - (a) delete navigate's experiments (§1);
   - (b) the parser in-process (§6);
   - (c) memory's relationships derived from nodes (§3);
   - (d) the pass-through required (§4);
   - (e) the compiler's fixture-fitted rules (§5);
   - (f) the bottom layer trimmed (§7);
   - (g) one LLM call mode (§2), once verified.
3. **Phase 3: the bugs in §10,** each with a test that fails first.

Rough size: 1,500 to 2,000 lines out of about 18,000, one container, about 15 settings, a prompt and
about 70 result files. The larger gain is in the number of states. There's one router, one read form,
one security configuration, one parser and one settings namespace, and every table flag has one
definition.

In Phase 2, compiled Cypher on the virtual graph is worth a thought. The router never picks it, since
compiled SQL always wins where a request compiles, and only `ask --cypher` and the eval's Cypher column
reach it. Dropping it would remove `navigate.writer` altogether: `--cypher` would mean free Cypher, and
`render_cypher` would stay for memory's route. It changes a reported number (compiled Cypher's 38/3/8),
so it's a decision too.

## Phase 1, as built (2026-09-29)

Changing no results, as checked:
- **The build:** after the changes, two builds in a row gave the same fingerprint. Every LLM call hit the
  cache, so every naming prompt and model prompt was one seen before. Against the baseline build, the
  bottom layer, the Variables and level-1 membership hash the same.
- **The virtual graph's model:** the same.
- **Accuracy:** execution, graph accuracy and the log report give the same verdict for every question
  (gold 6 / 3 / 6; graph-shaped 5 / 8 / 8; the log's 176 questions 133 / 38 / 133).
- **The other evals:** bottom layer, navigation, memory, memory_entitlements, converse (26/26), distill
  (13/13) and economics all rerun and match.
- **Tests:** 104 pass, and the parser's 52.

What changed:
- **The router's rule, once** (`navigate.ROUTES`, `stands`, `route`). The live router runs it on
  candidates, lazily, and the evaluations' `pick` runs it on answers already computed. `answer_routed`
  is its candidates.
- **An answer says which tables it read** (`tables`): from the plan when compiled, and from the query
  when written freely. `converse` and the gateway's Cypher check read it, instead of regex-scraping the
  query. The rest of the answer record (its optional keys) is unchanged; §2's fuller record wasn't
  needed for this.
- **Memory's read conditions, once.** `memory.cypher()` builds them from the `Guard` the memory route
  uses.
- **Liveness, once.** `load` sets `Table.frozen` and `Table.sandbox` (`LIVENESS`), and navigate,
  computations, memory and the log's questions read the flags. The two differing `FROZEN` queries and
  `PERSONAL` are gone.
- **One settings namespace.** `parameters:` is gone. Every section is top level, `s["navigate"]` like
  `s["memory"]`, and the two `virtualize` sections are one.
- **Canonical names, once** (`qlsc_parse.catalog.canonical`, used by `extract` and `Catalog`). The
  catalog no longer re-keys its tables, `rules=` is gone, and `transient()` names the `{` convention.
  `extract` still reproduces the example's catalog exactly.
- **`resolve.py`:**
  - one join recorder;
  - the ON clause's join type passed down, instead of retagging it afterwards;
  - MERGE origins through `_derived`;
  - the per-node filter closure gone, and with it the per-file lint exemption;
  - dead code under the pinned sqlglot gone, and `output_summary`'s unused parameter.
- **The compiler:** `dump` gone; `plan_tables`.
- **The evaluations:**
  - `match.py` holds the ruler (moved from `execution.py`), the verdict chain, both routes, the route
    table and LLM usage. `execution`, `log_accuracy`, `graph_accuracy` and `qdd` use it.
  - One override parser. It suffixes a result file only for values that differ from the defaults.
  - The `*_writer_compiled` results are the baselines now. The old free-writer baselines are gone
    (git has them).
  - `diagnose.py`, `diagnose_cypher.py`, `agreement.py` and 56 `qdd_*` result files are gone. `qdd`
    writes to `<work>/qdd/`, with the commit it ran at.
  - `native` and `quantiles` are in `common.py`.
  - `economics` draws from 1,000 candidates: today's runs had fetched most of the first 400.
- **Tests:**
  - the SQL compile tests run the compiled SQL over a few rows (sqlglot's executor) and assert the
    answer, not the spelling;
  - new: the join-confidence rule (`test_joins.py`), the matcher (`test_match.py`), the router's order,
    and a batch against its anchors fetched alone (a fake virtual graph);
  - gone: `within`, `DSU`, the catalog round trip, `computation_ids`' edge case and the duplicate router
    test;
  - loosened: the Cypher whole-string comparison, and the check notes' wording.
- **Found on the way, fixed:** the connector crashed printing the bytes of a query on a row-policied
  table, which BigQuery doesn't report. That broke `virtualize` since the row policy was set up.

Left for phases 2 and 3, found on the way:
- **Builds aren't fully deterministic** (phase 3). A level-1 group's naming evidence can differ from
  build to build:
  - `cluster.evidence` breaks ties in the table counts and the sample query arbitrarily;
  - `hierarchy.documents` joins the Variables in `collect()` order;
  - `virtualize`'s GROUPS picks a table's area from tied counts.

  A different evidence text misses the LLM cache and renames things. The baseline build before Phase 1
  did: new level-2 names, and new relationship types in the virtual graph's model. The next builds hit
  the cache again. Fixing it means one more round of names, once.
- **Not done from §9:** the remaining eval duplication (the two job-log readers, the anchor queries), and
  fixtures for the example's hard-coded anchors and labels. The oracle's `Rulebook` independence (§9) is
  still open.
- **Environment:** the Docker VM's disk filled during a rebuild. Most of it is another project's volume.
  Neo4j quarantined `bigquery` and set it read-only, and both were restored. About 4 GB is free now.

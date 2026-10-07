# From an informational page to a demo: the full-page pass

Status: partly agreed (2026-10-07; the decisions are the last section). The result of a pass over the finished Example page (all eight sections), at desktop and phone width, in light and dark.
Nothing in the layout or the components is changed by it. Two things were done: the Cypher the page's generators run now lives in one folder, and the
references below were collected. What a visitor sees changes only in the steps the last section marks as agreed.

## What the pass checked

| Check | Result |
|---|---|
| Console on a fresh load | no errors or warnings |
| Horizontal overflow at 400 px, every section | none; the wide tables scroll inside their own box (memory's cost table and governed matrix, accuracy's scores table and query boxes, security's results table) |
| Phone width, the last two sections (memory, security) | reads well: the principal map wraps to the width, the pipeline stacks, the segmented controls wrap to two lines |
| Dark mode, memory and security | legible; the green holds; the `EstateTiles` refactor draws the same 323 tiles in both views it serves |
| The generators after moving the queries | `ui_discovery.py`, `ui_virtual.py`, `ui_memory.py` write byte-identical JSON |

One thing to fix, not fixed: the accuracy section's scores table, the page's headline table, is 880 px wide in a 360 px box on a phone, so the numbers that matter
most are reached by scrolling sideways. A stacked layout (a card a method) would read better there.

Not checked: a real touch device (the pane emulates one), Safari and Firefox (Chromium only), and the screen-reader reading order.

Measuring in the Browser pane needs care: while the pane is hidden, CSS transitions freeze mid-way. The tile maps animate between layouts, so a measurement
taken then shows tiles at their old positions and a page that seems to overflow (it reported 724 px in a 390 px viewport). With transitions off it does not.
It is not a bug, and not worth a fix, but it will mislead the next person who measures.

## How busy it is

At 1440 x 900 the page is 23,270 px, about 26 screens, and on a phone about 42,000 px. A section is 2,800 to 4,000 px, with three to five parts and 1,000 to
1,300 words. Where the length is:

| Section | Height | Parts, tallest first (px) |
|---|---|---|
| Discovering the semantic layer | 3,907 | joins 1,601 · regrouped 1,275 · funnel 710 |
| Generating the Virtual Graph schema | 3,866 | schema explorer 1,142 · what it is for 1,099 · two pictures 802 · steps 423 |
| Promoting results to memory | 3,967 | how long it holds 1,374 · what is promoted 856 · what it buys 837 · governed 499 |
| Accuracy at full scale | 3,081 | every question 752 · how often right 667 · costs 424 · caveats 408 · gain 374 |
| Row-level security | 3,417 | principals 953 · checked 847 · pipeline 665 · same question 551 |
| Routing a request | 2,767 | ladder 848 · trace 832 · served 476 · closing paragraph 210 |
| The warehouse | 1,356 | |
| The scenario | 535 | |

### A section with one main component

Each section keeps one component open, the one that carries its claim, and the rest become a row of collapsed items: a title and a one-sentence finding
(for example "Every figure above, by method: 186 questions"), opening in place. My picks, for you to overrule:

| Section | Main (stays open) | Collapsed |
|---|---|---|
| Discovery | the tables regrouped | the funnel becomes a one-line strip (315,729 queries to 109 groups); the join chords |
| Virtual Graph | the two pictures (`.semantic` beside `.rows`), with the explorer's node and arrow panel folded into it | the steps as a strip; the generated schema detail and what was left out; the Cypher questions |
| Router | the ladder | the ten-question trace (it becomes the live router demo, below); what each rung served; the Cypher rung's limits |
| Memory | what it buys (the cards and the pays-back-after-8 chart) | what is promoted (the schema graph); how long it holds; governed (see below) |
| Accuracy | how often the answer is right | the question wall; costs; the gain. "Before you quote these" stays open, shortened: the caveats must not hide |
| Security | the same question, three principals | the principal map; the pipeline; the checks as a one-line result ("0 schema leaks, 0 row incidents; all 4 broken gateways caught, all 3 bypasses refused") |

By my estimate the page goes from 23,000 px to about 11,000, with everything one click away. The estimate assumes about 70 px a collapsed item.

### Other things that make it busy

1. **The 323-tile map is drawn four times**: the warehouse, the regrouped tables, the memory freshness and the security principals. Each is 950 to 1,400 px.
   One sticky map with a lens would save about 3,000 px, but it was decided against: it breaks the flow of the page, where each section arrives with its own
   picture. The four stay. The saving has to come from collapsing what surrounds each map.
2. **The schema graph is drawn four times** (the two pictures, the explorer, the questions, memory's fetch). The explorer and the two pictures overlap most.
3. **Memory's "Governed once remembered" and security's principal map say the same thing** about the same three principals. One of them can point at the other.
4. **The router's "what each rung served" and accuracy's scores** are two views of the same evaluations. Keep one headline and link the other.
5. **A results strip at the top.** The header band now shows only the estate (3 projects, 323 tables, 315,729 queries). The page's findings (right 90% of the time
   against 66% for the schema alone; a remembered read in 0.045 s against 0.709 s; no leaks across 60 principal questions) are 20,000 px down. A visitor who
   leaves after one screen should have met them, each linking to its section, each with its caveat in its section.
6. **The sidebar lists sections, not parts.** If sections stay long, listing the parts under the current section would let a visitor jump inside one.

How to build it, when it is agreed:

- One shared `Part` and one shared `Detail` (a disclosure). `Part` and the loading boilerplate are copied verbatim into six section files today; the change
  that adds collapsing and a references row at each section header is the moment to make them one.
- Mount a collapsed component when it opens, not before: the tile maps and the graph layouts measure their container, and a hidden one measures zero.
- Use native `<details>` or `hidden="until-found"` so the browser's find-in-page still opens what it finds, and open the item a `#section/part` link names.

## From informational to a demo

What the earlier demo's run view had, in our terms: two panels for one question (the estate alone, the estate with the semantic layer), a row of metric cards on
each (tool calls, context window, response time), a "Thinking" log of the steps as they happen, and a row of "Try" suggestions.

### Live, not replayed (decided)

Each section and each component gets an expander at its left edge. Pressed, it opens to the right and shows the query or command behind what is on screen, with
a Run button. Run goes against the real thing and shows the result in place: Cypher against the Fennmoor graph (the semantic layer, the rows through Virtual
Graph, memory), commands against the BigQuery warehouse as the `qlsc` service account. Nothing is mocked and nothing is replayed. The router's trace is the same
idea for a request: the steps of a real `qlsc ask` streamed into a thought log as they happen.

### Component types

| Component | What it is | Where it sits |
|---|---|---|
| **Run expander** | The left-edge control, the query or command it opens, Run, and the result as a graph (NVL) or a table; it knows its database and, where it matters, its principal | every section: the layer (discovery), rows through Virtual Graph, memory, the same query as each principal (security) |
| **ThoughtLog** | The steps of one request as they happen: what was tried, what it returned or why it declined, with the cost of each | the router's trace first; then memory (fetch, then the local read) and security (the signed request through the driver) |
| **SideBySide** | The same question run two ways, each with its metric cards (tool calls, tokens, seconds, warehouse queries) | accuracy (the methods), memory (BigQuery against memory) |
| **AskBar** | A question box with "Try ..." suggestions | router, accuracy |
| **PrincipalPicker** | Who is asking; it feeds the others | security, memory |

### What live needs

The app is static today: no server, no secrets. Live makes it a small server in front of Neo4j and BigQuery, and these shape it:

- **What a visitor may run.** The queries and commands the page shows (the files in `queries/`, with the parameters the page offers), or any text typed into the box.
  Free text against a public database needs a read-only user, row and time limits, and for SQL a cap on bytes billed. Named ones need none of that. Open question.
- **Credentials stay on the server**, and BigQuery is reached as the `qlsc` service account, never a personal one. A principal's run goes through the real signed
  pass-through (`entitle.token`), so the security section runs for real, refusals included.
- **Spend and abuse.** A rate limit, a bytes-billed cap on every BigQuery job, a timeout, and a ceiling on model spend per visitor for anything that calls one (`ask`).
- **Where the databases run.** Neo4j and Virtual Graph are Docker containers on this machine. A public page needs them hosted (or tunnelled), with the layer
  reviewed first: it holds no warehouse rows, but it does hold the log's principals and the literal values queries filtered on. Fennmoor's are synthetic.
- **The measured results stay measured.** The accuracy figures come from an hour of runs and about $25; they are not re-run on page load, and the page says they
  are recorded. What goes live there is one question through the methods, which is a call a visitor waits for and pays for.
- **The router's thought log** needs each rung's outcome as it happens. To confirm: whether `navigate.answer_routed` (`src/qlsc/navigate.py:709`) exposes it. If it only
  returns at the end, the change is an optional progress callback, a refactor that must not change results (CLAUDE.md: run `eval/fingerprint.py` around it).
- **Comparison runs kept counts, not transcripts** (tokens, seconds, LLM calls, tool calls by kind: for Q01, 1 `list_tables`, 9 `describe_table`, 14 `run_sql`,
  1 `submit`). Live runs would capture the steps as they go, so this stops being a limit.

NVL is the visualization library (`@neo4j-nvl/react`); check its licence terms and its bundle size before committing to it, and keep the schema graphs as they are
unless NVL reproduces their layered layout.

### The Cypher and the calls each section would use

Cypher is in `ui/src/examples/fennmoor/queries/` when a generator already runs it, and in `examples/fennmoor-bank/demo.cypher` (26 queries, each tested, each
returning paths so they draw as graphs) when it is a candidate for the Run expander. Paths are from the repo root; lines are as of commit `363c1d5`.

| Section | Cypher | Calls (a recording, or live where noted) |
|---|---|---|
| Discovery | `demo.cypher` 2.3 (the joins behind one variable), 2.5 (joins kept out), 3.3 (one area, top to bottom), 3.5 (nearest groups by vector index), 3.6 (from meaning to data); the six in `queries/discovery/` | `qlsc build` stages in order (`src/qlsc/cli.py:62`): `parse.run`, `load.run`, `variables.run`, `computations.run`, `cluster.run`, `hierarchy.run`, `align.run`, `requests.run`; each prints what it kept |
| Virtual Graph | `demo.cypher` 5.1, 5.2 (the evidence for each relationship); `queries/virtual/`; the composite query `examples/fennmoor-bank/demo.py:26` (the layer and live rows in one statement, signed) | `qlsc virtualize` (`src/qlsc/virtualize.py:380`): `nodes` 137, `relationships` 179, `names` 213 (the model's naming), `schema_json` 287, `render` 338. The ten questions are `eval/graph_questions.yaml`, run by `eval/graph_accuracy.py:28` |
| Router | the Cypher the model writes for a graph-shaped question (`results/graph_accuracy.json`, shown in the trace) | `qlsc ask "..." --run` over `navigate.answer_routed` (`src/qlsc/navigate.py:709`): `route` 644, `stands` 629, `ROUTES` 626, then each rung: `answer_memory` 664, `answer_precedent` 798, `answer_compiled` 526, `answer_cypher` 854, `answer_free` 557. Cost and time per call: `meter.measure` (`src/qlsc/meter.py:81`). `demo.py` `exchange` (line 106) already prints "first ask, the same ask again, after a rejection" |
| Memory | `queries/memory/`; the reads a template generates (`memory.cypher`, `src/qlsc/memory.py:399`) | `memory.template` 362, `run_batch` 479, `recall` 761, `recall_batch` 774, `write` 642, `holds_until` 616, `cadence_days` 609, `answerable` 994; `qlsc recall Customer cif_number=...`. The paired timing is `eval/economics.py:121` |
| Accuracy | none | `eval/comparison/run.py:188` (`run`), `trace_of` 108; the judge is `eval/match.py:237` (`judge`), `compare` 73. A recorded question per method |
| Security | the same Cypher as each principal (`$qlsc_principal`); `demo.py` 26 and 70 | `entitle.allowlist` (`src/qlsc/entitle.py:103`), `token` 214, `signed` 226, `signing` 268, `enforced` 252; the driver's `materialize` (`vg-passthrough/src/qlsc/passthrough/Passthrough.java:174`). The three refusals are `eval/entitlements.py:380` (`driver_probes`) and the four broken gateways `:409` (`broken`) |

### Where the Cypher lives (done)

Twelve queries were string constants inside three generators. They are now one file each, `ui/src/examples/fennmoor/queries/<section>/<name>.cypher`, with the
database, parameters and meaning in a comment at the top, read by `examples/fennmoor-bank/generate/ui_queries.py`. The page can import the same file to show
it (`?raw`), so the query on the page and the one that made its numbers cannot drift. It stays in the UI tree, not the example's, because the page is deployed
from `ui/`, and an import from outside it would not build there. The Run expander's server reads the same files.

Left where it is: the tool's own Cypher (some 70 query constants in 18 modules of `src/qlsc/`), which CLAUDE.md puts in the module that uses it, and which a refactor must
not change the results of; and `demo.cypher`, which Browser users and `tests/test_demo_cypher.py` already depend on. When the Run expander needs one of
those, the file goes into `queries/` and `demo.cypher` keeps its copy only if a test compares them; otherwise `demo.cypher` should be generated from `queries/`.
That is a decision for the Run expander's step, not this one.

## Links from each section header to the code

A row of links at each section's header, to the functions that do the work. The paths and lines below are verified against this commit; the repository is
`https://github.com/jeffneo/semantic-context`, and a link is `.../blob/<ref>/<path>#L<line>`.

| Section | Links |
|---|---|
| The scenario, the warehouse | `examples/fennmoor-bank/estate.yaml`; `src/qlsc/extract.py:46` (`extract_log`), `:125` (`extract_catalog`); `src/qlsc/warehouse/bigquery.py`; `examples/fennmoor-bank/generate/make_catalog.py` |
| Discovery | `src/qlsc/cli.py:62` (`build`); `parser/qlsc_parse/fingerprint.py:68`, `resolve.py` (what a query reads and joins); `src/qlsc/joins.py:161` (`judge_joins`), `:81` (`IdSpaces`); `src/qlsc/variables.py:55` (`components`); `src/qlsc/cluster.py:201` (`run`), `:108` (`leiden`); `src/qlsc/hierarchy.py:150` (`run`), `:102` (`knn`) |
| Virtual Graph | `src/qlsc/virtualize.py:380` (`run`), `:137`, `:179`, `:213`, `:287`, `:338`; `examples/fennmoor-bank/eval/graph_questions.yaml` |
| Router | `src/qlsc/navigate.py:626` (`ROUTES`), `:644` (`route`), `:709` (`answer_routed`); `src/qlsc/compile.py:830` (`compile_sql`); `src/qlsc/requests.py:112` |
| Memory | `src/qlsc/memory.py:362` (`template`), `:479` (`run_batch`), `:609` (`cadence_days`), `:761` (`recall`), `:994` (`answerable`) |
| Accuracy | `examples/fennmoor-bank/eval/comparison/run.py:188`, its `README.md`; `eval/match.py:237` |
| Row-level security | `src/qlsc/entitle.py:103`, `:214`, `:226`, `:268`; `vg-passthrough/src/qlsc/passthrough/Passthrough.java:174`, `Token.java:29` (`verify`), `Rewrite.java:20`; `examples/fennmoor-bank/entitlements/setup.py:271` (`row_policies`); `eval/entitlements.py:380`, `:409` |

Line numbers drift. Decided: links name a commit (a constant in `src/repo.ts`, bumped when the page is released). They were tested against GitHub at `363c1d5`: every file and line in
this plan resolves and holds the symbol named. The check should stay a script run beside the UI's build, in the way `tests/test_boundary.py` checks the tool, so a
bump that moves a line fails there. A link to a function name with no
line, where the file has one definition, never goes stale.

## Decisions

Decided (2026-10-07):

1. **Four maps stay**, one per section.
2. **Live, not mocked or replayed**: a left-edge expander per section and component that shows the query or command and runs it against the real Fennmoor graph
   or BigQuery warehouse.
3. **The router's thought log is live**, and is where the ThoughtLog component starts.
4. **No "concept demo" mark** in the header.
5. **Links name a commit**, tested.
6. **The ten Cypher questions stay in every section they appear in** (Virtual Graph and router).

Still to decide, before the Run expander is built:

- Named queries only, or free text too (see What live needs).
- Where the databases are hosted for a public page, and who pays for the spend caps.
- Whether each section's main component and collapsed items are as proposed above (nothing said yet).

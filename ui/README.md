# ui/

The context engine demo's front end. A static single-page app: Vite, React 19, TypeScript, Tailwind v4. The page reads recorded JSON, written from the
example's evaluation results by `examples/fennmoor-bank/generate/ui_*.py`, so it needs no server to be read. Its **Run this live** controls (a query or a
`qlsc` command beside each part, chosen from the page's examples and run for real, read-only) go through a small local server, `uv run examples/fennmoor-bank/server.py`, run from the
repository root; Vite proxies `/api` to it. It needs the example's Neo4j databases, Virtual Graph and BigQuery access, and refuses anything that writes.

```bash
cd ui
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc, then a static dist/ (served from the root of a site: see Hosting)
```

Node: the latest (26 at the time of writing; `.nvmrc` says so: `nvm use`). The key packages are on their latest majors: Vite 8, React 19, TypeScript 7,
Tailwind 4. Vite 8 needs Node 20.19 or newer, or 22.12 or newer.

## Why this kit

Static hosting first, Python API only (decided 2026-10-06): no SSR, no API routes, so Next.js would add a server to run and secure for nothing. Vite is the
lightest scaffold that keeps the option to move to Next later: the components are plain React, and the one router import (react-router) is confined to the
routes, the nav and the example page.
Neo4j's graph library (NVL) will be added for graph canvases only; the rest is our own minimal components so a brand is a theme file.

## Colours: one file, injectable

Every colour is a CSS variable in [`src/theme/tokens.css`](src/theme/tokens.css), in three groups so a brand can be injected selectively:

| Group | Tokens | Brand it? |
|---|---|---|
| SURFACE | `--bg`, `--fg`, `--fg-muted`, `--line`... | usually not (the clean, neutral look) |
| ACTION | `--accent`, `--link`, `--focus` | yes: this is where a brand colour goes |
| SHARDS | `--shard-semantic`, `--shard-rows`, `--shard-memory`, `--composite`, `--warehouse` | the diagram's colours, one per Neo4j shard, the deck's too |
| STATUS | `--ok`, `--bad` | right and wrong answers (the accuracy charts) |
| AREAS | `--area-1` to `--area-4` | four categorical colours for the semantic layer's broad areas; kept apart from the shards' and the status colours |

A brand theme is a `[data-theme="name"]` block in `src/theme/themes/`, and `?theme=name` switches to it (remembered). `themes/neo4j.css` is a
**placeholder**: only ACTION is overridden, and its values are not the official palette. Replace them with Neo4j's tokens. Light and dark are a separate axis
(`?mode=light|dark|system`; **light by default for now**; the nav's button toggles it).

Tailwind utilities read the tokens (`bg-bg`, `text-fg-muted`, `border-line`, `text-shard-semantic`), so no component names a colour.

## Pages

| Path | Page |
|---|---|
| `/` | The landing page: the name and the architecture diagram, filling the viewport. Nothing under it |
| `/examples` | Goes to the example (to a list of them once there are several) |
| `/examples/:slug` | An example's page: its own header, the contents down the left, the sections down the page. `/examples/fennmoor` is the first |

An example is a folder under `src/examples/<slug>/` whose `index.tsx` default-exports an `Example` ([types.ts](src/examples/types.ts)): a name, a line, the figures
for its header, and sections in groups. The page and its contents sidebar are the same for every example. To add one: the folder, and a line each in
[`examples/index.ts`](src/examples/index.ts)'s list and loaders. An example loads when its page opens, so its data stays out of the landing page's download.
A section with no `Body` is listed as "soon"; give it a `Body` when its visualization is built.

Each Fennmoor section that draws real results has its data written by a generator in `examples/fennmoor-bank/generate/`, from what the example already
measured or built. Nothing is mocked, and none of the spec's answer key or the physical GCP project name reaches the page. Run each after the stage it reads:

| Section | Data | Generator | Reads |
|---|---|---|---|
| The warehouse | `fennmoor/warehouse.json` | `ui_warehouse.py` | the catalog extract (`qlsc extract`) |
| Discovering the semantic layer | `fennmoor/discovery/discovery.json` | `ui_discovery.py` | the semantic layer's graph (`qlsc build`, Neo4j up) |
| Generating the Virtual Graph schema | `fennmoor/virtual/virtual.json` | `ui_virtual.py` | `qlsc virtualize`'s files in `work/virtual/` and the graph (Neo4j up), and `results/graph_accuracy.json` |
| Routing a request | `fennmoor/router/router.json` | `ui_router.py` | the evaluations' results (`results/economics.json`, `log_accuracy.json`, `graph_accuracy.json`) and the comparison's agent run |
| Promoting results to memory | `fennmoor/memory/memory.json` | `ui_memory.py` | `qlsc.memory.template` over the generated model, the layer's write cadences and a remembered node (Neo4j up), and the memory evaluations' results (`results/memory*.json`, `economics.json`) |
| Row-level security, passed through | `fennmoor/security/security.json` | `ui_security.py` | the entitlement evaluation's results and run (`results/entitlements.json`, `work/entitlements/`) and the allowlists the warehouse produced (`work/allowlists/`) |
| Accuracy | `fennmoor/accuracy/accuracy.json` | `ui_accuracy.py` | the comparison's results (`eval/comparison/run.py report`) |

```bash
uv run examples/fennmoor-bank/generate/ui_warehouse.py
uv run examples/fennmoor-bank/generate/ui_discovery.py
uv run examples/fennmoor-bank/generate/ui_virtual.py
uv run examples/fennmoor-bank/generate/ui_router.py
uv run examples/fennmoor-bank/generate/ui_memory.py
uv run examples/fennmoor-bank/generate/ui_security.py
uv run examples/fennmoor-bank/generate/ui_accuracy.py
```

Each section lists the code that does its work, linked to a commit (`src/examples/fennmoor/code-links.json`; a branch's lines move). After code changes, push, then
`uv run examples/fennmoor-bank/generate/ui_code_links.py` re-pins the links to `origin/main` and moves each to its symbol's new line (`--check` only reports);
`tests/test_code_links.py` fails when a link is off its line.

The Cypher those generators run is one file each in [`fennmoor/queries/`](src/examples/fennmoor/queries/README.md), so a query the page shows and the one that
made its data are the same file.

The discovery, Virtual Graph, router, memory, security and accuracy sections load their data when the section mounts (the accuracy file is the largest: every query the methods wrote),
so the page opens before they arrive.

```
src/
  App.tsx, main.tsx             the routes (react-router)
  pages/                        ExamplePage (the shell every example uses), NotFound
  components/                   Nav, Hero, SectionNav (the contents sidebar), ArchitectureDiagram (the hero: agents; the composite as the box around the three
                                shards; the warehouse across the bottom; arcs between the shards; tasks run one at a time, each flashing along the connections
                                and layers it uses and fading slowly; SVG, no tooltip, nothing follows the pointer)
  examples/                     the list and loaders; fennmoor/ holds its data, EstateTiles (the estate's squares, for a section to colour) and queries/ (the Cypher, a file each) and a folder or file per section: Scenario, Warehouse, discovery/
                                (funnel, the tables regrouped by meaning, the join chords), virtual/ (the steps, the .semantic paths beside the .rows schema, the generated schema as a layered graph, the questions it
                                answers), router/ (the ladder, ten questions followed down it, what each rung served), memory/ (the template drawn on the schema,
                                what promotion buys, how long it holds, how it stays governed), security/ (what each principal may read, the same question
                                asked as each, the pass-through's pipeline and its refusals, the checks), accuracy/ (scores, the question wall, costs, outcomes)
  repo.ts                       the repository the header links to
  live/                         the live panels: the control at a part's left, its query or command, the result as a graph (NVL) or table; api.ts talks to the demo server
  theme/                        tokens, brand themes, the theme hook
```

## Configuration

`NEO4J_CONTACT_EMAIL` is the contact shown, as plain text, beside the light/dark button (nothing is shown when it is unset). Put it in `ui/.env.local`
(ignored by git; [`.env.example`](.env.example) is the template) or in the host's environment, and it is compiled into the page when the app is built or
served. Only `NEO4J_CONTACT_*` and `VITE_*` variables reach the browser (`envPrefix` in `vite.config.ts`): a bare `NEO4J_` would expose `NEO4J_PASSWORD`.

## Running it live

The information in every section is the recorded evidence, drawn from the generators' data; it is never re-run when a page loads. Beside it, each part has a
control at its left (live/LiveRun.tsx) that opens to the right on the query or command behind that part, with **Run**. The query is a default: change it and run
the change. It goes to the real graph or warehouse and shows the result in place, as a graph (NVL) or a table, or, for a command, as the output prints.

The page cannot hold a database password or reach Bolt, so it talks to a small server on this machine, `examples/fennmoor-bank/server.py` (standard library only;
Vite proxies `/api` to it). Start it from the repository root, beside `npm run dev`:

```bash
uv run examples/fennmoor-bank/server.py        # http://127.0.0.1:8787; QLSC_DEMO_PORT changes the port
```

It uses the example's own configuration: the database addresses are `estate.yaml`'s (`neo4j`, `virtualize.neo4j`), the passwords are `.env`'s (`NEO4J_PASSWORD`),
BigQuery is the estate's connector as the `qlsc` service account. Nothing of it reaches the browser, and there is nothing new to set. The services it needs are
the ones the example already runs: Neo4j, Virtual Graph (and its composite), and a BigQuery login for SQL and commands.

| Where a query goes | What it is |
|---|---|
| `layer` | the semantic layer (`bigquery` database) |
| `memory` | what Virtual Graph reads fetched |
| `rows` | the warehouse's rows as a graph, through Virtual Graph (the gateway signs the query) |
| `composite` | one query across all of them (`USE fennmoor.rows ...`) |
| SQL | one SELECT in BigQuery, in the graph's table names |
| commands | `qlsc ask`, `recall`, and the example's `demo.py` composite and exchange, with their arguments |

**Only reads.** A Cypher session is opened with read access, so Neo4j itself refuses a write, whatever the text says; procedures that reach out of the database
(files, URLs, administration) are refused before they are sent; SQL must be a single query statement, bills at most `navigate.maximum_bytes_billed`, and every query
has a time limit and a row limit. Commands are a fixed list run as argument lists, never a shell. `recall` keeps what it fetched in memory: that is what it is for.
The server answers only this machine, and only a page served from it.

**Who is asking.** The default is `admin`, the data source's own identity: the administrator's view. On `rows` and in SQL a panel can run as another principal
(marketing, risk, contact-center): the query is signed for them and Virtual Graph's pass-through runs it as their service account, so the warehouse's own row
and column rules apply, and its refusals are shown as they are. The security section's panels offer the picker, and an "unsigned" option that shows the
pass-through refusing a query with no principal. The layer and memory hold the estate's metadata, not its rows: they are the administrator's view.

The queries each part opens with are the files in [`queries/`](src/examples/fennmoor/queries/README.md), registered in `src/examples/fennmoor/live.ts`. Without
the server a panel says so and how to start it.

## Hosting

`dist/` is plain files, but pages have real paths, so the host must send unknown paths to `index.html`. [`vercel.json`](vercel.json) does it for Vercel (set
`NEO4J_CONTACT_EMAIL` in the project's environment variables); `vite` and `vite preview` do it already; any other host needs the same rule (a bucket: set
the 404 page to `index.html`).

## Rules

- Every number on a page is either counted from the data it draws (the example's header and scenario) or measured by qlsc's own evaluations and cited
  to its file with the caveat that travels with it. Nothing is mocked: what a page shows is recorded evidence, and what its live panel runs is real.
- The first screen is the name and the diagram, filling the viewport, and the landing page is only that.
- Keep it static and light: no state library; the router is the only dependency beyond React.

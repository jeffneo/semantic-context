# ui/

The context engine demo's front end. A static single-page app: Vite, React 19, TypeScript, Tailwind v4. No server of its own: the replay demo
will read recorded JSON, and Live mode will call the qlsc Python API.

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

Fennmoor's warehouse (the squares, the schema panel) draws `src/examples/fennmoor/warehouse.json`: BigQuery's catalog as qlsc extracted it, with nothing of the
spec's answer key and the logical Fennmoor project names. Regenerate it after `qlsc extract` and `generate/build.py`:

```bash
uv run examples/fennmoor-bank/generate/ui_warehouse.py
```

```
src/
  App.tsx, main.tsx             the routes (react-router)
  pages/                        ExamplePage (the shell every example uses), NotFound
  components/                   Nav, Hero, SectionNav (the contents sidebar), ArchitectureDiagram (the hero: agents; the composite as the box around the three
                                shards; the warehouse across the bottom; arcs between the shards; tasks run one at a time, each flashing along the connections
                                and layers it uses and fading slowly; SVG, no tooltip, nothing follows the pointer)
  examples/                     the list and loaders; fennmoor/ holds its data, Scenario, Warehouse, TableSchema and its sections
  theme/                        tokens, brand themes, the theme hook
```

## Configuration

`NEO4J_CONTACT_EMAIL` is the contact shown, as plain text, beside the light/dark button (nothing is shown when it is unset). Put it in `ui/.env.local`
(ignored by git; [`.env.example`](.env.example) is the template) or in the host's environment, and it is compiled into the page when the app is built or
served. Only `NEO4J_CONTACT_*` and `VITE_*` variables reach the browser (`envPrefix` in `vite.config.ts`): a bare `NEO4J_` would expose `NEO4J_PASSWORD`.

## Hosting

`dist/` is plain files, but pages have real paths, so the host must send unknown paths to `index.html`. [`vercel.json`](vercel.json) does it for Vercel (set
`NEO4J_CONTACT_EMAIL` in the project's environment variables); `vite` and `vite preview` do it already; any other host needs the same rule (a bucket: set
the 404 page to `index.html`).

## Rules

- Every number on a page is either counted from the data it draws (the example's header and scenario) or measured by qlsc's own evaluations and cited
  to its file with the caveat that travels with it. Nothing is mocked: the demos that follow replay real recorded runs.
- The first screen is the name and the diagram, filling the viewport, and the landing page is only that.
- Keep it static and light: no state library; the router is the only dependency beyond React.

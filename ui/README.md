# ui/

The context engine demo's front end. A static single-page app: Vite, React 19, TypeScript, Tailwind v4. No server of its own: the replay demo
will read recorded JSON, and Live mode will call the qlsc Python API.

```bash
cd ui
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc, then a static dist/ (base "./": serve it from any path)
```

Node: the latest (26 at the time of writing; `.nvmrc` says so: `nvm use`). The key packages are on their latest majors: Vite 8, React 19, TypeScript 7,
Tailwind 4. Vite 8 needs Node 20.19 or newer, or 22.12 or newer.

## Why this kit

Static hosting first, Python API only (decided 2026-10-06): no SSR, no API routes, so Next.js would add a server to run and secure for nothing. Vite is the
lightest scaffold that keeps the option to move to Next later: the components are plain React and nothing here imports a framework router.
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

## Layout

```
src/
  App.tsx                       the landing page
  components/ArchitectureDiagram.tsx   the hero: agents; the composite as the box around the three shards; the warehouse across the bottom;
                                arcs between the shards; tasks run one at a time, each flashing along the connections and layers it uses and fading slowly (SVG; no tooltip, nothing follows the pointer)
  components/{Nav,Hero,Evidence,HowItWorks,Footer}.tsx
  content/proof.ts              every figure on the page, with its source file in the repository: change a number here, never in a component
  theme/                        tokens, brand themes, the theme hook
```

## Rules

- Every number on the page is measured by qlsc's own evaluations and cites its file in `content/proof.ts`; the caveat travels with them.
  Nothing is mocked: the demo that follows replays real recorded runs.
- The first screen is the name and the diagram, filling the viewport: nothing else above the fold.
- Keep it static and light: no state library, no router until a second page needs one.

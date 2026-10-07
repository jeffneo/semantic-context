import { useEffect, useState } from "react";

/*
  The context engine on a page. Agents on top; below them the composite database, drawn as the box around the three shards it
  queries as one (semantic layer, virtual graph, agent memory); the warehouse runs across the bottom. Arcs between the shards show
  how they interface.

  The diagram is still until something happens: one task at a time runs, its path flashing along the connections and layers it
  uses and fading slowly behind it, then the next, in a loop. Nothing follows the pointer.

  Colours are the deck's (tokens in theme/tokens.css): semantic layer blue, virtual graph (rows) orange, agent memory green,
  composite purple, warehouse grey. A solid card stores data; a dashed one stores nothing.
*/

type Id = "agent" | "composite" | "semantic" | "rows" | "memory" | "warehouse";
type Tone = "sem" | "rows" | "mem" | "wh" | "agent";

const COLOR: Record<Tone, string> = {
  sem: "var(--shard-semantic)",
  rows: "var(--shard-rows)",
  mem: "var(--shard-memory)",
  wh: "var(--warehouse)",
  agent: "var(--fg-muted)",
};
const COMP = "var(--composite)";

// what each layer is, for the narrow-screen list (the wide diagram has no tooltip: it is tasks that explain it)
const INFO: Record<Id, { title: string; text: string; fact: string }> = {
  agent: {
    title: "AI agents",
    text: "Ask a question, recall an entity's context, remember what was learned. Every call acts as the person it serves; the warehouse's own rules decide what comes back.",
    fact: "Example: 0 row incidents across 3 principals and 60 questions",
  },
  composite: {
    title: "Composite database",
    text: "One Cypher query across the layer, the rows and the memory. It stores nothing; it is the only place the three meet.",
    fact: "Three aliases: semantic · rows · memory",
  },
  semantic: {
    title: "Semantic layer",
    text: "What the business's own queries say its data means: the Variables joined columns share, its business areas, the measures it computes again and again.",
    fact: "Example: 50 Variables · 1,185 Computations · 1,092 requests",
  },
  rows: {
    title: "Virtual graph",
    text: "The warehouse's live rows as a graph, queried in Cypher and translated to SQL at query time. Its model is derived from usage, not drawn. Zero copy.",
    fact: "Example: 11 labels and 14 relationship types, derived",
  },
  memory: {
    title: "Agent memory",
    text: "What an agent fetched and kept, with when, by whom and how long it holds, and what it learned. A repeat read is local.",
    fact: "Example: a repeat read in 0.05 s, against 0.7 s for the query",
  },
  warehouse: {
    title: "Your data warehouse",
    text: "Stays where it is. The engine reads its query log and catalog once, and its rows only at query time. Nothing is copied out.",
    fact: "Example: a synthetic bank, 324 tables, 315,729 jobs in 90 days",
  },
};

interface Edge {
  id: string;
  d: string;
  /** the same path the other way, for a step that runs against the connection's drawn direction */
  dRev?: string;
  from: Tone;
  to: Tone;
  /** the gradient's axis, in diagram coordinates (a straight line has no bounding box to take it from) */
  axis: [number, number, number, number];
  both?: boolean;
  label?: { x: number; y: number; text: string; anchor?: "start" | "middle" | "end" };
}

const EDGES: Record<string, Edge> = {
  // the shards with one another: arcs over the cards, inside the composite
  derive: { id: "derive", d: "M330 296 C330 226 700 226 700 296", from: "sem", to: "rows", axis: [330, 0, 700, 0], label: { x: 515, y: 284, text: "derives its model", anchor: "middle" } },
  recall: { id: "recall", d: "M900 296 C900 226 1270 226 1270 296", from: "rows", to: "mem", axis: [900, 0, 1270, 0], label: { x: 1085, y: 284, text: "recall: fetch and keep", anchor: "middle" } },
  fresh: { id: "fresh", d: "M230 296 C230 186 1370 186 1370 296", from: "sem", to: "mem", axis: [230, 0, 1370, 0], label: { x: 800, y: 199, text: "holds until: from the log's cadence", anchor: "middle" } },
  // the warehouse with the layer and the rows
  log: { id: "log", d: "M470 766 V526", from: "wh", to: "sem", axis: [0, 766, 0, 526], label: { x: 486, y: 664, text: "extract · build", anchor: "start" } },
  sql: { id: "sql", d: "M800 766 V526", dRev: "M800 526 V766", from: "wh", to: "rows", axis: [0, 766, 0, 526], both: true, label: { x: 816, y: 664, text: "SQL at query time", anchor: "start" } },
  views: { id: "views", d: "M1155 800 H940", from: "wh", to: "wh", axis: [1155, 0, 940, 0], label: { x: 1047, y: 788, text: "views over", anchor: "middle" } },
  // the agents into the composite
  agent: { id: "agent", d: "M800 104 V168", dRev: "M800 168 V104", from: "agent", to: "agent", axis: [0, 104, 0, 168], both: true },
};

/** where each layer's card sits, for its halo */
const BOX: Record<Exclude<Id, "composite">, { x: number; y: number; w: number; h: number; r: number; tone: Tone }> = {
  agent: { x: 500, y: 16, w: 600, h: 88, r: 18, tone: "agent" },
  semantic: { x: 80, y: 296, w: 450, h: 230, r: 18, tone: "sem" },
  rows: { x: 575, y: 296, w: 450, h: 230, r: 18, tone: "rows" },
  memory: { x: 1070, y: 296, w: 450, h: 230, r: 18, tone: "mem" },
  warehouse: { x: 40, y: 700, w: 1520, h: 184, r: 22, tone: "wh" },
};

/** One step of a task: a connection flashes (against its drawn direction if `rev`), or a layer does. */
type Step = { edge: string; rev?: boolean } | { node: Exclude<Id, "composite"> };

interface Task {
  name: string;
  detail: string;
  steps: Step[];
}

/*
  The tasks, each the path the real system takes for it. They loop in this order, one at a time.
  `ask` finds context in the layer, then reads the live rows; `recall` fetches an entity's context and keeps it; a repeat `ask` never
  leaves memory; `remember` keeps what was learned, for as long as the log says it holds; and the layer builds itself from the log.
*/
const TASKS: Task[] = [
  {
    name: "Ask a question",
    detail: "find context · compile · run as the principal",
    steps: [{ edge: "agent" }, { node: "semantic" }, { edge: "derive" }, { node: "rows" }, { edge: "sql" }, { node: "warehouse" }, { edge: "sql", rev: true }, { edge: "agent", rev: true }],
  },
  {
    name: "Recall a customer",
    detail: "fetch the context once, keep it with its provenance",
    steps: [{ edge: "agent" }, { node: "rows" }, { edge: "sql" }, { node: "warehouse" }, { edge: "sql", rev: true }, { edge: "recall" }, { node: "memory" }, { edge: "agent", rev: true }],
  },
  {
    name: "Ask it again",
    detail: "answered from memory: no warehouse, no model",
    steps: [{ edge: "agent" }, { node: "memory" }, { edge: "agent", rev: true }],
  },
  {
    name: "Remember what was learned",
    detail: "kept until the log says the data changes",
    steps: [{ edge: "agent" }, { node: "memory" }, { node: "semantic" }, { edge: "fresh" }],
  },
  {
    name: "The layer builds itself",
    detail: "from the warehouse's own query log, once",
    steps: [{ node: "warehouse" }, { edge: "views" }, { edge: "log" }, { node: "semantic" }, { edge: "derive" }, { node: "rows" }],
  },
];

const STEP_S = 0.4; // seconds between one step lighting and the next: the flash travels
const FADE_S = 1.9; // how long a step takes to fade: rapid flash, slow fade
const REST_S = 1.0; // after the last step starts, before the next task begins

function Marker({ tone }: { tone: Tone }) {
  return (
    <marker id={`arr-${tone}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M1 1.5 L8.5 5 L1 8.5 z" style={{ fill: COLOR[tone] }} />
    </marker>
  );
}

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export default function ArchitectureDiagram() {
  // `tick` counts every task run, so a task that comes round again restarts its animations; `idx` is which task
  const [tick, setTick] = useState(0);
  const idx = tick % TASKS.length;
  const task = TASKS[idx];
  const still = reducedMotion();

  useEffect(() => {
    if (still) return;
    const ms = (task.steps.length * STEP_S + REST_S) * 1000;
    const t = window.setTimeout(() => setTick((n) => n + 1), ms);
    return () => window.clearTimeout(t);
  }, [tick, task, still]);

  // render functions, not components: defined here, a component would remount on every state change
  const shard = (id: Id, x: number, tone: Tone, title: string, alias: string, tag: string, lines: string[], dashed = false) => {
    const tagW = tag.length * 8.2 + 24;
    const aliasW = alias.length * 9 + 26;
    return (
      <g key={id} className="dg-node" style={{ ["--c" as string]: COLOR[tone] }} data-dashed={dashed}>
        <rect className="card" x={x} y={296} width={450} height={230} rx={18} />
        <text x={x + 28} y={346} fontSize={26} fontWeight={600}>
          {title}
        </text>
        <rect className="tag" x={x + 450 - 28 - tagW} y={322} width={tagW} height={28} rx={14} />
        <text className="tagtext mono" x={x + 450 - 28 - tagW / 2} y={341} fontSize={14} textAnchor="middle">
          {tag}
        </text>
        <rect className="alias" x={x + 28} y={362} width={aliasW} height={26} rx={13} />
        <text className="aliastext mono" x={x + 28 + aliasW / 2} y={380} fontSize={14.5} textAnchor="middle">
          {alias}
        </text>
        {lines.map((l, i) => (
          <text key={l} className="muted" x={x + 28} y={426 + i * 29} fontSize={18.5}>
            {l}
          </text>
        ))}
      </g>
    );
  };

  const item = (cx: number, title: string, sub: string) => (
    <g key={title}>
      <rect className="item" x={cx - 140} y={766} width={280} height={68} rx={12} />
      <text x={cx - 118} y={795} fontSize={18.5} fontWeight={600}>
        {title}
      </text>
      <text className="muted" x={cx - 118} y={819} fontSize={14.5}>
        {sub}
      </text>
    </g>
  );

  const chip = (x: number, w: number, text: string) => (
    <g key={text}>
      <rect x={x} y={44} width={w} height={32} rx={16} className="dg-pill" />
      <text className="mono" x={x + w / 2} y={65} fontSize={14.5} textAnchor="middle">
        {text}
      </text>
    </g>
  );

  /** the standing connection: faint, with its arrowheads and its label */
  const edge = (e: Edge) => (
    <g key={e.id} className="dg-edge">
      <path className="base" d={e.d} style={{ stroke: `url(#grad-${e.id})` }} markerEnd={`url(#arr-${e.to})`} markerStart={e.both ? `url(#arr-${e.from})` : undefined} />
      {e.label && (
        <text className="elabel" x={e.label.x} y={e.label.y} textAnchor={e.label.anchor ?? "middle"}>
          {e.label.text}
        </text>
      )}
    </g>
  );

  /** one step of the running task: a rapid flash along the connection, or around the layer, and a slow fade */
  const light = (s: Step, i: number) => {
    const delay = `${i * STEP_S}s`;
    const key = `${tick}-${i}`;
    if ("node" in s) {
      const b = BOX[s.node];
      return (
        <rect
          key={key}
          className="halo"
          x={b.x}
          y={b.y}
          width={b.w}
          height={b.h}
          rx={b.r}
          filter="url(#glow)"
          style={{ ["--c" as string]: COLOR[b.tone], animationDelay: delay, animationDuration: `${FADE_S}s` }}
        />
      );
    }
    const e = EDGES[s.edge];
    const d = s.rev && e.dRev ? e.dRev : e.d;
    const common = { d, pathLength: 100, style: { animationDelay: delay, animationDuration: `${FADE_S}s` } };
    return (
      <g key={key}>
        <path className="lit" {...common} filter="url(#glow)" style={{ ...common.style, stroke: `url(#grad-${e.id})` }} />
        <path className="lit-core" {...common} style={{ ...common.style, animationDuration: `${FADE_S * 0.7}s` }} />
      </g>
    );
  };

  return (
    <div className="h-full w-full">
      {/* wide screens: the diagram, filling the space it is given */}
      <svg
        className="dg hidden h-full w-full md:block"
        viewBox="0 0 1600 900"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        // a label, not a <title>: a <title> child shows as the browser's own tooltip on hover
        aria-label="The context engine: agents query a composite database, which is the box around three shards: a semantic layer, a virtual graph over the warehouse's rows, and agent memory. The warehouse runs across the bottom. Tasks run in turn: ask a question, recall a customer, ask it again, remember what was learned, and the layer building itself from the query log."
      >
        <defs>
          {(["sem", "rows", "mem", "wh", "agent"] as Tone[]).map((t) => (
            <Marker key={t} tone={t} />
          ))}
          <filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1600" height="900">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {Object.values(EDGES).map((e) => (
            <linearGradient key={e.id} id={`grad-${e.id}`} gradientUnits="userSpaceOnUse" x1={e.axis[0]} y1={e.axis[1]} x2={e.axis[2]} y2={e.axis[3]}>
              <stop offset="0" style={{ stopColor: COLOR[e.from] }} />
              <stop offset="1" style={{ stopColor: COLOR[e.to] }} />
            </linearGradient>
          ))}
        </defs>

        {/* legend (top left) and the task running (top right): small, and out of the way of the diagram */}
        <g aria-hidden="true">
          <rect className="lg-solid" x={40} y={22} width={30} height={18} rx={5} />
          <text className="muted" x={82} y={36} fontSize={15}>
            stores data
          </text>
          <rect className="lg-dashed" x={40} y={48} width={30} height={18} rx={5} />
          <text className="muted" x={82} y={62} fontSize={15}>
            stores nothing
          </text>
        </g>
        {!still && (
          <g key={`label-${tick}`} className="task-label" aria-hidden="true">
            <text x={1560} y={44} fontSize={21} fontWeight={600} textAnchor="end">
              {task.name}
            </text>
            <text className="muted" x={1560} y={69} fontSize={15} textAnchor="end">
              {task.detail}
            </text>
            {TASKS.map((_, i) => (
              <circle key={i} className={i === idx ? "dot on" : "dot"} cx={1560 - (TASKS.length - 1 - i) * 18} cy={90} r={4} />
            ))}
          </g>
        )}

        {/* the agents */}
        <g className="dg-node" style={{ ["--c" as string]: COLOR.agent }}>
          <rect className="card" x={500} y={16} width={600} height={88} rx={18} />
          <text x={528} y={68} fontSize={26} fontWeight={600}>
            AI agents
          </text>
          {chip(700, 62, "ask")}
          {chip(770, 84, "recall")}
          {chip(862, 106, "remember")}
          {chip(976, 100, "converse")}
        </g>

        {/* the composite: the box around the three shards */}
        <g className="dg-node" style={{ ["--c" as string]: COMP }} data-dashed="true">
          <rect className="card" x={40} y={168} width={1520} height={444} rx={28} />
          <text x={76} y={563} fontSize={22} fontWeight={600}>
            Composite database
          </text>
          <text className="muted" x={76} y={589} fontSize={16.5}>
            stores nothing · one Cypher query across all three
          </text>
        </g>

        {shard("semantic", 80, "sem", "Semantic layer", ".semantic", "stores data", ["Tables · columns · queries · joins", "Variables · business areas", "Computations · request bank"])}
        {shard("rows", 575, "rows", "Virtual graph", ".rows", "stores nothing", ["The warehouse's live rows as a graph", "Cypher translated to SQL at query time", "Zero copy"], true)}
        {shard("memory", 1070, "mem", "Agent memory", ".memory", "stores data", ["What agents fetched and kept", "Provenance · holds until · who read it", "Tasks · facts · decisions · skills"])}

        {/* the warehouse, across the bottom */}
        <g className="dg-node" style={{ ["--c" as string]: COLOR.wh }}>
          <rect className="card" x={40} y={700} width={1520} height={184} rx={22} />
          <text x={76} y={742} fontSize={22} fontWeight={600}>
            Your data warehouse
          </text>
          <text className="muted" x={1524} y={742} fontSize={16.5} textAnchor="end">
            nothing is copied out
          </text>
          {item(470, "Query log", "who ran what, how often")}
          {item(800, "Graph views", "what the rows are read from")}
          {item(1295, "Source datasets", "the business's tables")}
        </g>

        {/* the lock on the way in: every call is made as a principal */}
        <g aria-hidden="true">
          <rect x={824} y={128} width={17} height={13} rx={3} style={{ fill: "var(--fg-muted)" }} />
          <path d="M828 128 v-4.5 a4.5 4.5 0 0 1 9 0 V128" fill="none" strokeWidth={2} style={{ stroke: "var(--fg-muted)" }} />
          <text className="muted mono" x={852} y={141} fontSize={14.5}>
            as the principal
          </text>
          <text className="muted mono" x={778} y={141} fontSize={14.5} textAnchor="end">
            Cypher · tools
          </text>
        </g>

        {/* the standing connections, then the running task over them (never in the pointer's way) */}
        {Object.values(EDGES).map(edge)}
        {!still && <g className="running">{task.steps.map(light)}</g>}
      </svg>

      {/* narrow screens: the same layers as a list */}
      <ol className="space-y-3 md:hidden">
        {(["agent", "composite", "semantic", "rows", "memory", "warehouse"] as Id[]).map((id) => (
          <li key={id} className="rounded-card border border-line bg-bg-subtle p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{
                  background:
                    id === "semantic" ? COLOR.sem : id === "rows" ? COLOR.rows : id === "memory" ? COLOR.mem : id === "composite" ? COMP : id === "warehouse" ? COLOR.wh : COLOR.agent,
                }}
              />
              {INFO[id].title}
            </div>
            <p className="mt-1 text-sm text-fg-muted">{INFO[id].text}</p>
            <p className="mt-2 font-mono text-xs text-fg-muted">{INFO[id].fact}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

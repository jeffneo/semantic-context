import { useEffect, useId, useState } from "react";

/*
  How a query reaches the warehouse as the person asking, in the landing diagram's style, smaller. A question comes in as one of the principals; the gateway asks the
  warehouse what they may read and signs the Cypher with a token that names them; Virtual Graph turns it into SQL and carries the token along; its JDBC pass-through
  verifies the token and runs the SQL as that principal's own service account; and BigQuery's grants, column tags and row policies decide what comes back. A query with
  no token, a forged one or an expired one is refused by the driver before BigQuery sees it.

  The path flashes in order and fades, once round and again, as on the landing page; with reduced motion the diagram is still.
*/
type Tone = "plain" | "rows" | "wh";
const COLOR: Record<Tone, string> = { plain: "var(--fg-muted)", rows: "var(--shard-rows)", wh: "var(--warehouse)" };

const STEP_S = 0.5;
const FADE_S = 1.7;
const REST_S = 2.2;

interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
  r: number;
  tone: Tone;
}
const Y = 30;
const H = 220;
const BOX: Record<"agent" | "gate" | "sql" | "driver" | "bq", Box> = {
  agent: { x: 20, y: Y, w: 230, h: H, r: 18, tone: "plain" },
  gate: { x: 335, y: Y, w: 290, h: H, r: 18, tone: "plain" },
  sql: { x: 732, y: 100, w: 210, h: 132, r: 12, tone: "rows" },
  driver: { x: 987, y: 100, w: 221, h: 132, r: 12, tone: "rows" },
  bq: { x: 1315, y: Y, w: 265, h: H, r: 18, tone: "wh" },
};
const VG = { x: 710, y: Y, w: 520, h: H, r: 18 };

interface Edge {
  id: string;
  d: string;
  from: Tone;
  to: Tone;
  axis: [number, number, number, number];
  label?: { x: number; y: number; text: string };
}
const EDGES: Edge[] = [
  { id: "ask", d: "M250 140 H335", from: "plain", to: "plain", axis: [250, 0, 335, 0], label: { x: 292, y: 126, text: "ask" } },
  { id: "signed", d: "M625 140 H710", from: "plain", to: "rows", axis: [625, 0, 710, 0], label: { x: 667, y: 126, text: "signed" } },
  { id: "inner", d: "M942 166 H987", from: "rows", to: "rows", axis: [942, 0, 987, 0] },
  { id: "sql", d: "M1230 140 H1315", from: "rows", to: "wh", axis: [1230, 0, 1315, 0], label: { x: 1272, y: 126, text: "SQL" } },
  { id: "back", d: "M1447 250 V330 H135 V250", from: "wh", to: "plain", axis: [1447, 0, 135, 0], label: { x: 790, y: 322, text: "only the rows the principal may see" } },
];

// what lights, in order: a connection (flash along it) or a box (a halo)
const STEPS: ({ edge: string } | { box: keyof typeof BOX })[] = [
  { box: "agent" },
  { edge: "ask" },
  { box: "gate" },
  { edge: "signed" },
  { box: "sql" },
  { edge: "inner" },
  { box: "driver" },
  { edge: "sql" },
  { box: "bq" },
  { edge: "back" },
];

const STEP_TEXT: [string, string][] = [
  ["A question, as a principal", "Marketing, risk or contact-center: the agent acts as the person it serves."],
  ["The gateway signs it", "It asks the warehouse what that principal may read, then signs the Cypher with a token that names them."],
  ["Virtual Graph translates", "The Cypher becomes SQL, and the token rides along on every statement."],
  ["The JDBC pass-through verifies", "It checks the token, then runs the SQL as the principal's own service account. No token, a forged one or an expired one: refused."],
  ["BigQuery decides", "Table grants, column policy tags and row access policies apply, exactly as for that person anywhere else."],
];

export default function Passthrough() {
  const uid = useId().replace(/:/g, "");
  const [tick, setTick] = useState(0);
  const still = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  useEffect(() => {
    if (still) return;
    const t = window.setTimeout(() => setTick((n) => n + 1), (STEPS.length * STEP_S + REST_S) * 1000);
    return () => window.clearTimeout(t);
  }, [tick, still]);

  const edge = (e: Edge) => (
    <g key={e.id} className="dg-edge">
      <path className="base" d={e.d} style={{ stroke: `url(#${uid}-g-${e.id})` }} markerEnd={`url(#${uid}-a-${e.to})`} />
      {e.label && (
        <text className="elabel" x={e.label.x} y={e.label.y} textAnchor="middle" fontSize={e.id === "back" ? 15 : 14}>
          {e.label.text}
        </text>
      )}
    </g>
  );

  const light = (s: (typeof STEPS)[number], i: number) => {
    const delay = `${i * STEP_S}s`;
    const key = `${tick}-${i}`;
    if ("box" in s) {
      const b = BOX[s.box];
      return <rect key={key} className="halo" x={b.x} y={b.y} width={b.w} height={b.h} rx={b.r} style={{ ["--c" as string]: COLOR[b.tone], animationDelay: delay, animationDuration: `${FADE_S}s` }} />;
    }
    const e = EDGES.find((x) => x.id === s.edge)!;
    const common = { d: e.d, pathLength: 100, style: { animationDelay: delay, animationDuration: `${FADE_S}s` } };
    return (
      <g key={key}>
        <path className="lit" {...common} style={{ ...common.style, stroke: `url(#${uid}-g-${e.id})` }} />
        <path className="lit-core" {...common} style={{ ...common.style, animationDuration: `${FADE_S * 0.7}s` }} />
      </g>
    );
  };

  const node = (tone: Tone, b: Box, title: string, tag: string | null, lines: string[], dashed = false) => (
    <g className="dg-node" style={{ ["--c" as string]: COLOR[tone] }} data-dashed={dashed}>
      <rect className="card" x={b.x} y={b.y} width={b.w} height={b.h} rx={b.r} />
      <text x={b.x + 24} y={b.y + 46} fontSize={24} fontWeight={600}>
        {title}
      </text>
      {tag && (
        <>
          <rect className="tag" x={b.x + b.w - 24 - (tag.length * 8.2 + 24)} y={b.y + 22} width={tag.length * 8.2 + 24} height={28} rx={14} />
          <text className="tagtext mono" x={b.x + b.w - 24 - (tag.length * 8.2 + 24) / 2} y={b.y + 41} fontSize={14} textAnchor="middle">
            {tag}
          </text>
        </>
      )}
      {lines.map((l, i) => (
        <text key={l} className="muted" x={b.x + 24} y={b.y + 88 + i * 28} fontSize={17.5}>
          {l}
        </text>
      ))}
    </g>
  );

  const item = (b: Box, title: string, lines: string[], strong = false, warn?: string) => (
    <g className="dg-node" style={{ ["--c" as string]: COLOR.rows }}>
      <rect className="item" x={b.x} y={b.y} width={b.w} height={b.h} rx={b.r} style={strong ? { stroke: "var(--shard-rows)", strokeWidth: 2.4 } : undefined} />
      <text x={b.x + 18} y={b.y + 34} fontSize={20} fontWeight={600}>
        {title}
      </text>
      {lines.map((l, i) => (
        <text key={l} className="muted" x={b.x + 18} y={b.y + 62 + i * 24} fontSize={16.5}>
          {l}
        </text>
      ))}
      {warn && (
        <text x={b.x + 18} y={b.y + 118} fontSize={15} style={{ fill: "var(--bad)" }}>
          {warn}
        </text>
      )}
    </g>
  );

  return (
    <div className="mt-6">
      <svg
        className="dg hidden h-auto w-full md:block"
        viewBox="0 0 1600 350"
        role="img"
        aria-label="How a query reaches the warehouse as the principal: a question comes in as a principal; the gateway asks the warehouse what they may read and signs the Cypher with a token naming them; Virtual Graph turns it into SQL and carries the token; its JDBC pass-through verifies the token and runs the SQL as that principal's service account; BigQuery's grants, column tags and row policies decide what comes back. A query with no valid token is refused by the driver."
      >
        <defs>
          {(["plain", "rows", "wh"] as Tone[]).map((t) => (
            <marker key={t} id={`${uid}-a-${t}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
              <path d="M1 1.5 L8.5 5 L1 8.5 z" style={{ fill: COLOR[t] }} />
            </marker>
          ))}
          {EDGES.map((e) => (
            <linearGradient key={e.id} id={`${uid}-g-${e.id}`} gradientUnits="userSpaceOnUse" x1={e.axis[0]} y1={e.axis[1]} x2={e.axis[2]} y2={e.axis[3]}>
              <stop offset="0" style={{ stopColor: COLOR[e.from] }} />
              <stop offset="1" style={{ stopColor: COLOR[e.to] }} />
            </linearGradient>
          ))}
        </defs>

        {/* the agent, and who it may be */}
        {node("plain", BOX.agent, "A question", null, ["Asked as the principal", "it serves:"])}
        {[
          ["marketing", "var(--area-1)"],
          ["risk", "var(--area-2)"],
          ["contact-center", "var(--area-3)"],
        ].map(([p, c], i) => (
          <text key={p} className="mono" x={BOX.agent.x + 24} y={BOX.agent.y + 150 + i * 24} fontSize={15.5} style={{ fill: c }}>
            {p}
          </text>
        ))}

        {/* the gateway */}
        {node("plain", BOX.gate, "The gateway", "signs", ["Asks the warehouse what", "the principal may read,", "then signs the Cypher with", "a token that names them."])}

        {/* Virtual Graph: a box around the translation and the driver, which stores nothing */}
        <g className="dg-node" style={{ ["--c" as string]: COLOR.rows }} data-dashed="true">
          <rect className="card" x={VG.x} y={VG.y} width={VG.w} height={VG.h} rx={VG.r} />
          <text x={VG.x + 24} y={VG.y + 46} fontSize={24} fontWeight={600}>
            Virtual Graph
          </text>
          <rect className="tag" x={VG.x + VG.w - 24 - 133} y={VG.y + 22} width={133} height={28} rx={14} />
          <text className="tagtext mono" x={VG.x + VG.w - 24 - 66.5} y={VG.y + 41} fontSize={14} textAnchor="middle">
            stores nothing
          </text>
        </g>
        {item(BOX.sql, "Cypher to SQL", ["The token rides along", "on every statement."])}
        {item(BOX.driver, "JDBC pass-through", ["Verifies the token, then", "runs as the principal."], true, "No valid token: refused")}

        {/* the warehouse, and what decides there */}
        <g className="dg-node" style={{ ["--c" as string]: COLOR.wh }}>
          <rect className="card" x={BOX.bq.x} y={BOX.bq.y} width={BOX.bq.w} height={BOX.bq.h} rx={BOX.bq.r} />
          <text x={BOX.bq.x + 24} y={BOX.bq.y + 46} fontSize={24} fontWeight={600}>
            BigQuery
          </text>
          <rect className="tag" x={BOX.bq.x + BOX.bq.w - 24 - 82} y={BOX.bq.y + 22} width={82} height={28} rx={14} />
          <text className="tagtext mono" x={BOX.bq.x + BOX.bq.w - 24 - 41} y={BOX.bq.y + 41} fontSize={14} textAnchor="middle">
            decides
          </text>
          {["Table grants", "Column policy tags", "Row access policies"].map((t, i) => (
            <g key={t}>
              <rect className="item" x={BOX.bq.x + 22} y={BOX.bq.y + 80 + i * 44} width={BOX.bq.w - 44} height={34} rx={17} />
              <text className="mono" x={BOX.bq.x + BOX.bq.w / 2} y={BOX.bq.y + 102 + i * 44} fontSize={15} textAnchor="middle">
                {t}
              </text>
            </g>
          ))}
        </g>

        {/* a small lock on the signed hop */}
        <g transform="translate(659 142)" style={{ fill: "none", stroke: "var(--fg-muted)", strokeWidth: 1.6 }} aria-hidden="true">
          <rect x="0" y="7" width="16" height="12" rx="2.5" />
          <path d="M3.5 7 V4.5 a4.5 4.5 0 0 1 9 0 V7" />
        </g>

        {EDGES.map(edge)}
        {!still && <g className="running">{STEPS.map(light)}</g>}
      </svg>

      {/* narrow screens: the same steps as a list */}
      <ol className="space-y-3 md:hidden">
        {STEP_TEXT.map(([title, text], i) => (
          <li key={title} className="rounded-card border border-line bg-bg-subtle p-4">
            <p className="text-sm font-semibold">
              <span className="mr-2 font-mono text-xs text-fg-muted">{i + 1}</span>
              {title}
            </p>
            <p className="mt-1 text-sm text-fg-muted">{text}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

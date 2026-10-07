import { useMemo, useState } from "react";
import type { Pick, Virtual } from "./data";
import { COMPACT } from "./force";
import SchemaGraph from "./SchemaGraph";
import { focusOf, semanticGraph, seedOfPath, type Focus, type Seed } from "./semantic";

const BLUE = "var(--shard-semantic)"; // the semantic layer's colour in the architecture
const ORANGE = "var(--shard-rows)"; // the Virtual Graph's

/** A label in two or three short lines, so a long variable name sits under its circle without running into the next. */
function lines(label: string, width = 15): string[] {
  const out: string[] = [];
  for (const word of label.split(" ")) {
    const last = out[out.length - 1];
    if (last !== undefined && (last + " " + word).length <= width) out[out.length - 1] = last + " " + word;
    else out.push(word);
  }
  return out;
}

/*
  The two pictures of one model, side by side as in the architecture: .semantic, the paths the build found (a table, its column, the variable the column
  holds), and .rows, the schema generated from them. Pick anything in either and what it makes, or is made from, lights in both.
*/
export default function Compare({ d }: { d: Virtual }) {
  const [seed, setSeed] = useState<Seed>({ nodes: [], edges: ["HANDLED_BY"] });
  const focus = useMemo(() => focusOf(d, seed), [d, seed]);
  const onSchema = (p: Pick) => setSeed(p.kind === "node" ? { nodes: [p.id], edges: [] } : { nodes: [], edges: [p.id] });
  const onPath = (id: string) => setSeed(seedOfPath(d, id));

  return (
    <div className="mt-6">
      <p className="min-h-6 text-sm leading-relaxed" aria-live="polite">
        <Reads d={d} focus={focus} seed={seed} />
      </p>
      <div className="mt-3 grid grid-cols-1 items-stretch gap-4 xl:grid-cols-[minmax(0,1fr)_2.75rem_minmax(0,1fr)]">
        <Panel chip=".semantic" color={BLUE} title="The paths the build found" sub="a table, its column, and the variable the column holds">
          <PathsGraph d={d} focus={focus} onPick={onPath} />
        </Panel>
        <div className="hidden flex-col items-center justify-center gap-1 text-fg-muted xl:flex" aria-hidden="true">
          <svg width="30" height="14" viewBox="0 0 30 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 7h26M21 2l6 5-6 5" />
          </svg>
          <span className="text-[10px] uppercase tracking-wider [writing-mode:vertical-rl]">generates</span>
        </div>
        <Panel chip=".rows" color={ORANGE} title="The schema generated from them" sub="node labels, and the relationship types between them">
          <SchemaGraph d={d} pick={null} onPick={onSchema} lit={focus} size={COMPACT} />
        </Panel>
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1.5 text-xs text-fg-muted" aria-label="Key">
        <li className="flex items-center gap-2">
          <span className="h-3.5 w-7 rounded-[5px] border" style={{ borderColor: BLUE, background: `color-mix(in oklab, ${BLUE} 10%, var(--bg))` }} aria-hidden="true" /> table → node
        </li>
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full border-2" style={{ borderColor: BLUE, background: "var(--bg)" }} aria-hidden="true" /> column → an arrow, where it points
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3.5 w-3.5 rounded-full" style={{ background: BLUE }} aria-hidden="true" /> variable: what the columns hold in common
        </li>
      </ul>
    </div>
  );
}

function Panel({ chip, color, title, sub, children }: { chip: string; color: string; title: string; sub: string; children: React.ReactNode }) {
  return (
    <section className="rounded-card border p-3" style={{ borderColor: `color-mix(in oklab, ${color} 45%, var(--line))` }}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-1 pb-2">
        <span className="rounded-full border px-2.5 py-0.5 font-mono text-xs" style={{ borderColor: color, color, background: "var(--bg)" }}>
          {chip}
        </span>
        <span className="text-sm font-medium">{title}</span>
        <span className="text-xs text-fg-muted">{sub}</span>
      </div>
      <div className="rounded-md bg-bg-subtle">{children}</div>
    </section>
  );
}

/** What is lit, in words: the path on the left and what it became on the right. */
function Reads({ d, focus, seed }: { d: Virtual; focus: Focus; seed: Seed }) {
  const arrows = d.relationships.filter((r) => focus.edges.has(r.type));
  const short = (t: string) => t.split(".").slice(-1)[0];
  if (arrows.length === 1 && seed.nodes.length === 0 && !seed.holders?.length) {
    const r = arrows[0];
    const end = d.nodes.find((n) => n.label === r.end)!;
    return (
      <>
        <span className="font-mono text-xs" style={{ color: BLUE }}>
          {short(r.table)}.{r.column} → {r.variable ?? "?"} ← {short(end.table)}.{r.endKey}
        </span>
        <span className="mx-3 text-fg-muted">becomes</span>
        <span className="font-mono text-xs" style={{ color: ORANGE }}>
          (:{r.start})-[:{r.type}]-&gt;(:{r.end})
        </span>
      </>
    );
  }
  return (
    <span className="text-fg-muted">
      <span style={{ color: BLUE }}>
        {count(focus.tables.size, "table")}, {count(focus.columns.size, "column")}, {count(focus.variables.size, "variable")}
      </span>{" "}
      make{" "}
      <span style={{ color: ORANGE }}>
        {count(focus.nodes.size, "node label")} and {count(focus.edges.size, "relationship type")}
      </span>
      .
    </span>
  );
}

const count = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

const W = COMPACT.w;
const H = COMPACT.h;

function PathsGraph({ d, focus, onPick }: { d: Virtual; focus: Focus; onPick: (id: string) => void }) {
  const g = useMemo(() => semanticGraph(d, W, H), [d]);
  const by = useMemo(() => new Map(g.nodes.map((n) => [n.id, n])), [g]);
  const on = (id: string) => {
    const kind = by.get(id)!.kind;
    return kind === "table" ? focus.tables.has(id) : kind === "column" ? focus.columns.has(id) : focus.variables.has(id);
  };
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="The semantic layer's paths from tables through columns to variables">
      <defs>
        <marker id="sem-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0 1 L9 5 L0 9 z" fill={BLUE} />
        </marker>
      </defs>
      {g.edges.map((e) => {
        const [a, b] = [by.get(e.from)!, by.get(e.to)!];
        const lit = on(e.from) && on(e.to);
        // stop at the edge of each shape, so an arrowhead is not buried
        const [dx, dy] = [b.x - a.x, b.y - a.y];
        const len = Math.max(1, Math.hypot(dx, dy));
        const pull = (n: typeof a, sign: number) => (n.kind === "table" ? Math.min(len / 2, Math.abs(dx) > Math.abs(dy) ? n.r * 0.9 : 15) : n.r) * sign;
        const [x0, y0] = [a.x + (dx / len) * pull(a, 1), a.y + (dy / len) * pull(a, 1)];
        const [x1, y1] = [b.x - (dx / len) * (pull(b, 1) + 2), b.y - (dy / len) * (pull(b, 1) + 2)];
        return <line key={e.from + e.to} x1={x0} y1={y0} x2={x1} y2={y1} stroke={BLUE} strokeWidth={lit ? 1.8 : 1.1} opacity={lit ? 0.85 : 0.14} markerEnd="url(#sem-arrow)" className="transition-opacity" />;
      })}
      {g.nodes.map((n) => {
        const lit = on(n.id);
        const common = { opacity: lit ? 1 : n.kind === "column" ? 0.14 : 0.3, style: { cursor: "pointer" }, onClick: () => onPick(n.id), className: "transition-opacity" };
        if (n.kind === "table")
          return (
            <g key={n.id} {...common}>
              <rect x={n.x - n.r + 6} y={n.y - 12} width={n.r * 2 - 12} height={24} rx={8} fill={`color-mix(in oklab, ${BLUE} 10%, var(--bg))`} stroke={BLUE} strokeWidth={lit ? 2 : 1.3} />
              <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize={11} className="fill-fg font-mono">
                {n.label.length > 14 ? n.label.slice(0, 13) + "…" : n.label}
              </text>
            </g>
          );
        if (n.kind === "variable")
          return (
            <g key={n.id} {...common}>
              <circle cx={n.x} cy={n.y} r={n.r - 2} fill={BLUE} opacity={0.9} />
              <text textAnchor="middle" fontSize={11.5} fontWeight={600} className="fill-fg" style={{ paintOrder: "stroke", stroke: "var(--bg)", strokeWidth: 3.5, strokeLinejoin: "round" }}>
                {lines(n.label).map((l, i) => (
                  <tspan key={i} x={n.x} y={n.y + n.r + 12 + i * 13}>
                    {l}
                  </tspan>
                ))}
              </text>
            </g>
          );
        return (
          <g key={n.id} {...common}>
            <circle cx={n.x} cy={n.y} r={6.5} fill="var(--bg)" stroke={BLUE} strokeWidth={lit ? 2.2 : 1.4} />
            {lit && (
              <text x={n.x} y={n.y - 11} textAnchor="middle" fontSize={10.5} className="fill-fg font-mono" style={{ paintOrder: "stroke", stroke: "var(--bg)", strokeWidth: 3, strokeLinejoin: "round" }}>
                {n.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

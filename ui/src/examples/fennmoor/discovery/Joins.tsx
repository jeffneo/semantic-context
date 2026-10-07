import { useMemo, useState } from "react";
import type { Discovery, Join, Variable } from "./data";

const n = (x: number) => x.toLocaleString("en-US");
const short = (table: string) => table.split(".").slice(-1)[0];

/** How a join came to be trusted, from the strongest. The words are the build's: who ran it, and how many made it independently. */
const CONFIDENCE: Record<string, { label: string; stroke: string; dash?: string }> = {
  production: { label: "run by a pipeline or a dashboard", stroke: "var(--fg)" },
  corroborated: { label: "made independently by several people", stroke: "color-mix(in oklab, var(--fg) 60%, var(--bg))" },
  single: { label: "one person's, contradicted by nothing", stroke: "color-mix(in oklab, var(--fg) 40%, var(--bg))", dash: "5 4" },
};
const KEY = ["production", "corroborated", "single"];

/*
  What the joins revealed: columns the business joins are one thing. Pick a variable to see its columns around a circle and, as chords, the joins
  queries made between them, heavier for the ones run more often. The joins the layer refused to merge on are the next part.
*/
export default function Joins({ d }: { d: Discovery }) {
  const [pick, setPick] = useState(0);
  const v = d.variables[pick];
  return (
    <div className="mt-6">
      <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-[17rem_minmax(0,1fr)]">
        <ul className="max-h-[34rem] overflow-auto rounded-card border border-line bg-bg-subtle p-1.5" aria-label="Variables">
          {d.variables.map((x, i) => (
            <li key={i}>
              <button
                type="button"
                aria-pressed={i === pick}
                onClick={() => setPick(i)}
                className={`w-full rounded-md px-3 py-2 text-left transition-colors ${i === pick ? "bg-bg shadow-[inset_0_0_0_1px_var(--line-strong)]" : "hover:bg-bg"}`}
              >
                <span className="flex items-baseline justify-between gap-3 text-sm font-medium">
                  {x.name}
                  <span className="text-xs font-normal tabular-nums text-fg-muted">{x.tables} tables</span>
                </span>
                <span className="mt-0.5 block truncate font-mono text-[11px] text-fg-muted">{[...new Set(x.columns.map(([, c]) => c))].slice(0, 3).join(", ")}</span>
              </button>
            </li>
          ))}
        </ul>
        <Chords key={pick} v={v} />
      </div>
    </div>
  );
}

function Chords({ v }: { v: Variable }) {
  const [hot, setHot] = useState<number | null>(null);
  const [edge, setEdge] = useState<Join | null>(null);
  const count = v.columns.length;
  // Where every column has the same name (a key called customer_key in 26 tables) the table is the label and the column is said once.
  const same = new Set(v.columns.map(([, c]) => c)).size === 1;
  const label = ([table, column]: [string, string]) => (same ? short(table) : `${short(table)}.${column}`);
  // A big variable's labels would run into each other, so they run outward from the circle; a small one's read across.
  const radial = count > 14;
  const R = radial ? 190 : 150;
  const font = radial ? 12 : 11;
  const room = Math.ceil(Math.max(...v.columns.map((c) => label(c).length)) * font * 0.6) + 24; // px a label takes
  const W = radial ? Math.max(900, 2 * (R + room)) : 900;
  const H = radial ? 2 * (R + room) : 520;
  const [cx, cy] = [W / 2, H / 2];
  const at = (i: number, r = R) => {
    const a = (i / count) * Math.PI * 2 - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a), Math.cos(a), (a * 180) / Math.PI] as const;
  };
  const heaviest = Math.max(1, ...v.joins.map((j) => j[3]));
  const lines = useMemo(
    () => ({
      production: v.joins.filter((j) => j[2] === "production").length,
      corroborated: v.joins.filter((j) => j[2] === "corroborated").length,
      single: v.joins.filter((j) => j[2] === "single").length,
    }),
    [v],
  );
  const readout = edge
    ? `${v.columns[edge[0]][1]} ⇄ ${v.columns[edge[1]][1]} · ${short(v.columns[edge[0]][0])} and ${short(v.columns[edge[1]][0])} · ${CONFIDENCE[edge[2]]?.label ?? edge[2]} · ${n(edge[3])} runs, ${edge[4]} ${edge[4] === 1 ? "person" : "people"}`
    : hot !== null
      ? `${v.columns[hot][0]}.${v.columns[hot][1]}`
      : `${count} columns in ${v.tables} tables, ${v.joins.length} joins between them`;

  return (
    <section className="rounded-card border border-line p-5" aria-label={`The variable ${v.name}`}>
      <h4 className="text-base font-semibold tracking-tight">{v.name}</h4>
      <p className="mt-1 max-w-3xl text-sm text-fg-muted">{v.description}</p>
      {same && <p className="mt-1 font-mono text-xs text-fg-muted">column: {v.columns[0][1]}, in each table</p>}

      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 h-auto w-full" role="img" aria-label={`The columns of ${v.name} and the joins between them`}>
        {v.joins.map((j, k) => {
          const [ax, ay] = at(j[0]);
          const [bx, by] = at(j[1]);
          const [mx, my] = [(ax + bx) / 2, (ay + by) / 2];
          const [qx, qy] = [cx + (mx - cx) * 0.15, cy + (my - cy) * 0.15]; // pulled toward the centre: a chord, not a line
          const style = CONFIDENCE[j[2]] ?? CONFIDENCE.single;
          const on = hot === null ? edge === null || edge === j : j[0] === hot || j[1] === hot;
          return (
            <path
              key={k}
              d={`M${ax} ${ay} Q${qx} ${qy} ${bx} ${by}`}
              fill="none"
              stroke={style.stroke}
              strokeDasharray={style.dash}
              strokeLinecap="round"
              strokeWidth={1 + (3.5 * Math.log1p(j[3])) / Math.log1p(heaviest)}
              opacity={on ? 0.8 : 0.08}
              className="transition-opacity"
              onMouseEnter={() => setEdge(j)}
              onMouseLeave={() => setEdge(null)}
              style={{ cursor: "default" }}
            />
          );
        })}
        {v.columns.map((c, i) => {
          const [x, y, cos, deg] = at(i);
          const [lx, ly] = at(i, R + 14);
          const left = cos < 0;
          // outward along the radius (flipped on the left so it reads upright), or across for a small circle
          const place = radial
            ? { transform: `rotate(${left ? deg + 180 : deg} ${lx} ${ly})`, textAnchor: left ? ("end" as const) : ("start" as const), dy: 4 }
            : { textAnchor: cos > 0.15 ? ("start" as const) : cos < -0.15 ? ("end" as const) : ("middle" as const), dy: Math.abs(cos) <= 0.15 ? (ly < cy ? -4 : 12) : 4 };
          return (
            <g key={i} onMouseEnter={() => setHot(i)} onMouseLeave={() => setHot(null)} style={{ cursor: "default" }}>
              <circle cx={x} cy={y} r={hot === i ? 7 : 5} className="fill-bg stroke-fg" strokeWidth={2} />
              <text x={lx} y={ly} {...place} className="fill-fg font-mono" fontSize={font} opacity={hot === null || hot === i ? 1 : 0.45}>
                {label(c)}
              </text>
            </g>
          );
        })}
      </svg>

      <p className="h-5 overflow-hidden whitespace-nowrap font-mono text-xs text-fg-muted" aria-live="polite">
        {readout}
      </p>
      <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs text-fg-muted" aria-label="Key">
        {KEY.filter((k) => lines[k as keyof typeof lines] > 0).map((k) => (
          <li key={k} className="flex items-center gap-2">
            <svg width="26" height="6" aria-hidden="true">
              <line x1="1" y1="3" x2="25" y2="3" stroke={CONFIDENCE[k].stroke} strokeWidth="2.5" strokeDasharray={CONFIDENCE[k].dash} strokeLinecap="round" />
            </svg>
            {lines[k as keyof typeof lines]} {CONFIDENCE[k].label}
          </li>
        ))}
        <li>line weight: how often queries ran it</li>
      </ul>
    </section>
  );
}

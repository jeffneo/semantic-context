import { METHOD_COLOR, n, type Accuracy } from "./data";

/*
  What a request costs, per method: the median (the dot) to the 90th percentile (the bar's end) of tokens and of seconds, with the service's target as a
  dashed line. A method past the line is not delivering inside it.
*/
const LABEL = "10rem"; // the label and value columns are the same on every row, so the target line can sit over the middle one
const VALUE = "8rem";
const GAP = "1rem";

interface Axis {
  /** where a value sits along the plot, from 0 to 1 */
  at: (v: number) => number;
  ticks: [value: number, label: string][];
}
const TOKENS: Axis = {
  at: (v) => Math.min(1, Math.max(0, (Math.log10(v) - 3) / (Math.log10(200_000) - 3))), // 1,000 to 200,000, on a log scale
  ticks: [
    [1_000, "1k"],
    [10_000, "10k"],
    [100_000, "100k"],
  ],
};
const SECONDS: Axis = {
  at: (v) => Math.min(1, Math.max(0, v / 60)),
  ticks: [0, 15, 30, 45, 60].map((v) => [v, `${v} s`]),
};

export default function Costs({ d }: { d: Accuracy }) {
  return (
    <div className="mt-6 grid grid-cols-1 gap-x-12 gap-y-10 xl:grid-cols-2">
      <Range
        title="Tokens a request"
        note="log scale"
        axis={TOKENS}
        target={d.targets.tokens}
        targetLabel={`target ${n(d.targets.tokens)}`}
        rows={d.methods.map((m) => ({ id: m.id, name: m.name, p50: m.log.tokens_p50, p90: m.log.tokens_p90, text: `${n(m.log.tokens_p50)} – ${n(m.log.tokens_p90)}` }))}
      />
      <Range
        title="Seconds a request"
        note="under parallel load"
        axis={SECONDS}
        target={d.targets.seconds}
        targetLabel={`target ${d.targets.seconds} s`}
        rows={d.methods.map((m) => ({ id: m.id, name: m.name, p50: m.log.seconds_p50, p90: m.log.seconds_p90, text: `${m.log.seconds_p50} – ${m.log.seconds_p90} s` }))}
      />
    </div>
  );
}

interface Row {
  id: keyof typeof METHOD_COLOR;
  name: string;
  p50: number;
  p90: number;
  text: string;
}

function Range({ title, note, axis, target, targetLabel, rows }: { title: string; note: string; axis: Axis; target: number; targetLabel: string; rows: Row[] }) {
  const grid = { gridTemplateColumns: `${LABEL} minmax(0, 1fr) ${VALUE}`, columnGap: GAP };
  const pos = (v: number) => `${axis.at(v) * 100}%`;
  return (
    <figure>
      <figcaption className="flex items-baseline justify-between text-sm">
        <span className="font-medium">{title}</span>
        <span className="text-xs text-fg-muted">median to 90th percentile · {note}</span>
      </figcaption>
      <div className="relative mt-8">
        {/* the target and the axis ticks, over the middle column */}
        <div className="pointer-events-none absolute inset-y-0" style={{ left: `calc(${LABEL} + ${GAP})`, right: `calc(${VALUE} + ${GAP})` }}>
          <div className="absolute inset-y-0 border-l border-dashed border-fg/50" style={{ left: pos(target) }}>
            <span className="absolute -top-5 left-1 whitespace-nowrap text-[10px] text-fg-muted">{targetLabel}</span>
          </div>
        </div>
        {rows.map((r) => (
          <div key={r.id} className="grid items-center py-2" style={grid}>
            <span className="text-sm">{r.name}</span>
            <div className="relative h-4">
              <span
                className="absolute top-1/2 h-[3px] -translate-y-1/2 rounded-full"
                style={{ left: pos(r.p50), width: `${(axis.at(r.p90) - axis.at(r.p50)) * 100}%`, background: METHOD_COLOR[r.id] }}
              />
              <span className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2" style={{ left: pos(r.p90), background: METHOD_COLOR[r.id] }} />
              <span className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ left: pos(r.p50), background: METHOD_COLOR[r.id] }} />
            </div>
            <span className="text-right text-xs tabular-nums text-fg-muted">{r.text}</span>
          </div>
        ))}
        <div className="grid" style={grid}>
          <span />
          <div className="relative h-5 border-t border-line">
            {axis.ticks.map(([v, label]) => (
              <span key={label} className="absolute top-1 -translate-x-1/2 whitespace-nowrap text-[10px] text-fg-muted" style={{ left: pos(v) }}>
                {label}
              </span>
            ))}
          </div>
          <span />
        </div>
      </div>
    </figure>
  );
}

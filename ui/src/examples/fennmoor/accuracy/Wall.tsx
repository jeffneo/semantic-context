import { useMemo, useState } from "react";
import { METHOD_COLOR, n, type Accuracy, type MethodId, type Question, type Verdict } from "./data";

const IDS: MethodId[] = ["naive-schema", "naive-agent", "layer", "agent"];

const right = (q: Question, m: MethodId) => q.r[m].v === "correct";
const score = (q: Question) => IDS.filter((m) => right(q, m)).length;
/** Questions with the same score are ordered by which methods got them, the agent's first, so the patterns sit together. */
const weight = (q: Question) => IDS.reduce((w, m, i) => w + (right(q, m) ? 2 ** i : 0), 0);
const byEase = (a: Question, b: Question) => score(b) - score(a) || weight(b) - weight(a) || a.id.localeCompare(b.id);

/** A square's corner: right, wrong, or an answer with no rows (outlined). */
const corner = (v: Verdict) => (v === "correct" ? "bg-ok" : v === "empty" ? "bg-bg ring-1 ring-inset ring-bad" : "bg-bad");

/*
  Every question as a square whose four corners are the four methods (top row: the schema in the prompt, the generic agent; bottom row: the layer, the
  agent using it). Sorted by how many methods got it right, so the agent's corner can be followed down the wall. Hover reads a question on one fixed
  line; a click opens it beside the wall.
*/
export default function Wall({ d }: { d: Accuracy }) {
  const ordered = useMemo(() => [...d.questions].sort(byEase), [d]);
  const log = ordered.filter((q) => q.group === "log");
  const gold = ordered.filter((q) => q.group === "gold");

  // Start on a question the agent answered and neither naive method did: the gain, in one square.
  const start = ordered.find((q) => right(q, "agent") && !right(q, "naive-schema") && !right(q, "naive-agent")) ?? ordered[0];
  const [selected, setSelected] = useState(start);
  const [hovered, setHovered] = useState<Question | null>(null);
  const shown = hovered ?? selected;

  const only = log.filter((q) => right(q, "agent") && !right(q, "naive-schema") && !right(q, "naive-agent")).length;
  const all = log.filter((q) => score(q) === 4).length;
  const none = log.filter((q) => score(q) === 0).length;
  const lost = log.filter((q) => !right(q, "agent") && (right(q, "naive-schema") || right(q, "naive-agent"))).length;

  return (
    <div className="mt-6">
      <ul className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-fg-muted" aria-label="Key">
        <li className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-[3px] bg-ok" aria-hidden="true" /> right
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-[3px] bg-bad" aria-hidden="true" /> wrong
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-[3px] bg-bg ring-1 ring-inset ring-bad" aria-hidden="true" /> no rows
        </li>
        <li className="flex items-center gap-2">
          <Key /> corners: schema, generic agent / layer, agent with the layer
        </li>
      </ul>

      <p className="mt-4 h-6 overflow-hidden whitespace-nowrap text-xs text-fg-muted" aria-live="polite">
        <span className="font-mono text-fg">{shown.id}</span> <span className="ml-2">{shown.text}</span>
      </p>

      <div className="mt-2 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_26rem]">
        <div>
          <div className="rounded-card border border-line bg-bg-subtle p-4">
            <p className="text-xs text-fg-muted">
              {log.length} questions written from queries the business ran, the easiest first
            </p>
            <Squares qs={log} selected={selected} onHover={setHovered} onSelect={setSelected} />
            <p className="mt-5 text-xs text-fg-muted">
              {gold.length} gold questions: hand-written, never asked before, and harder ({d.methods.map((m) => `${m.gold.right}`).join(", ")} right, in the
              order of the corners)
            </p>
            <Squares qs={gold} selected={selected} onHover={setHovered} onSelect={setSelected} />
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-4">
            <Tally value={all} label="right on all four methods" />
            <Tally value={only} label="right only with the layer's agent" />
            <Tally value={lost} label="the agent missed and a naive method got" />
            <Tally value={none} label="wrong on all four" />
          </dl>
        </div>
        <div className="xl:sticky xl:top-20 xl:max-h-[calc(100svh-6rem)] xl:overflow-auto xl:rounded-card">
          <Detail d={d} q={selected} />
        </div>
      </div>
    </div>
  );
}

function Squares(props: { qs: Question[]; selected: Question; onHover: (q: Question | null) => void; onSelect: (q: Question) => void }) {
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {props.qs.map((q) => {
        const on = props.selected === q;
        return (
          <button
            key={q.id}
            type="button"
            aria-label={`${q.id}: ${q.text}`}
            aria-pressed={on}
            className={`grid h-6 w-6 grid-cols-2 gap-[2px] rounded-[4px] transition-transform hover:scale-125 ${on ? "ring-2 ring-link ring-offset-2 ring-offset-bg-subtle" : ""}`}
            onMouseEnter={() => props.onHover(q)}
            onMouseLeave={() => props.onHover(null)}
            onFocus={() => props.onHover(q)}
            onBlur={() => props.onHover(null)}
            onClick={() => props.onSelect(q)}
          >
            {IDS.map((m) => (
              <span key={m} className={`rounded-[2px] ${corner(q.r[m].v)}`} />
            ))}
          </button>
        );
      })}
    </div>
  );
}

function Key() {
  return (
    <span className="grid h-4 w-4 grid-cols-2 gap-[1.5px]" aria-hidden="true">
      {IDS.map((m) => (
        <span key={m} className="rounded-[1.5px]" style={{ background: METHOD_COLOR[m] }} />
      ))}
    </span>
  );
}

function Tally({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <dd className="text-2xl font-semibold tabular-nums tracking-tight">{value}</dd>
      <dt className="text-xs text-fg-muted">{label}</dt>
    </div>
  );
}

const VERDICT: Record<Verdict, [string, string]> = {
  correct: ["right", "text-ok"],
  wrong: ["wrong", "text-bad"],
  empty: ["no rows", "text-bad"],
};

function Detail({ d, q }: { d: Accuracy; q: Question }) {
  return (
    <section className="rounded-card border border-line bg-bg p-5" aria-label={`Question ${q.id}`}>
      <p className="text-xs text-fg-muted">
        <span className="font-mono text-fg">{q.id}</span> ·{" "}
        {q.group === "gold" ? "gold question, written by hand" : `written from a query run by ${q.who ?? "an analyst"}`}
      </p>
      <p className="mt-2 text-base font-medium leading-snug">{q.text}</p>

      <ul className="mt-5 divide-y divide-line">
        {d.methods.map((m) => {
          const r = q.r[m.id];
          const [word, tone] = VERDICT[r.v];
          return (
            <li key={m.id} className="py-3">
              <div className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-sm font-medium">
                  <span className="h-3 w-3 rounded-[3px]" style={{ background: METHOD_COLOR[m.id] }} aria-hidden="true" />
                  {m.name}
                </span>
                <span className={`text-sm font-medium ${tone}`}>{word}</span>
              </div>
              {r.why && <p className="mt-1 text-xs text-fg-muted">{r.why}</p>}
              <p className="mt-1 text-xs tabular-nums text-fg-muted">
                {n(r.t)} tokens · {r.s} s · ${r.c.toFixed(3)}
                {m.id === "agent" && ` · first answer by ${q.agent.route === "precedent" ? "precedent" : "a compiled request"}, ${q.agent.outcome}`}
              </p>
              {r.sql && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-xs text-link hover:underline">The query it wrote</summary>
                  <pre className="mt-2 max-h-56 overflow-auto rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{r.sql}</pre>
                </details>
              )}
            </li>
          );
        })}
      </ul>

      {q.ref && (
        <details className="mt-1 border-t border-line pt-3">
          <summary className="cursor-pointer text-xs text-link hover:underline">The business's own query, the reference</summary>
          <pre className="mt-2 max-h-56 overflow-auto rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{q.ref}</pre>
        </details>
      )}
    </section>
  );
}

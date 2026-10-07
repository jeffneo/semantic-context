import type { CSSProperties } from "react";
import { n, type Accuracy, type FirstAnswers } from "./data";

/** The agent's six ways of ending an exchange, in the order they read: right in the best way first, wrong in the worst way last. */
const OUTCOMES: { key: string; style: CSSProperties; says: string }[] = [
  { key: "right at once", style: { background: "var(--ok)" }, says: "The first answer was right and the agent took it." },
  { key: "right after corrections", style: { background: "color-mix(in oklab, var(--ok) 70%, var(--bg))" }, says: "The agent corrected a wrong answer into a right one." },
  { key: "right, past the targets", style: { background: "color-mix(in oklab, var(--ok) 45%, var(--bg))" }, says: "Right, but over the token or the time target." },
  {
    key: "right, rejected by the agent",
    style: { background: "repeating-linear-gradient(135deg, var(--ok) 0 3px, color-mix(in oklab, var(--ok) 25%, var(--bg)) 3px 6px)" },
    says: "The layer's answer was right and the agent rejected it (over rounding, ordering and the like), then ran the exchange on to its four-answer cap.",
  },
  { key: "accepted wrong", style: { background: "var(--bad)" }, says: "The agent accepted an answer that was wrong." },
  { key: "never right", style: { background: "color-mix(in oklab, var(--bad) 40%, var(--bg))" }, says: "No answer in the exchange was right." },
];

/** Where the agent's gain comes from: how its exchanges ended, and what a precedent does that a compiled request does not. */
export default function Gain({ d }: { d: Accuracy }) {
  const total = Object.values(d.outcomes).reduce((a, b) => a + b, 0);
  return (
    <div className="mt-6 grid grid-cols-1 gap-x-12 gap-y-10 xl:grid-cols-2">
      <div>
        <p className="text-sm font-medium">How the agent's {total} exchanges ended</p>
        <div className="mt-3 flex h-4 overflow-hidden rounded-full bg-line" role="img" aria-label="The agent's exchanges by how they ended">
          {OUTCOMES.map((o) => (
            <div key={o.key} style={{ ...o.style, width: `${((d.outcomes[o.key] ?? 0) / total) * 100}%` }} />
          ))}
        </div>
        <ul className="mt-4 space-y-2.5">
          {OUTCOMES.map((o) => (
            <li key={o.key} className="grid grid-cols-[1rem_2.5rem_minmax(0,1fr)] items-baseline gap-x-2 text-sm">
              <span className="h-3 w-3 translate-y-0.5 rounded-[3px]" style={o.style} aria-hidden="true" />
              <span className="text-right font-semibold tabular-nums">{d.outcomes[o.key] ?? 0}</span>
              <span>
                <span className="font-medium">{o.key}</span> <span className="text-fg-muted">{o.says}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-sm font-medium">The first answer: a precedent, or a compiled request</p>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Route
            name="Precedent"
            says="The business's own query for a request like this one, its values set from the question."
            r={d.routes.precedent}
          />
          <Route name="Compiled" says="A request the layer writes from the semantic layer, for a question with no precedent." r={d.routes.compiled} />
        </div>
        <p className="mt-4 text-sm text-fg-muted">
          Most of the gain is precedent: the business's own query for a request like this one, with its values set from the question.
        </p>
      </div>
    </div>
  );
}

function Route({ name, says, r }: { name: string; says: string; r: FirstAnswers }) {
  return (
    <div className="rounded-card border border-line p-4">
      <p className="text-sm font-medium">{name}</p>
      <p className="mt-1 text-xs text-fg-muted">{says}</p>
      <p className="mt-4 text-2xl font-semibold tabular-nums tracking-tight">
        {r.right}
        <span className="text-base font-normal text-fg-muted"> of {r.n} right</span>
      </p>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line">
        <div className="h-full bg-ok" style={{ width: `${(r.right / r.n) * 100}%` }} />
      </div>
      <p className="mt-3 text-xs tabular-nums text-fg-muted">
        median {n(r.tokens_p50)} tokens, {r.seconds_p50} seconds
      </p>
    </div>
  );
}

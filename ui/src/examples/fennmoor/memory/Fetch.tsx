import { useMemo, useState } from "react";
import SchemaGraph from "../virtual/SchemaGraph";
import type { Virtual } from "../virtual/data";
import { MEMORY, n, type Context, type Memory, type Read } from "./data";

const HOP_STRENGTH = [1, 0.62, 0.32];
const HOP_WORDS = ["the node itself", "every relationship touching it", "the to-one ends of what was fetched"];

/** What a read does, in words. */
function says(r: Read, cap: number, quarters: number): string {
  if (r.hop === 0) return "The node, by its key.";
  if (r.inward) return r.windowed ? `The facts that point at it: since the start of ${quarters === 1 ? "last quarter" : `${quarters} quarters ago`}, the ${cap} most recent.` : `Every one that points at it, up to ${cap}.`;
  return "The one it points at, by the key its column holds.";
}

/*
  What is promoted: the template for an anchor, drawn on the generated schema. The node itself, every relationship touching it (the facts into it
  windowed and capped), then the to-one ends of what was fetched (a fact's dimensions). Pick a customer to see how much each read fetched.
*/
export default function Fetch({ m, v }: { m: Memory; v: Virtual }) {
  const [anchor, setAnchor] = useState("Customer");
  const [pick, setPick] = useState(m.contexts.findIndex((c) => c.key.endsWith("7129")));
  const reads = m.templates[anchor];
  const ctx: Context | null = anchor === "Customer" ? m.contexts[pick] : null;

  const tint = useMemo(() => {
    const nodes = new Map<string, { strength: number; badge?: string }>();
    for (const r of reads) {
      const have = nodes.get(r.label);
      const strength = Math.max(have?.strength ?? 0, HOP_STRENGTH[r.hop]);
      const total = ctx ? [...reads.filter((x) => x.label === r.label)].reduce((s, x) => s + (ctx.reads[x.name] ?? 0), 0) : null;
      nodes.set(r.label, { strength, badge: total === null ? undefined : n(total) });
    }
    return { color: MEMORY, nodes, edges: new Set(reads.filter((r) => r.type).map((r) => r.type as string)) };
  }, [reads, ctx]);

  const biggest = Math.max(...m.contexts.map((c) => c.nodes));
  return (
    <div className="mt-6">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
        <span className="text-fg-muted">Fetch the context of a</span>
        <div role="group" aria-label="Anchor" className="flex flex-wrap gap-1.5">
          {v.nodes.map((x) => (
            <button
              key={x.label}
              type="button"
              aria-pressed={anchor === x.label}
              onClick={() => setAnchor(x.label)}
              className={`rounded-md border px-2.5 py-1 text-xs transition-colors ${anchor === x.label ? "border-transparent text-bg" : "border-line text-fg-muted hover:text-fg"}`}
              style={anchor === x.label ? { background: MEMORY } : undefined}
            >
              {x.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_30rem]">
        <div className="rounded-card border border-line bg-bg-subtle p-3">
          <SchemaGraph d={v} pick={null} onPick={() => undefined} tint={tint} />
          <ul className="flex flex-wrap gap-x-5 gap-y-1 px-2 pb-1 text-xs text-fg-muted" aria-label="Key">
            {HOP_WORDS.map((w, i) => (
              <li key={w} className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-[3px] border-2" style={{ borderColor: MEMORY, background: `color-mix(in oklab, ${MEMORY} ${Math.round(8 + 22 * HOP_STRENGTH[i])}%, var(--bg))` }} aria-hidden="true" />
                hop {i}: {w}
              </li>
            ))}
            {ctx && <li>the number on a box: nodes fetched</li>}
          </ul>
        </div>

        <div className="xl:sticky xl:top-20">
          {ctx ? (
            <div className="mb-4 rounded-card border border-line p-4">
              <p className="text-xs text-fg-muted">A recorded context: {m.contexts.length} customers, from {n(Math.min(...m.contexts.map((c) => c.nodes)))} nodes to {n(biggest)}</p>
              <div className="mt-3 flex h-14 items-end gap-[3px]" role="group" aria-label="Customers">
                {m.contexts.map((c, i) => (
                  <button
                    key={c.key}
                    type="button"
                    aria-label={`Customer ending ${c.key.slice(-4)}: ${c.nodes} nodes`}
                    aria-pressed={i === pick}
                    onClick={() => setPick(i)}
                    className="flex-1 rounded-t-[3px] transition-opacity hover:opacity-100"
                    style={{ height: `${Math.max(6, (Math.log10(c.nodes) / Math.log10(biggest)) * 100)}%`, background: MEMORY, opacity: i === pick ? 1 : 0.35 }}
                  />
                ))}
              </div>
              <p className="mt-3 text-sm">
                <span className="font-semibold tabular-nums">{n(ctx.nodes)}</span> nodes, <span className="font-semibold tabular-nums">{n(ctx.edges)}</span> relationships, fetched in{" "}
                <span className="font-semibold tabular-nums">{ctx.seconds}</span> s
              </p>
              {ctx.capped.length > 0 && <p className="mt-1 text-xs text-fg-muted">Capped, and flagged on the context: {ctx.capped.map((c) => c.split(/<-|->|-/)[1] ?? c).join(", ")}.</p>}
            </div>
          ) : (
            <p className="mb-4 rounded-card border border-dashed border-line-strong p-4 text-xs text-fg-muted">
              The recorded contexts are customers'. Pick Customer to see how much each read fetched.
            </p>
          )}
          <ol className="max-h-[26rem] overflow-auto rounded-card border border-line bg-bg">
            {reads.map((r) => (
              <li key={r.name} className="border-b border-line px-4 py-2.5 last:border-b-0">
                <p className="flex items-baseline justify-between gap-3">
                  <span className="font-mono text-[11px] [overflow-wrap:anywhere]">
                    <span className="text-fg-muted">hop {r.hop} · </span>
                    {r.name}
                  </span>
                  {ctx && <span className="shrink-0 text-xs font-semibold tabular-nums">{n(ctx.reads[r.name] ?? 0)}{ctx.capped.includes(r.name) && <span className="ml-1 font-normal text-fg-muted">capped</span>}</span>}
                </p>
                <p className="mt-0.5 text-xs text-fg-muted">{says(r, m.settings.cap, m.settings.window_quarters)}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}

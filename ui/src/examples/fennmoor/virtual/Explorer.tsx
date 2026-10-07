import { useState } from "react";
import type { Pick, Virtual, VNode, VRel } from "./data";
import SchemaGraph from "./SchemaGraph";

const short = (table: string) => table.split(".").slice(-1)[0];

/** The view's SELECT, laid out to read: its columns, then its source. */
const pretty = (sql: string) => sql.replace(/^SELECT /, "SELECT\n  ").replace(/ FROM /, "\nFROM ");

/*
  The generated schema, to explore: the graph, and beside it how the selected node or relationship was made: what the semantic layer said, which column,
  and the view that exposes the table. The graph is read from the layer; nothing here is written by hand.
*/
export default function Explorer({ d }: { d: Virtual }) {
  const [pick, setPick] = useState<Pick>({ kind: "node", id: "Customer" });
  const [hover, setHover] = useState<Pick | null>(null);
  const shown = hover ?? pick;
  const node = (label: string) => d.nodes.find((n) => n.label === label)!;
  const rel = (type: string) => d.relationships.find((r) => r.type === type)!;
  const line =
    shown.kind === "node"
      ? `(:${shown.id})  ·  ${node(shown.id).table}`
      : `(:${rel(shown.id).start})-[:${shown.id}]->(:${rel(shown.id).end})  ·  ${short(rel(shown.id).table)}.${rel(shown.id).column}`;

  return (
    <div className="mt-6">
      <p className="h-6 overflow-hidden whitespace-nowrap font-mono text-xs text-fg-muted" aria-live="polite">
        {line}
      </p>
      <div className="mt-2 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_25rem]">
        <div className="rounded-card border border-line bg-bg-subtle p-3">
          <SchemaGraph d={d} pick={pick} onPick={setPick} onHover={setHover} />
          <ul className="flex flex-wrap gap-x-6 gap-y-1 px-2 pb-1 text-xs text-fg-muted" aria-label="Key">
            <li>box: a node label, keyed by the column shown</li>
            <li>arrow: a column that holds another node's key</li>
          </ul>
        </div>
        <div className="xl:sticky xl:top-20 xl:max-h-[calc(100svh-6rem)] xl:overflow-auto xl:rounded-card">
          {pick.kind === "node" ? <NodePanel d={d} n={node(pick.id)} onPick={setPick} /> : <EdgePanel d={d} r={rel(pick.id)} onPick={setPick} />}
        </div>
      </div>
    </div>
  );
}

function Fact({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3 py-2 text-sm">
      <dt className="text-fg-muted">{k}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function NodePanel({ d, n, onPick }: { d: Virtual; n: VNode; onPick: (p: Pick) => void }) {
  const out = d.relationships.filter((r) => r.start === n.label);
  const into = d.relationships.filter((r) => r.end === n.label);
  return (
    <section className="rounded-card border border-line bg-bg p-5" aria-label={`The ${n.label} node`}>
      <p className="text-xs uppercase tracking-wider text-fg-muted">Node label</p>
      <h4 className="text-xl font-semibold tracking-tight">{n.label}</h4>
      <dl className="mt-3 divide-y divide-line">
        <Fact k="Table">
          <span className="font-mono text-xs break-all">{n.table}</span>
        </Fact>
        <Fact k="Key">
          <span className="font-mono text-xs">{n.key}</span>
          {n.variable && <span className="text-fg-muted">, the variable "{n.variable}"</span>}
        </Fact>
        <Fact k="Why a node">{n.why}</Fact>
        {n.area && <Fact k="Area">{n.area}</Fact>}
      </dl>

      <Links title="Points at" rels={out} other={(r) => r.end} onPick={onPick} />
      <Links title="Pointed at by" rels={into} other={(r) => r.start} onPick={onPick} />

      <p className="mt-5 text-xs font-medium uppercase tracking-wider text-fg-muted">Properties · {n.properties.length}</p>
      <ul className="mt-2 grid grid-cols-1 gap-x-5 sm:grid-cols-2 xl:grid-cols-1">
        {n.properties.map(([name, type]) => (
          <li key={name} className="flex items-baseline justify-between gap-3 border-b border-line py-1 font-mono text-[11px]">
            <span className={name === n.key ? "font-semibold" : ""}>
              {name}
              {name === n.key && <span className="ml-1.5 rounded bg-fg px-1 text-[9px] font-normal text-bg">key</span>}
            </span>
            <span className="text-fg-muted">{type.toLowerCase()}</span>
          </li>
        ))}
      </ul>

      <p className="mt-5 text-xs font-medium uppercase tracking-wider text-fg-muted">The view it reads, in the graph's own dataset</p>
      <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{pretty(n.sql)}</pre>
    </section>
  );
}

function Links({ title, rels, other, onPick }: { title: string; rels: VRel[]; other: (r: VRel) => string; onPick: (p: Pick) => void }) {
  if (rels.length === 0) return null;
  return (
    <div className="mt-4">
      <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">{title}</p>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {rels.map((r) => (
          <li key={r.type}>
            <button
              type="button"
              onClick={() => onPick({ kind: "edge", id: r.type })}
              className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px] hover:border-line-strong"
            >
              {r.type} <span className="text-fg-muted">{title === "Points at" ? "→" : "←"} {other(r)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function EdgePanel({ d, r, onPick }: { d: Virtual; r: VRel; onPick: (p: Pick) => void }) {
  const start = d.nodes.find((n) => n.label === r.start)!;
  const end = d.nodes.find((n) => n.label === r.end)!;
  return (
    <section className="rounded-card border border-line bg-bg p-5" aria-label={`The ${r.type} relationship`}>
      <p className="text-xs uppercase tracking-wider text-fg-muted">Relationship type</p>
      <h4 className="text-xl font-semibold tracking-tight">{r.type}</h4>
      <p className="mt-1 font-mono text-xs">
        (:{r.start})-[:{r.type}]-&gt;(:{r.end})
      </p>
      <dl className="mt-3 divide-y divide-line">
        <Fact k="Follows">
          <span className="font-mono text-xs break-all">
            {short(r.table)}.{r.column}
          </span>
          <span className="text-fg-muted"> holds </span>
          <span className="font-mono text-xs break-all">
            {short(end.table)}.{r.endKey}
          </span>
        </Fact>
        {r.variable && <Fact k="Variable">{r.variable}</Fact>}
        <Fact k="Evidence">{r.why}</Fact>
      </dl>
      <p className="mt-4 text-sm leading-relaxed text-fg-muted">
        Rows of {start.label} point at rows of {end.label} through that column. Only trusted joins build a variable, so a join production contradicts never becomes
        a relationship.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {[start, end].map((n) => (
          <button
            key={n.label}
            type="button"
            onClick={() => onPick({ kind: "node", id: n.label })}
            className="rounded border border-line px-2 py-1 text-xs hover:border-line-strong"
          >
            {n.label}
          </button>
        ))}
      </div>
    </section>
  );
}

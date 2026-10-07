import { lazy, Suspense, useEffect, useRef, useState, type ReactNode } from "react";
import { cypher, getInfo, method, ServerError, sql, type Info, type MethodArgs, type QueryResult } from "./api";
import ResultTable from "./ResultTable";
import type { CypherSpec, LiveSpec, MethodPreset, MethodSpec, SqlSpec, Target } from "./types";

const ResultGraph = lazy(() => import("./ResultGraph")); // NVL is large: it loads when a result has a graph to draw

type Where = Target | "sql" | "ask";
const WHERE: Record<Where, { name: string; color: string }> = {
  layer: { name: "the semantic layer", color: "var(--shard-semantic)" },
  memory: { name: "memory", color: "var(--shard-memory)" },
  rows: { name: "the warehouse's rows, through Virtual Graph", color: "var(--shard-rows)" },
  composite: { name: "the composite: layer, rows and memory in one query", color: "var(--composite)" },
  sql: { name: "BigQuery", color: "var(--warehouse)" },
  ask: { name: "qlsc: the layer, the router, Virtual Graph and BigQuery", color: "var(--composite)" },
};

const START = "uv run examples/fennmoor-bank/server.py";

/*
  A control at the left of a part: pressed, it opens to the right on the query or the command behind what is above it, with Run. The query is a default to change
  and run as any other; it goes to the real database or warehouse, through the demo server (examples/fennmoor-bank/server.py), and only reads. Nothing is mocked.
*/
export default function LiveRun({ specs, hint = "Run it live" }: { specs: LiveSpec[]; hint?: string }) {
  const [open, setOpen] = useState(false);
  const [which, setWhich] = useState(0);
  const [server, setServer] = useState<{ info: Info } | { error: string } | null>(null);

  useEffect(() => {
    if (!open || server) return;
    let live = true;
    getInfo().then(
      (info) => live && setServer({ info }),
      (e: Error) => live && setServer({ error: e.message }),
    );
    return () => {
      live = false;
    };
  }, [open, server]);

  const spec = specs[Math.min(which, specs.length - 1)];
  return (
    <div className="mt-6 flex items-start gap-3">
      <button
        type="button"
        aria-expanded={open}
        aria-label={open ? "Close the live query" : hint}
        onClick={() => setOpen(!open)}
        className={`flex shrink-0 items-center gap-2 rounded-md border border-line text-xs transition-colors hover:border-line-strong hover:text-fg ${open ? "w-9 flex-col justify-start self-stretch bg-bg-subtle py-2.5 text-fg" : "h-9 px-2.5 text-fg-muted"}`}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M3 4.5l3.5 3.5L3 11.5" />
          <path d="M8.5 12H13" />
        </svg>
        {!open && <span>{hint}</span>}
      </button>
      <div className="grid min-w-0 flex-1 transition-[grid-template-columns] duration-300" style={{ gridTemplateColumns: open ? "1fr" : "0fr" }}>
        <div className="min-w-0 overflow-hidden">
          {open && (
            <div className="rounded-card border border-line">
              {specs.length > 1 && (
                <div role="tablist" className="flex gap-1 border-b border-line p-1.5 text-sm">
                  {specs.map((s, i) => (
                    <button
                      key={i}
                      type="button"
                      role="tab"
                      aria-selected={i === which}
                      onClick={() => setWhich(i)}
                      className={`rounded px-3 py-1 ${i === which ? "bg-fg text-bg" : "text-fg-muted hover:text-fg"}`}
                    >
                      {s.kind === "cypher" ? "Cypher" : s.kind === "sql" ? "SQL" : "Command"}
                    </button>
                  ))}
                </div>
              )}
              {!server ? (
                <p className="p-4 text-sm text-fg-muted">Connecting…</p>
              ) : "error" in server ? (
                <Down message={server.error} retry={() => setServer(null)} />
              ) : spec.kind === "cypher" ? (
                <CypherPanel key={which} spec={spec} info={server.info} />
              ) : spec.kind === "sql" ? (
                <SqlPanel key={which} spec={spec} info={server.info} />
              ) : (
                <MethodPanel key={which} spec={spec} info={server.info} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Down({ message, retry }: { message: string; retry: () => void }) {
  return (
    <div className="p-4 text-sm">
      <p>
        <strong className="font-medium">Not connected.</strong> <span className="text-fg-muted">{message}.</span> This runs against the real graph and warehouse through a small
        server on this machine. Start it from the repository root:
      </p>
      <pre className="mt-2 overflow-x-auto rounded-md bg-bg-subtle px-3 py-2 font-mono text-xs">{START}</pre>
      <button type="button" onClick={retry} className="mt-3 rounded-md border border-line px-3 py-1 text-xs hover:border-line-strong">
        Try again
      </button>
    </div>
  );
}

// ---- what every panel has

function Head({ where, children }: { where: Where; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line px-4 py-2.5 text-xs text-fg-muted">
      <span className="flex items-center gap-2 text-fg">
        <span className="inline-block h-2 w-2 rounded-full" style={{ background: WHERE[where].color }} />
        {WHERE[where].name}
      </span>
      <span className="ml-auto flex flex-wrap items-center gap-3">{children}</span>
    </div>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <label className="flex items-center gap-1.5">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)} className="max-w-[22rem] rounded border border-line bg-bg px-1.5 py-1 text-fg">
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

const Principal = ({ info, value, onChange }: { info: Info; value: string; onChange: (v: string) => void }) => (
  <Select label="Run as" value={value} onChange={onChange} options={info.principals.map((p) => ({ value: p.name, label: p.name === "admin" ? "admin (the data source)" : p.name }))} />
);

type Run<T> = { s: "idle" } | { s: "running"; since: number } | { s: "done"; r: T } | { s: "error"; message: string };

/** Runs a request, one at a time: a new one cancels the one before. */
function useRun<T>() {
  const [state, setState] = useState<Run<T>>({ s: "idle" });
  const abort = useRef<AbortController | null>(null);
  const start = (go: (signal: AbortSignal) => Promise<T>) => {
    abort.current?.abort();
    const a = (abort.current = new AbortController());
    setState({ s: "running", since: Date.now() });
    go(a.signal).then(
      (r) => !a.signal.aborted && setState({ s: "done", r }),
      (e: unknown) => !a.signal.aborted && setState({ s: "error", message: e instanceof ServerError ? e.message : String(e) }),
    );
  };
  useEffect(() => () => abort.current?.abort(), []);
  return [state, start] as const;
}

function Elapsed({ since }: { since: number }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => tick((n) => n + 1), 200);
    return () => clearInterval(t);
  }, []);
  return <span className="tabular-nums">{((Date.now() - since) / 1000).toFixed(1)} s</span>;
}

function Failure({ message }: { message: string }) {
  return (
    <div className="border-t border-line px-4 py-3 text-sm">
      <p className="whitespace-pre-wrap break-words" style={{ color: "var(--bad)" }}>
        {message}
      </p>
    </div>
  );
}

function Editor({ value, onChange, onRun, rows = 6 }: { value: string; onChange: (v: string) => void; onRun: () => void; rows?: number }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
          e.preventDefault();
          onRun();
        }
      }}
      rows={Math.min(14, Math.max(rows, value.split("\n").length))}
      spellCheck={false}
      aria-label="The query"
      className="block w-full resize-y border-0 bg-bg px-4 py-3 font-mono text-[13px] leading-relaxed outline-none"
    />
  );
}

function RunBar({ running, since, edited, reset, run, runLabel = "Run" }: { running: boolean; since?: number; edited: boolean; reset: () => void; run: () => void; runLabel?: string }) {
  return (
    <div className="flex items-center gap-3 border-t border-line bg-bg-subtle px-4 py-2 text-xs text-fg-muted">
      <button type="button" onClick={run} className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-accent-fg">
        {running ? "Run again" : runLabel}
      </button>
      <span className="hidden sm:inline">⌘↵ or Ctrl+↵</span>
      {edited && (
        <button type="button" onClick={reset} className="underline-offset-2 hover:underline">
          Reset to the default
        </button>
      )}
      <span className="ml-auto">{running && since ? <Elapsed since={since} /> : "Only reads."}</span>
    </div>
  );
}

// ---- results

const n = (x: number) => x.toLocaleString("en-US");

function Result({ r }: { r: QueryResult }) {
  const hasGraph = r.graph.nodes.length > 0;
  const [tab, setTab] = useState<"graph" | "table">(hasGraph ? "graph" : "table");
  const tabClass = (on: boolean) => `rounded px-2.5 py-1 ${on ? "bg-fg text-bg" : "hover:text-fg"}`;
  return (
    <div className="border-t border-line">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-4 py-2 text-xs text-fg-muted">
        <div role="tablist" className="flex gap-1">
          {hasGraph && (
            <button type="button" role="tab" aria-selected={tab === "graph"} onClick={() => setTab("graph")} className={tabClass(tab === "graph")}>
              Graph · {r.graph.nodes.length} nodes, {r.graph.relationships.length} relationships
            </button>
          )}
          <button type="button" role="tab" aria-selected={tab === "table"} onClick={() => setTab("table")} className={tabClass(tab === "table")}>
            Table · {n(r.rows.length)} {r.rows.length === 1 ? "row" : "rows"}
          </button>
        </div>
        <span className="ml-auto tabular-nums">
          {r.seconds.toFixed(2)} s · as {r.principal}
          {r.more && ` · the first ${n(r.rows.length)} of more`}
          {r.total !== undefined && r.total > r.rows.length && ` · the first ${n(r.rows.length)} of ${n(r.total)}`}
          {r.bytesBilled ? ` · ${(r.bytesBilled / 1048576).toFixed(0)} MiB billed` : ""}
        </span>
      </div>
      {tab === "graph" && hasGraph ? (
        <Suspense fallback={<p className="p-4 text-sm text-fg-muted">Loading the graph view…</p>}>
          <ResultGraph nodes={r.graph.nodes} rels={r.graph.relationships} />
        </Suspense>
      ) : (
        <ResultTable columns={r.columns} rows={r.rows} />
      )}
      {r.sent && (
        <details className="border-t border-line px-4 py-2 text-xs text-fg-muted">
          <summary className="cursor-pointer">What was sent to Virtual Graph (the gateway signed it)</summary>
          <pre className="mt-2 overflow-x-auto font-mono text-[12px] text-fg">{r.sent}</pre>
        </details>
      )}
    </div>
  );
}

// ---- Cypher and SQL

type Runner = (query: string, who: string, signed: boolean, signal: AbortSignal) => Promise<QueryResult>;

function QueryPanel({ spec, info, where, run }: { spec: CypherSpec | SqlSpec; info: Info; where: Where; run: Runner }) {
  const [preset, setPreset] = useState(0);
  const [text, setText] = useState(spec.presets[0].query);
  const [who, setWho] = useState("admin");
  const [signed, setSigned] = useState(true);
  const [state, start] = useRun<QueryResult>();
  const go = () => start((signal) => run(text, who, signed, signal));
  return (
    <div>
      <Head where={where}>
        {spec.presets.length > 1 && (
          <Select
            label="Query"
            value={String(preset)}
            onChange={(v) => {
              setPreset(Number(v));
              setText(spec.presets[Number(v)].query);
            }}
            options={spec.presets.map((p, i) => ({ value: String(i), label: p.label }))}
          />
        )}
        {spec.principals && <Principal info={info} value={who} onChange={setWho} />}
        {spec.kind === "cypher" && spec.unsigned && (
          <label className="flex items-center gap-1.5">
            <input type="checkbox" checked={signed} onChange={(e) => setSigned(e.target.checked)} />
            Sign it, as the gateway does
          </label>
        )}
      </Head>
      <Editor value={text} onChange={setText} onRun={go} />
      <RunBar
        running={state.s === "running"}
        since={state.s === "running" ? state.since : undefined}
        edited={text !== spec.presets[preset].query}
        reset={() => setText(spec.presets[preset].query)}
        run={go}
      />
      {state.s === "error" && <Failure message={state.message} />}
      {state.s === "done" && <Result r={state.r} />}
    </div>
  );
}

function CypherPanel({ spec, info }: { spec: CypherSpec; info: Info }) {
  return <QueryPanel spec={spec} info={info} where={spec.target} run={(query, principal, signed, signal) => cypher({ target: spec.target, query, principal, signed }, signal)} />;
}

function SqlPanel({ spec, info }: { spec: SqlSpec; info: Info }) {
  return <QueryPanel spec={spec} info={info} where="sql" run={(query, principal, _signed, signal) => sql({ query, principal }, signal)} />;
}

// ---- commands

const ROUTES = [
  { value: "auto", label: "the router's choice" },
  { value: "sql", label: "SQL only" },
  { value: "cypher", label: "Cypher over Virtual Graph only" },
  { value: "memory", label: "memory only" },
];

/** The command as it would be typed in a terminal, for the visitor to read. */
function commandLine(spec: MethodSpec, a: MethodPreset, principal: string): string {
  const as = principal === "admin" ? "" : ` --as ${principal}`;
  switch (spec.command) {
    case "ask":
      return `qlsc ask${a.route && a.route !== "auto" ? ` --${a.route}` : ""} --run${as} ${JSON.stringify(a.question ?? "")}`;
    case "recall":
      return `qlsc recall ${a.entity ?? "Customer"} ${a.key ?? ""}${as}`;
    case "composite":
      return "uv run examples/fennmoor-bank/demo.py composite";
    case "exchange":
      return `uv run examples/fennmoor-bank/demo.py exchange ${a.n ?? "0"}`;
  }
}

type Progress = { s: "idle" } | { s: "running"; since: number } | { s: "done"; code: number; seconds: number } | { s: "error"; message: string };

function MethodPanel({ spec, info }: { spec: MethodSpec; info: Info }) {
  const [preset, setPreset] = useState(0);
  const [a, setA] = useState<MethodPreset>(spec.presets[0]);
  const [who, setWho] = useState("admin");
  const [lines, setLines] = useState<{ line: string; at: number }[]>([]);
  const [status, setStatus] = useState<Progress>({ s: "idle" });
  const abort = useRef<AbortController | null>(null);
  const log = useRef<HTMLPreElement>(null);
  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => {
    log.current?.scrollTo({ top: log.current.scrollHeight });
  }, [lines]);

  const go = () => {
    abort.current?.abort();
    const ac = (abort.current = new AbortController());
    setLines([]);
    setStatus({ s: "running", since: Date.now() });
    const body: MethodArgs = { command: spec.command, principal: who, question: a.question, route: a.route, label: a.entity, key: a.key, n: a.n };
    method(
      body,
      (e) => {
        if (ac.signal.aborted) return;
        if (e.t === "out") setLines((l) => [...l, { line: e.line, at: e.at }]);
        else if (e.t === "end") setStatus({ s: "done", code: e.code, seconds: e.seconds });
        else setStatus({ s: "error", message: e.message });
      },
      ac.signal,
    ).catch((e: unknown) => !ac.signal.aborted && setStatus({ s: "error", message: e instanceof ServerError ? e.message : String(e) }));
  };

  const field = "w-full rounded border border-line bg-bg px-2.5 py-1.5 font-mono text-[13px]";
  return (
    <div>
      <Head where={spec.command === "composite" ? "composite" : spec.command === "recall" ? "memory" : "ask"}>
        {spec.presets.length > 1 && (
          <Select
            label="Example"
            value={String(preset)}
            onChange={(v) => {
              setPreset(Number(v));
              setA(spec.presets[Number(v)]);
            }}
            options={spec.presets.map((p, i) => ({ value: String(i), label: p.label }))}
          />
        )}
        {spec.principals && <Principal info={info} value={who} onChange={setWho} />}
      </Head>
      <div className="grid gap-3 px-4 py-3">
        {spec.command === "ask" && (
          <>
            <input aria-label="The question" value={a.question ?? ""} onChange={(e) => setA({ ...a, question: e.target.value })} onKeyDown={(e) => e.key === "Enter" && go()} className={field} />
            <div className="text-xs text-fg-muted">
              <Select label="Route" value={a.route ?? "auto"} onChange={(v) => setA({ ...a, route: v })} options={ROUTES} />
            </div>
          </>
        )}
        {spec.command === "recall" && (
          <div className="grid grid-cols-[8rem_1fr] gap-2">
            <input aria-label="The label" value={a.entity ?? ""} onChange={(e) => setA({ ...a, entity: e.target.value })} className={field} />
            <input aria-label="Its key" value={a.key ?? ""} onChange={(e) => setA({ ...a, key: e.target.value })} onKeyDown={(e) => e.key === "Enter" && go()} className={field} />
          </div>
        )}
        {spec.command === "exchange" && (
          <div className="text-xs text-fg-muted">
            <Select label="Question" value={a.n ?? "0"} onChange={(v) => setA({ ...a, n: v })} options={["0", "1", "2"].map((v) => ({ value: v, label: `number ${v}` }))} />
          </div>
        )}
        <pre className="overflow-x-auto rounded-md bg-bg-subtle px-3 py-2 font-mono text-xs text-fg-muted">$ {commandLine(spec, a, who)}</pre>
      </div>
      <RunBar
        running={status.s === "running"}
        since={status.s === "running" ? status.since : undefined}
        edited={JSON.stringify(a) !== JSON.stringify(spec.presets[preset])}
        reset={() => setA(spec.presets[preset])}
        run={go}
      />
      {status.s === "error" && <Failure message={status.message} />}
      {(lines.length > 0 || status.s === "running") && (
        <pre ref={log} className="max-h-96 overflow-auto border-t border-line bg-bg px-4 py-3 font-mono text-[12.5px] leading-relaxed">
          {lines.map((l, i) => (
            <div key={i} className="flex gap-3">
              <span className="w-12 shrink-0 select-none text-right tabular-nums text-fg-muted">{l.at.toFixed(1)}</span>
              <span className="min-w-0 whitespace-pre-wrap break-words">{l.line}</span>
            </div>
          ))}
          {status.s === "running" && <div className="text-fg-muted">…</div>}
        </pre>
      )}
      {status.s === "done" && (
        <p className="border-t border-line px-4 py-2 text-xs tabular-nums text-fg-muted">
          {status.code === 0 ? "Finished" : `Exited with code ${status.code}`} in {status.seconds.toFixed(1)} s
        </p>
      )}
    </div>
  );
}

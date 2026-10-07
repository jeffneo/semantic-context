import { useState } from "react";
import { MEMORY, type TraceConversation, type TraceDecision, type TraceLearned, type TraceMessage, type TraceTool, type Traces } from "./data";

const plural = (k: number, one: string, many = one + "s") => `${k} ${k === 1 ? one : many}`;
const took = (ms: number | null) => (ms === null ? "" : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`);

const counts = (c: TraceConversation) => ({
  messages: c.messages.length,
  tools: c.messages.reduce((a, m) => a + (m.tools?.length ?? 0), 0),
  learned: c.messages.reduce((a, m) => a + (m.learned?.length ?? 0), 0),
  decided: c.messages.reduce((a, m) => a + (m.decided?.length ?? 0), 0),
});

/*
  What an agent did, as memory keeps it: a conversation read back from the graph, with each task's tool calls under the message that began it. The conversations are the
  example's (conversations/*.yaml): the words are written down, and the tool calls ran for real against the layer and the warehouse. Memory keeps the words, each tool call
  with what it was asked, what came back, what it read and how long it took, what was learned, and what was decided and on what. It keeps no hidden reasoning: only a
  decision's stated rationale. The transcript can be read without the trace; a line still says where tools were called.
*/
export default function Trace({ t }: { t: Traces }) {
  const [which, setWhich] = useState(0);
  const [trace, setTrace] = useState(true);
  const c = t.conversations[which];
  const k = counts(c);
  return (
    <div className="mt-6">
      <div role="radiogroup" aria-label="A conversation" className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {t.conversations.map((x, i) => {
          const y = counts(x);
          const on = i === which;
          return (
            <button
              key={x.title}
              type="button"
              role="radio"
              aria-checked={on}
              onClick={() => setWhich(i)}
              className={`rounded-card border p-4 text-left transition-colors ${on ? "bg-bg-subtle" : "hover:border-line-strong"}`}
              style={{ borderColor: on ? MEMORY : "var(--line)" }}
            >
              <span className="block text-sm font-medium leading-snug">{x.title}</span>
              <span className="mt-1.5 block text-xs text-fg-muted">
                for {x.as} · {plural(y.messages, "message")}, {plural(y.tools, "tool call")}
                {y.decided > 0 && `, ${plural(y.decided, "decision")}`}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
        <p className="text-sm text-fg-muted">
          <span className="font-medium text-fg">{plural(k.tools, "tool call")}</span>, {plural(k.learned, "fact")} learned, {plural(k.decided, "decision")}, in {plural(k.messages, "message")}
        </p>
        <div role="group" aria-label="What to show" className="ml-auto flex gap-1 rounded-md border border-line p-1 text-sm">
          {[
            { on: false, label: "Transcript" },
            { on: true, label: "With the trace" },
          ].map((m) => (
            <button
              key={m.label}
              type="button"
              aria-pressed={trace === m.on}
              onClick={() => setTrace(m.on)}
              className={`rounded px-3 py-1 ${trace === m.on ? "bg-fg text-bg" : "text-fg-muted hover:text-fg"}`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <ol className="mt-4 border-t border-line">
        {c.messages.map((m, i) => (
          <Message key={i} m={m} trace={trace} />
        ))}
      </ol>

      <p className="mt-6 max-w-3xl text-sm text-fg-muted">
        Memory keeps no hidden reasoning, only the words, the tool calls and a decision's stated rationale. These are the example's written conversations: the tool calls in them ran for real, and this is the graph
        they left. Everything in it is owned by the principal it acted for, and private to them.
      </p>
    </div>
  );
}

function Message({ m, trace }: { m: TraceMessage; trace: boolean }) {
  const user = m.role === "user";
  const tools = m.tools ?? [];
  const learned = m.learned ?? [];
  const decided = m.decided ?? [];
  const did = [
    tools.length > 0 && `${plural(tools.length, "tool call")}: ${tools.map((x) => x.tool).join(", ")}`,
    learned.length > 0 && `${plural(learned.length, "fact")} learned`,
    decided.length > 0 && `${plural(decided.length, "decision")}`,
  ].filter(Boolean);
  return (
    <li className="grid grid-cols-[4.5rem_1fr] gap-x-4 border-b border-line py-4">
      <span className={`pt-0.5 text-xs font-medium uppercase tracking-wide ${user ? "text-fg" : "text-fg-muted"}`}>{user ? "User" : "Agent"}</span>
      <div className="min-w-0">
        <p className={`max-w-3xl leading-relaxed ${user ? "" : "text-fg-muted"}`}>{m.text}</p>
        {did.length > 0 && (
          <p className="mt-2 flex items-center gap-2 text-xs text-fg-muted">
            <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: MEMORY }} />
            {did.join(" · ")}
          </p>
        )}
        {trace && (
          <div className="mt-3 space-y-3">
            {tools.length > 0 && (
              <ul className="space-y-2">
                {tools.map((x, j) => (
                  <Tool key={j} x={x} />
                ))}
              </ul>
            )}
            {learned.length > 0 && <Learned items={learned} />}
            {decided.map((d, j) => (
              <Decision key={j} d={d} />
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

function Tool({ x }: { x: TraceTool }) {
  const how = x.tool === "recall" ? `from ${x.origin}, ${x.nodes} nodes` : `${x.route}${x.writer ? `, ${x.writer}` : ""}${x.fromMemory ? ", from memory" : ""}`;
  return (
    <li className="rounded-card border border-line p-3 text-sm">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-mono text-xs font-semibold">{x.tool}</span>
        <span className="text-xs text-fg-muted">{how}</span>
        <span className="ml-auto text-xs tabular-nums text-fg-muted">
          {x.status !== "ok" && <span className="mr-2 text-bad">{x.status}</span>}
          {took(x.ms)}
        </span>
      </div>
      <p className="mt-1.5 max-w-3xl">{x.asked}</p>
      {x.reads.length > 0 && (
        <p className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-fg-muted">
          read
          {x.reads.map((r) => (
            <span key={r.label + r.name} className="rounded border border-line px-1.5 py-0.5">
              {r.label} <span className="font-mono">{r.name}</span>
            </span>
          ))}
        </p>
      )}
      {x.query && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-fg-muted hover:text-fg">The query it ran</summary>
          <pre className="mt-2 overflow-x-auto rounded-md bg-bg-subtle px-3 py-2 font-mono text-xs leading-relaxed">{x.query}</pre>
        </details>
      )}
    </li>
  );
}

function Learned({ items }: { items: TraceLearned[] }) {
  return (
    <ul className="space-y-1 text-sm">
      {items.map((l, i) => (
        <li key={i} className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-xs font-medium text-fg-muted">learned</span>
          {l.entity ? (
            <span>
              {l.entity} ({l.entityType}), <span className="text-fg-muted">{l.predicate}</span>
            </span>
          ) : (
            <span>
              <span className="text-fg-muted">{l.predicate}:</span> {l.value}
            </span>
          )}
          {l.replaced && l.replaced !== l.value && l.because && (
            <span className="text-xs text-fg-muted">
              replaces “{l.replaced}” ({l.because === "corrected" ? "it was wrong" : "it changed"})
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

function Decision({ d }: { d: TraceDecision }) {
  return (
    <div className="rounded-card border border-l-[3px] p-3 text-sm" style={{ borderColor: "var(--line)", borderLeftColor: MEMORY }}>
      <p>
        <span className="text-xs font-medium text-fg-muted">decided </span>
        <span className="font-medium">{d.choice}</span>
      </p>
      <p className="mt-1 max-w-3xl text-fg-muted">{d.rationale}</p>
      {d.alternatives.length > 0 && <p className="mt-1.5 text-xs text-fg-muted">weighed: {d.alternatives.join("; ")}</p>}
      {d.basedOn.length > 0 && (
        <p className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-fg-muted">
          based on
          {d.basedOn.map((b, i) => (
            <span key={i} className="rounded border border-line px-1.5 py-0.5">
              {b.label === "Step" ? `a tool call: ${b.what}` : `${b.what}: ${b.value}`}
            </span>
          ))}
        </p>
      )}
      {d.outcome.length > 0 && <p className="mt-2 text-xs font-medium text-ok">outcome: {d.outcome.join(", ")}</p>}
    </div>
  );
}

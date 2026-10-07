import { useMemo, useState } from "react";
import type { Virtual, VQuestion } from "./data";
import SchemaGraph from "./SchemaGraph";

const VERDICT: Record<string, [word: string, tone: string]> = {
  correct: ["right", "text-ok"],
  wrong: ["wrong", "text-bad"],
  empty: ["no rows", "text-bad"],
  declined: ["declined", "text-fg-muted"],
  failed: ["failed", "text-bad"],
};
const verdict = (v: string) => VERDICT[v] ?? [v, "text-fg-muted"];

/** The labels and the relationship types a Cypher query walks, to light them on the schema. */
function walked(cypher: string, d: Virtual) {
  const labels = new Set([...cypher.matchAll(/\(\s*\w*\s*:\s*(\w+)/g)].map((m) => m[1]));
  const types = new Set([...cypher.matchAll(/\[\s*\w*\s*:\s*([A-Z0-9_|]+)/g)].flatMap((m) => m[1].split("|")));
  return {
    nodes: new Set(d.nodes.filter((n) => labels.has(n.label)).map((n) => n.label)),
    edges: new Set(d.relationships.filter((r) => types.has(r.type)).map((r) => r.type)),
  };
}

/*
  What the schema is for: questions that are natural over a graph (who handled a customer's calls, which merchants two customers share), answered in
  Cypher over the generated model. The labels and types a query walks light up. Ten hand-written questions, scored against the data by the same ruler as
  the other accuracy checks: directional, not a benchmark.
*/
export default function Questions({ d }: { d: Virtual }) {
  const [id, setId] = useState(d.questions[1]?.id ?? d.questions[0].id);
  const q = d.questions.find((x) => x.id === id) as VQuestion;
  const lit = useMemo(() => walked(q.cypher ?? "", d), [q, d]);
  const count = (pick: (x: VQuestion) => string) => d.questions.filter((x) => pick(x) === "correct").length;

  return (
    <div className="mt-6">
      <p className="max-w-3xl text-[17px] leading-relaxed">
        Over these {d.questions.length} questions, Cypher on the generated schema was right on {count((x) => x.cypher_verdict)}, SQL on {count((x) => x.sql_verdict)}, and
        the router's own pick on {count((x) => x.routed_verdict)}.
      </p>
      <div className="mt-5 grid grid-cols-1 items-start gap-5 xl:grid-cols-[22rem_minmax(0,1fr)]">
        <ul className="max-h-[40rem] overflow-auto rounded-card border border-line bg-bg-subtle p-1.5" aria-label="Questions">
          {d.questions.map((x) => {
            const [cw, ct] = verdict(x.cypher_verdict);
            const [sw, st] = verdict(x.sql_verdict);
            return (
              <li key={x.id}>
                <button
                  type="button"
                  aria-pressed={x.id === id}
                  onClick={() => setId(x.id)}
                  className={`w-full rounded-md px-3 py-2.5 text-left transition-colors ${x.id === id ? "bg-bg shadow-[inset_0_0_0_1px_var(--line-strong)]" : "hover:bg-bg"}`}
                >
                  <span className="line-clamp-2 block text-sm leading-snug">{x.text}</span>
                  <span className="mt-1.5 flex gap-4 text-[11px]">
                    <span>
                      <span className="text-fg-muted">Cypher </span>
                      <span className={ct}>{cw}</span>
                    </span>
                    <span>
                      <span className="text-fg-muted">SQL </span>
                      <span className={st}>{sw}</span>
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>

        <section className="rounded-card border border-line p-5" aria-label={`Question ${q.id}`}>
          <p className="text-xs text-fg-muted">
            <span className="font-mono text-fg">{q.id}</span> · the reference answer has {q.rows.toLocaleString("en-US")} rows
          </p>
          <p className="mt-1 text-base font-medium leading-snug">{q.text}</p>
          <div className="mt-3 rounded-card border border-line bg-bg-subtle p-2">
            <SchemaGraph d={d} pick={null} onPick={() => undefined} lit={lit} />
          </div>
          <dl className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
            <Verdict name="Cypher, over the schema" v={q.cypher_verdict} why={q.cypher_why} />
            <Verdict name="SQL, over the tables" v={q.sql_verdict} why={q.sql_why} />
            <Verdict name="The router chose" v={q.routed_verdict} why={q.routed} />
          </dl>
          <p className="mt-5 text-xs font-medium uppercase tracking-wider text-fg-muted">The Cypher it wrote</p>
          <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{q.cypher ?? "None was written: the model declined the question."}</pre>
        </section>
      </div>
    </div>
  );
}

function Verdict({ name, v, why }: { name: string; v: string; why: string }) {
  const [word, tone] = verdict(v);
  return (
    <div className="rounded-md border border-line p-3">
      <dt className="text-xs text-fg-muted">{name}</dt>
      <dd className={`mt-0.5 font-medium ${tone}`}>{word}</dd>
      <dd className="mt-1 text-xs leading-relaxed text-fg-muted">{why}</dd>
    </div>
  );
}

import { useState } from "react";
import { n, RUNGS, type Router, type RungId, type Trace as TraceT } from "./data";

const VERDICT: Record<string, [string, string]> = {
  correct: ["right", "text-ok"],
  wrong: ["wrong", "text-bad"],
  empty: ["no rows", "text-bad"],
};
const verdict = (v: string) => VERDICT[v] ?? [v, "text-fg-muted"];

type Row = { id: RungId; state: "served" | "declined" | "not reached" | "not exercised"; why: string };

/** The ladder as this question fell down it: the first two rungs were not part of the evaluation, the rest are as recorded. */
function rows(t: TraceT): Row[] {
  return [
    { id: "memory", state: "not exercised", why: "" },
    { id: "precedent", state: "not exercised", why: "" },
    { id: "compiled", ...t.compiled },
    { id: "cypher", ...t.cypher },
    { id: "free", ...t.free },
  ];
}

/*
  Ten questions that are natural over a graph, as the router took them. Compiled SQL is tried first; when its request does not compile, free Cypher
  over the generated schema; when that declines, free SQL. What each declined is the model's own reason, recorded.
*/
export default function Trace({ r }: { r: Router }) {
  const [id, setId] = useState(r.trace.find((t) => t.routed === "cypher")?.id ?? r.trace[0].id);
  const t = r.trace.find((x) => x.id === id) as TraceT;
  const fall = rows(t);
  const [word, tone] = verdict(t.verdict);
  let order = 0; // the rungs the request reached, in turn: each dot drops after the one before

  return (
    <div className="mt-6 grid grid-cols-1 items-start gap-5 xl:grid-cols-[22rem_minmax(0,1fr)]">
      <ul className="max-h-[44rem] overflow-auto rounded-card border border-line bg-bg-subtle p-1.5" aria-label="Questions">
        {r.trace.map((x) => {
          const rung = RUNGS.find((u) => u.id === x.routed)!;
          const [w, c] = verdict(x.verdict);
          return (
            <li key={x.id}>
              <button
                type="button"
                aria-pressed={x.id === id}
                onClick={() => setId(x.id)}
                className={`w-full rounded-md px-3 py-2.5 text-left transition-colors ${x.id === id ? "bg-bg shadow-[inset_0_0_0_1px_var(--line-strong)]" : "hover:bg-bg"}`}
              >
                <span className="line-clamp-2 block text-sm leading-snug">{x.text}</span>
                <span className="mt-1.5 flex items-center gap-2 text-[11px]">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: rung.color }} aria-hidden="true" />
                  <span className="text-fg-muted">served by {rung.name}</span>
                  <span className={c}>{w}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      <section className="rounded-card border border-line p-5" aria-label={`Question ${t.id}`}>
        <p className="text-xs text-fg-muted">
          <span className="font-mono text-fg">{t.id}</span> · the reference answer has {n(t.rows)} rows
        </p>
        <p className="mt-1 text-base font-medium leading-snug">{t.text}</p>

        <ol key={t.id} className="mt-5">
          {fall.map((f, i) => {
            const rung = RUNGS[i];
            const reached = f.state === "served" || f.state === "declined";
            const mine = reached ? order++ : 0;
            return (
              <li key={f.id} className="relative grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 pb-4 last:pb-0">
                {i < fall.length - 1 && <span className="absolute bottom-0 left-[11px] top-6 w-px bg-line-strong" aria-hidden="true" />}
                <span className="z-10 grid h-6 w-6 place-items-center" aria-hidden="true">
                  <span
                    className={`h-3.5 w-3.5 rounded-full border-2 ${reached ? "fall" : ""}`}
                    style={{
                      "--i": mine,
                      borderColor: rung.color,
                      background: f.state === "served" ? rung.color : "var(--bg)",
                      opacity: reached ? undefined : 0.45,
                    } as React.CSSProperties}
                  />
                </span>
                <div className={f.state === "not reached" || f.state === "not exercised" ? "opacity-60" : ""}>
                  <p className="flex flex-wrap items-baseline gap-x-3 text-sm">
                    <span className="font-medium">{rung.name}</span>
                    <span className="text-xs text-fg-muted">
                      {f.state === "served"
                        ? "served"
                        : f.state === "declined"
                          ? "did not stand"
                          : f.state === "not reached"
                            ? "not reached"
                            : "not part of this evaluation"}
                    </span>
                  </p>
                  {f.why && <p className="mt-1 text-xs leading-relaxed text-fg-muted">{f.why}</p>}
                </div>
              </li>
            );
          })}
        </ol>

        <div className="mt-5 grid grid-cols-1 gap-3 border-t border-line pt-4 sm:grid-cols-[10rem_minmax(0,1fr)]">
          <div>
            <p className="text-xs text-fg-muted">Scored against the reference</p>
            <p className={`mt-0.5 text-lg font-semibold ${tone}`}>{word}</p>
          </div>
          <p className="self-end text-xs leading-relaxed text-fg-muted">{t.verdictWhy}</p>
        </div>

        <p className="mt-4 text-xs font-medium uppercase tracking-wider text-fg-muted">The {t.queryKind === "cypher" ? "Cypher" : "SQL"} that served</p>
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{t.query}</pre>
      </section>
    </div>
  );
}

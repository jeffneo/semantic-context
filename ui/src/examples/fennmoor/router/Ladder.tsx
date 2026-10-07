import { n, RUNGS, type Router, type RungId } from "./data";

/** What each rung has been measured at, by the evaluation that exercised it. */
function stats(r: Router): Record<RungId, { value: string; label: string }[]> {
  const m = r.memory;
  return {
    memory: [
      { value: `${m.fromMemory} of ${m.questions}`, label: `questions about five customers answered from memory, ${m.sameRows} with the same rows as the SQL` },
      { value: `${m.memoryMedian} s`, label: `median, against ${m.sqlMedian} s for the SQL in BigQuery` },
      { value: `${n(m.sessionMibWithout)} → ${n(m.sessionMibWith)} MiB`, label: "billed over the session, the fetch included" },
    ],
    precedent: [
      { value: `${r.agent.precedent.right} of ${r.agent.precedent.n}`, label: "right, of the agent's first answers that were a precedent" },
      { value: n(r.agent.precedent.tokensMedian), label: `tokens, median, in ${r.agent.precedent.secondsMedian} s` },
    ],
    compiled: [
      { value: `${r.log.compiled.n} of ${r.log.n}`, label: "log questions compiled, one shot" },
      { value: `${r.log.compiled.right} right`, label: "of those that compiled" },
      { value: n(r.agent.sql.tokensMedian), label: `tokens, median, in ${r.agent.sql.secondsMedian} s: the agent's first answers that were SQL` },
    ],
    cypher: [
      { value: `${r.graph.cypherRight} of ${r.graph.n}`, label: `graph-shaped questions right by Cypher (SQL alone: ${r.graph.sqlRight})` },
      { value: `${r.graph.picked.cypher.n}`, label: `of those it was the router's pick, ${r.graph.picked.cypher.right} right` },
    ],
    free: [{ value: `${r.log.free.n} of ${r.log.n}`, label: `log questions needed it (one went to Cypher), ${r.log.rungs.free.right} of ${r.log.rungs.free.n} right` }],
  };
}

/*
  The rule: five rungs, tried in order, cheapest first, and the first whose answer stands serves. There is no model deciding: each rung says for itself whether
  it can answer, and the router takes the first that can.
*/
export default function Ladder({ r }: { r: Router }) {
  const all = stats(r);
  return (
    <ol className="relative mt-6">
      <span className="absolute bottom-6 left-[15px] top-6 w-px bg-line-strong" aria-hidden="true" />
      {RUNGS.map((rung, i) => (
        <li key={rung.id} className="relative grid grid-cols-[2rem_minmax(0,1fr)] gap-x-4 pb-5 last:pb-0">
          <span
            className="z-10 mt-4 grid h-8 w-8 place-items-center rounded-full text-sm font-semibold text-bg"
            style={{ background: rung.color }}
            aria-hidden="true"
          >
            {i + 1}
          </span>
          <div className="grid grid-cols-1 gap-x-8 gap-y-3 rounded-card border p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]" style={{ borderColor: `color-mix(in oklab, ${rung.color} 40%, var(--line))` }}>
            <div>
              <h4 className="text-base font-semibold tracking-tight">{rung.name}</h4>
              <p className="mt-1 text-sm leading-relaxed">{rung.is}</p>
              <p className="mt-2 text-sm text-fg-muted">
                <span className="font-medium text-fg">Serves when</span> {rung.serves.charAt(0).toLowerCase() + rung.serves.slice(1)}
              </p>
            </div>
            <ul className="grid content-start gap-2">
              {all[rung.id].map((s) => (
                <li key={s.value + s.label} className="flex items-baseline gap-3 text-xs">
                  <span className="w-28 shrink-0 text-right text-sm font-semibold tabular-nums">{s.value}</span>
                  <span className="text-fg-muted">{s.label}</span>
                </li>
              ))}
            </ul>
          </div>
        </li>
      ))}
    </ol>
  );
}

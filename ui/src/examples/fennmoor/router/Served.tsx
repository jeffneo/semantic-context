import { n, RUNGS, type Hit, type Router, type RungId } from "./data";

interface Set {
  name: string;
  note: string;
  parts: { rung: RungId; label?: string; hit: Hit }[];
}

/*
  Which rung served, in each evaluation that ran the router. They are different question sets with different rungs switched on, so they are not
  compared with each other: each shows what the router did on that set, and how the answers it chose did.
*/
export default function Served({ r }: { r: Router }) {
  const sets: Set[] = [
    {
      name: `The agent's ${r.agent.precedent.n + r.agent.sql.n} questions`,
      note: "precedent first, then SQL. Memory and Cypher were not switched on, and the agent's first answers are counted.",
      parts: [
        { rung: "precedent", hit: r.agent.precedent },
        { rung: "compiled", label: "Compiled or free SQL", hit: r.agent.sql },
      ],
    },
    {
      name: `${r.log.n} questions from the log, one shot`,
      note: "compiled SQL, then free Cypher, then free SQL. No agent, no memory, no precedent.",
      parts: [
        { rung: "compiled", hit: r.log.rungs.compiled },
        { rung: "cypher", hit: r.log.rungs.cypher },
        { rung: "free", hit: r.log.rungs.free },
      ],
    },
    {
      name: `${r.graph.n} graph-shaped questions`,
      note: "the same three rungs, on questions chosen because they are natural over a graph.",
      parts: [
        { rung: "compiled", hit: { n: r.trace.filter((t) => t.routed === "compiled").length, right: r.trace.filter((t) => t.routed === "compiled" && t.verdict === "correct").length } },
        { rung: "cypher", hit: r.graph.picked.cypher },
        { rung: "free", hit: { n: r.trace.filter((t) => t.routed === "free").length, right: r.trace.filter((t) => t.routed === "free" && t.verdict === "correct").length } },
      ],
    },
    {
      name: `${r.memory.questions} questions about five customers`,
      note: "with their contexts remembered. Right here means the same rows as the SQL.",
      parts: [{ rung: "memory", hit: { n: r.memory.fromMemory, right: r.memory.sameRows } }],
    },
  ];

  return (
    <div className="mt-6 space-y-7">
      {sets.map((s) => {
        const total = s.parts.reduce((sum, p) => sum + p.hit.n, 0);
        return (
          <figure key={s.name}>
            <figcaption className="flex flex-wrap items-baseline gap-x-3">
              <span className="text-sm font-medium">{s.name}</span>
              <span className="text-xs text-fg-muted">{s.note}</span>
            </figcaption>
            <div className="mt-2 flex h-5 gap-0.5 overflow-hidden rounded-md" role="img" aria-label={`${s.name}: ${s.parts.map((p) => `${p.hit.n} by ${p.label ?? RUNGS.find((u) => u.id === p.rung)!.name}`).join(", ")}`}>
              {s.parts.map((p) => (
                <div key={p.rung} className="relative" style={{ width: `${(p.hit.n / total) * 100}%`, background: RUNGS.find((u) => u.id === p.rung)!.color, minWidth: 3 }} />
              ))}
            </div>
            <ul className="mt-2 flex flex-wrap gap-x-7 gap-y-1 text-xs">
              {s.parts.map((p) => (
                <li key={p.rung} className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: RUNGS.find((u) => u.id === p.rung)!.color }} aria-hidden="true" />
                  <span className="font-medium">{p.label ?? RUNGS.find((u) => u.id === p.rung)!.name}</span>
                  <span className="tabular-nums text-fg-muted">
                    {n(p.hit.n)} served, {n(p.hit.right)} right
                  </span>
                </li>
              ))}
            </ul>
          </figure>
        );
      })}
    </div>
  );
}

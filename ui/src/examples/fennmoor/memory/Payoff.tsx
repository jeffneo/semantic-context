import { MEMORY, n, type Memory } from "./data";

const GREY = "var(--warehouse)"; // the warehouse's colour in the architecture

/*
  What promotion buys, from one recorded session: fifty questions about five customers, each answered as SQL in BigQuery and from memory (its cache off
  for the SQL, as a first-time query). The five contexts were fetched together before the first question.
*/
export default function Payoff({ m }: { m: Memory }) {
  const s = m.session;
  const cards = [
    { value: `${s.memoryMedian} s`, label: `a question from memory, median, against ${s.sqlMedian} s as SQL` },
    { value: `${s.secondsWithout} → ${s.secondsWith} s`, label: "query time over the session, the fetch included" },
    { value: `${n(s.mibWithout)} → ${n(s.mibWith)} MiB`, label: "billed by BigQuery over the session, the fetch included" },
    { value: `${s.sameAnswer} of ${s.fromMemory}`, label: "answers from memory with the same rows as the SQL" },
  ];
  return (
    <div className="mt-6">
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="rounded-card border border-line p-4">
            <dd className="text-2xl font-semibold tabular-nums tracking-tight">{c.value}</dd>
            <dt className="mt-1 text-xs leading-relaxed text-fg-muted">{c.label}</dt>
          </div>
        ))}
      </dl>
      <div className="mt-6 grid grid-cols-1 gap-x-10 gap-y-8 xl:grid-cols-2">
        <Cumulative m={m} />
        <Strip m={m} />
      </div>
      <Fetches m={m} />
    </div>
  );
}

/** Time spent as questions are asked: SQL every time, or one fetch and then memory. */
function Cumulative({ m }: { m: Memory }) {
  const { questions: qs, fetchSeconds } = m.session;
  const sql: number[] = [0];
  const mem: number[] = [fetchSeconds];
  qs.forEach((q, i) => {
    sql.push(sql[i] + q.sql);
    mem.push(mem[i] + q.memory);
  });
  const cross = sql.findIndex((v, i) => mem[i] <= v);
  const [W, H, L, R, T, B] = [640, 300, 46, 14, 14, 36];
  const top = Math.ceil(Math.max(sql[sql.length - 1], mem[mem.length - 1]) / 10) * 10;
  const x = (i: number) => L + (i / qs.length) * (W - L - R);
  const y = (v: number) => H - B - (v / top) * (H - T - B);
  const line = (a: number[]) => a.map((v, i) => `${i ? "L" : "M"}${x(i)} ${y(v)}`).join(" ");
  return (
    <figure>
      <figcaption className="text-sm font-medium">
        Time spent, as the questions are asked <span className="font-normal text-fg-muted">seconds</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 h-auto w-full" role="img" aria-label="Cumulative query time: SQL every time against one fetch and then memory">
        {[0, 10, 20, 30, 40].filter((v) => v <= top).map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--line)" />
            <text x={L - 8} y={y(v) + 4} textAnchor="end" fontSize={11} className="fill-fg-muted">
              {v}
            </text>
          </g>
        ))}
        {[0, 10, 20, 30, 40, 50].map((i) => (
          <text key={i} x={x(i)} y={H - 14} textAnchor="middle" fontSize={11} className="fill-fg-muted">
            {i}
          </text>
        ))}
        <text x={(L + W - R) / 2} y={H - 1} textAnchor="middle" fontSize={11} className="fill-fg-muted">
          questions asked
        </text>
        {cross > 0 && (
          <g>
            <line x1={x(cross)} x2={x(cross)} y1={T} y2={H - B} stroke="var(--fg)" strokeDasharray="4 4" opacity={0.4} />
            <text x={x(cross) + 6} y={T + 12} fontSize={11} className="fill-fg">
              pays back after {cross} questions
            </text>
          </g>
        )}
        <path d={line(sql)} fill="none" stroke={GREY} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
        <path d={line(mem)} fill="none" stroke={MEMORY} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
        <text x={x(qs.length) - 6} y={y(sql[sql.length - 1]) - 8} textAnchor="end" fontSize={12} fontWeight={600} fill={GREY}>
          SQL each time: {sql[sql.length - 1].toFixed(1)} s
        </text>
        <text x={x(qs.length) - 6} y={y(mem[mem.length - 1]) - 8} textAnchor="end" fontSize={12} fontWeight={600} fill={MEMORY}>
          fetched once, then memory: {mem[mem.length - 1].toFixed(1)} s
        </text>
      </svg>
      <p className="mt-1 text-xs text-fg-muted">
        Memory starts at {fetchSeconds} s: the {Object.values(m.session.fetches).find((f) => f.seconds === fetchSeconds)?.customers ?? ""} customers' contexts fetched together, once. Every question after that is a local graph read.
      </p>
    </figure>
  );
}

/** Each question's time, both ways, on one log scale. */
function Strip({ m }: { m: Memory }) {
  const [W, H, L, R] = [640, 250, 20, 20];
  const [lo, hi] = [Math.log10(0.01), Math.log10(3)];
  const x = (v: number) => L + ((Math.log10(v) - lo) / (hi - lo)) * (W - L - R);
  const rows = [
    { name: "SQL in BigQuery", color: GREY, y: 70, v: m.session.questions.map((q) => q.sql), median: m.session.sqlMedian },
    { name: "from memory", color: MEMORY, y: 165, v: m.session.questions.map((q) => q.memory), median: m.session.memoryMedian },
  ];
  return (
    <figure>
      <figcaption className="text-sm font-medium">
        Each of the fifty questions, both ways <span className="font-normal text-fg-muted">seconds, log scale</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 h-auto w-full" role="img" aria-label="Each question's time as SQL and from memory">
        {[0.01, 0.1, 1].map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={14} y2={H - 30} stroke="var(--line)" />
            <text x={x(v)} y={H - 12} textAnchor="middle" fontSize={11} className="fill-fg-muted">
              {v} s
            </text>
          </g>
        ))}
        {rows.map((r) => (
          <g key={r.name}>
            <text x={L} y={r.y - 36} fontSize={12} fontWeight={600} fill={r.color}>
              {r.name}
            </text>
            {r.v.map((v, i) => (
              <circle key={i} cx={x(v)} cy={r.y + ((i * 7) % 5) * 8 - 16} r={4} fill={r.color} opacity={0.55} />
            ))}
            <line x1={x(r.median)} x2={x(r.median)} y1={r.y - 26} y2={r.y + 24} stroke={r.color} strokeWidth={2.5} />
            <text x={x(r.median) + 7} y={r.y + 44} fontSize={11} className="fill-fg-muted">
              median {r.median} s
            </text>
          </g>
        ))}
      </svg>
    </figure>
  );
}

/** What a fetch costs, and how many questions about a customer it takes to pay for it in bytes billed. */
function Fetches({ m }: { m: Memory }) {
  return (
    <div className="mt-8">
      <h4 className="text-base font-semibold tracking-tight">What a fetch costs</h4>
      <p className="mt-1 max-w-3xl text-sm text-fg-muted">
        A warehouse bills the columns a query scans, not the rows it returns, so fetching many customers together costs about what one does. The break-even is
        the questions about one customer after which fetching has billed less than running each question's SQL.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs text-fg-muted">
              <th className="pb-2 pr-4 font-medium">Fetched</th>
              <th className="pb-2 pr-4 text-right font-medium">Customers</th>
              <th className="pb-2 pr-4 text-right font-medium">Seconds</th>
              <th className="pb-2 pr-4 text-right font-medium">MiB billed per customer</th>
              <th className="pb-2 text-right font-medium">Break-even, questions per customer</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(m.session.fetches)
              .sort((a, b) => b[1].breakEven - a[1].breakEven)
              .map(([name, f]) => (
                <tr key={name}>
                  <td className="border-t border-line py-2.5 pr-4">{name}</td>
                  <td className="border-t border-line py-2.5 pr-4 text-right tabular-nums">{f.customers}</td>
                  <td className="border-t border-line py-2.5 pr-4 text-right tabular-nums">{f.seconds}</td>
                  <td className="border-t border-line py-2.5 pr-4 text-right tabular-nums">{f.mibPerCustomer}</td>
                  <td className="border-t border-line py-2.5 text-right font-semibold tabular-nums">{f.breakEven}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

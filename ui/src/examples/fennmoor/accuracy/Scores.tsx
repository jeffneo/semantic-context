import { METHOD_COLOR, n, pct, wilson, type Accuracy } from "./data";

/*
  The headline: how often each method's answer is right on the questions written from the business's own queries. The bar is the score and the
  bracket on it the 95% interval (Wilson): how far a score on this many questions can be trusted.
*/
export default function Scores({ d }: { d: Accuracy }) {
  const questions = d.methods[0].log.n;
  const [agent, layer] = [d.methods[3], d.methods[2]].map((m) => ({ m, ci: wilson(m.log.right, m.log.n) }));
  const naive = d.methods.slice(0, 2).reduce((a, b) => (b.log.right > a.log.right ? b : a));
  const naiveCi = wilson(naive.log.right, naive.log.n);
  const agentClear = agent.ci[0] > naiveCi[1]; // the agent's interval lies wholly above the best naive method's
  const layerOverlaps = layer.ci[0] <= naiveCi[1];

  return (
    <div className="mt-6">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[880px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs text-fg-muted">
              <th className="pb-3 pr-6 font-medium">Method</th>
              <th className="pb-3 pr-6 font-medium">Right, of {questions} questions</th>
              <th className="pb-3 pr-6 text-right font-medium">Delivered</th>
              <th className="pb-3 pr-6 text-right font-medium">Tokens a request</th>
              <th className="pb-3 pr-6 text-right font-medium">Seconds</th>
              <th className="pb-3 text-right font-medium">Cost per right answer</th>
            </tr>
          </thead>
          <tbody>
            {d.methods.map((m) => {
              const [lo, hi] = wilson(m.log.right, m.log.n);
              const score = m.log.right / m.log.n;
              const ours = m.id === "agent";
              const cell = `border-t border-line py-4 ${ours ? "bg-bg-subtle" : ""}`;
              return (
                <tr key={m.id}>
                  <td className={`${cell} pl-3 pr-6`}>
                    <p className={ours ? "font-semibold" : "font-medium"}>{m.name}</p>
                    <p className="mt-0.5 max-w-xs text-xs text-fg-muted">{m.blurb}</p>
                  </td>
                  <td className={`${cell} pr-6`}>
                    <div className="flex items-center gap-4">
                      <div className="relative h-3 min-w-[240px] flex-1 rounded-full bg-line">
                        <div className="absolute inset-y-0 left-0 rounded-full" style={{ width: pct(score), background: METHOD_COLOR[m.id] }} />
                        <div
                          aria-hidden="true"
                          className="absolute -inset-y-1 border-x-2 border-fg/60"
                          style={{ left: `${lo * 100}%`, width: `${(hi - lo) * 100}%` }}
                        >
                          <span className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-fg/60" />
                        </div>
                      </div>
                      <p className="w-28 text-right tabular-nums">
                        <span className={`text-lg ${ours ? "font-semibold" : "font-medium"}`}>{pct(score)}</span>
                        <span className="ml-2 text-xs text-fg-muted">
                          {Math.round(lo * 100)}–{Math.round(hi * 100)}
                        </span>
                      </p>
                    </div>
                    <p className="mt-1 text-xs text-fg-muted">
                      {m.log.right} of {m.log.n}
                    </p>
                  </td>
                  <td className={`${cell} pr-6 text-right tabular-nums`}>{m.log.delivered}</td>
                  <td className={`${cell} pr-6 text-right tabular-nums`}>{n(m.log.tokens_p50)}</td>
                  <td className={`${cell} pr-6 text-right tabular-nums`}>{m.log.seconds_p50}</td>
                  <td className={`${cell} pr-3 text-right tabular-nums`}>${(m.log.cost / m.log.right).toFixed(3)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-fg-muted">
        Delivered: right, and inside the service's targets of {n(d.targets.tokens)} tokens and {d.targets.seconds} seconds a request. Tokens and seconds
        are medians. The bracket is the 95% interval of the score.
      </p>
      <p className="mt-5 max-w-3xl text-[17px] leading-relaxed">
        An agent that uses the layer is right on {pct(agent.m.log.right / agent.m.log.n)}; the same model with only the schema, on{" "}
        {pct(Math.min(...d.methods.slice(0, 2).map((m) => m.log.right / m.log.n)))} to {pct(naive.log.right / naive.log.n)}.
        {agentClear && " That lead is well outside the noise."}{" "}
        {layerOverlaps && (
          <span className="text-fg-muted">
            The layer's one-shot score ({pct(layer.m.log.right / layer.m.log.n)}) is higher than the schema's, but the intervals overlap: on its own it is not
            what makes the difference.
          </span>
        )}
      </p>
    </div>
  );
}

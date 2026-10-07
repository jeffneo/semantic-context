import { n, type Security } from "./data";

const CONTROL: Record<string, string> = {
  "navigation unfiltered (the trace shows everything; queries still run as the principal)": "The gateway tells a principal about tables and columns it cannot read",
  "hidden columns and their filter values shown": "Hidden columns and their filter values are shown",
  "SQL run as the estate, not the principal": "SQL is run as the estate, not as the principal",
  "the gateway signs as the data source, not the principal": "The gateway signs every query as the data source",
};
const BY: Record<string, string> = { schema: "the schema check", rows: "the rows check" };

/*
  The warehouse as the oracle. Each principal asked every gold question and six probes, by both routes. Schema: nothing the gateway says names what they cannot
  read. Rows: every BigQuery job Virtual Graph ran for them is theirs in the warehouse's own job log. Then gateways broken on purpose, to see each check catch.
*/
export default function Checked({ d }: { d: Security }) {
  return (
    <div className="mt-6">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs text-fg-muted">
              <th className="pb-2 pr-4 font-medium">Principal</th>
              <th className="pb-2 pr-4 text-right font-medium">Questions</th>
              <th className="pb-2 pr-4 text-right font-medium">Schema leaks</th>
              <th className="pb-2 pr-4 text-right font-medium">Row incidents</th>
              <th className="pb-2 pr-4 text-right font-medium">Answered by SQL</th>
              <th className="pb-2 pr-4 text-right font-medium">Answered by Cypher</th>
              <th className="pb-2 pr-4 text-right font-medium">Strings looked for</th>
              <th className="pb-2 text-right font-medium">Warehouse agrees</th>
            </tr>
          </thead>
          <tbody>
            {d.evaluation.map((e) => (
              <tr key={e.principal}>
                <th scope="row" className="border-t border-line py-3 pr-4 text-left font-medium">
                  {e.principal}
                </th>
                <td className="border-t border-line py-3 pr-4 text-right tabular-nums">{e.questions}</td>
                <td className="border-t border-line py-3 pr-4 text-right font-semibold tabular-nums">{e.schemaLeaks}</td>
                <td className="border-t border-line py-3 pr-4 text-right font-semibold tabular-nums">{e.rowIncidents}</td>
                <td className="border-t border-line py-3 pr-4 text-right tabular-nums">{e.sqlAnswered}</td>
                <td className="border-t border-line py-3 pr-4 text-right tabular-nums">{e.cypherAnswered}</td>
                <td className="border-t border-line py-3 pr-4 text-right tabular-nums">{n(d.principals.find((p) => p.name === e.principal)?.canaries ?? 0)}</td>
                <td className={`border-t border-line py-3 text-right ${e.oracleAgrees ? "text-ok" : "text-bad"}`}>{e.oracleAgrees ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 max-w-3xl text-xs leading-relaxed text-fg-muted">
        Cypher answers fewer questions than SQL because the Virtual Graph models only some of the tables and the question must fit them; when it does answer, it ran as the principal.
        &ldquo;Strings looked for&rdquo; are what the schema check searched every response and prompt for: unreadable tables, hidden columns, their filter values, and the log's people.
      </p>

      <h4 className="mt-8 text-base font-semibold tracking-tight">Broken on purpose, to see the checks catch it</h4>
      <ul className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-2">
        {d.controls.map((c) => (
          <li key={c.name} className="flex items-baseline justify-between gap-4 rounded-card border border-line p-4 text-sm">
            <span>{CONTROL[c.name] ?? c.name}</span>
            <span className={`shrink-0 text-xs font-medium ${c.caught ? "text-ok" : "text-bad"}`}>{c.caught ? `caught by ${BY[c.by] ?? c.by}` : "not caught"}</span>
          </li>
        ))}
        {d.driver.map((x) => (
          <li key={x.name} className="flex items-baseline justify-between gap-4 rounded-card border border-line p-4 text-sm">
            <span>{x.name.charAt(0).toUpperCase() + x.name.slice(1)}</span>
            <span className={`shrink-0 text-xs font-medium ${x.refused ? "text-ok" : "text-bad"}`}>{x.refused ? "refused" : "ran"}</span>
          </li>
        ))}
      </ul>

      <h4 className="mt-8 text-base font-semibold tracking-tight">What this does not cover</h4>
      <ul className="mt-3 grid max-w-3xl list-disc gap-2 pl-5 text-sm leading-relaxed text-fg-muted marker:text-fg-muted">
        <li>
          <span className="text-fg">The principals are impersonated service accounts</span> standing in for people. Workforce or OIDC identity is a later step.
        </li>
        <li>
          <span className="text-fg">No result cache is keyed by principal,</span> because Virtual Graph keeps none that was found. If it does, it must key by principal.
        </li>
        <li>
          <span className="text-fg">One estate, three test principals,</span> over a synthetic bank. The checks show the mechanism holds there, not that it holds everywhere.
        </li>
      </ul>
    </div>
  );
}

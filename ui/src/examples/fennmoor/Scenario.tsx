import { SOURCE_NAMES, WAREHOUSE } from "./data";

const day = (iso: string, plus = 0) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + plus);
  return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
};

export default function Scenario() {
  const { log, teams, serviceAccounts } = WAREHOUSE;
  const sources = [...new Set(WAREHOUSE.projects.flatMap((p) => p.datasets.map((d) => d.source)).filter((s): s is string => !!s))].map(
    (s) => SOURCE_NAMES[s] ?? s,
  );
  const facts: [string, string][] = [
    ["The bank", "A US regional retail bank (fictional)"],
    ["The estate", "BigQuery, built up the way real ones are: sources replicated raw, a dbt-built warehouse, Looker, a legacy EDW and analysts' sandboxes"],
    ["Source systems", `${sources.slice(0, 8).join(", ")} and ${sources.length - 8} more`],
    ["Who queries it", `${teams} teams and ${serviceAccounts} service accounts`],
    ["The record", `${log.jobs.toLocaleString("en-US")} queries over ${log.days} days, ${day(log.start)} to ${day(log.start, log.days - 1)}`],
  ];
  return (
    <div className="mt-8 grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <div className="max-w-2xl space-y-4 text-[17px] leading-relaxed">
        <p>
          {WAREHOUSE.org} has a data estate that nobody has written down. Over the years its tables, views and models have accumulated across three
          projects, and what each one means, which can be joined to which, and which to trust lives in people's heads.
        </p>
        <p>
          What does exist is a record of what people did with it: every query run over {log.days} days, and BigQuery's catalog of what is where.
          That is all the engine is given. From it, it infers the meaning, builds the layer an agent needs to answer questions about the bank, and
          keeps what it learns.
        </p>
        <p className="text-fg-muted">The warehouse itself, as BigQuery holds it, is next.</p>
      </div>
      <dl className="divide-y divide-line self-start rounded-card border border-line text-sm">
        {facts.map(([k, v]) => (
          <div key={k} className="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-4 px-4 py-3">
            <dt className="text-fg-muted">{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

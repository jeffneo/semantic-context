import type { Discovery } from "./data";

const n = (x: number) => x.toLocaleString("en-US");

interface Stage {
  n: number;
  label: string;
  says: string;
  /** the layer's own output, drawn in its colour */
  out?: boolean;
}

/*
  How the log narrows to the semantic layer, stage by stage. Bars are on a log scale (the first is 315,729 and the last 4), centred so the shape is a
  funnel. Each count is what the build found, not a figure from the plan.
*/
export default function Funnel({ d, queries, days }: { d: Discovery; queries: number; days: number }) {
  const f = d.funnel;
  const stages: Stage[] = [
    { n: queries, label: "queries run", says: `Everything the warehouse's log recorded in ${days} days: by people, dashboards and pipelines.` },
    { n: f.texts, label: "distinct texts", says: "A query run again with other dates or values is the same text once." },
    {
      n: f.shapes,
      label: "query shapes",
      says: `A query with its literals taken out. Each is parsed into the tables, columns, filters and joins it uses, and so are the ${f.viewShapes} view definitions.`,
    },
    { n: f.joinKeys, label: "join keys", says: "Pairs of columns a query joined on, with who joined them and how often." },
    {
      n: f.variables,
      label: "variables",
      says: `The real-world thing joined columns share, such as a customer or an account: ${f.joined} of the warehouse's ${n(f.columns)} columns.`,
      out: true,
    },
    { n: f.groups["1"], label: "groups", says: "Columns and variables the business reads together, found from the queries.", out: true },
    { n: f.groups["2"], label: "areas", says: "Groups that belong together, one level up.", out: true },
    { n: f.groups["3"], label: "broad areas", says: "The business in a handful of parts, each named from what is in it.", out: true },
  ];
  const widest = Math.log10(stages[0].n);
  return (
    <ol className="mt-6 divide-y divide-line rounded-card border border-line">
      {stages.map((s) => (
        <li key={s.label} className="grid grid-cols-[6.5rem_minmax(0,1fr)] items-center gap-x-5 gap-y-1 px-4 py-3 md:grid-cols-[9rem_minmax(0,1fr)_minmax(0,19rem)]">
          <div>
            <p className="text-right text-2xl font-semibold tabular-nums tracking-tight md:text-left">{n(s.n)}</p>
            <p className="text-right text-xs text-fg-muted md:text-left">{s.label}</p>
          </div>
          <div className="h-3 rounded-full bg-bg-subtle">
            <div
              className="mx-auto h-full rounded-full"
              style={{
                width: `${Math.max(3, (Math.log10(s.n) / widest) * 100)}%`,
                background: s.out ? "var(--shard-semantic)" : "color-mix(in oklab, var(--fg) 55%, var(--bg))",
              }}
            />
          </div>
          <p className="col-span-2 text-xs leading-relaxed text-fg-muted md:col-span-1">{s.says}</p>
        </li>
      ))}
    </ol>
  );
}

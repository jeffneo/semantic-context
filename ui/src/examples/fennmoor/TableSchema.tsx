import { fullName, type Located } from "./data";

/** The selected table: its full name, how it is stored, its columns, and a view's definition. A column the search matches is marked. */
export default function TableSchema({ located, highlight }: { located: Located; highlight: string }) {
  const { project, dataset, table } = located;
  const facts = [
    table.kind === "view" ? "view" : table.kind === "sharded" ? `date-sharded, ${table.shards} daily tables` : "table",
    `${table.columns.length} columns`,
    table.partition && `partitioned by ${table.partition}`,
    table.cluster?.length && `clustered by ${table.cluster.join(", ")}`,
  ].filter(Boolean);
  return (
    <section className="rounded-card border border-line bg-bg p-5" aria-label={`Schema of ${fullName(located)}`}>
      <p className="font-mono text-sm break-all">
        <span className="text-fg-muted">
          {project.name}.{dataset.name}.
        </span>
        <span className="font-semibold">{table.name}</span>
      </p>
      <p className="mt-1 text-sm text-fg-muted">{facts.join(" · ")}</p>

      <ul className="mt-5 grid content-start gap-x-8 sm:grid-cols-2 xl:grid-cols-1">
        {table.columns.map(([name, type]) => {
          const hit = highlight !== "" && name.toLowerCase().includes(highlight);
          return (
            <li key={name} className="flex items-baseline justify-between gap-4 border-b border-line py-1.5 font-mono text-xs">
              <span className={hit ? "rounded bg-link/15 px-1 font-semibold text-fg" : ""}>{name}</span>
              <span className="text-right break-all text-fg-muted">{type}</span>
            </li>
          );
        })}
      </ul>
      {table.sql && (
        <div className="mt-6">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-muted">Definition</p>
          <pre className="max-h-80 overflow-auto rounded-md border border-line bg-bg-subtle p-4 font-mono text-xs leading-relaxed">{table.sql}</pre>
        </div>
      )}
    </section>
  );
}

import { useDeferredValue, useMemo, useState } from "react";
import { ALL, fullName, SOURCE_NAMES, TOTALS, WAREHOUSE, type Dataset, type Located, type Project, type Table } from "./data";
import TableSchema from "./TableSchema";

const PROJECT_NOTES: Record<string, string> = {
  "fennmoor-raw": "Source systems, replicated as they are",
  "fennmoor-dw": "Staging, intermediate models, marts and ML scores",
  "fennmoor-analytics": "A legacy EDW, BI caches, sandboxes",
};
const LAYER_NAMES: Record<string, string> = {
  raw: "raw",
  staging: "staging",
  intermediate: "intermediate",
  mart: "marts",
  ml: "ML",
  legacy: "legacy",
  sandbox: "sandbox",
  bi: "BI cache",
  ops: "operations",
};

const TILE = 14; // px; with a 3px gap
const GAP = 3;
const across = (n: number) => Math.max(2, Math.ceil(Math.sqrt(n * 1.8))); // roughly square blocks, whatever the table count

/** The table a visitor starts on: a customer dimension, the kind of table every question about the bank reaches. */
const START = ALL.find((l) => fullName(l) === "fennmoor-dw.dw_core.dim_customer") ?? ALL[0];

export default function Warehouse() {
  const [selected, setSelected] = useState<Located>(START);
  const [hovered, setHovered] = useState<Located | null>(null);
  const [query, setQuery] = useState("");
  const q = useDeferredValue(query.trim().toLowerCase());

  // A table matches by its name or by any of its columns' names: searching for a join key lights every table that carries it.
  const found = useMemo(() => {
    if (!q) return null;
    const hit = ALL.filter((l) => fullName(l).toLowerCase().includes(q) || l.table.columns.some(([c]) => c.toLowerCase().includes(q)));
    return new Set(hit.map((l) => l.table));
  }, [q]);
  const shown = hovered ?? selected;

  return (
    <div className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
        <ul className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-fg-muted" aria-label="Key">
          <li className="flex items-center gap-2">
            <span className="tile table static" aria-hidden="true" /> {TOTALS.byKind.table} tables
          </li>
          <li className="flex items-center gap-2">
            <span className="tile view static" aria-hidden="true" /> {TOTALS.byKind.view} views
          </li>
          <li className="flex items-center gap-2">
            <span className="tile sharded static" aria-hidden="true" /> {TOTALS.byKind.sharded} date-sharded families
          </li>
        </ul>
        <label className="relative block w-full sm:w-80">
          <span className="sr-only">Find a table or a column</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Find a table or a column, e.g. cif_number"
            className="w-full rounded-md border border-line bg-bg px-3 py-2 text-sm outline-none placeholder:text-fg-muted/70 focus:border-line-strong"
          />
        </label>
      </div>

      {/* One line, in a fixed place: the name of the square under the pointer (or the selected one). Nothing floats over the map. */}
      <p className="mt-4 flex h-6 items-baseline gap-3 overflow-hidden whitespace-nowrap font-mono text-xs text-fg-muted" aria-live="polite">
        <span className="text-fg">{fullName(shown)}</span>
        <span>
          {shown.table.kind}
          {shown.table.shards ? `, ${shown.table.shards} daily tables` : ""}, {shown.table.columns.length} columns
        </span>
        {found && <span className="ml-auto pl-4">{found.size === 0 ? "no matches" : `${found.size} match "${q}"`}</span>}
      </p>

      {/* On a wide screen the schema sits beside the map and stays in view while the map is scrolled; on a narrow one it follows it. */}
      <div className="mt-2 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_26rem]">
        <div className="grid grid-cols-1 gap-5">
          {WAREHOUSE.projects.map((p) => (
            <ProjectPanel key={p.name} project={p} found={found} selected={selected} onHover={setHovered} onSelect={setSelected} />
          ))}
        </div>
        <div className="xl:sticky xl:top-20 xl:max-h-[calc(100svh-6rem)] xl:overflow-auto xl:rounded-card">
          <TableSchema located={selected} highlight={q} />
        </div>
      </div>
    </div>
  );
}

function ProjectPanel(props: {
  project: Project;
  found: Set<Table> | null;
  selected: Located;
  onHover: (l: Located | null) => void;
  onSelect: (l: Located) => void;
}) {
  const { project } = props;
  const count = project.datasets.reduce((n, d) => n + d.tables.length, 0);
  const datasets = [...project.datasets].sort((a, b) => b.tables.length - a.tables.length || a.name.localeCompare(b.name));
  return (
    <section className="rounded-card border border-line bg-bg-subtle p-4" aria-label={project.name}>
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="font-mono text-sm font-medium">{project.name}</h3>
        <span className="text-xs tabular-nums text-fg-muted">
          {project.datasets.length} datasets, {count} tables
        </span>
      </div>
      <p className="mt-0.5 text-xs text-fg-muted">{PROJECT_NOTES[project.name]}</p>
      <div className="mt-4 flex flex-wrap gap-x-5 gap-y-4">
        {datasets.map((d) => (
          <DatasetBlock key={d.name} {...props} dataset={d} />
        ))}
      </div>
    </section>
  );
}

function DatasetBlock({
  project,
  dataset,
  found,
  selected,
  onHover,
  onSelect,
}: {
  project: Project;
  dataset: Dataset;
  found: Set<Table> | null;
  selected: Located;
  onHover: (l: Located | null) => void;
  onSelect: (l: Located) => void;
}) {
  const n = dataset.tables.length;
  const width = across(n) * (TILE + GAP) - GAP;
  const label = dataset.source ? (SOURCE_NAMES[dataset.source] ?? dataset.source) : (LAYER_NAMES[dataset.layer] ?? dataset.layer);
  return (
    <div role="group" aria-label={`${project.name}.${dataset.name}`} className="w-fit">
      <p className="whitespace-nowrap font-mono text-[11px] leading-tight">{dataset.name}</p>
      <p className="mb-1.5 whitespace-nowrap text-[10px] leading-tight text-fg-muted">
        {label} · {n}
      </p>
      <div className="flex flex-wrap" style={{ width, gap: GAP }}>
        {dataset.tables.map((table) => {
          const l: Located = { project, dataset, table };
          const same = selected.table === table;
          const dim = found !== null && !found.has(table);
          return (
            <button
              key={table.name}
              type="button"
              aria-label={fullName(l)}
              aria-pressed={same}
              className={`tile ${table.kind}${same ? " sel" : ""}${dim ? " dim" : ""}`}
              onMouseEnter={() => onHover(l)}
              onMouseLeave={() => onHover(null)}
              onFocus={() => onHover(l)}
              onBlur={() => onHover(null)}
              onClick={() => onSelect(l)}
            />
          );
        })}
      </div>
    </div>
  );
}

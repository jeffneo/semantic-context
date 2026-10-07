import type { Virtual } from "./data";

/*
  How the model is made, in the order the build does it, with what each step found here. The wording is the build's own (qlsc/virtualize.py).
*/
export default function Steps({ d }: { d: Virtual }) {
  const steps = [
    {
      name: "Scope",
      count: d.inScope,
      unit: "tables",
      says: `The tables to model. By default, every table production builds; here, the ${d.inScope} the configuration names.`,
    },
    {
      name: "Nodes",
      count: d.nodes.length,
      unit: "labels",
      says: "A table is a node where a variable's trusted joins converge on one of its columns, or where production's MERGE key identifies its rows. Every key is checked unique in the data.",
    },
    {
      name: "Relationships",
      count: d.relationships.length,
      unit: "types",
      says: "A column of one node's table that holds the variable another node is keyed by points at that node. Suspect joins never become relationships.",
    },
    {
      name: "Names",
      count: d.nodes.length + d.relationships.length,
      unit: "names, by a model",
      says: "A model names the labels and the types. They are checked to be unique and never one memory reserves.",
    },
    {
      name: "Views",
      count: d.nodes.length,
      unit: "views",
      says: "One view per node's table, in a dataset of their own. Virtual Graph reads one dataset.",
    },
  ];
  return (
    <div className="mt-6">
      <ol className="grid grid-cols-1 gap-3 md:grid-cols-5">
        {steps.map((s, i) => (
          <li key={s.name} className="relative rounded-card border border-line p-4">
            <p className="flex items-center gap-2 text-xs text-fg-muted">
              <span className="grid h-5 w-5 place-items-center rounded-full text-[11px] font-semibold text-bg" style={{ background: "var(--shard-rows)" }}>
                {i + 1}
              </span>
              {s.name}
            </p>
            <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight">
              {s.count} <span className="text-sm font-normal text-fg-muted">{s.unit}</span>
            </p>
            <p className="mt-2 text-xs leading-relaxed text-fg-muted">{s.says}</p>
          </li>
        ))}
      </ol>

      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-card border border-dashed border-line-strong px-5 py-4" style={{ borderColor: "var(--shard-rows)" }}>
        <p className="text-3xl font-semibold tabular-nums tracking-tight">0</p>
        <p className="min-w-0 flex-1 text-sm leading-relaxed">
          <span className="font-medium">rows copied.</span> <span className="text-fg-muted">The views are SELECTs over the source tables. Virtual Graph translates each Cypher query into SQL when it is asked and runs it in the warehouse, so it reads the rows as they are now.</span>
        </p>
      </div>
    </div>
  );
}

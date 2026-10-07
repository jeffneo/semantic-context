import { useEffect, useState, type ReactNode } from "react";
import Compare from "./Compare";
import Explorer from "./Explorer";
import Questions from "./Questions";
import Steps from "./Steps";
import type { Virtual } from "./data";

/*
  The Virtual Graph section: the model qlsc generates from the semantic layer so the warehouse's rows can be read as a graph, without copying them
  (qlsc virtualize). How it is made, the result to explore, and what it answers. Every table, key and reason is the build's own.
*/
export default function VirtualBody() {
  const [d, setD] = useState<Virtual | null>(null);
  useEffect(() => {
    let live = true;
    void import("./virtual.json").then((m) => live && setD(m.default as unknown as Virtual));
    return () => {
      live = false;
    };
  }, []);

  if (!d) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading the generated schema…</div>;
  return (
    <div>
      <Part title="From the semantic layer to a graph schema" lead="Warehouses rarely declare their keys, so the model is written from usage: where the business's trusted joins converge, and what points at what.">
        <Steps d={d} />
      </Part>
      <Part
        title="Two pictures of one model"
        lead="The semantic layer holds the paths; the Virtual Graph holds the schema made from them. Pick a table, a column, a variable, a box or an arrow, and what it makes or is made from lights in both."
      >
        <Compare d={d} />
      </Part>
      <Part title="The generated schema" lead="Select a box or an arrow to see how it was made: what the layer said, the column, and the view that exposes the table.">
        <Explorer d={d} />
        <Left d={d} />
      </Part>
      <Part title="What it is for" lead="Questions that are natural over a graph: who handled a customer's calls, which merchants two customers share. Pick one to see the part of the schema its Cypher walks.">
        <Questions d={d} />
      </Part>
    </div>
  );
}

/** What was kept out of the model, and why: a model that says what it left out can be trusted about what it kept. */
function Left({ d }: { d: Virtual }) {
  return (
    <div className="mt-8">
      <h4 className="text-base font-semibold tracking-tight">Left out</h4>
      <ul className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-3">
        {d.leftOut.map((x) => (
          <li key={x.name} className="rounded-card border border-line p-4 text-sm">
            <p className="font-mono text-xs break-all">{x.name}</p>
            <p className="mt-1 text-xs text-fg-muted">{x.what === "table" ? "not a node: " : "not a relationship: "}{x.why}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Part({ title, lead, children }: { title: string; lead: string; children: ReactNode }) {
  return (
    <div className="mt-14 first:mt-8">
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-1 max-w-3xl text-fg-muted">{lead}</p>
      {children}
    </div>
  );
}

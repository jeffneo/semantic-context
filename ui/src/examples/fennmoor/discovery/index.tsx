import { useEffect, useState } from "react";
import Part from "../../Part";
import { LIVE } from "../live";
import { WAREHOUSE } from "../data";
import type { Discovery } from "./data";
import Funnel from "./Funnel";
import Joins from "./Joins";
import KeptOut from "./KeptOut";
import Regroup from "./Regroup";

/*
  The discovery section: what the build made of the query log (qlsc build, read from the layer's graph). A funnel for the scale, the tables regrouped
  by meaning for the result, and the joins for the evidence. Counts and names are the build's own; the area names and descriptions were written by a model
  from what each holds.
*/
export default function DiscoveryBody() {
  const [d, setD] = useState<Discovery | null>(null);
  useEffect(() => {
    let live = true;
    void import("./discovery.json").then((m) => live && setD(m.default as unknown as Discovery));
    return () => {
      live = false;
    };
  }, []);

  if (!d) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading the semantic layer…</div>;
  return (
    <div>
      <Part summary={`${WAREHOUSE.log.jobs.toLocaleString("en-US")} queries in, ${d.funnel.groups["1"]} groups out: each stage keeps only what the one before it supports.`} title="From a query log to a layer" lead="Nothing was written down. The build reads the log and the catalog, and each stage keeps only what the one before it supports." live={LIVE.discovery.funnel}>
        <Funnel d={d} queries={WAREHOUSE.log.jobs} days={WAREHOUSE.log.days} />
      </Part>
      <Part
        live={LIVE.discovery.regroup}
        title="The tables, regrouped by meaning"
        lead="Tables are filed by where they came from. The layer groups what the business reads together, whichever dataset it is in. Colours are the four broad areas: switch to By dataset to see them scattered."
      >
        <Regroup d={d} />
      </Part>
      <Part summary="Columns the business joins are one real-world thing: which variables join which tables." title="What the joins revealed" lead="Columns the business joins are one real-world thing. Each variable is found from the joins queries actually made." live={LIVE.discovery.joins}>
        <Joins d={d} />
      </Part>
      <Part
        live={LIVE.discovery.keptOut}
        summary="Queries also join things that are not the same thing: the joins left out of the variables, and why."
        title="Joins the layer would not merge on"
        lead="Queries do join things that are not the same thing. Where production keeps two id spaces apart and translates between them, a join that equates them is left out of the variables, so one customer's account number never becomes another system's."
      >
        <KeptOut d={d} />
      </Part>
    </div>
  );
}


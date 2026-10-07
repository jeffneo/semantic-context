import { useEffect, useState } from "react";
import Part from "../../Part";
import { LIVE } from "../live";
import Ladder from "./Ladder";
import Served from "./Served";
import Trace from "./Trace";
import type { Router } from "./data";

/*
  The router section: how a request reaches the source data. A rule over five rungs, each measured by the evaluation that exercised it; ten questions
  followed down the ladder as they fell; and what each evaluation's router served. The figures are the evaluations' own (results/).
*/
export default function RouterBody() {
  const [r, setR] = useState<Router | null>(null);
  useEffect(() => {
    let live = true;
    void import("./router.json").then((m) => live && setR(m.default as unknown as Router));
    return () => {
      live = false;
    };
  }, []);

  if (!r) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading the router's evidence…</div>;
  return (
    <div>
      <Part
        live={LIVE.router.ladder}
        title="A rule, not a model"
        lead="Five rungs, cheapest first. Each says for itself whether it can answer; the first whose answer stands serves, and the ones below it never run."
      >
        <Ladder r={r} />
      </Part>
      <Part
        live={LIVE.router.trace(r)}
        summary="Ten questions followed down the rungs, with why each one served or declined." title="A question, down the ladder"
        lead="Ten questions that are natural over a graph, as the router took them. When the request compiles, compiled SQL serves; when it does not, free Cypher over the generated schema is tried, and when that declines too, free SQL."
      >
        <Trace r={r} />
      </Part>
      <Part summary="What the router chose in each evaluation, and how often it was right." title="What each rung served" lead="The evaluations that ran the router, and what it chose on each. They are different questions with different rungs switched on.">
        <Served r={r} />
      </Part>
      <Part summary="Free Cypher reaches what a request cannot express, but only over the tables the graph models." title="Where the Cypher rung does not reach" lead="Free Cypher reaches what a request cannot express, but only over the tables the Virtual Graph models.">
        <p className="mt-4 max-w-3xl text-[17px] leading-relaxed">
          On the {r.log.n} questions from the log, the Cypher route alone was right on {r.log.cypher.correct}, declined {r.log.cypher.declined}, and for{" "}
          {r.log.cypher["not covered"]} none of the tables was in the graph, which here models {r.graph.tables}. The router took it once, and it was wrong. On the questions
          chosen for the graph it was the router's pick on {r.graph.picked.cypher.n} of {r.graph.n}, and right on {r.graph.picked.cypher.right}. Between the two
          routes, {r.log.eitherRight} of the {r.log.n} log questions were answered right by one or the other, against {r.log.sqlRight} by SQL alone.
        </p>
      </Part>
    </div>
  );
}


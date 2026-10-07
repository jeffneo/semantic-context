import { useEffect, useState } from "react";
import Part from "../../Part";
import { LIVE } from "../live";
import type { Virtual } from "../virtual/data";
import Fetch from "./Fetch";
import Governed from "./Governed";
import Holds from "./Holds";
import Payoff from "./Payoff";
import Trace from "./Trace";
import type { Memory, Traces } from "./data";
import { n } from "./data";

/*
  The memory section: a Virtual Graph read promoted into memory (qlsc remember). What is fetched, what it buys, how long it holds, and how it stays governed.
  Every figure is from the memory evaluations' own results (results/) or the layer.
*/
export default function MemoryBody() {
  const [d, setD] = useState<{ m: Memory; v: Virtual; t: Traces } | null>(null);
  useEffect(() => {
    let live = true;
    void Promise.all([import("./memory.json"), import("../virtual/virtual.json"), import("./traces.json")]).then(
      ([m, v, t]) => live && setD({ m: m.default as unknown as Memory, v: v.default as unknown as Virtual, t: t.default as unknown as Traces }),
    );
    return () => {
      live = false;
    };
  }, []);

  if (!d) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading memory's evidence…</div>;
  const { m, v, t } = d;
  return (
    <div>
      <Part
        live={LIVE.memory.fetch}
        summary="The entity, the facts that point at it and their dimensions, drawn on the schema, with what each read fetched." title="What is promoted"
        lead="The Virtual Graph reads the warehouse's rows on demand and keeps nothing. Memory keeps what a read fetched: the entity, the facts that point at it, and their dimensions, each fact still tied to the layer it came from."
      >
        <Fetch m={m} v={v} />
        <p className="mt-6 max-w-3xl text-sm text-fg-muted">
          Read back, it is the same: {m.checks.contextsSame} of {m.checks.contexts} contexts came back from memory exactly as fetched, and {n(m.checks.questions.same)} context questions gave
          the same rows on memory as on the virtual graph. A batch of {m.checks.batch.customers} was fetched in {m.checks.batch.seconds} s, against {m.checks.batch.oneAtATime} s one at a time.
        </p>
      </Part>
      <Part live={LIVE.memory.payoff} title="What it buys" lead="The next question about the same customer is a local graph read, not a query to the warehouse: faster, and nothing billed.">
        <Payoff m={m} />
      </Part>
      <Part live={LIVE.memory.holds} summary="A fact holds for how often its table is written: move the age to see what goes stale." title="How long it holds" lead="Nothing is promised fresh for ever. A fact holds for how often its table is written, as the log shows it, and a stale one is fetched again.">
        <Holds m={m} />
      </Part>
      <Part
        live={LIVE.memory.governed}
        summary="Once remembered, each principal sees only what BigQuery would show them." title="Governed once remembered"
        lead="A row that has left the warehouse has left its row policies behind, so memory carries them: each principal sees only what BigQuery would show them."
      >
        <Governed m={m} />
      </Part>
      <Part
        live={LIVE.memory.trace(t)}
        summary="An agent's conversations, kept as a graph: the words, each tool call, what was learned and what was decided."
        title="What the agent did, auditable"
        lead="Memory also keeps the agent's own work: each conversation, the tools it called, what it learned and what it decided, and what each decision rests on. It is a graph like any other, so an audit is a query."
      >
        <Trace t={t} />
      </Part>
    </div>
  );
}


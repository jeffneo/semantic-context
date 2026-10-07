import { useEffect, useState, type ReactNode } from "react";
import Checked from "./Checked";
import Pipe from "./Pipe";
import Principals from "./Principals";
import Same from "./Same";
import type { Security } from "./data";

/*
  The security section: the warehouse's own row-level security, honoured on every route. What each principal may read (the warehouse's answer), the same
  question asked as each, how a Cypher query reaches the warehouse as them (the JDBC pass-through), and how it was checked, with the warehouse as the oracle.
*/
export default function SecurityBody() {
  const [d, setD] = useState<Security | null>(null);
  useEffect(() => {
    let live = true;
    void import("./security.json").then((m) => live && setD(m.default as unknown as Security));
    return () => {
      live = false;
    };
  }, []);

  if (!d) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading the security evidence…</div>;
  return (
    <div>
      <Part
        title="The warehouse is the rulebook"
        lead="qlsc re-implements no rule. For each principal it asks the warehouse what they may read (tables, columns, rows) and works from the answer."
      >
        <Principals d={d} />
      </Part>
      <Part title="The same question, three principals" lead="Nothing below was filtered by qlsc. The query ran as each principal, so BigQuery decided.">
        <Same d={d} />
      </Part>
      <Part
        title="How Cypher reaches the warehouse as the principal"
        lead="Virtual Graph reads rows through one identity of its own, which would show every principal everything. The pass-through driver stands in for it and runs each statement as the principal it was signed for."
      >
        <Pipe d={d} />
      </Part>
      <Part title="Checked against the warehouse" lead="The warehouse is the oracle: what comes back is compared with what BigQuery shows that principal.">
        <Checked d={d} />
      </Part>
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

import { useState } from "react";
import { n, type Case, type Security, type Side } from "./data";

// categorical colours for the three principals: not the shards' (which mean a layer of the architecture)
const COLOR: Record<string, string> = { marketing: "var(--area-1)", risk: "var(--area-2)", "contact-center": "var(--area-3)" };

/** What a principal got, on the route that answered: Cypher through the pass-through when it did, else SQL. */
function shown(a: { cypher: Side; sql: Side }): { route: "Cypher" | "SQL"; side: Side } {
  return a.cypher.query && a.cypher.total ? { route: "Cypher", side: a.cypher } : a.sql.query && a.sql.total ? { route: "SQL", side: a.sql } : { route: a.cypher.declined ? "Cypher" : "SQL", side: a.cypher.declined ? a.cypher : a.sql };
}

const NOTE: Record<string, string> = {
  P1: "One question, and for marketing and risk the very same Cypher. Risk's rows are filtered by the warehouse's row access policy, not by qlsc: the pass-through ran the query as risk.",
  P2: "Marketing may not read the identifier columns, so it cannot be told names and emails: it gets the affluent customers' keys. Risk reads them, but only for its own rows.",
};

/*
  The same question asked as each principal. What differs between the answers is what the warehouse differs on, and nothing here was filtered by qlsc: the query
  runs as the principal, so BigQuery applies the grants, the column tags and the row policy. An answer about people keeps its columns and its size, not the values.
*/
export default function Same({ d }: { d: Security }) {
  const [id, setId] = useState(d.cases[0].id);
  const c = d.cases.find((x) => x.id === id) as Case;
  return (
    <div className="mt-6">
      <div role="group" aria-label="Question" className="flex flex-wrap gap-2">
        {d.cases.map((x) => (
          <button
            key={x.id}
            type="button"
            aria-pressed={x.id === id}
            onClick={() => setId(x.id)}
            className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${x.id === id ? "border-fg" : "border-line text-fg-muted hover:text-fg"}`}
          >
            {x.text}
          </button>
        ))}
      </div>
      <p className="mt-4 max-w-3xl text-sm text-fg-muted">{NOTE[c.id]}</p>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        {d.principals.map((p) => {
          const { route, side } = shown(c.as[p.name]);
          const rows = side.rows ? [...side.rows].sort((a, b) => b[1] - a[1]) : null;
          const top = rows ? Math.max(...rows.map((r) => r[1])) : 0;
          return (
            <section key={p.name} className="flex flex-col rounded-card border p-4" style={{ borderColor: `color-mix(in oklab, ${COLOR[p.name]} 45%, var(--line))` }} aria-label={`As ${p.name}`}>
              <p className="flex items-baseline justify-between text-sm">
                <span className="font-semibold" style={{ color: COLOR[p.name] }}>
                  as {p.name}
                </span>
                {side.query && <span className="text-xs text-fg-muted">{route}</span>}
              </p>
              {side.query ? (
                <pre className="mt-2 max-h-28 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-bg-subtle p-2.5 font-mono text-[10.5px] leading-relaxed">{side.query}</pre>
              ) : null}

              <div className="mt-3 flex-1">
                {side.total ? (
                  <>
                    <p className="text-2xl font-semibold tabular-nums tracking-tight">
                      {n(side.total)} <span className="text-sm font-normal text-fg-muted">{side.total === 1 ? "row" : "rows"}</span>
                    </p>
                    {rows ? (
                      <ul className="mt-3 space-y-1.5">
                        {rows.map(([k, v]) => (
                          <li key={String(k)} className="grid grid-cols-[2.2rem_minmax(0,1fr)_3.4rem] items-center gap-2 text-xs">
                            <span className="font-mono">{k ?? "none"}</span>
                            <span className="h-2.5 rounded-sm" style={{ width: `${(v / top) * 100}%`, background: COLOR[p.name] }} />
                            <span className="text-right tabular-nums text-fg-muted">{n(v)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 flex flex-wrap gap-1.5">
                        {side.columns?.map((col) => (
                          <span key={col} className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px]">
                            {col}
                          </span>
                        ))}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-2xl font-semibold tracking-tight text-fg-muted">Nothing</p>
                    <p className="mt-2 text-xs leading-relaxed text-fg-muted">{side.why ?? side.declined ?? c.as[p.name].sql.why ?? c.as[p.name].cypher.declined}</p>
                  </>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

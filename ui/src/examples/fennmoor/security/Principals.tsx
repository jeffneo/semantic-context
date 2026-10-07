import { useState } from "react";
import EstateTiles from "../EstateTiles";
import { ALL, fullName } from "../data";
import type { Security } from "./data";

const short = (t: string) => t.split(".").slice(-2).join(".");

/*
  What the warehouse lets each test principal read: tables (a grant), columns (a policy tag the principal can or cannot read) and rows (a row access policy).
  This is the warehouse's own answer, asked as the principal, and the gateway uses it as it is.
*/
export default function Principals({ d }: { d: Security }) {
  const [name, setName] = useState("risk");
  const p = d.principals.find((x) => x.name === name)!;
  const readable = new Set(p.readable);
  const marked = new Set([...p.rowFiltered, ...p.hidden.map(([t]) => t)].filter((t) => readable.has(t)));
  const tables = ALL.length;

  return (
    <div className="mt-6">
      <div role="group" aria-label="Principal" className="inline-flex rounded-md border border-line p-0.5 text-sm">
        {d.principals.map((x) => (
          <button
            key={x.name}
            type="button"
            aria-pressed={x.name === name}
            onClick={() => setName(x.name)}
            className={`rounded px-3 py-1.5 transition-colors ${x.name === name ? "bg-fg text-bg" : "text-fg-muted hover:text-fg"}`}
          >
            {x.name}
          </button>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <div>
          <div className="rounded-card border border-line bg-bg-subtle p-4">
            <EstateTiles
              look={(l) => {
                const id = fullName(l);
                return { ink: readable.has(id) ? "var(--ok)" : "color-mix(in oklab, var(--fg) 14%, var(--bg))", ring: marked.has(id) };
              }}
            />
          </div>
          <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1.5 text-xs text-fg-muted" aria-label="Key">
            <li className="flex items-center gap-2">
              <span className="tile table static" style={{ ["--ink" as string]: "var(--ok)" }} aria-hidden="true" /> may read
            </li>
            <li className="flex items-center gap-2">
              <span className="tile table static" style={{ ["--ink" as string]: "color-mix(in oklab, var(--fg) 14%, var(--bg))" }} aria-hidden="true" /> may not
            </li>
            <li className="flex items-center gap-2">
              <span className="tile table sel static" style={{ ["--ink" as string]: "var(--ok)" }} aria-hidden="true" /> readable, but with columns hidden or rows filtered
            </li>
          </ul>
        </div>

        <section className="rounded-card border border-line bg-bg p-5 xl:sticky xl:top-20" aria-label={`What ${p.name} may read`}>
          <h4 className="text-lg font-semibold tracking-tight">{p.name}</h4>
          <p className="mt-1 text-sm text-fg-muted">{p.rule}</p>
          <dl className="mt-4 divide-y divide-line text-sm">
            <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3 py-2.5">
              <dt className="text-fg-muted">Tables</dt>
              <dd>
                <span className="font-semibold tabular-nums">{p.readable.length}</span> of {tables}
              </dd>
            </div>
            <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3 py-2.5">
              <dt className="text-fg-muted">Columns</dt>
              <dd>
                {p.hidden.length === 0 ? (
                  p.tagged ? (
                    <>all of them: the {p.tagged} tagged identifier columns are theirs to read</>
                  ) : (
                    "none are tagged in what they read"
                  )
                ) : (
                  <>
                    <span className="font-semibold tabular-nums">{p.hidden.length}</span> hidden by a policy tag
                    <span className="mt-2 flex flex-wrap gap-1.5">
                      {p.hidden.map(([t, c]) => (
                        <span key={t + c} className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px] text-fg-muted">
                          {short(t).split(".")[1]}.{c}
                        </span>
                      ))}
                    </span>
                  </>
                )}
              </dd>
            </div>
            <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-3 py-2.5">
              <dt className="text-fg-muted">Rows</dt>
              <dd>
                {p.rowFiltered.length === 0 ? (
                  "no row access policy in what they read"
                ) : (
                  <>
                    a row access policy on <span className="font-mono text-xs">{short(p.rowFiltered[0])}</span>
                    {p.name === "risk" ? ": only Kansas and Nebraska customers" : ": they are named for every row"}
                  </>
                )}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-xs leading-relaxed text-fg-muted">
            Asked of the warehouse, as {p.name}. The gateway keeps no copy of a rule: when the warehouse changes, so does the answer.
          </p>
        </section>
      </div>
    </div>
  );
}

import { useState, type CSSProperties } from "react";
import type { Security } from "./data";

type Mode = "signed" | "none" | "forged" | "expired";
const MODES: [Mode, string][] = [
  ["signed", "Through the gateway"],
  ["none", "No token"],
  ["forged", "A forged token"],
  ["expired", "An expired token"],
];

type State = "ok" | "refused" | "skipped" | "unreached";

interface Stage {
  name: string;
  says: string;
  state: State;
}

/** The statement's way from the question to the warehouse in each case: where it is made, and where it stops. */
function stages(mode: Mode): Stage[] {
  const bypass = mode !== "signed";
  return [
    {
      name: bypass ? "A Neo4j user connects directly" : "A question, as risk",
      says: bypass ? "Browser, or an agent's own driver, straight to the Virtual Graph: not through the gateway." : "An agent asks. The gateway knows who is asking: risk.",
      state: "ok",
    },
    {
      name: "The gateway signs",
      says: bypass
        ? mode === "none"
          ? "Skipped: the query carries no token."
          : mode === "forged"
            ? "Not the gateway: a token naming marketing, signed with risk's signature, not the gateway's key."
            : "A token the gateway did sign, used after it expired."
        : "Adds WHERE $qlsc_principal IS NOT NULL and binds a token: the principal and an expiry, signed with a key only the gateway and the driver hold.",
      state: mode === "none" || mode === "forged" ? "skipped" : "ok", // a forged token did not come from the gateway
    },
    { name: "Virtual Graph", says: "Translates the Cypher into SQL and carries the parameter into every statement it sends.", state: "ok" },
    {
      name: "The pass-through driver",
      says: bypass ? "Refuses the statement before any SQL runs." : "Inside Virtual Graph's JVM. Verifies the token, removes it, and connects as risk.",
      state: bypass ? "refused" : "ok",
    },
    {
      name: "BigQuery",
      says: bypass ? "Never reached: nothing ran." : "Runs as risk. The grants, the column tags and the row policy apply, exactly as for risk's own query.",
      state: bypass ? "unreached" : "ok",
    },
  ];
}

const STYLE: Record<State, { border: string; tone: string }> = {
  ok: { border: "var(--ok)", tone: "text-ok" },
  refused: { border: "var(--bad)", tone: "text-bad" },
  skipped: { border: "var(--line-strong)", tone: "text-fg-muted" },
  unreached: { border: "var(--line)", tone: "text-fg-muted" },
};
const WORD: Record<State, string> = { ok: "passes", refused: "refused", skipped: "skipped", unreached: "not reached" };

/*
  How a Cypher query reaches the warehouse as the principal. The gateway signs; the driver inside Virtual Graph verifies and connects as that principal. Try a
  query that did not come through the gateway: the driver refuses it, with the reasons it gave in the evaluation.
*/
export default function Pipe({ d }: { d: Security }) {
  const [mode, setMode] = useState<Mode>("signed");
  const refusal = mode === "none" ? d.driver[0] : mode === "forged" ? d.driver[1] : mode === "expired" ? d.driver[2] : null;
  return (
    <div className="mt-6">
      <div role="group" aria-label="How the query arrives" className="inline-flex flex-wrap rounded-md border border-line p-0.5 text-sm">
        {MODES.map(([m, label]) => (
          <button
            key={m}
            type="button"
            aria-pressed={mode === m}
            onClick={() => setMode(m)}
            className={`rounded px-3 py-1.5 transition-colors ${mode === m ? "bg-fg text-bg" : "text-fg-muted hover:text-fg"}`}
          >
            {label}
          </button>
        ))}
      </div>

      <ol key={mode} className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-5">
        {stages(mode).map((s, i) => (
          <li
            key={s.name}
            className="fall relative rounded-card border-2 p-4"
            style={{ "--i": i, borderColor: STYLE[s.state].border, borderStyle: s.state === "skipped" ? "dashed" : "solid", opacity: s.state === "unreached" ? 0.55 : undefined } as CSSProperties}
          >
            <p className="flex items-center justify-between text-xs">
              <span className="text-fg-muted">{i + 1}</span>
              <span className={`font-medium ${STYLE[s.state].tone}`}>{WORD[s.state]}</span>
            </p>
            <p className="mt-2 text-sm font-semibold leading-snug">{s.name}</p>
            <p className="mt-1.5 text-xs leading-relaxed text-fg-muted">{s.says}</p>
          </li>
        ))}
      </ol>

      <div className="mt-4 min-h-16 rounded-card border border-line bg-bg-subtle p-4 text-sm">
        {refusal ? (
          <>
            <p className="text-xs text-fg-muted">What the driver said:</p>
            <p className="mt-1 font-mono text-xs leading-relaxed text-bad">{refusal.why}</p>
          </>
        ) : (
          <p className="leading-relaxed">
            <span className="font-medium">The warehouse answers as risk.</span>{" "}
            <span className="text-fg-muted">The statement reaches BigQuery without its token, on a connection that impersonates risk, so risk's rows come back and no one else's.</span>
          </p>
        )}
      </div>

      <h4 className="mt-8 text-base font-semibold tracking-tight">What the driver does with each statement</h4>
      <ol className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-3">
        {[
          ["Verifies", "the bound token: a principal and an expiry, signed with a key only the gateway and the driver hold. Unsigned, forged or expired, it is refused with a reason."],
          ["Removes", "the predicate and its parameter, so the token never reaches BigQuery."],
          ["Runs as the principal", "on a connection that impersonates them. The warehouse, not qlsc, then decides which tables, columns and rows."],
        ].map(([k, v], i) => (
          <li key={k} className="rounded-card border border-line p-4 text-sm">
            <p className="font-semibold">
              <span className="mr-2 text-fg-muted">{i + 1}</span>
              {k}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-fg-muted">{v}</p>
          </li>
        ))}
      </ol>
      <p className="mt-3 max-w-3xl text-xs text-fg-muted">
        It lets through only Virtual Graph's own startup checks (a key's uniqueness, and metadata), which return a constant or names, never rows. Before the gateway
        reads on anyone's behalf it checks, once, that the virtual graph refuses an unsigned query, and if it does not the read fails closed.
      </p>
    </div>
  );
}

import { MEMORY, type Memory } from "./data";

const CELL: Record<string, { word: string; tone: string }> = {
  ok: { word: "context", tone: "text-ok" },
  refused: { word: "refused", tone: "text-fg-muted" },
  "nothing they may read": { word: "nothing they may read", tone: "text-fg-muted" },
};

const CONTROLS: Record<string, string> = {
  "reads ignored (risk sees rows its steps never read)": "Memory ignores whose own step read a row",
  "columns unrestricted (marketing)": "Memory ignores which columns a principal may see",
  "another's reads (risk read with marketing's steps)": "One principal reads with another's steps",
};

const anchorName = (a: { label: string; key: string }) => `${a.label} ${a.key.length > 8 ? `…${a.key.slice(-4)}` : a.key}`;

/*
  A remembered row has left the warehouse's own enforcement, so memory enforces it: a row-policied table's nodes are read from memory only by a principal
  whose own step read them, and each principal's fetch is shaped by what they may see. Each principal recalls each anchor, and what memory returns is
  checked against BigQuery read as that principal.
*/
export default function Governed({ m }: { m: Memory }) {
  const e = m.entitlements;
  return (
    <div className="mt-6">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs text-fg-muted">
              <th className="pb-2 pr-3 font-medium">Recalls as</th>
              {e.anchors.map((a) => (
                <th key={a.label + a.key} className="px-2 pb-2 font-mono font-medium">
                  {anchorName(a)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {e.principals.map((p, r) => (
              <tr key={p}>
                <th scope="row" className="border-t border-line py-3 pr-3 text-left font-medium">
                  {p}
                </th>
                {e.verdicts[r].map((v, c) => {
                  const cell = CELL[v] ?? { word: v, tone: "text-fg-muted" };
                  return (
                    <td key={c} className="border-t border-line px-2 py-3 align-top">
                      <span
                        className={`inline-block rounded-md border px-2 py-1 text-xs leading-tight ${cell.tone}`}
                        style={v === "ok" ? { borderColor: MEMORY, background: `color-mix(in oklab, ${MEMORY} 10%, var(--bg))` } : { borderColor: "var(--line)" }}
                      >
                        {cell.word}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-5 max-w-3xl text-[17px] leading-relaxed">
        <span className="font-semibold">{e.incidents} incidents</span> in {e.recalls} recalls. {e.served} returned a context, each the same as that principal's own fetch and
        checked against the warehouse as them; the rest were refused, or held nothing they may read.
      </p>

      <h4 className="mt-8 text-base font-semibold tracking-tight">Broken on purpose, to see the check catch it</h4>
      <ul className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-3">
        {e.controls.map((c) => (
          <li key={c.name} className="rounded-card border border-line p-4 text-sm">
            <p>{CONTROLS[c.name] ?? c.name}</p>
            <p className={`mt-2 text-xs font-medium ${c.caught ? "text-ok" : "text-bad"}`}>{c.caught ? "caught by the check" : "not caught"}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

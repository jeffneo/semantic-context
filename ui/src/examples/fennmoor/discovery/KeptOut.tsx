import type { Discovery } from "./data";

const cut = (column: string) => column.split(".").slice(-2).join(".");

/*
  The joins that were not allowed to merge anything, and why: queries do join things that are not the same thing. Where production keeps two id spaces apart and
  translates between them, a join that equates them is left out of the variables.
*/
export default function KeptOut({ d }: { d: Discovery }) {
  const two = d.keptOut.filter((k) => k.kind === "two id spaces");
  return (
    <div className="mt-6">
      <ul className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {two.map((k) => (
          <li key={k.a + k.b} className="rounded-card border border-line p-4">
            <p className="font-mono text-xs leading-relaxed">
              {cut(k.a)} <span className="text-fg-muted">⇄</span> {cut(k.b)}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-fg-muted">{k.why}</p>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-fg-muted">
        {d.keptOut.length - two.length} more relate two things without identifying them, such as a date to the month it falls in.
      </p>
    </div>
  );
}

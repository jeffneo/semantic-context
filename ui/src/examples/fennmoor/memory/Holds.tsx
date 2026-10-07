import { useMemo, useState } from "react";
import { ALL, fullName } from "../data";
import EstateTiles from "../EstateTiles";
import { MEMORY, n, type Hold, type Memory } from "./data";

const CLASSES: { id: string; label: string; says: string; test: (h: Hold) => boolean }[] = [
  { id: "daily", label: "Written daily", says: "holds a day", test: (h) => h === 1 },
  { id: "week", label: "Every 2 to 14 days", says: "holds that long", test: (h) => typeof h === "number" && h > 1 && h <= 14 },
  { id: "month", label: "About monthly", says: "holds about a month", test: (h) => typeof h === "number" && h > 14 },
  { id: "none", label: "No cadence in the log", says: "the default: a day", test: (h) => h === "none" },
  { id: "frozen", label: "Frozen", says: "holds for good", test: (h) => h === "frozen" },
];
const when = (iso: string) => new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit", timeZone: "UTC", timeZoneName: "short" });

const CHECKS: Record<string, string> = {
  "within its lifetime": "Inside its lifetime, a recall reads memory",
  "past it": "Past it, a recall fetches again from the virtual graph",
  "a stale fact": "A stale fact is never served as fresh",
  "a refetch rewrites a relationship from its column": "A refetch rewrites a relationship from its column",
  "a changed template": "A changed template fetches again",
};

/*
  How long what was fetched holds. A fact holds for its table's write cadence, the median gap between the days the log shows it written; a frozen table's holds
  for good; a context holds until its first fact expires. Here every table of the estate, coloured by whether a fact from it would still hold at the age you
  choose. (The Virtual Graph models eleven tables, all written daily, so a context here holds a day.)
*/
export default function Holds({ m }: { m: Memory }) {
  const [age, setAge] = useState(0);
  const days = (h: Hold) => (h === "frozen" ? Infinity : h === "none" ? m.settings.unknown_hold_days : h);
  const items = useMemo(() => [...ALL].map((l) => ({ l, id: fullName(l), hold: m.holds[fullName(l)] as Hold })), [m]);

  const fresh = items.filter((i) => age < days(i.hold)).length;
  const p = m.provenance;

  return (
    <div className="mt-6">
      <div className="rounded-card border border-line p-4">
        <label className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          <span className="font-medium">Age of what was fetched</span>
          <input type="range" min={0} max={45} step={0.5} value={age} onChange={(e) => setAge(Number(e.target.value))} className="h-2 min-w-48 flex-1" style={{ accentColor: MEMORY }} />
          <span className="w-20 text-right font-semibold tabular-nums">{age} {age === 1 ? "day" : "days"}</span>
        </label>
        <p className="mt-2 text-xs text-fg-muted">
          <span className="font-semibold tabular-nums text-fg">{fresh}</span> of {items.length} tables' facts still hold at this age. A recall past a context's hold fetches it again.
        </p>
      </div>

      <div className="mt-4 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_21rem]">
        <div className="rounded-card border border-line bg-bg-subtle p-4">
          <EstateTiles look={(_, id) => ({ ink: age < days(m.holds[id]) ? MEMORY : "color-mix(in oklab, var(--fg) 14%, var(--bg))" })} />
        </div>
        <ul className="rounded-card border border-line">
          {CLASSES.map((c) => {
            const mine = items.filter((i) => c.test(i.hold));
            const still = mine.filter((i) => age < days(i.hold)).length;
            return (
              <li key={c.id} className="flex items-baseline justify-between gap-3 border-b border-line px-4 py-3 last:border-b-0">
                <span>
                  <span className="block text-sm font-medium">{c.label}</span>
                  <span className="block text-xs text-fg-muted">{c.says}</span>
                </span>
                <span className="text-right text-sm tabular-nums">
                  <span className="font-semibold" style={{ color: still ? MEMORY : undefined }}>
                    {still}
                  </span>
                  <span className="text-fg-muted"> of {mine.length}</span>
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-5 xl:grid-cols-2">
        <section className="rounded-card border border-line p-5" aria-label="What a remembered node carries">
          <h4 className="text-base font-semibold tracking-tight">What every remembered node carries</h4>
          <p className="mt-1 text-xs text-fg-muted">From a customer node in memory. Its other columns are not shown.</p>
          <dl className="mt-3 divide-y divide-line text-sm">
            {[
              ["fetched_at", when(p.fetchedAt)],
              ["holds_until", when(p.holdsUntil)],
              ["fetched_by", p.fetchedBy],
              ["from", "the virtual graph"],
            ].map(([k, v]) => (
              <div key={k} className="grid grid-cols-[7rem_minmax(0,1fr)] gap-3 py-2">
                <dt className="font-mono text-xs text-fg-muted">{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 font-mono text-xs text-fg-muted">fetched_with</p>
          <pre className="mt-1.5 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-bg-subtle p-3 font-mono text-[11px] leading-relaxed">{p.read}</pre>
        </section>

        <section className="rounded-card border border-line p-5" aria-label="Freshness, checked">
          <h4 className="text-base font-semibold tracking-tight">Freshness, checked</h4>
          <ul className="mt-3 space-y-2.5">
            {Object.entries(m.checks.freshness).map(([k, ok]) => (
              <li key={k} className="flex items-baseline gap-3 text-sm">
                <span className={ok ? "text-ok" : "text-bad"} aria-hidden="true">
                  {ok ? "✓" : "✗"}
                </span>
                {CHECKS[k] ?? k}
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs leading-relaxed text-fg-muted">
            A node a fetch no longer returns (it left the window) stays, stale by its holds_until, and is never read as fresh. Remembering a context again leaves
            memory's counts {m.checks.idempotent ? "unchanged" : "changed"}.
          </p>
          <p className="mt-2 text-xs text-fg-muted">{n(m.checks.questions.same)} context questions gave the same rows on memory and on the virtual graph; {m.checks.questions.capped} over a capped relationship were left out.</p>
        </section>
      </div>
    </div>
  );
}

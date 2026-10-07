import { useState, type ReactNode } from "react";
import { useLayout } from "../layout";
import LiveRun from "../live/LiveRun";
import type { LiveSpec } from "../live/types";

/** What the control says it will run: its first query or command, named as the panel names it. */
function runHint(live: LiveSpec[]): string {
  const label = live[0].presets[0].label;
  return `Run this live: ${/^[A-Z][a-z]/.test(label) ? label[0].toLowerCase() + label.slice(1) : label}`;
}

interface Props {
  title: string;
  lead: string;
  live?: LiveSpec[];
  hint?: string;
  /** The finding in a sentence. A part with one is folded to a line in the compact layout, and opens in place; one without stays open. */
  summary?: string;
  children: ReactNode;
}

/*
  A part of a section: a title, a line on what it shows, and what it shows. `live` adds a control at the left, after it, that opens on the query or the
  command behind the part, to run for real (see live/LiveRun.tsx): the recorded evidence first, then the same thing in the real graph.
*/
export default function Part({ title, lead, live, hint, summary, children }: Props) {
  const compact = useLayout() === "compact";
  const [open, setOpen] = useState(false);

  if (summary && compact) {
    return (
      <div className="mt-4 border-t border-line pt-4 first:mt-8">
        <button type="button" aria-expanded={open} onClick={() => setOpen(!open)} className="group flex w-full items-start gap-3 text-left">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={`mt-1 shrink-0 text-fg-muted transition-transform ${open ? "rotate-90" : ""}`}>
            <path d="M6 3.5l4.5 4.5L6 12.5" />
          </svg>
          <span className="min-w-0">
            <span className="block text-base font-semibold tracking-tight group-hover:underline">{title}</span>
            {!open && <span className="mt-0.5 block max-w-3xl text-sm text-fg-muted">{summary}</span>}
          </span>
        </button>
        {open && (
          <div className="mt-2 pl-7">
            <p className="max-w-3xl text-fg-muted">{lead}</p>
            {children}
            {live && <LiveRun specs={live} hint={hint ?? runHint(live)} />}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="mt-14 first:mt-8">
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-1 max-w-3xl text-fg-muted">{lead}</p>
      {children}
      {live && <LiveRun specs={live} hint={hint ?? runHint(live)} />}
    </div>
  );
}

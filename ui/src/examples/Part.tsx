import type { ReactNode } from "react";
import LiveRun from "../live/LiveRun";
import type { LiveSpec } from "../live/types";

/*
  A part of a section: a title, a line on what it shows, and what it shows. `live` adds a control at the left, after it, that opens on the query or the
  command behind the part, to run for real (see live/LiveRun.tsx): the recorded evidence first, then the same thing in the real graph.
*/
/** What the control says it will run: its first query or command, named as the panel names it. */
function runHint(live: LiveSpec[]): string {
  const label = live[0].presets[0].label;
  return `Run this live: ${/^[A-Z][a-z]/.test(label) ? label[0].toLowerCase() + label.slice(1) : label}`;
}

export default function Part({ title, lead, live, hint, children }: { title: string; lead: string; live?: LiveSpec[]; hint?: string; children: ReactNode }) {
  return (
    <div className="mt-14 first:mt-8">
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-1 max-w-3xl text-fg-muted">{lead}</p>
      {children}
      {live && <LiveRun specs={live} hint={hint ?? runHint(live)} />}
    </div>
  );
}

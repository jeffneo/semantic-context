import type { ReactNode } from "react";
import LiveRun from "../live/LiveRun";
import type { LiveSpec } from "../live/types";

/*
  A part of a section: a title, a line on what it shows, and what it shows. `live` adds a control at the left, under the line, that opens on the query or the
  command behind the part, to run for real (see live/LiveRun.tsx).
*/
export default function Part({ title, lead, live, hint, children }: { title: string; lead: string; live?: LiveSpec[]; hint?: string; children: ReactNode }) {
  return (
    <div className="mt-14 first:mt-8">
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-1 max-w-3xl text-fg-muted">{lead}</p>
      {live && <LiveRun specs={live} hint={hint} />}
      {children}
    </div>
  );
}

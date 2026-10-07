import type { ComponentType } from "react";

/** One part of an example page: a heading in the sidebar and a section down the page. */
export interface Section {
  id: string;
  title: string;
  /** one sentence: what the section shows */
  summary: string;
  /** the section's content; a section without one is listed as coming */
  Body?: ComponentType;
}

export interface SectionGroup {
  label: string;
  sections: Section[];
}

/** A worked example: a scenario, its data, and the sections that explain what the engine does with it. Fennmoor Bank is the first. */
export interface Example {
  slug: string;
  name: string;
  tagline: string;
  /** the figures in the header band */
  stats: { label: string; value: string }[];
  groups: SectionGroup[];
}

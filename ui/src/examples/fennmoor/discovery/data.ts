/*
  The semantic layer qlsc discovered, as the page draws it (written by examples/fennmoor-bank/generate/ui_discovery.py from the layer's graph): how the
  log narrows to groups, the hierarchy of areas, where each table sits in it, the variables the joins revealed, and the joins that were kept out.
*/
export interface Area {
  name: string;
  description: string;
  level: 1 | 2 | 3;
  /** tables with a column in it */
  tables: number;
  /** what it is made of: columns and variables at level 1, groups above */
  members: number;
  stability?: number;
  /** the area above it, by position in the list */
  parent?: number;
}
export interface TableEntry {
  id: string;
  columns: number;
  /** the level-1 group holding most of its columns, then its level-2 and level-3 areas */
  groups?: [number, number, number];
  /** the share of its columns that group holds */
  share?: number;
  /** no query in the log referenced it */
  unread?: true;
}
/** A join between two of a variable's columns (by position): who made it, the runs of the queries that used it, how many people. */
export type Join = [a: number, b: number, confidence: string, runs: number, people: number];
export interface Variable {
  name: string;
  description: string;
  tables: number;
  columns: [table: string, column: string][];
  joins: Join[];
}
export interface KeptOut {
  a: string;
  b: string;
  kind: string;
  why: string;
}
export interface Discovery {
  funnel: {
    texts: number;
    shapes: number;
    viewShapes: number;
    joinKeys: number;
    variables: number;
    joined: number;
    columns: number;
    groups: Record<"1" | "2" | "3", number>;
  };
  areas: Area[];
  tables: TableEntry[];
  variables: Variable[];
  keptOut: KeptOut[];
}

/** The colour of a broad area, by its position among the level-3 areas (the layer lists them first). */
export const AREA_COLOR = ["var(--area-1)", "var(--area-2)", "var(--area-3)", "var(--area-4)"];

/*
  The Virtual Graph model qlsc generated from the semantic layer, as the page draws it (written by examples/fennmoor-bank/generate/ui_virtual.py from
  `qlsc virtualize`'s own files): the node labels with the reason each table is one, the relationship types with the column that points, what was left
  out, and the graph-shaped questions answered over it.
*/
export interface VNode {
  label: string;
  /** the source table, and the view that exposes it to the graph */
  table: string;
  view: string;
  key: string;
  /** the real-world thing the key holds (a Variable of the semantic layer) */
  variable: string | null;
  why: string;
  /** the group of the semantic layer the table sits in */
  area: string | null;
  properties: [column: string, type: string][];
  sql: string;
}
export interface VRel {
  type: string;
  start: string;
  end: string;
  /** the table and column that point at the end node's key */
  table: string;
  column: string;
  endKey: string;
  variable: string | null;
  why: string;
}
export interface LeftOut {
  what: "table" | "join";
  name: string;
  why: string;
}
export interface VQuestion {
  id: string;
  text: string;
  cypher: string;
  cypher_verdict: string;
  cypher_why: string;
  sql_verdict: string;
  sql_why: string;
  routed: string;
  routed_verdict: string;
  rows: number;
}
export interface Virtual {
  inScope: number;
  nodes: VNode[];
  relationships: VRel[];
  leftOut: LeftOut[];
  questions: VQuestion[];
}

/** Something on the graph: a node (by label) or a relationship (by type). */
export type Pick = { kind: "node"; id: string } | { kind: "edge"; id: string };

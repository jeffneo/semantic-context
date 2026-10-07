/** Where a Cypher query goes (the server's targets). */
export type Target = "layer" | "memory" | "rows" | "composite";

export interface Preset {
  label: string;
  query: string;
}

/** A Cypher panel: the query it opens with (a preset is chosen from the list, and the text is the visitor's to edit), and where it runs. */
export interface CypherSpec {
  kind: "cypher";
  target: Target;
  presets: Preset[];
  /** a principal can be picked: the query runs as them, so the warehouse's rules apply (Virtual Graph only) */
  principals?: boolean;
  /** offers sending it unsigned, as any Neo4j user could: the pass-through refuses it */
  unsigned?: boolean;
}

/** A SQL panel: one SELECT, in the graph's table names, run in BigQuery. */
export interface SqlSpec {
  kind: "sql";
  presets: Preset[];
  principals?: boolean;
}

export type Command = "ask" | "recall" | "composite" | "exchange";

export interface MethodPreset {
  label: string;
  question?: string;
  route?: string;
  entity?: string;
  key?: string;
  n?: string;
}

/** A command panel: one of qlsc's own commands, with its arguments to change, its output as it prints. */
export interface MethodSpec {
  kind: "method";
  command: Command;
  presets: MethodPreset[];
  principals?: boolean;
}

export type LiveSpec = CypherSpec | SqlSpec | MethodSpec;

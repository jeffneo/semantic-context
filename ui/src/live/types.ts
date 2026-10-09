/** Where a Cypher query goes (the server's targets). */
export type Target = "layer" | "memory" | "rows" | "composite";

export interface Preset {
  label: string;
  query: string;
}

/** A Cypher panel: a query chosen from the presets (shown, not editable), and where it runs. */
export interface CypherSpec {
  kind: "cypher";
  target: Target;
  presets: Preset[];
  /** a principal can be picked: the query runs as them, so the warehouse's rules apply (Virtual Graph only) */
  principals?: boolean;
  /** offers sending it unsigned, as any Neo4j user could: the pass-through refuses it */
  unsigned?: boolean;
  /** the query takes $customer: one the server chooses (a customer with activity, not yet remembered), shown above it */
  customer?: boolean;
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
  /** a recall's key: `cif_number=*` is the customer the server chose */
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

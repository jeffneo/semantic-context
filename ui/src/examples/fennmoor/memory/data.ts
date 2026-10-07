/*
  Promotion to memory as the page draws it (written by examples/fennmoor-bank/generate/ui_memory.py from the memory evaluations' own results, the layer's
  write cadences and qlsc's own template function). Memory keeps what a Virtual Graph read fetched: an entity's context, each fact held for its table's
  write cadence, every node carrying where it came from.
*/
export interface Read {
  hop: 0 | 1 | 2;
  /** `Customer<-MADE_BY-CardTransaction`: how the read is named in the results */
  name: string;
  label: string;
  type: string | null;
  start: string | null;
  end: string | null;
  /** the many side: facts that point at the nodes already fetched */
  inward: boolean;
  /** limited to the recent quarters by the table's partition column */
  windowed: boolean;
}
export interface Context {
  key: string;
  nodes: number;
  edges: number;
  /** nodes each read fetched */
  reads: Record<string, number>;
  /** the reads that hit the cap */
  capped: string[];
  seconds: number;
}
export type Hold = number | "frozen" | "none";
export interface Memory {
  settings: { hops: number; window_quarters: number; cap: number; unknown_hold_days: number };
  templates: Record<string, Read[]>;
  contexts: Context[];
  provenance: { fetchedAt: string; holdsUntil: string; fetchedBy: string; read: string };
  /** by table id */
  holds: Record<string, Hold>;
  session: {
    questions: { sql: number; memory: number; same: boolean }[];
    fetchSeconds: number;
    fetches: Record<string, { customers: number; seconds: number; mibPerCustomer: number; breakEven: number }>;
    sqlMedian: number;
    memoryMedian: number;
    secondsWithout: number;
    secondsWith: number;
    mibWithout: number;
    mibWith: number;
    sameAnswer: number;
    fromMemory: number;
  };
  checks: {
    contexts: number;
    contextsSame: number;
    questions: { same: number; capped: number; different: number };
    freshness: Record<string, boolean>;
    batch: { customers: number; seconds: number; oneAtATime: number };
    latency: Record<string, number>;
    idempotent: boolean;
  };
  entitlements: {
    anchors: { label: string; key: string }[];
    principals: string[];
    verdicts: string[][];
    recalls: number;
    served: number;
    incidents: number;
    controls: { name: string; caught: boolean }[];
  };
}

export const MEMORY = "var(--shard-memory)"; // memory's colour in the architecture
export const n = (x: number) => x.toLocaleString("en-US");

/*
  An agent's work as memory keeps it (written by examples/fennmoor-bank/generate/ui_trace.py from the memory database): the conversation's messages in order,
  and under the user's message that began a task, the tools it called, what was learned and what was decided.
*/
export interface Layered {
  label: string;
  name: string;
}
export interface TraceTool {
  tool: string;
  status: string;
  ms: number | null;
  /** what it was asked: the question, or the entity recalled */
  asked: string;
  reads: Layered[];
  /** recall: where the context came from, and its size */
  origin?: string;
  nodes?: number;
  edges?: number;
  /** ask: how it was answered */
  route?: string;
  writer?: string;
  query?: string | null;
  fromMemory?: boolean;
}
export interface TraceLearned {
  predicate: string;
  value: string;
  origin?: string;
  entity?: string;
  entityType?: string;
  /** it replaced an earlier fact: because the world changed, or because the earlier one was wrong */
  because?: string;
  replaced?: string;
}
export interface TraceDecision {
  choice: string;
  rationale: string;
  alternatives: string[];
  basedOn: { label: string; what: string; value: string | null }[];
  outcome: string[];
}
export interface TraceMessage {
  role: "user" | "agent";
  text: string;
  /** on a user's message: the tools its task called, in order, and what was decided in it */
  tools?: TraceTool[];
  decided?: TraceDecision[];
  learned?: TraceLearned[];
}
export interface TraceConversation {
  title: string;
  /** the principal it acted for */
  as: string;
  started: string;
  messages: TraceMessage[];
}
export interface Traces {
  conversations: TraceConversation[];
}

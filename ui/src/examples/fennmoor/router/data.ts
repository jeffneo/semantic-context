/*
  The router as the page draws it (written by examples/fennmoor-bank/generate/ui_router.py from the evaluations' own results). The router is a rule:
  the first rung, in order, whose answer stands. Each rung has been measured by the evaluation that exercised it, and no evaluation exercised all five.
*/
export type RungId = "memory" | "precedent" | "compiled" | "cypher" | "free";

export interface Rung {
  id: RungId;
  name: string;
  color: string;
  /** what it is */
  is: string;
  /** the rule for when it serves */
  serves: string;
}

/** The ladder, in the order the router tries it (qlsc/navigate.py `ROUTES`). Cheapest first: each rung is tried only when the ones above did not stand. */
export const RUNGS: Rung[] = [
  {
    id: "memory",
    name: "Memory",
    color: "var(--shard-memory)",
    is: "The compiled request, answered from the context memory already holds.",
    serves: "One entity, whose context the reader holds fresh.",
  },
  {
    id: "precedent",
    name: "Precedent",
    color: "var(--shard-semantic)",
    is: "The business's own query for a request like this one, its values set from the question.",
    serves: "A close request in the bank, whose filled query is still that shape.",
  },
  {
    id: "compiled",
    name: "Compiled SQL",
    color: "color-mix(in oklab, var(--shard-semantic) 55%, var(--bg))",
    is: "One typed request, written from the layer's options and compiled to SQL along the log's trusted joins, so no join multiplies the fact's rows.",
    serves: "The request compiles.",
  },
  {
    id: "cypher",
    name: "Free Cypher",
    color: "var(--shard-rows)",
    is: "Cypher written over the generated Virtual Graph schema: the neighbourhoods and paths a request cannot express.",
    serves: "It answers: not declined, and its query checked and run.",
  },
  {
    id: "free",
    name: "Free SQL",
    color: "var(--warehouse)",
    is: "SQL written freely over the tables the walk found.",
    serves: "Always. It is the last rung.",
  },
];

export interface Hit {
  n: number;
  right: number;
}
export interface Step {
  state: "served" | "declined" | "not reached";
  why: string;
}
/** One of the ten graph-shaped questions, as it fell down the ladder. */
export interface Trace {
  id: string;
  text: string;
  rows: number;
  compiled: Step;
  cypher: Step;
  free: Step;
  routed: "compiled" | "cypher" | "free";
  verdict: string;
  verdictWhy: string;
  query: string;
  queryKind: "cypher" | "sql";
}
export interface Router {
  memory: {
    questions: number;
    fromMemory: number;
    sameRows: number;
    memoryMedian: number;
    sqlMedian: number;
    compileMedian: number;
    sessionSecondsWithout: number;
    sessionSecondsWith: number;
    sessionMibWithout: number;
    sessionMibWith: number;
  };
  /** the comparison's agent: its first answers, a precedent or SQL (compiled or free) */
  agent: Record<"precedent" | "sql", Hit & { tokensMedian: number; secondsMedian: number }>;
  log: {
    n: number;
    picked: Record<"sql" | "cypher", Hit>;
    rungs: Record<"compiled" | "cypher" | "free", Hit>;
    compiled: Hit;
    free: Hit;
    sqlRight: number;
    cypher: Record<"correct" | "wrong" | "empty" | "failed" | "declined" | "not covered", number>;
    eitherRight: number;
  };
  graph: { n: number; /** the tables the Virtual Graph models */ tables: number; picked: Record<"sql" | "cypher", Hit>; sqlRight: number; cypherRight: number };
  trace: Trace[];
}

export const n = (x: number) => x.toLocaleString("en-US");

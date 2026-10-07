/*
  The accuracy comparison as the page draws it (written by examples/fennmoor-bank/generate/ui_accuracy.py from the comparison's results): four methods
  answering the same 186 questions, scored on the answer's rows against a reference. Nothing here is mocked or tuned for the page.
*/
export type MethodId = "naive-schema" | "naive-agent" | "layer" | "agent";
export type Verdict = "correct" | "wrong" | "empty";

export interface Stats {
  n: number;
  right: number;
  delivered: number;
  tokens_p50: number;
  tokens_p90: number;
  seconds_p50: number;
  seconds_p90: number;
  cost: number;
}
export interface Method {
  id: MethodId;
  name: string;
  blurb: string;
  log: Stats;
  gold: Stats;
}
export interface Result {
  v: Verdict;
  /** why a wrong answer is wrong */
  why: string;
  /** right, and within the service's targets */
  d: boolean;
  t: number;
  s: number;
  c: number;
  sql: string;
}
export interface Question {
  id: string;
  group: "gold" | "log";
  text: string;
  who?: string;
  /** the business's own query, which a log question was scored against */
  ref?: string;
  r: Record<MethodId, Result>;
  agent: { route: string; outcome: string; turns: number };
}
export interface FirstAnswers {
  n: number;
  right: number;
  tokens_p50: number;
  seconds_p50: number;
}
export interface Accuracy {
  targets: { tokens: number; seconds: number };
  methods: Method[];
  outcomes: Record<string, number>;
  routes: { precedent: FirstAnswers; compiled: FirstAnswers };
  questions: Question[];
}

/** How a method is drawn everywhere on the section: the naive ones grey, the layer's two blue. */
export const METHOD_COLOR: Record<MethodId, string> = {
  "naive-schema": "color-mix(in oklab, var(--fg) 26%, var(--bg))",
  "naive-agent": "color-mix(in oklab, var(--fg) 46%, var(--bg))",
  layer: "color-mix(in oklab, var(--shard-semantic) 50%, var(--bg))",
  agent: "var(--shard-semantic)",
};

/** The 95% Wilson interval for k right of n: how far a score on this many questions can be trusted. */
export function wilson(k: number, n: number, z = 1.96): [number, number] {
  const p = k / n;
  const d = 1 + (z * z) / n;
  const centre = (p + (z * z) / (2 * n)) / d;
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [centre - half, centre + half];
}

export const n = (x: number) => x.toLocaleString("en-US");
export const pct = (x: number) => `${Math.round(x * 100)}%`;

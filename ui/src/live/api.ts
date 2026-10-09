import type { Command } from "./types";

export interface GraphNode {
  $: "node";
  id: string;
  labels: string[];
  properties: Record<string, unknown>;
}
export interface GraphRel {
  $: "rel";
  id: string;
  type: string;
  from: string;
  to: string;
  properties: Record<string, unknown>;
}
export interface QueryResult {
  columns: string[];
  rows: unknown[][];
  more: boolean;
  seconds: number;
  graph: { nodes: GraphNode[]; relationships: GraphRel[] };
  /** what was sent, when the gateway changed it (the signature added) */
  sent?: string | null;
  principal: string;
  total?: number;
  bytesBilled?: number;
}
export interface Info {
  principals: { name: string }[];
  targets: string[];
  limits: { rows: number; seconds: number; bytes: number };
}
export type MethodEvent = { t: "out"; line: string; at: number } | { t: "end"; code: number; seconds: number } | { t: "error"; message: string };

/** The server said no (a refusal, an error from a database): its words. `unreachable`: there is no server to say anything. */
export class ServerError extends Error {
  readonly unreachable: boolean;
  constructor(message: string, unreachable = false) {
    super(message);
    this.unreachable = unreachable;
  }
}

async function send(path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(path, init);
  } catch (e) {
    if (init.signal?.aborted) throw e;
    throw new ServerError("the demo server is not running", true);
  }
}

async function json<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new ServerError("the demo server is not running", true); // the dev server's proxy answers with a bare 500 when nothing is listening
  }
  if (!res.ok) throw new ServerError((data as { error?: string }).error ?? res.statusText);
  return data as T;
}

const post = (path: string, body: unknown, signal?: AbortSignal) =>
  send(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });

let info: Promise<Info> | null = null;
/** What the server offers; asked once, and again after a failure. */
export function getInfo(): Promise<Info> {
  info ??= send("/api/info", {}).then((r) => json<Info>(r));
  info.catch(() => (info = null));
  return info;
}

export const cypher = (body: { target: string; query: string; principal: string; signed: boolean; customer?: string }, signal?: AbortSignal) =>
  post("/api/cypher", body, signal).then((r) => json<QueryResult>(r));

export const sql = (body: { query: string; principal: string }, signal?: AbortSignal) => post("/api/sql", body, signal).then((r) => json<QueryResult>(r));

export interface MethodArgs {
  command: Command;
  principal: string;
  question?: string;
  route?: string;
  label?: string;
  key?: string;
  n?: string;
}

/** A command's output, line by line as it prints. */
export async function method(body: MethodArgs, onEvent: (e: MethodEvent) => void, signal: AbortSignal): Promise<void> {
  const res = await post("/api/method", body, signal);
  if (!res.ok || !res.body) return void (await json(res));
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    pending += decoder.decode(value, { stream: true });
    const lines = pending.split("\n");
    pending = lines.pop() ?? "";
    for (const line of lines) if (line) onEvent(JSON.parse(line) as MethodEvent);
  }
}

/** A customer to try memory on, chosen by the server: one with calls and card activity that memory does not hold yet. */
export const pick = () => post("/api/pick", {}).then((r) => json<{ customer: string; of: number; remembered: number }>(r));

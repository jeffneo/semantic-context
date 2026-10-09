/*
  Everything the page offers to run, as one file for the demo server to hold itself to, hosted or local: `npm run presets` writes dist/presets.json.
  Run through Vite's SSR build, so the .cypher and .sql files and the JSON the dynamic presets read load as they do in the page; nothing here is a second list.
*/
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { LIVE } from "../src/examples/fennmoor/live";
import type { LiveSpec } from "../src/live/types";

const json = (path: string) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
const data: Record<string, unknown> = {
  questions: json("../src/examples/fennmoor/virtual/virtual.json"),
  trace: undefined, // two sections name theirs: see below
};

const specs: LiveSpec[] = [];
for (const [section, entries] of Object.entries(LIVE)) {
  for (const [name, entry] of Object.entries(entries as Record<string, unknown>)) {
    if (typeof entry !== "function") {
      specs.push(...(entry as LiveSpec[]));
      continue;
    }
    const arg = name === "questions" ? data.questions : section === "router" ? json("../src/examples/fennmoor/router/router.json") : json("../src/examples/fennmoor/memory/traces.json");
    specs.push(...(entry as (a: unknown) => LiveSpec[])(arg));
  }
}

/** A query as the server compares it: as the page sends it, less the line ending. A query is not compared with its whitespace folded: a newline ends a // comment. */
const fold = (q: string) => q.trimEnd();
const unique = <T>(xs: T[]) => [...new Set(xs.map((x) => JSON.stringify(x)))].map((x) => JSON.parse(x) as T);

const out = {
  cypher: {} as Record<string, string[]>,
  sql: [] as string[],
  ask: [] as { question: string; route: string }[],
  recall: [] as { entity: string; key: string }[],
  exchange: [] as string[],
};
for (const spec of specs) {
  if (spec.kind === "cypher") (out.cypher[spec.target] ??= []).push(...spec.presets.map((p) => fold(p.query)));
  else if (spec.kind === "sql") out.sql.push(...spec.presets.map((p) => fold(p.query)));
  else
    for (const p of spec.presets) {
      if (spec.command === "ask") out.ask.push({ question: p.question ?? "", route: p.route ?? "auto" });
      if (spec.command === "recall") out.recall.push({ entity: p.entity ?? "", key: p.key ?? "" });
      if (spec.command === "exchange") out.exchange.push(p.n ?? "0");
    }
}
for (const t of Object.keys(out.cypher)) out.cypher[t] = [...new Set(out.cypher[t])];
out.sql = [...new Set(out.sql)];
out.ask = unique(out.ask);
out.recall = unique(out.recall);
out.exchange = [...new Set(out.exchange)];

const to = process.argv[2] ?? "dist/presets.json";
mkdirSync(dirname(to), { recursive: true });
writeFileSync(to, JSON.stringify(out, null, 1));
console.log(`${to}: ${Object.values(out.cypher).flat().length} Cypher, ${out.sql.length} SQL, ${out.ask.length} questions, ${out.recall.length} recalls, ${out.exchange.length} exchanges`);

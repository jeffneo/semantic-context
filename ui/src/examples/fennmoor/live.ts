import { preset } from "../../live/query";
import type { LiveSpec, MethodPreset } from "../../live/types";
import type { Router } from "./router/data";
import type { Virtual } from "./virtual/data";
import counts from "./queries/discovery/counts.cypher?raw";
import evidence from "./queries/discovery/evidence_for_a_variable.cypher?raw";
import keptOut from "./queries/discovery/joins_kept_out.cypher?raw";
import keys from "./queries/discovery/keys_across_the_warehouse.cypher?raw";
import map from "./queries/discovery/map_of_the_business.cypher?raw";
import down from "./queries/discovery/meaning_to_data.cypher?raw";
import nearest from "./queries/discovery/nearest_groups.cypher?raw";
import levels from "./queries/discovery/semantic_levels.cypher?raw";
import computed from "./queries/discovery/what_is_computed.cypher?raw";
import segments from "./queries/accuracy/customers_by_segment.sql?raw";
import holds from "./queries/memory/holds_summary.cypher?raw";
import neighbourhood from "./queries/memory/neighbourhood.cypher?raw";
import provenance from "./queries/memory/provenance_of.cypher?raw";
import remembered from "./queries/memory/remembered.cypher?raw";
import stateCounts from "./queries/security/customers_by_state.cypher?raw";
import stateSql from "./queries/security/customers_by_state.sql?raw";
import affluent from "./queries/security/affluent_customers.cypher?raw";
import callsBySite from "./queries/security/calls_by_site.cypher?raw";
import accounts from "./queries/virtual/accounts_graph.cypher?raw";
import customers from "./queries/virtual/customers_sample.cypher?raw";
import modelPaths from "./queries/virtual/model_paths.cypher?raw";
import modelTable from "./queries/virtual/model_table.cypher?raw";
import rowsSchema from "./queries/virtual/rows_schema.cypher?raw";

/*
  What each part of the Fennmoor page can run, for real, from the control at its left (live/LiveRun.tsx). The queries are the files in queries/ (most from
  demo-101.md and demo.cypher, the walk-through this example already has); the commands are qlsc's own. A visitor changes any of them and runs the change.
*/

const CALLS = "How many calls did each contact center site handle since April 2026?";
const CARD = "Card spend by customer segment last quarter";
const DEPOSITS = "What is the total deposit balance by customer segment?";
const AGENTS = "Which agents handled calls from customer 0001000025, and how many of that customer's calls did each handle?";

const asks = (...q: string[]): MethodPreset[] => q.map((question) => ({ label: question, question, route: "auto" }));

export const LIVE = {
  discovery: {
    funnel: [{ kind: "cypher", target: "layer", presets: [preset("How much the build holds", counts), preset("Groups at each level", levels)] }],
    regroup: [
      {
        kind: "cypher",
        target: "layer",
        presets: [preset("The map of the business", map), preset("The five nearest groups, by embedding", nearest), preset("From meaning down to data", down)],
      },
    ],
    joins: [
      {
        kind: "cypher",
        target: "layer",
        presets: [
          preset("The keys the whole warehouse joins on", keys),
          preset("The joins behind one variable", evidence),
          preset("Joins kept out of the variables", keptOut),
          preset("What the business computes", computed),
        ],
      },
    ],
  },
  virtual: {
    steps: [{ kind: "cypher", target: "layer", presets: [preset("The paths the model was derived from", modelPaths), preset("The same, as a table", modelTable)] }],
    compare: [{ kind: "cypher", target: "composite", presets: [preset("The Virtual Graph's schema", rowsSchema)] }],
    explorer: [
      {
        kind: "cypher",
        target: "rows",
        principals: true,
        presets: [preset("A customer's accounts and their products", accounts), preset("Ten customers, read live", customers)],
      },
    ],
    /** The ten graph questions' Cypher, run as it was written, and the same question put to the router as a command. */
    questions: (d: Virtual): LiveSpec[] => [
      { kind: "cypher", target: "rows", principals: true, presets: d.questions.flatMap((q) => (q.cypher ? [{ label: `${q.id}: ${q.text}`, query: q.cypher.trimEnd() + "\n" }] : [])) },
      { kind: "method", command: "ask", principals: true, presets: [{ label: "Which agents handled a customer's calls", question: AGENTS, route: "cypher" }] },
    ],
  },
  router: {
    ladder: [{ kind: "method", command: "ask", principals: true, presets: asks(CARD, CALLS, DEPOSITS) }],
    trace: (r: Router): LiveSpec[] => [{ kind: "method", command: "ask", principals: true, presets: asks(...r.trace.map((t) => t.text)) }],
  },
  memory: {
    fetch: [
      { kind: "cypher", target: "memory", presets: [preset("Is this customer remembered?", remembered), preset("Where it came from, and how long it holds", provenance), preset("Its neighbourhood, drawn", neighbourhood)] },
      { kind: "method", command: "recall", principals: true, presets: [{ label: "Fetch a customer, or read them from memory", entity: "Customer", key: "cif_number=0001000033" }] },
    ],
    payoff: [
      { kind: "method", command: "recall", principals: true, presets: [{ label: "Ask twice: the first reads BigQuery, the second memory", entity: "Customer", key: "cif_number=0001000033" }] },
      { kind: "method", command: "exchange", presets: [{ label: "An agent asks, asks again, and corrects", n: "0" }, { label: "A second question", n: "1" }, { label: "A third question", n: "2" }] },
    ],
    holds: [{ kind: "cypher", target: "layer", presets: [preset("How often each table is written", holds)] }],
    governed: [{ kind: "method", command: "recall", principals: true, presets: [{ label: "Recall a customer as a principal", entity: "Customer", key: "cif_number=0001000033" }] }],
  },
  accuracy: {
    scores: [
      { kind: "method", command: "ask", principals: true, presets: asks(CALLS, DEPOSITS, CARD) },
      { kind: "sql", presets: [preset("A reference query: customers in each segment", segments)] },
    ],
  },
  security: {
    principals: [{ kind: "sql", principals: true, presets: [preset("Customers in each state, as the warehouse lets a principal see them", stateSql)] }],
    same: [
      {
        kind: "cypher",
        target: "rows",
        principals: true,
        presets: [preset("Customers in each state", stateCounts), preset("Names and email addresses of the affluent customers", affluent)],
      },
    ],
    pipe: [
      { kind: "cypher", target: "rows", principals: true, unsigned: true, presets: [preset("Calls handled at each site", callsBySite)] },
      {
        kind: "method",
        command: "ask",
        principals: true,
        presets: [{ label: "A principal with no right to the risk tables", question: "What is the churn risk of our high-balance customers?", route: "auto" }],
      },
    ],
  },
} satisfies Record<string, Record<string, LiveSpec[] | ((arg: never) => LiveSpec[])>>;

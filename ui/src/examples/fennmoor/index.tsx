import type { Example, Section } from "../types";
import { TOTALS, WAREHOUSE } from "./data";
import AccuracyBody from "./accuracy";
import DiscoveryBody from "./discovery";
import MemoryBody from "./memory";
import RouterBody from "./router";
import Scenario from "./Scenario";
import VirtualBody from "./virtual";
import Warehouse from "./Warehouse";

const n = (x: number) => x.toLocaleString("en-US");

/*
  The scenario and the warehouse, then the aspects of the solution shown in depth, in the order a reader meets them. Each is listed and has its place
  on the page; one without a Body is not built yet.
*/
const scenario: Section = {
  id: "scenario",
  title: "The scenario",
  summary: "A bank, an estate nobody has documented, and what there is to learn from.",
  Body: Scenario,
};
const warehouse: Section = {
  id: "warehouse",
  title: "The warehouse",
  summary: "Every table and view in BigQuery, by project and dataset. Pick one for its schema; search finds names and columns.",
  Body: Warehouse,
};
const discovery: Section = {
  id: "discovery",
  title: "Discovering the semantic layer",
  summary: "What the tables mean and how they join, found automatically from the queries people ran.",
  Body: DiscoveryBody,
};
const virtualGraph: Section = {
  id: "virtual-graph",
  title: "Generating the Virtual Graph schema",
  summary: "The Virtual Graph's schema, generated from the semantic layer, so the rows can be read as a graph without copying them.",
  Body: VirtualBody,
};
const router: Section = {
  id: "router",
  title: "Routing a request",
  summary: "Each request goes to the source data by the route that suits it, from remembered context to free SQL.",
  Body: RouterBody,
};
const memory: Section = {
  id: "memory",
  title: "Promoting results to memory",
  summary: "Result sets read through the Virtual Graph are promoted into memory, so the next question need not go back to the warehouse.",
  Body: MemoryBody,
};
const accuracy: Section = {
  id: "accuracy",
  title: "Accuracy at full scale",
  summary: "How often the answers are right, measured on the full estate and the business's own questions.",
  Body: AccuracyBody,
};
const security: Section = {
  id: "security",
  title: "Row-level security, passed through",
  summary: "A pass-through JDBC mechanism that guarantees every read respects the row-level policies the warehouse already enforces.",
};

const fennmoor: Example = {
  slug: "fennmoor",
  name: WAREHOUSE.org,
  tagline: "A fictional regional bank with a BigQuery estate nobody has documented. The engine is given its catalog and 90 days of its query log.",
  stats: [
    { value: String(TOTALS.projects), label: "projects" },
    { value: String(TOTALS.datasets), label: "datasets" },
    { value: n(TOTALS.tables), label: "tables and views" },
    { value: n(TOTALS.columns), label: "columns" },
    { value: n(WAREHOUSE.log.jobs), label: `queries in ${WAREHOUSE.log.days} days` },
  ],
  groups: [
    { label: "The estate", sections: [scenario, warehouse] },
    { label: "What the engine does", sections: [discovery, virtualGraph, router, memory, accuracy, security] },
  ],
};

export default fennmoor;

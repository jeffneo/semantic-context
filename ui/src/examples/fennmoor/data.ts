import raw from "./warehouse.json";

/*
  The Fennmoor warehouse as BigQuery holds it (written by examples/fennmoor-bank/generate/ui_warehouse.py from qlsc's catalog extract): three
  projects, their datasets, and in each dataset the tables, views and date-sharded families with their columns. Nothing here is the answer key.
*/
export type Kind = "table" | "view" | "sharded";

export interface Table {
  name: string;
  kind: Kind;
  columns: [name: string, type: string][];
  partition?: string;
  cluster?: string[];
  /** a view's definition */
  sql?: string;
  /** a sharded family: how many daily tables it stands for */
  shards?: number;
}
export interface Dataset {
  name: string;
  layer: string;
  source: string | null;
  tables: Table[];
}
export interface Project {
  name: string;
  datasets: Dataset[];
}
export interface Warehouse {
  org: string;
  log: { start: string; days: number; jobs: number };
  teams: number;
  serviceAccounts: number;
  projects: Project[];
}

/** How the source systems' names read on the page. */
export const SOURCE_NAMES: Record<string, string> = {
  aml_vendor: "AML vendor",
  amplitude: "Amplitude",
  avaya_legacy: "Avaya (legacy)",
  braze: "Braze",
  bureau: "Credit bureau",
  card_processor: "Card processor",
  core_banking: "Core banking",
  erp: "ERP general ledger",
  fraud_vendor: "Fraud platform",
  ga4: "Google Analytics 4",
  genesys: "Genesys Cloud",
  los: "Loan origination",
  manual_upload: "Manual uploads",
  olb_platform: "Online banking",
  salesforce: "Salesforce",
  workday: "Workday",
};

export const WAREHOUSE = raw as unknown as Warehouse;

/** Where a table is found: the page keeps this as the selection, and shows it as the full name. */
export interface Located {
  project: Project;
  dataset: Dataset;
  table: Table;
}
export const fullName = (l: Located) => `${l.project.name}.${l.dataset.name}.${l.table.name}`;

export const ALL: Located[] = WAREHOUSE.projects.flatMap((project) =>
  project.datasets.flatMap((dataset) => dataset.tables.map((table) => ({ project, dataset, table }))),
);

export const TOTALS = {
  projects: WAREHOUSE.projects.length,
  datasets: WAREHOUSE.projects.reduce((n, p) => n + p.datasets.length, 0),
  tables: ALL.length,
  columns: ALL.reduce((n, l) => n + l.table.columns.length, 0),
  byKind: ALL.reduce<Record<Kind, number>>((n, l) => ({ ...n, [l.table.kind]: n[l.table.kind] + 1 }), { table: 0, view: 0, sharded: 0 }),
};

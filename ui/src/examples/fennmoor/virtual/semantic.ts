import type { Virtual } from "./data";

/*
  The semantic layer's side of the model: the paths the build followed to write the schema. A table has columns, and a column that is a key or points
  at one is the real-world thing it holds, a variable. Where a column holds the variable another table is keyed by, that path is one arrow of the schema;
  the keyed table is a node. This builds those paths as a graph from the schema's own evidence, and lays it out (deterministically: nothing is random).
*/
export type Kind = "table" | "column" | "variable";
export interface SNode {
  id: string;
  kind: Kind;
  label: string;
  r: number;
  x: number;
  y: number;
}
export interface SEdge {
  from: string;
  to: string;
  /** HAS_COLUMN (a table to its column) or IS (a column to the variable it holds) */
  kind: "HAS_COLUMN" | "IS";
}

const short = (table: string) => table.split(".").slice(-1)[0];
export const tableId = (table: string) => `t:${table}`;
export const columnId = (table: string, column: string) => `c:${table}.${column}`;
export const variableId = (name: string) => `v:${name}`;

const RADIUS: Record<Kind, number> = { table: 46, column: 10, variable: 24 };

export function semanticGraph(d: Virtual, w: number, h: number): { nodes: SNode[]; edges: SEdge[] } {
  const nodes = new Map<string, SNode>();
  const edges: SEdge[] = [];
  const add = (id: string, kind: Kind, label: string) => {
    if (!nodes.has(id)) nodes.set(id, { id, kind, label, r: RADIUS[kind], x: 0, y: 0 });
  };
  const column = (table: string, name: string, variable: string | null) => {
    add(tableId(table), "table", short(table));
    add(columnId(table, name), "column", name);
    edges.push({ from: tableId(table), to: columnId(table, name), kind: "HAS_COLUMN" });
    if (variable) {
      add(variableId(variable), "variable", variable);
      edges.push({ from: columnId(table, name), to: variableId(variable), kind: "IS" });
    }
  };
  for (const n of d.nodes) column(n.table, n.key, n.variable);
  for (const r of d.relationships) column(r.table, r.column, r.variable);

  const list = [...nodes.values()].sort((a, b) => a.id.localeCompare(b.id));
  // The most room the nodes can be given without squeezing the picture to fit: the largest ideal distance whose layout needs no real shrinking.
  let at = forces(list, edges, w, h, 60).at;
  for (const k of [130, 115, 100, 88, 76]) {
    const tried = forces(list, edges, w, h, k);
    if (Math.min(tried.sx, tried.sy) >= 0.92) {
      at = tried.at;
      break;
    }
  }
  for (const n of list) Object.assign(n, at.get(n.id));
  return { nodes: list, edges };
}

/** Fruchterman and Reingold with ideal distance k, from a fixed start, then boxes pushed apart and the whole fitted to the canvas (sx and sy: by how much). */
function forces(nodes: SNode[], edges: SEdge[], w: number, h: number, k: number) {
  const pos = new Map(nodes.map((n, i) => [n.id, { x: Math.cos((i / nodes.length) * 2 * Math.PI) * w * 0.4, y: Math.sin((i / nodes.length) * 2 * Math.PI) * h * 0.4 }]));
  for (let step = 0; step < 700; step++) {
    const heat = (w / 9) * (1 - step / 700) + 0.5;
    const move = new Map(nodes.map((n) => [n.id, { x: 0, y: 0 }]));
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++) {
        const [a, b] = [pos.get(nodes[i].id)!, pos.get(nodes[j].id)!];
        const [dx, dy] = [a.x - b.x, a.y - b.y];
        const d = Math.max(1, Math.hypot(dx, dy));
        const f = (k * k) / d;
        move.get(nodes[i].id)!.x += (dx / d) * f;
        move.get(nodes[i].id)!.y += (dy / d) * f;
        move.get(nodes[j].id)!.x -= (dx / d) * f;
        move.get(nodes[j].id)!.y -= (dy / d) * f;
      }
    for (const e of edges) {
      const [a, b] = [pos.get(e.from)!, pos.get(e.to)!];
      const [dx, dy] = [a.x - b.x, a.y - b.y];
      const d = Math.max(1, Math.hypot(dx, dy));
      const f = (d * d) / k;
      move.get(e.from)!.x -= (dx / d) * f;
      move.get(e.from)!.y -= (dy / d) * f;
      move.get(e.to)!.x += (dx / d) * f;
      move.get(e.to)!.y += (dy / d) * f;
    }
    for (const n of nodes) {
      const [p, m] = [pos.get(n.id)!, move.get(n.id)!];
      m.x -= p.x * 0.3; // a pull to the middle: clusters that repel each other stay on the canvas
      m.y -= p.y * 0.3;
      const len = Math.max(1, Math.hypot(m.x, m.y));
      p.x += (m.x / len) * Math.min(len, heat);
      p.y += (m.y / len) * Math.min(len, heat);
    }
  }
  for (let pass = 0; pass < 60; pass++)
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++) {
        const [a, b] = [pos.get(nodes[i].id)!, pos.get(nodes[j].id)!];
        const [dx, dy] = [b.x - a.x, b.y - a.y];
        const gap = nodes[i].r + nodes[j].r + 8;
        const d = Math.max(0.01, Math.hypot(dx, dy));
        if (d < gap) {
          const push = (gap - d) / 2;
          a.x -= (dx / d) * push;
          a.y -= (dy / d) * push;
          b.x += (dx / d) * push;
          b.y += (dy / d) * push;
        }
      }
  const xs = nodes.map((n) => pos.get(n.id)!.x);
  const ys = nodes.map((n) => pos.get(n.id)!.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const pad = 58; // room for a table's width and a variable's label
  const [sx, sy] = [(w - 2 * pad) / Math.max(1, x1 - x0), (h - 2 * pad) / Math.max(1, y1 - y0)];
  const at = new Map(nodes.map((n) => [n.id, { x: pad + (pos.get(n.id)!.x - x0) * sx, y: pad + (pos.get(n.id)!.y - y0) * sy }]));
  return { at, sx, sy };
}

/** What is lit in both pictures at once: the schema's nodes and arrows, and the paths (tables, columns, variables) behind them. */
export interface Focus {
  nodes: Set<string>;
  edges: Set<string>;
  tables: Set<string>;
  columns: Set<string>;
  variables: Set<string>;
}
/** A thing picked in either picture: nodes (shown with the arrows they have), arrows, and nodes shown only for their own key. */
export interface Seed {
  nodes: string[];
  edges: string[];
  holders?: string[];
}

/** A node lights its arrows and their other ends; an arrow lights its two nodes. Then the paths follow from what is lit. */
export function focusOf(d: Virtual, seed: Seed): Focus {
  const holders = seed.holders ?? [];
  const nodes = new Set([...seed.nodes, ...holders]);
  const edges = new Set(seed.edges);
  for (const r of d.relationships) if (seed.nodes.includes(r.start) || seed.nodes.includes(r.end)) edges.add(r.type);
  for (const r of d.relationships)
    if (edges.has(r.type)) {
      nodes.add(r.start);
      nodes.add(r.end);
    }
  const f: Focus = { nodes, edges, tables: new Set(), columns: new Set(), variables: new Set() };
  const node = (label: string) => d.nodes.find((n) => n.label === label)!;
  // a node asked for brings its own table, key and variable; an arrow brings the path it follows: its table and pointing column, the variable, the
  // key column and table it reaches (not the table's own key, which is not on that path)
  for (const label of [...seed.nodes, ...holders]) {
    const n = node(label);
    f.tables.add(tableId(n.table));
    f.columns.add(columnId(n.table, n.key));
    if (n.variable) f.variables.add(variableId(n.variable));
  }
  for (const r of d.relationships)
    if (edges.has(r.type)) {
      const end = node(r.end);
      f.tables.add(tableId(r.table));
      f.tables.add(tableId(end.table));
      f.columns.add(columnId(r.table, r.column));
      f.columns.add(columnId(end.table, end.key));
      if (r.variable) f.variables.add(variableId(r.variable));
    }
  return f;
}

/** What a click on a path in the semantic picture means in the schema: a table or its key column is its node, a pointing column its arrow, a variable the arrows that follow it and the node it keys. */
export function seedOfPath(d: Virtual, id: string): Seed {
  const [kind, rest] = [id[0], id.slice(2)];
  if (kind === "t") return { nodes: [], edges: [], holders: d.nodes.filter((n) => n.table === rest).map((n) => n.label) };
  if (kind === "c") {
    const key = d.nodes.filter((n) => columnId(n.table, n.key) === id);
    if (key.length) return { nodes: [], edges: [], holders: key.map((n) => n.label) };
    return { nodes: [], edges: d.relationships.filter((r) => columnId(r.table, r.column) === id).map((r) => r.type) };
  }
  return {
    nodes: [],
    edges: d.relationships.filter((r) => r.variable === rest).map((r) => r.type),
    holders: d.nodes.filter((n) => n.variable === rest).map((n) => n.label),
  };
}

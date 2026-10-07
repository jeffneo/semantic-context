import type { VNode, VRel } from "./data";

/*
  Where the nodes of a schema go: in layers. A node nothing points at (the facts: calls, transactions) is at the top; one is a layer below the lowest of
  those that point at it; nodes that point at nothing (the dimensions: a branch, a product) line up along the bottom. Within a layer, nodes are ordered
  to keep the arrows short (the barycentre of their neighbours, a few sweeps). Deterministic: no randomness, so the picture is the same every time and
  for every visitor.
*/
export const W = 820;
export const H = 640;
const PAD = 56;
/** A narrower canvas, for when two pictures sit side by side. */
export const COMPACT = { w: 640, h: 720 };

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export const boxWidth = (label: string) => Math.max(124, label.length * 9.2 + 30);
export const BOX_H = 54;
const GAP = 26; // the least space between two boxes in a row
const STAGGER = 40; // a crowded row alternates up and down by this much

export function layout(nodes: VNode[], rels: VRel[], w = W, h = H): Map<string, Box> {
  const ids = nodes.map((n) => n.label).sort();
  const out = new Map(ids.map((id) => [id, [] as string[]]));
  const into = new Map(ids.map((id) => [id, [] as string[]]));
  for (const r of rels) {
    out.get(r.start)!.push(r.end);
    into.get(r.end)!.push(r.start);
  }

  // layers: longest path from the top (a bounded number of passes, so a cycle cannot loop), then the sinks to the bottom
  const layer = new Map(ids.map((id) => [id, 0]));
  for (let pass = 0; pass < ids.length; pass++) for (const r of rels) layer.set(r.end, Math.max(layer.get(r.end)!, layer.get(r.start)! + 1));
  const last = Math.max(...layer.values());
  for (const id of ids) if (out.get(id)!.length === 0 && last > 0) layer.set(id, last);

  const rows: string[][] = Array.from({ length: last + 1 }, () => []);
  for (const id of ids) rows[layer.get(id)!].push(id);

  // order each row by where its neighbours sit (their place in their own row, from 0 to 1)
  const place = (id: string) => {
    const row = rows[layer.get(id)!];
    return row.length === 1 ? 0.5 : row.indexOf(id) / (row.length - 1);
  };
  for (let sweep = 0; sweep < 8; sweep++)
    for (const row of sweep % 2 ? [...rows].reverse() : rows) {
      const key = new Map(
        row.map((id) => {
          const near = [...out.get(id)!, ...into.get(id)!];
          return [id, near.length ? near.reduce((s, n) => s + place(n), 0) / near.length : 0.5] as const;
        }),
      );
      row.sort((a, b) => key.get(a)! - key.get(b)! || a.localeCompare(b));
    }

  const boxes = new Map<string, Box>();
  rows.forEach((row, li) => {
    const widths = row.map(boxWidth);
    const crowded = widths.reduce((sum, bw) => sum + bw, 0) + (row.length - 1) * GAP > w - 2 * PAD;
    const y = rows.length === 1 ? h / 2 : PAD + 27 + (li / (rows.length - 1)) * (h - 2 * PAD - 54);
    row.forEach((id, i) => {
      const x = PAD + ((i + 0.5) / row.length) * (w - 2 * PAD);
      boxes.set(id, { x, y: y + (crowded ? (i % 2 ? STAGGER : -STAGGER) * (li === rows.length - 1 ? 1 : 0.5) : 0), w: widths[i], h: BOX_H });
    });
  });
  return boxes;
}

/** The point where the line from a box's middle toward (tx, ty) leaves the box. */
export function edgePoint(b: Box, tx: number, ty: number): [number, number] {
  const [dx, dy] = [tx - b.x, ty - b.y];
  const t = Math.min(dx === 0 ? Infinity : b.w / 2 / Math.abs(dx), dy === 0 ? Infinity : b.h / 2 / Math.abs(dy));
  return [b.x + dx * t, b.y + dy * t];
}

import { useId, useMemo } from "react";
import type { Pick, Virtual, VRel } from "./data";
import { edgePoint, H, layout, W, type Box } from "./force";

interface Props {
  d: Virtual;
  pick: Pick | null;
  onPick: (p: Pick) => void;
  onHover?: (p: Pick | null) => void;
  /** when set, only these are drawn at full strength (the labels and the types a question's Cypher uses) */
  lit?: { nodes: Set<string>; edges: Set<string> } | null;
  /** the canvas, when it is not the usual one */
  size?: { w: number; h: number };
  /** draw the schema in another colour with some of it taken: the nodes (how strongly, and a count on the corner) and the arrows that were */
  tint?: { color: string; nodes: Map<string, { strength: number; badge?: string }>; edges: Set<string> };
}

const COLOR = "var(--shard-rows)"; // the Virtual Graph's colour in the architecture

/** A relationship's curve: from the edge of one box to the edge of the other, bowed a little (more when two nodes have several). */
function curve(r: VRel, boxes: Map<string, Box>, bend: number) {
  const [a, b] = [boxes.get(r.start)!, boxes.get(r.end)!];
  const [mx, my] = [(a.x + b.x) / 2, (a.y + b.y) / 2];
  const [dx, dy] = [b.x - a.x, b.y - a.y];
  const len = Math.max(1, Math.hypot(dx, dy));
  const [cx, cy] = [mx - (dy / len) * bend, my + (dx / len) * bend];
  const [x0, y0] = edgePoint(a, cx, cy);
  const [x1, y1] = edgePoint(b, cx, cy);
  return { d: `M${x0} ${y0} Q${cx} ${cy} ${x1} ${y1}`, lx: 0.25 * x0 + 0.5 * cx + 0.25 * x1, ly: 0.25 * y0 + 0.5 * cy + 0.25 * y1 };
}

/*
  The schema as a graph: a box per node label, an arrow per relationship type, in the Virtual Graph's colour. Select a node or an arrow to read how it was
  made. Where a question is given, the labels and types its Cypher uses stay bright and the rest fade.
*/
export default function SchemaGraph({ d, pick, onPick, onHover, lit, size = { w: W, h: H }, tint }: Props) {
  const uid = useId().replace(/:/g, ""); // marker ids are shared by the whole page, so each graph names its own
  const boxes = useMemo(() => layout(d.nodes, d.relationships, size.w, size.h), [d, size.w, size.h]);
  const edges = useMemo(() => {
    // parallel arrows between the same two nodes fan out
    const group = new Map<string, VRel[]>();
    for (const r of d.relationships) {
      const key = [r.start, r.end].sort().join("|");
      group.set(key, [...(group.get(key) ?? []), r]);
    }
    return d.relationships.map((r) => {
      const peers = group.get([r.start, r.end].sort().join("|"))!;
      const i = peers.indexOf(r);
      const bend = peers.length === 1 ? 16 : (i - (peers.length - 1) / 2) * 44;
      return { r, ...curve(r, boxes, bend) };
    });
  }, [d, boxes]);

  const edgeOn = (r: VRel) => {
    if (lit) return lit.edges.has(r.type);
    if (pick?.kind === "node") return r.start === pick.id || r.end === pick.id;
    if (pick?.kind === "edge") return r.type === pick.id;
    return true;
  };
  const nodeOn = (label: string) => {
    if (lit) return lit.nodes.has(label);
    if (pick?.kind === "node") return label === pick.id || d.relationships.some((r) => (r.start === pick.id && r.end === label) || (r.end === pick.id && r.start === label));
    if (pick?.kind === "edge") return d.relationships.some((r) => r.type === pick.id && (r.start === label || r.end === label));
    return true;
  };

  return (
    <svg viewBox={`0 0 ${size.w} ${size.h}`} className="h-auto w-full" role="img" aria-label={`The generated schema: ${d.nodes.length} node labels and ${d.relationships.length} relationship types`}>
      <defs>
        {[
          ["arrow", COLOR],
          ["arrow-tint", tint?.color ?? COLOR],
          ["arrow-grey", "var(--line-strong)"],
        ].map(([id, fill]) => (
          <marker key={id} id={`${uid}-${id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 1 L9 5 L0 9 z" fill={fill} />
          </marker>
        ))}
      </defs>

      {edges.map(({ r, d: path, lx, ly }) => {
        const on = edgeOn(r);
        const chosen = pick?.kind === "edge" && pick.id === r.type;
        const taken = tint ? tint.edges.has(r.type) : true;
        const stroke = tint ? (taken ? tint.color : "var(--line-strong)") : COLOR;
        return (
          <g key={r.type} opacity={tint ? (taken ? 1 : 0.5) : on ? 1 : lit ? 0.12 : 0.28} className="transition-opacity">
            <path d={path} fill="none" stroke={stroke} strokeWidth={chosen ? 3.5 : tint && taken ? 2.4 : tint ? 1.3 : 1.8} strokeLinecap="round" markerEnd={`url(#${uid}-${tint ? (taken ? "arrow-tint" : "arrow-grey") : "arrow"})`} opacity={chosen || tint ? 1 : 0.75} />
            <text x={lx} y={ly} textAnchor="middle" dy={3.5} fontSize={11} className="fill-fg font-mono" style={{ paintOrder: "stroke", stroke: "var(--bg)", strokeWidth: 4, strokeLinejoin: "round" }}>
              {r.type}
            </text>
            {/* a wide invisible stroke, so a thin arrow is easy to hit */}
            <path
              d={path}
              fill="none"
              stroke="transparent"
              strokeWidth={16}
              style={{ cursor: "pointer" }}
              onClick={() => onPick({ kind: "edge", id: r.type })}
              onMouseEnter={() => onHover?.({ kind: "edge", id: r.type })}
              onMouseLeave={() => onHover?.(null)}
            />
          </g>
        );
      })}

      {d.nodes.map((n) => {
        const b = boxes.get(n.label)!;
        const chosen = pick?.kind === "node" && pick.id === n.label;
        const t = tint?.nodes.get(n.label);
        const color = tint ? (t ? tint.color : "var(--line-strong)") : COLOR;
        return (
          <g
            key={n.label}
            transform={`translate(${b.x - b.w / 2} ${b.y - b.h / 2})`}
            opacity={tint ? (t ? 1 : 0.55) : nodeOn(n.label) ? 1 : lit ? 0.16 : 0.4}
            className="transition-opacity"
            style={{ cursor: "pointer" }}
            onClick={() => onPick({ kind: "node", id: n.label })}
            onMouseEnter={() => onHover?.({ kind: "node", id: n.label })}
            onMouseLeave={() => onHover?.(null)}
          >
            <rect
              width={b.w}
              height={b.h}
              rx={11}
              fill={tint ? (t ? `color-mix(in oklab, ${color} ${Math.round(8 + 22 * t.strength)}%, var(--bg))` : "var(--bg-subtle)") : `color-mix(in oklab, ${color} ${chosen ? 18 : 8}%, var(--bg))`}
              stroke={color}
              strokeWidth={chosen ? 3 : tint && t ? 2 : 1.6}
            />
            {t?.badge && (
              <g transform={`translate(${b.w - 4} -9)`}>
                <rect x={-(t.badge.length * 6.6 + 12)} width={t.badge.length * 6.6 + 12} height={17} rx={8.5} fill={color} />
                <text x={-(t.badge.length * 6.6 + 12) / 2} y={12} textAnchor="middle" fontSize={10.5} fontWeight={600} className="font-mono" fill="var(--bg)">
                  {t.badge}
                </text>
              </g>
            )}
            <text x={b.w / 2} y={22} textAnchor="middle" fontSize={15} fontWeight={600} className="fill-fg">
              {n.label}
            </text>
            <text x={b.w / 2} y={40} textAnchor="middle" fontSize={11} className="fill-fg-muted font-mono">
              {n.key}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

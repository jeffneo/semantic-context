import type NVL from "@neo4j-nvl/base";
import type { Node, Relationship } from "@neo4j-nvl/base";
import { InteractiveNvlWrapper } from "@neo4j-nvl/react";
import { useMemo, useRef, useState } from "react";
import { useTheme } from "../theme/useTheme";
import type { GraphNode, GraphRel } from "./api";
import { caption } from "./ResultTable";

const COLORS = [
  "--shard-semantic",
  "--shard-rows",
  "--shard-memory",
  "--composite",
  "--area-1",
  "--area-2",
  "--area-3",
  "--area-4",
];

/*
  A result's nodes and relationships, drawn by NVL, Neo4j's own visualization library. A label has a colour for as long as the page is open; click a node to
  read its properties. NVL's usage telemetry is off.
*/
export default function ResultGraph({
  nodes,
  rels,
}: {
  nodes: GraphNode[];
  rels: GraphRel[];
}) {
  const { mode } = useTheme();
  const [chosen, setChosen] = useState<string | null>(null);
  const nvl = useRef<NVL>(null);

  const { drawn, links, legend } = useMemo(() => {
    const css = getComputedStyle(document.documentElement);
    const palette = COLORS.map((c) => css.getPropertyValue(c).trim() || "#888");
    const labels = [...new Set(nodes.map((n) => n.labels[0] ?? ""))].sort();
    const colour = (n: GraphNode) =>
      palette[labels.indexOf(n.labels[0] ?? "") % palette.length];
    return {
      drawn: nodes.map(
        (n): Node => ({
          id: n.id,
          caption: caption(n),
          color: colour(n),
          size: 22,
          captionAlign: "center",
          captionSize: 2,
        }),
      ),
      links: rels.map(
        (r): Relationship => ({
          id: r.id,
          from: r.from,
          to: r.to,
          caption: r.type,
          color: css.getPropertyValue("--line-strong").trim() || "#999",
        }),
      ),
      legend: labels.map((l) => ({
        label: l,
        color: palette[labels.indexOf(l) % palette.length],
      })),
    };
    // the palette is read from the page's variables, so it is read again when light becomes dark
  }, [nodes, rels, mode]);

  const node = nodes.find((n) => n.id === chosen);
  return (
    <div>
      <div className="relative h-[26rem] w-full bg-bg">
        <InteractiveNvlWrapper
          nodes={drawn}
          rels={links}
          ref={nvl}
          nvlOptions={{ disableTelemetry: true }}
          nvlCallbacks={{
            onLayoutDone: () => nvl.current?.fit(drawn.map((n) => n.id)),
          }}
          mouseEventCallbacks={{
            onPan: true,
            onZoomAndPan: true,
            onDrag: true,
            onNodeClick: (n: Node) => setChosen(n.id),
            onCanvasClick: () => setChosen(null),
          }}
          style={{ width: "100%", height: "100%" }}
        />
        <ul className="pointer-events-none absolute left-3 top-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          {legend.map((l) => (
            <li
              key={l.label}
              className="flex items-center gap-1.5 rounded bg-bg/80 px-1.5 py-0.5"
            >
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: l.color }}
              />
              {l.label || "(no label)"}
            </li>
          ))}
        </ul>
      </div>
      <div className="border-t border-line px-4 py-3 text-xs">
        {node ? (
          <>
            <p className="font-mono">(:{node.labels.join(":")})</p>
            <dl className="mt-1 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-0.5">
              {Object.entries(node.properties).map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className="font-mono text-fg-muted">{k}</dt>
                  <dd className="min-w-0 break-words">
                    {typeof v === "string" ? v : JSON.stringify(v)}
                  </dd>
                </div>
              ))}
            </dl>
          </>
        ) : (
          <p className="text-fg-muted">
            Drag to move, scroll to zoom, click a node for its properties.
          </p>
        )}
      </div>
    </div>
  );
}

import type { GraphNode, GraphRel } from "./api";

type Elem = GraphNode | GraphRel | { $: "path"; nodes: GraphNode[]; rels: GraphRel[] };

const isElem = (v: unknown): v is Elem => typeof v === "object" && v !== null && "$" in v;

/** The property that names a node on a page: a name, else a title, else the first text it has. */
export function caption(n: GraphNode): string {
  const p = n.properties;
  for (const k of ["name", "site_name", "title", "label", "description"]) if (typeof p[k] === "string") return p[k] as string;
  for (const k of Object.keys(p)) if (typeof p[k] === "string" && (p[k] as string).length <= 40) return p[k] as string;
  for (const k of Object.keys(p)) if (typeof p[k] === "number") return String(p[k]);
  return n.labels[0] ?? "";
}

function Cell({ v }: { v: unknown }) {
  if (v === null || v === undefined) return <span className="text-fg-muted">null</span>;
  if (isElem(v)) {
    if (v.$ === "node")
      return (
        <span className="font-mono text-xs" title={JSON.stringify(v.properties)}>
          (:{v.labels.join(":")} <span className="text-fg-muted">{caption(v)}</span>)
        </span>
      );
    if (v.$ === "rel") return <span className="font-mono text-xs">[:{v.type}]</span>;
    return <span className="font-mono text-xs">path of {v.nodes.length} nodes</span>;
  }
  if (typeof v === "number") return <span className="tabular-nums">{v.toLocaleString("en-US")}</span>;
  if (typeof v === "object") return <span className="font-mono text-xs">{JSON.stringify(v).slice(0, 120)}</span>;
  return <>{String(v)}</>;
}

/** A result as a table: one column a column of the query, one row a row. */
export default function ResultTable({ columns, rows }: { columns: string[]; rows: unknown[][] }) {
  if (!columns.length) return <p className="p-4 text-sm text-fg-muted">The query returned no columns.</p>;
  return (
    <div className="max-h-96 overflow-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-bg-subtle">
          <tr>
            {columns.map((c) => (
              <th key={c} className="whitespace-nowrap border-b border-line px-3 py-2 font-mono text-xs font-medium text-fg-muted">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line last:border-b-0">
              {r.map((v, j) => (
                <td key={j} className="max-w-[28rem] truncate px-3 py-1.5 align-top">
                  <Cell v={v} />
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-3 py-4 text-fg-muted">
                No rows.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

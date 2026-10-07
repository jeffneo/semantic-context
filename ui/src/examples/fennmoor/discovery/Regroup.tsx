import { useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { ALL, fullName, type Located } from "../data";
import { AREA_COLOR, type Area, type Discovery, type TableEntry } from "./data";
import { LABEL_MAX, pack, tileAt, type Block } from "./layout";

type Mode = "datasets" | 3 | 2 | 1;

/*
  The same 323 tables, where the layer puts them (by what is read together), and where BigQuery files them (by dataset). A tile's colour is its broad
  area and never changes, so the move shows: tiles of one colour, scattered over many datasets, come together. Click a table and the others
  in its group are outlined, wherever they live.
*/
export default function Regroup({ d }: { d: Discovery }) {
  const entries = useMemo(() => new Map(d.tables.map((t) => [t.id, t])), [d]);
  const items = useMemo(() => [...ALL].sort((a, b) => fullName(a).localeCompare(fullName(b))).map((l) => ({ l, id: fullName(l), e: entries.get(fullName(l)) })), [entries]);

  const start = items.find((i) => i.id === "fennmoor-dw.dw_core.dim_customer") ?? items[0];
  const [mode, setMode] = useState<Mode>(3);
  const [selected, setSelected] = useState(start.id);
  const [hovered, setHovered] = useState<string | null>(null);
  const [focus, setFocus] = useState<number | null>(null);

  // The width the map has, so the blocks can wrap to it.
  const holder = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(720);
  useLayoutEffect(() => {
    const el = holder.current;
    if (!el) return;
    const read = () => setWidth(Math.floor(el.clientWidth));
    read();
    const watch = new ResizeObserver(read);
    watch.observe(el);
    return () => watch.disconnect();
  }, []);

  const { blocks, members } = useMemo(() => blocksFor(mode, d, items), [mode, d, items]);
  const { placed, height } = useMemo(() => pack(blocks, width), [blocks, width]);
  const where = useMemo(() => {
    const at = new Map<string, [number, number]>();
    for (const p of placed) (members.get(p.block.key) ?? []).forEach((id, i) => at.set(id, tileAt(p, i)));
    return at;
  }, [placed, members]);

  const unread = d.tables.filter((t) => t.unread).length;
  const noGroup = d.tables.filter((t) => !t.groups).length - unread;
  const sel = items.find((i) => i.id === selected) ?? start;
  const shown = items.find((i) => i.id === hovered) ?? sel;
  const kin = sel.e?.groups ? sel.e.groups[0] : null;
  const broad = (e?: TableEntry) => (e?.groups ? e.groups[2] : null);

  return (
    <div className="mt-6">
      <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
        <div role="group" aria-label="Arrange the tables" className="inline-flex rounded-md border border-line p-0.5 text-sm">
          {(
            [
              ["datasets", "By dataset"],
              [3, `${d.funnel.groups["3"]} broad areas`],
              [2, `${d.funnel.groups["2"]} areas`],
              [1, `${d.funnel.groups["1"]} groups`],
            ] as [Mode, string][]
          ).map(([m, label]) => (
            <button
              key={String(m)}
              type="button"
              aria-pressed={mode === m}
              onClick={() => setMode(m)}
              className={`rounded px-3 py-1.5 transition-colors ${mode === m ? "bg-fg text-bg" : "text-fg-muted hover:text-fg"}`}
            >
              {label}
            </button>
          ))}
        </div>
        <ul className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-fg-muted" aria-label="Key">
          <li className="flex items-center gap-2">
            <span className="tile table static" aria-hidden="true" /> table
          </li>
          <li className="flex items-center gap-2">
            <span className="tile view static" aria-hidden="true" /> view
          </li>
          <li className="flex items-center gap-2">
            <span className="tile sharded static" aria-hidden="true" /> date-sharded
          </li>
          <li className="flex items-center gap-2">
            <span className="tile table nogroup static" aria-hidden="true" /> in no group
          </li>
        </ul>
      </div>

      <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="The broad areas">
        {d.areas
          .filter((a) => a.level === 3)
          .map((a, i) => (
            <li key={a.name}>
              <button
                type="button"
                aria-pressed={focus === i}
                onClick={() => setFocus(focus === i ? null : i)}
                className={`h-full w-full rounded-card border p-3 text-left transition-colors ${focus === i ? "border-fg" : "border-line hover:border-line-strong"}`}
              >
                <span className="flex items-center gap-2 text-sm font-medium">
                  <span className="h-3 w-3 rounded-[3px]" style={{ background: AREA_COLOR[i] }} aria-hidden="true" />
                  {a.name}
                </span>
                <span className="mt-1 block text-xs tabular-nums text-fg-muted">{a.tables} tables touch it</span>
                <span className="mt-1 line-clamp-2 block text-xs text-fg-muted">{a.description}</span>
              </button>
            </li>
          ))}
      </ul>

      <p className="mt-5 h-6 overflow-hidden whitespace-nowrap text-xs" aria-live="polite">
        <span className="font-mono text-fg">{shown.id}</span>
        <span className="ml-3 text-fg-muted">{path(shown.e, d.areas)}</span>
      </p>

      <div className="mt-2 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="rounded-card border border-line bg-bg-subtle p-4">
          <div ref={holder} className="relative w-full transition-[height] duration-500" style={{ height }}>
            {items.map(({ l, id, e }) => {
              const [x, y] = where.get(id) ?? [0, 0];
              const color = e?.groups ? AREA_COLOR[e.groups[2]] : null;
              const dim = focus !== null && broad(e) !== focus;
              const same = id !== sel.id && kin !== null && e?.groups?.[0] === kin;
              const style = { translate: `${x}px ${y}px`, ...(color ? { "--ink": color } : {}) } as CSSProperties;
              return (
                <button
                  key={id}
                  type="button"
                  aria-label={id}
                  aria-pressed={id === sel.id}
                  className={`tile placed ${l.table.kind}${color ? "" : " nogroup"}${dim ? " dim" : ""}${id === sel.id ? " sel" : ""}${same ? " kin" : ""}`}
                  style={style}
                  onMouseEnter={() => setHovered(id)}
                  onMouseLeave={() => setHovered(null)}
                  onFocus={() => setHovered(id)}
                  onBlur={() => setHovered(null)}
                  onClick={() => setSelected(id)}
                />
              );
            })}
            {placed
              .filter((p) => p.block.labelled)
              .map((p) =>
                p.block.heading ? (
                  <div key={`${String(mode)}:${p.block.key}`} className="block-label pointer-events-none flex items-baseline gap-2" style={{ translate: `${p.x}px ${p.y}px` }}>
                    {p.block.color && <span className="h-2.5 w-2.5 translate-y-px rounded-[3px]" style={{ background: p.block.color }} aria-hidden="true" />}
                    <span className="text-xs font-medium">{p.block.name}</span>
                    <span className="text-[11px] tabular-nums text-fg-muted">{p.block.count} tables</span>
                  </div>
                ) : (
                  <div key={`${String(mode)}:${p.block.key}`} className="block-label pointer-events-none" style={{ translate: `${p.x}px ${p.y}px`, maxWidth: LABEL_MAX }}>
                    <p className="truncate font-mono text-[11px] leading-tight">{p.block.name}</p>
                    <p className="text-[10px] leading-tight text-fg-muted">{p.block.count} tables</p>
                  </div>
                ),
              )}
          </div>
        </div>

        <div className="xl:sticky xl:top-20 xl:max-h-[calc(100svh-6rem)] xl:overflow-auto xl:rounded-card">
          <Where d={d} item={sel} items={items} onPick={setSelected} />
        </div>
      </div>
      <p className="mt-4 max-w-3xl text-xs leading-relaxed text-fg-muted">
        Each table is drawn once, in the group that holds most of its columns. A table with columns in several groups touches each of them, which is why a
        count above is higher than the tiles under it. The tables in no group are the {unread} no query read and {noGroup} whose columns no group holds. Names and descriptions
        were written by a model from what each group holds.
      </p>
    </div>
  );
}

type Item = { l: Located; id: string; e: TableEntry | undefined };

/** A table's place in words: its group, the area above it, the broad area above that. */
function path(e: TableEntry | undefined, areas: Area[]) {
  if (!e) return "";
  if (!e.groups) return e.unread ? "no query in the log read it" : "no group holds its columns";
  return e.groups.map((i) => areas[i].name).join("  ›  ");
}

/** The blocks of a layout, in the order they are laid out (with the headings of the sections they sit in), and the tiles in each. */
function blocksFor(mode: Mode, d: Discovery, items: Item[]): { blocks: Block[]; members: Map<string, string[]> } {
  const members = new Map<string, string[]>();
  const names = new Map<string, string>();
  const order = new Map<string, number[]>(); // what a block sorts by, before its size
  const section = new Map<string, { key: string; name: string; color?: string }>(); // the heading a block sits under
  const projects = ["fennmoor-raw", "fennmoor-dw", "fennmoor-analytics"];
  for (const { l, id, e } of items) {
    let key: string;
    let rank: number[];
    if (mode === "datasets") {
      key = `${l.project.name}.${l.dataset.name}`;
      names.set(key, l.dataset.name);
      section.set(key, { key: l.project.name, name: l.project.name });
      rank = [projects.indexOf(l.project.name)];
    } else if (e?.groups) {
      const i = e.groups[mode - 1];
      key = `a${i}`;
      names.set(key, d.areas[i].name);
      rank = [e.groups[2], mode === 1 ? e.groups[1] : 0];
      // groups sit under their area, areas under their broad area; the broad areas have no heading above them
      const up = mode === 1 ? e.groups[1] : mode === 2 ? e.groups[2] : null;
      if (up !== null) section.set(key, { key: `a${up}`, name: d.areas[up].name, color: AREA_COLOR[e.groups[2]] });
    } else {
      key = "none";
      names.set(key, "In no group");
      rank = [99, 0];
      if (mode !== 3) section.set(key, { key: "none", name: "In no group" });
    }
    members.set(key, [...(members.get(key) ?? []), id]);
    order.set(key, rank);
  }
  const sorted = [...members.keys()].sort((a, b) => {
    const [ra, rb] = [order.get(a)!, order.get(b)!];
    for (let i = 0; i < ra.length; i++) if (ra[i] !== rb[i]) return ra[i] - rb[i];
    return members.get(b)!.length - members.get(a)!.length || names.get(a)!.localeCompare(names.get(b)!);
  });

  const blocks: Block[] = [];
  let current: string | null = null;
  for (const key of sorted) {
    const up = section.get(key);
    if (up && up.key !== current) {
      current = up.key;
      const tiles = sorted.filter((k) => section.get(k)?.key === up.key).reduce((n, k) => n + members.get(k)!.length, 0);
      blocks.push({ key: `heading:${up.key}`, name: up.name, count: tiles, labelled: true, heading: true, color: up.color });
    }
    const count = members.get(key)!.length;
    // a heading already says "In no group", and the many small groups are unlabelled: found by hovering
    const labelled = key === "none" ? mode === 3 : mode !== 1 || count >= 4;
    blocks.push({ key, name: names.get(key)!, count, labelled });
  }
  return { blocks, members };
}

const LEVEL = ["group", "area", "broad area"];

/** The selected table: where the layer put it, from the broad area down to its group, and what else is in that group. */
function Where({ d, item, items, onPick }: { d: Discovery; item: Item; items: Item[]; onPick: (id: string) => void }) {
  const { l, e } = item;
  const chain = e?.groups ? [...e.groups].reverse() : [];
  const sameGroup = e?.groups ? items.filter((i) => i.id !== item.id && i.e?.groups?.[0] === e.groups![0]) : [];
  return (
    <section className="rounded-card border border-line bg-bg p-5" aria-label={`Where ${item.id} sits`}>
      <p className="font-mono text-sm break-all">
        <span className="text-fg-muted">
          {l.project.name}.{l.dataset.name}.
        </span>
        <span className="font-semibold">{l.table.name}</span>
      </p>
      <p className="mt-1 text-sm text-fg-muted">
        {l.table.kind} · {e?.columns ?? l.table.columns.length} columns
        {e?.groups && e.share !== undefined && ` · ${Math.round(e.share * 100)}% of them in its group`}
      </p>

      {chain.length === 0 ? (
        <p className="mt-5 text-sm">
          {e?.unread
            ? "No query in the 90 days read this table, so the log says nothing about what it means: it is in no group."
            : "Queries read it, but none of its columns is held by a group."}
        </p>
      ) : (
        <ol className="mt-5 space-y-4">
          {chain.map((i, depth) => {
            const a = d.areas[i];
            return (
              <li key={i} style={{ marginLeft: depth * 14 }} className="border-l-2 pl-3" >
                <p className="flex items-baseline gap-2 text-xs text-fg-muted">
                  <span className="h-2.5 w-2.5 translate-y-px rounded-[3px]" style={{ background: AREA_COLOR[e!.groups![2]] }} aria-hidden="true" />
                  {LEVEL[2 - depth]} · {a.tables} tables touch it
                  {a.stability !== undefined && ` · stability ${a.stability}`}
                </p>
                <p className="mt-0.5 text-sm font-medium leading-snug">{a.name}</p>
                <p className="mt-1 text-xs leading-relaxed text-fg-muted">{a.description}</p>
              </li>
            );
          })}
        </ol>
      )}

      {sameGroup.length > 0 && (
        <div className="mt-5 border-t border-line pt-4">
          <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">Read together with it</p>
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {sameGroup.slice(0, 14).map((i) => (
              <li key={i.id}>
                <button
                  type="button"
                  onClick={() => onPick(i.id)}
                  className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px] text-fg-muted hover:border-line-strong hover:text-fg"
                >
                  {i.l.dataset.name}.{i.l.table.name}
                </button>
              </li>
            ))}
            {sameGroup.length > 14 && <li className="px-1 py-0.5 text-[11px] text-fg-muted">and {sameGroup.length - 14} more</li>}
          </ul>
        </div>
      )}
    </section>
  );
}

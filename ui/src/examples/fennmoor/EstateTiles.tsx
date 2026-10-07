import { useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { ALL, fullName, type Located } from "./data";
import { pack, tileAt, type Block } from "./discovery/layout";

const PROJECTS = ["fennmoor-raw", "fennmoor-dw", "fennmoor-analytics"];

/** How a table's square is drawn: its colour, and a ring for one worth marking. */
export interface TileLook {
  ink: string;
  ring?: boolean;
}

/*
  The estate's squares by dataset, as in the warehouse section, for a page to colour by something about each table: how long it holds, who may read it.
  The squares do not respond to the pointer; the page says what the colours mean.
*/
export default function EstateTiles({ look }: { look: (l: Located, id: string) => TileLook }) {
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

  const items = useMemo(() => [...ALL].map((l) => ({ l, id: fullName(l) })).sort((a, b) => a.id.localeCompare(b.id)), []);
  const { placed, height, where } = useMemo(() => {
    const members = new Map<string, string[]>();
    const rank = new Map<string, number>();
    const names = new Map<string, string>();
    for (const { l, id } of items) {
      const key = `${l.project.name}.${l.dataset.name}`;
      members.set(key, [...(members.get(key) ?? []), id]);
      rank.set(key, PROJECTS.indexOf(l.project.name));
      names.set(key, l.dataset.name);
    }
    const blocks: Block[] = [...members.keys()]
      .sort((a, b) => rank.get(a)! - rank.get(b)! || members.get(b)!.length - members.get(a)!.length || a.localeCompare(b))
      .map((key) => ({ key, name: names.get(key)!, count: members.get(key)!.length, labelled: true }));
    const packed = pack(blocks, width);
    const at = new Map<string, [number, number]>();
    for (const p of packed.placed) members.get(p.block.key)!.forEach((id, i) => at.set(id, tileAt(p, i)));
    return { ...packed, where: at };
  }, [items, width]);

  return (
    <div ref={holder} className="relative w-full" style={{ height }}>
      {items.map(({ l, id }) => {
        const [x, y] = where.get(id) ?? [0, 0];
        const t = look(l, id);
        const style = { translate: `${x}px ${y}px`, "--ink": t.ink } as CSSProperties;
        return <span key={id} aria-hidden="true" className={`tile placed static ${l.table.kind}${t.ring ? " sel" : ""}`} style={style} />;
      })}
      {placed.map((b) => (
        <div key={b.block.key} className="pointer-events-none absolute left-0 top-0" style={{ translate: `${b.x}px ${b.y}px`, maxWidth: 200 }}>
          <p className="truncate font-mono text-[11px] leading-tight">{b.block.name}</p>
          <p className="text-[10px] leading-tight text-fg-muted">{b.block.count} tables</p>
        </div>
      ))}
    </div>
  );
}

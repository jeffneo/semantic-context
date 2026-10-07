import { useEffect, useState } from "react";
import type { SectionGroup } from "../examples/types";

/*
  The contents of an example page, down the left: the sections, in their groups, with the one being read marked. Links are plain #anchors (the page
  scrolls smoothly to them), so a section can be linked to and the back button works.
*/
export default function SectionNav({ groups }: { groups: SectionGroup[] }) {
  const ids = groups.flatMap((g) => g.sections.map((s) => s.id));
  const [active, setActive] = useState(ids[0]);
  const key = ids.join(",");

  useEffect(() => {
    // The section being read is the last one whose top has reached the header's edge; at the very bottom of the page, the last section.
    const list = key.split(",");
    const update = () => {
      const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      let current = list[0];
      for (const id of list) {
        const top = document.getElementById(id)?.getBoundingClientRect().top;
        if (top !== undefined && top <= 120) current = id;
      }
      setActive(atBottom ? list[list.length - 1] : current);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [key]);

  return (
    <nav aria-label="Contents" className="sticky top-20 py-10 text-sm">
      {groups.map((g) => (
        <div key={g.label} className="mb-7">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-fg-muted">{g.label}</p>
          <ul className="border-l border-line">
            {g.sections.map((s) => {
              const on = s.id === active;
              return (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    aria-current={on ? "location" : undefined}
                    className={`-ml-px flex items-baseline justify-between gap-2 border-l py-1.5 pl-3 pr-1 transition-colors ${
                      on ? "border-fg font-medium text-fg" : "border-transparent text-fg-muted hover:text-fg"
                    }`}
                  >
                    {s.title}
                    {!s.Body && <span className="text-[10px] font-normal uppercase tracking-wider text-fg-muted/70">soon</span>}
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

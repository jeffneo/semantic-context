import { useSyncExternalStore } from "react";

/*
  How much of a section is open. Compact: each section keeps the part that carries its claim open, and the rest are one line each, opening in place. Full: every part
  open, as the page was before. ?layout=full or ?layout=compact sets it, and the page remembers it. Parts name what folds with a `summary` (see examples/Part.tsx),
  so putting the page back is this one switch, and removing the summaries removes the feature.
*/
export type Layout = "compact" | "full";
const KEY = "ui-layout";
const listeners = new Set<() => void>();

function read(): Layout {
  const asked = new URLSearchParams(window.location.search).get("layout");
  if (asked === "full" || asked === "compact") return asked;
  try {
    return localStorage.getItem(KEY) === "full" ? "full" : "compact";
  } catch {
    return "compact";
  }
}

export function setLayout(l: Layout) {
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* the page works without it */
  }
  const url = new URL(window.location.href);
  url.searchParams.delete("layout");
  window.history.replaceState(null, "", url);
  listeners.forEach((f) => f());
}

export function useLayout(): Layout {
  return useSyncExternalStore(
    (f) => {
      listeners.add(f);
      return () => listeners.delete(f);
    },
    read,
    () => "compact",
  );
}

import type { Example } from "./types";

/*
  The examples, one per estate. The list is all the nav needs, so it is light; an example itself (its data is large) loads when its page is opened.
  To add one: a folder beside fennmoor/ whose index.tsx default-exports an Example, and a line in each of these two.
*/
export const EXAMPLE_LIST = [{ slug: "fennmoor", name: "Fennmoor Bank" }] as const;

const LOADERS: Record<string, () => Promise<{ default: Example }>> = {
  fennmoor: () => import("./fennmoor"),
};

const loaded = new Map<string, Promise<Example>>();

/** The example's promise (the same one every call, so React can suspend on it), or null for a slug that is not an example. */
export function loadExample(slug: string): Promise<Example> | null {
  const load = LOADERS[slug];
  if (!load) return null;
  if (!loaded.has(slug)) loaded.set(slug, load().then((m) => m.default));
  return loaded.get(slug)!;
}

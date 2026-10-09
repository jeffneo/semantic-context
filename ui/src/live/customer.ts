import { useSyncExternalStore } from "react";
import { pick, ServerError } from "./api";

/*
  The customer the memory examples run on: one for the whole page, so that the check, the recall and the check again all name the same customer. It is chosen
  when the page loads (`startCustomer`, from main.tsx), which also wakes the path to the warehouse before the first live example is opened; "choose another" replaces it.
*/
interface State {
  customer: string | null;
  error: string | null;
}
let state: State = { customer: null, error: null };
let started = false;
const listeners = new Set<() => void>();

function set(next: State) {
  state = next;
  listeners.forEach((l) => l());
}

export function chooseCustomer() {
  started = true;
  set({ customer: null, error: null });
  pick().then(
    (r) => set({ customer: r.customer, error: null }),
    (e: unknown) => set({ customer: null, error: e instanceof ServerError ? e.message : String(e) }),
  );
}

/** Once, as the page loads. */
export function startCustomer() {
  if (!started) chooseCustomer();
}

export function useCustomer(wanted: boolean) {
  const s = useSyncExternalStore(
    (l) => (listeners.add(l), () => void listeners.delete(l)),
    () => state,
  );
  if (wanted && !started) queueMicrotask(startCustomer); // a page that did not start it at load (a test, a lone panel)
  return { ...s, choose: chooseCustomer };
}

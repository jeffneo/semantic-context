import { useSyncExternalStore } from "react";

/** The brand themes available (each is a [data-theme] block in ./themes/*.css). "default" is no override. */
export const THEMES = ["default", "neo4j"] as const;
export type Theme = (typeof THEMES)[number];
export type Mode = "system" | "light" | "dark";

const THEME_KEY = "ui-theme";
const MODE_KEY = "ui-mode";

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null; // private windows, blocked storage
  }
}
function write(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* the page works without it */
  }
}

function currentTheme(): Theme {
  const asked = new URLSearchParams(window.location.search).get("theme") ?? read(THEME_KEY);
  return (THEMES as readonly string[]).includes(asked ?? "") ? (asked as Theme) : "default";
}
function currentMode(): Mode {
  const asked = new URLSearchParams(window.location.search).get("mode") ?? read(MODE_KEY);
  return asked === "dark" || asked === "system" ? asked : "light"; // light for now; "system" follows the OS
}

function apply(theme: Theme, mode: Mode) {
  const root = document.documentElement;
  if (theme === "default") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
  if (mode === "system") root.removeAttribute("data-mode");
  else root.setAttribute("data-mode", mode);
}

/** Called once before the first render. */
export function applyStoredTheme() {
  const theme = currentTheme();
  const mode = currentMode();
  // a theme or mode named in the URL is remembered
  if (new URLSearchParams(window.location.search).has("theme")) write(THEME_KEY, theme);
  if (new URLSearchParams(window.location.search).has("mode")) write(MODE_KEY, mode);
  apply(theme, mode);
}

// One store for the page, so the nav's toggle and the footer's selectors agree.
let state = { theme: "default" as Theme, mode: "light" as Mode };
let ready = false;
const listeners = new Set<() => void>();
function init() {
  if (ready) return;
  ready = true;
  state = { theme: currentTheme(), mode: currentMode() };
}
function set(next: Partial<typeof state>) {
  state = { ...state, ...next };
  apply(state.theme, state.mode);
  listeners.forEach((l) => l());
}

export function useTheme() {
  init();
  const snapshot = useSyncExternalStore(
    (l) => (listeners.add(l), () => listeners.delete(l)),
    () => state,
  );
  return {
    theme: snapshot.theme,
    mode: snapshot.mode,
    setTheme: (t: Theme) => (write(THEME_KEY, t), set({ theme: t })),
    setMode: (m: Mode) => (write(MODE_KEY, m), set({ mode: m })),
  };
}

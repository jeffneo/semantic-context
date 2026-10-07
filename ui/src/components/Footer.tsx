import { THEMES, useTheme, type Mode } from "../theme/useTheme";

const MODES: Mode[] = ["system", "light", "dark"];

export default function Footer() {
  const { theme, setTheme, mode, setMode } = useTheme();
  return (
    <footer>
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-10 text-sm text-fg-muted sm:flex-row sm:items-center sm:justify-between">
        <p>A concept demo on a synthetic estate. Not a product.</p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
          <label className="flex items-center gap-2">
            Theme
            <select
              className="rounded-md border border-line-strong bg-bg px-2 py-1 text-fg"
              value={theme}
              onChange={(e) => setTheme(e.target.value as (typeof THEMES)[number])}
            >
              {THEMES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            Mode
            <select
              className="rounded-md border border-line-strong bg-bg px-2 py-1 text-fg"
              value={mode}
              onChange={(e) => setMode(e.target.value as Mode)}
            >
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </footer>
  );
}

import { Link, NavLink } from "react-router";
import { REPO } from "../repo";
import { useTheme } from "../theme/useTheme";

/** Set in the environment (see .env.example); the header shows nothing when it is unset. */
const CONTACT = import.meta.env.NEO4J_CONTACT_EMAIL;

export default function Nav() {
  const { mode, setMode } = useTheme();
  const dark = mode === "dark";
  return (
    <header className="sticky top-0 z-20 h-14 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex h-full max-w-[1800px] items-center justify-between px-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5 text-sm font-semibold tracking-tight">
          <span aria-hidden="true" className="grid h-6 w-6 place-items-center rounded-md bg-accent text-accent-fg">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
              <circle cx="4" cy="7" r="2" />
              <circle cx="10" cy="3.5" r="1.5" />
              <circle cx="10" cy="10.5" r="1.5" />
            </svg>
          </span>
          Neo4j ContextEngine
        </Link>
        <div className="flex items-center gap-5 text-sm text-fg-muted">
          {/* /examples goes to the example, and to a list of them once there are several */}
          <NavLink to="/examples" className={({ isActive }) => (isActive ? "font-medium text-fg" : "hover:text-fg")}>
            Example
          </NavLink>
          {CONTACT && (
            <span className="hidden select-text md:inline">
              Contact <span className="text-fg">{CONTACT}</span>
            </span>
          )}
          <button
            type="button"
            onClick={() => setMode(dark ? "light" : "dark")}
            aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
            className="grid h-8 w-8 place-items-center rounded-md border border-line text-fg-muted transition hover:text-fg"
          >
            {dark ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
              </svg>
            )}
          </button>
          <a
            href={REPO}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Source on GitHub"
            className="grid h-8 w-8 place-items-center rounded-md text-fg-muted transition hover:text-fg"
          >
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
}

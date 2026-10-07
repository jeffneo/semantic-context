import { Link, NavLink } from "react-router";
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
        </div>
      </div>
    </header>
  );
}

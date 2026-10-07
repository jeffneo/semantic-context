import { CAVEAT, PROOF } from "../content/proof";

export default function Evidence() {
  return (
    <section id="evidence" className="scroll-mt-14 border-b border-line">
      <div className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="max-w-2xl text-balance text-3xl font-semibold tracking-tight sm:text-4xl">Measured, not claimed.</h2>
        <p className="mt-4 max-w-2xl text-fg-muted">
          Each figure answers a problem teams hit when they point an agent at a warehouse, and each links to the run behind it.
        </p>

        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {PROOF.map((p) => (
            <article key={p.problem} className="flex flex-col bg-bg p-6">
              <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">{p.problem}</p>
              <p className="mt-6 flex items-baseline gap-2">
                <span className="text-5xl font-semibold tracking-tight">{p.figure}</span>
                <span className="text-sm text-fg-muted">{p.unit}</span>
              </p>
              <p className="mt-3 flex-1 text-sm text-fg-muted">{p.versus}</p>
              <p className="mt-5 font-mono text-xs text-fg-muted">{p.source}</p>
            </article>
          ))}
        </div>
        <p className="mt-5 max-w-3xl text-xs text-fg-muted">{CAVEAT}</p>
      </div>
    </section>
  );
}

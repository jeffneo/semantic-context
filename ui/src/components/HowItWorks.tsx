import { STEPS } from "../content/proof";

export default function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-14 border-b border-line bg-bg-subtle">
      <div className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="max-w-2xl text-balance text-3xl font-semibold tracking-tight sm:text-4xl">The cheapest trustworthy route first.</h2>
        <p className="mt-4 max-w-2xl text-fg-muted">
          The model chooses and fills in; code compiles and checks. Most questions never need the expensive path.
        </p>
        <ol className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <li key={s.n} className="rounded-card border border-line bg-bg p-6">
              <span className="grid h-7 w-7 place-items-center rounded-full border border-line-strong font-mono text-xs">{s.n}</span>
              <h3 className="mt-4 text-base font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-fg-muted">{s.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

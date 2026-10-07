import { Suspense, use, useEffect } from "react";
import { useLocation, useParams } from "react-router";
import SectionNav from "../components/SectionNav";
import { setLayout, useLayout } from "../layout";
import { codeUrl } from "../repo";
import { loadExample } from "../examples";
import type { Example, Section } from "../examples/types";
import NotFound from "./NotFound";

/*
  An example's page, the same for every example: its own header (name, one line, the size of the estate), then the contents down the left and the
  sections down the page. What differs is the Example it is given (src/examples/<slug>/), loaded when the page opens.
*/
export default function ExamplePage() {
  const { slug = "" } = useParams();
  const loading = loadExample(slug);
  if (!loading) return <NotFound />;
  return (
    <Suspense fallback={<p className="mx-auto max-w-[1800px] px-5 py-24 text-fg-muted sm:px-8">Loading the example…</p>}>
      <Loaded loading={loading} />
    </Suspense>
  );
}

function Loaded({ loading }: { loading: Promise<Example> }) {
  const ex = use(loading);
  const { hash } = useLocation();
  const layout = useLayout();

  // Opening a link into a section (/examples/fennmoor#warehouse) cannot scroll until the example has loaded, so it is done here, once. Links within
  // the page are the browser's own, and scroll smoothly.
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "instant" });
  }, []);

  return (
    <>
      <header className="border-b border-line bg-bg-subtle">
        <div className="mx-auto max-w-[1800px] px-5 pb-10 pt-12 sm:px-8">
          <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">Example</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight sm:text-5xl">{ex.name}</h1>
          <p className="mt-4 max-w-3xl text-lg text-fg-muted">{ex.tagline}</p>
          <dl className="mt-8 flex flex-wrap gap-x-12 gap-y-5">
            {ex.stats.map((s) => (
              <div key={s.label}>
                <dd className="text-2xl font-semibold tabular-nums tracking-tight">{s.value}</dd>
                <dt className="text-sm text-fg-muted">{s.label}</dt>
              </div>
            ))}
          </dl>
          <div role="group" aria-label="Layout" className="mt-8 inline-flex items-center gap-3 text-sm text-fg-muted">
            Layout
            <span className="inline-flex rounded-md border border-line bg-bg p-0.5">
              {(["compact", "full"] as const).map((l) => (
                <button key={l} type="button" aria-pressed={layout === l} onClick={() => setLayout(l)} className={`rounded px-3 py-1 capitalize transition-colors ${layout === l ? "bg-fg text-bg" : "hover:text-fg"}`}>
                  {l}
                </button>
              ))}
            </span>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1800px] grid-cols-1 gap-12 px-5 sm:px-8 lg:grid-cols-[13rem_minmax(0,1fr)]">
        <aside className="hidden lg:block">
          <SectionNav groups={ex.groups} />
        </aside>
        <div>
          {ex.groups.flatMap((g) => g.sections).map((s) => (
            <SectionView key={s.id} section={s} commit={ex.commit} />
          ))}
        </div>
      </div>
    </>
  );
}

function SectionView({ section, commit }: { section: Section; commit?: string }) {
  const { Body } = section;
  return (
    <section id={section.id} className="scroll-mt-20 border-b border-line py-14 last:border-b-0">
      <h2 className="text-2xl font-semibold tracking-tight">{section.title}</h2>
      <p className="mt-2 max-w-2xl text-fg-muted">{section.summary}</p>
      {commit && section.code && (
        <p className="mt-3 flex max-w-4xl flex-wrap items-baseline gap-x-3 gap-y-1 text-xs text-fg-muted">
          <span>Code</span>
          {section.code.map((l) => (
            <a key={l.label} href={codeUrl(commit, l)} target="_blank" rel="noopener noreferrer" className="font-mono text-fg underline decoration-line-strong underline-offset-2 hover:decoration-fg">
              {l.label}
            </a>
          ))}
        </p>
      )}
      {Body ? (
        <Body />
      ) : (
        <div className="mt-6 grid h-28 place-items-center rounded-card border border-dashed border-line-strong text-sm text-fg-muted">
          The visualization for this is still to come.
        </div>
      )}
    </section>
  );
}

import ArchitectureDiagram from "./ArchitectureDiagram";

/*
  The first screen: the name, and the architecture filling the rest of the viewport. Nothing else.
  The height is the viewport's less the nav (56px); the diagram scales to fit what is left under the title.
*/
export default function Hero() {
  return (
    <section id="top" className="relative flex h-[calc(100svh-56px)] min-h-[560px] flex-col overflow-hidden border-b border-line">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(to right, var(--line) 1px, transparent 1px), linear-gradient(to bottom, var(--line) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(ellipse 80% 70% at 50% 40%, black 10%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(ellipse 80% 70% at 50% 40%, black 10%, transparent 80%)",
          opacity: 0.45,
        }}
      />
      <div className="relative mx-auto flex w-full max-w-[1800px] flex-1 min-h-0 flex-col px-5 pb-4 pt-5 sm:px-8">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Neo4j ContextEngine</h1>
        <div id="architecture" className="mt-2 min-h-0 flex-1">
          <ArchitectureDiagram />
        </div>
      </div>
    </section>
  );
}

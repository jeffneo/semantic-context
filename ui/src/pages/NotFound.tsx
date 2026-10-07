import { Link } from "react-router";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-[1800px] px-5 py-24 sm:px-8">
      <h1 className="text-3xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-3 text-fg-muted">There is nothing at this address.</p>
      <Link to="/" className="mt-6 inline-block text-link hover:underline">
        Back to the start
      </Link>
    </section>
  );
}

import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";
import Hero from "./components/Hero";
import Nav from "./components/Nav";
import { EXAMPLE_LIST } from "./examples";
import ExamplePage from "./pages/ExamplePage";
import NotFound from "./pages/NotFound";

/** A new page starts at the top; a link with a #section is left to the page, which scrolls to it. */
function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname, hash]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Hero />} />
          {/* one example for now; this becomes a list when there are more */}
          <Route path="/examples" element={<Navigate to={`/examples/${EXAMPLE_LIST[0].slug}`} replace />} />
          <Route path="/examples/:slug" element={<ExamplePage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </>
  );
}

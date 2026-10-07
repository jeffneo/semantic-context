import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// A static build: dist/ is plain files. Pages have real paths (/examples/fennmoor), so the app is served from the root of a site and the host
// sends unknown paths to index.html (vercel.json does it for Vercel; `vite` and `vite preview` do it already).
export default defineConfig({
  base: "/",
  // Only these prefixes reach the browser. A bare NEO4J_ would also expose NEO4J_PASSWORD from the environment, so the prefix names the one setting.
  envPrefix: ["VITE_", "NEO4J_CONTACT_"],
  plugins: [react(), tailwindcss()],
});

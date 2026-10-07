import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// A static build: `base: "./"` lets the dist folder be served from any path (a bucket, a Pages site, a subpath).
export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
});

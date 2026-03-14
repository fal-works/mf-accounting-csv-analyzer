import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "dist/browser",
    emptyOutDir: true,
    rollupOptions: {
      input: "csv-importer.html",
    },
  },
});

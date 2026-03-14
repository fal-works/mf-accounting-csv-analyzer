import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["gui/client/**/*.test.ts", "gui/server/**/*.test.ts"],
  },
});

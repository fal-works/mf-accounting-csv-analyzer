import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["gui/**/*.test.ts"],
  },
});

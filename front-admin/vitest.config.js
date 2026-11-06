import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  test: {
    globals: true,
    environment: "happy-dom",
    include: [
      "src/views/product/__tests__/**/*.test.{js,ts}",
      "src/components/__tests__/**/*.test.{js,ts}",
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/views/product/**/*.{js,ts,vue}", "src/components/**/*.{js,ts,vue}"],
      exclude: ["src/**/__tests__/**"],
    },
  },
});

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90000,
  expect: { timeout: 7000 },
  fullyParallel: false,
  workers: 1, // ← 1 worker para evitar conflictos con la DB
  retries: 0, // ← Sin reintentos para no confundir el conteo
  outputDir: "reports/playwright-output",
  reporter: [
    ["list"],
    ["json", { outputFile: "reports/results.json" }],
    ["junit", { outputFile: "reports/results.xml" }],
  ],
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:5173",
    actionTimeout: 15000,
    navigationTimeout: 20000,
    trace: "off",
    screenshot: "off",
    video: "off",
    headless: true,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
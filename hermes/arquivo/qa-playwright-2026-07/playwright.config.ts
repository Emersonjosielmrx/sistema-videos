import { defineConfig, devices } from "@playwright/test";
import { BASE_URL } from "./config.js";

export default defineConfig({
  testDir: "./tests",
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,   // 1 conta trial de cada vez (rate-limit no cadastro)
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    ["html", { outputFolder: "reports/html", open: "never" }],
    ["json", { outputFile: "reports/result.json" }],
  ],
  use: {
    baseURL: BASE_URL,
    headless: true,
    viewport: { width: 1440, height: 900 },
    screenshot: "on",
    trace: "retain-on-failure",
    video: "off",
    locale: "pt-BR",
  },
  // channel "chrome" usa o Google Chrome instalado no sistema (evita baixar o build do PW).
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], channel: "chrome" } }],
});

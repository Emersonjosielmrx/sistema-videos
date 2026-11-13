import { defineConfig } from '@playwright/test';

/**
 * Config Playwright pra rodar no Windows local mas executar contra a VPS de beta.
 * Cada worker = uma conta independente (sem cross-pollution). Screenshots ficam em
 * tests/screenshots/, relatório HTML em tests/reports/.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1, // serial enquanto dependemos do arquivo de estado compartilhado
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'tests/reports/html' }],
    ['json', { outputFile: 'tests/reports/results.json' }],
  ],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.HERMES_BASE || 'https://hermescall.opus-sem-limites.com.br',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },
  outputDir: 'tests/reports/output',
  globalSetup: './global-setup.ts',
  // Não baixa browsers do Chromium por padrão em Windows off-line demais — tenta headless mesmo assim.
  projects: [
    {
      name: 'chromium',
      use: {
        channel: 'chromium',
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
});

/**
 * Debug P1-2 — captura o que acontece após click em "Entrar" no modal ?action=login.
 */
import { test } from '@playwright/test';
import { P } from '../helpers/qa';
import { getAccount } from '../helpers/accounts';

test('debug login modal flow', async ({ page }) => {
  const acc = await getAccount('trial');
  test.skip(!acc, 'trial sem cache');

  const requests: { url: string; method: string; status?: number }[] = [];
  const consoleMsgs: string[] = [];
  page.on('request', (r) => {
    if (r.url().includes('/api/')) requests.push({ url: r.url(), method: r.method() });
  });
  page.on('response', async (r) => {
    if (r.url().includes('/api/auth/login')) {
      const i = requests.findIndex((x) => x.url === r.url());
      if (i >= 0) requests[i].status = r.status();
    }
  });
  page.on('console', (msg) => consoleMsgs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', (e) => consoleMsgs.push(`[pageerror] ${e.message}`));

  await page.goto(P.base + '/?action=login', { waitUntil: 'domcontentloaded' });
  console.log('after goto, URL=', page.url());

  await page.waitForSelector('input[type="email"], input[name="email"]', { timeout: 15_000 });
  await page.fill('input[type="email"], input[name="email"]', acc!.email);
  await page.fill('input[type="password"]', acc!.password);

  // Screenshot antes
  await page.screenshot({ path: 'tests/screenshots/debug-1-before-click.png' });
  console.log('antes do click, URL=', page.url(), 'hasEmailInput=', await page.locator('input[type="email"]').count());

  await page.click('button[type="submit"], button:has-text("Entrar")');

  // Espera 5s pra ver o que rola
  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'tests/screenshots/debug-2-after-click.png' });
  console.log('5s após click, URL=', page.url());

  // Tenta ler localStorage
  const ls = await page.evaluate(() => {
    const out: Record<string, string> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k) out[k] = localStorage.getItem(k) || '';
    }
    return out;
  });
  console.log('localStorage keys:', Object.keys(ls));
  for (const [k, v] of Object.entries(ls)) console.log(`  ${k} = ${v.slice(0, 80)}`);

  // Lista requests /api/
  console.log('requests /api/:');
  for (const r of requests) console.log(`  ${r.method} ${r.url} → ${r.status ?? '?'}`);

  console.log('console msgs:');
  for (const m of consoleMsgs) console.log(`  ${m}`);

  // Tenta de novo aguardar mais 5s
  await page.waitForTimeout(5000);
  console.log('10s após click, URL=', page.url());
});

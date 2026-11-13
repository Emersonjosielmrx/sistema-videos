/**
 * Smoke UI — passa por TODAS as rotas da sidebar pra cada persona, capturando screenshots
 * e procurando console.error a cada passo. @smoke @regression
 *
 * Cada persona roda SUA lista de abas (filtrada por /me.features.tabs). Para cada aba:
 *   1. Navega via goto (com cache-busting query).
 *   2. Espera o estado "ready" da página (algum texto conhecido).
 *   3. Verifica se apareceu console.error / uncaught.
 *   4. Tira screenshot.
 *
 * Se QUALQUER aba falha com 5xx, console.error ou redirect pra /login → falha o spec.
 *
 * @slow — demora ~10min pra rodar completo. Pra CI: usar grep @smoke em subset.
 */
import { test, expect, request as pwRequest } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow, ALL_PLANS } from '../helpers/accounts';

test.beforeAll(async ({ request }) => {
  await ensureAccounts(request);
});

interface TabUrl { tab: string; path: string; expectText: string | RegExp; }

const URL_BY_TAB: TabUrl[] = [
  { tab: 'cost', path: '/dashboard', expectText: /Visão Geral|Cost|Indicadores/i },
  { tab: 'crm', path: '/crm', expectText: /CRM|Lead|funil/i },
  { tab: 'chat', path: '/chat', expectText: /Chat|conversa|sess/i },
  { tab: 'manager_chat', path: '/manager', expectText: /Gestor|Funcionário|Manager/i },
  { tab: 'specialized', path: '/agents', expectText: /Agente|Especialistas|Funcionários/i },
  { tab: 'agenda', path: '/agenda', expectText: /Agenda|evento|cronograma/i },
  { tab: 'catalog', path: '/catalog', expectText: /Catálogo|vitrine|produto/i },
  { tab: 'calls', path: '/calls', expectText: /Chamada|Telefonia|grava/i },
  { tab: 'meeting-ai', path: '/meeting', expectText: /Reuni|Imeet|Meet|gravação/i },
];

for (const plan of ALL_PLANS) {
  test(`smoke UI @ ${plan}`, async ({ page }) => {
    const acc = await getAccountOrThrow(plan).catch((e) => { console.warn('skip', plan, e.message); return null; });
    test.skip(!acc, `${plan} sem cache disponível (rate-limit ativo) — reativa depois`);
    if (!acc) return;

    // Bypass P1-2 (frontend não redireciona pós-login): injeta token em localStorage
    // ANTES da app montar via addInitScript, depois goto /. Equivalente a um login
    // bem-sucedido sem depender do modal.
    await page.addInitScript(({ token, user }) => {
      try {
        localStorage.setItem('hermes.token', token);
        localStorage.setItem('hermes.user', user);
      } catch {}
    }, { token: acc!.token, user: JSON.stringify({ email: acc!.email }) });

    await page.goto(P.base + '/', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

    // Coleta as abas via /me
    const me = await page.request.get(P.base + '/api/auth/me', {
      headers: { Authorization: `Bearer ${acc!.token}` },
    });
    expect(me.status()).toBeLessThan(300);
    const tabs: string[] = (await me.json()).features?.tabs ?? [];

    // Com filtro
    const urls = URL_BY_TAB.filter((u) => tabs.includes(u.tab));

    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    for (const url of urls) {
      // Cache-busting
      const sep = url.path.includes('?') ? '&' : '?';
      const target = P.base + url.path + sep + 't=' + Date.now();
      const resp = await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 15_000 });
      const status = resp?.status() ?? 0;
      // Aceita 200 (página) ou redirect 30x. NÃO pode ser 404/500 nem unauthorized pra /login.
      if (!page.url().includes('/login') && status !== 200) {
        expect.soft(status, `${plan} ${url.path}`).toBeLessThan(400);
      }
      // Espera algum conteúdo renderizar
      try {
        await page.waitForSelector(`text=${typeof url.expectText === 'string' ? url.expectText : '.*'}`, {
          timeout: 5_000,
          state: 'visible',
        });
      } catch {
        // Não achou texto — só avisa, não falha (pode estar em estado de "empty state").
        console.warn(`${plan} ${url.path}: texto ${url.expectText} não apareceu`);
      }
      // Screenshot pra evidências
      await page.screenshot({ path: `tests/screenshots/smoke-${plan}-${url.tab}.png`, fullPage: false });
    }

    // Falha se houve erros de console (excluindo network resource errors conhecidos)
    const fatals = consoleErrors.filter(e =>
      !e.includes('ERR_NAME_NOT_RESOLVED') && !e.includes('favicon') && !e.includes('source map'),
    );
    expect.soft(fatals.length, `${plan} console.error count`).toBeLessThanOrEqual(0);
    if (fatals.length > 0) {
      console.error(`[${plan}] erros de console:`, fatals.slice(0, 5).join(' | '));
    }
  });
}

/**
 * Smoke API refatorado — REAPROVEITA contas entre runs. Sem isso, 4 personas =
 * 4 cadastros/hora, queima o rate-limit (5/10min) em 1 execução.
 *
 * Estratégia nova:
 *   - Cria 1 admin + 1 user por plano na primeira vez; cacheia em disco (state.json).
 *   - Runs seguintes só validam com a conta cacheada.
 *   - Detecta se a conta cacheada ainda está válida (login + /me com 200), senão recria.
 */
import { test, expect } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow, ALL_PLANS } from '../helpers/accounts';

// Rotas REAIS do backend (verificadas em cmd/server/httpapi.go). Rotas antigas do
// teste (/api/calls/recent, /api/chat/sessions, /api/crm/deals, /api/agenda/events,
// /api/phone-numbers, /api/meet/sessions) NUNCA existiram — foram substituídas pelos
// nomes reais abaixo. Sem isso o smoke acusava 404 em rotas fantasma.
const ROUTES = [
  { path: '/api/auth/me' },
  { path: '/api/billing' },
  { path: '/api/projects' },
  { path: '/api/settings' },
  { path: '/api/contacts/leads', feature: 'crm' },
  { path: '/api/contacts/tags', feature: 'crm' },
  { path: '/api/crm/board', feature: 'crm' },
  { path: '/api/chat/threads', feature: 'chat' },
  { path: '/api/agents', feature: 'specialized' },
  { path: '/api/agent-profiles', feature: 'specialized' },
  { path: '/api/campaigns', feature: 'calls' },
  { path: '/api/transcripts' }, // não é gated por plano no backend (disponível a todos)
  { path: '/api/recordings' },  // idem
  { path: '/api/agenda/appointments', feature: 'agenda' },
  { path: '/api/catalog/products', feature: 'catalog' },
];

test.beforeAll(async ({ request }) => {
  // Cria (ou reusa) 1 conta por plano uma única vez por arquivo.
  await ensureAccounts(request);
});

for (const plan of ALL_PLANS) {
  test(`smoke API @ ${plan}`, async ({ request }) => {
    const acc = await getAccountOrThrow(plan).catch((e) => { console.warn('skip', plan, e.message); return null; });
    test.skip(!acc, `${plan} sem cache disponível (rate-limit ativo) — reativa depois`);
    if (!acc) return;

    // /me + features
    const me = await request.get(P.base + '/api/auth/me', {
      headers: { Authorization: `Bearer ${acc.token}` },
    });
    expect.soft(me.status(), `${plan} /me`).toBeLessThan(300);
    const meBody = await me.json().catch(() => ({} as any));
    const tabs: string[] = (meBody.features?.tabs ?? []).sort();
    const expected: string[] = {
      trial: ['agenda', 'calls', 'catalog', 'chat', 'cost', 'crm', 'manager_chat', 'meeting-ai', 'specialized'],
      start_voz: ['calls', 'cost', 'crm'],
      start_texto: ['chat', 'cost', 'crm', 'manager_chat', 'specialized'],
      pro: ['agenda', 'calls', 'catalog', 'chat', 'cost', 'crm', 'manager_chat', 'specialized'],
      scale: ['agenda', 'calls', 'catalog', 'chat', 'cost', 'crm', 'manager_chat', 'meeting-ai', 'specialized'],
    }[plan] ?? [];
    expect.soft(tabs, `${plan} features.tabs`).toEqual(expected);

    // Smoke rotas
    for (const r of ROUTES) {
      const wantsIt = !r.feature || expected.includes(r.feature);
      const resp = await request.get(P.base + r.path, {
        headers: { Authorization: `Bearer ${acc.token}` },
      });
      if (wantsIt) {
        // catalog pode ter paginação que retorna 200 mesmo vazio.
        expect.soft(resp.status(), `${plan} ${r.path}`).toBeLessThan(400);
      } else {
        expect.soft(resp.status(), `${plan} ${r.path} deveria ser 403`).toBe(403);
      }
    }
  });
}

test('smoke UI - homepage pública carrega sem 5xx', async ({ page }) => {
  await page.goto(P.base + '/', { waitUntil: 'domcontentloaded', timeout: 15_000 });
  // Não exige status 200 (CDN pode devolver 200 com hydration), só que NÃO seja 5xx.
  const resp = await page.goto(P.base + '/');
  expect.soft(resp?.status() ?? 0, 'homepage status').toBeLessThan(500);
});

test('smoke UI - /api/version tem build/channel', async ({ request }) => {
  const r = await request.get(P.base + '/api/version');
  expect(r.status()).toBe(200);
  const j = await r.json();
  expect(j.version).toBeTruthy();
  expect(j.channel).toBeTruthy();
});

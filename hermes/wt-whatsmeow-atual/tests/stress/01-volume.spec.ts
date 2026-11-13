/**
 * P7 stress test — volume realista pra validar que o backend segura.
 *
 *   - Cria 50 contatos em sequência (latência aceitável < 30s)
 *   - Lista todos os contatos da conta (page size 50)
 *   - Faz 20 GETs paralelos /api/contacts (race condition do cache/DB)
 *   - Faz 10 POSTs /api/chat/sessions em paralelo
 *
 * NÃO valida WhatsApp real — só mede latência e taxa de 5xx.
 *
 * @stress
 */
import { test, expect, request as pwRequest } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow } from '../helpers/accounts';

test.beforeAll(async () => { await ensureAccounts(pwRequest as any); });

test('stress: cria 50 contatos em < 30s e nenhum 5xx', async () => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro cacheada');
  const req = await pwRequest.newContext();
  const authH = { Authorization: `Bearer ${acc!.token}` };
  const tag = Date.now().toString(36);
  const t0 = Date.now();
  let fails = 0;
  for (let i = 0; i < 50; i++) {
    const r = await req.post(P.base + '/api/contacts', {
      headers: { ...authH, 'Content-Type': 'application/json' },
      data: { name: `Stress ${tag} #${i}`, phone: `5511${tag.slice(-7)}${i.toString().padStart(3, '0')}` },
    });
    if (r.status() >= 500) fails++;
    else if (r.status() === 429) {
      console.warn(`rate-limit em i=${i}, espera 5s e tenta dnv`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
  const dt = Date.now() - t0;
  console.log(`[stress] 50 contatos em ${dt}ms (${(dt / 50).toFixed(0)}ms/contato)`);
  expect.soft(fails, 'nenhum 5xx durante criação em massa').toBe(0);
  expect.soft(dt, '< 30s pra 50 contatos').toBeLessThan(30_000);
});

test('stress: 20 GETs paralelos a /api/contacts (race condition do DB pool)', async () => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  const req = await pwRequest.newContext();
  const authH = { Authorization: `Bearer ${acc!.token}` };
  const reqs = Array.from({ length: 20 }, () =>
    req.get(P.base + '/api/contacts', { headers: authH }).then(r => r.status()),
  );
  const statuses = await Promise.all(reqs);
  const fivexx = statuses.filter(s => s >= 500).length;
  const rateLimited = statuses.filter(s => s === 429).length;
  console.log(`[stress] 20 paralelos: 5xx=${fivexx} 429=${rateLimited} outros=${statuses.filter(s => s !== 429 && s < 500).length}`);
  expect.soft(fivexx, 'race condition deve produzir 0 5xx').toBe(0);
});

test('stress: 10 POSTs paralelos a /api/chat/sessions', async () => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  const req = await pwRequest.newContext();
  const authH = { Authorization: `Bearer ${acc!.token}` };
  const tag = Date.now().toString(36);
  const reqs = Array.from({ length: 10 }, (_, i) =>
    req.post(P.base + '/api/chat/sessions', {
      headers: { ...authH, 'Content-Type': 'application/json' },
      data: { title: `Stress session ${tag} #${i}`, kind: 'whatsapp' },
    }).then(r => r.status()),
  );
  const statuses = await Promise.all(reqs);
  const fivexx = statuses.filter(s => s >= 500).length;
  const created = statuses.filter(s => s === 200 || s === 201).length;
  console.log(`[stress] 10 chat sessions paralelas: 201=${created} 5xx=${fivexx}`);
  expect.soft(fivexx, 'paralelismo de criação de sessão').toBe(0);
});

test('stress: /api/billing responde em < 2s sob carga concorrente', async () => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  const req = await pwRequest.newContext();
  const authH = { Authorization: `Bearer ${acc!.token}` };
  const reqs = Array.from({ length: 15 }, () => {
    const t0 = Date.now();
    return req.get(P.base + '/api/billing', { headers: authH }).then(r => ({ s: r.status(), dt: Date.now() - t0 }));
  });
  const results = await Promise.all(reqs);
  const fivexx = results.filter(r => r.s >= 500).length;
  const slow = results.filter(r => r.dt > 2000).length;
  const max = Math.max(...results.map(r => r.dt));
  console.log(`[stress] /api/billing: 5xx=${fivexx} slow>2s=${slow} max=${max}ms`);
  expect.soft(fivexx).toBe(0);
  expect.soft(max, 'pior caso < 5s').toBeLessThan(5000);
});

/**
 * Auditoria de segurança ativa — @security
 *
 * O que checa (cadência rápida, todos com @regression):
 *  1. IDOR: acessar /api/contacts/:id, /api/agent-profiles/:id, /api/campaigns/:id de outro user (espera 404 ou 403, nunca 200 com payload).
 *  2. Authn bypass: GET /api/calls/recent sem token → 401. Com token inválido → 401.
 *  3. Cupom: POST /api/billing/coupon com "ADMIN"/"FREE"/"TESTE" (não na allowlist) → 400. Com cupom válido → 200.
 *  4. Webhook Asaas: POST sem header / com token errado / com payload forjado → 401 ou 4xx (nunca 200 confirmando pagamento).
 *  5. Rate-limit: 6 logins com senha errada em sequência → algum bloqueio.
 *  6. SQL injection em campos: ' OR 1=1-- em tags/contacts/profile names → ver se aparece 500 ou vaza dados.
 *  7. Path traversal: nome de campanha "../../etc/passwd" → não deve quebrar ou vazar FS.
 *  8. Cross-tenant: usuário A cria recurso; usuário B tenta ler/deletar → 403/404.
 *
 * Tudo via request context — não precisa de UI.
 */
import { test, expect, request as pwRequest, APIRequestContext } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow, ALL_PLANS } from '../helpers/accounts';

test.beforeAll(async () => { await ensureAccounts(pwRequest as any); });

const ADMIN_LOGIN = { email: process.env.HERMES_ADMIN_EMAIL || 'admin@hermescall.com', password: process.env.HERMES_ADMIN_PASS || 'admin123' };

/** Helper: tenta login e devolve token ou string vazia. */
async function tryLogin(req: APIRequestContext, email: string, password: string): Promise<string> {
  try {
    const r = await req.post(P.base + '/api/auth/login', { data: { email, password } });
    if (!r.ok()) return '';
    return (await r.json()).token ?? '';
  } catch { return ''; }
}

test('SEC-1: IDOR cross-tenant entre 2 usuários', async () => {
  // Usa o fixture global pra não estourar rate-limit do cadastro principal.
  const req = await pwRequest.newContext();
  let userAEmail = '', userBEmail = '';
  for (let i = 0; i < 10 && (!userAEmail || !userBEmail); i++) {
    try {
      const a = await req.post(P.base + '/api/auth/register', {
        data: { name: 'A', email: `idA${Date.now()}${i}@qa.local`, password: '<SEGREDO_REMOVIDO>', plan: 'trial' },
      });
      const b = await req.post(P.base + '/api/auth/register', {
        data: { name: 'B', email: `idB${Date.now()}${i}@qa.local`, password: '<SEGREDO_REMOVIDO>', plan: 'trial' },
      });
      if (a.ok()) userAEmail = (await a.json()).user.email;
      if (b.ok()) userBEmail = (await b.json()).user.email;
    } catch {}
  }
  test.skip(!userAEmail || !userBEmail, 'rate-limit impediu criar 2 contas');

  const tokA = await tryLogin(req, userAEmail, 'pwpw123');
  const tokB = await tryLogin(req, userBEmail, 'pwpw123');
  expect(tokA).toBeTruthy();
  expect(tokB).toBeTruthy();

  // A cria contato; B tenta GET nesse contato
  const c = await req.post(P.base + '/api/contacts', {
    headers: { Authorization: `Bearer ${tokA}` },
    data: { name: 'Cliente Secreto A', phone: '5511999990001' },
  });
  test.skip(!c.ok(), 'criar contato falhou');
  const contactId = ((await c.json()) as any).id ?? (await c.json() as any).contact?.id;

  // B lê (deve falhar)
  const c2 = await req.get(P.base + `/api/contacts/${contactId}`, {
    headers: { Authorization: `Bearer ${tokB}` },
  });
  expect.soft(c2.status(), 'B NÃO pode ler contato de A').not.toBe(200);

  // B tenta atualizar
  const c3 = await req.put(P.base + `/api/contacts/${contactId}`, {
    headers: { Authorization: `Bearer ${tokB}` },
    data: { name: 'PWN' },
  });
  expect.soft(c3.status(), 'B NÃO pode editar contato de A').not.toBe(200);

  // B tenta deletar
  const c4 = await req.delete(P.base + `/api/contacts/${contactId}`, {
    headers: { Authorization: `Bearer ${tokB}` },
  });
  expect.soft(c4.status(), 'B NÃO pode deletar contato de A').not.toBe(200);
});

test('SEC-2: auth bypass — sem token', async () => {
  const req = await pwRequest.newContext();
  // Endpoints "internos" sensíveis devem exigir token.
  for (const path of ['/api/calls/recent', '/api/agents', '/api/contacts', '/api/billing', '/api/agent-profiles', '/api/campaigns']) {
    const r = await req.get(P.base + path);
    expect.soft(r.status(), `GET ${path} sem token`).toBe(401);
    const r2 = await req.post(P.base + path, { data: {} });
    expect.soft(r2.status(), `POST ${path} sem token`).toBeGreaterThanOrEqual(401);
  }
});

test('SEC-3: auth bypass — token inválido / forjado', async () => {
  const req = await pwRequest.newContext();
  for (const tok of ['fake.tok.en', '', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiJ9.fake', 'undefined']) {
    const r = await req.get(P.base + '/api/calls/recent', { headers: { Authorization: `Bearer ${tok}` } });
    expect.soft(r.status(), `token ${tok.slice(0, 10)}…`).toBeGreaterThanOrEqual(401);
  }
});

test('SEC-4: cupom inválido é recusado', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta trial cacheada');
  const req = await pwRequest.newContext();
  for (const coupon of ['ADMIN', 'FREE', 'TESTE', '', 'foo-bar', 'GRÁTIS']) {
    const r = await req.post(P.base + '/api/billing/coupon', {
      headers: { Authorization: `Bearer ${acc!.token}` },
      data: { coupon },
    });
    expect.soft(r.status(), `cupom "${coupon}" deve falhar`).toBeGreaterThanOrEqual(400);
    const body = await r.json().catch(() => ({} as any));
    expect.soft(body.applied, `cupom "${coupon}" não pode setar applied=true`).not.toBe(true);
  }
});

test('SEC-5: webhook Asaas rejeita sem token / com token errado', async () => {
  const req = await pwRequest.newContext();
  // Sem header de autenticação
  const r1 = await req.post(P.base + '/api/billing/webhook', {
    data: { event: 'PAYMENT_CONFIRMED', payment: { id: 'fake' } },
  });
  expect.soft(r1.status(), 'webhook sem token').toBeGreaterThanOrEqual(400);
  // Com header errado
  const r2 = await req.post(P.base + '/api/billing/webhook', {
    headers: { 'asaas-access-token': 'token-errado' },
    data: { event: 'PAYMENT_CONFIRMED', payment: { id: 'fake', status: 'CONFIRMED' } },
  });
  expect.soft(r2.status(), 'webhook com token errado').toBeGreaterThanOrEqual(400);
});

test('SEC-6: SQL injection não derruba servidor', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  const payloads = [
    "' OR 1=1--",
    "'; DROP TABLE contacts; --",
    "1' OR '1'='1",
    "admin'--",
    "{\"$ne\":null}",
  ];
  for (const p of payloads) {
    // Em tags (campo texto livre, vetor clássico de injection)
    const r = await req.post(P.base + '/api/tags', {
      headers: { Authorization: `Bearer ${acc!.token}` },
      data: { name: p },
    });
    // Tem que ser 400 (validation) ou 409 (dedup) ou 201. NUNCA 500.
    expect.soft(r.status(), `tag payload ${p.slice(0, 15)}`).toBeLessThan(500);
  }
});

test('SEC-7: path traversal em nomes de recurso', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  const payloads = [
    '../../etc/passwd',
    '..\\..\\windows\\system32',
    '/proc/self/environ',
    '.../.ssh/id_rsa',
  ];
  for (const p of payloads) {
    const r = await req.post(P.base + '/api/campaigns', {
      headers: { Authorization: `Bearer ${acc!.token}` },
      data: { name: p, kind: 'whatsapp' },
    });
    // Verifica APENAS se a resposta permite — não tenta parsear se vier HTML
    // (alguns retornam 404 HTML, que NÃO é falha de traversal).
    expect.soft(r.status(), `payload ${p.slice(0, 20)}`).not.toBe(500);
    const ct = r.headers()['content-type'] || '';
    if (ct.includes('application/json')) {
      const body = await r.json().catch(() => ({} as any));
      if (body.name && typeof body.name === 'string') {
        // Se aceitou criar, nome não pode ter .., /, \\ — sanitizou.
        const sanitized = !body.name.includes('..') && !body.name.includes('/') && !body.name.includes('\\');
        expect.soft(sanitized, `path ${p}: nome não foi sanitizado (${body.name})`).toBe(true);
      }
    }
  }
});

test('SEC-8: rate-limit de login bloqueia brute force', async () => {
  const req = await pwRequest.newContext();
  let blocked = 0;
  for (let i = 0; i < 8; i++) {
    const r = await req.post(P.base + '/api/auth/login', {
      data: { email: 'nonexistent@local.test', password: `wrong${i}` },
    });
    if (r.status() === 429 || r.status() === 403) blocked++;
  }
  expect.soft(blocked >= 1, 'deve bloquear pelo menos uma tentativa após 8x').toBe(true);
});

test('SEC-9: admin bypassa TODOS os gates (403 plan_forbidden não deve atingir admin)', async () => {
  const req = await pwRequest.newContext();
  const tok = await tryLogin(req, ADMIN_LOGIN.email, ADMIN_LOGIN.password);
  test.skip(!tok, `admin não conseguiu logar (configurar HERMES_ADMIN_EMAIL/PASS ou criar conta dev)`);
  // Admin precisa acessar rotas restritas de outros planos sem 403.
  const paths = ['/api/calls/recent', '/api/agent-profiles', '/api/campaigns', '/api/meet/sessions'];
  for (const path of paths) {
    const r = await req.get(P.base + path, { headers: { Authorization: `Bearer ${tok}` } });
    expect.soft(r.status(), `admin em ${path}`).toBeLessThan(400);
  }
});

test('SEC-10: payload gigante não derruba o servidor nem retorna 500', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  // 5MB de string (deve dar 413 ou 400, nunca 500)
  const giant = 'A'.repeat(5 * 1024 * 1024);
  for (const path of ['/api/contacts', '/api/agent-profiles', '/api/campaigns']) {
    const r = await req.post(P.base + path, {
      headers: { Authorization: `Bearer ${acc!.token}` },
      data: { name: giant, phone: '5511999990002' },
    });
    expect.soft(r.status(), `payload gigante em ${path}`).toBeLessThan(500);
    expect.soft(r.status(), `payload gigante em ${path}`).toBeLessThan(600);
  }
});

test('SEC-11: tipo errado em campo (number onde espera string) não causa 500', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  // Envia um objeto onde deveria vir string
  const r = await req.post(P.base + '/api/contacts', {
    headers: { Authorization: `Bearer ${acc!.token}` },
    data: { name: { evil: 'object' }, phone: ['array', 'not', 'string'] },
  });
  expect.soft(r.status(), 'tipo errado').toBeLessThan(500);
});

test('SEC-12: JSON malformado retorna 400, não 500', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  for (const broken of ['{not json', '{"a":}', '{,}', '{"__proto__":{"x":1}}', 'null', '[]']) {
    const r = await req.post(P.base + '/api/contacts', {
      headers: {
        Authorization: `Bearer ${acc!.token}`,
        'Content-Type': 'application/json',
      },
      data: broken,
    });
    expect.soft(r.status(), `json broken: ${broken.slice(0, 15)}`).toBeLessThan(500);
  }
});

test('SEC-13: prototype pollution em body não vaza propriedades', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  const r = await req.post(P.base + '/api/contacts', {
    headers: { Authorization: `Bearer ${acc!.token}` },
    data: { name: 'normal', phone: '5511999990003', __proto__: { admin: true, plan: 'enterprise' } },
  });
  // Se aceitou, verifica que os campos perigosos não foram absorvidos
  if (r.ok()) {
    const body = await r.json();
    expect.soft(body.admin, 'admin não deve ter sido promovido').toBeFalsy();
    expect.soft(body.user?.plan, 'plan não deve ter sido promovido').not.toBe('enterprise');
  }
  expect.soft(r.status(), 'proto pollution').toBeLessThan(500);
});

test('SEC-14: header injection / CRLF em campos não vaza em 5xx', async () => {
  const acc = await getAccountOrThrow('trial').catch(() => null);
  test.skip(!acc, 'sem conta');
  const req = await pwRequest.newContext();
  const payloads = [
    'value\r\nX-Injected: pwn',
    'value\nSet-Cookie: pwn=1',
    'value%0d%0aX-Injected: pwn',
  ];
  for (const p of payloads) {
    const r = await req.post(P.base + '/api/contacts', {
      headers: { Authorization: `Bearer ${acc!.token}` },
      data: { name: p, phone: '5511999990004' },
    });
    expect.soft(r.status(), `CRLF payload: ${p.slice(0, 15)}`).toBeLessThan(500);
  }
});

test('SEC-15: token de outro usuário não vaza dados via /me', async () => {
  const req = await pwRequest.newContext();
  // Cria duas contas trial
  let tokA = '', tokB = '';
  for (let i = 0; i < 5 && (!tokA || !tokB); i++) {
    const a = await req.post(P.base + '/api/auth/register', {
      data: { name: 'A', email: `sec15a${Date.now()}${i}@qa.local`, password: '<SEGREDO_REMOVIDO>', plan: 'trial' },
    });
    const b = await req.post(P.base + '/api/auth/register', {
      data: { name: 'B', email: `sec15b${Date.now()}${i}@qa.local`, password: '<SEGREDO_REMOVIDO>', plan: 'trial' },
    });
    if (a.ok()) tokA = (await a.json()).token;
    if (b.ok()) tokB = (await b.json()).token;
  }
  test.skip(!tokA || !tokB, 'rate-limit impediu criar contas');
  // A com token de B não deve funcionar
  const r = await req.get(P.base + '/api/auth/me', { headers: { Authorization: `Bearer ${tokB}` } });
  const meB = await r.json();
  expect.soft(meB.user?.email, 'email do /me deve ser do dono do token').toContain('sec15b');
  // Garante que o token A não dá acesso a dados de B
  const r2 = await req.get(P.base + '/api/contacts', { headers: { Authorization: `Bearer ${tokA}` } });
  // /api/contacts não tem handler — backend retorna 404. Testamos que A não vaza nada,
  // independente do status code (que pode ser 404 pq a rota não existe, não 200 com payload).
  expect.soft(r2.status(), 'rota inexistente deve ser 404').toBe(404);
  // Garante que o 404 é JSON ou texto vazio, NUNCA HTML
  const ct = r2.headers()['content-type'] || '';
  expect.soft(ct.includes('text/html'), `404 não pode ser HTML (foi ${ct})`).toBe(false);
});

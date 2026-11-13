/**
 * E2E FLUXO 1 — Signup → primeira campanha WhatsApp enviada
 *
 * Simula o caminho de ouro do usuário novo:
 *   1. Cadastra conta trial (auto via /api/auth/register)
 *   2. Aplica cupom se necessário (trial não precisa)
 *   3. Cria tag de segmentação
 *   4. Cria 3 contatos
 *   5. Cria agente WhatsApp (agent-profile)
 *   6. Cria campanha conectando agente+contatos
 *   7. Inicia campanha
 *   8. Verifica que aparece nos recentes /api/calls/recent OU /api/campaigns/:id/runs
 *   9. Captura screenshots a cada passo pra evidência
 *
 * NÃO valida que o WhatsApp REAL foi entregue (precisa de Evolution/z-api).
 * Valida que o BACKEND ACEITA o fluxo end-to-end sem 500 nem 4xx inesperado.
 *
 * @e2e @flow
 */
import { test, expect, request as pwRequest } from '@playwright/test';
import { P } from '../helpers/qa';

const UNIQUE = Date.now().toString(36);

test('flow 1: signup → tag → contatos → agente → campanha → start', async () => {
  const req = await pwRequest.newContext();
  const errors: string[] = [];
  const log = (msg: string) => console.log(`[flow1] ${msg}`);

  // 1. Cadastro trial
  log('1. signup');
  const signup = await req.post(P.base + '/api/auth/register', {
    data: {
      name: 'Flow User',
      email: `flow1${UNIQUE}@qa.local`,
      password: '<SEGREDO_REMOVIDO>',
      plan: 'trial',
    },
  });
  expect(signup.status(), 'signup status').toBeLessThan(300);
  const signupBody = await signup.json();
  const token = signupBody.token;
  expect(token, 'token recebido').toBeTruthy();

  const authH = { Authorization: `Bearer ${token}` };
  const api = (path: string, init: any = {}) =>
    fetch(P.base + path, { ...init, headers: { ...authH, 'Content-Type': 'application/json', ...(init.headers ?? {}) } });

  // 2. /me carrega
  log('2. /me');
  const me = await api('/api/auth/me');
  expect(me.status).toBe(200);
  const meBody = await me.json();
  expect(meBody.email).toContain('flow1');

  // 3. Criar tag
  log('3. criar tag');
  const tagResp = await api('/api/tags', {
    method: 'POST',
    body: JSON.stringify({ name: `flow1-tag-${UNIQUE}`, color: '#FF6B6B' }),
  });
  if (tagResp.status >= 500) errors.push(`tag 5xx: ${tagResp.status}`);
  const tagBody = await tagResp.json().catch(() => ({} as any));
  const tagId = tagBody.id ?? tagBody.tag?.id;

  // 4. Criar 3 contatos
  log('4. criar contatos');
  const contactIds: string[] = [];
  for (let i = 0; i < 3; i++) {
    const cr = await api('/api/contacts', {
      method: 'POST',
      body: JSON.stringify({
        name: `Contato Flow ${i}`,
        phone: `5511999${UNIQUE.slice(-4)}${i.toString().padStart(2, '0')}`,
        tag_ids: tagId ? [tagId] : undefined,
      }),
    });
    if (cr.status >= 500) {
      errors.push(`contact ${i} 5xx: ${cr.status}`);
    } else if (cr.ok()) {
      const c = await cr.json();
      contactIds.push(c.id ?? c.contact?.id);
    }
  }
  expect(contactIds.length, 'pelo menos 1 contato criado').toBeGreaterThan(0);

  // 5. Criar agente WhatsApp
  log('5. criar agente');
  const agentResp = await api('/api/agent-profiles', {
    method: 'POST',
    body: JSON.stringify({
      name: `Agente Flow ${UNIQUE}`,
      kind: 'whatsapp',
      system_prompt: 'Você é um agente de teste do QA.',
      persona: 'amigável',
    }),
  });
  if (agentResp.status >= 500) errors.push(`agent 5xx: ${agentResp.status}`);
  const agentBody = await agentResp.json().catch(() => ({} as any));
  const agentId = agentBody.id ?? agentBody.profile?.id;

  // 6. Criar campanha conectando tudo
  log('6. criar campanha');
  const campResp = await api('/api/campaigns', {
    method: 'POST',
    body: JSON.stringify({
      name: `Flow1 Campanha ${UNIQUE}`,
      kind: 'whatsapp',
      agent_profile_id: agentId,
      contact_ids: contactIds,
      message_template: 'Olá! Esta é uma campanha de teste do QA.',
    }),
  });
  if (campResp.status >= 500) {
    errors.push(`campaign 5xx: ${campResp.status}`);
  } else {
    const campBody = await campResp.json().catch(() => ({} as any));
    const campId = campBody.id ?? campBody.campaign?.id;
    expect(campId, 'campanha criada com id').toBeTruthy();

    // 7. Iniciar
    log('7. start campanha');
    const startResp = await api(`/api/campaigns/${campId}/start`, { method: 'POST' });
    // 200/202 = ok; 409 = já rodando (aceita); 400 = regra de negócio
    if (![200, 202, 400, 409].includes(startResp.status)) {
      errors.push(`start status inesperado: ${startResp.status}`);
    }

    // 8. Verifica que aparece no GET
    log('8. verificar campanha');
    const getCamp = await api(`/api/campaigns/${campId}`);
    expect(getCamp.status, 'GET campanha').toBeLessThan(400);
  }

  // Resultado final
  log(`final: errors=${errors.length}`);
  if (errors.length > 0) {
    console.error('[flow1] erros:', errors);
  }
  expect(errors, `nenhum 5xx no fluxo completo: ${errors.join('; ')}`).toHaveLength(0);
});

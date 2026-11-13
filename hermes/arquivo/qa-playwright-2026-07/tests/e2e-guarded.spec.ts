// e2e-guarded.spec.ts — Etapa 6: fluxos com efeito externo bloqueado.
// Regra do dono: WhatsApp / ligacao / disparo em massa NUNCA enviam de verdade.
// Aqui provamos que o BACKEND recusa a acao sem WhatsApp pareado (o guard funciona),
// sem jamais disparar um envio real.
import { test, expect } from "@playwright/test";
import { createTrialAccount, loginAs, navTab, type Account } from "../lib/session.js";
import { apiGet, apiPost, pickArray } from "../lib/backend.js";

let account: Account;
test.beforeAll(async () => { test.setTimeout(120_000); account = await createTrialAccount(); });

test.describe("Fluxos bloqueados — guard confirmado, sem envio real", () => {
  test("conta trial nao tem WhatsApp pareado (GET /api/sessions vazio)", async ({}, info) => {
    const r = await apiGet(account, "/api/sessions");
    expect(r.ok).toBeTruthy();
    const sessions = pickArray(r.data, "sessions");
    info.annotations.push({ type: "guard", description: `sessions=${sessions.length}` });
    expect(sessions.length, "conta trial nao deveria ter linha WhatsApp").toBe(0);
  });

  test("enviar WhatsApp sem sessao e' RECUSADO pelo backend (nao envia)", async ({}, info) => {
    // Usa um sid inexistente de proposito — o backend deve recusar antes de qualquer envio.
    const r = await apiPost(account, "/api/sessions/no-session-qa/messages/text", {
      to: "550000000000", text: "TESTE-QA-NAO-ENVIAR",
    });
    info.annotations.push({ type: "guard", description: `send status=${r.status}` });
    // 404 (no such session) / 400 / 403 — qualquer recusa prova o guard. 2xx seria FALHA (enviou!).
    expect(r.ok, "envio NAO deveria ter sido aceito").toBeFalsy();
    expect([400, 403, 404, 409, 422].includes(r.status), `esperava recusa, veio ${r.status}`).toBeTruthy();
  });

  test("UI de Telefonia/Chat monta sem linha, mas sem permitir envio real", async ({ page }, info) => {
    await loginAs(page, account);
    expect(await navTab(page, "calls"), "nav calls").toBeTruthy();
    await page.waitForTimeout(1500);
    // A tela deve carregar (mostrando estado 'sem linha' ou pareamento), sem crashar.
    const shot = info.outputPath("calls.png");
    await page.screenshot({ path: shot });
    // Nao clicamos em nada que dispare ligacao/disparo — so' confirmamos que a view montou.
    const heading = await page.locator("h1,h2,h3").allInnerTexts();
    info.annotations.push({ type: "ui", description: heading.slice(0, 3).join(" | ").slice(0, 120) });
    expect(heading.length, "a view de telefonia deveria montar algo").toBeGreaterThan(0);
  });
});

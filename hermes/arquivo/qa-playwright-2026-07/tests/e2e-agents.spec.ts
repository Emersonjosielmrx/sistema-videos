// e2e-agents.spec.ts — Etapa 2: Agentes / Funcionarios IA do comeco ao fim.
// Ciclo: criar -> verificar no BACKEND (GET) -> limpar (DELETE). Nao confia so' na UI.
import { test, expect } from "@playwright/test";
import { createTrialAccount, loginAs, navTab, type Account } from "../lib/session.js";
import { apiPost, listAgents, apiDelete, pickArray, getSettings } from "../lib/backend.js";
import { tracker } from "../lib/cleanup.js";
import { verifySemantic } from "../lib/vision.js";

let account: Account;
test.beforeAll(async () => { test.setTimeout(180_000); account = await createTrialAccount(); });

test.describe("Agentes IA — criar, verificar no backend, limpar", () => {
  test("criar agente com voz -> aparece no GET /api/agent-profiles -> deletar", async ({}, info) => {
    const t = tracker(account);
    const name = "QA_Agent_" + Date.now();
    // CREATE
    const created = await apiPost(account, "/api/agent-profiles", {
      name, voice: "nova", system_prompt: "Voce e um agente de teste QA. Seja breve.",
      provider: "openai", model: "gpt-4o-mini",
    });
    expect(created.ok, `create falhou: ${JSON.stringify(created)}`).toBeTruthy();
    const id = created.data?.id;
    expect(id, "create deveria devolver id").toBeTruthy();
    t.track("agente " + name, `/api/agent-profiles/${id}`);

    // VERIFICAR NO BACKEND
    const back = await listAgents(account);
    const arr = pickArray(back.data, "profiles");
    const found = arr.find((p: any) => p.id === id || p.name === name);
    expect(found, "agente deveria aparecer no GET /api/agent-profiles").toBeTruthy();
    expect(found.name).toBe(name);
    expect(found.voice || found.tts_voice, "voz deveria ter persistido").toBe("nova");
    info.annotations.push({ type: "backend", description: `agente ${id} confirmado com voz=nova` });

    // CLEANUP
    const cleaned = await t.cleanupAll();
    info.annotations.push({ type: "cleanup", description: JSON.stringify(cleaned) });
    const back2 = await listAgents(account);
    const still = pickArray(back2.data, "profiles").find((p: any) => p.id === id);
    expect(still, "agente deveria ter sido removido").toBeFalsy();
  });

  test("preview de voz (TTS edge-tts) retorna audio_base64", async () => {
    // Prova que a sintese de voz funciona de verdade (edge-tts, gratis, sem chave).
    const r = await apiPost(account, "/api/tts/preview", { text: "Ola, este e um teste de voz.", voice: "nova" });
    expect(r.ok, `preview TTS falhou: ${r.status} ${JSON.stringify(r.data).slice(0, 120)}`).toBeTruthy();
    expect(r.data?.audio_base64, "esperava audio_base64 no preview").toBeTruthy();
    expect((r.data.audio_base64 as string).length, "audio deveria ter bytes").toBeGreaterThan(100);
  });

  test("wizard de criar agente abre na UI (visao confirma)", async ({ page }, info) => {
    await loginAs(page, account);
    expect(await navTab(page, "specialized"), "nav specialized").toBeTruthy();
    await page.waitForTimeout(1500);
    const tab = page.getByRole("tab", { name: /Criar Funcion.rio F.cil/i }).first();
    if (await tab.isVisible().catch(() => false)) { await tab.click({ force: true }); await page.waitForTimeout(1500); }
    await expect(page.getByRole("button", { name: /Pr.xima Etapa/i }).first()).toBeVisible({ timeout: 15_000 });
    const shot = info.outputPath("agent-wizard.png");
    await page.screenshot({ path: shot });
    const v = await verifySemantic(shot, "Um assistente de criacao de agente de IA esta' aberto, mostrando uma etapa com opcoes de configuracao.");
    if (v.pass !== null) info.annotations.push({ type: "vision", description: v.verdict });
    expect(v.pass === null || v.pass === true, `visao reprovou: ${v.verdict}`).toBeTruthy();
  });
});

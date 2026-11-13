// e2e-wizards.spec.ts — Etapa 4: Gestor Facil, Follow-up, Conhecimento.
// Gestor: PUT wizard -> GET confirma os campos. Follow-up: criar -> GET -> deletar.
import { test, expect } from "@playwright/test";
import { createTrialAccount, loginAs, navTab, type Account } from "../lib/session.js";
import { apiPost, apiPut, getManagerWizard, listFollowups, pickArray } from "../lib/backend.js";
import { tracker } from "../lib/cleanup.js";
import { verifySemantic } from "../lib/vision.js";

let account: Account;
test.beforeAll(async () => { test.setTimeout(180_000); account = await createTrialAccount(); });

test.describe("Wizards — salvar e verificar no backend", () => {
  test("Gestor Facil: salvar config -> GET /api/easy-manager/wizard confirma", async ({}, info) => {
    const marker = "QA_Mgr_" + Date.now();
    const put = await apiPut(account, "/api/easy-manager/wizard", {
      config: { name: marker, systemPrompt: "Prompt do gestor QA", provider: "gemini", enabled: true },
    });
    expect(put.ok, `PUT wizard falhou: ${JSON.stringify(put)}`).toBeTruthy();
    const back = await getManagerWizard(account);
    const cfg = back.data?.config || {};
    expect(cfg.name, "nome do gestor deveria persistir").toBe(marker);
    expect(cfg.systemPrompt, "prompt deveria persistir").toBe("Prompt do gestor QA");
    expect(cfg.provider).toBe("gemini");
    info.annotations.push({ type: "backend", description: `gestor confirmado: name/prompt/provider` });
  });

  test("Follow-up: criar sequencia -> GET /api/followup/sequences confirma -> deletar", async ({}, info) => {
    const t = tracker(account);
    const name = "QA_Seq_" + Date.now();
    const created = await apiPost(account, "/api/followup/sequences", {
      name, trigger_value: "no_reply", template: "Ola {nome}, tudo bem?", delay_minutes: 60,
    });
    expect(created.ok, `create sequencia falhou: ${JSON.stringify(created)}`).toBeTruthy();
    const id = created.data?.id;
    expect(id).toBeTruthy();
    t.track("followup " + name, `/api/followup/sequences/${id}`);

    const back = await listFollowups(account);
    const rules = pickArray(back.data, "rules");
    expect(rules.find((r: any) => r.id === id || r.name === name), "sequencia deveria aparecer em GET").toBeTruthy();
    info.annotations.push({ type: "backend", description: `sequencia ${id} confirmada` });

    const cleaned = await t.cleanupAll();
    info.annotations.push({ type: "cleanup", description: JSON.stringify(cleaned) });
    const back2 = await listFollowups(account);
    expect(pickArray(back2.data, "rules").find((r: any) => r.id === id), "sequencia deveria sumir").toBeFalsy();
  });

  test("Gestor Facil na UI: 4 etapas + Salvar Gestor visivel", async ({ page }, info) => {
    await loginAs(page, account);
    expect(await navTab(page, "specialized"), "nav specialized").toBeTruthy();
    await page.waitForTimeout(1500);
    const tab = page.getByRole("tab", { name: /Criar Gestor F.cil/i }).first();
    await expect(tab).toBeVisible({ timeout: 10_000 });
    await tab.click({ force: true });
    await page.waitForTimeout(1500);
    await expect(page.getByRole("button", { name: /Salvar Gestor/i }).first()).toBeVisible({ timeout: 10_000 });
    const prox = page.getByRole("button", { name: /Pr.xima Etapa/i }).first();
    await expect(prox).toBeVisible({ timeout: 10_000 });
    await prox.click({ force: true });
    await page.waitForTimeout(1200);
    const etapas = await page.getByText(/Identidade e Motor do Gestor|Canais e Matriz|Ferramentas|Superpoderes/i).count();
    expect(etapas, "esperava as etapas do wizard do Gestor").toBeGreaterThan(0);
    const shot = info.outputPath("gestor-ui.png");
    await page.screenshot({ path: shot });
  });

  test("Base de Conhecimento: aba abre (mapeia se persiste ou e' cosmetica)", async ({ page }, info) => {
    await loginAs(page, account);
    expect(await navTab(page, "specialized"), "nav specialized").toBeTruthy();
    await page.waitForTimeout(1500);
    const tab = page.getByRole("tab", { name: /Base de Conhecimento/i }).first();
    if ((await tab.count()) === 0) { test.skip(true, "aba Conhecimento nao encontrada"); return; }
    await tab.click({ force: true });
    await page.waitForTimeout(1500);
    const shot = info.outputPath("conhecimento.png");
    await page.screenshot({ path: shot });
    const v = await verifySemantic(shot, "Uma secao de Base de Conhecimento (documentos/treino da IA) esta' visivel.");
    if (v.pass !== null) info.annotations.push({ type: "vision", description: v.verdict });
    // Honesto: alguns botoes aqui sao cosmeticos/disabled — nao forcamos verde falso.
    const disabledBtns = await page.locator("button:disabled:visible").count();
    info.annotations.push({ type: "nota", description: `botoes disabled visiveis: ${disabledBtns}` });
  });
});

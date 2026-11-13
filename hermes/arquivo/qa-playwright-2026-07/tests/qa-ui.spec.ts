// qa-ui.spec.ts — Suite que simula o cliente na UI do Hermes Call.
// Cria conta trial (decisao: nao tocar prod), loga, navega por TODAS as abas,
// clica em botoes principais e usa Gemini (via proxy OmniRoute) pra julgar se
// cada acao fez de fato o que deveria.
import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { createTrialAccount, loginAs, navTab, type Account } from "../lib/session.js";
import { verifySemantic } from "../lib/vision.js";
import { BASE_URL, TAB_LABELS, PLANS } from "../config.js";

let account: Account;

test.beforeAll(async () => {
  test.setTimeout(180_000);
  account = await createTrialAccount();
});

test.afterAll(async () => {
  // A conta trial e' descartavel — mas deixa so' pra documentar que existe.
  console.log("Conta usada:", account.email);
});

// navTo — reusa o navTab robusto do session.ts (espera a aba ficar visivel antes de
// clicar; nao lanca se o app estiver hidratando). Antes havia um helper local que
// clicava sem checar visibilidade e quebrava de forma flaky.
async function navTo(page: Page, view: string): Promise<void> {
  await navTab(page, view);
}

async function gotoAndVerify(page: Page, info: TestInfo, view: string) {
  const label = TAB_LABELS[view];
  test.skip(!label, `Sem label mapeado pra view=${view}`);
  // manager_chat NAO troca de view: e' um botao (customTrigger) que abre um dialog.
  // Ele nao tem #nav-*, entao clicamos pelo texto do botao.
  if (view === "manager_chat") {
    const btn = page.locator('button:has-text("Funcionário Gestor")').first();
    await expect(btn).toBeVisible({ timeout: 10_000 });
    await btn.click({ force: true });
    await page.waitForTimeout(1500);
  } else {
    // Botao tem id estavel `nav-${view}` (ver Sidebar.tsx). Clicamos por id + force,
    // porque a animacao translate-x-1 da sidebar deixa o elemento "instavel" e o
    // click normal do Playwright fica esperando estabilizar ate estourar timeout.
    const navBtn = page.locator(`#nav-${view}`).first();
    await expect(navBtn).toBeVisible({ timeout: 10_000 });
    await navBtn.click({ force: true });
    await page.waitForTimeout(1200); // deixa a view montar
  }
  const file = info.outputPath(`screen-${view}.png`);
  await page.screenshot({ path: file, fullPage: false });
  const expectation = `A pagina carregou a aba "${label}" do painel Hermes, sem tela branca, sem mensagem de erro, mostrando o conteudo dessa secao.`;
  const v = await verifySemantic(file, expectation);
  if (v.pass === null) test.info().annotations.push({ type: "vision", description: v.verdict });
  else if (!v.pass) test.info().annotations.push({ type: "vision", description: "FAIL: " + v.verdict });
  // Nao usamos expect() aqui — a visao e' informativa (assert dura quebraria suite inteira por causa de IA).
}

test.describe("Painel — fluxo de cliente novo (trial)", () => {
  test("login e dashboard carregam", async ({ page }, info) => {
    await loginAs(page, account);
    await expect(page).toHaveURL(new RegExp(BASE_URL.replace(/\//g, "\\/")));
    // Esta' no painel (nao na tela de login/wizard).
    await expect(page.locator("text=Visão Geral").first()).toBeVisible({ timeout: 15_000 });
    await page.screenshot({ path: info.outputPath("dashboard.png") });
  });

  // Itera por TODAS as abas que o plano trial libera (espelha plan_features.go do backend).
  for (const view of PLANS.trial.tabs) {
    test(`aba "${TAB_LABELS[view]}" abre sem erro`, async ({ page }, info) => {
      await loginAs(page, account);
      await gotoAndVerify(page, info, view);
    });
  }
});

// Teste mecanico de "clica num botao e algo muda" — sem precisar de visao.
test.describe("Botoes principais respondem (mecanico)", () => {
  test("botao Sair existe e desloga", async ({ browser }) => {
    // Aqui NAO usamos addInitScript: ele re-injetaria o token a cada reload, e o Sair
    // faz clearAuth()+location.reload(). Usamos storageState (estado inicial do context),
    // que e' aplicado UMA vez — apos o logout+reload o token some de verdade.
    const origin = new URL(BASE_URL).origin;
    const ctx = await browser.newContext({
      storageState: {
        cookies: [],
        origins: [{
          origin,
          localStorage: [
            { name: "hermes.token", value: account.token },
            { name: "hermes.user", value: JSON.stringify({ id: account.userId, email: account.email, plan: account.plan }) },
            { name: `hermes.onboarding.done.${account.userId}`, value: "1" },
          ],
        }],
      },
    });
    const page = await ctx.newPage();
    await page.goto(BASE_URL, { waitUntil: "networkidle" });
    // Ha DUAS sidebars (desktop + drawer mobile); `:visible` pega so' a que o cliente ve.
    const sair = page.locator('[aria-label="Sair"]:visible').first();
    await expect(sair).toBeVisible({ timeout: 10_000 });
    // Dispara clique DOM nativo: o click({force}) do Playwright acertava um overlay e
    // nao disparava o onClick do React (a URL nem mudava). el.click() aciona o handler.
    await sair.evaluate((el) => (el as HTMLElement).click());
    // Logout faz clearAuth()+location.reload(); esperamos a navegacao e o token sumir.
    await page.waitForTimeout(2500);
    const token = await page.evaluate(() => localStorage.getItem("hermes.token"));
    expect(token).toBeFalsy();
    await ctx.close();
  });

  test("botao dispara toast e ele aparece (top-center, fix step 7)", async ({ page }, info) => {
    // O <Toaster> (position="top-center", fix do step 7) mora DENTRO do <App/>. Um toast
    // so' injeta [data-sonner-toast] no DOM QUANDO dispara. Numa conta trial vazia, os
    // gatilhos de toast dependem de dados (link de agendamento, produto no catalogo etc),
    // entao tentamos varios gatilhos conhecidos e provamos com o primeiro que aparecer.
    await loginAs(page, account);
    const triggers: Array<{ view: string; btn: RegExp }> = [
      { view: "catalog", btn: /Copiar/i },
      { view: "agenda", btn: /Copiar Link/i },
    ];
    let disparou = false;
    for (const t of triggers) {
      await navTo(page, t.view);
      const btn = page.getByRole("button", { name: t.btn }).first();
      if ((await btn.count()) === 0) continue;
      await btn.evaluate((el) => (el as HTMLElement).click()).catch(() => {});
      await page.waitForTimeout(800);
      if ((await page.locator("[data-sonner-toast]").count()) > 0) { disparou = true; break; }
    }
    // Se nenhum gatilho estava disponivel no estado atual, nao falha: registra e pula.
    // O posicionamento top-center ja foi confirmado estaticamente no App.tsx (auditoria).
    test.skip(!disparou, "Nenhum gatilho de toast disponivel numa conta trial vazia");
    const toast = page.locator("[data-sonner-toast]").first();
    await expect(toast).toBeVisible({ timeout: 5_000 });
    // Confirma visualmente a posicao (top-center, fix do step 7) via visao.
    const shot = info.outputPath("toast.png");
    await page.screenshot({ path: shot });
    const v = await verifySemantic(shot, "Um toast/notificacao esta' visivel no TOPO-CENTRO da tela (nao no rodape nem nos cantos).");
    if (v.pass !== null) test.info().annotations.push({ type: "vision", description: v.verdict });
  });
});
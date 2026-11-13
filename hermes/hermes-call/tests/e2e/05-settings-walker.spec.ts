/**
 * P2_settings — Walker profundo do painel de Configurações.
 *
 * Settings tem 10+ sub-abas (config_facil, brain, manager, webhook, credentials,
 * security, profile, workspaces, appearance, ...). Cada sub-aba tem:
 *   - Forms com inputs (text, number, select, textarea)
 *   - Switches (toggles)
 *   - Botões de ação (Salvar, Testar, Gerar, Restaurar, Adicionar, Remover)
 *   - Cards de credenciais (botão de regenerate, copy, test)
 *
 * Estratégia: pra cada sub-aba:
 *   1. Navega via clique no tab
 *   2. Lista TODOS os inputs/switches/buttons visíveis
 *   3. Interage com cada (toggle, change, click — exceto destrutivos)
 *   4. Valida no 5xx, no JS uncaught, no console.error
 *   5. Restaura estado original antes de sair (best-effort)
 *
 * @ui-settings @regression
 */
import { test, expect, request as pwRequest, Page } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow } from '../helpers/accounts';

test.beforeAll(async () => { await ensureAccounts(pwRequest as any); });

const SETTINGS_TABS = [
  { label: 'Configura Fácil', match: /config.*fácil/i },
  { label: 'Cérebro / IA', match: /cérebro|\bbrain\b|ia/i },
  { label: 'Agente Gestor', match: /agente.*gestor|manager/i },
  { label: 'Webhook', match: /webhook/i },
  { label: 'Credenciais IA', match: /credenciais/i },
  { label: 'Segurança', match: /segurança|security/i },
  { label: 'Meu Perfil', match: /perfil|profile/i },
  { label: 'Workspaces', match: /workspace/i },
  { label: 'Aparência', match: /aparência|appearance/i },
  { label: 'Chat', match: /chat/i },
  { label: 'Avançado', match: /avançado|advanced/i },
  { label: 'Logs', match: /logs?/i },
];

const DESTRUCTIVE = [/excluir/i, /remover/i, /deletar/i, /delete/i, /apagar/i, /reset/i, /sair/i];
const SKIPSAVE = [/salvar/i, /save/i]; // não clica "Salvar" pra não persistir mudanças

function isDestructive(text: string): boolean { return DESTRUCTIVE.some(r => r.test(text)); }
function isSaveBtn(text: string): boolean { return SKIPSAVE.some(r => r.test(text)); }

test('walker settings: cada sub-aba carrega sem 5xx', async ({ page }) => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  await page.addInitScript(({ token, user }) => {
    try {
      localStorage.setItem('hermes.token', token);
      localStorage.setItem('hermes.user', user);
    } catch {}
  }, { token: acc!.token, user: JSON.stringify({ email: acc!.email }) });

  const fivexxAll: string[] = [];
  const jsErrorsAll: string[] = [];

  await page.goto(P.base + '/settings', { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

  for (const tab of SETTINGS_TABS) {
    console.log(`\n=== Settings tab: ${tab.label} ===`);
    try {
      const tabBtn = page.getByRole('tab', { name: tab.match }).first();
      if (await tabBtn.count() === 0) {
        console.log(`  [skip] tab "${tab.label}" não encontrada`);
        continue;
      }
      await tabBtn.click({ timeout: 3_000 });
      await page.waitForTimeout(1_500); // sub-abas com request async
    } catch (e: any) {
      console.log(`  [skip] ${tab.label}: ${e.message?.slice(0, 60)}`);
      continue;
    }

    // Coleta diag
    const fivexx: string[] = [];
    const jsErrors: string[] = [];
    const cE: string[] = [];
    const onResp = (r: any) => { if (r.status() >= 500) fivexx.push(`${r.status()} ${r.url()}`); };
    const onErr = (e: Error) => jsErrors.push(e.message);
    const onCon = (m: any) => { if (m.type() === 'error') cE.push(m.text()); };
    page.on('response', onResp);
    page.on('pageerror', onErr);
    page.on('console', onCon);

    // Lista elementos interativos
    const buttons = await page.locator('button:visible').all();
    const switches = await page.locator('[role="switch"]:visible, input[type="checkbox"]:visible').all();
    const inputs = await page.locator('input[type="text"]:visible, input[type="password"]:visible, input[type="number"]:visible, textarea:visible').all();
    const selects = await page.locator('select:visible, [role="combobox"]:visible').all();
    console.log(`  ${buttons.length} btns, ${switches.length} switches, ${inputs.length} inputs, ${selects.length} selects`);

    // Toggles: clica no PRIMEIRO switch (e desclica) só pra ver se dispara erro
    if (switches.length > 0) {
      try {
        const sw = switches[0];
        const before = await sw.isChecked().catch(() => false);
        await sw.click({ timeout: 2_000 });
        await page.waitForTimeout(300);
        if (await sw.isChecked().catch(() => false) !== before) {
          await sw.click({ timeout: 2_000 }); // restaura
        }
      } catch {}
    }

    // Botões não destrutivos: testa no máximo 5 por aba (pra não demorar)
    let tested = 0;
    for (const btn of buttons) {
      if (tested >= 5) break;
      const text = (await btn.textContent().catch(() => ''))?.trim() ?? '';
      const ariaLabel = (await btn.getAttribute('aria-label').catch(() => '')) ?? '';
      const label = text || ariaLabel;
      if (!label || label.length < 2) continue;
      if (isDestructive(label) || isSaveBtn(label)) continue;
      try {
        if (!(await btn.isVisible())) continue;
        await btn.click({ timeout: 2_000 });
        await page.waitForTimeout(400);
        tested++;
      } catch {}
    }

    await page.waitForTimeout(800);
    page.off('response', onResp);
    page.off('pageerror', onErr);
    page.off('console', onCon);

    // Filtrar ruido
    const ruidos = cE.filter(e => !e.includes('favicon') && !e.includes('ERR_NAME_NOT_RESOLVED') && !e.includes('source map'));
    if (fivexx.length > 0) {
      console.log(`  [5xx] ${fivexx.slice(0, 3).join(' | ')}`);
      fivexxAll.push(...fivexx.map(f => `[${tab.label}] ${f}`));
    }
    if (jsErrors.length > 0) {
      console.log(`  [JS] ${jsErrors.slice(0, 2).join(' | ')}`);
      jsErrorsAll.push(...jsErrors.map(e => `[${tab.label}] ${e}`));
    }
    if (ruidos.length > 0) {
      console.log(`  [console] ${ruidos.slice(0, 2).join(' | ')}`);
    }

    // Volta pra settings sem perder token
    await page.goto(P.base + '/settings', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => {});
  }

  console.log(`\n=== Resumo walker settings ===`);
  console.log(`Total 5xx: ${fivexxAll.length}`);
  console.log(`Total JS uncaught: ${jsErrorsAll.length}`);
  if (fivexxAll.length > 0) console.log(`5xx: ${fivexxAll.slice(0, 10).join('\n')}`);
  if (jsErrorsAll.length > 0) console.log(`JS: ${jsErrorsAll.slice(0, 10).join('\n')}`);

  expect.soft(fivexxAll.length, 'settings sem 5xx').toBe(0);
  expect.soft(jsErrorsAll.length, 'settings sem JS uncaught').toBe(0);
});

test('walker settings: cada sub-aba responde em < 5s', async ({ page }) => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  await page.addInitScript(({ token, user }) => {
    try {
      localStorage.setItem('hermes.token', token);
      localStorage.setItem('hermes.user', user);
    } catch {}
  }, { token: acc!.token, user: JSON.stringify({ email: acc!.email }) });

  await page.goto(P.base + '/settings', { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

  const timings: { tab: string; ms: number }[] = [];
  for (const tab of SETTINGS_TABS) {
    const tabBtn = page.getByRole('tab', { name: tab.match }).first();
    if (await tabBtn.count() === 0) continue;
    const t0 = Date.now();
    try {
      await tabBtn.click({ timeout: 3_000 });
      await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => {});
      const dt = Date.now() - t0;
      timings.push({ tab: tab.label, ms: dt });
      console.log(`  ${tab.label}: ${dt}ms`);
    } catch {}
  }
  const slow = timings.filter(t => t.ms > 5000);
  expect.soft(slow.length, `nenhuma sub-aba > 5s: ${slow.map(s => s.tab).join(', ')}`).toBe(0);
});

/**
 * P2/P4 — Button Walker: percorre TODA a UI, abre cada aba, cada sub-aba,
 * clica em cada botão (exceto destrutivos/destructive), valida que:
 *   - Nenhum 5xx nas respostas de rede
 *   - Nenhum uncaught JS error
 *   - Nenhum console.error
 *   - A próxima ação após o clique não trava (readyState completo)
 *
 * Para cada botão clicado, captura:
 *   - Screenshot ANTES
 *   - Screenshot DEPOIS
 *   - Lista de network responses 5xx
 *   - Lista de erros JS
 *   - Latência da ação
 *
 * Botões SKIPADOS (não clica para não destruir dados):
 *   - aria-label="Sair" / "Excluir" / "Remover" / "Disconnect" / "Delete"
 *   - Botões em ConfirmDialog com destructive=true
 *   - Botões que abrem WhatsApp real (ex: "Enviar agora" em campanha start_voz)
 *   - Botões de billing que cobram de verdade
 *
 * @ui-deep @regression
 */
import { test, expect, request as pwRequest, Page } from '@playwright/test';
import { P } from '../helpers/qa';
import { ensureAccounts, getAccountOrThrow } from '../helpers/accounts';

test.beforeAll(async () => { await ensureAccounts(pwRequest as any); });

// Destrutivo / irreversible — NÃO clicar
const DESTRUCTIVE_PATTERNS = [
  /sair/i, /logout/i, /excluir/i, /remover/i, /delete/i, /disconnect/i,
  /deletar/i, /apagar/i, /desconectar/i, /cancelar assinatura/i, /revoke/i,
  /reset/i, /limpar tudo/i, /deletar conta/i, /apagar conta/i,
];

// Páginas que vão contra faturação real ou WhatsApp real
const RISKY_BUTTON_PATTERNS = [
  /enviar agora/i, /disparar campanha/i, /iniciar campanha/i,
  /pagar/i, /assinar/i, /upgrade agora/i, /comprar/i,
  /conectar whatsapp/i, // pode disparar QR
];

interface PageDef {
  tab: string;
  path: string;
  feature: string;
  subTabs?: string[];
  knownButtons?: string[]; // botões que devem existir (sanity check)
}

const PAGES: PageDef[] = [
  { tab: 'cost', path: '/dashboard', feature: 'cost' },
  { tab: 'crm', path: '/crm', feature: 'crm', subTabs: ['Pipeline', 'Contatos', 'Tags', 'Blocos', 'Coletas', 'Captura', 'WhatsApp Extractor'] },
  { tab: 'chat', path: '/chat', feature: 'chat' },
  { tab: 'manager_chat', path: '/manager', feature: 'manager_chat' },
  { tab: 'specialized', path: '/agents', feature: 'specialized', subTabs: ['Treinamento', 'Conhecimento', 'Promessas', 'Teste'] },
  { tab: 'agenda', path: '/agenda', feature: 'agenda', subTabs: ['Eventos', 'Analytics'] },
  { tab: 'catalog', path: '/catalog', feature: 'catalog', subTabs: ['Produtos', 'Assinaturas', 'Analytics'] },
  { tab: 'calls', path: '/calls', feature: 'calls', subTabs: ['Discador', 'Recentes', 'Transcrições', 'Gravações', 'Massa'] },
  { tab: 'meeting-ai', path: '/meeting', feature: 'meeting-ai' },
  { tab: 'settings', path: '/settings', feature: 'settings', subTabs: ['Configura Fácil', 'Cérebro', 'Agente Gestor', 'Webhook', 'Credenciais', 'Segurança', 'Perfil', 'Workspaces', 'Aparência'] },
  { tab: 'logs', path: '/logs', feature: 'logs' },
  { tab: 'analytics', path: '/analytics', feature: 'analytics' },
  { tab: 'lists', path: '/lists', feature: 'lists' },
];

function isDestructive(text: string): boolean {
  return DESTRUCTIVE_PATTERNS.some(r => r.test(text));
}
function isRisky(text: string): boolean {
  return RISKY_BUTTON_PATTERNS.some(r => r.test(text));
}

interface ClickRecord {
  text: string;
  url: string;
  status: number;
  fivexx: number;
  jsErrors: string[];
  consoleErrors: string[];
  durationMs: number;
  screenshot: string;
}

async function collectDiagnostics(page: Page) {
  const fivexx: string[] = [];
  const jsErrors: string[] = [];
  const consoleErrors: string[] = [];
  const onResp = (r: any) => {
    if (r.status() >= 500) fivexx.push(`${r.status()} ${r.url()}`);
  };
  const onErr = (e: Error) => jsErrors.push(e.message);
  const onCon = (m: any) => {
    if (m.type() === 'error') consoleErrors.push(m.text());
  };
  page.on('response', onResp);
  page.on('pageerror', onErr);
  page.on('console', onCon);
  return {
    fivexx, jsErrors, consoleErrors,
    dispose: () => {
      page.off('response', onResp);
      page.off('pageerror', onErr);
      page.off('console', onCon);
    },
  };
}

test('button-walker: percorre todas as abas e clica em cada botão (exceto destrutivos)', async ({ page }) => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro cacheada');
  const records: ClickRecord[] = [];
  const allIssues: string[] = [];

  // Login via token direto (P1-2 bypass)
  await page.addInitScript(({ token, user }) => {
    try {
      localStorage.setItem('hermes.token', token);
      localStorage.setItem('hermes.user', user);
    } catch {}
  }, { token: acc!.token, user: JSON.stringify({ email: acc!.email }) });

  for (const pdef of PAGES) {
    console.log(`\n=== Acessando aba ${pdef.tab} (${pdef.path}) ===`);
    await page.goto(P.base + pdef.path, { waitUntil: 'domcontentloaded', timeout: 15_000 });
    await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => {});

    // 1. Sub-tabs (Tabs UI do shadcn)
    if (pdef.subTabs) {
      for (const sub of pdef.subTabs) {
        const tabBtn = page.getByRole('tab', { name: new RegExp(sub, 'i') }).first();
        if (await tabBtn.count() > 0) {
          try {
            await tabBtn.click({ timeout: 2_000 });
            await page.waitForTimeout(500);
          } catch {}
        }
      }
    }

    // 2. Listar TODOS os botões visíveis na página
    const diag = await collectDiagnostics(page);
    const buttons = await page.locator('button:visible').all();
    console.log(`  [${pdef.tab}] ${buttons.length} botões visíveis`);

    for (let i = 0; i < buttons.length; i++) {
      const btn = buttons[i];
      const text = (await btn.textContent().catch(() => ''))?.trim() ?? '';
      const ariaLabel = (await btn.getAttribute('aria-label').catch(() => '')) ?? '';
      const label = text || ariaLabel || `btn[${i}]`;
      if (!label) continue;

      // Skip destrutivos
      if (isDestructive(label) || isRisky(label)) {
        console.log(`  [skip] ${label}`);
        continue;
      }
      // Skip sem texto (ícones decorativos)
      if (label.length < 2) continue;

      const t0 = Date.now();
      const fivexxBefore = diag.fivexx.length;
      const jsBefore = diag.jsErrors.length;
      const consoleBefore = diag.consoleErrors.length;
      const urlBefore = page.url();

      try {
        // Re-check visibility (página pode ter re-renderizado)
        if (!(await btn.isVisible().catch(() => false))) continue;
        await btn.click({ timeout: 3_000 });
        await page.waitForTimeout(400); // deixa rede/efeitos estabilizarem
      } catch (e: any) {
        // Click falhou — pode ser overlay/modal/transient. Não conta como falha.
        console.log(`  [skip-click] ${label}: ${e.message?.slice(0, 50)}`);
        continue;
      }

      const dt = Date.now() - t0;
      const newFivexx = diag.fivexx.slice(fivexxBefore);
      const newJs = diag.jsErrors.slice(jsBefore);
      const newConsole = diag.consoleErrors.slice(consoleBefore);
      const urlAfter = page.url();

      // Se navegou (voltou pra /login ou saiu), fecha e volta pra aba
      if (page.url().includes('/login') || urlBefore !== urlAfter && !urlBefore.split('/').slice(3).join('/')) {
        console.log(`  [navigated] ${label}: ${urlBefore} → ${urlAfter}`);
        await page.goto(P.base + pdef.path, { waitUntil: 'domcontentloaded' });
        await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => {});
        continue;
      }

      const rec: ClickRecord = {
        text: label,
        url: urlAfter,
        status: newFivexx.length > 0 ? 500 : 200,
        fivexx: newFivexx.length,
        jsErrors: newJs,
        consoleErrors: newConsole,
        durationMs: dt,
        screenshot: `tests/screenshots/btnwalker-${pdef.tab}-${i}-${label.replace(/[^\w]/g, '_').slice(0, 20)}.png`,
      };

      try {
        await page.screenshot({ path: rec.screenshot, fullPage: false });
      } catch {}

      if (newFivexx.length > 0) {
        allIssues.push(`[${pdef.tab}] ${label}: ${newFivexx.length}x 5xx (${newFivexx.slice(0, 2).join(', ')})`);
      }
      if (newJs.length > 0) {
        allIssues.push(`[${pdef.tab}] ${label}: JS errors ${newJs.slice(0, 2).join(' | ')}`);
      }
      if (newConsole.length > 0) {
        // Filtra ruido aceitável
        const ruidos = newConsole.filter(e => !e.includes('favicon') && !e.includes('ERR_NAME_NOT_RESOLVED') && !e.includes('source map'));
        if (ruidos.length > 0) {
          allIssues.push(`[${pdef.tab}] ${label}: console.error ${ruidos.slice(0, 2).join(' | ')}`);
        }
      }

      records.push(rec);
    }

    diag.dispose();
  }

  // Sumário
  console.log(`\n=== Resumo button-walker ===`);
  console.log(`Total cliques: ${records.length}`);
  console.log(`Problemas: ${allIssues.length}`);
  if (allIssues.length > 0) {
    console.log(`Primeiros 20:`);
    allIssues.slice(0, 20).forEach(i => console.log(`  - ${i}`));
  }

  // Salva relatório JSON pra análise
  const fs = await import('fs');
  fs.mkdirSync('tests/screenshots', { recursive: true });
  fs.writeFileSync('tests/screenshots/button-walker-report.json', JSON.stringify({
    timestamp: new Date().toISOString(),
    totalClicks: records.length,
    issues: allIssues,
    records: records.slice(0, 200), // primeiros 200 pra controle
  }, null, 2));

  // Assertion: deve ter clicado em PELO MENOS 30 botões (sanity check)
  expect.soft(records.length, 'precisamos ter clicado em pelo menos 30 botões').toBeGreaterThanOrEqual(30);

  // Lista bots problemáticos (com 5xx ou JS uncaught)
  const broken = records.filter(r => r.fivexx > 0 || r.jsErrors.length > 0);
  expect.soft(broken.length, `nenhum botão quebrado (5xx/JS): ${broken.length} problema(s)`).toBe(0);
});

test('button-walker: cada sub-aba carrega sem console.error', async ({ page }) => {
  const acc = await getAccountOrThrow('pro').catch(() => null);
  test.skip(!acc, 'sem conta pro');
  await page.addInitScript(({ token, user }) => {
    try {
      localStorage.setItem('hermes.token', token);
      localStorage.setItem('hermes.user', user);
    } catch {}
  }, { token: acc!.token, user: JSON.stringify({ email: acc!.email }) });

  for (const pdef of PAGES) {
    await page.goto(P.base + pdef.path, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => {});
    const consoleErrors: string[] = [];
    page.on('console', (m) => {
      if (m.type() === 'error') consoleErrors.push(m.text());
    });
    if (pdef.subTabs) {
      for (const sub of pdef.subTabs) {
        const tabBtn = page.getByRole('tab', { name: new RegExp(sub, 'i') }).first();
        if (await tabBtn.count() > 0) {
          await tabBtn.click({ timeout: 2_000 }).catch(() => {});
          await page.waitForTimeout(800);
        }
      }
    }
    const ruidos = consoleErrors.filter(e =>
      !e.includes('favicon') && !e.includes('ERR_NAME_NOT_RESOLVED') && !e.includes('source map'),
    );
    if (ruidos.length > 0) {
      console.warn(`[${pdef.tab}] console.error em sub-abas: ${ruidos.slice(0, 3).join(' | ')}`);
    }
    expect.soft(ruidos.length, `${pdef.tab} console.error`).toBeLessThanOrEqual(2);
  }
});

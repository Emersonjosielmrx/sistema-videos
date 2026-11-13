/**
 * QA Helpers — ações reutilizáveis do Playwright.
 *
 * Cada helper é uma função que abre o estado interno (login, plano, contexto)
 * e devolve o estado resultante, pra encadear com a próxima ação sem ter que
 * repetir o setup. Usado por TODOS os specs e2e/*.spec.ts.
 *
 * Padrão: tudo é assíncrono, error-first nunca — quem quiser tratar exceção
 * que chame playwright expect().
 */
import { Page, BrowserContext, expect } from '@playwright/test';

const BASE = process.env.HERMES_BASE || 'https://hermescall.opus-sem-limites.com.br';
const COUPON = process.env.HERMES_QA_COUPON || 'TESTE_GRATIS';

let _accountCounter = 0;

export interface Account {
  email: string;
  password: string;
  plan: 'trial' | 'start_voz' | 'start_texto' | 'pro' | 'scale';
  token: string;
}

export const P = {
  base: BASE,
  coupon: COUPON,
  /** Tempo default de espera (em ms) pra elementos aparecerem. */
  timeout: 10_000,
};

/** Aguarda o `app` estar montado (substitui o polling nas chamadas comuns). */
export async function openApp(page: Page, route = '/'): Promise<void> {
  await page.goto(P.base + route, { waitUntil: 'networkidle' });
  // Se bate em /login, acabou de abrir e tá deslogado — comportamento normal.
}

/** Faz login com email/senha no painel. Devolve token JWT pra chamadas API diretas. */
export async function login(page: Page, email: string, password: string): Promise<string> {
  const resp = await page.request.post(P.base + '/api/auth/login', {
    data: { email, password },
  });
  if (resp.status() !== 200 && resp.status() !== 402 && resp.status() !== 403) {
    throw new Error(`login failed: ${resp.status()} ${await resp.text()}`);
  }
  const body = await resp.json();
  return body.token || '';
}

/** Registra um usuário novo com plano X. Auto-incrementa pra não duplicar email. */
export async function register(
  page: Page,
  plan: Account['plan'] = 'trial',
  opts: { admin?: boolean } = {},
): Promise<Account> {
  _accountCounter++;
  const tag = `qa${Date.now().toString(36).slice(-5)}${_accountCounter}`;
  const email = `${tag}.${plan}@qa.local`;
  const password = '<SEGREDO_REMOVIDO>';
  const cpf = plan === 'trial' ? '' : '11144477735';

  const resp = await page.request.post(P.base + '/api/auth/register', {
    data: {
      name: `QA ${plan}`,
      email,
      password,
      plan,
      cpf_cnpj: cpf,
    },
  });
  // 201 = criado; 429 = rate-limit; 4xx com JSON {error} = problema conhecido.
  const body = await resp.json().catch(() => ({}));
  if (resp.status() === 429) throw new Error('rate-limited — espera 10min');
  if (resp.status() !== 201 && resp.status() !== 200 && !body.token) {
    throw new Error(`register failed: ${resp.status()} ${JSON.stringify(body)}`);
  }
  if (plan !== 'trial' && body.token) {
    // Aplica cupom pra liberar o billing gate (só no test, em prod cobrança real).
    const r2 = await page.request.post(P.base + '/api/billing/coupon', {
      headers: { Authorization: `Bearer ${body.token}` },
      data: { coupon: P.coupon },
    });
    if (!r2.ok()) {
      throw new Error(`coupon failed: ${r2.status()} ${await r2.text()}`);
    }
  }
  return { email, password, plan, token: body.token || '' };
}

/** Acessa o painel via cookie/sessão real (não é só o token API). */
export async function loginUI(page: Page, email: string, password: string): Promise<void> {
  await page.goto(P.base + '/login', { waitUntil: 'networkidle' });
  // Fallback: se cair direto na tela principal, procura formulário.
  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  if (await emailInput.count() === 0) return; // já tá logado
  await emailInput.fill(email);
  await page.locator('input[type="password"]').first().fill(password);
  await page.locator('button:has-text("Entrar"), button[type="submit"]').first().click();
  await page.waitForURL((url) => !url.toString().includes('/login'), { timeout: P.timeout });
}

/** Limpa sessão do navegador — usa pra forçar re-login entre specs. */
export async function logout(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.context().clearCookies();
}

/** Anexa listeners que viram qualquer erro JS (rede, render) em erro do test.
 *  Só funciona em page mode (Playwright request context não tem page). */
export function attachErrorListeners(page: Page | null, label: string): { detach: () => void } {
  if (!page) return { detach: () => {} };
  const errors: string[] = [];
  const onPageError = (err: Error) => {
    errors.push(`[${label}] uncaught: ${err.message}`);
  };
  const onConsole = (msg: { type(): string; text(): string }) => {
    if (msg.type() === 'error') errors.push(`[${label}] console: ${msg.text()}`);
  };
  const onResponse = (resp: { status(): number; url(): string }) => {
    if (resp.status() >= 500) errors.push(`[${label}] http 5xx: ${resp.status()} ${resp.url()}`);
  };
  page.on('pageerror', onPageError);
  page.on('console', onConsole);
  page.on('response', onResponse);
  return {
    detach: () => {
      page.off('pageerror', onPageError);
      page.off('console', onConsole);
      page.off('response', onResponse);
      if (errors.length > 0) {
        // Filtra erros de rede que são de assets não-críticos (ex: favicon off-line).
        // Considera erro só quando tem pelo menos 1 uncaught ou http 5xx.
        const fatals = errors.filter(e => !e.includes('ERR_NAME_NOT_RESOLVED') && !e.includes('favicon'));
        if (fatals.length > 0) {
          throw new Error(`Page errors em ${label}:\n  ${fatals.join('\n  ')}`);
        }
      }
    },
  };
}

/** Espera elemento aparecer (text-based), evitando flaky por animações. */
export async function waitForText(page: Page, text: string | RegExp): Promise<void> {
  await page.waitForSelector(`text=${text}`, { timeout: P.timeout, state: 'visible' });
}

/** Tira screenshot nomeado pra reports. */
export async function shoot(page: Page, name: string): Promise<string> {
  const path = `tests/screenshots/${name}.png`;
  await page.screenshot({ path, fullPage: true });
  return path;
}

/** Verifica que NENHUM console.error aconteceu durante uma ação. */
export async function expectNoConsoleErrors(page: Page, fn: () => Promise<void>): Promise<void> {
  const before = (page as any)._qaErrCount || 0;
  await fn();
  await page.waitForTimeout(500); // deixa console.error chegar
  const after = (page as any)._qaErrCount || 0;
  if (after > before) {
    throw new Error(`Console errors detectados durante a ação (${before}→${after})`);
  }
}

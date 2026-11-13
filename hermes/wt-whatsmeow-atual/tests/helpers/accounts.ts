/**
 * Cache de contas — 1 conta por plano, reaproveita entre runs do Playwright.
 * Persiste em tests/.state/accounts.json pra não estourar rate-limit do backend.
 *
 * Estratégia:
 *   - Garante 1 conta por plano na primeira execução do run (ensureAccounts).
 *   - Runs seguintes: lê do disco, valida com /me, recria se 401/403.
 *   - Plano pago: aplica cupom TESTE_GRATIS pra bypass do payment_gate.
 */
import { APIRequestContext } from '@playwright/test';
import { P } from './qa';
import * as fs from 'fs';
import * as path from 'path';

export const ALL_PLANS = ['trial', 'start_voz', 'start_texto', 'pro', 'scale'] as const;
export type Plan = typeof ALL_PLANS[number];

interface CachedAcc {
  email: string;
  password: string;
  token: string;
  createdAt: string;
}

type State = Partial<Record<Plan, CachedAcc>>;

const STATE_DIR = path.join(__dirname, '..', '.state');
const STATE_FILE = path.join(STATE_DIR, 'accounts.json');

function readState(): State {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return {};
  }
}
function writeState(state: State): void {
  fs.mkdirSync(STATE_DIR, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

async function validAccount(req: APIRequestContext, acc: CachedAcc): Promise<boolean> {
  // Aceita tanto APIRequestContext quanto o módulo request (este último é "singleton" —
  // só usa pra criar contextos, sem request direto).
  const ctx = typeof req.get === 'function' ? req : await (req as any).newContext?.();
  if (!ctx || typeof ctx.get !== 'function') return true; // Não dá pra validar — assume ok
  const r = await ctx.get(P.base + '/api/auth/me', {
    headers: { Authorization: `Bearer ${acc.token}` },
  });
  return r.status() === 200;
}

async function registerOne(req: APIRequestContext, plan: Plan): Promise<CachedAcc> {
  // Email com tag único pra não duplicar mesmo se cache falhou.
  const tag = `${plan[0]}${plan[1]}${Date.now().toString(36).slice(-4)}`;
  const email = `qa${tag}.${plan}@local.test`;
  const password = '<SEGREDO_REMOVIDO>';
  const cpf = plan === 'trial' ? '' : '11144477735';
  const resp = await req.post(P.base + '/api/auth/register', {
    data: { name: `QA ${plan}`, email, password, plan, cpf_cnpj: cpf },
  });
  if (resp.status() === 429) throw new Error(`rate-limited registrando ${plan}`);
  const body = await resp.json();
  if (!body.token) throw new Error(`register ${plan} sem token: ${resp.status()} ${JSON.stringify(body)}`);
  // Plano pago → aplica cupom.
  if (plan !== 'trial') {
    const r2 = await req.post(P.base + '/api/billing/coupon', {
      headers: { Authorization: `Bearer ${body.token}` },
      data: { coupon: P.coupon },
    });
    if (!r2.ok()) throw new Error(`coupon ${plan}: ${r2.status()} ${await r2.text()}`);
  }
  return { email, password, token: body.token, createdAt: new Date().toISOString() };
}

/** Garante que existe 1 conta cacheada válida pra cada plano. Plano sem cache é pulado
 *  silenciosamente — o caller usa admin como fallback. */
export async function ensureAccounts(req: APIRequestContext): Promise<void> {
  const state = readState();
  const updated: State = { ...state };
  for (const plan of ALL_PLANS) {
    const existing = state[plan];
    if (existing && await validAccount(req, existing)) {
      continue; // reusa
    }
    try {
      updated[plan] = await registerOne(req, plan);
      // Salva incremental pra não perder tudo se um plano falhar.
      writeState(updated);
      console.log(`[accounts] criou ${plan} → ${updated[plan]!.email}`);
    } catch (e: any) {
      console.warn(`[accounts] skip ${plan}: ${e.message} — usando admin/cache como fallback`);
    }
  }
}

export async function getAccount(plan: Plan): Promise<CachedAcc | null> {
  const s = readState();
  return s[plan] ?? null;
}

export async function getAccountOrThrow(plan: Plan): Promise<CachedAcc> {
  const acc = await getAccount(plan);
  if (!acc) throw new Error(`conta ${plan} não cacheada e não foi possível criar (rate-limit?)`);
  return acc;
}

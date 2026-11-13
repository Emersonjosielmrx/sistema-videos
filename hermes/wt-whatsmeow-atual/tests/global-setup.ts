/**
 * Global setup — roda 1× antes de qualquer spec.
 * Provisiona contas QA e arquiva cache em tests/.state/.
 */
import { request } from '@playwright/test';
import { ensureAccounts } from './helpers/accounts';

export default async function globalSetup(): Promise<void> {
  const ctx = await request.newContext({
    baseURL: process.env.HERMES_BASE || 'https://hermescall.opus-sem-limites.com.br',
  });
  await ensureAccounts(ctx as any);
}

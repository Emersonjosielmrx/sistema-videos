#!/usr/bin/env -S npx tsx
/**
 * Provisiona contas QA — roda standalone antes de qualquer suite Playwright.
 * Persiste em tests/.state/accounts.json. Idempotente.
 */
import { readState, writeState, ensureAccounts } from '../helpers/accounts';
import { request as pwRequest } from '@playwright/test';

(async () => {
  const ctx = await pwRequest.newContext({
    baseURL: process.env.HERMES_BASE || 'https://hermescall.opus-sem-limites.com.br',
  });
  await ensureAccounts(ctx as any);
  const s = readState();
  for (const [plan, acc] of Object.entries(s)) {
    if (acc) console.log(`${plan}: ${acc.email}`);
  }
  process.exit(0);
})().catch((e) => { console.error(e); process.exit(1); });

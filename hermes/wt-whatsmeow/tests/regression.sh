#!/usr/bin/env bash
# Regressão rápida — chamada por cron de checkpoint, pela dona no fim, e
# após cada fix grande. NÃO roda os E2E completos (são lentos), só o smoke.
# Exit code 0 = tudo verde. !=0 = tem regressão (P0 a investigar).

set -uo pipefail

cd "$(dirname "$0")" || exit 2
cd ..  # raiz do repo

echo "==[ Regressão ]== $(date -u +%FT%TZ)"

# 1. Backend online?
BASE="${HERMES_BASE:-https://hermescall.opus-sem-limites.com.br}"
if ! curl -s -o /dev/null -w '%{http_code}' "$BASE/api/version" | grep -q '^200$'; then
  echo "🚨 backend offline ($BASE/api/version ≠ 200)"
  exit 1
fi

# 2. Suite de smoke do Playwright (sem E2E lento).
cd tests
if [ ! -f node_modules/.bin/playwright ]; then
  echo "playwright não instalado — rode npm install primeiro"
  exit 1
fi

# Carrega contas (se ainda não tem)
node -r ts-node/register -e "
const { request } = require('@playwright/test');
const { ensureAccounts } = require('./helpers/accounts');
(async () => {
  const ctx = await request.newContext({ baseURL: process.env.HERMES_BASE || 'http://localhost:8095' });
  await ensureAccounts(ctx);
  process.exit(0);
})();
" 2>&1 | tail -5

# Roda smoke + segurança serial
npx playwright test 01-smoke-routes.spec.ts 02-security.spec.ts --reporter=line 2>&1 | tail -50
RC=$?
cd ..
[ "$RC" -ne 0 ] && echo "🚨 smoke falhou (rc=$RC)"
exit "$RC"

#!/bin/sh
# mostra onde o OmniRoute monta o User-Agent e a versao do Antigravity
cd /app/.build/next/server/chunks
for f in 88852.js 36827.js; do
  echo "== $f"
  grep -oE '.{0,220}antigravity/[$"+`].{0,220}' "$f" | head -3 | cut -c1-460
done
echo "== versoes no codigo"
grep -ohE '"?[0-9]+\.[0-9]+\.[0-9]+"?[^;]{0,20}(antigravity|ANTIGRAVITY)' 88852.js 36827.js | head -5
grep -ohE '(ANTIGRAVITY_VERSION|antigravityVersion|AG_VERSION|IDE_VERSION|ideVersion)[^;]{0,80}' 88852.js 36827.js | sort -u | head -8

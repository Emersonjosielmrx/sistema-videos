#!/bin/bash
# Testa a divisão de planos end-to-end contra o beta:
# - 5 contas, uma por plano (trial, start_voz, start_texto, pro, scale)
# - Aplica cupom TESTE_GRATIS para liberar contas pagas (sem cupom o payment_gate barra)
# - Login → /me → valida features.tabs
# - Hit uma rota proibida do plano → espera 403 plan_forbidden
set -uo pipefail

BASE="${1:-http://localhost:8095}"
ts=$(date +%s)

pass=0; fail=0
ok() { echo "  ok $1"; pass=$((pass+1)); }
ko() { echo "  FAIL $1 ($2)"; fail=$((fail+1)); }

register() {
  local plan="$1"
  local email="t${ts}.${plan}@test.local"
  curl -s -X POST "$BASE/api/auth/register" -H 'Content-Type: application/json' \
    -d "{\"name\":\"T ${plan}\",\"email\":\"${email}\",\"password\":\"senha123\",\"plan\":\"${plan}\",\"cpf_cnpj\":\"11144477735\"}" >/dev/null
  echo "$email"
}

login() {
  curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1\",\"password\":\"senha123\"}" \
    | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))'
}

apply_coupon() {
  curl -s -X POST "$BASE/api/billing/coupon" -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $1" \
    -d '{"coupon":"TESTE_GRATIS"}' >/dev/null
}

get_json() {
  local tok="$1" path="$2"
  curl -s "$BASE$path" -H "Authorization: Bearer $tok"
}

status_of() {
  local tok="$1" path="$2"
  curl -s -o /dev/null -w '%{http_code}' "$BASE$path" -H "Authorization: Bearer $tok"
}

assert_features() {
  local label="$1" tok="$2" want_contains="$3" want_forbids="$4"
  local me; me="$(get_json "$tok" /api/auth/me)"
  local tabs; tabs="$(echo "$me" | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin).get("features",{}).get("tabs",[])))')"
  for t in $want_contains; do
    if echo " $tabs " | grep -q " $t "; then ok "$label tem aba $t"
    else ko "$label tem aba $t" "tabs=[$tabs]"; fi
  done
  for t in $want_forbids; do
    if echo " $tabs " | grep -q " $t "; then ko "$label NAO devia ter $t" "tabs=[$tabs]"
    else ok "$label sem aba $t"; fi
  done
}

assert_route_forbidden() {
  local label="$1" tok="$2" path="$3"
  local code; code="$(status_of "$tok" "$path")"
  if [ "$code" = "403" ]; then ok "$label rota $path bloqueada (403)"
  else ko "$label rota $path devia ser 403" "code=$code"; fi
}

assert_route_ok() {
  local label="$1" tok="$2" path="$3"
  local code; code="$(status_of "$tok" "$path")"
  if [ "$code" = "200" ]; then ok "$label rota $path ok (200)"
  else ko "$label rota $path devia ser 200" "code=$code"; fi
}

test_plan() {
  local plan="$1" want_contains="$2" want_forbids="$3" route_200="$4" route_403="$5"
  echo "==> ${plan}"
  local email; email=$(register "$plan")
  sleep 0.4
  local tok; tok=$(login "$email")
  if [ -z "$tok" ]; then ko "${plan} login" "sem token"; return; fi
  ok "${plan} login"
  if [ "$plan" != "trial" ]; then
    apply_coupon "$tok"
    sleep 0.2
    tok=$(login "$email")  # re-login agora que billing ta active
  fi
  assert_features "$plan" "$tok" "$want_contains" "$want_forbids"
  if [ -n "$route_200" ]; then assert_route_ok "$plan" "$tok" "$route_200"; fi
  if [ -n "$route_403" ]; then assert_route_forbidden "$plan" "$tok" "$route_403"; fi
}

echo "==> Base: $BASE"
test_plan trial        "cost crm chat calls meeting-ai catalog agenda specialized manager_chat" "" /api/agent-profiles ""
test_plan start_voz    "cost crm calls"            "chat manager_chat specialized catalog agenda meeting-ai" /api/calls/recent /api/agent-profiles
test_plan start_texto  "cost crm chat manager_chat specialized" "calls catalog agenda meeting-ai" /api/agent-profiles /api/calls/recent
test_plan pro          "cost crm chat calls specialized manager_chat catalog agenda" "meeting-ai" /api/agent-profiles /api/meet/sessions
test_plan scale        "cost crm chat calls meeting-ai catalog agenda specialized manager_chat" "" /api/meet/sessions ""

echo
echo "==> Resumo: $pass ok, $fail falha"
[ $fail -eq 0 ] || exit 1

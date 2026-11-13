#!/usr/bin/env bash
# Etapa 3 (variante "a bancada liga"): o 8288 (bancada, perfil "Cliente Simulado") liga pro 8653
# (produção), que ATENDE SOZINHA com a IA dela. Testa a voz real da produção: transcrição, IA,
# voz, interrupção e tempo de resposta. Roda NA VPS. Nada de segredo é exibido.
#   ligacao-teste.sh disparar ["fala de abertura"]   → dispara e mostra o id da campanha
#   ligacao-teste.sh relatorio <desde: "YYYY-MM-DD HH:MM:SS">  → resumo dos logs das duas pontas
set -euo pipefail
SID=<SEGREDO_REMOVIDO>          # 8288 na bancada
PROF=36e3e547-fb9f-41c9-8e23-22b8336d24ce     # "Cliente Simulado" (conta de teste da bancada)
# Número de destino: fica FORA do git, em /etc/hermes-call/ensaio.env (DEST=55...), só na VPS.
[ -r /etc/hermes-call/ensaio.env ] && . /etc/hermes-call/ensaio.env
DEST=${DEST:?defina DEST em /etc/hermes-call/ensaio.env}

token() {
  python3 - <<'PY'
import json, urllib.request
env = dict(l.rstrip("\n").split("=", 1) for l in open("/etc/hermes-bancada/bancada.env") if "=" in l and not l.startswith("#"))
body = json.dumps({"email": "hayllateste@test.com", "password": env["BANCADA_CLIENTE_SENHA"]}).encode()
req = urllib.request.Request("http://127.0.0.1:8091/api/auth/login", data=body, headers={"Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=20)).get("token", ""))
PY
}

disparar() {
  local fala=${1:-"Alô, boa noite! Vi que vocês mexem com atendimento por inteligência artificial. Quem tá falando?"}
  local tk; tk=$(token)
  [ -n "$tk" ] || { echo "login na bancada falhou"; exit 1; }
  local body
  body=$(python3 -c 'import json,sys; print(json.dumps({"numbers":[sys.argv[1]],"names":["Hermes produção"],"profile_id":sys.argv[2],"conversational":True,"convo_max_ms":150000,"max_ring_ms":40000,"tts_message":sys.argv[3]}))' "$DEST" "$PROF" "$fala")
  curl -s -m 90 -X POST "http://127.0.0.1:8091/api/sessions/$SID/broadcast" -H "Authorization: Bearer $tk" -H "Content-Type: application/json" -d "$body"
  echo
  unset tk
}

relatorio() {
  local desde=$1
  echo "=== PRODUÇÃO (atendeu no 8653)"
  journalctl -u hermes-call --since "$desde" --no-pager -o cat | grep -E "call|voice|barge|latência|reserva|fala|STT|TTS|level=ERROR|level=WARN" \
    | grep -viE "key=|token|secret|password|telegram poll" | cut -c1-260 | tail -60
  echo "=== BANCADA (ligou do 8288)"
  journalctl -u hermes-bancada --since "$desde" --no-pager -o cat | grep -E "runCampaign|call|voice|barge|latência|level=ERROR|level=WARN" \
    | grep -viE "key=|token|secret|password|retry motor primário" | cut -c1-260 | tail -40
}

case "${1:-}" in
  disparar) shift; disparar "$@" ;;
  relatorio) relatorio "${2:?desde}" ;;
  *) echo "uso: $0 disparar [fala] | relatorio 'YYYY-MM-DD HH:MM:SS'"; exit 1 ;;
esac

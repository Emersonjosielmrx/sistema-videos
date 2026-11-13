#!/usr/bin/env bash
# Laboratório na bancada (roda NA VPS). Uso:
#   lab-bancada.sh preparar <REL>          atualiza o programa + copia agentes e voz da produção
#   lab-bancada.sh rodar "<agente>" <persona> <turnos> <pronuncia true|false> [modo]
# Nada de segredo é exibido (senha da bancada lida do arquivo root-only; chaves de banco pra banco).
set -euo pipefail
SRC=4e8adf4a-6530-47e2-af4c-1c268e6e68d7   # admin da produção
ADM=6dbb3d22-87e7-49f9-a7ac-2883eeebba31   # admin da bancada
P="sudo -u postgres psql -v ON_ERROR_STOP=1 -q -tA"
cd /
B=/opt/hermes-bancada

preparar() {
  REL=$1
  cp -a /opt/hermes-call/releases/$REL/hermes-call $B/hermes-call.novo && mv -f $B/hermes-call.novo $B/hermes-call
  rm -rf $B/dist.novo && cp -a /opt/hermes-call/releases/$REL/dist $B/dist.novo && rm -rf $B/dist && mv $B/dist.novo $B/dist
  echo "$REL" > $B/VERSAO
  # Agentes de ligação (só os textos; áudios não precisam no nível 1/2)
  # Só as colunas que existem nos DOIS bancos (a produção tem colunas antigas a mais)
  local qc="SELECT string_agg(column_name, ',' ORDER BY column_name) FROM information_schema.columns WHERE table_name='agent_profiles' AND table_schema='public'"
  local cb cp cols
  cb=$($P -d bancada_main -c "$qc" | tr ',' '
' | sort)
  cp=$($P -d wacalls_main -c "$qc" | tr ',' '
' | sort)
  cols=$(comm -12 <(echo "$cb") <(echo "$cp") | paste -sd, -)
  $P -d bancada_main -c "DROP TABLE IF EXISTS _imp_prof; CREATE TABLE _imp_prof (LIKE agent_profiles)"
  $P -d wacalls_main -c "COPY (SELECT $cols FROM agent_profiles WHERE user_id='$SRC' AND name IN ('Teste E (renomeado 02-10)','Vendas Hermes Call')) TO STDOUT" | $P -d bancada_main -c "COPY _imp_prof ($cols) FROM STDIN"
  $P -d bancada_main -c "DELETE FROM agent_profiles WHERE user_id='$ADM' AND name IN (SELECT name FROM _imp_prof);
    UPDATE _imp_prof SET id = gen_random_uuid(), user_id = '$ADM', audio_id = NULL, trigger_audio_id = NULL, offer_audio_id = NULL, instance_name = '';
    INSERT INTO agent_profiles SELECT * FROM _imp_prof; DROP TABLE _imp_prof"
  # Voz da ligação (ElevenLabs da dona) pro teste de pronúncia: chaves de banco pra banco
  $P -d bancada_main -c "DELETE FROM credentials WHERE user_id='$ADM' AND provider='elevenlabs'; DROP TABLE IF EXISTS _imp_el; CREATE TABLE _imp_el (name text, type text, provider text, api_key text, base_url text)"
  $P -d wacalls_main -c "COPY (SELECT name, type, provider, api_key, base_url FROM credentials WHERE user_id='$SRC' AND provider='elevenlabs') TO STDOUT" | $P -d bancada_main -c "COPY _imp_el FROM STDIN"
  $P -d bancada_main -c "INSERT INTO credentials (id,user_id,name,type,provider,api_key,base_url) SELECT gen_random_uuid(), '$ADM', name, type, provider, api_key, base_url FROM _imp_el; DROP TABLE _imp_el"
  # Chaves do Gemini (inclusive as grátis) pra comparar modelos nas etapas de texto
  $P -d bancada_main -c "DELETE FROM credentials WHERE user_id='$ADM' AND provider='gemini'; DROP TABLE IF EXISTS _imp_gm; CREATE TABLE _imp_gm (name text, type text, provider text, api_key text, base_url text)"
  $P -d wacalls_main -c "COPY (SELECT name, type, provider, api_key, base_url FROM credentials WHERE user_id='$SRC' AND provider='gemini') TO STDOUT" | $P -d bancada_main -c "COPY _imp_gm FROM STDIN"
  $P -d bancada_main -c "INSERT INTO credentials (id,user_id,name,type,provider,api_key,base_url) SELECT gen_random_uuid(), '$ADM', name, type, provider, api_key, base_url FROM _imp_gm; DROP TABLE _imp_gm"
  # Groq, OpenRouter e proxies Webshare (v0.7.0: rodízio de chaves e proxy de saída) — banco pra banco
  $P -d bancada_main -c "DELETE FROM credentials WHERE user_id='$ADM' AND (provider IN ('groq','webshare') OR base_url ILIKE '%openrouter%'); DROP TABLE IF EXISTS _imp_gq; CREATE TABLE _imp_gq (name text, type text, provider text, api_key text, base_url text)"
  $P -d wacalls_main -c "COPY (SELECT name, type, provider, api_key, base_url FROM credentials WHERE user_id='$SRC' AND (provider IN ('groq','webshare') OR base_url ILIKE '%openrouter%') ORDER BY created_at) TO STDOUT" | $P -d bancada_main -c "COPY _imp_gq FROM STDIN"
  $P -d bancada_main -c "INSERT INTO credentials (id,user_id,name,type,provider,api_key,base_url) SELECT gen_random_uuid(), '$ADM', name, type, provider, api_key, base_url FROM _imp_gq; DROP TABLE _imp_gq"
  # A voz da bancada aponta pra chave Groq de STT pelo id: reaponta pro id novo (senão "voice service disabled")
  $P -d bancada_main -c "UPDATE settings SET value = jsonb_set(value, '{stt_credential_id}', to_jsonb((SELECT id::text FROM credentials WHERE user_id='$ADM' AND provider='groq' ORDER BY (name='Groq Whisper STT') DESC, created_at LIMIT 1))), updated_at=now() WHERE user_id='$ADM' AND key='voice' AND EXISTS (SELECT 1 FROM credentials WHERE user_id='$ADM' AND provider='groq')"
  VOZ=$($P -d wacalls_main -c "SELECT COALESCE(value->>'tts_voice','') FROM settings WHERE user_id='$SRC' AND key='voice'")
  $P -d bancada_main -c "UPDATE settings SET value = value || jsonb_build_object('tts_provider','elevenlabs','tts_voice','$VOZ','tts_credential_id',''), updated_at=now() WHERE user_id='$ADM' AND key='voice'"
  systemctl restart hermes-bancada
  for i in $(seq 1 20); do sleep 3; curl -s -m3 http://127.0.0.1:8091/api/version >/dev/null && break; done
  echo "bancada: $(systemctl is-active hermes-bancada) $(cat $B/VERSAO) | agentes: $($P -d bancada_main -c "SELECT string_agg(name, ', ') FROM agent_profiles WHERE user_id='$ADM'") | chaves voz: $($P -d bancada_main -c "SELECT count(*) FROM credentials WHERE user_id='$ADM' AND provider='elevenlabs'")"
  journalctl -u hermes-bancada --since "-1 min" --no-pager -o cat | grep -E "voice service|level=ERROR" | grep -viE "key=|token|secret|password" | cut -c1-200
}

token() {
  local email pass
  email=$(sed -n 's/^HERMES_ADMIN_EMAIL=//p' /etc/hermes-bancada/bancada.env)
  pass=$(sed -n 's/^HERMES_ADMIN_PASSWORD=//p' /etc/hermes-bancada/bancada.env)
  python3 - "$email" "$pass" <<'PY'
import json, sys, urllib.request
body = json.dumps({"email": sys.argv[1], "password": sys.argv[2]}).encode()
req = urllib.request.Request("http://127.0.0.1:8091/api/auth/login", data=body, headers={"Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=20)).get("token", ""))
PY
}

rodar() {
  local nome=$1 persona=$2 turnos=$3 pron=$4 modo=${5:-vendas} modelo=${6:-} chave=${7:-} modav=${8:-} chav=${9:-}
  local id; id=$($P -d bancada_main -c "SELECT id FROM agent_profiles WHERE user_id='$ADM' AND name='$nome'")
  [ -n "$id" ] || { echo "agente '$nome' não existe na bancada"; exit 1; }
  local tk; tk=$(token)
  [ -n "$tk" ] || { echo "login na bancada falhou"; exit 1; }
  local out=/root/lab-$(date +%H%M%S)-$$.json
  curl -s -m 280 -X POST "http://127.0.0.1:8091/api/agents/$id/call-lab" -H "Authorization: Bearer $tk" -H "Content-Type: application/json" \
    -d "{\"persona\":\"$persona\",\"turnos\":$turnos,\"pronuncia\":$pron,\"modo\":\"$modo\",\"modelo\":\"$modelo\",\"chave\":\"$chave\",\"modelo_avaliador\":\"$modav\",\"chave_avaliador\":\"$chav\"}" > "$out"
  unset tk
  echo "$out"
  cat "$out"
}

case "${1:-}" in
  preparar) preparar "$2" ;;
  rodar) shift; rodar "$@" ;;
  *) echo "uso: $0 preparar <REL> | rodar <agente> <persona> <turnos> <true|false> [modo]"; exit 1 ;;
esac

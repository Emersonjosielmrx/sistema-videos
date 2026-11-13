#!/usr/bin/env bash
# ops/vps/ensaio.sh — JANELA DE ENSAIO: ligação IA × IA de verdade entre a BANCADA e a PRODUÇÃO.
# Roda NA VPS (como root). Decisão da dona em 04/10: "janela de ensaio".
#
#   A BANCADA (linha 8288, versão em teste) é a VENDEDORA: liga com o agente "Vendas Hermes Call".
#   A PRODUÇÃO (linha 8653) faz a CLIENTE: atende SÓ ligações do 8288 com o perfil "Cliente Simulado (ensaio)".
#   Fora da janela a produção volta exatamente ao normal.
#
#   ensaio.sh inicio            liga a janela (produção reinicia ~10 s; desliga sozinha em 30 min se esquecida)
#   ensaio.sh ligar [agente]    a bancada liga pro 8653 (agente padrão: "Vendas Hermes Call")
#   ensaio.sh relatorio [desde] resumo das duas pontas (desde: "YYYY-MM-DD HH:MM:SS"; padrão: última ligação)
#   ensaio.sh fim               desliga a janela (produção reinicia ~10 s). Pode rodar quantas vezes quiser.
#   ensaio.sh completo [agente] inicio + ligar + espera a ligação acabar + relatorio + fim (fim garantido)
#   ensaio.sh status
#
# Cuidados:
#   - Durante a janela, ligação do 8288 pro 8653 é atendida pela IA "cliente" (é o teste). Outros números: normal.
#   - O WhatsApp ainda não reconhece o aceite do Hermes (docs/REGRESSOES_LIGACAO.md §5): o celular que tiver o
#     8653 pode continuar tocando durante o ensaio — NÃO atender.
#   - Na bancada com versão ≥ v0.8.0, a IA vendedora espera o aceite pra ouvir: o bancada.env precisa de
#     HERMES_VOICE_ESPERA_ACEITE=false (só na bancada) enquanto o aceite não for consertado.
# Nada de segredo é exibido (senha da bancada lida do arquivo root-only).
set -euo pipefail

PROD_ADMIN=4e8adf4a-6530-47e2-af4c-1c268e6e68d7          # admin@hermescall.com (produção, linha 8653)
BANC_ADMIN=6dbb3d22-87e7-49f9-a7ac-2883eeebba31          # admin da bancada
BANC_SID=edba8cacecab3732912295e5b33da30d                # 8288 na bancada
# Números completos ficam SÓ na VPS (o repositório pode ficar público): /etc/hermes-call/ensaio.env com
#   DEST=<número da linha da produção que faz a cliente, ex.: 5591…8653>
#   ORIGEM=<número da linha da bancada que faz a vendedora, ex.: 5591…8288>
[ -f /etc/hermes-call/ensaio.env ] && . /etc/hermes-call/ensaio.env
DEST=${DEST:-}
ORIGEM=${ORIGEM:-}
CLIENTE_NOME="Cliente Simulado (ensaio)"
CLIENTE_VOZ=EXAVITQu4vr4xnSDxMaL                         # voz ElevenLabs diferente da vendedora
DROPIN=/etc/systemd/system/hermes-call.service.d/40-ensaio.conf
ESTADO=/root/ensaio-estado
MARCA=/root/ENSAIO_ATIVO
SAIDA=/root/ensaios
P="sudo -u postgres psql -v ON_ERROR_STOP=1 -q -tA"
cd /

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "PAROU: $*" >&2; exit 1; }

prod_ok() { curl -s -m3 http://127.0.0.1:8080/api/version | grep -q '"build"'; }
banc_ok() { curl -s -m3 http://127.0.0.1:8091/api/version | grep -q '"build"'; }
espera() { local f=$1 n=${2:-30}; for i in $(seq 1 "$n"); do "$f" && return 0; sleep 3; done; return 1; }

reiniciar_producao() {
  systemctl daemon-reload
  systemctl restart hermes-call
  espera prod_ok 30 || die "a produção não voltou a responder em 90 s — veja: journalctl -u hermes-call -n 80"
  sleep 15   # linhas do WhatsApp reconectarem
}

ligacao_ativa_na_producao() {
  # Ligação em curso = "call ACTIVE" nos últimos 10 min sem fim depois dela.
  local ultimo_ativo ultimo_fim
  ultimo_ativo=$(journalctl -u hermes-call --since "-10 min" --no-pager -o short-unix | grep -E 'call ACTIVE|incoming call' | tail -1 | cut -d' ' -f1 | cut -d. -f1)
  [ -n "$ultimo_ativo" ] || return 1
  ultimo_fim=$(journalctl -u hermes-call --since "-10 min" --no-pager -o short-unix | grep -E 'call terminated|cliente desligou|media stats da ligação|ligação encerrada|entrega=|ligação não atendida|chamada encerrada' | tail -1 | cut -d' ' -f1 | cut -d. -f1)
  [ -z "$ultimo_fim" ] || [ "$ultimo_fim" -lt "$ultimo_ativo" ]
}

perfil_cliente_producao() {
  # Cria/atualiza o perfil "Cliente Simulado (ensaio)" na conta admin da produção, copiando o roteiro da bancada.
  local prompt_b64
  prompt_b64=$($P -d bancada_main -c "SELECT encode(convert_to(system_prompt,'UTF8'),'base64') FROM agent_profiles WHERE name='Cliente Simulado' ORDER BY created_at LIMIT 1" | tr -d '\n')
  [ -n "$prompt_b64" ] || die "perfil 'Cliente Simulado' não encontrado na bancada"
  $P -d wacalls_main -c "
    INSERT INTO agent_profiles (id, user_id, name, system_prompt, voice_id, enable_two_audio, created_at)
    VALUES (gen_random_uuid(), '$PROD_ADMIN', '$CLIENTE_NOME', convert_from(decode('$prompt_b64','base64'),'UTF8'), '$CLIENTE_VOZ', false, now())
    ON CONFLICT (user_id, name) DO UPDATE SET system_prompt = EXCLUDED.system_prompt, voice_id = EXCLUDED.voice_id, enable_two_audio = false"
  $P -d wacalls_main -c "SELECT id FROM agent_profiles WHERE user_id='$PROD_ADMIN' AND name='$CLIENTE_NOME'"
}

cmd_inicio() {
  [ -n "$DEST" ] && [ -n "$ORIGEM" ] || die "defina DEST e ORIGEM em /etc/hermes-call/ensaio.env"
  [ ! -f "$MARCA" ] || { log "janela já está ligada desde $(cat $MARCA) (rode 'fim' antes, se quiser recomeçar)"; return 0; }
  if ligacao_ativa_na_producao; then die "há uma ligação em andamento na produção agora — tente de novo em alguns minutos"; fi
  local pid cur
  pid=$(perfil_cliente_producao | tail -1)
  [ -n "$pid" ] || die "não consegui criar o perfil do cliente na produção"
  cur=$($P -d wacalls_main -c "SELECT COALESCE(value->>'voice_profile_id','') FROM settings WHERE user_id='$PROD_ADMIN' AND key='agent_chat'")
  printf 'VOICE_PROFILE_ID_ANTES=%s\nCOMECO=%s\n' "$cur" "$(date '+%F %T')" > "$ESTADO"
  # O lado CLIENTE tem que soar como uma pessoa: sem som de fundo de call center e sem palavras
  # de apoio (no 1º ensaio, 04/10, o barulho de um lado virava "fala" do outro). Guarda os
  # valores de antes pra devolver no "fim".
  $P -d wacalls_main -c "SELECT jsonb_build_object('ambient_mode',value->'ambient_mode','background_noise',value->'background_noise','filler_enabled',value->'filler_enabled')::text FROM settings WHERE user_id='$PROD_ADMIN' AND key='voice'" > "$ESTADO.voz"
  $P -d wacalls_main -c "UPDATE settings SET value = value || '{\"ambient_mode\":\"\",\"background_noise\":\"\",\"filler_enabled\":false}'::jsonb, updated_at = now() WHERE user_id='$PROD_ADMIN' AND key='voice'"
  $P -d wacalls_main -c "
    INSERT INTO settings (key, user_id, value, updated_at) VALUES ('agent_chat','$PROD_ADMIN', jsonb_build_object('voice_profile_id','$pid'), now())
    ON CONFLICT (key, user_id) DO UPDATE SET value = jsonb_set(COALESCE(settings.value,'{}'::jsonb), '{voice_profile_id}', to_jsonb('$pid'::text)), updated_at = now()"
  mkdir -p "$(dirname "$DROPIN")"
  cat > "$DROPIN" <<EOF
# JANELA DE ENSAIO (ops/vps/ensaio.sh) — a produção atende SÓ o 8288 (bancada) como cliente simulado.
# Removido por "ensaio.sh fim". Se ficou aqui por engano: apague este arquivo, systemctl daemon-reload,
# systemctl restart hermes-call.
[Service]
Environment="HERMES_AUTO_ANSWER_ACEITAR=true"
Environment="HERMES_AUTO_ANSWER_SOMENTE_DE=$ORIGEM"
Environment="HERMES_AUTO_ANSWER_ATRASO_MS=1500"
EOF
  date '+%F %T' > "$MARCA"
  # Rede de segurança: desliga sozinha em 30 min se ninguém rodar "fim".
  systemd-run --quiet --unit=hermes-ensaio-fim --on-active=30min /bin/bash "$(readlink -f "$0")" fim >/dev/null 2>&1 || true
  log "reiniciando a produção com a janela de ensaio..."
  reiniciar_producao
  log "JANELA LIGADA: a produção atende só o $ORIGEM como '$CLIENTE_NOME' (desliga sozinha em 30 min)"
}

cmd_fim() {
  local antes=""
  systemctl stop hermes-ensaio-fim.timer >/dev/null 2>&1 || true
  if [ -f "$ESTADO" ]; then antes=$(sed -n 's/^VOICE_PROFILE_ID_ANTES=//p' "$ESTADO"); fi
  $P -d wacalls_main -c "UPDATE settings SET value = jsonb_set(value, '{voice_profile_id}', to_jsonb('$antes'::text)), updated_at = now() WHERE user_id='$PROD_ADMIN' AND key='agent_chat'" || true
  if [ -s "$ESTADO.voz" ]; then
    local voz_b64; voz_b64=$(base64 -w0 < "$ESTADO.voz")
    $P -d wacalls_main -c "UPDATE settings SET value = value || jsonb_strip_nulls(convert_from(decode('$voz_b64','base64'),'UTF8')::jsonb), updated_at = now() WHERE user_id='$PROD_ADMIN' AND key='voice'" || true
    rm -f "$ESTADO.voz"
  fi
  if [ -f "$DROPIN" ] || [ -f "$MARCA" ]; then
    rm -f "$DROPIN" "$MARCA"
    log "desligando a janela: reiniciando a produção..."
    reiniciar_producao
  fi
  rm -f "$ESTADO"
  log "JANELA DESLIGADA: produção normal ($(curl -s -m3 http://127.0.0.1:8080/api/version))"
}

token_bancada() {
  python3 - <<'PY'
import json, urllib.request
env = dict(l.rstrip("\n").split("=", 1) for l in open("/etc/hermes-bancada/bancada.env") if "=" in l and not l.startswith("#"))
body = json.dumps({"email": env["HERMES_ADMIN_EMAIL"], "password": env["HERMES_ADMIN_PASSWORD"]}).encode()
req = urllib.request.Request("http://127.0.0.1:8091/api/auth/login", data=body, headers={"Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=20)).get("token", ""))
PY
}

cmd_ligar() {
  local agente=${1:-"Vendas Hermes Call"} dono perfil tk body
  [ -f "$MARCA" ] || die "a janela de ensaio está desligada (rode: ensaio.sh inicio)"
  banc_ok || die "a bancada não está respondendo (systemctl status hermes-bancada)"
  # A linha 8288 da bancada tem que estar na conta admin da bancada (agentes, voz ElevenLabs e chaves).
  dono=$($P -d bancada_main -c "SELECT user_id FROM sessions WHERE id='$BANC_SID'")
  if [ "$dono" != "$BANC_ADMIN" ]; then
    log "passando a linha 8288 da bancada pra conta admin da bancada (vendedora)"
    $P -d bancada_main -c "UPDATE sessions SET user_id='$BANC_ADMIN' WHERE id='$BANC_SID'"
    systemctl restart hermes-bancada; espera banc_ok 30 || die "bancada não voltou"; sleep 15
  fi
  perfil=$($P -d bancada_main -c "SELECT id FROM agent_profiles WHERE user_id='$BANC_ADMIN' AND name='$agente' LIMIT 1")
  [ -n "$perfil" ] || die "agente '$agente' não existe na bancada (rode /root/lab-bancada.sh preparar <REL>)"
  tk=$(token_bancada); [ -n "$tk" ] || die "login na bancada falhou"
  body=$(python3 -c 'import json,sys; print(json.dumps({"numbers":[sys.argv[1]],"names":["Cliente ensaio"],"profile_id":sys.argv[2],"conversational":True,"convo_max_ms":150000,"max_ring_ms":40000}))' "$DEST" "$perfil")
  date '+%F %T' > /root/ensaio-ultima-ligacao
  # 05/10: o DEST também é um celular de verdade. Ele TOCA; se alguém atender nele, a ligação
  # vira a três (vendedora + cliente simulado + pessoa) e o ensaio não vale.
  log "ATENÇÃO: o celular do $DEST vai TOCAR. Avise a dona antes e peça para NÃO atender."
  log "bancada ($(curl -s -m3 http://127.0.0.1:8091/api/version | grep -o '"build":"[^"]*"')) liga pro $DEST com '$agente'"
  curl -s -m 90 -X POST "http://127.0.0.1:8091/api/sessions/$BANC_SID/broadcast" -H "Authorization: Bearer $tk" -H "Content-Type: application/json" -d "$body" | cut -c1-300
  echo
  unset tk
}

esperar_fim_da_ligacao() {
  local desde; desde=$(cat /root/ensaio-ultima-ligacao)
  for i in $(seq 1 70); do   # até ~3,5 min
    sleep 3
    journalctl -u hermes-bancada --since "$desde" --no-pager -o cat | grep -qE 'Campanha finalizada|runCampaign: fim|campaign finished|conversational: cliente desligou|call terminated' && { sleep 5; return 0; }
  done
  log "a ligação não terminou em 3,5 min — seguindo pro relatório"
}

cmd_relatorio() {
  local desde=${1:-$(cat /root/ensaio-ultima-ligacao 2>/dev/null || date -d '-10 min' '+%F %T')} f
  mkdir -p "$SAIDA"; f="$SAIDA/$(date -d "$desde" '+%Y%m%d-%H%M%S').txt"
  {
    echo "# Ensaio IA × IA — desde $desde"
    echo "bancada (vendedora): $(curl -s -m3 http://127.0.0.1:8091/api/version)"
    echo "produção (cliente):  $(curl -s -m3 http://127.0.0.1:8080/api/version)"
    echo
    echo "## VENDEDORA (bancada)"
    journalctl -u hermes-bancada --since "$desde" --no-pager -o cat \
      | grep -E 'remote accepted|call ACTIVE|aguardando_aceite|espera_aceite|2-audio|oferta|voice transcribed|voice ai reply|latência real|barge-in|descartad|eco|reserva|terminated|cliente desligou|media stats|level=ERROR|level=WARN' \
      | grep -viE 'key=|token|secret|password|telegram poll' | sed -E 's/[0-9]{10,}/N/g; s/session=[0-9a-f]+ //' | cut -c1-260
    echo
    echo "## CLIENTE (produção)"
    journalctl -u hermes-call --since "$desde" --no-pager -o cat \
      | grep -E 'incoming call|inbound call|atendida pela IA|voice transcribed|voice ai reply|latência real|barge-in|terminated|media stats|level=ERROR|level=WARN' \
      | grep -viE 'key=|token|secret|password|telegram poll' | sed -E 's/[0-9]{10,}/N/g; s/session=[0-9a-f]+ //' | cut -c1-260
    echo
    echo "## RESUMO"
    # Aceite vindo do aparelho principal (sem ":NN" no remetente) = uma pessoa atendeu no celular.
    local atendeu
    atendeu=$(journalctl -u hermes-bancada --since "$desde" --no-pager -o cat | grep 'sentido=recebida' \
      | grep -E 'from=\\"[0-9]+@lid\\"[^>]*><accept' | grep -oE 'time=[^ ]+' | head -1 || true)
    if [ -n "$atendeu" ]; then
      echo "ENSAIO INVÁLIDO: um celular de verdade ATENDEU esta ligação ($atendeu). A vendedora ouviu duas"
      echo "  fontes ao mesmo tempo; não use os números da conversa abaixo. Repita avisando para não atender."
    fi
    echo "latência da vendedora (fim da fala do cliente → 1º áudio, ms):"
    journalctl -u hermes-bancada --since "$desde" --no-pager -o cat | grep -o 'ms_fim_fala_ate_1o_audio=[0-9]*' | cut -d= -f2 | awk '{s+=$1; n++; if($1>m)m=$1} END {if(n) printf "  %d respostas, média %.0f, pior %d\n", n, s/n, m; else print "  nenhuma resposta medida"}'
    echo "oferta interrompida: $(journalctl -u hermes-bancada --since "$desde" --no-pager -o cat | grep -c 'interrompida=true') vez(es)"
  } | tee "$f"
  echo "(salvo em $f)"
}

cmd_status() {
  if [ -f "$MARCA" ]; then echo "janela LIGADA desde $(cat $MARCA)"; else echo "janela desligada"; fi
  echo "produção: $(curl -s -m3 http://127.0.0.1:8080/api/version)"
  echo "bancada:  $(curl -s -m3 http://127.0.0.1:8091/api/version)"
  [ -f "$DROPIN" ] && echo "drop-in de ensaio presente: $DROPIN" || true
}

case "${1:-}" in
  inicio) cmd_inicio ;;
  fim) cmd_fim ;;
  ligar) shift; cmd_ligar "$@" ;;
  relatorio) shift; cmd_relatorio "$@" ;;
  status) cmd_status ;;
  completo)
    shift
    trap 'cmd_fim' EXIT
    cmd_inicio
    cmd_ligar "$@"
    esperar_fim_da_ligacao
    cmd_relatorio
    ;;
  *) sed -n '2,25p' "$0"; exit 1 ;;
esac

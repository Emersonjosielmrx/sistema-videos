#!/usr/bin/env bash
# trancar-servico.sh — tranca o arquivo do serviço do Hermes e tira os segredos dele.
# Roda NA VPS, como root, pela dona: `ssh -t hermes-prod /opt/hermes-call/ops/trancar-servico.sh`
# (ou dois cliques em ops\TRANCAR-SERVICO-E-SENHAS.bat no PC).
#
# Achado de 15/10/2026: /etc/systemd/system/hermes-call.service estava com permissão 666 (qualquer
# usuário/processo da VPS compartilhada lê e ESCREVE) e trazia o token do bot do Telegram e a URL do
# banco (usuário com senha igual ao nome) em Environment=. O que este script faz, nesta ordem:
#   1. backup da unit e do drop-in de segredos (600);
#   2. troca a senha do usuário do banco (opcional, pergunta) por uma aleatória de 32 letras;
#   3. aceita um token NOVO do bot do Telegram (opcional; gere no BotFather antes: /revoke);
#   4. leva WACALLS_PG_URL e HERMES_TELEGRAM_TOKEN para 10-segredos.conf (600) e tira da unit;
#   5. se /etc/hermes-call/alertas.env estiver preenchido, liga o monitor do próprio Hermes
#      (HERMES_MONITOR_BOT_TOKEN/CHAT_ID: aviso quando a linha do WhatsApp cai ou é bloqueada);
#   6. chmod 644 na unit, daemon-reload, e REINÍCIO SEGURO (só sem ligação em curso; espera até 10 min);
#   7. se o serviço não voltar, desfaz tudo (inclusive a senha do banco) e reinicia com o antigo.
# O backup diário (hermes-backup.sh) lê Environment= pelo systemctl show, que inclui o drop-in: não quebra.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "rode como root"; exit 1; }
UNIT=/etc/systemd/system/hermes-call.service
DROP=/etc/systemd/system/hermes-call.service.d/10-segredos.conf
ALERTAS=/etc/hermes-call/alertas.env
KEYF=/root/.hermes-campanha-apikey
SID=290f2fb3c1ad8d570c732d16afd41f1e   # linha 8653 (campanha)
umask 077
TS=$(date +%Y%m%d-%H%M)

echo
echo "TRANCAR O SERVIÇO DO HERMES (permissões, segredos, senha do banco)"
echo "-------------------------------------------------------------------"
echo "Permissão da unit hoje: $(stat -c %a "$UNIT")   (certo é 644)"
echo "Segredos na unit: $(grep -cE '^Environment=(WACALLS_PG_URL|HERMES_TELEGRAM_TOKEN)=' "$UNIT" || true) linha(s)   (certo é 0)"
echo "Vai reiniciar o serviço no fim, só sem ligação em curso (as 2 linhas caem por ~15 s)."
echo
read -rp "Digite SIM para continuar: " OK
[ "$OK" = "SIM" ] || { echo "Cancelado. Nada foi alterado."; exit 0; }

# ---------- 1. valores atuais + backup ----------
PGURL=$(sed -nE 's/^Environment=WACALLS_PG_URL=(.*)$/\1/p' "$UNIT" | head -1)
TGTOK=$(sed -nE 's/^Environment=HERMES_TELEGRAM_TOKEN=(.*)$/\1/p' "$UNIT" | head -1)
if [ -z "$PGURL" ]; then PGURL=$(sed -nE 's/^Environment=WACALLS_PG_URL=(.*)$/\1/p' "$DROP" | head -1); fi
if [ -z "$TGTOK" ]; then TGTOK=$(sed -nE 's/^Environment=HERMES_TELEGRAM_TOKEN=(.*)$/\1/p' "$DROP" | head -1); fi
[ -n "$PGURL" ] || { echo "não achei WACALLS_PG_URL nem na unit nem no drop-in: parando"; exit 1; }
cp -a "$UNIT" "$UNIT.bak-$TS"; cp -a "$DROP" "$DROP.bak-$TS"; chmod 600 "$UNIT.bak-$TS" "$DROP.bak-$TS"
echo "backup: $UNIT.bak-$TS e $DROP.bak-$TS (600)"
PGUSER=$(printf '%s' "$PGURL" | sed -E 's#^postgres://([^:/@]+):.*#\1#')
SENHA_ANTIGA=$(printf '%s' "$PGURL" | sed -E 's#^postgres://[^:/@]+:([^@]*)@.*#\1#')

# ---------- 2. senha nova do banco ----------
TROCOU_SENHA=0
read -rp "Trocar a senha do usuário do banco '$PGUSER' por uma aleatória? (SIM/não): " OKPG
if [ "$OKPG" = "SIM" ]; then
  NOVA=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)
  sudo -u postgres psql -v ON_ERROR_STOP=1 -qc "ALTER USER \"$PGUSER\" PASSWORD '$NOVA'"
  PGURL=$(printf '%s' "$PGURL" | sed -E "s#^(postgres://[^:/@]+:)[^@]*@#\1$NOVA@#")
  TROCOU_SENHA=1
  echo "senha do banco trocada (vale para conexões novas; o reinício no fim aplica)"
fi

# ---------- 3. token novo do bot (opcional) ----------
read -rsp "Token NOVO do bot do Telegram do Hermes (Enter = manter o atual): " NOVOTOK; echo
NOVOTOK=${NOVOTOK//[[:space:]]/}
if [ -n "$NOVOTOK" ]; then
  if printf 'url = "https://api.telegram.org/bot%s/getMe"\n' "$NOVOTOK" | curl -sS -m 15 -K - 2>/dev/null | grep -q '"ok":true'; then
    TGTOK=$NOVOTOK; echo "token novo aceito pelo Telegram"
  else
    echo "o Telegram recusou o token novo: mantendo o atual"
  fi
fi

# ---------- 4/5. drop-in de segredos ----------
MON_TOKEN=""; MON_CHAT=""
if [ -r "$ALERTAS" ]; then
  MON_TOKEN=$(sed -nE 's/^ALERTA_TG_TOKEN=(.*)$/\1/p' "$ALERTAS" | head -1)
  MON_CHAT=$(sed -nE 's/^ALERTA_TG_CHAT=(.*)$/\1/p' "$ALERTAS" | head -1)
fi
{
  echo "[Service]"
  grep -E '^Environment=' "$DROP" | grep -vE '^Environment=(WACALLS_PG_URL|HERMES_TELEGRAM_TOKEN|HERMES_MONITOR_BOT_TOKEN|HERMES_MONITOR_CHAT_ID)=' || true
  echo "Environment=WACALLS_PG_URL=$PGURL"
  [ -n "$TGTOK" ] && echo "Environment=HERMES_TELEGRAM_TOKEN=$TGTOK"
  if [ -n "$MON_TOKEN" ] && [ -n "$MON_CHAT" ]; then
    echo "Environment=HERMES_MONITOR_BOT_TOKEN=$MON_TOKEN"
    echo "Environment=HERMES_MONITOR_CHAT_ID=$MON_CHAT"
    echo "  monitor do Hermes (linha caída/bloqueada) ligado com o bot dos alertas" >&2
  fi
} > "$DROP.novo"
install -m 600 "$DROP.novo" "$DROP"; rm -f "$DROP.novo"

# ---------- 6. unit limpa e trancada ----------
grep -vE '^Environment=(WACALLS_PG_URL|HERMES_TELEGRAM_TOKEN)=' "$UNIT" > "$UNIT.novo"
install -m 644 "$UNIT.novo" "$UNIT"; rm -f "$UNIT.novo"
chmod 644 "$UNIT"; chmod 600 "$DROP"
systemctl daemon-reload
VIS=$(systemctl show hermes-call -p Environment --value | tr ' ' '\n' | grep -cE '^(WACALLS_PG_URL|HERMES_JWT_SECRET)=' || true)
echo "conferência: unit $(stat -c %a "$UNIT"), drop-in $(stat -c %a "$DROP"), $VIS de 2 segredos visíveis pelo systemd"

desfazer() {
  echo "DESFAZENDO: voltando unit e drop-in do backup"
  install -m 644 "$UNIT.bak-$TS" "$UNIT"; install -m 600 "$DROP.bak-$TS" "$DROP"
  if [ "$TROCOU_SENHA" = 1 ]; then
    sudo -u postgres psql -v ON_ERROR_STOP=1 -qc "ALTER USER \"$PGUSER\" PASSWORD '$SENHA_ANTIGA'" && echo "senha do banco voltou à anterior"
  fi
  systemctl daemon-reload; systemctl restart hermes-call
  sleep 5; systemctl is-active hermes-call && echo "serviço de volta com a configuração antiga"
}

# ---------- 7. reinício seguro ----------
ativo() {
  if [ -r "$KEYF" ]; then
    curl -s -m 5 -H "X-API-Key: $(cat "$KEYF")" "http://127.0.0.1:8080/api/sessions/$SID/calls" | sed -nE 's/.*"active":([0-9]+).*/\1/p'
  else
    echo 0
  fi
}
REINICIADO=0
for i in $(seq 1 30); do
  A=$(ativo); [ -n "$A" ] || A=0
  R=$(sudo -u postgres psql -d wacalls_main -Atc "SELECT count(*) FROM campaign_results WHERE status IN ('ringing','sending','dispatched')" 2>/dev/null || echo 0)
  if [ "$A" = 0 ] && [ "$R" = 0 ]; then
    echo "linha livre às $(date +%T): reiniciando o serviço"
    systemctl restart hermes-call; REINICIADO=1; break
  fi
  echo "ligação em curso (ativas=$A em_voo=$R): esperando 20 s"; sleep 20
done
if [ "$REINICIADO" != 1 ]; then
  echo "Linha ocupada por 10 min. A configuração nova JÁ está gravada e vale no próximo reinício."
  echo "Se trocou a senha do banco, reinicie assim que a linha ficar livre: systemctl restart hermes-call"
  exit 2
fi
OKV=0
for i in $(seq 1 30); do curl -s -m3 http://127.0.0.1:8080/api/version | grep -q '"build"' && { OKV=1; break; }; sleep 3; done
if [ "$OKV" != 1 ]; then echo "o serviço NÃO voltou em 90 s"; journalctl -u hermes-call -n 20 --no-pager -o cat | tail -8; desfazer; exit 1; fi
S=""
for i in $(seq 1 20); do S=$(curl -s http://127.0.0.1:8080/saude-local); echo "$S" | grep -q '"linhas_conectadas":2' && break; sleep 3; done
echo "versão: $(curl -s http://127.0.0.1:8080/api/version)"
echo "linhas: $(echo "$S" | sed -nE 's/.*"linhas_conectadas":([0-9]+).*/\1/p') conectadas"
journalctl -u hermes-call --since '-2 min' --no-pager -o cat | grep -E 'monitor de avisos|sessions restored|level=ERROR' | cut -c1-140 | tail -4
echo
echo "PRONTO. Unit 644 sem segredos; segredos em $DROP (600)."
[ "$TROCOU_SENHA" = 1 ] && echo "Senha do banco trocada. Backups antigos da unit ($UNIT.bak-*) guardam a senha velha: apague-os quando quiser."
[ -n "$NOVOTOK" ] && echo "Token do bot trocado: revogue o antigo no BotFather se ainda não revogou."
exit 0

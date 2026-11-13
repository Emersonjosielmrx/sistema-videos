#!/usr/bin/env bash
# backup-vps.sh — backup de TODAS as VPS da dona para o Google Drive. Roda NA PRODUÇÃO (a única que
# tem a autorização do Google). As outras VPS só exportam, por SSH, com uma chave que não serve para
# mais nada (comando forçado: /usr/local/sbin/vps-backup-exportar). Cada item é gravado num arquivo
# temporário na produção (um por vez, apagado em seguida) e enviado ao Drive com novas tentativas:
# o Google limita as requisições por minuto, e envio em fluxo (rclone rcat) não dá para repetir —
# foi o que derrubou quase toda a 1ª cópia em 05/10 ("rateLimitExceeded").
#
#   backup-vps.sh chave-publica   mostra a chave pública (cria na 1ª vez). Usada pelo instalador das outras VPS.
#   backup-vps.sh instalar        instala o exportador aqui, liga o agendamento (04:30) e dispara a 1ª cópia
#   backup-vps.sh rodar           faz o backup agora (é o que o agendamento chama)
#   backup-vps.sh estado          o que há no Drive e como foi a última execução
#   backup-vps.sh receber <vps> <diario|semanal> <item>   grava a ENTRADA como esse item e envia
#                                 (para uma cópia avulsa entregue de fora, sem a chave de backup)
#
# No Drive:  backup-vps/<vps>/diario/<AAAA-MM-DD>/   bancos (pg_dumpall), n8n (fluxos+credenciais+chave), "sistema"
#            backup-vps/<vps>/semanal/<AAAA-MM-DD>/  volumes do docker e pastas de projeto (domingo e na 1ª vez)
# Guarda 7 diários e 4 semanais por VPS. O backup do Hermes (hermes-backup.sh) continua separado, às 03:30.
# Falha em qualquer item → aviso no Telegram (hermes-alerta.sh); os itens que deram certo ficam.
#
# Config opcional (fora do git): /etc/hermes-call/backup-vps.env
#   ALVOS="teste=209.145.60.53 vps157=157.173.207.22"   REMOTE=hermes-drive:backup-vps
#   MANTER_DIAS=7  MANTER_SEMANAS=4  BWLIMIT=40M  DIA_SEMANAL=7 (1=segunda … 7=domingo)  LOCAL=producao
#   IGNORAR="pg.wizardly_kepler"   itens que NÃO entram (separados por espaço): contêiner de outro projeto
#                                  que falha todo dia e marcava a unidade inteira como 'failed' (15/10/2026)
set -Eeuo pipefail

APP=/opt/hermes-call
CONF=/etc/hermes-call/backup-vps.env
CHAVE=/root/.ssh/backup_vps
ALERTA=$APP/ops/hermes-alerta.sh
MANTER_DIAS=7; MANTER_SEMANAS=4; DIA_SEMANAL=7
# shellcheck disable=SC1090
[ -r "$CONF" ] && . "$CONF"
# O que vier pelo ambiente vale por cima (usado no ensaio e na 1ª cópia, mais lenta).
EXPORTADOR=${EXPORTADOR:-/usr/local/sbin/vps-backup-exportar}
ALVOS=${ALVOS-"teste=209.145.60.53 vps157=157.173.207.22"}
LOCAL=${LOCAL:-producao}
REMOTE=${REMOTE:-hermes-drive:backup-vps}
BWLIMIT=${BWLIMIT:-40M}
SPOOL=${SPOOL:-/var/tmp/backup-vps}
# Paciência com o limite do Google (poucas requisições por segundo, novas tentativas), mas com TETO:
# em 06/10 um envio de 215 MB ficou mais de 3 h preso (30 tentativas × 5 min de espera cada, de dia,
# com o identificador compartilhado do rclone). Agora cada arquivo desiste em no máximo ~1 h e o
# backup segue para o próximo item; o que falhar entra no aviso e é tentado de novo no dia seguinte.
RCLONE_OPTS=(--retries 3 --retries-sleep 30s --low-level-retries 10 --timeout 90s --contimeout 30s
             --max-duration 60m --tpslimit 3 --bwlimit "$BWLIMIT")

log() { echo "[$(date '+%F %T')] $*"; }
die() { echo; echo "PAROU: $*" >&2; exit 1; }
alerta() { if [ -x "$ALERTA" ]; then "$ALERTA" "$@" || true; elif [ "${1:-}" != --resolvido ]; then echo "[sem hermes-alerta] $*" >&2; fi; }
[ "$(id -u)" = 0 ] || die "rode como root"

ssh_alvo() { # $1 = endereço, $2 = pedido ("lista" ou "item <nome>")
  ssh -n -i "$CHAVE" -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 \
      -o StrictHostKeyChecking=accept-new "root@$1" "$2"
}
pedir() { # $1 = endereço ou "local", $2 = pedido
  # </dev/null e ssh -n: quem exporta nunca lê a entrada (senão comeria o resto da lista do laço)
  if [ "$1" = local ]; then SSH_ORIGINAL_COMMAND="$2" "$EXPORTADOR" </dev/null; else ssh_alvo "$1" "$2"; fi
}

cmd_chave_publica() {
  if [ ! -f "$CHAVE" ]; then
    mkdir -p /root/.ssh; chmod 700 /root/.ssh
    ssh-keygen -q -t ed25519 -N '' -C backup-da-producao -f "$CHAVE" >&2
  fi
  cat "$CHAVE.pub"
}

nome_do_arquivo() { case "$1" in pg.*) echo "$1.sql.gz" ;; *) echo "$1.tgz" ;; esac; }

enviar_arquivo() { # $1 = arquivo local, $2 = destino no Drive (com nome). Diz o tamanho em bytes na saída.
  local arq=$1 dest=$2 bytes
  bytes=$(stat -c %s "$arq" 2>/dev/null || echo 0)
  [ "$bytes" -ge 100 ] || { echo "$bytes"; return 2; }   # vazio: a exportação não produziu nada
  rclone copyto "$arq" "$dest" "${RCLONE_OPTS[@]}" >&2 || { echo "$bytes"; return 1; }
  echo "$bytes"
}

espaco_para() { # $1 = MB estimados do item. Verdadeiro se cabe no disco com folga de 3 GB.
  local livre; livre=$(df -m --output=avail "$SPOOL" 2>/dev/null | tail -1 | tr -d ' ')
  [ "${livre:-0}" -gt $(( ${1:-0} + 3000 )) ]
}

guardar() { # $1 = nome da vps, $2 = endereço|local, $3 = fazer o semanal? (1/0), $4 = arquivo do manifesto
  local nome=$1 onde=$2 semanal=$3 man=$4 lista freq item mb dest arq t0 bytes tmpf falhas=0 feitos=0
  mkdir -p "$SPOOL"; chmod 700 "$SPOOL"
  local dia; dia=$(date +%F)
  if ! lista=$(pedir "$onde" lista 2>&1); then
    log "$nome: NÃO consegui a lista ($(echo "$lista" | tail -1 | cut -c1-120))"
    echo "FALHA lista - - $(echo "$lista" | tail -1 | cut -c1-100)" >> "$man"
    return 1
  fi
  while read -r freq item mb; do
    [ -n "${item:-}" ] || continue
    case "$freq" in
      diario) dest="$REMOTE/$nome/diario/$dia" ;;
      semanal) [ "$semanal" = 1 ] || continue; dest="$REMOTE/$nome/semanal/$dia" ;;
      grande|pulado) echo "FORA $item ${mb}MB ($freq: não entra no backup)" >> "$man"; continue ;;
      *) continue ;;
    esac
    # Lista de exclusão (IGNORAR no .env): item de outro projeto que falha sempre não conta como falha.
    case " ${IGNORAR:-} " in *" $item "*) echo "IGNORADO $item ${mb}MB (na lista IGNORAR do backup-vps.env)" >> "$man"; continue ;; esac
    arq=$(nome_do_arquivo "$item")
    t0=$(date +%s)
    if ! espaco_para "$mb"; then
      echo "FALHA $item ${mb}MB 0s (sem espaço no disco da produção para preparar)" >> "$man"; falhas=$((falhas+1)); continue
    fi
    tmpf="$SPOOL/$nome.$arq.parcial"
    if ! pedir "$onde" "item $item" > "$tmpf" 2>>"$man.erros"; then
      echo "FALHA $item - $(( $(date +%s) - t0 ))s (a exportação na origem falhou)" >> "$man"; falhas=$((falhas+1))
    elif bytes=$(enviar_arquivo "$tmpf" "$dest/$arq" 2>>"$man.erros"); then
      echo "ok $freq $item $(( bytes / 1048576 ))MB $(( $(date +%s) - t0 ))s" >> "$man"; feitos=$((feitos+1))
    else
      echo "FALHA $item ${bytes:-0}B $(( $(date +%s) - t0 ))s (o envio ao Drive falhou, ou a exportação veio vazia)" >> "$man"; falhas=$((falhas+1))
    fi
    rm -f "$tmpf"
  done <<< "$lista"
  log "$nome: $feitos item(ns) guardado(s), $falhas falha(s)"
  [ "$falhas" = 0 ]
}

limpar_antigos() { # $1 = pasta no Drive (…/diario ou …/semanal), $2 = quantos manter
  local pasta=$1 manter=$2 d
  rclone lsf --dirs-only "$pasta" --tpslimit 3 2>/dev/null | sed 's#/$##' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort -r \
    | tail -n +"$(( manter + 1 ))" | while read -r d; do
        rclone purge "$pasta/$d" --tpslimit 3 >/dev/null 2>&1 && log "apagado do Drive (antigo): $pasta/$d" || true
      done || true   # pasta ainda vazia ou sem nada antigo não é erro
}

cmd_rodar() {
  command -v rclone >/dev/null || die "rclone não instalado (rode antes o configurar-backup-drive.sh)"
  rclone lsd "${REMOTE%%:*}:" >/dev/null 2>&1 || die "a autorização do Google Drive não responde (${REMOTE%%:*}:)"
  exec 9>/run/lock/backup-vps.lock
  flock -n 9 || die "já há um backup das VPS rodando"
  local nome ip semanal todas_ok=1 resumo="" man par
  TMP_RODAR=$(mktemp -d); trap 'rm -rf "$TMP_RODAR"; rm -f "$SPOOL"/*.parcial 2>/dev/null' EXIT   # global: o trap roda fora da função
  log "início — destino $REMOTE"
  for par in "$LOCAL=local" $ALVOS; do
    nome=${par%%=*}; ip=${par#*=}
    semanal=0
    { [ "$(date +%u)" = "$DIA_SEMANAL" ] || [ "${FORCAR_SEMANAL:-0}" = 1 ]; } && semanal=1
    # 1ª vez desta VPS (ainda sem nenhum semanal no Drive): faz o semanal também.
    [ -z "$(rclone lsf --dirs-only "$REMOTE/$nome/semanal" 2>/dev/null | head -1)" ] && semanal=1
    # SO_DIARIO=1: só bancos, n8n e definições (a 1ª cópia de dia; os volumes vão às 04:30).
    [ "${SO_DIARIO:-0}" = 1 ] && semanal=0
    man="$TMP_RODAR/$nome.txt"; : > "$man"; : > "$man.erros"
    echo "# backup de $nome ($ip) em $(date '+%F %T') — semanal: $semanal" >> "$man"
    if guardar "$nome" "$ip" "$semanal" "$man"; then
      limpar_antigos "$REMOTE/$nome/diario" "$MANTER_DIAS"
      limpar_antigos "$REMOTE/$nome/semanal" "$MANTER_SEMANAS"
    else
      todas_ok=0
      resumo="$resumo
$nome: $(grep -c '^FALHA' "$man") falha(s) — $(grep '^FALHA' "$man" | head -3 | awk '{print $2}' | tr '\n' ' ')"
    fi
    [ -s "$man.erros" ] && { echo "# mensagens de erro:" >> "$man"; tail -c 3000 "$man.erros" >> "$man"; }
    rclone copyto "$man" "$REMOTE/$nome/diario/$(date +%F)/MANIFESTO.txt" "${RCLONE_OPTS[@]}" >/dev/null 2>&1 || true
    { sed 's/^/   /' "$man" | grep -vE '^   ok ' | head -12; } || true
  done
  if [ "$todas_ok" = 1 ]; then
    log "fim ok"
    alerta --resolvido backup-vps-falhou "✅ Backup de todas as VPS voltou a funcionar."
  else
    log "fim COM FALHAS"
    alerta --chave backup-vps-falhou "❌ BACKUP DAS VPS com falha:$resumo
Detalhe no Drive: backup-vps/<vps>/diario/$(date +%F)/MANIFESTO.txt"
    exit 1
  fi
}

cmd_receber() { # <vps> <diario|semanal> <item>  — o conteúdo do item vem pela entrada padrão
  local nome=${1:-} freq=${2:-} item=${3:-} arq bytes t0
  case "$nome" in *[!A-Za-z0-9._-]*|"") die "nome de vps inválido" ;; esac
  case "$freq" in diario|semanal) ;; *) die "use diario ou semanal" ;; esac
  case "$item" in *[!A-Za-z0-9._-]*|"") die "nome de item inválido" ;; esac
  mkdir -p "$SPOOL"; chmod 700 "$SPOOL"
  arq=$(nome_do_arquivo "$item"); t0=$(date +%s)
  TMP_RECEBER="$SPOOL/$nome.$arq.parcial"; trap 'rm -f "$TMP_RECEBER"' EXIT   # global: o trap roda fora da função
  espaco_para 0 || die "sem espaço no disco da produção"
  cat > "$TMP_RECEBER"
  if bytes=$(enviar_arquivo "$TMP_RECEBER" "$REMOTE/$nome/$freq/$(date +%F)/$arq"); then
    echo "ok $freq $item $(( bytes / 1048576 ))MB $(( $(date +%s) - t0 ))s"
  else
    echo "FALHA $item ${bytes:-0}B $(( $(date +%s) - t0 ))s (o envio ao Drive falhou, ou veio vazio)"; exit 1
  fi
}

cmd_instalar() {
  [ -f "$APP/ops/vps-backup-exportar" ] || die "falta $APP/ops/vps-backup-exportar"
  install -m 700 "$APP/ops/vps-backup-exportar" "$EXPORTADOR"
  [ -f "$CHAVE" ] || die "a chave ainda não existe: rode antes os dois comandos que levam a chave pública às outras VPS"
  echo "== Conferindo o acesso às outras VPS (só a lista)"
  local par nome ip n ok=1
  for par in $ALVOS; do
    nome=${par%%=*}; ip=${par#*=}
    if n=$(ssh_alvo "$ip" lista 2>&1 | grep -cE '^(diario|semanal) '); then
      echo "   $nome ($ip): ok, $n item(ns) para guardar"
    else
      echo "   $nome ($ip): NÃO consegui entrar (o instalador dessa VPS já foi rodado?)"; ok=0
    fi
  done
  [ "$ok" = 1 ] || die "resolva o acesso acima e rode de novo. Nada foi agendado."
  cat > /etc/systemd/system/hermes-backup-vps.service <<EOF
# Backup de todas as VPS para o Google Drive. Instalado por ops/vps/backup-todas/backup-vps.sh instalar.
[Unit]
Description=Backup de todas as VPS para o Google Drive
After=network-online.target

[Service]
Type=oneshot
ExecStart=$APP/ops/backup-vps.sh rodar
Nice=19
IOSchedulingClass=idle
TimeoutStartSec=10h
EOF
  cat > /etc/systemd/system/hermes-backup-vps.timer <<EOF
# Todo dia às 04:30 (depois do backup do Hermes, das 03:30). Persistent: se a VPS estava desligada, roda ao ligar.
[Unit]
Description=Backup de todas as VPS - diario as 04:30

[Timer]
OnCalendar=*-*-* 04:30:00
RandomizedDelaySec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload
  systemctl enable --now hermes-backup-vps.timer >/dev/null
  echo "== Agendado: todo dia às 04:30. Próxima: $(systemctl list-timers hermes-backup-vps.timer --no-pager | sed -n 2p | awk '{print $1, $2, $3}')"
  echo "== Disparando a PRIMEIRA cópia agora, em segundo plano e devagar (para não atrapalhar as ligações):"
  echo "   só bancos, n8n e definições. Os volumes e pastas (~45 GB) vão sozinhos na madrugada, às 04:30."
  systemctl reset-failed hermes-backup-vps-primeira.service >/dev/null 2>&1 || true
  systemd-run --quiet --unit=hermes-backup-vps-primeira --description="Backup das VPS - primeira copia" \
    --property=Nice=19 --setenv=SO_DIARIO=1 --setenv=BWLIMIT=8M "$APP/ops/backup-vps.sh" rodar
  echo "   Pode fechar este terminal. Para acompanhar:  ssh hermes-prod /opt/hermes-call/ops/backup-vps.sh estado"
}

cmd_estado() {
  echo "agendamento: $(systemctl is-enabled hermes-backup-vps.timer 2>/dev/null || echo 'não instalado') | agora: $(systemctl is-active hermes-backup-vps.service 2>/dev/null || true) | última: $(systemctl show -p Result,ExecMainExitTimestamp --value hermes-backup-vps.service 2>/dev/null | tr '\n' ' ')"
  echo "primeira cópia (de dia): $(systemctl is-active hermes-backup-vps-primeira.service 2>/dev/null || true)"
  { journalctl -u hermes-backup-vps.service -u hermes-backup-vps-primeira.service --no-pager -o cat -n 10 2>/dev/null | cut -c1-160 | sed 's/^/   /'; } || true
  local par nome
  for par in "$LOCAL=local" $ALVOS; do
    nome=${par%%=*}
    echo "$nome no Drive: $(rclone size "$REMOTE/$nome" 2>/dev/null | tr '\n' ' ' | sed -E 's/\([0-9]+ Byte\)//') | diários: $(rclone lsf --dirs-only "$REMOTE/$nome/diario" 2>/dev/null | tr -d / | tr '\n' ' ')| semanais: $(rclone lsf --dirs-only "$REMOTE/$nome/semanal" 2>/dev/null | tr -d / | tr '\n' ' ')"
  done
}

case "${1:-}" in
  chave-publica) cmd_chave_publica ;;
  instalar) cmd_instalar ;;
  rodar) cmd_rodar ;;
  receber) shift; cmd_receber "$@" ;;
  estado) cmd_estado ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac

#!/usr/bin/env bash
# configurar-backup-drive.sh — manda o backup diário do Hermes Call também para o GOOGLE DRIVE.
# Roda NA VPS, pela DONA, num terminal DO PC DELA (o -L é o que deixa o Google "voltar" para cá):
#
#     ssh -t -L 53682:127.0.0.1:53682 hermes-prod /opt/hermes-call/ops/configurar-backup-drive.sh
#
# Por que é a dona que roda: é ela que entra na conta do Google e autoriza. O agente não entra em
# conta de ninguém. A autorização fica guardada só neste servidor (/root/.config/rclone/rclone.conf).
#
# O que faz:
#   1. instala o rclone (programa de cópia) se não tiver;
#   2. abre a autorização do Google: aparece um link, a dona abre no navegador do PC, entra na
#      conta e clica em Permitir. O acesso pedido é o MÍNIMO (drive.file): o rclone só enxerga os
#      arquivos que ele mesmo criar, não o resto do Drive;
#   3. grava RCLONE_REMOTE em /etc/hermes-call/backup.env (o hermes-backup.sh já sabe usar);
#   4. roda um backup agora e mostra o que chegou no Drive.
# Os backups vão para a pasta "hermes-call-backup" do Drive. Têm dados de clientes e as chaves das
# linhas do WhatsApp: proteja a conta do Google com verificação em duas etapas.
# Para parar de mandar:  configurar-backup-drive.sh desligar   (não apaga nada do Drive)
set -euo pipefail

REMOTE=hermes-drive
PASTA=hermes-call-backup
CONF=/etc/hermes-call/backup.env

die() { echo; echo "PAROU: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "rode como root"

if [ "${1:-}" = "desligar" ]; then
  [ -f "$CONF" ] && sed -i -E '/^RCLONE_REMOTE=/d' "$CONF"
  echo "Backup volta a ficar só na VPS. O que já está no Google Drive continua lá."
  exit 0
fi

[ -t 0 ] || die "rode num terminal de verdade:  ssh -t -L 53682:127.0.0.1:53682 hermes-prod /opt/hermes-call/ops/configurar-backup-drive.sh"

echo "== Backup do Hermes Call no Google Drive"
if ! command -v rclone >/dev/null; then
  echo "== Instalando o rclone (programa de cópia), pelo instalador do sistema"
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq rclone >/dev/null || die "não consegui instalar o rclone (apt-get install rclone)."
fi
echo "   rclone: $(rclone version | head -1)"

# Autorização que ficou pela metade (terminal fechado antes de clicar em Permitir) não serve: refaz.
REMOTES=$(rclone listremotes 2>/dev/null || true)
if grep -qxF "$REMOTE:" <<< "$REMOTES" && ! rclone lsd "$REMOTE:" >/dev/null 2>&1; then
  echo "== Havia uma autorização do Google incompleta; começando de novo"
  rclone config delete "$REMOTE" >/dev/null 2>&1 || true
fi
REMOTES=$(rclone listremotes 2>/dev/null || true)
if grep -qxF "$REMOTE:" <<< "$REMOTES"; then
  echo "== A autorização do Google já existia e funciona"
else
  cat <<EOF

== AUTORIZAR NO GOOGLE
   Vai aparecer um link que começa com  http://127.0.0.1:53682/auth
   1. Copie o link e abra no navegador DESTE PC (o mesmo onde este terminal está aberto).
   2. Entre na conta do Google onde quer guardar os backups.
   3. Clique em Permitir. Aparece "Success!" e este terminal continua sozinho.
   ENQUANTO ISSO ESTE TERMINAL FICA PARADO em "Waiting for code...": é normal, ele está esperando você.
   (Se a página não abrir, você entrou sem o "-L 53682:127.0.0.1:53682" no comando: saia e entre de novo.)

EOF
  rclone config create "$REMOTE" drive scope=drive.file >/dev/null || die "a autorização não terminou. Rode de novo."
fi

echo "== Testando o acesso ao Drive"
rclone mkdir "$REMOTE:$PASTA" || die "não consegui criar a pasta no Drive. Apague a autorização (rclone config delete $REMOTE) e rode de novo."
echo "teste $(date '+%F %T')" | rclone rcat "$REMOTE:$PASTA/LEIA-ME.txt" || die "não consegui gravar no Drive."
echo "   pasta \"$PASTA\" criada no Google Drive."

mkdir -p "$(dirname "$CONF")"; touch "$CONF"; chmod 600 "$CONF"
sed -i -E '/^RCLONE_REMOTE=/d' "$CONF"
printf 'RCLONE_REMOTE=%s:%s\n' "$REMOTE" "$PASTA" >> "$CONF"
echo "== Configurado: o backup das 03:30 passa a ir também para o Drive"

echo "== Rodando um backup agora (a primeira cópia leva alguns minutos; não feche o terminal)"
if systemctl start hermes-backup.service; then
  echo "   backup terminou sem erro."
else
  echo "   O BACKUP TERMINOU COM ERRO. Últimas linhas:"
  journalctl -u hermes-backup.service -n 15 --no-pager -o cat | cut -c1-200
  die "confira com o agente antes de confiar no backup do Drive."
fi
echo "== O que está no Google Drive agora:"
rclone lsd "$REMOTE:$PASTA" 2>/dev/null | awk '{print "   pasta " $NF}'
echo "   tamanho: $(rclone size "$REMOTE:$PASTA" 2>/dev/null | tr '\n' ' ')"
echo
echo "PRONTO. Avise o agente: ele confere e faz o teste de recuperar um backup do Drive na bancada."

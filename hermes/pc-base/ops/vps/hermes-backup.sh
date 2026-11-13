#!/usr/bin/env bash
# hermes-backup.sh — backup DIÁRIO do Hermes Call. Roda NA VPS de produção pelo timer
# systemd hermes-backup.timer (03:30). Instalado em /opt/hermes-call/ops/ por
# ops/vps/instalar-operacao.sh. Pode rodar à mão:  systemctl start hermes-backup.service
#
# Cada execução = uma pasta /var/backups/hermes-call/diario/hermes-AAAAMMDD-HHMMSS/ com:
#   db/<banco>.dump      pg_dump -Fc de TODOS os bancos wacalls_* (wacalls_main e os de
#                        cada linha WhatsApp — chaves e histórico, o que se perdeu em 24/09)
#   db/globais.sql       papéis/usuários do Postgres (pg_dumpall --globals-only)
#   gravacoes/           MP3 das ligações          ┐ INCREMENTAL: arquivo que não mudou
#   uploads/             imagens do catálogo       ├ desde o backup anterior vira hard link
#   audio-ambiente/      áudio de ambiente (dist)  ┘ (rsync --link-dest) e não ocupa espaço
#   MANIFESTO            sha256 dos dumps + contagem/tamanho das pastas
# (Antes eram 7 cópias INTEIRAS das gravações por semana; na VPS compartilhada isso podia
# encher o disco.)
#
# Retenção local: 7 diários + 4 semanais (domingo vira semanal, por hard link: sem custo
# extra). MANTER_*=0 vira 1 (nunca apaga todos).
# Cópia fora da VPS: SE RCLONE_REMOTE estiver configurado (de preferência um remote
# "crypt" do rclone — o backup tem dados pessoais e chaves do WhatsApp): os dumps vão
# por dia (retenção igual à local) e as pastas de arquivos são ESPELHADAS em
# $RCLONE_REMOTE/arquivos (rclone sync: só o que mudou trafega). Sem RCLONE_REMOTE: só
# local, e avisa (log todo dia; Telegram aos domingos).
# Falha em qualquer passo → aviso no Telegram (hermes-alerta.sh).
#
# Config opcional (fora do git): /etc/hermes-call/backup.env
#   RCLONE_REMOTE=meuremote:pasta     DEST=/var/backups/hermes-call
#   UPLOADS_DIR=/caminho  RECORDINGS_DIR=/caminho  AUDIO_DIR=/caminho   (sobrepõem a detecção)
#   MANTER_DIARIOS=7  MANTER_SEMANAIS=4  DB_PREFIXO=wacalls_
#
# Idempotente: trava (flock) contra execução dupla; cada execução cria uma pasta nova e a
# retenção apaga as mais antigas. Não para o serviço nem mexe no banco.
set -Eeuo pipefail

SVC=hermes-call
APP=/opt/hermes-call
ALERTA=$APP/ops/hermes-alerta.sh
CONF=/etc/hermes-call/backup.env
# shellcheck disable=SC1090
[ -r "$CONF" ] && . "$CONF"
DEST=${DEST:-/var/backups/hermes-call}
MANTER_DIARIOS=${MANTER_DIARIOS:-7}
MANTER_SEMANAIS=${MANTER_SEMANAIS:-4}
DB_PREFIXO=${DB_PREFIXO:-wacalls_}
RCLONE_REMOTE=${RCLONE_REMOTE:-}
# Nunca 0 (apagaria todos os backups): mínimo 1.
[ "$MANTER_DIARIOS" -ge 1 ] 2>/dev/null || MANTER_DIARIOS=1
[ "$MANTER_SEMANAIS" -ge 1 ] 2>/dev/null || MANTER_SEMANAIS=1

log() { echo "[$(date '+%F %T')] $*"; }
alerta() {
  if [ -x "$ALERTA" ]; then "$ALERTA" "$@" || true
  elif [ "${1:-}" != --resolvido ]; then echo "[sem hermes-alerta] $*" >&2; fi
}

PASSO="início"
RUN=""
falhou() {
  local rc=$?
  trap - ERR
  log "FALHOU no passo: $PASSO (código $rc)"
  alerta --chave backup-falhou "❌ BACKUP DO HERMES FALHOU
Passo: $PASSO (código $rc)
Ver: journalctl -u hermes-backup -n 50"
  if [ -n "$RUN" ] && [ -d "$RUN" ]; then mv "$RUN" "$RUN.INCOMPLETO" 2>/dev/null || true; fi
  exit "$rc"
}
trap falhou ERR

cd /   # psql/pg_dump rodam como postgres; evita aviso de "could not change directory"
mkdir -p "$DEST/diario" "$DEST/semanal"
chmod 700 "$DEST"
exec 9>"$DEST/.lock"
flock -n 9 || { log "outro backup já está rodando — saindo"; exit 0; }

# ---------- onde estão os arquivos (lê a unit do serviço; backup.env sobrepõe) ----------
PASSO="descobrir caminhos"
WD=$(systemctl show "$SVC" -p WorkingDirectory --value 2>/dev/null || true)
[ -n "$WD" ] || WD=/
# Environment= da unit + os arquivos de EnvironmentFile= (ex.: segredos).
ENVS=$(systemctl show "$SVC" -p Environment --value 2>/dev/null | tr ' ' '\n' || true)
while read -r ef _; do
  ef=${ef#-}
  if [ -n "$ef" ] && [ -r "$ef" ]; then
    ENVS="$ENVS"$'\n'"$(grep -E '^[[:space:]]*[A-Z_]+=' "$ef" | sed -E 's/^[[:space:]]*//; s/"//g' || true)"
  fi
done < <(systemctl show "$SVC" -p EnvironmentFiles --value 2>/dev/null | tr ';' '\n' || true)
envdo() { echo "$ENVS" | sed -n "s/^$1=//p" | tail -1; }
abs() { case "$1" in /*) echo "$1" ;; *) echo "$WD/$1" ;; esac; }
STATIC=$(systemctl show "$SVC" -p ExecStart --value 2>/dev/null | grep -o -- '-static[= ][^ ;]*' | head -1 | sed 's/^-static[= ]//' || true)
if [ -z "${UPLOADS_DIR:-}" ]; then
  u=$(envdo HERMES_UPLOADS_DIR); [ -n "$u" ] || u=data/uploads      # padrão do servidor
  UPLOADS_DIR=$(abs "$u")
fi
if [ -z "${RECORDINGS_DIR:-}" ]; then
  RECORDINGS_DIR=$(envdo WACALLS_RECORDING_DIR); [ -n "$RECORDINGS_DIR" ] || RECORDINGS_DIR=/var/lib/hermes-call/recordings
fi
if [ -z "${AUDIO_DIR:-}" ]; then
  if [ -n "$STATIC" ]; then AUDIO_DIR="$(abs "$STATIC")/audio"; else AUDIO_DIR=$APP/dist/audio; fi
fi
log "uploads=$UPLOADS_DIR gravações=$RECORDINGS_DIR áudio=$AUDIO_DIR destino=$DEST"

# Backup completo anterior (base do incremental).
ANTERIOR=$(find "$DEST/diario" -mindepth 1 -maxdepth 1 -type d -name 'hermes-*' ! -name '*.INCOMPLETO' | sort | tail -1 || true)

# ---------- espaço em disco ----------
PASSO="checar espaço em disco"
FILTRO="left(datname, ${#DB_PREFIXO}) = '$DB_PREFIXO' AND NOT datistemplate"   # wacalls_main + wacalls_<linha>
BANCOS=$(sudo -u postgres psql -XAtc "SELECT datname FROM pg_database WHERE $FILTRO ORDER BY 1")
[ -n "$BANCOS" ] || { log "nenhum banco ${DB_PREFIXO}* encontrado"; false; }
DB_BYTES=$(sudo -u postgres psql -XAtc "SELECT COALESCE(sum(pg_database_size(datname)),0) FROM pg_database WHERE $FILTRO")
ARQ_KB=0
if [ -z "$ANTERIOR" ]; then   # 1º backup: arquivos copiados inteiros
  for d in "$UPLOADS_DIR" "$RECORDINGS_DIR" "$AUDIO_DIR"; do
    if [ -d "$d" ]; then ARQ_KB=$(( ARQ_KB + $(du -sk "$d" | cut -f1) )); fi
  done
fi
PRECISA_KB=$(( DB_BYTES / 1024 / 2 + ARQ_KB + 1024 * 1024 ))   # dumps ~metade do banco + arquivos novos + 1 GB de folga
LIVRE_KB=$(df -Pk "$DEST" | awk 'NR==2{print $4}')
if [ "$LIVRE_KB" -lt "$PRECISA_KB" ]; then
  log "espaço insuficiente: livre ${LIVRE_KB} KB, precisa ~${PRECISA_KB} KB"
  false
fi

# ---------- bancos ----------
NOME="hermes-$(date +%Y%m%d-%H%M%S)"
RUN="$DEST/diario/$NOME"
mkdir -p "$RUN/db"
for db in $BANCOS; do
  PASSO="pg_dump $db"
  sudo -u postgres pg_dump -Fc "$db" > "$RUN/db/$db.dump"
done
PASSO="pg_dumpall --globals-only"
sudo -u postgres pg_dumpall --globals-only > "$RUN/db/globais.sql"
log "bancos: $(echo "$BANCOS" | wc -l) dump(s)"

# ---------- arquivos (incremental por hard link) ----------
# copia_pasta <origem> <nome>: copia <origem>/ para $RUN/<nome>/; o que não mudou desde
# o backup anterior vira hard link para o arquivo de lá (não ocupa espaço de novo).
copia_pasta() {
  local src=$1 nome=$2
  if [ ! -d "$src" ]; then log "sem pasta $nome ($src)"; return 0; fi
  mkdir -p "$RUN/$nome"
  if command -v rsync >/dev/null; then
    if [ -n "$ANTERIOR" ] && [ -d "$ANTERIOR/$nome" ]; then
      rsync -a --link-dest="$ANTERIOR/$nome" "$src/" "$RUN/$nome/"
    else
      rsync -a "$src/" "$RUN/$nome/"
    fi
  else
    # Sem rsync: parte do anterior por hard link e copia por cima só o que é mais novo.
    if [ -n "$ANTERIOR" ] && [ -d "$ANTERIOR/$nome" ]; then cp -al "$ANTERIOR/$nome/." "$RUN/$nome/"; fi
    cp -a -u "$src/." "$RUN/$nome/"
  fi
}
PASSO="cópia das gravações";           copia_pasta "$RECORDINGS_DIR" gravacoes
if [ -d /tmp/wacalls-recordings ]; then  # local antigo (até migrar)
  PASSO="cópia das gravações antigas (/tmp)"; copia_pasta /tmp/wacalls-recordings gravacoes-tmp-antigo
fi
PASSO="cópia dos uploads";             copia_pasta "$UPLOADS_DIR" uploads
PASSO="cópia do áudio de ambiente";    copia_pasta "$AUDIO_DIR" audio-ambiente

PASSO="manifesto"
{
  ( cd "$RUN" && sha256sum db/* )
  for d in gravacoes gravacoes-tmp-antigo uploads audio-ambiente; do
    if [ -d "$RUN/$d" ]; then echo "$d: $(find "$RUN/$d" -type f | wc -l) arquivo(s), $(du -sh --apparent-size "$RUN/$d" | cut -f1)"; fi
  done
  echo "novo neste backup: $(du -sh "$RUN" | cut -f1) (o resto é hard link do anterior)"
} > "$RUN/MANIFESTO"
chmod -R go-rwx "$RUN"
log "backup local pronto: $RUN"

# ---------- semanal (domingo) ----------
SEMANAL=0
if [ "$(date +%u)" = 7 ]; then
  PASSO="cópia semanal"
  cp -al "$RUN" "$DEST/semanal/$NOME"
  SEMANAL=1
fi

# ---------- retenção local ----------
PASSO="retenção local"
manter() {   # manter <pasta> <quantos>: apaga os backups completos mais antigos além de N
  find "$1" -mindepth 1 -maxdepth 1 -type d -name 'hermes-*' ! -name '*.INCOMPLETO' | sort | head -n -"$2" | xargs -r rm -rf
}
manter "$DEST/diario" "$MANTER_DIARIOS"
manter "$DEST/semanal" "$MANTER_SEMANAIS"
# Restos de execuções que falharam: somem depois de 2 dias.
find "$DEST/diario" -mindepth 1 -maxdepth 1 -type d -name '*.INCOMPLETO' -mtime +1 -exec rm -rf {} +

# ---------- cópia fora da VPS ----------
if [ -n "$RCLONE_REMOTE" ]; then
  command -v rclone >/dev/null || { PASSO="rclone não instalado (RCLONE_REMOTE=$RCLONE_REMOTE)"; false; }
  PASSO="rclone: dumps do dia"
  rclone copy "$RUN/db" "$RCLONE_REMOTE/diario/$NOME/db" --transfers 2 --retries 3
  rclone copy "$RUN/MANIFESTO" "$RCLONE_REMOTE/diario/$NOME/" --retries 3
  if [ $SEMANAL = 1 ]; then
    PASSO="rclone: dumps semanais"
    rclone copy "$RUN/db" "$RCLONE_REMOTE/semanal/$NOME/db" --transfers 2 --retries 3
  fi
  PASSO="rclone: espelho dos arquivos"
  for d in gravacoes uploads audio-ambiente; do
    if [ -d "$RUN/$d" ]; then rclone sync "$RUN/$d" "$RCLONE_REMOTE/arquivos/$d" --transfers 2 --retries 3; fi
  done
  PASSO="retenção no remoto"
  rclone delete "$RCLONE_REMOTE/diario" --min-age "$(( MANTER_DIARIOS + 1 ))d" || true
  rclone delete "$RCLONE_REMOTE/semanal" --min-age "$(( MANTER_SEMANAIS * 7 + 1 ))d" || true
  rclone rmdirs "$RCLONE_REMOTE/diario" --leave-root || true
  rclone rmdirs "$RCLONE_REMOTE/semanal" --leave-root || true
  log "cópia fora da VPS ok: $RCLONE_REMOTE"
else
  log "AVISO: RCLONE_REMOTE não configurado — backup só no disco da VPS (perde-se junto com ela)"
  if [ "$(date +%u)" = 7 ]; then
    alerta --chave backup-sem-remoto "⚠️ BACKUP DO HERMES só está no disco da VPS (RCLONE_REMOTE não configurado em $CONF). Se a VPS cair, o backup cai junto."
  fi
fi

alerta --resolvido backup-falhou "✅ Backup do Hermes voltou a funcionar ($NOME)."
log "fim ok"

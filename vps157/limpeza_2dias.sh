#!/bin/bash
# Limpeza automatica da VPS 157 a cada 2 dias (criado 26/10/2026).
# So mexe em lixo regeneravel. NUNCA toca: n8n (contêineres, volumes, /root/recovery),
# OmniRoute (/opt/omniroute*, imagens omniroute:*), volumes do Docker,
# /opt/atlas, /opt/recap_worker, /opt/vps-redroid, contêineres/imagens redroid, eclipse-temurin (ativador usa).
# Backups do OmniRoute (data/db_backups e /root/omniroute-backups) nao sao apagados: vao pro Drive
# (manhwa-drive:vps157-arquivo/omniroute/...) pelo mover_drive.sh, que confere antes de apagar o local.
# Agendado em /etc/cron.d/limpeza-vps-2dias (04:50, dias pares) e /etc/cron.d/limpeza-vps-disco (de hora em hora,
# so roda se o disco passar de 85%). Simular: SIMULAR=1 bash limpeza_2dias.sh
# Limites (29/10, pedido do dono; o que passa vai pro Drive, nada some):
#   video-oficina: so a imagem em uso | omniroute: a em uso + 1 pra voltar atras |
#   copias do banco do OmniRoute antes de mudanca (/opt/omniroute/backup_storage_*.sqlite): so a mais nova |
#   log de container > 100 MB: copia .gz pro Drive e esvazia.
# NUNCA "docker container prune" aqui: os redroid parados sao de proposito (29/10 apagou e teve de recriar).
set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
SIMULAR=${SIMULAR:-0}
LOG=/opt/limpeza-vps/limpeza.log
exec 9>/run/limpeza_vps.lock
flock -n 9 || { echo "ja tem uma limpeza rodando"; exit 1; }
[ "$SIMULAR" = 1 ] || exec >>"$LOG" 2>&1

livre() { df -BM / | awk 'NR==2{print $4}'; }
faz() { echo "  > $*"; [ "$SIMULAR" = 1 ] || eval "$@"; }
echo "===== $(date '+%F %T') inicio (simular=$SIMULAR) livre=$(livre)"

# 1) journal do sistema: guarda 300 MB
faz "journalctl --vacuum-size=300M >/dev/null 2>&1"

# 2) cache do apt, npm e pip do root
faz "apt-get clean"
faz "rm -rf /root/.npm/_cacache /root/.cache/pip"

# 3) /tmp: arquivos e pastas sem mexer ha mais de 2 dias (nao toca sockets/locks do sistema)
find /tmp -mindepth 1 -maxdepth 1 -mtime +2 \
  ! -name '.X11-unix' ! -name '.ICE-unix' ! -name 'systemd-private-*' ! -name 'tmux-*' ! -name 'snap-private-tmp' ! -name '.font-unix' ! -name '.XIM-unix' \
  -printf '  tmp: %p\n' 2>/dev/null
[ "$SIMULAR" = 1 ] || find /tmp -mindepth 1 -maxdepth 1 -mtime +2 \
  ! -name '.X11-unix' ! -name '.ICE-unix' ! -name 'systemd-private-*' ! -name 'tmux-*' ! -name 'snap-private-tmp' ! -name '.font-unix' ! -name '.XIM-unix' \
  -exec rm -rf {} + 2>/dev/null

# 4) contêineres parados ha mais de 2 dias, so de tarefas antigas do swarm (video-oficina, fluxia, traefik)
for c in $(docker ps -a --filter status=exited --format '{{.Names}}' | grep -E '^(video-oficina|fluxia_fluxia|traefik_traefik)\.1\.'); do
  fim=$(docker inspect -f '{{.State.FinishedAt}}' "$c" | cut -c1-19)
  if [ "$(date -d "$fim" +%s 2>/dev/null || echo 0)" -lt "$(date -d '-2 days' +%s)" ]; then faz "docker rm $c >/dev/null"; fi
done

# 5) imagens video-oficina e omniroute que nenhum container usa vao pro Drive (passo 8) e saem da VPS.
#    video-oficina guarda so a em uso; omniroute guarda a em uso + a mais nova das outras.
ARGS=()
EM_USO=$(docker ps -aq --no-trunc | xargs -r docker inspect -f '{{.Image}}' 2>/dev/null | sort -u)
for repo in video-oficina omniroute; do
  guarda=0; [ $repo = omniroute ] && guarda=1
  for id in $(docker images "$repo" --no-trunc --format '{{.CreatedAt}}|{{.ID}}' | sort -r | cut -d'|' -f2 | awk '!v[$0]++'); do
    echo "$EM_USO" | grep -qx "$id" && continue
    if [ $guarda -gt 0 ]; then guarda=$((guarda-1)); echo "  imagem guardada (voltar atras): $id"; continue; fi
    ARGS+=("imagem:$id" imagens/$repo)
  done
done

# 6) imagens sem nome (dangling) e cache de build com mais de 2 dias
faz "docker image prune -f >/dev/null"
faz "docker builder prune -f --filter until=48h >/dev/null"

# 7) logs de contêiner acima de 100 MB: copia .gz em envio/ (vai pro Drive no passo 8) e esvazia o arquivo
ENVIO=/opt/limpeza-vps/envio
mkdir -p "$ENVIO"
for f in $(find /var/lib/docker/containers -name '*-json.log' -size +100M 2>/dev/null); do
  nome=$(docker inspect -f '{{.Name}}' "$(basename "$(dirname "$f")")" 2>/dev/null | tr -d / | cut -d. -f1)
  gz="$ENVIO/${nome:-sem_nome}_$(date +%Y%m%d_%H%M).log.gz"
  faz "pigz -c $f > $gz && truncate -s 0 $f"
done

# 8) backups do OmniRoute com mais de 2 h vao pro Drive (a limpeza semanal dele cria um novo todo domingo 04:30)
for f in $(find /opt/omniroute/data/db_backups -maxdepth 1 -type f -name '*.sqlite' -mmin +120 2>/dev/null); do
  ARGS+=("$f" omniroute/db_backups)
done
for d in $(find /root/omniroute-backups -mindepth 1 -maxdepth 1 -mmin +120 2>/dev/null); do
  ARGS+=("$d" omniroute/root-omniroute-backups)   # pasta vira <nome>.tar.gz la
done
# copias do banco feitas antes de mudar algo: fica so a mais nova
for f in $(ls -t /opt/omniroute/backup_storage_*.sqlite 2>/dev/null | tail -n +2); do
  ARGS+=("$f" omniroute/antes_mudanca)
done
for f in $(find "$ENVIO" -maxdepth 1 -type f -name '*.gz' 2>/dev/null); do
  ARGS+=("$f" logs_containers)
done
if [ ${#ARGS[@]} -gt 0 ]; then
  printf '  drive: %s -> %s\n' "${ARGS[@]}"
  [ "$SIMULAR" = 1 ] || /opt/limpeza-vps/mover_drive.sh "${ARGS[@]}"
fi

echo "===== $(date '+%F %T') fim livre=$(livre)"

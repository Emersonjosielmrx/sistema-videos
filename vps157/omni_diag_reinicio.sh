#!/bin/bash
# So leitura. Investiga os 3 reinicios do omniroute de 21/11 (22:07, 22:10 e 22:11 UTC), mostra o cron semanal e a saude agora.
export LC_ALL=C
C=omniroute
mask() { sed -E 's/(sk-|eyJ)[A-Za-z0-9_.-]{12,}/\1<mascarado>/g; s/[A-Fa-f0-9]{32,}/<hex>/g'; }

echo "agora UTC: $(date -u '+%F %T') | hora da VPS: $(date '+%T')"

echo "== conteiner =="
docker inspect -f 'inicio={{.State.StartedAt}} reinicios={{.RestartCount}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} saude={{.State.Health.Status}} politica={{.HostConfig.RestartPolicy.Name}}' $C
echo "healthcheck:"; docker inspect -f '{{json .Config.Healthcheck}}' $C | cut -c1-300
echo "entrypoint/cmd:"; docker inspect -f '{{json .Config.Entrypoint}} {{json .Config.Cmd}}' $C | cut -c1-300
echo "autoheal/watchtower:"; docker ps --format '{{.Names}} {{.Image}}' | grep -iE 'autoheal|watchtower|heal' || echo "nenhum"

echo "== eventos do docker 22:05-22:12 UTC =="
timeout 20 docker events --since 2026-11-21T22:05:00Z --until 2026-11-21T22:12:30Z \
  --filter container=$C --filter event=kill --filter event=die --filter event=stop \
  --filter event=restart --filter event=start \
  --format '{{.Time}} {{.Action}} exit={{index .Actor.Attributes "exitCode"}} sig={{index .Actor.Attributes "signal"}}' 2>&1 \
  | while read -r t rest; do
      case "$t" in [0-9]*) echo "$(date -u -d "@$t" +%T)Z $rest";; *) echo "$t $rest";; esac
    done | head -20

echo "== log do app logo antes de cada saida (UTC) =="
for t in 22:07:35 22:10:35 22:11:08; do
  e=$(date -u -d "2026-11-21 $t UTC" +%s)
  ini=$(date -u -d "@$((e-90))" +%FT%TZ)
  fim=$(date -u -d "@$((e+3))" +%FT%TZ)
  echo "--- saida as $t (log de $ini a $fim) ---"
  docker logs --since "$ini" --until "$fim" $C 2>&1 \
    | grep -E '"level":(50|60)|WAL|[Ss]hutdown|SIGTERM|SIGINT|[Ff]atal|[Uu]ncaught|[Uu]nhandled|guard|watchdog|stall|lag|exiting' \
    | mask | cut -c1-240 | tail -6
  echo "   (ultimas 3 linhas, sem filtro)"
  docker logs --since "$ini" --until "$fim" $C 2>&1 | mask | cut -c1-200 | tail -3
done

echo "== cron semanal =="
grep -v -E '^#|^$' /etc/cron.d/omniroute-limpeza
echo "--- limpeza_omniroute.sh ---"
mask < /opt/omniroute/limpeza_omniroute.sh | cut -c1-200 | sed -n '1,90p'
echo "limpar_contas.py esta agendado?"
grep -rIl 'limpar_contas' /etc/cron.d /etc/cron.daily /etc/cron.weekly /etc/crontab /var/spool/cron /etc/systemd/system 2>/dev/null || echo "nao esta em cron nem systemd"
echo "timers:"; systemctl list-timers --all --no-pager 2>/dev/null | grep -iE 'omni|limpeza' || echo "nenhum"

echo "== envio do backup antigo pro Drive =="
echo "servico: $(systemctl is-active mover-bkp-omni-21nov.service 2>&1)"
tail -n 3 /opt/limpeza-vps/drive.log | cut -c1-200
ls -la /opt/omniroute/data/storage.sqlite.bkp_1411_agopus 2>&1 | cut -c1-160

echo "== saude agora =="
docker inspect -f 'saude={{.State.Health.Status}} reinicios={{.RestartCount}} inicio={{.State.StartedAt}}' $C
echo "locked nos ultimos 10 min: $(docker logs --since 10m $C 2>&1 | grep -c 'database is locked')"
uptime
df -h / | tail -1
curl -s -o /dev/null -w 'resposta http=%{http_code} tempo=%{time_total}s\n' http://localhost:20128/v1/models

echo "== sobras dos agentes de revisao e teste e meus scripts (so lista, nada e apagado) =="
find /root /tmp /opt/omniroute -maxdepth 1 -type f \( -name 'rev_*' -o -name 't_db*' -o -name 't_gw*' -o -name 'omni_*' \) -printf '%p %s bytes\n' 2>/dev/null | head -20
echo fim

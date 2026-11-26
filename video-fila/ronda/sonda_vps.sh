#!/bin/bash
# /mnt/win-bootcamp/claude-central/ronda/sonda_vps.sh - roda NA VPS (enviado via stdin pelo ronda.sh). Somente leitura.
echo "disco $(df -h / | awk 'NR==2{print $5}') | ram livre $(free -m | awk 'NR==2{print $7}') MB"
systemctl --failed --no-legend --plain 2>/dev/null | awk '{print "  !! servico falho: "$1}'
docker ps -a --filter status=exited --format '{{.Names}} {{.Status}}' 2>/dev/null | grep -E '(second|minute|hour)s? ago' | sed 's/^/  !! container parou recente: /' | head -8
for l in /var/log/backup_v2.log /var/log/backup_cas*.log /var/log/cas_backup*.log; do
  [ -f "$l" ] && tail -30 "$l" | grep -i -E 'erro|error|denied|fail' | tail -1 | sed "s|^|  !! $(basename $l): |" | cut -c1-160
done

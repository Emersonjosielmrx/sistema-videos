#!/bin/bash
# Retrato da produção de recap longo (rodar no Git Bash). Plano: producao/COLAB_RECAP_LONGO.md
cd /d/recapd-ambientes/producao/colab
RC=/d/tools/rclone.exe
echo "=== $(date '+%d/%m %H:%M')"
echo "--- alimentador"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*cliente.py*' } | ForEach-Object { (\$_.CommandLine -split 'cliente.py')[1].Trim() }"
tail -3 alimentar.log; tail -2 alimentar.err 2>/dev/null | grep -iE "error|traceback" || true
echo "--- token: $(tail -1 token_loop.log)"
echo "--- vivos (min atrás)"
for f in $($RC lsf manhwa-drive:colab_recap --files-only --include 'vivo*.json'); do
  em=$($RC cat manhwa-drive:colab_recap/$f | grep -o '"em": *"[^"]*"' | cut -d'"' -f4)
  echo "  $f: $(( ($(date +%s) - $(date -d "$em" +%s)) / 60 ))"
done
echo "--- fila"
for p in $($RC lsf manhwa-drive:colab_recap/fila --dirs-only); do
  echo "  $p $($RC lsf manhwa-drive:colab_recap/fila/$p | grep -E 'pronto|erro|em_andamento' | tr '\n' ' ')"
  $RC cat manhwa-drive:colab_recap/fila/${p}em_andamento.json 2>/dev/null | grep -o '"por": *"[^"]*"' | sed 's/^/     /'
done
echo "--- prontos no Drive: $($RC lsf manhwa-drive:videos-backup/anime/1_youtube_pendente --dirs-only | wc -l)"
echo "--- kaggle"
/d/hipercool-videos/venv/Scripts/python.exe kaggle_lancar.py status 2>&1 | tail -1
echo "--- vps"
for h in hermes-staging hermes-prod hermes-bloqueio; do
  echo "  $h: $(timeout 40 ssh -o BatchMode=yes -o ConnectTimeout=15 $h "docker inspect -f '{{.State.Status}} reinicios={{.RestartCount}}' recap_worker; docker logs --tail 2 recap_worker 2>&1 | tail -1 | cut -c1-140" </dev/null 2>&1 | tr '\n' ' ')"
done

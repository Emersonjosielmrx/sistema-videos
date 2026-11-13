#!/usr/bin/env bash
# Inicia a BANCADA com o ambiente da produção + as diferenças da bancada.
set -euo pipefail
PID=$(systemctl show hermes-call -p MainPID --value)
[ -n "$PID" ] && [ "$PID" != 0 ] || { echo "produção fora do ar: bancada não inicia"; exit 1; }
while IFS= read -r -d '' kv; do
  case "$kv" in
    INVOCATION_ID=*|JOURNAL_STREAM=*|SYSTEMD_EXEC_PID=*|MANAGERPID=*|NOTIFY_SOCKET=*) ;;
    *) export "$kv" ;;
  esac
done < /proc/$PID/environ
set -a; . /etc/hermes-bancada/bancada.env; set +a
exec /opt/hermes-bancada/hermes-call -static /opt/hermes-bancada/dist -addr 127.0.0.1:8091

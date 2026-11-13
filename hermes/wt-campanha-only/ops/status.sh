#!/usr/bin/env bash
# ops/status.sh — mostra a versão no ar na produção, as versões guardadas e o relógio
# (relógio fora do NTP faz o servidor julgar mal a idade das ligações recebidas).
set -euo pipefail
ssh -o BatchMode=yes -o ConnectTimeout=15 hermes-prod \
  "/opt/hermes-call/releases/hermes-release.sh status; echo; /opt/hermes-call/releases/hermes-release.sh listar; echo; echo \"Relógio sincronizado (NTP): \$(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo desconhecido)\""

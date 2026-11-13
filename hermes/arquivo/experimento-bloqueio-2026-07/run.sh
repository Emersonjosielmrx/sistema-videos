#!/bin/bash
# Hermes Call Anexo - Investigation launcher
# Roda dentro de /opt/hermes-call-anexo/
# USO: ./run.sh start | stop | status | logs | qr-now
set -e
DIR=/opt/hermes-call-anexo
BIN=$DIR/bin/investigation
LOG=$DIR/data/investigation.log
PIDFILE=$DIR/data/investigation.pid
DB=$DIR/data/investigation.db

mkdir -p "$DIR/data"

case "$1" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "already running pid=$(cat $PIDFILE)"
      exit 1
    fi
    cd "$DIR/data"
    nohup env DB_PATH="$DB" "$BIN" >> "$LOG" 2>&1 &
    echo $! > "$PIDFILE"
    echo "started pid=$!"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      kill "$PID" 2>/dev/null && echo "sent SIGTERM to $PID"
      rm -f "$PIDFILE"
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "running pid=$(cat $PIDFILE)"
    else
      echo "not running"
    fi
    ;;
  logs)
    tail -f "$LOG"
    ;;
  qr-now)
    # Re-começa do zero (apaga DB) só pra gerar QR novo
    read -p "Isso apaga o DB e gera QR novo. Confirma? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
      rm -f "$DB"*
      [ -f "$PIDFILE" ] && kill $(cat "$PIDFILE") 2>/dev/null
      rm -f "$PIDFILE"
      "$0" start
      sleep 2
      tail -50 "$LOG"
    fi
    ;;
  *)
    echo "uso: $0 start | stop | status | logs | qr-now"
    exit 1
    ;;
esac

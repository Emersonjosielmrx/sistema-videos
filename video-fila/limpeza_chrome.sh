#!/bin/bash
# limpeza_chrome.sh — versão Linux do limpeza_chrome.ps1 para os notebooks (x200ma, acer), cron a cada 10 min.
# 03/11 (dona: "muitos navegadores travam antes de colocar a URL, ficam na aba nova e ficam lá sem serem eliminados —
# não pode acontecer em nenhum PC"). Só Chrome de automação (com --remote-debugging-port); o resto nunca.
#  - >= 15 min com TODAS as abas em branco (about:blank / nova aba) = travou -> fecha;
#  - >= 30 min sem responder pela porta = travou -> fecha;
#  - >= 3 h, nenhum python/node vivo cita a porta e quem abriu já morreu = esquecido -> fecha.
LOG="$HOME/limpeza_chrome.log"
L() { echo "$(date '+%F %T') $(hostname) $*" >> "$LOG"; }
fechar() {  # SIGTERM primeiro (o Chrome grava cookies e sai); 10 s depois, SIGKILL
    kill -TERM "$1" 2>/dev/null; sleep 10; kill -0 "$1" 2>/dev/null && kill -KILL "$1" 2>/dev/null
    L "fechou Chrome porta $2 pid $1: $3"
}
usos=$(ps -eo args | grep -E '^[^ ]*(python|node)' | tr '\n' ' ')
ps -eo pid=,ppid=,etimes=,args= | grep -E 'chrom(e|ium)' | grep -- '--remote-debugging-port=' | grep -v -- '--type=' |
while read -r pid ppid seg args; do
    porta=$(echo "$args" | grep -oE 'remote-debugging-port=[0-9]+' | cut -d= -f2)
    [ "$seg" -lt 900 ] && continue
    abas=$(curl -s -m 8 "http://127.0.0.1:$porta/json/list")
    if [ -z "$abas" ]; then
        sleep 3; abas=$(curl -s -m 8 "http://127.0.0.1:$porta/json/list")
    fi
    if [ -z "$abas" ]; then
        [ "$seg" -ge 1800 ] && fechar "$pid" "$porta" "travado: não responde pela porta (aberto há $((seg / 60)) min)"
        continue
    fi
    urls=$(echo "$abas" | python3 -c 'import json,sys
print("\n".join(t.get("url","") for t in json.load(sys.stdin) if t.get("type")=="page"))' 2>/dev/null)
    n=$(echo "$urls" | grep -c .)
    if [ "$n" -gt 0 ] && ! echo "$urls" | grep -qvE '^(about:blank|chrome://newtab/?|chrome://new-tab-page/?|chrome-search://local-ntp.*)$'; then
        fechar "$pid" "$porta" "travado na aba nova: $n aba(s) em branco, aberto há $((seg / 60)) min"
        continue
    fi
    [ "$seg" -lt 10800 ] && continue
    echo "$usos" | grep -qE "(^|[^0-9])$porta([^0-9]|$)" && continue
    ps -o args= -p "$ppid" 2>/dev/null | grep -qE '(python|node)' && continue
    fechar "$pid" "$porta" "esquecido: aberto há $((seg / 3600)) h e ninguém usa a porta"
done

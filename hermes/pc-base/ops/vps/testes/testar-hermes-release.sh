#!/usr/bin/env bash
# ops/vps/testes/testar-hermes-release.sh — testa a troca de versão do hermes-release.sh SEM
# VPS: carrega o script com "source" e troca systemctl/curl/journalctl/sleep por funções
# falsas que simulam versões com e sem /saude-local, linhas do WhatsApp e pânico no registro.
# Roda no PC (Git Bash) ou em qualquer Linux:   bash ops/vps/testes/testar-hermes-release.sh
#
# Cenário que motivou (04/10): voltar para uma versão SEM /saude-local "falhava" na conferência
# de linhas e a volta automática RECOLOCAVA a versão nova. Uma volta nunca pode se desfazer.
set -uo pipefail

AQUI=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$AQUI/../hermes-release.sh"
# Pasta temporária própria: TUDO do teste fica nela (nada em /opt). Sem ela, PARA — com T vazio
# os "rm -rf $T/..." apontariam pra raiz.
T=$(mktemp -d 2>/dev/null || true)
case "$T" in /*/*) [ -d "$T" ] || { echo "PAROU: mktemp falhou"; exit 1; } ;; *) echo "PAROU: mktemp falhou"; exit 1 ;; esac
trap 'rm -rf "$T"' EXIT
FALHAS=0
PASSOU=0

ok()    { PASSOU=$((PASSOU + 1)); echo "  ok   $*"; }
falha() { FALHAS=$((FALHAS + 1)); echo "  FALHOU $*"; }
confere() { # confere <descrição> <esperado> <obtido>
  if [ "$2" = "$3" ]; then ok "$1"; else falha "$1 (esperado: '$2', veio: '$3')"; fi
}

# ---------------------------------------------------------------- cenário (estado falso)
# Linhas pareadas do servidor: $T/linhas (ids) e as da administradora: $T/admin.
# Cada versão: $T/cfg/<ID> com
#   RESPONDE (1/0) e RESPONDE_APOS (s depois de subir) — /api/version;
#   SAUDE_LOCAL (1/0) — tem /saude-local (senão devolve a página do painel, como a v0.7.0);
#   CONECTA (todas | nenhuma | "ids") e CONECTA_APOS (s) — linhas conectadas depois de subir;
#   PANICO_SUBIR / PANICO_DESLIGAR (1 = escreve "panic:" no registro ao subir/desligar);
#   CHAVES ("A=1 B=true": chaves de teste ligadas) e CAMPO_CHAVES (0 = /saude-local sem o campo).
# $T/rodando = ID do processo no ar ("" = parado); $T/inicio = hora em que subiu;
# $T/relogio = relógio falso (o sleep falso avança); $T/journal = registro, uma linha por entrada.
nova_versao() { # nova_versao <ID> [VAR=valor ...]
  local id=$1; shift
  mkdir -p "$REL/$id/dist"
  echo "$id" > "$REL/$id/hermes-call"
  printf 'id=%s\ncommit=%s\nbuild=%s\n' "$id" "${id##*_}" "$id" > "$REL/$id/INFO"
  { echo "RESPONDE=1"; echo "RESPONDE_APOS=0"; echo "SAUDE_LOCAL=1"; echo "CONECTA=todas"; echo "CONECTA_APOS=0"
    echo "PANICO_SUBIR=0"; echo "PANICO_DESLIGAR=0"; echo "CHAVES="; echo "CAMPO_CHAVES=1"
    for kv in "$@"; do echo "${kv%%=*}=\"${kv#*=}\""; done; } > "$T/cfg/$id"
}

instalar_no_ar() { # instalar_no_ar <ID>: estado inicial, sem passar pelo ativar (no ar há horas)
  cp "$REL/$1/hermes-call" "$APP/hermes-call"
  rm -rf "$APP/dist"; cp -a "$REL/$1/dist" "$APP/dist"
  echo "$1" > "$REL/ATUAL"
  echo "$1" > "$T/rodando"
  echo $(( $(relogio) - 10000 )) > "$T/inicio"
}

cfg() { # cfg <ID> <VAR>
  local RESPONDE RESPONDE_APOS SAUDE_LOCAL CONECTA CONECTA_APOS PANICO_SUBIR PANICO_DESLIGAR CHAVES CAMPO_CHAVES
  # shellcheck disable=SC1090
  . "$T/cfg/$1"
  eval "echo \"\${$2}\""
}

rodando() { cat "$T/rodando" 2>/dev/null || true; }
registra() { echo "$*" >> "$T/journal"; }
relogio() { cat "$T/relogio"; }
no_ar_ha() { echo $(( $(relogio) - $(cat "$T/inicio") )); }

# json_lista a b c → ["a","b","c"]
json_lista() { local x o=""; for x in "$@"; do o="$o,\"$x\""; done; echo "[${o#,}]"; }

# ---------------------------------------------------------------- comandos falsos
sleep() { echo $(( $(relogio) + ${1%%.*} )) > "$T/relogio"; }
systemctl() {
  case "$1" in
    is-active) [ -n "$(rodando)" ] ;;
    stop)
      local r; r=$(rodando)
      if [ -n "$r" ] && [ "$(cfg "$r" PANICO_DESLIGAR)" = 1 ]; then
        registra "hermes-call[100]: panic: send on closed channel"
        registra "systemd[1]: hermes-call.service: Main process exited, code=dumped, status=6/ABRT"
      fi
      registra "systemd[1]: Stopped hermes-call.service."
      echo "" > "$T/rodando" ;;
    start)
      local id; id=$(cat "$APP/hermes-call")
      echo "$id" > "$T/rodando"
      relogio > "$T/inicio"
      registra "systemd[1]: Started hermes-call.service."
      registra "hermes-call[200]: subindo build=$id"
      if [ "$(cfg "$id" PANICO_SUBIR)" = 1 ]; then
        registra "hermes-call[200]: panic: runtime error: invalid memory address or nil pointer dereference"
      fi ;;
    restart) systemctl stop "$2"; systemctl start "$2" ;;
    *) return 0 ;;
  esac
}
curl() {
  local url="${*: -1}" r; r=$(rodando)
  [ -n "$r" ] || return 7
  [ "$(cfg "$r" RESPONDE)" = 1 ] || return 7
  [ "$(no_ar_ha)" -ge "$(cfg "$r" RESPONDE_APOS)" ] || return 7
  case "$url" in
    */api/version) echo "{\"version\":\"v0.8.0\",\"build\":\"$r\",\"channel\":\"producao\"}" ;;
    */saude-local)
      if [ "$(cfg "$r" SAUDE_LOCAL)" != 1 ]; then
        echo '<!doctype html><html><head><title>Hermes Call</title></head></html>' # painel (SPA)
        return 0
      fi
      local todas on="" fora="" adm="" x c n=0 p=0
      todas=$(cat "$T/linhas"); c=$(cfg "$r" CONECTA)
      case "$c" in todas) c=$todas ;; nenhuma) c="" ;; esac
      [ "$(no_ar_ha)" -ge "$(cfg "$r" CONECTA_APOS)" ] || c=""
      for x in $todas; do
        p=$((p + 1))
        case " $c " in *" $x "*) on="$on $x"; n=$((n + 1)) ;; *) fora="$fora $x" ;; esac
        case " $(cat "$T/admin") " in *" $x "*) adm="$adm $x" ;; esac
      done
      local ch=""
      # shellcheck disable=SC2046
      [ "$(cfg "$r" CAMPO_CHAVES)" = 1 ] && ch=",\"chaves_de_teste\":$(json_lista $(cfg "$r" CHAVES))"
      # mesmo formato do servidor (cmd/server/health_local.go, campos na ordem do struct)
      # shellcheck disable=SC2086
      echo "{\"build\":\"$r\",\"linhas_pareadas\":$p,\"linhas_conectadas\":$n,\"no_ar_s\":$(no_ar_ha),\"ids_conectadas\":$(json_lista $on),\"ids_fora\":$(json_lista $fora),\"ids_admin\":$(json_lista $adm)$ch}" ;;
    *) return 22 ;;
  esac
}
# journalctl falso: "-n1 --show-cursor" devolve a última linha + "-- cursor: <nº da linha>";
# "--after-cursor N" devolve só as linhas depois da N; sem isso (ex.: --since), tudo.
journalctl() {
  local depois="" mostra=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --after-cursor) depois=$2; shift ;;
      --show-cursor) mostra=1 ;;
    esac
    shift
  done
  if [ $mostra = 1 ]; then
    [ "${SEM_CURSOR:-0}" = 1 ] && return 0   # journalctl que não informa a posição
    local n; n=$(wc -l < "$T/journal" | tr -d ' ')
    [ "$n" -gt 0 ] || return 0
    tail -n1 "$T/journal"; echo "-- cursor: $n"; return 0
  fi
  if [ -n "$depois" ]; then tail -n +"$((depois + 1))" "$T/journal"; else cat "$T/journal"; fi
}

# ---------------------------------------------------------------- execução
preparar_ambiente() { # preparar_ambiente [ids das linhas] [ids da administradora]
  rm -rf "$T/app" "$T/cfg" "$T/journal" "$T/rodando"
  mkdir -p "$T/app/releases" "$T/cfg"
  : > "$T/journal"
  echo 100000 > "$T/relogio"
  echo "${1:-l1 l2}" > "$T/linhas"
  echo "${2:-l1}" > "$T/admin"
}

# decidido_em: segundos entre a troca e a decisão, tirado do log do script.
decidido_em() { sed -n 's/.*decidido em \([0-9]*\) s.*/\1/p' "$T/saida" | head -n1; }

# roda <subcomando...>: chama o main do script num subshell (o "die" sai só dele).
# Saída em $T/saida, código de saída em $COD.
roda() {
  ( set -euo pipefail; main "$@" ) > "$T/saida" 2>&1
  COD=$?
}

# shellcheck disable=SC1090
. "$SCRIPT"
set +e
APP=$T/app
REL=$APP/releases
agora_s() { cat "$T/relogio"; }   # depois do source: troca o relógio do script pelo falso

ANTIGA=20260925-0158_29e4e85   # estável de verdade, sem /saude-local
PROD=20261003-1200_af7413e     # v0.7.0, sem /saude-local
NOVA=20261004-1500_abc1234     # com /saude-local
OUTRA=20261005-0900_def5678    # com /saude-local

echo "== 1. publicar versão nova (com /saude-local) a partir de uma versão sem ele"
preparar_ambiente
nova_versao "$PROD" SAUDE_LOCAL=0
nova_versao "$NOVA"
instalar_no_ar "$PROD"
roda ativar "$NOVA"
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a nova" "$NOVA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a nova" "$NOVA" "$(rodando)"
grep -q "$PROD -> $NOVA OK" "$REL/HISTORICO" && ok "HISTORICO registra OK" || falha "HISTORICO sem a linha OK"

echo "== 2. publicar versão nova a partir de outra com /saude-local; linhas reconectam"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a outra" "$OUTRA" "$(cat "$REL/ATUAL")"

echo "== 3. publicar versão que não reconecta nenhuma linha (0 de 2): volta sozinha"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" CONECTA=nenhuma
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "ATUAL continua a anterior" "$NOVA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"

echo "== 4. publicar versão que não responde /api/version: volta sozinha"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" RESPONDE=0
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "ATUAL continua a anterior" "$NOVA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"

echo "== 5. ativar (publicar) uma versão SEM /saude-local saindo de uma com: pula a conferência"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$PROD" SAUDE_LOCAL=0
instalar_no_ar "$NOVA"
roda ativar "$PROD"
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a de destino" "$PROD" "$(cat "$REL/ATUAL")"
confere "processo no ar é a de destino" "$PROD" "$(rodando)"
grep -q "conferência de linhas pulada" "$T/saida" && ok "log diz que pulou a conferência" || falha "log não diz que pulou"

echo "== 6. voltar-estavel para a estável SEM /saude-local (o caso de 04/10)"
preparar_ambiente
nova_versao "$ANTIGA" SAUDE_LOCAL=0
nova_versao "$NOVA"
instalar_no_ar "$NOVA"
echo "$ANTIGA" > "$REL/ESTAVEL"
roda voltar-estavel
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a estável" "$ANTIGA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a estável (NÃO reativou a nova)" "$ANTIGA" "$(rodando)"
grep -q "$NOVA -> $ANTIGA VOLTA OK" "$REL/HISTORICO" && ok "HISTORICO registra a volta" || falha "HISTORICO sem a volta"
roda voltar-estavel
confere "rodar de novo não faz nada" "$ANTIGA" "$(rodando)"

echo "== 7. reverter.sh (ativar <ID> volta) para versão SEM /saude-local"
preparar_ambiente
nova_versao "$PROD" SAUDE_LOCAL=0
nova_versao "$NOVA"
instalar_no_ar "$NOVA"
roda ativar "$PROD" volta
confere "termina sem erro" 0 "$COD"
confere "processo no ar é a de destino (NÃO reativou a nova)" "$PROD" "$(rodando)"
# o reverter.sh sem argumento acha a "anterior" assim:
confere "reverter.sh acha a anterior no HISTORICO" "$NOVA" "$(grep ' OK$' "$REL/HISTORICO" | tail -1 | awk '{print $3}')"

echo "== 8. voltar <ID> para versão que NÃO responde: fica nela e avisa (não se desfaz)"
preparar_ambiente
nova_versao "$PROD" RESPONDE=0
nova_versao "$NOVA"
instalar_no_ar "$NOVA"
roda voltar "$PROD"
confere "termina com erro (avisa)" 1 "$COD"
confere "ATUAL é a de destino" "$PROD" "$(cat "$REL/ATUAL")"
confere "processo no ar NÃO voltou pra nova" "$PROD" "$(rodando)"
grep -q "reverter.sh $NOVA" "$T/saida" && ok "mostra o comando pra recolocar a nova" || falha "não mostrou o comando"

echo "== 9. pânico ao DESLIGAR a versão antiga não recusa a nova"
preparar_ambiente
nova_versao "$NOVA" PANICO_DESLIGAR=1
nova_versao "$OUTRA"
instalar_no_ar "$NOVA"
registra "hermes-call[100]: rodando há dias"
roda ativar "$OUTRA"
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a nova" "$OUTRA" "$(cat "$REL/ATUAL")"
grep -q "panic: send on closed channel" "$T/journal" && ok "(o pânico do desligamento está no registro)" || falha "cenário não gerou o pânico"

echo "== 10. pânico na versão NOVA: recusa e volta sozinha"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" PANICO_SUBIR=1
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "ATUAL continua a anterior" "$NOVA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"
grep -q "teve pânico/aborto" "$T/saida" && ok "log mostra o pânico" || falha "log não mostra o pânico"

echo "== 11. journalctl sem posição (sem marca): usa a hora e ainda acha o pânico da nova"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" PANICO_SUBIR=1
instalar_no_ar "$NOVA"
SEM_CURSOR=1
roda ativar "$OUTRA"
SEM_CURSOR=0
confere "termina com erro" 1 "$COD"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"

echo "== 12. 3 linhas; UMA de cliente não volta: aceita com aviso e diz qual"
preparar_ambiente "l1 l2 l3" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" CONECTA="l1 l2"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina sem erro" 0 "$COD"
confere "ATUAL é a nova" "$OUTRA" "$(cat "$REL/ATUAL")"
grep -q "não voltaram: l3" "$T/saida" && ok "log diz qual linha (l3)" || falha "log não diz qual linha"
grep -q "aviso $OUTRA: a linha l3" "$REL/HISTORICO" && ok "HISTORICO guarda o aviso" || falha "HISTORICO sem o aviso"
confere "reverter.sh ainda acha a anterior" "$NOVA" "$(grep ' OK$' "$REL/HISTORICO" | tail -1 | awk '{print $3}')"
d=$(decidido_em); if [ -n "$d" ] && [ "$d" -le 120 ]; then ok "decidiu em $d s (≤ 120)"; else falha "decidiu em '$d' s"; fi

echo "== 13. a linha da ADMINISTRADORA não volta: recusa"
preparar_ambiente "l1 l2 l3" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" CONECTA="l2 l3"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"
grep -q "a linha l1 é da administradora" "$T/saida" && ok "log explica" || falha "log não explica"

echo "== 14. DUAS linhas não voltam: recusa"
preparar_ambiente "l1 l2 l3" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" CONECTA="l1"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"

echo "== 15. linhas demoram 40 s pra voltar: espera e aceita sem aviso"
preparar_ambiente "l1 l2 l3" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" CONECTA_APOS=40
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina sem erro" 0 "$COD"
if grep -q "aviso" "$REL/HISTORICO"; then falha "não deveria ter aviso"; else ok "sem aviso"; fi

echo "== 16. pior caso de tempo: responde só aos 85 s e uma linha nunca volta: decide em ≤ 120 s"
preparar_ambiente "l1 l2 l3" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" RESPONDE_APOS=85 CONECTA="l1 l2"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina sem erro (aceita com aviso)" 0 "$COD"
d=$(decidido_em); if [ -n "$d" ] && [ "$d" -le 120 ]; then ok "decidiu em $d s (≤ 120)"; else falha "decidiu em '$d' s"; fi

echo "== 17. não reconecta nada e só responde aos 85 s: recusa em ≤ 120 s"
preparar_ambiente "l1 l2" "l1"
nova_versao "$NOVA"
nova_versao "$OUTRA" RESPONDE_APOS=85 CONECTA=nenhuma
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
d=$(decidido_em); if [ -n "$d" ] && [ "$d" -le 120 ]; then ok "decidiu em $d s (≤ 120)"; else falha "decidiu em '$d' s"; fi
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"

echo "== 18. versão nova com CHAVE DE TESTE ligada na produção: recusa e volta sozinha"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" CHAVES="HERMES_VOICE_ESPERA_ACEITE=false HERMES_TESTE_ACEITE_POR_RELAY=true"
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "termina com erro" 1 "$COD"
confere "ATUAL continua a anterior" "$NOVA" "$(cat "$REL/ATUAL")"
confere "processo no ar é a anterior" "$NOVA" "$(rodando)"
grep -q "chave(s) de TESTE ligada(s) no ambiente da PRODUÇÃO: HERMES_VOICE_ESPERA_ACEITE=false HERMES_TESTE_ACEITE_POR_RELAY=true" "$T/saida" \
  && ok "mensagem clara, com as chaves" || falha "mensagem sem as chaves"
grep -q "$NOVA -> $OUTRA FALHOU" "$REL/HISTORICO" && ok "HISTORICO registra a falha" || falha "HISTORICO sem a falha"

echo "== 19. lista de chaves vazia ou versão sem o campo: segue normal"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" CHAVES=""
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "lista vazia: termina sem erro" 0 "$COD"
preparar_ambiente
nova_versao "$NOVA"
nova_versao "$OUTRA" CAMPO_CHAVES=0
instalar_no_ar "$NOVA"
roda ativar "$OUTRA"
confere "sem o campo: termina sem erro" 0 "$COD"

echo "== 20. a VOLTA não confere chave de teste (nunca se desfaz)"
preparar_ambiente
nova_versao "$PROD" CHAVES="<SEGREDO_REMOVIDO>"
nova_versao "$NOVA"
instalar_no_ar "$NOVA"
roda voltar "$PROD"
confere "termina sem erro" 0 "$COD"
confere "processo no ar é a de destino" "$PROD" "$(rodando)"

echo
if [ "$FALHAS" -gt 0 ]; then
  echo "RESULTADO: $FALHAS falha(s), $PASSOU ok"
  echo "--- última saída do script:"; cat "$T/saida"
  exit 1
fi
echo "RESULTADO: tudo certo ($PASSOU conferências)"

#!/usr/bin/env bash
# hermes-release.sh — roda NA VPS de produção (instalado em /opt/hermes-call/releases/hermes-release.sh).
# Guarda cada versão publicada numa pasta própria e troca entre elas com um comando.
# Chamado pelos scripts do PC (ops/publicar.sh, ops/reverter.sh, ops/status.sh) — não precisa rodar à mão.
#
#   /opt/hermes-call/releases/<ID>/hermes-call   binário
#   /opt/hermes-call/releases/<ID>/dist/         painel
#   /opt/hermes-call/releases/<ID>/INFO          commit, data, md5
#   /opt/hermes-call/releases/<ID>/banco.dump    backup do banco feito ANTES de trocar para a versão seguinte
#   /opt/hermes-call/releases/ATUAL              ID no ar
#   /opt/hermes-call/releases/ESTAVEL            ID da versão BOA CONHECIDA (volta segura; nunca é apagada)
#   /opt/hermes-call/releases/<ID>/PROTEGIDA     versão que o "limpar" nunca apaga (com o backup do banco)
#   /opt/hermes-call/releases/HISTORICO          uma linha por troca
#
# Subcomandos: bootstrap | status | listar | compilar <dir_build> <ID> <VERSAO> | preparar <ID> <dir_build>
#             | ativar <ID> | ativar <ID> volta | voltar <ID> | backup-banco <ID> | limpar
#             | marcar-estavel <ID> | voltar-estavel
#
# PUBLICAR (ativar <ID>) e VOLTAR (ativar <ID> volta, voltar <ID>, voltar-estavel) são diferentes:
#   - publicar confere tudo (responde, linhas, pânico) e, se falhar, volta sozinho pra anterior;
#   - voltar é emergência: confere SÓ se o serviço responde /api/version e NUNCA se desfaz
#     sozinho (em 04/10 a volta pra uma versão sem /saude-local "falhava" na conferência de
#     linhas e a volta automática RECOLOCAVA a versão nova — ops/vps/testes/).
# "ativar <ID> volta" existe pra compatibilidade: o script velho (até a v0.7.0) ignora o
# "volta" e faz o ativar dele, que só confere /api/version.
set -euo pipefail

APP=/opt/hermes-call
REL=$APP/releases
SVC=hermes-call
PORT=8080
BOOT_ID="20260826-1859_6c5794b"          # TOC-fix, no ar desde 26/ago (tag PRODUCAO-2026-08-26-tocfix)
BOOT_MD5="9b27aa6db656d57b6d3dc5fc76527bec"
MANTER=8                                  # quantas versões guardar

log() { echo "[$(date '+%F %T')] $*"; }
die() { echo "ERRO: $*" >&2; exit 1; }
atual() { cat "$REL/ATUAL" 2>/dev/null || true; }
estavel() { cat "$REL/ESTAVEL" 2>/dev/null || true; }

cmd_bootstrap() {
  mkdir -p "$REL"
  if [ -n "$(atual)" ]; then log "já inicializado (ATUAL=$(atual))"; return; fi
  local md5; md5=$(md5sum "$APP/hermes-call" | cut -d' ' -f1)
  [ "$md5" = "$BOOT_MD5" ] || die "binário no ar ($md5) não é o TOC-fix esperado ($BOOT_MD5) — pare e investigue"
  local d=$REL/$BOOT_ID
  mkdir -p "$d"
  cp -a "$APP/hermes-call" "$d/hermes-call"
  cp -a "$APP/dist" "$d/dist"
  cat > "$d/INFO" <<EOF
id=$BOOT_ID
commit=6c5794b
tag=PRODUCAO-2026-08-26-tocfix
md5=$md5
origem=cópia do que estava no ar em $(date '+%F %T') (versão de 26/ago)
EOF
  echo "$BOOT_ID" > "$REL/ATUAL"
  echo "$(date '+%F %T') bootstrap $BOOT_ID" >> "$REL/HISTORICO"
  log "versão atual guardada em $d"
}

cmd_status() {
  local id; id=$(atual)
  echo "ATUAL=$id"
  echo "ESTAVEL=$(estavel)  (volta segura: ops/voltar-estavel.sh)"
  [ -n "$id" ] && sed 's/^/  /' "$REL/$id/INFO"
  echo "servico=$(systemctl is-active $SVC)"
  echo "md5_no_ar=$(md5sum $APP/hermes-call | cut -d' ' -f1)"
  echo "api_version=$(curl -s -m5 http://127.0.0.1:$PORT/api/version)"
}

cmd_listar() {
  local a; a=$(atual)
  for d in $(ls -1d "$REL"/*/ 2>/dev/null | sort); do
    local id; id=$(basename "$d")
    local m=" "; [ "$id" = "$a" ] && m="*"
    local b="";  [ -f "$d/banco.dump" ] && b="(backup banco $(du -h "$d/banco.dump" | cut -f1))"
    local e="";  [ "$id" = "$(estavel)" ] && e="[ESTÁVEL]"
    [ -f "$d/PROTEGIDA" ] && [ -z "$e" ] && e="[protegida]"
    echo "$m $id  $(grep '^commit=' "$d/INFO" | cut -d= -f2)  $e $b"
  done
  echo "--- últimas trocas"; tail -n 10 "$REL/HISTORICO"
}

# compilar <dir_build> <ID> <VERSAO>: go vet + go build do código em <dir_build>/src.
# Toolchain FIXO (sem GOTOOLCHAIN=auto baixando compilador no meio da publicação):
#   1. Go instalado na VPS (/usr/local/go) >= versão do go.mod  → usa ele (GOTOOLCHAIN=local);
#   2. senão, o toolchain exato do go.mod JÁ baixado no cache    → usa ele (sem baixar nada);
#   3. senão PARA com a instrução de instalar antes (nada muda na produção).
cmd_compilar() {
  local b=$1 id=$2 versao=$3
  [ -f "$b/src/go.mod" ] || die "código não encontrado em $b/src"
  cd "$b/src"
  export PATH=$PATH:/usr/local/go/bin CGO_ENABLED=1
  local req tem cache
  req=$(awk '$1=="go"{print $2; exit}' go.mod | tr -d '\r')  # CRLF vindo do Windows quebrava o caminho do toolchain
  tem=$(GOTOOLCHAIN=local go env GOVERSION | sed 's/^go//')
  if [ "$(printf '%s\n%s\n' "$req" "$tem" | sort -V | head -1)" = "$req" ]; then
    export GOTOOLCHAIN=local
  else
    cache="$(GOTOOLCHAIN=local go env GOMODCACHE)/golang.org/toolchain@v0.0.1-go$req.linux-amd64"
    [ -d "$cache" ] || die "Go da VPS ($tem) é mais velho que o go.mod ($req) e o toolchain go$req não está no cache. Instale antes, fora da publicação: cd /tmp && GOTOOLCHAIN=go$req go version   (ou atualize /usr/local/go)"
    export GOTOOLCHAIN=go$req
  fi
  log "go: $(go version)"
  log "go vet (tags mlow)"
  nice -n 19 go vet -tags mlow ./... || die "go vet falhou — publicação cancelada (nada mudou na produção)"
  log "go build"
  nice -n 19 go build -p 2 -tags mlow \
    -ldflags "-X main.buildStamp=$id -X main.appVersion=v$versao -X main.appChannel=producao" \
    -o "$b/hermes-call" ./cmd/server
}

# preparar <ID> <dir_build>: dir_build tem hermes-call e client-dist/ já compilados
cmd_preparar() {
  local id=$1 b=$2 d=$REL/$1
  [ -f "$b/hermes-call" ] && [ -d "$b/client-dist" ] || die "build incompleto em $b"
  go_meta=$(PATH=$PATH:/usr/local/go/bin go version -m "$b/hermes-call")
  echo "$go_meta" | grep -q -- '-tags=mlow' || die "binário SEM -tags=mlow (causa 'fica conectando') — recusado"
  ldd "$b/hermes-call" | grep -q libopus_mlow || die "binário não liga na libopus_mlow — recusado"
  rm -rf "$d"; mkdir -p "$d"
  cp -a "$b/hermes-call" "$d/hermes-call"
  # painel: parte do painel que está no ar (mantém arquivos extras que existem só na VPS) + build novo por cima
  cp -a "$REL/$(atual)/dist" "$d/dist"
  cp -a "$b/client-dist/." "$d/dist/"
  cp "$b/INFO" "$d/INFO"
  echo "md5=$(md5sum "$d/hermes-call" | cut -d' ' -f1)" >> "$d/INFO"
  log "versão $id pronta em $d (ainda NÃO está no ar)"
}

cmd_backup_banco() {
  local id=$1 f=$REL/$1/banco.dump
  log "backup do banco wacalls_main -> $f"
  sudo -u postgres pg_dump -Fc wacalls_main > "$f.tmp" && mv "$f.tmp" "$f"
  log "backup ok ($(du -h "$f" | cut -f1))"
}

# ativar <ID>: PUBLICA a versão; se não subir saudável, volta sozinho para a anterior.
# Saudável = responde /api/version com o build certo em até 90 s E não tem chave de teste
# ligada (sem_chaves_de_teste) E (se as duas versões têm o /saude-local) as linhas do WhatsApp
# voltam pela regra do linhas_ok E não teve pânico/aborto no registro depois da troca (janela
# de 45 s). Decide em até ~110 s depois da troca.
cmd_ativar() {
  local id=$1 d=$REL/$1 ant; ant=$(atual)
  [ -f "$d/hermes-call" ] && [ -d "$d/dist" ] || die "versão $id não existe em $REL"
  [ "$id" != "$ant" ] || die "$id já está no ar"
  local antes_json t0
  AVISO_LINHAS=""
  antes_json=$(saude_local)
  log "linhas do WhatsApp conectadas antes da troca: $(campo_num "$antes_json" linhas_conectadas | grep . || echo "desconhecido (versão no ar sem /saude-local)")"
  trocar "$id"
  t0=$(agora_s)
  if saudavel "$id" && sem_chaves_de_teste "$id" && linhas_ok "$id" "$antes_json" "$t0" && sem_panico "$t0"; then
    log "decidido em $(( $(agora_s) - t0 )) s depois da troca"
    echo "$id" > "$REL/ATUAL"
    echo "$(date '+%F %T') $ant -> $id OK" >> "$REL/HISTORICO"
    [ -z "$AVISO_LINHAS" ] || echo "$(date '+%F %T') aviso $id: $AVISO_LINHAS" >> "$REL/HISTORICO"
    log "NO AR: $id  (anterior: $ant — para voltar: ops/reverter.sh)"
    [ -z "$AVISO_LINHAS" ] || log "ATENÇÃO: $AVISO_LINHAS"
  else
    log "decidido em $(( $(agora_s) - t0 )) s depois da troca"
    log "versão $id NÃO subiu saudável — voltando automaticamente para $ant"
    trocar "$ant"
    saudavel "$ant" || die "ATENÇÃO: nem a anterior ($ant) respondeu — verificar journalctl -u $SVC"
    echo "$(date '+%F %T') $ant -> $id FALHOU, voltou para $ant" >> "$REL/HISTORICO"
    die "publicação de $id falhou; produção continua em $ant"
  fi
}

# voltar <ID>: VOLTA de emergência (ops/reverter.sh, ops/voltar-estavel.sh, o .bat). Confere SÓ
# se o serviço responde /api/version com o build da versão de destino. Não confere linhas nem
# pânico (a versão de destino pode ser antiga, sem /saude-local) e NUNCA volta sozinha pra
# versão de onde saiu: quem pediu a volta queria sair dela. Se o destino não responder, fica
# instalado (ATUAL = destino), avisa e mostra o comando pra decidir na mão.
cmd_voltar() {
  local id=$1 d=$REL/$1 ant; ant=$(atual)
  [ -f "$d/hermes-call" ] && [ -d "$d/dist" ] || die "versão $id não existe em $REL"
  if [ "$id" = "$ant" ]; then log "$id já está no ar — nada a fazer"; return 0; fi
  log "VOLTA: $ant -> $id (confere só /api/version; não volta sozinho para $ant)"
  trocar "$id"
  echo "$id" > "$REL/ATUAL"   # é o que está instalado agora, respondendo ou não
  if saudavel "$id"; then
    echo "$(date '+%F %T') $ant -> $id VOLTA OK" >> "$REL/HISTORICO"
    log "NO AR: $id  (volta de $ant)"
  else
    echo "$(date '+%F %T') $ant -> $id VOLTA SEM RESPOSTA" >> "$REL/HISTORICO"
    die "a versão $id foi instalada mas NÃO respondeu /api/version em 90 s. NÃO voltei sozinho para $ant (uma volta nunca se desfaz sozinha). Veja: journalctl -u $SVC -n 100 --no-pager ; para recolocar $ant: bash ops/reverter.sh $ant"
  fi
}

trocar() {
  local d=$REL/$1
  cp -a "$d/hermes-call" "$APP/hermes-call.trocando"
  mv -f "$APP/hermes-call.trocando" "$APP/hermes-call"
  rm -rf "$APP/dist.trocando" "$APP/dist.saindo"
  cp -a "$d/dist" "$APP/dist.trocando"
  mv "$APP/dist" "$APP/dist.saindo"
  mv "$APP/dist.trocando" "$APP/dist"
  rm -rf "$APP/dist.saindo"
  # stop + start (em vez de restart) pra marcar a posição do registro ENTRE os dois: o que a
  # versão que SAI escreve ao desligar (inclusive pânico/aborto no desligamento) fica antes
  # da marca e não conta contra a versão que ENTRA (sem_panico). Falha aqui não interrompe:
  # o saudavel decide e a volta automática continua funcionando.
  systemctl stop $SVC || log "aviso: systemctl stop $SVC falhou"
  sleep 1   # o journald termina de gravar o que o processo antigo deixou no caminho
  MARCA_REGISTRO=$(marca_registro)
  MARCA_HORA=$(date '+%F %T')
  systemctl start $SVC || log "aviso: systemctl start $SVC falhou"
}

# marca_registro: posição (cursor) da última linha do registro do serviço ("" se vazio).
marca_registro() {
  journalctl -u $SVC -n1 --show-cursor --no-pager 2>/dev/null | sed -n 's/^-- cursor: //p' | tail -n1 || true
}

# registro_desde_a_troca: só o que entrou no registro DEPOIS da marca feita no trocar (sem
# marca — registro vazio ou journalctl antigo — usa a hora, que também é depois do stop).
registro_desde_a_troca() {
  if [ -n "${MARCA_REGISTRO:-}" ]; then
    journalctl -u $SVC --after-cursor "$MARCA_REGISTRO" --no-pager 2>/dev/null || true
  else
    journalctl -u $SVC --since "${MARCA_HORA:-}" --no-pager 2>/dev/null || true
  fi
}

# Prazos da publicação (segundos depois da troca). Decisão em até ~110 s no pior caso:
# responde (até 90) → linhas (até 60, sem passar de 105 desde a troca) → pânico (janela de 45).
PRAZO_RESPONDER_S=90
ESPERA_LINHAS_S=60
PRAZO_LINHAS_S=105
JANELA_PANICO_S=45

# agora_s: relógio em segundos (função pra o teste trocar por um relógio falso).
agora_s() { date +%s; }

# saude_local: resposta do /saude-local ("" se a versão no ar não tem — ele só existe a partir
# de 04/10/2026; a versão antiga devolve a página do painel ou 404 nesse endereço).
saude_local() {
  local r; r=$(curl -s -m3 http://127.0.0.1:$PORT/saude-local 2>/dev/null || true)
  case "$r" in *'"linhas_conectadas"'*) printf '%s\n' "$r" ;; esac
}
# campo_num <json> <campo>: número do campo ("" se não tem).
campo_num() { printf '%s\n' "$1" | grep -o "\"$2\":[0-9]*" | head -n1 | cut -d: -f2 || true; }
# campo_ids <json> <campo>: lista de ids do campo, separados por espaço ("" se vazia/ausente).
campo_ids() { printf '%s\n' "$1" | sed -n "s/.*\"$2\":\[\([^]]*\)\].*/\1/p" | tr -d '" ' | tr ',' ' ' || true; }
conta_palavras() { echo $#; }
# linhas_que_faltam <ids antes> <ids agora>: as de antes que não estão agora.
linhas_que_faltam() {
  local x out=""
  for x in $1; do case " $2 " in *" $x "*) ;; *) out="$out $x" ;; esac; done
  printf '%s' "${out# }"
}

# tem_saude_local: a versão no ar (que JÁ respondeu /api/version) tem o /saude-local?
# 3 tentativas pra não confundir uma resposta lenta com "não tem".
tem_saude_local() {
  for i in 1 2 3; do
    [ -z "$(saude_local)" ] || return 0
    sleep 1
  done
  return 1
}

# sem_chaves_de_teste <ID>: a PRODUÇÃO não sobe com chave "só bancada" ligada no ambiente
# (/saude-local "chaves_de_teste", ex.: HERMES_VOICE_ESPERA_ACEITE=false,
# HERMES_TESTE_ACEITE_POR_RELAY=true, HERMES_AUTO_ANSWER_ACEITAR=true — cmd/server/aceite_teste.go;
# pedido 2 do online em docs/PEDIDOS_AO_PC.md). Lista não vazia = RECUSA e a volta automática
# recoloca a anterior. Versão sem /saude-local ou sem o campo (antigas) ou lista vazia: segue.
sem_chaves_de_teste() {
  local id=$1 j="" chaves
  for i in 1 2 3; do
    j=$(saude_local); [ -z "$j" ] || break
    sleep 1
  done
  if [ -z "$j" ]; then log "chaves de teste: a versão $id não tem /saude-local (versão antiga) — conferência pulada"; return 0; fi
  chaves=$(campo_ids "$j" chaves_de_teste)
  if [ -n "$chaves" ]; then
    log "RECUSADA: a versão $id subiu com chave(s) de TESTE ligada(s) no ambiente da PRODUÇÃO: $chaves"
    log "  Chave de teste na produção é proibida (são só da bancada). Tire do ambiente do serviço"
    log "  (systemctl cat $SVC; drop-ins em /etc/systemd/system/$SVC.service.d/), systemctl daemon-reload, e publique de novo."
    return 1
  fi
  return 0
}

# linhas_ok <ID> <json de antes> <t0>: as linhas do WhatsApp que estavam conectadas voltaram?
# Espera até 60 s (sem passar de 105 s desde a troca) todas voltarem; se não voltarem, decide
# pela regra do decide_linhas. Sem número de antes (versão de origem sem /saude-local) ou versão
# de destino sem /saude-local (ativar de uma versão antiga): a conferência é PULADA (no log).
linhas_ok() {
  local id=$1 antes_json=$2 t0=$3
  local antes; antes=$(campo_num "$antes_json" linhas_conectadas)
  if [ -z "$antes" ]; then log "conferência de linhas pulada: a versão anterior não informava as linhas (sem /saude-local)"; return 0; fi
  if [ "$antes" = 0 ]; then log "conferência de linhas: nenhuma linha estava conectada antes da troca"; return 0; fi
  if ! tem_saude_local; then log "conferência de linhas pulada: a versão $id não tem /saude-local (versão antiga)"; return 0; fi
  local ids_antes admin limite prazo agora_json agora="" faltam=""
  ids_antes=$(campo_ids "$antes_json" ids_conectadas)
  admin=$(campo_ids "$antes_json" ids_admin)
  limite=$(( $(agora_s) + ESPERA_LINHAS_S )); prazo=$(( t0 + PRAZO_LINHAS_S ))
  [ "$limite" -le "$prazo" ] || limite=$prazo
  while :; do
    agora_json=$(saude_local)
    agora=$(campo_num "$agora_json" linhas_conectadas)
    faltam=$(linhas_que_faltam "$ids_antes" "$(campo_ids "$agora_json" ids_conectadas)")
    admin="$admin $(campo_ids "$agora_json" ids_admin)"
    if [ -n "$agora" ] && [ "$agora" -ge "$antes" ] && [ -z "$faltam" ]; then
      log "linhas conectadas: $agora (antes: $antes)"; return 0
    fi
    [ "$(agora_s)" -lt "$limite" ] || break
    sleep 3
  done
  decide_linhas "$antes" "${agora:-0}" "$ids_antes" "$faltam" "$admin" "$(( $(agora_s) - t0 ))"
}

# decide_linhas <antes> <agora> <ids antes> <faltam> <ids admin> <segundos>: nem todas voltaram.
# Regra (a mais segura sem derrubar todo mundo à toa):
#  - nenhuma linha voltou (0 de N)              → RECUSA: defeito da versão (pega todas);
#  - 2 ou mais não voltaram                     → RECUSA: mais de uma ao mesmo tempo é a versão;
#  - não voltou uma linha da ADMINISTRADORA     → RECUSA: a linha da dona nunca fica pra trás;
#  - versão sem a lista de ids (não sei qual)   → RECUSA;
#  - não voltou UMA linha de cliente (N-1 de N) → ACEITA com AVISO (id no log e no HISTORICO).
#    Uma linha só costuma ser problema dela (celular desconectado, bloqueio, proxy do cliente);
#    voltar a versão derrubaria de novo TODAS as linhas e as ligações em andamento sem
#    consertar essa — e a versão anterior teria o mesmo problema com ela.
decide_linhas() {
  local antes=$1 agora=$2 ids_antes=$3 faltam=$4 admin=$5 seg=$6 x n
  log "a versão nova reconectou $agora de $antes linha(s) do WhatsApp em $seg s; não voltaram: ${faltam:-? (sem a lista de ids)}"
  [ -z "$faltam" ] || log "  de quem é: sudo -u postgres psql wacalls_main -c \"select id, name, user_id from sessions where id in ('$(echo $faltam | sed "s/ /','/g")')\""
  if [ "$agora" -eq 0 ]; then log "RECUSADA: nenhuma linha voltou"; return 1; fi
  if [ -z "$ids_antes" ] || [ -z "$faltam" ]; then log "RECUSADA: sem a lista de ids não dá pra saber qual linha caiu"; return 1; fi
  n=$(conta_palavras $faltam)
  if [ "$n" -ge 2 ]; then log "RECUSADA: $n linhas não voltaram"; return 1; fi
  for x in $faltam; do
    case " $admin " in *" $x "*) log "RECUSADA: a linha $x é da administradora da plataforma"; return 1 ;; esac
  done
  AVISO_LINHAS="a linha $faltam (de cliente) não reconectou em $seg s — confira no painel"
  log "ACEITA com aviso: $AVISO_LINHAS"
  return 0
}

# sem_panico <t0>: nada de pânico/aborto do Go ou do codec na versão nova nos primeiros 45 s
# (só o registro depois da troca: o desligamento da versão antiga não conta).
# Só o que DERRUBA o processo: "panic: "/"fatal error: " no começo da mensagem (o pânico
# recuperado pelo servidor sai como atributo panic=..., não casa) e os sinais de aborto.
PANICO_RE=': (panic: |fatal error: )|SIGABRT|SIGSEGV|status=6/ABRT|status=11/SEGV'
sem_panico() {
  local t0=$1 falta
  falta=$(( t0 + JANELA_PANICO_S - $(agora_s) ))
  [ "$falta" -le 0 ] || sleep "$falta"
  local reg; reg=$(registro_desde_a_troca)
  if printf '%s\n' "$reg" | grep -E -q "$PANICO_RE"; then
    log "a versão nova teve pânico/aborto no registro:"
    printf '%s\n' "$reg" | grep -E -m3 "$PANICO_RE" || true
    return 1
  fi
  return 0
}

# saudavel <ID>: responde /api/version com o build da versão em até 90 s (prazo pelo relógio:
# curl lento não estica a espera).
saudavel() {
  local id=$1 want limite; want=$(grep '^build=' "$REL/$id/INFO" | cut -d= -f2 || true)
  limite=$(( $(agora_s) + PRAZO_RESPONDER_S ))
  while [ "$(agora_s)" -lt "$limite" ]; do
    sleep 3
    systemctl is-active --quiet $SVC || continue
    local v; v=$(curl -s -m3 http://127.0.0.1:$PORT/api/version || true)
    if echo "$v" | grep -q '"version"'; then
      if [ -z "$want" ] || echo "$v" | grep -q "\"build\":\"$want\""; then log "responde: $v"; return 0; fi
    fi
  done
  return 1
}

cmd_limpar() {
  local a e p; a=$(atual); e=$(estavel)
  # p = a ANTERIOR (destino do ops/reverter.sh, com o backup do banco feito na troca). Em 03/10 a
  # limpeza contou as compilações de teste (--so-compilar, bancada) e apagou a anterior junto com
  # o backup recém-feito.
  p=$(grep ' OK$' "$REL/HISTORICO" 2>/dev/null | tail -1 | awk '{print $3}' || true)
  ls -1d "$REL"/*/ | sort | head -n -$MANTER | while read -r d; do
    local id; id=$(basename "$d")
    if [ "$id" = "$a" ] || [ "$id" = "$e" ] || [ "$id" = "$p" ] || [ "$id" = "$BOOT_ID" ] || [ -f "$d/PROTEGIDA" ]; then continue; fi
    log "removendo versão antiga $id"; rm -rf "$d"
  done
  # backups de banco: só os 3 mais recentes (o das versões protegidas/estável fica sempre)
  ls -1t "$REL"/*/banco.dump 2>/dev/null | tail -n +4 | while read -r f; do
    local dd; dd=$(dirname "$f")
    if [ -f "$dd/PROTEGIDA" ] || [ "$(basename "$dd")" = "$e" ] || [ "$(basename "$dd")" = "$p" ]; then continue; fi
    rm -f "$f"
  done
}

# marcar-estavel <ID>: essa versão vira a volta segura (ESTAVEL) e fica PROTEGIDA da limpeza.
cmd_marcar_estavel() {
  local id=$1 d=$REL/$1
  [ -f "$d/hermes-call" ] && [ -d "$d/dist" ] || die "versão $id não existe em $REL"
  touch "$d/PROTEGIDA"
  echo "$id" > "$REL/ESTAVEL"
  echo "$(date '+%F %T') estavel $id" >> "$REL/HISTORICO"
  log "versão estável (volta segura): $id"
}

# voltar-estavel: coloca no ar a versão ESTAVEL. Pode rodar quantas vezes quiser (não alterna).
# É uma VOLTA (cmd_voltar): só confere /api/version e nunca se desfaz sozinha.
cmd_voltar_estavel() {
  local e; e=$(estavel)
  [ -n "$e" ] || die "nenhuma versão estável marcada (use: ops/reverter.sh)"
  if [ "$e" = "$(atual)" ]; then log "a versão estável ($e) JÁ está no ar — nada a fazer"; return 0; fi
  cmd_voltar "$e"
}

main() {
  case "${1:-}" in
    bootstrap) cmd_bootstrap ;;
    status)    cmd_status ;;
    listar)    cmd_listar ;;
    compilar)  cmd_compilar "$2" "$3" "$4" ;;
    preparar)  cmd_preparar "$2" "$3" ;;
    backup-banco) cmd_backup_banco "$2" ;;
    ativar)    if [ "${3:-}" = volta ]; then cmd_voltar "$2"; else cmd_ativar "$2"; fi ;;
    voltar)    cmd_voltar "$2" ;;
    limpar)    cmd_limpar ;;
    marcar-estavel) cmd_marcar_estavel "$2" ;;
    voltar-estavel) cmd_voltar_estavel ;;
    *) die "uso: $0 bootstrap|status|listar|compilar DIR ID VERSAO|preparar ID DIR|backup-banco ID|ativar ID [volta]|voltar ID|limpar|marcar-estavel ID|voltar-estavel" ;;
  esac
}

# Carregado com "source" (testes em ops/vps/testes/) só define as funções; rodado direto, executa.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi

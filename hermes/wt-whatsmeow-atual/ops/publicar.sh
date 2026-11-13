#!/usr/bin/env bash
# ops/publicar.sh — publica o commit atual (HEAD) na produção, com volta fácil.
# Rodar no Git Bash, na raiz D:\hermes\pc-base:   bash ops/publicar.sh
#   --so-compilar   compila e prepara na VPS, mas NÃO coloca no ar (teste seguro)
#
# Travas:
#  1. git precisa estar limpo (arquivos rastreados) — nunca publica código não commitado.
#  2. ANTI-RETROCESSO: o commit precisa CONTER a versão que está no ar. Publicar algo
#     mais antigo que a produção é recusado (foi o erro que já custou versões boas).
#  3. Compila na VPS numa pasta limpa, a partir do commit exato, SEMPRE com -tags mlow.
#  4. Faz backup do banco antes de trocar.
#  5. Se a versão nova não responder em 90s, a VPS volta sozinha para a anterior.
#  6. Na VPS, roda `go vet` antes de compilar (erro de vet = não publica) e marca o
#     binário com canal "producao" (/api/version deixava de dizer "beta").
#  7. Toolchain FIXO: usa o Go da VPS só se ele for >= a versão do go.mod; se não for,
#     usa o toolchain exato do go.mod SE já estiver baixado; senão PARA (nada de
#     GOTOOLCHAIN=auto baixando compilador no meio da publicação).
#  8. Depois de publicar, envia a tag PRODUCAO-<ID> pro GitHub (origin e emerson);
#     se o push falhar, só avisa (a produção já está no ar).
#  9. Antes da troca, a versão no ar vira a ESTÁVEL (volta segura) se ainda não houver uma.
# 10. A versão nova só fica no ar se, além de responder, reconectar as linhas do WhatsApp que
#     estavam conectadas e não tiver pânico/aborto no registro depois da troca
#     (hermes-release.sh ativar; decide em até ~110 s). Tolerância: UMA linha de cliente que
#     não voltou passa com aviso (id no log e no HISTORICO); nenhuma linha, duas ou mais, ou
#     a linha da administradora = volta sozinho. Também volta sozinho se o /saude-local da versão
#     nova listar "chaves_de_teste" (chave só-bancada no ambiente da produção é proibida).
#     Teste: ops/vps/testes/testar-hermes-release.sh
# 11. BANCADA (cópia de teste na mesma VPS, ligada ao 8288): por padrão NÃO é mexida.
#     Só com PUBLICAR_COM_BANCADA=1 ela vai pra mesma versão, e só se o aceite automático
#     estiver DESLIGADO no ambiente REAL dos processos (bancada e produção: o iniciar.sh da
#     bancada herda o ambiente da produção) e no /etc/hermes-bancada/bancada.env. Ligado =
#     PARA antes de publicar (nada muda). Depois, a versão da bancada é conferida pelo que ela
#     RESPONDE (127.0.0.1:8091/api/version), não pelo arquivo VERSAO. Incidente de 03/10:
#     docs/REGRESSOES_LIGACAO.md §6. (O antigo PUBLICAR_SEM_BANCADA não existe mais.)
# Para voltar depois: bash ops/voltar-estavel.sh (ou ops/reverter.sh <ID>)
set -euo pipefail
cd "$(dirname "$0")/.."

HOST=hermes-prod
REL=/opt/hermes-call/releases
BANCADA_URL=http://127.0.0.1:8091
SO_COMPILAR=0; [ "${1:-}" = "--so-compilar" ] && SO_COMPILAR=1
COM_BANCADA=0; [ "${PUBLICAR_COM_BANCADA:-}" = 1 ] && COM_BANCADA=1
ssh_() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }
die() { echo; echo "PAROU: $*" >&2; exit 1; }

# bancada_sem_aceite: 0 se o aceite automático (HERMES_AUTO_ANSWER_ACEITAR) está DESLIGADO em
# todo lugar de onde a bancada tira o ambiente. Confere o ambiente de VERDADE dos processos
# (/proc/<pid>/environ da bancada e da produção, que a bancada herda) e o bancada.env (aplicado
# por cima ao subir). Aceita true/1/yes/on, maiúsculo ou não, com ou sem aspas/export — mais
# rígido que o servidor (que só liga com "true"), de propósito.
bancada_sem_aceite() {
  ssh_ 'bash -s' <<'REMOTO'
RE='^[[:space:]]*(export[[:space:]]+)?HERMES_AUTO_ANSWER_ACEITAR[[:space:]]*=[[:space:]]*["'"'"']?[[:space:]]*(true|1|yes|on)'
ligado=""
for svc in hermes-bancada hermes-call; do
  pid=$(systemctl show -p MainPID --value "$svc" 2>/dev/null || true)
  if [ -n "$pid" ] && [ "$pid" != 0 ]; then
    if [ ! -r "/proc/$pid/environ" ]; then echo "   não consegui ler o ambiente de $svc (pid $pid)"; ligado="$ligado $svc(ilegível)"; continue; fi
    tr '\0' '\n' < "/proc/$pid/environ" | grep -Eiq "$RE" && ligado="$ligado $svc(processo $pid)"
  fi
done
if [ -f /etc/hermes-bancada/bancada.env ] && grep -Eiq "$RE" /etc/hermes-bancada/bancada.env; then
  ligado="$ligado /etc/hermes-bancada/bancada.env"
fi
if [ -n "$ligado" ]; then echo "   ACEITE AUTOMÁTICO LIGADO em:$ligado"; exit 3; fi
echo "   aceite automático desligado (bancada, produção e bancada.env)"
REMOTO
}

# 1. git limpo
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "há alterações não commitadas. Commite antes de publicar."
# Trava 11 antes de qualquer coisa: com a bancada junto, aceite automático ligado = não começa.
if [ $COM_BANCADA = 1 ] && [ $SO_COMPILAR = 0 ]; then
  echo "== Bancada junto (PUBLICAR_COM_BANCADA=1): conferindo o aceite automático"
  bancada_sem_aceite || die "aceite automático LIGADO (acima). A bancada entraria nas ligações pro 8288 (docs/REGRESSOES_LIGACAO.md §6). Desligue e rode de novo, ou publique sem a bancada (sem PUBLICAR_COM_BANCADA). Nada foi alterado."
fi
COMMIT=$(git rev-parse HEAD); CURTO=$(git rev-parse --short=7 HEAD)
ID="$(date +%Y%m%d-%H%M)_$CURTO"
VERSAO=$(git show "$COMMIT:VERSION" | tr -d '\r\n ')
echo "== Publicando $CURTO ($(git log -1 --format=%s))"

# 2. instala/atualiza o script da VPS e descobre o que está no ar
scp -q -o BatchMode=yes ops/vps/hermes-release.sh "$HOST:$REL.sh.novo" 2>/dev/null || { ssh_ "mkdir -p $REL"; scp -q ops/vps/hermes-release.sh "$HOST:$REL.sh.novo"; }
ssh_ "mkdir -p $REL && mv $REL.sh.novo $REL/hermes-release.sh && chmod +x $REL/hermes-release.sh && $REL/hermes-release.sh bootstrap"
NO_AR=$(ssh_ "cat $REL/ATUAL")
NO_AR_COMMIT=$(ssh_ "grep '^commit=' $REL/$NO_AR/INFO | cut -d= -f2")
echo "== No ar agora: $NO_AR (commit $NO_AR_COMMIT)"

git cat-file -e "$NO_AR_COMMIT^{commit}" 2>/dev/null || die "o commit que está no ar ($NO_AR_COMMIT) não existe neste git. Não dá pra garantir que não é retrocesso."
git merge-base --is-ancestor "$NO_AR_COMMIT" "$COMMIT" || die "RETROCESSO: $CURTO NÃO contém a versão no ar ($NO_AR_COMMIT). Faça as correções em cima dela (git log $NO_AR_COMMIT)."
[ "$(git rev-parse "$NO_AR_COMMIT")" != "$COMMIT" ] || die "esse commit já é o que está no ar."
echo "   ok: $CURTO é uma evolução da versão no ar ($(git rev-list --count "$NO_AR_COMMIT..$COMMIT") commit(s) a mais)"

# 3a. painel: compila NESTE PC (a VPS tem Node 18, velho demais para o Vite), a partir do commit exato
L="${TMPDIR:-/tmp}/hermes-build-$ID"
echo "== Compilando o painel neste PC ($L)"
rm -rf "$L"; mkdir -p "$L"
git -c core.autocrlf=false archive --format=tar "$COMMIT" client | tar -x -C "$L"
( cd "$L/client" && npm ci --no-audit --no-fund --loglevel=error && npm run build --silent )
echo "   painel: $(grep -o 'assets/index-[A-Za-z0-9_-]*\.js' "$L/client/dist/index.html")"

# 3b. servidor: envia o código exato e compila na VPS (precisa da libopus_mlow de lá)
B=/opt/hermes-build/$ID
echo "== Enviando e compilando o servidor na VPS ($B) — leva alguns minutos"
git -c core.autocrlf=false archive --format=tar "$COMMIT" | ssh_ "rm -rf $B && mkdir -p $B/src && tar -x -C $B/src"
tar -c -C "$L/client" dist | ssh_ "tar -x -C $B && mv $B/dist $B/client-dist"
rm -rf "$L"
# go vet + build com toolchain fixo e canal "producao" (ver hermes-release.sh compilar).
ssh_ "set -e
  $REL/hermes-release.sh compilar $B '$ID' '$VERSAO'
  printf 'id=%s\ncommit=%s\nbuild=%s\norigem=ops/publicar.sh em %s\n' '$ID' '$CURTO' '$ID' \"\$(date '+%F %T')\" > $B/INFO
  $REL/hermes-release.sh preparar '$ID' $B
  rm -rf $B" || { ssh_ "rm -rf $B"; die "falhou a compilação na VPS (nada foi alterado na produção)"; }

if [ $SO_COMPILAR = 1 ]; then
  echo; echo "== Compilado e preparado como $ID, mas NÃO publicado (--so-compilar)."
  echo "   Para publicar essa versão: ssh $HOST $REL/hermes-release.sh ativar $ID"
  exit 0
fi

# 4. VOLTA SEGURA: se ainda não há versão estável marcada, a que está no ar agora (que
#    vinha funcionando) vira a ESTÁVEL — protegida da limpeza; ops/voltar-estavel.sh (ou o
#    VOLTAR-VERSAO-ESTAVEL.bat) volta pra ela quantas vezes for preciso.
ESTAVEL=$(ssh_ "cat $REL/ESTAVEL 2>/dev/null || true")
if [ -z "$ESTAVEL" ]; then
  ssh_ "$REL/hermes-release.sh marcar-estavel '$NO_AR'"
  ESTAVEL=$NO_AR
fi
echo "== Versão estável (volta segura): $ESTAVEL"

# 5. backup do banco + troca (com volta automática se não subir)
ssh_ "$REL/hermes-release.sh backup-banco '$NO_AR' && $REL/hermes-release.sh ativar '$ID' && $REL/hermes-release.sh limpar"

git tag -f "PRODUCAO-$ID" "$COMMIT" >/dev/null
echo
echo "== PUBLICADO: $ID"
echo "   Tag local: PRODUCAO-$ID"
# A tag vai pro GitHub (as duas origens). Falha aqui NÃO desfaz nada: a produção já
# está no ar; só avisa como mandar depois.
for REMOTO in origin emerson; do
  git remote get-url "$REMOTO" >/dev/null 2>&1 || continue
  # GIT_TERMINAL_PROMPT=0: sem credencial, falha na hora em vez de travar pedindo senha.
  if GIT_TERMINAL_PROMPT=0 git push -q "$REMOTO" "PRODUCAO-$ID" 2>/dev/null; then
    echo "   Tag enviada para $REMOTO"
  else
    echo "   (aviso: não consegui enviar a tag para $REMOTO; rode depois: git push $REMOTO PRODUCAO-$ID)"
  fi
done
echo "   Conferir:  https://hermescall.opus-sem-limites.com.br/api/version  (build deve ser $ID)"
echo "   Se der problema:  bash ops/voltar-estavel.sh   (volta para a estável $ESTAVEL)"
echo "                     ou dois cliques em ops\VOLTAR-VERSAO-ESTAVEL.bat"
echo "   Validou e ficou bom:  bash ops/marcar-estavel.sh   (essa vira a nova volta segura)"

# Bancada (trava 11): só com PUBLICAR_COM_BANCADA=1. Falha aqui não desfaz a publicação da
# produção (já está no ar), mas o script termina com erro pra ninguém deixar passar.
BANCADA_PROBLEMA=""
if [ $COM_BANCADA = 1 ]; then
  echo "== Bancada: conferindo de novo o aceite automático antes de mexer"
  if ! bancada_sem_aceite; then
    BANCADA_PROBLEMA="aceite automático LIGADO: a bancada NÃO foi atualizada"
  elif ! ssh_ "[ -x /root/lab-bancada.sh ]"; then
    BANCADA_PROBLEMA="/root/lab-bancada.sh não existe na VPS: a bancada NÃO foi atualizada"
  else
    echo "== Atualizando a bancada para $ID"
    if ! ssh_ "/root/lab-bancada.sh preparar '$ID'"; then
      BANCADA_PROBLEMA="/root/lab-bancada.sh preparar $ID falhou"
    # A versão é a que a bancada RESPONDE (o arquivo VERSAO pode dizer uma e o processo ser outro).
    elif ! ssh_ "for i in \$(seq 1 20); do curl -s -m3 $BANCADA_URL/api/version | grep -q '\"build\":\"$ID\"' && exit 0; sleep 3; done; exit 1"; then
      BANCADA_PROBLEMA="a bancada não respondeu com build $ID em 60 s ($BANCADA_URL/api/version: $(ssh_ "curl -s -m3 $BANCADA_URL/api/version" || true))"
    else
      echo "   bancada no ar com build $ID"
    fi
    # O processo NOVO da bancada também tem que estar sem aceite (o preparar pode ter mexido no
    # ambiente). Se estiver ligado, a bancada é PARADA: parada ela não entra em ligação nenhuma.
    if ! bancada_sem_aceite; then
      ssh_ "systemctl stop hermes-bancada" || true
      BANCADA_PROBLEMA="a bancada subiu com o aceite automático LIGADO e foi PARADA (systemctl stop hermes-bancada)"
    fi
  fi
else
  echo "== Bancada não foi mexida (para levar junto: PUBLICAR_COM_BANCADA=1 bash ops/publicar.sh)"
fi

# Cópia de referência do código nas VPS (/opt/hermes-call-fonte) acompanha o que está no ar.
if [ "$(git rev-parse main)" = "$COMMIT" ]; then
  bash ops/enviar-fonte.sh || echo "   (aviso: não consegui atualizar /opt/hermes-call-fonte; rode bash ops/enviar-fonte.sh)"
fi

if [ -n "$BANCADA_PROBLEMA" ]; then
  die "produção publicada ($ID), mas a BANCADA: $BANCADA_PROBLEMA. Veja docs/REGRESSOES_LIGACAO.md §6 antes de qualquer ligação de teste pro 8288."
fi

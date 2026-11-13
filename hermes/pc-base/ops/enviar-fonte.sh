#!/usr/bin/env bash
# ops/enviar-fonte.sh — deixa uma cópia de REFERÊNCIA do código-fonte (repositório git
# completo, branch main + tags) em /opt/hermes-call-fonte nas VPS, pra outros agentes/
# projetos consultarem. Rodar no Git Bash, na raiz D:\hermes\pc-base, depois de publicar:
#   bash ops/enviar-fonte.sh                 # produção + teste
#   bash ops/enviar-fonte.sh hermes-prod     # só uma VPS
#
# Produção: vai por "git bundle" (repositório completo, sem credencial do GitHub na VPS).
# VPS de TESTE (hermes-staging, 209.145.60.53): recebe só uma CÓPIA LIMPA do código atual
# (git archive, SEM .git e sem histórico). Decisão da dona em 02/10: a 209 está comprometida
# e o histórico do git ainda contém senhas antigas. Só o que está COMMITADO vai: arquivos
# fora do git (ex.: deploy/.env.deploy) nunca são enviados.
# A cópia NÃO é usada pra compilar/publicar — publicar é só com ops/publicar.sh.
set -euo pipefail
cd "$(dirname "$0")/.."

HOSTS=("$@")
[ ${#HOSTS[@]} -gt 0 ] || HOSTS=(hermes-prod hermes-staging)
DEST=/opt/hermes-call-fonte
BUNDLE="${TMPDIR:-/tmp}/hermes-call-fonte.bundle"

git bundle create "$BUNDLE" main --tags >/dev/null 2>&1
COMMIT=$(git rev-parse --short=7 main)
echo "== Enviando main ($COMMIT) + tags"

LIMPA="${TMPDIR:-/tmp}/hermes-call-fonte-limpa.tar"
git -c core.autocrlf=false archive --format=tar -o "$LIMPA" main

for h in "${HOSTS[@]}"; do
  if [ "$h" = "hermes-staging" ]; then
    # Cópia limpa: substitui a pasta inteira (inclusive um .git antigo, se existir).
    scp -q -o BatchMode=yes -o ConnectTimeout=15 "$LIMPA" "$h:/tmp/hermes-call-fonte-limpa.tar"
    ssh -n -o BatchMode=yes -o ConnectTimeout=15 "$h" "set -e
      rm -rf $DEST.novo && mkdir -p $DEST.novo && tar -x -C $DEST.novo -f /tmp/hermes-call-fonte-limpa.tar
      printf 'commit=%s\nnota=copia limpa, sem historico git (VPS de teste)\n' '$COMMIT' > $DEST.novo/COPIA_LIMPA.txt
      rm -rf $DEST && mv $DEST.novo $DEST && rm -f /tmp/hermes-call-fonte-limpa.tar
      echo \"   $h: $DEST = copia limpa de $COMMIT (\$(find $DEST -type f | wc -l) arquivos, sem .git)\""
    continue
  fi
  scp -q -o BatchMode=yes -o ConnectTimeout=15 "$BUNDLE" "$h:/tmp/hermes-call-fonte.bundle"
  ssh -n -o BatchMode=yes -o ConnectTimeout=15 "$h" "set -e
    if [ -d $DEST/.git ]; then
      cd $DEST && git fetch -q --tags /tmp/hermes-call-fonte.bundle main:refs/remotes/bundle/main && git checkout -q -B main refs/remotes/bundle/main && git reset -q --hard main
    else
      git clone -q -b main /tmp/hermes-call-fonte.bundle $DEST
    fi
    cd $DEST
    git remote set-url origin https://github.com/fabricadeautomacoesia/hermes-call.git 2>/dev/null || git remote add origin https://github.com/fabricadeautomacoesia/hermes-call.git
    rm -f /tmp/hermes-call-fonte.bundle
    echo \"   $h: $DEST em \$(git log -1 --format='%h %ci' ) (\$(git ls-files | wc -l) arquivos)\""
done
rm -f "$BUNDLE" "$LIMPA"

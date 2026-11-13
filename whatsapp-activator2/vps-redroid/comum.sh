# Funções usadas pelos outros scripts. Não rode este arquivo direto.
# shellcheck shell=bash

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo; echo "ERRO: $*" >&2; exit 1; }
ok()  { echo "OK: $*"; }
info(){ echo "... $*"; }

precisa_root() {
  [ "$(id -u)" = 0 ] || die "rode como root (ex.: sudo bash $0)"
}

# Configuração (config.env do kit). Exportada para o docker compose usar.
ADB_PORT=5555
REDROID_IMAGE="redroid/redroid:12.0.0_64only-latest"
if [ -f "$KIT_DIR/config.env" ]; then
  # shellcheck disable=SC1091
  . "$KIT_DIR/config.env"
fi
export ADB_PORT REDROID_IMAGE
SERIAL="127.0.0.1:${ADB_PORT}"

# Id da entrada do GRUB (dentro de "Opções avançadas") para uma versão de kernel.
# Imprime "submenu>entrada" ou só "entrada" quando não há submenu.
grub_entrada() {
  local ver="$1" cfg=/boot/grub/grub.cfg sub ent
  ent=$(grep -oP "'\Kgnulinux-\Q${ver}\E-advanced-[^']+(?=')" "$cfg" | head -1 || true)
  [ -n "$ent" ] || return 1
  sub=$(grep -oP "'\Kgnulinux-advanced-[^']+(?=')" "$cfg" | head -1 || true)
  if [ -n "$sub" ]; then echo "${sub}>${ent}"; else echo "$ent"; fi
}

# Espera o Android do contêiner terminar de ligar (até $1 segundos, padrão 300).
espera_android() {
  local limite="${1:-300}" t=0 v
  info "esperando o Android ligar (até ${limite}s)"
  while [ "$t" -lt "$limite" ]; do
    adb connect "$SERIAL" >/dev/null 2>&1 || true
    v=$(adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
    if [ "$v" = 1 ]; then ok "Android ligado em ~${t}s"; return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' redroid 2>/dev/null)" != true ]; then
      echo "O contêiner redroid parou. Últimas linhas do registro dele:" >&2
      docker logs --tail 40 redroid >&2 || true
      echo "Mensagens do kernel sobre binder:" >&2
      dmesg 2>/dev/null | grep -i -E 'binder|redroid' | tail -20 >&2 || true
      return 1
    fi
    sleep 5; t=$((t + 5))
  done
  echo "O Android não terminou de ligar em ${limite}s. Últimas linhas do registro:" >&2
  docker logs --tail 40 redroid >&2 || true
  return 1
}

# Abre o WhatsApp e só devolve sucesso quando o processo dele está rodando (até 30 s).
# (O "monkey" que se usava antes dizia sucesso sem o app ficar aberto.)
abre_whatsapp() {
  local t=0
  adb -s "$SERIAL" shell am start -n com.whatsapp/.Main >/dev/null 2>&1 \
    || adb -s "$SERIAL" shell monkey -p com.whatsapp -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 \
    || true
  while [ "$t" -lt 30 ]; do
    if [ -n "$(adb -s "$SERIAL" shell pidof com.whatsapp 2>/dev/null | tr -d '\r')" ]; then return 0; fi
    sleep 2; t=$((t + 2))
  done
  return 1
}

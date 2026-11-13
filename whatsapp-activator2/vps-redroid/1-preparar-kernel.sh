#!/usr/bin/env bash
# Passo 1: deixa a VPS pronta para o Android em contêiner.
# Instala o kernel genérico do Debian (que tem o módulo binder) e marca para ele ser usado
# SÓ NO PRÓXIMO reinício. Se ele não ligar, um novo reinício volta sozinho ao kernel atual.
#   sudo bash 1-preparar-kernel.sh
set -euo pipefail
. "$(dirname "$0")/comum.sh"
precisa_root

# shellcheck disable=SC1091
. /etc/os-release
[ "${ID:-}" = debian ] || die "este kit é para Debian; esta VPS é ${PRETTY_NAME:-desconhecida}."

virt=$(systemd-detect-virt 2>/dev/null || true)
case "$virt" in
  lxc|lxc-libvirt|openvz|systemd-nspawn|docker|podman|wsl)
    die "esta VPS é um contêiner ($virt): o kernel é o do provedor e não pode ser trocado. Precisa de uma VPS KVM." ;;
esac
ok "virtualização: ${virt:-nenhuma}"

if modprobe -n binder_linux 2>/dev/null || [ -e /dev/binder ] || grep -qw binder /proc/filesystems; then
  ok "o kernel atual ($(uname -r)) já tem binder. Não precisa trocar: rode 2-instalar-android.sh."
  exit 0
fi
info "o kernel atual ($(uname -r)) não tem binder; vou instalar o kernel genérico do Debian"

[ -f /boot/grub/grub.cfg ] || die "não há /boot/grub/grub.cfg: esta VPS não liga pelo GRUB, o kernel é escolhido pelo provedor. Procure no painel do provedor uma opção de kernel."

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y linux-image-amd64

novo=$( (ls -1 /boot/vmlinuz-* 2>/dev/null || true) | sed 's|^/boot/vmlinuz-||' | grep -E -- '-amd64$' | grep -v cloud | sort -V | tail -1)
[ -n "$novo" ] || die "o kernel genérico não apareceu em /boot depois de instalar."
find "/lib/modules/$novo" -name 'binder_linux.ko*' | grep -q . \
  || die "o kernel $novo foi instalado mas não tem binder_linux. Mande a saída deste script."
ok "kernel genérico $novo instalado, com binder_linux"

# Escolha do kernel por "entrada salva" + "só no próximo reinício".
[ -f /etc/default/grub.antes-redroid ] || cp /etc/default/grub /etc/default/grub.antes-redroid
if grep -q '^GRUB_DEFAULT=' /etc/default/grub; then
  sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/' /etc/default/grub
else
  echo 'GRUB_DEFAULT=saved' >> /etc/default/grub
fi
if grep -qs '^GRUB_DEFAULT=' /etc/default/grub.d/*.cfg; then
  echo "AVISO: há GRUB_DEFAULT também em /etc/default/grub.d/:" >&2
  grep -s '^GRUB_DEFAULT=' /etc/default/grub.d/*.cfg >&2 || true
  die "comente essa linha (ponha # na frente) e rode este script de novo."
fi
update-grub

atual_ent=$(grub_entrada "$(uname -r)") || die "não achei o kernel atual no grub.cfg."
novo_ent=$(grub_entrada "$novo")       || die "não achei o kernel $novo no grub.cfg."
grub-set-default "$atual_ent"
grub-reboot "$novo_ent"

mkdir -p /var/lib/redroid-kit
echo "$novo" > /var/lib/redroid-kit/kernel-novo

cat <<EOF

PRONTO. Próximo passo:
  1. reinicie a VPS:   reboot
  2. entre de novo e confira:   uname -r     (deve mostrar $novo)
  3. rode:   sudo bash 2-instalar-android.sh

Se a VPS não voltar em ~5 minutos, use "reiniciar/forçar reinício" no painel do
provedor: o reinício seguinte volta sozinho para o kernel atual ($(uname -r)).
EOF

#!/usr/bin/env bash
# Só lê informações da VPS; não muda nada. Rode e mande a saída inteira.
#   sudo bash 0-diagnostico.sh

sec() { echo; echo "=== $* ==="; }

sec "sistema";        grep -E '^(PRETTY_NAME|VERSION_ID)=' /etc/os-release
sec "kernel";         uname -r
sec "virtualizacao";  systemd-detect-virt 2>/dev/null || echo "?"
sec "cpu/memoria";    nproc; free -h | head -2
sec "disco";          df -h / /boot /var/lib/docker 2>/dev/null
sec "docker";         docker version --format 'docker {{.Server.Version}}' 2>&1 | head -1
                      docker compose version 2>&1 | head -1
sec "grub";           ls -l /boot/grub/grub.cfg 2>&1
                      grep -h '^GRUB_DEFAULT' /etc/default/grub /etc/default/grub.d/*.cfg 2>/dev/null
                      ls /boot/vmlinuz-* 2>/dev/null
sec "binder no kernel atual"
  modprobe -n -v binder_linux 2>&1 | head -2
  grep -w binder /proc/filesystems || echo "sem binderfs carregado"
  ls -l /dev/binder* 2>/dev/null || echo "sem /dev/binder*"
  grep -h -E 'CONFIG_ANDROID_BINDER' "/boot/config-$(uname -r)" 2>/dev/null
sec "kernel generico disponivel"
  apt-cache policy linux-image-amd64 2>/dev/null | head -3
sec "porta 5555";     (ss -ltnp 2>/dev/null | grep -w ':5555') || echo "livre"
sec "adb";            command -v adb || echo "adb nao instalado"

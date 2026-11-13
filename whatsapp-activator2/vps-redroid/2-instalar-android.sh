#!/usr/bin/env bash
# Passo 2 (depois do reinício): liga o Android em contêiner, instala o WhatsApp oficial e
# agenda a "manutenção" (abrir o WhatsApp 2x por semana para o WhatsApp Web não cair).
#   sudo bash 2-instalar-android.sh
set -euo pipefail
. "$(dirname "$0")/comum.sh"
precisa_root
cd "$KIT_DIR"

# 1. binder
modprobe binder_linux devices=binder,hwbinder,vndbinder 2>/dev/null \
  || [ -e /dev/binder ] \
  || die "o kernel $(uname -r) não tem binder. Rodou 1-preparar-kernel.sh e reiniciou? (uname -r deve ser o kernel sem 'cloud')"
for d in binder hwbinder vndbinder; do
  [ -e "/dev/$d" ] || die "/dev/$d não existe depois de carregar o binder. Rode: dmesg | grep -i binder  e mande a saída."
done
ok "binder carregado (/dev/binder, /dev/hwbinder, /dev/vndbinder)"
echo binder_linux > /etc/modules-load.d/redroid.conf
echo 'options binder_linux devices=binder,hwbinder,vndbinder' > /etc/modprobe.d/redroid.conf
# Os nós /dev/binder* nascem 0600 (só root). Dentro do Android, servicemanager, hwservicemanager e
# os HAL rodam como "system" e precisam abrir o binder: sem 0666 o Android fica em loop de reinício
# ("Binder driver could not be opened"). A regra udev mantém isso nos próximos reinícios.
printf 'KERNEL=="binder", MODE="0666"\nKERNEL=="hwbinder", MODE="0666"\nKERNEL=="vndbinder", MODE="0666"\n' \
  > /etc/udev/rules.d/99-redroid-binder.rules
udevadm control --reload 2>/dev/null || true
chmod 0666 /dev/binder /dev/hwbinder /dev/vndbinder
ok "binder com permissão 0666 e regra udev; vai carregar sozinho nos próximos reinícios"

# 2. o kernel novo funcionou: passa a ser o padrão
if [ -f /var/lib/redroid-kit/kernel-novo ] && [ "$(uname -r)" = "$(cat /var/lib/redroid-kit/kernel-novo)" ]; then
  ent=$(grub_entrada "$(uname -r)") && grub-set-default "$ent" && ok "kernel $(uname -r) agora é o padrão do GRUB"
fi

# 3. docker, adb, apk, porta
docker info >/dev/null 2>&1 || die "Docker não está respondendo (docker info)."
docker compose version >/dev/null 2>&1 || die "falta o 'docker compose' (pacote docker-compose-plugin)."
if ! command -v adb >/dev/null; then
  info "instalando adb"
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq adb
fi
ok "adb: $(adb version | head -1)"
[ -f "$KIT_DIR/WhatsApp.apk" ] || die "copie o WhatsApp.apk para $KIT_DIR (veja LEIA.md)."
if [ "$(docker inspect -f '{{.State.Running}}' redroid 2>/dev/null)" != true ] \
   && ss -ltn 2>/dev/null | grep -q ":${ADB_PORT}\b"; then
  die "a porta ${ADB_PORT} já está em uso nesta VPS. Troque ADB_PORT no arquivo config.env."
fi

# 4. Android
# .env -> config.env: assim "docker compose" rodado à mão (LEIA.md, "Dia a dia") lê a mesma
# porta e imagem dos scripts, sem precisar carregar o comum.sh antes.
ln -sfn config.env .env
info "baixando a imagem do Android ($REDROID_IMAGE, ~1 GB na primeira vez) e ligando"
docker compose up -d
espera_android 300 || die "o Android não ligou (detalhes acima). Mande essa saída."

# 5. WhatsApp
if adb -s "$SERIAL" shell pm path com.whatsapp 2>/dev/null | grep -q package:; then
  ok "WhatsApp já estava instalado"
else
  info "instalando o WhatsApp (pode levar 1-2 min)"
  adb -s "$SERIAL" install -r "$KIT_DIR/WhatsApp.apk" || die "a instalação do APK falhou (mensagem acima)."
  adb -s "$SERIAL" shell pm path com.whatsapp | grep -q package: || die "o Android não mostra o WhatsApp instalado."
  ok "WhatsApp instalado"
fi
if abre_whatsapp; then
  ok "WhatsApp aberto (processo rodando)"
else
  echo "AVISO: não confirmei o WhatsApp em primeiro plano. Abra-o pelo conectar.bat." >&2
fi

# 6. manutenção 2x por semana
cat > /etc/systemd/system/redroid-manter-vivo.service <<EOF
[Unit]
Description=Abre o WhatsApp do Android em contêiner por alguns minutos
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/bin/bash $KIT_DIR/manter-vivo.sh
EOF
cat > /etc/systemd/system/redroid-manter-vivo.timer <<'EOF'
[Unit]
Description=WhatsApp do Android em contêiner: abrir 2x por semana

[Timer]
OnCalendar=Mon,Thu 04:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now redroid-manter-vivo.timer >/dev/null
ok "manutenção agendada: $(systemctl list-timers redroid-manter-vivo.timer --no-legend | awk '{print $1, $2, $3}')"

cat <<EOF

TUDO PRONTO NA VPS.
Agora, no seu PC, rode conectar.bat (veja LEIA.md) para ver a tela do Android,
cadastrar o número e conectar o WhatsApp Web.
EOF

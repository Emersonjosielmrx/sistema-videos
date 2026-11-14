# Máquinas enxutas — o que foi desligado em cada uma

Pedido da dona (14/11 01h): "retirar tudo que pode ser retirado do próprio sistema, permanentemente, pra economizar
processamento e RAM, como Bluetooth, serviços de impressão e tudo o possível, deixando apenas o Chrome, o Wi-Fi e os
serviços que precisamos pra rodar navegador e render. PC2, desktop e esse [PC1] precisam de Bluetooth, mas só isso.
Documente e liste tudo que desativou de cada um."

## O que FICA ligado em todas
Wi-Fi/rede (NetworkManager, wpa_supplicant), SSH, Tailscale, a tela (lightdm/Xfce — o Chrome precisa dela), som
(pipewire), DNS (systemd-resolved), cron, a acessibilidade at-spi (o Chrome usa), o keyring (guarda os cookies do Chrome).

## Parte 1 — usuário (FEITO 14/11 01h35, sem senha)
Script: `D:\tmp\enxugar\enxugar_usuario.sh`. Registro em cada máquina: `~/enxugar_desligados.txt`.
**Desfazer:** `bash ~/enxugar_desfazer.sh` na máquina.

| O que | STI | Acer | x200ma | Asus | HP |
|---|:-:|:-:|:-:|:-:|:-:|
| Bluetooth: bandeja (blueman) | ✅ | já não tinha | já não tinha | ✅ | ⏳ fora do ar |
| Bluetooth: transferência de arquivo (obex) | ✅ | ✅ | ✅ | ✅ | ⏳ |
| Impressão: bandeja (print-applet) | ✅ | — | — | ✅ | ⏳ |
| Atualizações do Mint (mintupdate, mintreport, mintwelcome) | ✅ | — | — | ✅ (+ mintdrivers aberto, 184 MB) | ⏳ |
| E-mail/agenda Evolution (3 serviços + alarme) | ✅ | ✅ | ✅ | ✅ | ⏳ |
| Câmera/celular/iPhone ao conectar (gvfs afc, gphoto2, mtp, goa) | ✅ | ✅ | ✅ | ✅ | ⏳ |
| Indexador de arquivos (tracker) | — | ✅ | ✅ | — | ⏳ |
| Localização (geoclue), teclado na tela (onboard), leitor de tela (orca) | ✅ | — | — | ✅ | ⏳ |
| Notas (sticky), troca de arquivos na rede (warpinator) | ✅ | — | — | ✅ | ⏳ |
| Placa de vídeo NVIDIA (nvidia-prime), SSH do keyring, pastas do usuário | ✅ | ✅ | ✅ | ✅ | ⏳ |

(— = não existia naquela máquina)

## Parte 2 — sistema (PRECISA DA SENHA: a dona cola em cada notebook)
Comando: `D:\tmp\enxugar\colar_em_cada_notebook.txt` (abrir no terminal do notebook, colar, digitar a senha).
Registro: `/root/enxugar_sistema.txt`. **Desfazer:** `sudo bash /root/enxugar_sistema_desfazer.sh`.

Desliga e trava (`systemctl disable` + `mask`): **bluetooth**, **impressão** (cups, cups-browsed), descoberta de rede
(avahi), modem 3G (ModemManager), atualização de firmware (fwupd + timer), perfis de cor (colord), relatório de erro
(kerneloops, whoopsie, apport), troca de placa de vídeo (switcheroo-control), perfil de energia (power-profiles-daemon),
montar pendrive (udisks2), instalador de pacotes (packagekit), **atualização automática** (unattended-upgrades,
apt-daily, apt-daily-upgrade, mintupdate-automation), e tarefas de manutenção (anacron, man-db, motd-news, e2scrub_all).

Status: ⏳ STI · ⏳ Acer · ⏳ x200ma · ⏳ Asus · ⏳ HP

## Windows (PC2 e desktop) — Bluetooth FICA (dona)
⏳ a fazer com cuidado (o PC2 é do hipercool — só tirar serviço do sistema, nunca worker): impressão (Spooler), Xbox,
Fax, Mapas, Telemetria, Windows Search, OneDrive/Teams na inicialização.

## Asus Eee PC 1015BX (14/11)
Ligado ao sistema como "asus" (`ssh asus`): AMD C-60 2 núcleos 1 GHz, 1,5 GB, Mint 22.3, disco 292 GB.
**Render: NÃO** — teste real (`celulares.py testar asus`) passou de 10 min num trecho que o PC1 faz em 24 s. Fica só
navegador (`maquina_remota.MAQUINAS["asus"]`, "lento"). Logins das contas: **só depois das 8h** (dona).

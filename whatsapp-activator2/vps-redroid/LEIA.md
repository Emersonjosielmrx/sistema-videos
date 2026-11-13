# WhatsApp numa VPS, sem emulador (Android em contêiner)

Um Android "sem tela" (Redroid) roda em Docker na VPS, com o WhatsApp oficial. Ele é o aparelho
principal do seu número. Você vê a tela dele no PC só quando precisa (scrcpy, por túnel SSH), e o
WhatsApp Web fica conectado nele. Duas vezes por semana a VPS abre o WhatsApp sozinha por 5 minutos,
para o WhatsApp Web não cair.

**Precisa:** VPS KVM com Debian 12 e Docker (as suas servem); ~1,5 GB de memória e ~4 GB de disco.
Não precisa de `/dev/kvm`. Precisa do módulo `binder` no kernel: o passo 1 instala o kernel do Debian
que tem esse módulo, e para isso **a VPS reinicia uma vez**.

## Qual VPS

- **Não use a `hermes-prod`**: o reinício derruba Hermes e o trader, e a regra é nada pesado nela.
- **Evite a `hermes-staging` (209)**: o guia de acesso diz que ela já foi invadida. Sua conta do
  WhatsApp ficaria lá dentro.
- **`hermes-bloqueio` (157)** é a candidata. O reinício derruba por ~1-2 min o roteador de IA e os
  proxies. Rode o diagnóstico antes para confirmar o kernel dela.

Abaixo uso `hermes-bloqueio`; troque se escolher outra. Os comandos são para o PowerShell ou cmd do
seu PC (a chave SSH já está configurada nele).

## Passo a passo

**Atalho: tudo com um comando.** No PowerShell, dentro desta pasta:

```
.\implantar.ps1 -Vps hermes-bloqueio
```

Ele copia o kit e o APK, roda o diagnóstico e o passo do kernel, e **para** se a VPS precisar
reiniciar. Depois do seu "pode reiniciar": `-Etapa reiniciar`; e por fim `-Etapa android`, que liga
o Android, instala o WhatsApp e roda os testes (salva a tela em `tela.png`). Os passos abaixo são o
mesmo caminho, feito à mão.

**0. Mandar o kit e o APK, e diagnosticar (não muda nada na VPS)**

```
ssh hermes-bloqueio "mkdir -p /opt/vps-redroid"
scp LEIA.md comum.sh 0-diagnostico.sh 1-preparar-kernel.sh 2-instalar-android.sh manter-vivo.sh docker-compose.yml config.env hermes-bloqueio:/opt/vps-redroid/
scp "D:\pc hp\hermes-call\whatsapp-activator\apk\WhatsApp.apk" hermes-bloqueio:/opt/vps-redroid/
ssh hermes-bloqueio "bash /opt/vps-redroid/0-diagnostico.sh"
```

(Os `scp` acima rodam dentro da pasta `vps-redroid`. Não use `scp -r` da pasta inteira: ela agora
tem o scrcpy dentro, que não precisa ir para a VPS.)

**1. Kernel com binder**

```
ssh hermes-bloqueio "bash /opt/vps-redroid/1-preparar-kernel.sh"
```

Se ele disser que o kernel atual já tem binder, pule para o passo 2. Senão, reinicie e confira:

```
ssh hermes-bloqueio reboot
ssh hermes-bloqueio "uname -r"
```

O `uname -r` deve mostrar o kernel **sem** `cloud`. O novo kernel vale só para esse reinício. Se a VPS
não voltar em ~5 min, force o reinício pelo painel do provedor: ela volta sozinha ao kernel antigo.

**2. Android + WhatsApp**

```
ssh hermes-bloqueio "bash /opt/vps-redroid/2-instalar-android.sh"
```

Liga o Android, instala o WhatsApp e agenda a manutenção. A partir daqui o kernel novo fica como
padrão.

**3. Ver a tela no PC e ativar o número**

1. O scrcpy 5.0 já está na pasta `scrcpy` ao lado do `conectar.bat` (`vps-redroid\scrcpy\scrcpy.exe`).
   Se um dia precisar baixar de novo: `scrcpy-win64-....zip` em https://github.com/Genymobile/scrcpy/releases.
2. O `conectar.bat` já aponta para `hermes-bloqueio`. Se usar outra VPS, troque a linha `set VPS=`.
3. Dê dois cliques no `conectar.bat`. Abre uma janela com a tela do Android.
4. Na primeira vez o WhatsApp mostra um aviso "You have a custom ROM installed": toque **OK**. É
   normal nesse Android em contêiner.
5. Depois dos termos, este Android (sem chip) cai na tela **"Link as companion device"**, com um QR.
   Não é essa. Toque em **⋮** (canto superior direito) > **"Register new account"** para chegar à
   tela do número.
6. No WhatsApp: digite o número, digite o código do SMS e crie o perfil.

**4. Conectar o WhatsApp Web (sem câmera, por código)**

1. No navegador, em web.whatsapp.com, clique em **"Entrar com número de telefone"** e digite o
   número. Aparece um código de 8 letras.
2. Na janela do Android: ⋮ > **Dispositivos conectados** > **Conectar dispositivo** >
   **"Conectar com número de telefone"**, e digite o código. Às vezes o próprio WhatsApp mostra uma
   notificação pedindo o código; dá para digitar por ela.

Pronto. Daqui em diante você só abre o `conectar.bat` se precisar mexer no WhatsApp do "celular".

## Dia a dia

| Quero... | Comando |
|---|---|
| ver a tela | `conectar.bat` |
| desligar o Android (economizar memória) | `ssh hermes-bloqueio "cd /opt/vps-redroid && docker compose stop"` |
| ligar de novo | `ssh hermes-bloqueio "cd /opt/vps-redroid && docker compose up -d"` |
| abrir o WhatsApp agora por 5 min | `ssh hermes-bloqueio "bash /opt/vps-redroid/manter-vivo.sh"` |
| ver quando a manutenção rodou | `ssh hermes-bloqueio "cat /opt/vps-redroid/manter-vivo.log"` |
| conferir se está tudo de pé | `ssh hermes-bloqueio "bash /opt/vps-redroid/verificar.sh"` |
| cópia de segurança da conta | `ssh hermes-bloqueio "cd /opt/vps-redroid && docker compose stop && tar czf /root/whatsapp-android-backup.tgz android-data && docker compose up -d"` |

Desligado ou ligado, a manutenção abre o WhatsApp 2x por semana (segunda e quinta, 4h). Se o
Android estava desligado, ela desliga de novo depois.

**A conta mora em `/opt/vps-redroid/android-data`. Não apague essa pasta.**

## Se algo falhar

Cada script para com `ERRO:` e o motivo. Copie a saída inteira e mande.

**"O Android não terminou de ligar"** com `zygote`/`servicemanager` em `restarting` e, no
`docker exec redroid logcat -d | grep -i binder`, a frase "Binder driver could not be opened": os
nós `/dev/binder*` estão `0600` (só root). Confira com `stat -c '%n %a' /dev/binder` na VPS; tem de
ser `666`. O `2-instalar-android.sh` já grava a regra udev que corrige isso; se precisar na hora:
`chmod 0666 /dev/binder /dev/hwbinder /dev/vndbinder && docker restart redroid`.

Testado em 08/10/2026 na `hermes-bloqueio` (Debian 13): kernel genérico com binder, Android 12
(Redroid) ligando, WhatsApp 2.26.39.75 instalado e aberto na tela do número, manutenção agendada, e
a janela do scrcpy pelo túnel. O Android fica usando ~630 MB e ~2% de uma CPU.

**O que falta, e só você pode fazer:** digitar o número e o código do SMS na janela do scrcpy. Essa
tela do WhatsApp recusa comando automático (`adb shell input tap/text` não tem efeito nela, de
propósito) — por isso o kit para aqui. Abra o `conectar.bat` e digite você mesma.

Se a tela do número não reagir nem ao seu teclado e mouse na janela do scrcpy, não insista: o plano B
é ativar a conta no emulador do Windows (AVD), que tem touchscreen emulado, e depois mover a pasta da
conta para a VPS.

Aviso para o futuro: a VPS ficou com dois kernels (o `cloud` antigo e o genérico). Se um dia uma
atualização apagar o kernel genérico antigo, o GRUB pode voltar ao `cloud` no reinício seguinte e o
Android não liga ("não tem binder"). Nesse caso, rode de novo `1-preparar-kernel.sh` e reinicie.

## Desfazer tudo

```
ssh hermes-bloqueio "systemctl disable --now redroid-manter-vivo.timer; cd /opt/vps-redroid && docker compose down"
ssh hermes-bloqueio "cp /etc/default/grub.antes-redroid /etc/default/grub && update-grub"
```

O segundo comando volta o GRUB para a configuração de antes. Depois do próximo reinício, confira com
`uname -r` qual kernel ligou: com os dois kernels instalados, a ordem padrão do GRUB pode escolher o
novo.

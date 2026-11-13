# Entrega de 08/10/2026 — WhatsApp sem celular

Quem recebe esta pasta provavelmente não viu nada do que está aqui. Este arquivo explica o que
existe, em que pé está e o que **não** se faz. Leia inteiro antes de mexer.

O trabalho foi feito no PC do Emerson, numa cópia do projeto em `D:\pc hp\hermes-call\`. Os
documentos antigos do Hermes Call citam `D:\hermes-call`, `D:\hermes-wt\pc-base` e
`C:\Users\Haylla\...` — esses caminhos **não existem** nessa máquina. Ajuste mentalmente.

---

## 1. A regra que vale acima de tudo

**Não se automatiza o cadastro de um número no WhatsApp.**

A tela de registro (`com.whatsapp.registration...RegisterPhone`) ignora toque e teclado injetados.
Isso é proteção anti-bot do WhatsApp, de propósito. O número e o código do SMS são digitados **por
uma pessoa**, na janela do celular virtual. Quem recebe esta pasta não deve escrever automação para
preencher esses campos nem procurar caminho que faça o toque injetado passar.

Essa decisão já foi tomada três vezes no projeto, de forma independente:

- `AVALIACAO.md`, seção 3, caminho B — *"Não recomendo e não faço... é burlar a proteção dele, com o
  maior risco de banimento."*
- `AVALIACAO.md`, seção 8 — *"É barreira contra cadastro automático: o programa não contorna."*
- `hermes-call/CONTINUAR_DAQUI.md` — *"O caminho de registrar o número sem aplicativo nenhum, por
  cliente não oficial, o agente do PC NÃO faz."*

Motivo prático, além do princípio: número cadastrado por automação é o perfil que o WhatsApp bane, e
o banimento cairia no número do cliente, dentro do painel da dona.

---

## 2. O que a dona quer construir

No painel do Hermes Call, em "nova conexão", um botão alternativo ao QR Code. O cliente digita o
número, confirma, e o sistema conecta a linha sozinho. O celular virtual liga só quando pedido e
desliga depois, para não consumir recurso.

Decisão dela em 08/10/2026: o painel oferece **os dois** caminhos abaixo, começando pelo primeiro.

| Caminho | Para quem | Estado |
|---|---|---|
| **Pareamento por código** (8 dígitos) | cliente que **já tem** WhatsApp no número | código escrito, não publicado — ver seção 3 |
| **Cadastro do zero** (celular virtual + SMS) | número novo, **sem** conta | travado numa incógnita — ver seção 5 |

São coisas diferentes e é fácil confundir: o pareamento por código **não cria conta**. Ele conecta o
Hermes como aparelho secundário de uma conta que já existe, igual ao WhatsApp Web. Não há SMS nele.

---

## 3. Hermes Call v0.10.0 — a aba "Por código" (pronta, não publicada)

Está em `hermes-call-v0.10.0\`, com o `LEIA.md` próprio explicando como aplicar. Resumo:

- Dois arquivos do frontend mudaram. **Nenhuma mudança no backend** (o endpoint
  `POST /api/sessions/{sid}/pair-code` já existia desde antes e o agente do Telegram já usava) e
  **nenhuma migração de banco**.
- Validado com `npx tsc --noEmit` e `npx vite build` — os dois passaram.
- **Não foi commitado, não foi enviado ao GitHub e não foi publicado.**
- `VERSION` foi para `0.10.0` e o `CHANGELOG.md` ganhou a entrada.

O que **não** foi feito e falta: ver a tela renderizada com o painel logado. O código compila e tipa,
mas ninguém olhou o resultado na tela ainda.

---

## 4. O celular virtual na VPS 157 (rodando)

A pasta `vps-redroid\` é um kit que põe um Android em contêiner (Redroid) numa VPS, sem emulador e
sem `/dev/kvm`. Está **instalado e funcionando** na VPS `hermes-bloqueio` (157), em
`/opt/vps-redroid`. Leia o `vps-redroid\LEIA.md`.

Estado conferido em 08/10/2026 18:45:

| Item | Valor |
|---|---|
| Kernel | `6.12.111+deb13-amd64` (o genérico; o `cloud` do Debian não tem o módulo `binder`) |
| Imagem | `redroid/redroid:12.0.0_64only-latest` |
| Android | `sys.boot_completed=1`, de pé há mais de 10 h |
| WhatsApp | 2.26.39.75 instalado, aberto na tela do número |
| Manutenção | `redroid-manter-vivo.timer`, segunda e quinta 04:00 |
| Consumo | ~630 MB de memória, ~1,5% de CPU |
| A conta | `/opt/vps-redroid/android-data` (357 MB) — **nunca apagar depois de ativada** |

Para conferir tudo de uma vez: `ssh hermes-bloqueio "bash /opt/vps-redroid/verificar.sh"` (só lê,
tira um print, não toca na tela).

Para ver a tela no PC: `vps-redroid\conectar.bat` (abre um túnel SSH e o scrcpy).

**Armadilhas já resolvidas — não refazer o diagnóstico:**

1. Os nós `/dev/binder*` nascem `0600 root` e o Android aborta com *"Binder driver could not be
   opened"*. A regra udev que põe `0666` já está dentro do `2-instalar-android.sh`.
2. `monkey` não abre o WhatsApp nessa imagem; use `am start -n com.whatsapp/.Main`.
3. A VPS ficou com dois kernels. Se uma atualização remover o genérico, o GRUB volta ao `cloud` e o
   Android não liga. Conserto: rodar `1-preparar-kernel.sh` e reiniciar.
4. O kernel do Debian 13 **não tem binderfs** (`CONFIG_ANDROID_BINDERFS is not set`). Sem binderfs os
   dispositivos binder são globais: **um celular virtual ligado por vez**. Isso não atrapalha o
   desenho (ligar só quando pedir, desligar depois), mas impede rodar vários em paralelo.

**Regras da dona sobre as VPS:** só a `hermes-bloqueio` (157). Nunca a `hermes-prod` (Hermes e trader
com dinheiro real). Nunca a `hermes-staging` (209, já foi invadida). Não reiniciar a 157 sem ela
autorizar — o reinício derruba o OmniRoute e os proxies por 1-2 min.

---

## 5. A incógnita que trava o cadastro do zero

Sabe-se que `adb shell input tap/text` **não** tem efeito na tela do número (e tem efeito nas telas
anteriores). **Não se sabe** se o teclado e o mouse de uma pessoa, na janela do scrcpy, são aceitos
ali. Testes com clique sintético foram feitos e **foram inconclusivos** — o primeiro método usado
estava quebrado e invalidou as conclusões seguintes. Não repita esses testes: a resposta tem de vir
da dona, abrindo o `conectar.bat` e digitando.

As duas saídas:

- **Se o scrcpy for aceito:** dá para embutir a tela do Android no painel e o próprio cliente digita
  o número e o SMS ali. Uma pessoa digitando numa tela remota não burla nada.
- **Se não for aceito:** o celular virtual tem de morar numa máquina com janela de emulador de
  verdade (o AVD do Windows, onde o clique de mouse funciona porque passa pelo touchscreen emulado),
  e a tela remota passa a ser a do Windows, não a do Android.

Em qualquer dos dois casos, **depois** desse minuto de digitação tudo é automático: o Hermes gera o
código de pareamento, o ativador digita no celular virtual, a linha é confirmada, o Android desliga e
volta a ligar alguns minutos a cada ~10 dias (regra dos 14 dias do WhatsApp).

---

## 6. Números de teste

Formato usado pela dona: **55 91 9 XXXXXXXX** (E.164 brasileiro, 13 dígitos). O atual é
**5591984698653**. O número `9198474247` que aparece em documentos antigos está incompleto —
não usar.

Pedir SMS de registro gasta tentativa real e o WhatsApp limita repetição. Não dispare por engano.

---

## 7. O que ficou pendente de decisão

1. Publicar ou não a v0.10.0 (seção 3).
2. O resultado do teste da dona no scrcpy (seção 5).
3. Sobras do ativador antigo na VPS de produção, à espera do OK dela para apagar: conta
   `ac***@internal.local`, três linhas "Linha Campanha" sem pareamento, imagem Docker de 6,8 GB e a
   pasta `/opt/whatsapp-activator`. Detalhes no `AVALIACAO.md`, seção 6.

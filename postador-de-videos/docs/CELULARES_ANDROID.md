# Celulares Android no ecossistema: o que fazer e como ligar

> Escrito em 23/10/2026 para fazer depois, com a dona. Qualquer agente, inclusive um mais simples, pode seguir.
> Comandos do PC1 rodam no Git Bash ou no PowerShell do PC1.

## Onde paramos

| Celular | Tailscale | Termux | Acesso por chave | Uso |
|---|---|---|---|---|
| **Redmi A3** | `redmi-a3` = `100.87.168.9` (conectado em 23/10) | instalado | **falta** (passo 2) | a definir |

Os celulares **não têm chip**: servem de tela vertical e para tarefas leves. Com chip de dados, o ganho principal
seria IP de operadora para baixar vídeos do YouTube (ver o fim).

## Regras

1. Acesso **só por chave**. Nunca use senha (nem `passwd` no Termux), nem peça senha à dona.
2. Uma conta por celular, se um dia postar pelo aplicativo. Nada de like, comentário ou visualização automática
   (regra da dona; foi a causa do bloqueio de 04/09).
3. Celular não renderiza vídeo nem clona voz: esquenta e o Android mata o programa.

## Passo 1: Tailscale (no celular)

Instalar o aplicativo Tailscale pela Play Store e entrar com a mesma conta dos PCs. Conferir no PC1:
```
"C:\Program Files\Tailscale\tailscale.exe" status
```
O celular aparece com o nome do modelo (ex.: `redmi-a3`) e um IP `100.x.x.x`.

## Passo 2: acesso do PC1 ao Termux por chave

**No PC1**, servir a chave PÚBLICA (não é segredo; é a mesma que libera os notebooks) só na rede da Tailscale, por 40 min:
```
mkdir -p /tmp/chave && cp ~/.ssh/id_rsa.pub /tmp/chave/k && cd /tmp/chave && timeout 2400 python -m http.server 8799 --bind 100.118.234.102
```

**No celular**, abrir o Termux e colar (uma linha):
```
pkg install -y openssh && mkdir -p ~/.ssh && curl -s http://100.118.234.102:8799/k >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && termux-wake-lock && sshd && echo PRONTO
```
Se perguntar algo na instalação, Enter. Deu certo quando aparecer **PRONTO**.

**No celular, configurações (importante na Xiaomi):**
- Configurações › Apps › Termux › Economia de bateria › **Sem restrições** (senão a Xiaomi fecha o Termux).
- Deixar na tomada e no Wi-Fi de casa.
- Para o acesso voltar sozinho depois de reiniciar: instalar o app **Termux:Boot** (F-Droid, mesma origem do Termux) e
  criar `~/.termux/boot/sshd` com `termux-wake-lock; sshd` (o agente faz isso por ssh depois do passo 2).

**No PC1, testar** (porta 8022 é a do Termux):
```
ssh -o BatchMode=yes -p 8022 100.87.168.9 "echo CONECTOU; getprop ro.product.model; getprop ro.build.version.release"
```

## Passo 3: o que montar (em ordem)

1. **Prévia vertical antes de postar.** O Short pronto toca no celular em pé para a dona ver legenda, corte e volume
   numa tela de celular de verdade; aprovação continua pelo Telegram. Base pronta para reaproveitar: o botão "Ver" do
   telão (`D:\video-fila\vitrine.py` `pedidos()` manda o arquivo; `vitrine\player.py` toca). No celular o "player"
   pode ser o próprio Chrome do Android aberto pelo Termux (`termux-open-url`) ou uma página do painel.
2. **Conferir como o aplicativo do YouTube cobre o Short.** Abrir o Short no app do YouTube, tirar print e checar se
   botões e título do app tapam a legenda ou o rosto. Precisa de ADB por Wi-Fi (Opções do desenvolvedor › Depuração
   sem fio) ou do Termux:API; decidir com a dona.
3. **Tela fixa de "produção ao vivo"**: o que cada PC renderiza agora, fila do dia e a meta de 3 vídeos/dia. O painel
   do telão já tem a base (`D:\video-fila\vitrine\painel.html` + `vitrine_painel.py`); criar uma tela `celular` em
   `TELAS` com quadros verticais.
4. Outras telas possíveis: parede de Shorts (cada celular gira os últimos Shorts de um projeto, sem som), comentários
   chegando, placar de 48 h, os mesmos quadros do telão com os pop-ups de inscrito e mil views.
5. **Controle remoto**: tela com botões grandes (pausar postagem, ver o que espera aprovação, ligar/desligar projetos);
   é a Central de Vídeos (porta 8790 do PC1) em versão de celular.
6. **Tarefas leves no Termux**: narração com vozes da internet (edge-tts), chamadas de IA de roteiro/título, medição
   de visualizações. Só tarefas curtas.
7. **Vigia mútuo**: entrar em `VIGIADAS` de `D:\video-fila\vitrine\vigia_mutuo.py` (ou só vigiar, sem ser vigiado,
   porque celular desliga a tela/Wi-Fi).
8. **Gravar a voz da dona** para narração própria ou para melhorar a voz clonada (microfone do celular é melhor que o
   do notebook).

## Se um dia tiver chip com dados

- **IP de operadora para o yt-dlp** (o maior ganho): o celular no 4G vira proxy pela Tailscale para o PC1, com limite
  diário de MB (como o `PROXY_MB_DIA` da Webshare em `anime_fetch.py`).
- **Verificação de canal por SMS** (ex.: ForjaReact esperando a verificação única): a dona faz; o celular só recebe.
- **Aviso de internet de casa caída**: no 4G ele enxerga quando todo o resto some.

## 29/10 (Fable, D20): proxy do celular já está pronto no PC1

`D:\postador-de-videosin\proxy_celular.py` (tarefa ProxyCelular, a cada 5 min) abre `ssh -D` até o Termux e mede a
saída. Para funcionar falta só o celular: Tailscale aberto, passo 2 acima (sshd por chave) e, para o IP ser de
operadora, chip com dados e Wi-Fi desligado. Ver: `python bin\proxy_celular.py --status`. Quem usa: as 6 contas
TikTok de `config\proxy_celular.json` (teste dos canais mortos).

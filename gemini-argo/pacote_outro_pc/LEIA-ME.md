# Argon e Argon Pro no VS Code de outro PC

Este pacote coloca no Claude Code (VS Code) do outro PC os mesmos modelos do PC principal:

- **Argon Pro** (`argon-pro`): o Argon decide e o Gemini 3.8 executa as ferramentas. É o melhor para **código**.
- **Argon** (`gemini-4-argon`): o Gemini 4 Argon puro, com raciocínio alto. É o melhor para **texto**: roteiro, análise
  e revisão.
- E também: Argon + Gemini 3.8, Gemini 3.8, Opus 4.6 e Opus 5.5.

O pacote **não leva senha nem cookie**. O instalador pede a chave na hora.

## O que precisa antes

1. **VS Code** instalado.
2. A extensão **Claude Code** instalada no VS Code (em Extensões, procure "Claude Code", da Anthropic).
3. A **chave do OmniRoute** (começa com `sk-`). No PC principal ela fica na Área de Trabalho, pasta
   "Claude VS Code - Trocar Modelo", arquivo `settings_1_...json`, na linha `ANTHROPIC_AUTH_TOKEN`.

## Instalar (2 minutos)

1. Descompacte esta pasta em qualquer lugar do outro PC.
2. Dê **dois cliques em `INSTALAR.bat`**.
3. Cole a chave e aperte Enter.
4. Espere aparecer **PRONTO**.
5. Feche **todas** as janelas do VS Code e abra de novo.

O chat do Claude Code já começa no **Argon Pro**. Para trocar de modelo, use o seletor de modelo do chat ou digite
`/model gemini-4-argon` (Argon puro) ou `/model argon-pro`.

Para desfazer, dê dois cliques em `DESINSTALAR.bat`: ele volta as configurações de antes.

## Como funciona (por que é tão simples)

O outro PC não roda nada do Argon. Ele só aponta o Claude Code para o servidor `http://157.173.207.22:20133`, onde já
estão o Argon, o Argon Pro e os outros modelos. Por isso:

- **O PC principal precisa estar ligado.** O Argon passa por ele, pelo túnel que liga o PC principal ao servidor.
  Se o Argon não responder, confira se o PC principal está ligado e com internet.
- A cota é a mesma do PC principal: as mesmas 29 contas Pro, numa fila. Se aparecer "Nenhuma conta com cota do Argon
  agora", a mensagem diz a hora em que a próxima volta. Até lá, use o **Gemini 3.8**.
- Os avisos de cota no Telegram (bot do Opus, comandos `argon`, `5.5`, `opus` e `creditos`) continuam os mesmos.

## Bom saber

- O Argon é lento: de 10 s a alguns minutos por resposta, porque pensa no nível alto.
- O Argon não vê imagem nem PDF e não faz busca na web. Para isso, use o Gemini 3.8.
- Título curto e anúncio curto: o Gemini 3.8 faz igual e muito mais rápido.

## A pasta `codigo/` (opcional)

É uma cópia do projeto do Argon (`D:\gemini-argo` no PC principal), **sem cookies, sem contas e sem chaves**. Serve
de referência, ou para um dia rodar o Argon direto neste PC em vez de passar pelo PC principal. Para isso seria
preciso: Python 3.11+, `pip install requests playwright`, logar contas Google Pro num Chrome e adaptar o
`sync_cookies.py`, que hoje usa o cofre de navegadores do PC principal. O passo a passo das descobertas está em
`codigo/ARGON_MELHORIAS.md`. **Para só usar, nada disso é necessário.**

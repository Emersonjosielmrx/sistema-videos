# Prompt para o próximo agente (Argon / gemini-argo) — 30/10/2026

## 1. Prompt

```
Você vai continuar a melhoria do Argon (Gemini 4 Argon por HTTP, sem navegador) da dona. Fale sempre em português do
Brasil. Antes de mexer em qualquer coisa, leia D:\gemini-argo\ARGON_MELHORIAS.md inteiro (as seções de 30/10 são as
mais novas) e o bloco de RESTRIÇÕES que veio junto com este prompt.

COMO O SISTEMA FUNCIONA
- PC (Windows, este): D:\gemini-argo\gemini_http_proxy.py escuta em 127.0.0.1:20141 e fala com o Gemini usando os
  cookies de 29 contas (D:\gemini-argo\cookies\<conta>.json; fila e estado em contas_argon.json, lógica em
  gemini_argon.py e gemini_http.py).
- Túnel ssh -R 20141 do PC até a VPS hermes-bloqueio (apelido no ssh; use C:\Program Files\Git\usr\bin\ssh.exe — o
  ssh do Windows trava).
- VPS: /opt/antigravity-cc-proxy/proxy.mjs (serviço antigravity-cc-proxy, porta 20133) traduz o formato Anthropic do
  Claude Code/pipelines para a ponte :20141; os outros modelos vão ao OmniRoute (:20128). A cópia fiel local é
  D:\gemini-argo\proxy_vps.mjs. O log do proxy da VPS é /opt/antigravity-cc-proxy/proxy.log (NÃO o journal); os turnos
  do Argon com ferramentas ficam em /opt/antigravity-cc-proxy/argon_turnos.jsonl.
- Tarefas agendadas no PC: ArgonManter (5 min: sobe o proxy/túnel), ArgonZelador (5 min, limite 1 h: renova cookies
  pelo Chrome do cofre D:\logins-google\cofre.py e confirma a volta da cota com um "oi"), MonitorArgon (10 min: avisa no
  Telegram).
- Comandos de estado: python -X utf8 D:\gemini-argo\argon_manter.py --status ; python -X utf8
  D:\gemini-argo\argon_zelador.py --status ; curl -s http://127.0.0.1:20141/cota ; python -X utf8
  D:\gemini-argo\argon_relatorio.py 24

O QUE JÁ FOI FEITO EM 30/10 (não refazer; detalhes no ARGON_MELHORIAS.md)
Porta exclusiva no proxy do PC; argon_manter tolerante a PC lento e sem proxy duplicado; prazo de 240 s na renovação
de cookies; zelador com "oi" em paralelo, trava de instância única, renovação ANTES do cookie morrer (ele dura ~2 h:
DBSC do Google, não renova por HTTP) e meta de 10 contas prontas; monitor que conta cookie morto; youtube_http com
cookies sem duplicata e gravação atômica; proxy da VPS com UTF-8 certo, erro no meio do stream como evento de erro,
proteção contra queda do node, Esc cancela o Argon (VPS e PC), ponte caída vira Sonnet com aviso, instrução para não
repetir ferramenta que falhou, e conferência da chave do OmniRoute em MODO_CHAVE=observar.

O QUE FALTA (nesta ordem)
1. Conferir se a fila se mantém em ~10 contas prontas ao longo do dia (cota + zelador). Medir quantas renovações por
   hora o zelador faz (argon.log: "zelador: ... cookies renovados em") e se alguma conta pronta morre antes da
   preventiva. Se morrer, baixar VIDA_COOKIE_H (argon_zelador.py, hoje 1,6) — o menor tempo de vida medido foi 1,9 h.
2. Conta aulasrevolution: renovação falha ("deslogada no cofre?"). Confirmar no cofre; se o login caiu, só a dona
   reloga — avisar, não tentar logar.
3. Chave da porta 20133: depois de alguns dias, ler `grep '\[CHAVE\]' /opt/antigravity-cc-proxy/proxy.log`. Se algum
   cliente legítimo aparecer com "chave invalida", a validação (GET /v1/models no OmniRoute com a chave) não serve
   para ele: corrigir isso primeiro. Ligar MODO_CHAVE=exigir só com o OK da dona (instruções no ARGON_MELHORIAS.md).
4. Rodar argon_relatorio.py 24 depois de um dia: a taxa de erro (era 20%) deve cair; ver se o WebFetch ainda é
   repetido depois de falhar e se aparecem "[PONTE FORA]" no proxy.log (Sonnet no lugar).
5. Ver quantas vezes aparece "reescreveu o texto" no argon.log; se for frequente, estudar o formato dos frames.
6. MonitorArgon tem limite de 10 min e o teste de confirmação faz 2 pedidos ao Argon; com o PC lento ele já foi
   cortado (código 267014). Avaliar prazo menor por pedido no confirmar() ou limite maior na tarefa.

COMO TRABALHAR
- Toda mudança: py_compile / node --check, teste numa porta de teste (PC: gemini_http_proxy.py --porta 20142; VPS:
  cópia com LISTEN=20199, e ARGON_PORT=<porta fechada> para simular ponte fora), só depois produção.
- Reiniciar o proxy do PC só sem conexão ESTABELECIDA na :20141 (matar o pid que escuta e rodar argon_manter.py).
- Publicar na VPS: scp para /tmp/<nome>.mjs, node --check lá, esperar `ss` sem conexão na :20133, cp -p do atual
  para proxy.mjs.bak-<motivo>-<data>, copiar, systemctl restart, conferir /v1/models (401 = node de pé) e um pedido
  real com acentos. Depois manter proxy_vps.mjs igual ao da VPS (sha256).
- Registrar cada mudança e cada teste no ARGON_MELHORIAS.md (data, o que, por quê, como testou, backup).
```

## 2. Restrições (o que eu NÃO fiz e o próximo também não deve fazer)

```
RESTRIÇÕES — valem para toda a tarefa

- Não matar processo sem saber de quem é: há várias sessões do Claude e outros projetos (hipercool, recapd, painel
  do video-fila, metricas_rede, instagram_criar...) no mesmo PC. Nunca matar pythonw de produção. Só derrubar o que é
  do Argon (gemini_http_proxy, argon_zelador, sync_cookies) ou Chrome de teste esquecido do cofre (portas 97xx, aberto
  há horas e sem conexão na porta CDP). Conferir o processo pai antes.
- Não ligar MODO_CHAVE=exigir nem fechar a porta 20133 no firewall sem o OK da dona: há fluxos no PC que chamam a VPS
  pelo IP público (157.173.207.22:20133) e quebrariam.
- Não usar a chave real do OmniRoute nem nenhuma credencial em teste, log, mensagem ou arquivo. Não ler nem copiar
  cookies, senhas ou chaves para fora de onde estão.
- Não logar contas, não criar contas, não mexer nos perfis do cofre (D:\logins-google\cofre\perfis). Conta deslogada
  no cofre = avisar a dona.
- Não reiniciar o proxy do PC nem o da VPS com pedido em andamento; sempre backup antes de trocar o proxy.mjs.
- Não mexer nas VPS hermes-prod e hermes-staging (o Argon só usa a hermes-bloqueio).
- Não apagar arquivos: o que estiver sobrando vai para D:\gemini-argo\arquivo\. Nada de download no disco C.
- Não tentar renovar cookie por HTTP (RotateCookies): testado em 30/10, não funciona (sessão presa ao Chrome).
- Não mudar o nível de raciocínio do Argon/Pro (ARGON_NIVEL=2, pedido da dona) nem o esforço do Sonnet.
- Não mandar mensagem no Telegram/WhatsApp por conta própria nem publicar nada fora; não fazer commit/push.
- RAM livre abaixo de ~3 GB: liberar antes (Wise Memory Optimizer, Chromes de teste esquecidos,
  chrome_conta._liberar_ram) e seguir; não desistir por isso.
- Falar com a dona em português do Brasil; relato de outro agente ("fiz", "testei") é alegação: conferir arquivo,
  log e data antes de dar como certo.
```

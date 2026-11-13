# Prompt pro Agente do Frontend — "Modo Retomada de Campanha"

> Cole isto pro agente do front. É uma feature nova de UI + contrato com o backend.
> O backend (eu) implemento a lógica; você faz o controle visual no painel.

## O que é
Um **modo automático de re-contato** que o usuário liga/desliga por um botão no painel.
Quando ATIVO, para cada contato da campanha o sistema segue esta cadência:

1. **1ª tentativa:** liga (ligação de voz normal da campanha).
2. **Não atendeu:** aguarda um intervalo e **liga de novo** (2ª tentativa).
3. **Não atendeu de novo:** em vez de insistir na ligação, **manda uma mensagem de texto**
   perguntando algo como *"Oi! Tentei te ligar. Posso te ligar agora?"* — e o **agente de
   texto (chatbot) assume a conversa** a partir daí.
4. **Quando o contato responder a mensagem:** o agente de texto conversa; se o cliente
   topar, o sistema **agenda/dispara uma nova ligação** ("retomada").

Ou seja: liga → não atende → liga de novo → não atende → vira texto → agente de texto
reengaja → se o cliente aceitar, liga de novo. O agente de texto tem que estar SEMPRE
respondendo no WhatsApp em paralelo (não é só ligação).

## Controle visual no painel (o que você faz)
- Um **toggle "Modo Retomada de Campanha"** (ligar/desligar) — visível na tela da campanha
  ou nas configurações do agente.
- Quando ligado, mostrar os parâmetros editáveis:
  - **Nº de tentativas de ligação antes de virar texto** (default 2)
  - **Intervalo entre tentativas** (ex.: 30 min, 2h, "amanhã")
  - **Mensagem de texto de reengajamento** (editável; default: *"Oi! Tentei te ligar mais
    cedo. Posso te ligar agora?"*)
  - **Janela de horário** pra re-contato (respeitar horário comercial — anti-incômodo)
- Um indicador por contato mostrando em que etapa ele está: `1ª ligação` / `2ª ligação` /
  `aguardando resposta texto` / `reagendado` / `concluído`.

## Contrato com o backend (o que eu implemento e você consome)
- Campo no request da campanha: `retry_mode: boolean` + `retry_attempts: int` +
  `retry_interval_min: int` + `retry_text_message: string`.
- O backend expõe o **estado de cada contato** na cadência via o endpoint de status da
  campanha (`GET /api/sessions/{sid}/broadcast/{cid}`) — vou adicionar um campo
  `retry_stage` em cada resultado (`call_1`, `call_2`, `awaiting_text`, `rescheduled`, `done`).
- O agente de texto que responde no WhatsApp já existe (AgentChat/console) — o modo
  retomada só o aciona quando cai pro texto.

## Importante
- **Anti-bloqueio:** o re-contato respeita o mesmo aquecimento/limite diário e gap da
  campanha (não pode virar spam de ligação+texto — o número já foi banido 1x).
- O toggle desligado = comportamento atual (liga uma vez, não insiste).

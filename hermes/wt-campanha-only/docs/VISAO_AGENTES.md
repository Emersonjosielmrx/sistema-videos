# Visão de Arquitetura — Agentes, Canais, Webhook e Voz (roadmap)

Anotações da dona sobre como o sistema DEVERIA funcionar. É o alvo, não o
estado atual. Norte para reorganizar settings e implementar o que falta.

---

## 1. Agente Gerenciador (o que opera o sistema) — memória compartilhada

É o agente com quem a DONA conversa para comandar tudo: ligações, campanhas,
contatos, buscas, queries, modificações — **acesso e controle total do sistema**
(a ideia é ser um "Hermes Agent"/OpenClaw específico deste app). Deve funcionar
em **3 canais com a MESMA memória** (mesma conversa, não importa o canal):

1. **Telegram** — funciona hoje ✅
2. **WhatsApp** (PV ou grupo do próprio número) — **NUNCA funcionou**. Cria o
   grupo mas não responde (nem PV nem grupo). Ideia: falar consigo mesmo; as
   mensagens do bot aparecem com uma **tag** (ex: `[Hermes]`) para distinguir
   quem é quem (tudo aparece como a própria pessoa enviando). Objetivo: usar o
   bot **sem** segundo WhatsApp conectado e sem precisar saber Telegram.
3. **Chat web** — **IMPLEMENTADO** ✅ (Jul 2026). Painel com drawer lateral,
   mesmo endpoint `/api/console/send`, mesma memória `consoleChatJID` +
   `consoleGeneralThread`.

**Princípio:** o agente opera todo o sistema independente do canal. O canal é só
interface; cérebro e memória são os mesmos. Não precisa do chat para nada.

### Onde fica o prompt dele
O prompt do agente gerenciador (o que atende a DONA) **deve ficar na aba de
Agentes Especializados** junto com os outros — ver reorganização abaixo.

---

## 2. Reorganização das abas de Agentes (hoje está confuso)

Hoje: "Atendimento WhatsApp" e "Agentes Especializados" separados e mal
nomeados. O "Atendimento WhatsApp" na verdade É o agente do chat/telegram
(gerenciador), não um atendente de cliente.

**Correto:**
- **Uma aba só pro Agente Gerenciador**: junta Telegram + WhatsApp(PV/grupo) +
  chat web. É o MESMO agente em canais diferentes → mesma aba.
- **Aba "Agentes Especializados"**: cria **múltiplos agentes** — de **chamada**
  E de **mensagem** WhatsApp. Por agente define modelo/prompt + **quando usar**:
  por tag/etiqueta, etapa de atendimento, produto ou campanha. (Ex.: a dona tem
  vários produtos — o próprio sistema + outros — cada um com pitch diferente.)

## 3. "Notificar no Telegram" vai pros Agentes Especializados

Quando um **agente específico é acionado** (cliente chegou em certa etapa/tag),
dispara uma **notificação automática** (Telegram/WhatsApp/app). Config
POR-AGENTE, não global.

## 4. Hermes Agent vs OpenClaw

Se o cliente já tem um **Hermes Agent** ou **OpenClaw** próprio, a integração
serve para **dar acesso a esse agente externo + instruções de como operar o
sistema**. É uma ponte para um agente de fora comandar o Hermes Call. Mesma
finalidade pros dois; só muda o provedor do "cérebro".

---

## 5. Webhook — mais eventos e canais de notificação

Além dos eventos atuais (call.*, message.*, session.*), adicionar:
- **Mudança de etapa** (quando o pipeline de atendimento avançar — recurso a
  construir).
- **Campo definido pelo cliente, analisado pela IA**: ex. "quer falar com
  humano", "quer contratar". A IA detecta e dispara o evento.
- Outros eventos que a **API do WhatsApp** ofereça.
- **Canal de notificação escolhível**: Telegram, WhatsApp (número X), ou **app
  (marcar como BETA — o app ainda não existe)**.

## 6. Voz — multi-LLM com GET de vozes (sem digitar)

Hoje só Whisper (STT) + edge-tts. Adicionar mais provedores de TTS:
- **ElevenLabs** (muito boas), **Gemini** (vozes nativas), **GPT/OpenAI TTS**.
- Todas **bem implementadas**: ao clicar no campo, faz **GET das vozes/modelos
  reais** da API — a pessoa NÃO digita nome de modelo nem de voz (igual ao
  "Buscar modelos" da IA). Mesma regra para STT.

---

## Diagnóstico técnico — por que o WhatsApp não responde (autoreply.go)

`aiAutoReply` (cmd/server/autoreply.go:29) faz `if evt.Info.IsFromMe { return }`.
Quando a dona fala CONSIGO MESMA (próprio número), a mensagem é "from me" →
ignorada sempre. Por isso o grupo é criado mas nada responde. Além disso o modo
default "private" ignora grupos, e o agente usado é o "attendant" (não o
gerenciador). Para visão "falar consigo mesmo com tag" funcionar, precisa de um
caminho separado que: (a) aceite IsFromMe quando for o chat/grupo do
gerenciador, (b) use o agente GERENCIADOR (não attendant), (c) evite loop
(não responder às próprias respostas — marcar/prefixar com a tag `[Hermes]` e
ignorar mensagens que já tenham a tag).

---

## Ordem sugerida de implementação

1. **[CRÍTICO/infra] Voltar ao deploy Docker** → conserta áudio da ligação
   (codec MLow, quebrou no deploy systemd), ffmpeg, edge-tts, tudo do jeito
   original. Ver docs/DEPLOY.md.
2. Corrigir carga de config de voz no boot (Whisper fica desligado).
3. Ferramentas do agente gerenciador = acesso total (buscar campanhas, queries…).
4. Agente responder no WhatsApp (PV + grupo) com tag `[Hermes]`.
5. Multi-LLM de voz + GET de vozes.
6. Webhook: novos eventos + canal de notificação escolhível.
7. Reorg das abas (Gerenciador único vs Especializados) + notify por-agente.
8. **Chat web plugado no consoleReply — CONCLUÍDO** ✅
   - `client/src/components/chat/ManagerChat.tsx` (Drawer com Sheet, auto-scroll,
     Enter para enviar, limpeza de histórico, threads).
   - Botão `MessageCircle` no header do AppShell (ao lado do ThemeToggle).
   - Endpoints usados: `GET /api/console/threads`, `GET /api/console/messages`,
     `POST /api/console/send`, `POST /api/console/clear`.
   - Memória compartilhada via `consoleChatJID` = Telegram + WhatsApp + Web Chat.

---

## Notas de implementação — Jul 2026

### Chat Web (ManagerChat) — COMPLETO
- **Arquivo**: `client/src/components/chat/ManagerChat.tsx`
- **Integração**: `client/src/components/layout/AppShell.tsx` (botão no header)
- **Endpoints**:
  - `GET /api/console/threads` — lista salas (agente base + perfis especializados)
  - `GET /api/console/messages?thread=<id>` — histórico da thread
  - `POST /api/console/send {thread, text}` — envia e recebe resposta do agente
  - `POST /api/console/clear {thread}` — limpa histórico
- **UI**: Drawer lateral (Sheet do Radix), bolhas de chat (user right / bot left),
  auto-scroll, Enter para enviar, Shift+Enter para quebra de linha, loading state,
  seletor de thread (quando há perfis especializados), botão limpar.
- **Segurança**: mesmo auth do painel (authHeaders), redirect para login em 401.
- **Limitação conhecida**: polling simples (sem streaming SSE). Para streaming
  real, seria preciso expor `consoleReply` via endpoint SSE ou WebSocket.

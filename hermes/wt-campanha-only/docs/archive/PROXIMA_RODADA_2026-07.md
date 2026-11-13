# Próxima rodada — melhorias pendentes (anotado 2026-07-16)

Itens levantados pelo dono após o deploy da v0.1.0-beta. **Fazer na próxima rodada**,
depois de resolver o STT da ligação (ver item 0). Não mexer em produção sem rollback.

## 0. BUG bloqueante — STT da ligação (voz "trava")

- **Sintoma:** na ligação, a IA só toca os fillers ("ok, entendo") e não responde,
  nem devolve resumo do que o cliente falou. No Telegram funciona normal.
- **Causa (diagnosticada):** o modo CONVERSACIONAL (`internal/voice/voiceagent.go`) +
  filtro anti-alucinação (`internal/voice/stt.go` → `isRepetitionHallucination`) foram
  ao ar pela 1ª vez na v0.1.0 (commits antigos nunca deployados). O Whisper `tiny`
  alucina no áudio streaming da ligação (devolve sempre o mesmo texto, `len=667`), o
  filtro descarta → `text==""` → retorna ANTES da IA (voiceagent.go:300).
- **Por que Telegram funciona:** manda arquivo de áudio inteiro/limpo; a ligação manda
  streaming com ruído/VAD, que o `tiny` não dá conta.
- **Caminhos de fix (investigar):**
  1. STT melhor pra ligação: Groq (Whisper large, nuvem) ou `base`/`small` local
     (RAM na VPS é apertada). Groq é o mais provável de resolver rápido.
  2. Revisar o VAD/captura do `voiceagent` (pode estar mandando eco/ruído pro STT).
  3. Se manter local: afrouxar o filtro só é seguro junto com STT melhor.
- **Estado:** produção está na v0.1.0-beta com esse bug. Decisão de rollback pendente.

## 1. Agente Telegram — semântica de "mandar áudio"

- Quando a pessoa fala "quero mandar um áudio", **assumir que NÃO é uma mensagem de
  voz** — é tocar um áudio **na ligação** (ou disparo em massa com áudio). Racional do
  dono: se ela quisesse mandar áudio pra alguém, mandava direto no WhatsApp; ela está
  no bot pra LIGAR.
- Exceção: se ela disser que é **em massa** / campanha, aí é o fluxo de disparo.
- **Onde:** prompt/intução do agente gerenciador (Telegram) — ajustar o entendimento
  de "áudio" pra ligação por padrão, com desambiguação só quando falar "em massa".

## 2. Filler imediato após a pessoa parar de falar

- Os "ok / sei / entendo" já tocam antes do STT (voiceagent.go:277-285), mas o dono
  sente que **ainda demora um pouco** depois que ele para de falar. Já foi pedido antes
  e melhorou, mas dá pra melhorar mais.
- **Investigar:** latência do VAD detectar fim de fala (`VADConfig`, silêncio mínimo);
  tocar o filler no início do `onUtterance` já acontece — o atraso pode estar no VAD
  esperar confirmar o silêncio. Ver `vad_silence_ms` (default 550ms) — talvez reduzir.
- **Se não der pra melhorar mais:** dizer ao dono o porquê (limite do VAD/latência de
  rede), pra ele não pedir de novo.

## 3. Voz Piper na VPS (TTS mais rápido)

- Adicionar **Piper TTS** na VPS. Se for mais rápido que o edge-tts, ganha tempo na
  latência da resposta da ligação. Piper roda local (sem rede), o que ajuda muito.
- **Ação:** instalar Piper na VPS + integrar como provider TTS (opção ao lado de
  edge-tts/elevenlabs/gemini/openai em `internal/voice/tts.go`).

## 4. Rotador de chaves grátis do ElevenLabs (ElevenLabs Flash)

- Objetivo: usar **ElevenLabs Flash** (TTS de baixa latência) com as chaves grátis que
  o dono tem, via um **rotador** que roda SEPARADO do sistema (mesma ideia do Groq p/
  Whisper) — o app só aponta pra um endpoint que faz o rodízio das chaves.
- **Pergunta do dono:** vale a pena adicionar um proxy da Webshare (pra não bloquear as
  chaves), sabendo que adiciona latência? → **resposta na seção abaixo.**

## Resposta: proxy Webshare vale a pena? (depende do uso)

- **Para TTS da LIGAÇÃO (tempo real):** ⚠️ **provavelmente NÃO vale.** O ElevenLabs
  Flash existe justamente pra latência baixa (~75ms). Um proxy Webshare adiciona um
  salto de rede (dezenas a centenas de ms) que come boa parte desse ganho. Pra ligação
  ao vivo, latência é rei — melhor usar **Piper/edge-tts local** (zero rede a terceiro).
- **Para áudio PRÉ-GERADO / disparo em massa (não é tempo real):** ✅ **vale.** Aí a
  latência não importa (gera antes de ligar), e o proxy protege as chaves grátis de
  bloqueio por IP no rodízio.
- **Estratégia recomendada:** ElevenLabs Flash (com rotador + proxy) só pra
  **pré-geração/massa**; ligação ao vivo usa **Piper local** (item 3). Assim junta o
  melhor: voz boa onde dá tempo, latência baixa onde é ao vivo.
- ⚠️ **Risco a sinalizar:** rodar rotador de várias chaves grátis do ElevenLabs pode
  violar os Termos de Uso deles (contas grátis não são pra uso comercial/rodízio) e
  levar a ban das contas. Decisão do dono; anotado como risco.

---

## 5. Histórico do WhatsApp pra personalizar o 1º áudio/atendimento

- **Ideia (dono):** ANTES de criar o primeiro áudio / atender, PUXAR a conversa
  existente daquele contato no WhatsApp (se houver) e usar como base — pra o áudio e o
  atendimento serem **personalizados** desde o primeiro contato, não genéricos.
- **Como injetar sem atrasar o agente:** NÃO despejar o histórico cru no prompt (deixa
  o LLM lento). Em vez disso, gerar um **RESUMO curto** do histórico (1-3 frases: quem
  é, o que já falou, estágio) e injetar esse resumo dinamicamente no system prompt do
  agente. O resumo pode ser pré-computado (cache por contato) pra não pesar na hora.
- **Onde:** o whatsmeow/ConversationStore já tem histórico (`GetHistoryByUser`); falta
  (a) buscar por JID antes de montar o áudio/atendimento, (b) resumir via LLM barata,
  (c) injetar o resumo no `systemMsg` clonado (como já fazemos com prompt de etapa).
- **Ganho:** "Oi João, vi que você perguntou sobre X semana passada..." em vez de um
  script frio. Aumenta conversão.

## 6. Sub-projeto: agente em reuniões (Meet) com todo o conhecimento

- **Ideia (dono):** um sub-projeto pra o agente ENTRAR em reuniões (Google Meet) já
  com **todo o conhecimento** — contexto do cliente, histórico, produto — pra participar
  de forma útil (ouvir, responder, resumir, registrar).
- **Base que já existe:** `meet_agent_worker.py` + `cmd/server/meet_agent.go` (gate de
  wake-word/auto testado; worker de áudio via Playwright estava pendente de ambiente).
- **Escopo a definir (sub-projeto próprio):** (a) entrar na reunião, (b) captar/tocar
  áudio (Playwright + o pipeline de voz que já temos: STT→LLM→TTS Piper), (c) carregar
  o "conhecimento" (histórico do contato + base de produto + CRM) no prompt via resumo
  (mesma técnica do item 5), (d) registrar a ata/resumo no histórico buscável.
- **Nota:** é grande — merece planejamento e provavelmente versão/deploy próprios. Anotar
  como sub-projeto, não misturar com a esteira de ligações.

---

## Ordem sugerida pra próxima rodada

1. Resolver o STT da ligação (item 0) — bloqueante. **(Piper já foi na v0.2.0 — validar
   se resolveu o travamento na prática.)**
2. Filler mais imediato (item 2) — **feito na v0.2.0 (VAD 2 estágios); validar.**
3. Semântica de áudio no Telegram (item 1) — **feito na v0.2.0; validar.**
4. Histórico do WhatsApp → resumo dinâmico no prompt (item 5) — alto valor, baixo risco.
5. ElevenLabs Flash + rotador + proxy só pra pré-geração/massa (item 4) — com o risco
   de ToS registrado.
6. Sub-projeto Meet (item 6) — planejamento próprio.

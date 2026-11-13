# Roadmap Hermes Call — Melhorias de Ligação por Voz

> Documento vivo. Todas as ideias abaixo estão **aprovadas** pela dona.
> A ordem de execução segue as PRIORIDADES definidas. Estratégia: subir a campanha
> com o mínimo seguro (anti-bloqueio + voz ElevenLabs) e ir melhorando "com o carro
> em movimento" — sem parar a operação.

Última atualização: 2026-07-18

---

## 🎯 PRIORIDADES (ordem de execução)

### FASE 0 — Pré-campanha (BLOQUEANTE: fazer antes de disparar)
1. **Anti-bloqueio** (crítico — o número já foi bloqueado uma vez)
2. **Rotador de chaves ElevenLabs** (uso pessoal da dona) + voz **ElevenLabs Flash**

### FASE 1 — Aprovar e iniciar campanha
3. Ligação de teste final com ElevenLabs Flash → aprovação → **disparar campanha Solar B2B**

### FASE 2+ — Melhorar com o carro em movimento (durante a campanha)
- Multi-agente "peraí que vou verificar" + RAG isolado
- Correção do engasgo do 1º áudio
- Demais ideias do backlog abaixo

---

## 📋 BACKLOG COMPLETO (todas aprovadas)

### 🛡️ Anti-bloqueio (FASE 0 — prioridade máxima)
- [ ] **Aquecimento de número**: começar devagar (poucas ligações/dia) e escalar gradual.
- [ ] **Gap aleatório entre ligações**: já existe `gap_min_ms`/`gap_max_ms` — afinar valores seguros.
- [ ] **Rotação de números**: distribuir a campanha entre vários chips/sessões.
- [ ] **Detecção de padrão de risco**: parar sozinho se muitas ligações caírem rápido (sinal de bloqueio iminente).
- [ ] **Horário comercial only**: só discar em janela configurada (já existe `respect_schedule`).
- [ ] **Limite diário por número**: teto de ligações/dia por chip.

### 🔊 Voz / áudio (FASE 0: rotador ElevenLabs)
- [ ] **Rotador de chaves ElevenLabs** (USO PESSOAL da dona — NÃO é pros clientes, só na conta dela):
      várias chaves cadastradas; usa uma; quando dá erro de crédito/401/429, pula pra próxima
      automaticamente. Evita ligação falhar por crédito grátis esgotado sem trocar no painel.
- [ ] **Voz ElevenLabs Flash** como voz padrão das ligações (mais realista que edge-tts).
- [ ] **Rotador de vozes**: alternar vozes entre ligações (parece equipe, não 1 robô só).
- [ ] **Corrigir engasgo do 1º frame** de áudio no começo da chamada.
- [ ] **Mix de sons ambiente aleatório**: cada ligação com fundo diferente do pool.
- [ ] **Volume dinâmico do fundo (ducking)**: abaixa quando ela fala, sobe na pausa.
- [ ] **Emoção no TTS**: usar tags de emoção do ElevenLabs (animado, empático).

### 🎭 Naturalidade / disfarçar que é IA
- [ ] **Multi-agente "peraí que vou verificar"**: agente rápido (Groq) atende e conduz; quando
      precisa consultar (preço/RAG/DB), diz "só um instante que vou verificar" e um SUBAGENTE
      faz a consulta pesada; o primeiro retoma com a resposta. Resolve o risco do RAG alucinar.
- [ ] **Fillers contextuais**: "hmm", "deixa eu ver", "então...", pausas naturais (já tem básico).
- [ ] **Variação de abertura aleatória**: sortear entre 5-6 aberturas por ligação (anti-detecção).
- [ ] **Hesitações e auto-correção**: "ah não, na verdade..." como humano.
- [ ] **Ruído de digitação** durante o "peraí" (teclado ao fundo).
- [ ] **Velocidade de fala variável** conforme o contexto emocional.
- [ ] **Barge-in fino**: cliente interrompe naturalmente (JÁ IMPLEMENTADO no backend — falta expor no painel e afinar).

### 🧠 Inteligência / conversa
- [ ] **RAG isolado no subagente** (via multi-agente): base de conhecimento sem alucinar na resposta direta.
- [ ] **Memória entre ligações**: se ligar de novo pro mesmo número, lembra da conversa anterior.
- [ ] **Detecção de humor/objeção**: "não tenho interesse" vs "me liga depois" → agir diferente.
- [ ] **Transferência pra humano (handoff)** quando o lead esquenta (campos já existem, falta o fluxo).
- [ ] **Resumo automático + tags** no fim da ligação (custom_tags JÁ IMPLEMENTADO no prompt).
- [ ] **Agendamento na conversa**: "pode ser terça?" → marca no CRM/agenda.

### 📊 Painel / operação
- [ ] **Ver transcrição da conversa em tempo real no chat** (dona pediu — "pra eu ver a resposta").
- [ ] **Monitoramento de crédito das chaves** (cofre JÁ IMPLEMENTADO — falta plugar failsThisWeek nos call sites).
- [ ] **Filtros de data** (?range=1d/all) no dashboard/custos/CRM (blueprint).
- [ ] **Meet bot** (IA em reuniões Google Meet) — feature grande (blueprint).
- [x] **Wizard de onboarding completo** — Frontend e Backend integrados e finalizados com testes de estresse (Arena).

---

## 📞 CAMPANHA — Estado (2026-07-18)
- Lote de teste de 10 números (Solar B2B) disparado. Resultado: anti-ban PAUSOU no limite
  diário de 20 ligações/dia (número está no dia 1 de aquecimento pós-ban de 17/07).
- 3 discados = todos no-connect (números sem WhatsApp). 7 ficaram queued pra amanhã.
- ✅ Rotação de vozes premade funcionou (Jessica→Matilda→Alice alternando).
- ✅ Anti-bloqueio funcionou (pausou sozinho, não queimou o número).
- ⚠️ Qualidade da lista dos 59: revisar — os 3 primeiros eram números mortos.
- Vozes premade da rotação (funcionam em conta free): Jessica cgSgspJ2msm6clMCkdW9,
  Matilda XrExE9yKIg1WjnnlVkGX, Alice Xb7hH8MSUJpSbSDYk0k2.
- **Aquecimento:** hoje teto 20; amanhã 40; dia 4-6=80; 7-13=150; 14+=300.
- Script de disparo do lote: deploy/_campaign_lote.js (ajustar NUMS e voice_pool).

## ⏱️ LATÊNCIA da resposta na ligação (2026-07-18 21h) — ✅ CAUSA RAIZ ACHADA
- Dona atendeu teste no próprio número → conversa fluiu (motor 100% OK). CONFIRMADO que
  o "ninguém atende" dos leads = leads NÃO atenderam nos 45s (não é bug); ACK vem limpo.
- **FALSO ALARME dos "26s".** O log `voice ai reply` só é impresso DEPOIS que
  `ProcessConversationStream` retorna — e dentro dele, cada frase faz Synthesize+`playback`,
  que é BLOQUEANTE (toca o áudio inteiro em tempo real). Ou seja: o intervalo
  `transcribed → ai reply` nos logs = tempo que a Francisca leva pra FALAR a resposta toda,
  NÃO a latência de resposta. Prova: o gap encolhe com o TAMANHO da resposta
  (4 parágrafos=29s de fala; resposta curta=6s de fala), não com "aquecimento de rede".
- Componentes medidos da própria VPS: Gemini stream **67ms** pro 1º byte / 674ms total;
  STT Groq ~1s; ElevenLabs ~0.6s/frase. Graças ao streaming frase-a-frase, a 1ª frase
  começa a tocar em ~1-2s. Com filler ligado, a dona achou o tempo bom ("apreu com o
  tempo de resposta bom").
- FIX de medição: adicionado log `voice first audio {ms}` (transcrição → 1ª frase no ar) —
  esse é o tempo REAL percebido. Deploy beta em andamento; validar em ligação ao vivo (<2s).
- Melhoria de UX possível (backlog): pedir ao prompt respostas mais CURTAS (1-2 frases) pra
  ela não monologar 29s; deixar o lead interagir mais. Barge-in já ajuda a cortar.

## 🐛 BUG achado nas gravações (2026-07-18)
- Gatilho duplicado: saudação "Oi, tudo bem?" tocava/registrava 2x (SetInitialContext
  chamado 2x: pré-carga + runConversation). FIX: idempotente. Deploy em andamento.
- Vazamento de initial_context (IA falou a instrução interna): era teste antigo sem
  tts_message; com gatilho explícito não ocorre. Monitorar.

## ✅ JÁ FEITO (nesta rodada)
- Bug STT Groq (`/v1/v1/` → 404): corrigido no código + config. STT transcrevendo OK.
- Voz feminina edge-tts (Thalita Multilingual) — mais realista que Francisca padrão.
- **Som de fundo CONTÍNUO** (toca a ligação toda, não só na fala) — modo configurável. Dona aprovou: "ficou excelente, disfarça que é IA".
- Confirmado: som de fundo **NÃO adiciona delay** (mix aritmético, goroutine separada).
- Duração de chamada até 10 min + desliga com 1 min de silêncio/ruído.
- Barge-in configurável (backend).
- Cofre de credenciais IA (GET /api/settings/ai/credentials + tabela credential_failures).
- Tags/alertas customizados injetados no system prompt.
- GET /api/whatsapp/status.
- Wizard de onboarding (backend: ambient, grupo wpp pós-QR, team bcrypt, tags/alertas).
- **Frontend 100% Atualizado**:
  - Wizard Completo com **Arena Bate-Pronto** (Simulador de Estresse) e **Mágica IA** (Geração automática de Agente).
  - **Modo Retorno de Campanha (Voice-First)** implementado visualmente na Aba Campanhas e Configurações de Voz.
  - **Escalonamento de Pressão (Ghosting)** implementado no Wizard de Follow-Up.
  - UX polida e robusta para implantação.

## 🔑 DESCOBERTA IMPORTANTE — ElevenLabs grátis x voz brasileira (2026-07-18)
- As 23 chaves ElevenLabs da dona são de plano GRÁTIS.
- **Contas grátis NÃO podem usar vozes da biblioteca via API** (erro 402 `paid_plan_required`).
  Isso trava as vozes brasileiras boas (Marianne, Nina M., etc.).
- Só funcionam as vozes PREMADE padrão (Sarah, Jessica, Matilda, Alice) — que têm
  **sotaque americano** ao falar português (o Flash é multilíngue mas a voz é gringa).
- Opções de voz:
  - Premade ElevenLabs: timbre premium, sotaque gringo no PT.
  - Voz BR ElevenLabs: exige plano pago (upgrade de pelo menos 1 chave).
  - **edge-tts Thalita**: brasileira nativa, grátis, JÁ APROVADA pela dona ("ficou excelente").
- Rotador de 23 chaves + tabela de visão + Flash: TUDO funcionando (testado nas ligações).
- Decisão de voz: PENDENTE da dona (testando premade; fallback Thalita BR).

## ⚠️ PENDÊNCIAS TÉCNICAS ANOTADAS
- **pgvector não instalado** no Postgres (`extension "vector" is not available`) — bloqueia RAG. Instalar quando for mexer no RAG.
- **Engasgo no 1º frame** de áudio da chamada — investigar (provável: TTS antes do RTP estabilizar).
- **Nome vs voz**: roteiro diz "Francisca" mas voz é Thalita/ElevenLabs — alinhar nome da persona.
- **failsThisWeek** só popula depois de plugar RecordFailure nos call sites de LLM/STT/TTS.

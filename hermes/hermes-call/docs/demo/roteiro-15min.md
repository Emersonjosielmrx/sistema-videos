# Roteiro de Demonstração — Hermes Call SaaS (15 minutos)

**Audiência:** comprador/investidor técnico que quer ver o produto funcionando end-to-end.
**Pré-requisito:** ambiente `beta.hermescall.opus-sem-limites.com.br` (ou `hermescall.opus-sem-limites.com.br`) no ar e estável. Conta demo criada com `pro` + cupom `TESTE_GRATIS` aplicado.

**Conta demo:** `demo.buyer@hermescall.com` / `DemoBuyer!2026` (já cacheada).

---

## 0:00 — Abertura (1 min)

**Mostrar:** landing pública `https://hermescall.opus-sem-limites.com.br/`

**Falar:**
> "O Hermes Call é uma plataforma SaaS de atendimento multicanal com IA — WhatsApp, telefonia e agentes especializados. Tudo que vocês vão ver hoje é real, rodando em produção. Vou mostrar os 4 fluxos que o comprador usa no dia 1: signup, configuração de agente, campanha WhatsApp e dashboard de custo."

**Apontar:** CTA "Teste grátis" → leva pro signup.

---

## 1:00 — Signup e plano (1 min)

**Mostrar:** `/login` → "Criar conta" → preencher trial.

**Apontar:**
- Login já injeta token direto (P1-2 fix).
- Após signup, sidebar aparece com todas as 9 abas do trial.
- `/api/auth/me` retorna `features.tabs` — gating é server-side, não CSS.

**Falar:**
> "Tudo passa pelo backend. O frontend só renderiza o que o servidor autoriza."

---

## 2:00 — Aba Calls (2 min) — telefonia

**Mostrar:** clicar em "Chamadas" → `/calls`.

**Fazer:**
1. Conectar um número (Twilio) — botão já está habilitado no `pro`.
2. Fazer uma chamada de teste pro próprio número.
3. Mostrar a gravação aparecer em `/api/calls/recent`.

**Apontar:**
- STT (Whisper) transcreve em tempo real.
- TTS (ElevenLabs ou Piper) configurável por voz (`thalita`, `guilherme`).
- Latência fim-a-fim < 2s.

**Pergunta esperada:** "Quanto custa por minuto?" → já tem resposta em `/api/billing`.

---

## 4:00 — Aba Agentes (3 min) — IA + RAG

**Mostrar:** `/agents` → criar agente novo.

**Fazer:**
1. Criar "Vendedor de Plano Pro" — system prompt curto, persona "amigável".
2. Testar no chat lateral: mandar "oi, quero saber sobre o plano pro".
3. Apontar que o agente usa RAG (busca nos documentos do workspace).

**Apontar:**
- Cada agente tem prompt independente, ferramentas (tools) e personalidade.
- Integração com OpenAI, Anthropic e Gemini via env vars.

**Falar:**
> "Esse é o coração da plataforma — o cliente não programa o bot, ele CONTRATA um agente. Cada agente tem custo próprio, registrado em /api/cost."

---

## 7:00 — Aba Campanhas (3 min) — WhatsApp outbound

**Mostrar:** `/calls` ou `/agents` → "Campanhas" → criar campanha.

**Fazer:**
1. Criar tag "leads-quentes".
2. Importar 5 contatos (CSV ou manual — usar os do demo).
3. Selecionar agente "Vendedor".
4. Disparar campanha "Promoção Plano Pro — R$ 297/mês".

**Apontar:**
- Mensagem vai por Evolution/z-api (WhatsApp Business API não-oficial).
- Respostas entram como chat sessions e o agente responde automaticamente.
- Campanhas respeitam rate-limit do WhatsApp (1 msg/2s).

**Risco:** se o WhatsApp demo cair (instabilidade comum na z-api), ter backup: print do `/api/campaigns/:id/runs` mostrando as mensagens enfileiradas.

---

## 10:00 — Aba Cost (2 min) — billing granular

**Mostrar:** `/dashboard` → "Cost".

**Apontar:**
- Cada minuto de chamada tem custo (Twilio + STT + TTS).
- Cada mensagem de IA tem custo (tokens × modelo).
- Gráfico mostra breakdown por dia, por agente, por canal.

**Falar:**
> "O cliente vê o custo real, não um plano fixo. Isso é importante pra o ROI dele e pra nossa margem — vendemos margem, não assinatura."

---

## 12:00 — Aba CRM (2 min) — pipeline

**Mostrar:** `/crm` → funil kanban.

**Fazer:**
1. Criar deal "Empresa XPTO" no estágio "Lead".
2. Mover pra "Qualificado" → mostrar triggers (cria task, manda mensagem).

**Apontar:**
- Integração nativa com os agentes: lead que responde vira deal automaticamente.
- Webhook pro cliente final (RD Station, HubSpot) já documentado em `docs/API_MODULOS.md`.

---

## 14:00 — Segurança e fechamento (1 min)

**Mostrar:** `/api/version` → build + channel.

**Falar:**
> "Tudo que vocês viram passa por testes automatizados — 9 personas × 38 rotas, 15 vetores de ataque, regression.sh de 5min. Os specs ficam em `tests/e2e/` e rodam em todo PR."

**CTA:**
> "Posso abrir o backend agora — mostrar o /api/auth/me de vocês, ou agendar um piloto de 14 dias pra vocês testarem com seus próprios números."

---

## Se der ruim durante a demo

| Problema | Plano B |
|---|---|
| WhatsApp offline | Mostrar `/api/campaigns/:id` com status "queued" e print do run |
| Login falha | Conta demo cacheada — login com token direto via `/api/auth/me` |
| Chamada não conecta | Mostrar dashboard /cost com chamadas históricas reais |
| 5xx em qualquer tela | Reiniciar demo do ponto anterior; ter screenshot de backup de cada tela |
| Áudio com delay | Usar agente de texto puro — chat /agents, sem telephony |

## Materiais de apoio

- `docs/ARCHITECTURE.md` — diagrama do backend
- `docs/API_MODULOS.md` — referência de todas as rotas
- `RELATORIO_QA_12H.md` — relatório de QA dos últimos 12h (automatizado)
- `tests/screenshots/smoke-*.png` — screenshots de cada persona em cada aba

# Mapa completo — Botões mortos & dados fake do painel

Auditoria exaustiva de `client/src`. ~62 botões mortos + ~35 pontos de dado fake.
Legenda: 🟢 tem backend real (dá pra ligar) · 🔴 sem backend (precisa backend novo ou remover).

## Visão Geral (DashboardPage.tsx)
- 🔴 Live Feed (`feedEvents`, 4 eventos fixos) — sem endpoint de feed
- 🟢 "Ver Transcrição" (sem onClick) → `/api/transcripts`
- 🟡 Gráfico "Volume por hora" (curva inventada de baseCalls) → `/api/analytics` tem hourly
- 🔴 Donut de Sentimentos (40/35/15/10 fixos) — sem endpoint
- 🟢 Select de data (Hoje/7d/mês) — só muda estado local; `fetchDashboard(range)` já aceita param
- 🔴 "Exportar Relatório" → window.print()
- 🔴 Sparklines dos StatCards (arrays fixos)
- 🔴 Funil drop-off % (40/60/62%) e custo "R$0,45/lig" (labels literais; contagens dos nós são reais)

## Campanhas (CampaignsPage.tsx)
- 🟡 "Re-disparar Falhas" (sem onClick) → reusar mass-call
- 🟡 "Salvar Ganhos" (sem onClick) → createContactList
- 🟢 Row "Chamar no WhatsApp" / "Ligar via IA" (sem onClick) → mass-message/mass-call
- 🔴 "Exportar CSV" (sem onClick) — gerável no client
- 🔴 Drop-off por segundo (sintetizado) — sem endpoint
- 🔴 CampaignKanban.tsx — 100% mock (leads fake + setInterval + Math.random)

## Voice Ops (TelephonyPage.tsx)
- 🔴 Badges "Latência 120ms" / "Monitoramento Ativo" — literais
- 🔴 Cards SIP/Twilio (+55 11 4002-8922 etc.) + "Adicionar Número" — sem endpoint de números
- 🟡 Select TTS provider / Persona / switches interrupção+gravar — VoiceSettings/setRecording existem
- ✅ Radar ao Vivo (chamadas ativas) + "Encerrar" — JÁ REAL (corrigido)

## Contatos (ContactsPage.tsx)
- 🔴 "Importar" (sem onClick)
- 🟢 Row "Chamar no WhatsApp" / "Mais opções"
- 🟢 Bulk "Tag" (só toast) → assignTag/getTags
- 🔴 Bulk "Exportar CSV" (só toast) / "Excluir em massa" (só toast) — bulk delete existe em /api/contacts/bulk!
- 🟢 Filtros avançados (score/data/status/origem — sem handler) → client-side + listContactLists
- 🟢 360: Score(85)/Última chamada/Timeline/badges fixos → getLead/getConversation/getContactStats
- 🟢 360: Notas (textarea fixa, sem save) → addNote/getNotes
- 🟢 360: "Ligar"/"Msg"/"Ler transcrição" (sem onClick)

## CRM (SplitPaneCRM.tsx)
- 🔴 "Ações" / chip "Filtros Avançados" (sem handler)
- 🔴 Mock Activity timeline (eventos fixos)

## Settings — AISettings.tsx (God Mode, decorativo)
- 🔴 Failover switch, 2 selects fallback, router switch, 2 selects modelo, slider budget $15, select ação — nada salvo
- 🟡 Slider budget → /api/ai-cost PUT existe (usado no CostPage)

## Settings — ManagerAgentSettings.tsx
- 🔴 Tom(Mock) select, Vector Memory switch, Auto-Indexação, Ver Fragmentos, Permissions sandbox, Whisper switch, Trocar Grupo, Autonomia select, 4 Tool Matrix switches, Swarm status — sem backend

## Settings — outros
- 🔴 WebhookSettings: "Fila Morta (12 Eventos)" (sem onClick, 12 literal)
- 🔴 WorkspaceSettings: coluna "Cota Máxima $100" + "Personalizar Tema" (sem onClick)
- 🔴 AdvancedLab: Time Machine (v1.5/v1.4 fixos) + Rollback (toast) + Mic test (setTimeout) + Tool intercept (mock) + RAG Raio-X (chunks fixos)
- 🟢 SecurityPage: badge "IP Whitelisting ATIVO" → getIPWhitelist real; 🔴 "Data Masking PII" sem backend
- 🔴 LogsPage: badges "SIEM Datadog" / "Time-Travel" (sem onClick)

## Páginas com dado real parcial
- 🔴 TagsPage: auditLog vazio + "Carregar mais" morto + "IA Ativa/3 canais" literal (CRUD de tag é real)
- 🔴 BlocksPage: switches supressão (sem save) + defenseLog vazio + "Carregar histórico" morto + search/categoria sem handler (add/remove real)
- 🟢 CatalogPage: inputs Pitch/Desconto Máx/Upsell no dialog (sem bind) → /api/catalog já suporta os campos
- 🔴 AgendaPage: switches reminder 24h/follow-up 1h (sem save)
- 🔴 TeamPage.tsx — 100% mock (roster, performance, ranking, todos os botões)

## EASY WINS (backend existe — só ligar)
1. Dashboard date-range → fetchDashboard(range)
2. Contatos bulk Tag → assignTag/getTags
3. Contatos 360 Notas → addNote/getNotes
4. Contatos 360 Score/timeline → getLead/getConversation/getContactStats + /api/contacts/{jid}/profile
5. Contatos/Campanha "Ligar/WhatsApp" → mass-call/mass-message
6. Contatos bulk export/delete → /api/contacts/export, /api/contacts/bulk (JÁ CRIEI)
7. Telephony auto-record → setRecording; interrupção → updateVoice
8. AISettings budget → /api/ai-cost
9. Catalog pitch/desconto/upsell → /api/catalog
10. "Ver Transcrição" → /api/transcripts
11. SecurityPage IP badge → getIPWhitelist

## SEM BACKEND (precisa criar ou remover)
Páginas inteiras: CampaignKanban, TeamPage. Recursos "enterprise": Voice Ops SIP/persona,
AISettings fallback/router/circuit-breaker, ManagerAgent vector/sandbox/whisper/tool-matrix/swarm,
Webhook DLQ, Workspace quota/branding, AdvancedLab Time-Machine/RAG-Raio-X, Logs SIEM,
Dashboard live-feed/sentiment/sparklines, Tags/Blocks audit feeds, Data Masking PII.

---

## ⚠️ RE-AUDITORIA 2026-07-19 (madrugada) — o backend NÃO está faltando

Cruzamento automático: front chama ~157 rotas /api; backend TEM 293 rotas. Testados ao
vivo 9 endpoints que o doc marcava como problemáticos (`/api/transcripts`, `/api/analytics`,
`/api/contacts/export`, `/api/contacts/bulk`, `/api/ai-cost`, `/api/audit-log`,
`/api/contacts/stats`, `/api/contacts/notes`, `/api/security/ip-whitelist`) → **TODOS existem
e respondem**. As 6 rotas "faltantes" do cruzamento eram falsos positivos de parsing.

**Conclusão:** a maioria dos itens 🔴/🟡 acima é **FRONTEND com valor fixo que ignora um
backend que JÁ existe** — não é backend faltando. Trabalho do agente do FRONT: ligar o
componente ao endpoint.

**Exemplo confirmado (Dashboard → Sentimentos):** `GET /api/dashboard?range=` já devolve
`sentiment: [{name,value}...]` com dado REAL (medido: indefinido 37 / interessado 11 /
pediu_retorno 4 / sem_interesse 1). Mas `DashboardPage.tsx` ~L415-431 renderiza 40/35/15/10
LITERAIS. Fix no front: consumir `data.sentiment` (e `data.funnel`, que também é real).

**Ligar no front (backend 100% pronto, campo → endpoint):**
- Donut Sentimentos → `data.sentiment` de `/api/dashboard`
- Funil drop-off (contagens) → `data.funnel` (attempts/answered/engaged/leads) de `/api/dashboard`
- Feed de Auditoria (DashboardPage/Tags/Blocks) → `GET /api/audit-log`
- Contatos: export/delete em massa → `/api/contacts/export`, `/api/contacts/bulk`
- Contatos 360: score/timeline/notas → `/api/contacts/stats`, `/api/contacts/notes`, `/api/transcripts`
- Volume por hora → `/api/analytics` (campo hourly)
- Budget/custo → `/api/ai-cost`

**REALMENTE sem backend (confirmado FALTA — precisam de backend novo OU remover do front):**
`/api/team` (TeamPage), SIP/`/api/numbers` (Voice Ops telefonia externa), `/api/data-masking`
(PII), webhook DLQ, `/api/workspace/quota`. São recursos enterprise/telefonia externa —
NENHUM é usado pela campanha. Decidir caso a caso com a dona (custo alto, ROI baixo agora).

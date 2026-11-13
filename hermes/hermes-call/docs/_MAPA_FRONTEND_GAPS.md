# Mapa Frontend × Backend — Gaps (Hermes Call)

> Levantamento 2026-07-21 (varredura de client/src/pages [27 páginas] e components [~95]).
> Legenda: 🟢 REAL (ligado a endpoint que existe) · 🟡 PARCIAL (parte real, parte fake) ·
> 🔴 FAKE (mock/dado fixo/botão morto).

## Onde o "fake" se concentra hoje
EasyManagerWizard, HumanAssistTab, KnowledgeManagerTab, GlobalRagManager (datasets/fontes/
auditoria), SpecializedAgents (fallback mock + performance + rollback), AgentOrchestratorFlow
(histórico), AgentTrainerPanel (diff + 2 botões finais), AdvancedLab (RAG/Time-Machine) e
Dashboard (sparklines/volume/rankings/feed de auditoria).

> Já sanados no código (o doc BOTOES_MORTOS_E_DADOS_FAKE.md está desatualizado nesses):
> TeamPage (hoje tela honesta "em desenvolvimento"), CampaignKanban (real via SSE, sem
> Math.random), TelephonyPage (redireciona pra Settings de voz, sem cards SIP fake),
> AgendaPage (switches reais).

## EASY WINS — backend JÁ existe, só falta ligar o front
1. **Dashboard donut Sentimentos** → consumir `data.sentiment` de `/api/dashboard` (hoje 40/35/15/10 literais em DashboardPage.tsx:415-431).
2. **Dashboard Feed de Auditoria** → usar `/api/audit-log` em vez de 3 strings fixas (DashboardPage.tsx:124-140).
3. **Dashboard "Volume por hora"** → `/api/analytics` (campo hourly) no lugar da curva sintética `baseCalls*0.1..1.0` (:298-303).
4. **AgentTrainerPanel** → ligar `/api/training/prompts/{id}/activate` nos 2 botões `disabled` (:580-585) e renderizar o diff real do prompt.
5. **EasySettingsWizard** grupo/colaborador/alerta/tag (:846,927,960,1013) → ligar aos endpoints de settings em vez de só `toast`.
6. **ManagerAgentSettings** Tool Matrix / Autonomia / sliders → incluir no payload do `/api/settings/manager` (já existe) em vez de estado local cosmético.
7. **SpecializedAgents** → remover fallback mock (mostrar vazio honesto) e ligar `revertVersion` a endpoint real (ou esconder).
8. **AgentRagPanel** switch "Auto-Evolução" → persistir junto ao agente.
9. **ListsPage** botão "Disparar Campanha WhatsApp" (:311) → mass-message/mass-call (padrão já usado em callList).

## Rotas /api a CONFIRMAR no Go (o front chama; verificar se existem/funcionam)
`/api/orchestration`, `/api/meet/turn`, `/api/training/*`, `/api/agents/generate|refine|wargame|evaluate`,
`/api/leads/capture|export`, `/api/settings/easy-wizard-*`, `/api/settings/manager`,
`/api/settings/attendant`, `/api/contacts/collected`, `/api/n8n`.

## Recursos citados no doc mas AUSENTES do front atual (NÃO recriar sem pedido)
SIP/Twilio `/api/numbers`, `/api/team`, `/api/data-masking` (PII), webhook DLQ "Fila Morta",
`/api/workspace/quota`, badges "SIEM Datadog"/"Time-Travel" em Logs.

## Pendências pontuais
- **TranscriptsPage**: endpoint de deleção de transcrição (só `// TODO`, :54).
- **AdvancedLab**: RAG real (não `setTimeout`), Time-Machine, RAG Raio-X, tool intercept.
- **ListsPage**: métricas health/conversion/lastUsed por lista.
- **SplitPaneCRM**: timeline de atividade do lead (hoje "Mock Activity" fixo).

> NOTA: este arquivo é o mapa bruto. O plano de execução fica em docs/impl/*.

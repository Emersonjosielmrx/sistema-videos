# 01 — Easy-Wins: ligar telas prontas a endpoints que JÁ existem

**Esforço:** baixo (só frontend + às vezes 1 campo no backend). **Impacto:** alto (some
o "dado falso" que a dona vê). **Pré-requisito:** nenhum. Faça primeiro.

> Regra: o backend destes itens JÁ existe. NÃO crie rota nova. Só troque o dado fixo do
> React pela chamada de API. Depois de cada item, rode `cd client && npx vite build`.

## 1. Dashboard — donut de Sentimentos
- **Arquivo:** `client/src/pages/DashboardPage.tsx:415-431` (hoje valores fixos 40/35/15/10).
- **Backend já entrega:** `GET /api/dashboard` retorna campo `sentiment` (ver `cmd/server/dashboard.go:102`, `SentimentBreakdown`).
- **Fazer:** usar `data.sentiment` no donut. Se vier vazio, mostrar "sem dados ainda" (não inventar números).
- **Pronto quando:** o donut reflete as transcrições reais do recorte de data.

## 2. Dashboard — Feed de Auditoria
- **Arquivo:** `client/src/pages/DashboardPage.tsx:124-140` (hoje 3 strings fixas sobrescrevendo transcrições).
- **Backend:** `GET /api/audit-log` (existe, 1 rota).
- **Fazer:** listar os eventos reais de `/api/audit-log` no feed.
- **Pronto quando:** o feed mostra ações reais (login, criação de agente, etc), não texto fixo.

## 3. Dashboard — "Volume por hora"
- **Arquivo:** `client/src/pages/DashboardPage.tsx:298-303` (curva sintética `baseCalls*0.1..1.0`).
- **Backend:** `GET /api/analytics` (13 rotas — achar a que dá série horária; se não houver `hourly`, usar a diária existente e rotular certo, OU adicionar `hourly` no analytics — ver nota).
- **Fazer:** plotar a série real. Se o backend não tiver granularidade horária, NÃO simular: use diário e ajuste o rótulo, ou abra tarefa pequena de backend pra expor `hourly`.
- **Pronto quando:** o gráfico vem de dados reais (ou é honesto sobre a granularidade).

## 4. AgentTrainerPanel — 2 botões finais + diff real
- **Arquivo:** `client/src/components/settings/AgentTrainerPanel.tsx:580-585` (botões `disabled`).
- **Backend:** `POST /api/training/prompts/{id}/activate` (existe). Jobs/prompts todos existem (`training_api.go`).
- **Fazer:** (a) renderizar o diff real entre o prompt atual e a versão candidata (vem de `/api/training/prompts`); (b) ligar "Salvar e Ativar" ao `activate`; (c) "Auto-Corrigir Guardrails" → criar job com `filter=errors` (ver doc 05 se o filtro não existir ainda).
- **Pronto quando:** clicar Ativar troca o prompt em produção e o diff mostra a mudança real.

## 5. EasySettingsWizard — grupo/colaborador/alerta/tag
- **Arquivo:** `client/src/components/settings/EasySettingsWizard.tsx:846,927,960,1013` (hoje só `toast`).
  - Já chama `/api/settings/easy-wizard-partial` (:145) e `/api/settings/easy-wizard-ai` (:196) — **CONFIRMAR no Go se existem** (o grep achou o front, não confirmei backend; se faltar, é tarefa pequena de settings).
- **Fazer:** ligar cada ação (criar tag, convidar colaborador, criar alerta) aos endpoints de settings/CRM correlatos que já existem (tags: `/api/contacts/tags`; alertas: settings). Sem `toast`-e-esquece.
- **Pronto quando:** cada passo persiste de verdade e reaparece ao recarregar.

## 6. ManagerAgentSettings — Tool Matrix / Autonomia / sliders
- **Arquivo:** `client/src/components/settings/ManagerAgentSettings.tsx` (estado local cosmético).
- **Backend:** `PUT /api/settings/manager` (existe).
- **Fazer:** incluir a Tool Matrix, o nível de autonomia e os sliders no payload do PUT; carregar do GET ao abrir.
- **Pronto quando:** as configs persistem no backend e são aplicadas no agente gestor.

## 7. Diversos honestos
- **SpecializedAgents:** remover fallback mock; mostrar lista vazia honesta; `revertVersion` → ligar a endpoint real de versões (`/api/training/prompts`) ou esconder o botão.
- **AgentRagPanel:** switch "Auto-Evolução" → persistir junto ao agente (campo novo em `agent_profiles`, ver doc 05).
- **ListsPage:** botão "Disparar Campanha WhatsApp" (:311) → usar mass-message/mass-call (padrão de `callList`).
- **TranscriptsPage:** endpoint de deleção (`// TODO` :54) → `DELETE /api/recordings/{id}` já existe; ligar.

## Verificação geral
`cd client && npx vite build` deve passar. Abrir cada tela e confirmar que o dado é real
(sem números redondos suspeitos). Nenhuma rota de backend nova nos itens 1,2,4,6,7 (só 3 e 5
podem precisar de um campo).

# FIX-FRONT-1 + FIX-FRONT-2: Botões decorativos → reais (2026-07-23)

Auditoria COMPLETA de TODOS os botões/handlers das abas e sub-abas de Settings.
Cada um que era decorativo (só toast verde) agora persiste / chama endpoint / tem
feedback real.

## FIX-FRONT-1 (rodada 1 — 11 botões)

| Onde | Antes | Agora |
|---|---|---|
| `GlobalRagManager.tsx:526` — "Salvar Parâmetros e Reindexar Vetores" | só toast | `POST /api/rag/params` (17 sliders) + reindex em background |
| `HumanAssistTab.tsx:121` — "Salvar Ponto Eletrônico" | só toast | `PUT /api/human-assist` (5 campos) |
| `SpecializedAgents.tsx:1009` — "Ouvir" (amostra de voz) | só toast | `POST /api/tts/preview` → toca OGG no `<audio>` |
| `AgentOrchestratorFlow.tsx:212` — "Executar" (nó HTTP) | só toast | `POST /api/agents/test-node` (IA roda prompt) |
| `AgentOrchestratorFlow.tsx:215` — "Pin Data" (mock) | só toast | copia `JSON mock` pro clipboard |
| `AgentOrchestratorFlow.tsx:632` — "Limpar Histórico" | só toast | limpa `execHistory` state (drawer mostra empty state) |
| `AgentTrainerPanel.tsx:391` — "Ativar Shadow Mode" | só toast (mentira) | `disabled` com tooltip "feature em construção" |
| `AgentChatTest.tsx:196` — "Stress Test" | só toast (mentira) | `disabled` com tooltip "feature em construção" |
| `EasyAgentWizard.tsx:1842` — "Simular Cliente Grosseiro" | só toast (mentira) | `disabled` com tooltip "feature em construção" |
| `SpecializedAgents.tsx:1001` — dropdown de vozes | nomes OpenAI (502) | vozes Microsoft Neural reais |
| `tts_preview.go` — endpoint | 502 quando frontend mandava `alloy` | map OpenAI/ElevenLabs → edge-tts Neural |

## FIX-FRONT-2 (rodada 2 — 6 handlers que FINGIAM persistir)

Estes eram PIORES: o usuário reconfigurava, clicava em Salvar, via toast verde
e PERDIA TUDO no F5. Backend nunca ficava sabendo.

| Onde | Antes (perigoso) | Agora |
|---|---|---|
| `EasyManagerWizard.tsx:63` — "Salvar Gestor" | só toast (handler vazio) | `PUT /api/easy-manager/wizard` (envelope `{config: {...}}`) |
| `EasySettingsWizard.tsx:846` — "Cadastrar Grupo" | só toast + state local | `POST /api/settings/easy-wizard-partial` (draft persistente) |
| `AdvancedLab.tsx:676` — lixeira de doc RAG | só state local | `DELETE /api/rag/documents/{id}` (remove do backend) |
| `SpecializedAgents.tsx:92` — "Reordenar Hierarquia" | só state local | persiste em `localStorage` (vê no F5) |
| `AgentChatTest.tsx:646` — "Injetar Contexto" | só toast | valida JSON + envia como `injected_context` no `/api/agents/{id}/test` |

### Backend change: `injected_context` em `/api/agents/{id}/test`

Aceita novo campo `injected_context` (string JSON). Se vier preenchido + JSON
válido, prepende no system prompt como bloco "VARIÁVEIS DE SIMULAÇÃO (use pra
adaptar a resposta, como se fossem dados reais do CRM)". A IA passa a usar
esses dados (ex: `lead_vip=true` muda o tom).

## Endpoints NOVOS adicionados

- `GET /api/rag/params` — hidrata sliders na abertura do painel
- `POST /api/rag/params` — persiste 17 campos + dispara reindex async
- `GET /api/human-assist` — devolve config do "Ponto Eletrônico (SOS)"
- `PUT /api/human-assist` — persiste config; valida adminNumber obrigatório se enabled=true
- `POST /api/agents/test-node` — roda UM nó do orquestrador isoladamente
- `DELETE /api/rag/documents/{id}` — remove doc + chunks (já existia, agora está sendo usado)

## Validação

- `deploy/_test_mega.cjs` — **30/30 passando**:
  - /api/version
  - /api/rag/params (GET, POST, roundtrip, sanitização chunkSize>4000, strategy inválida, topK<1)
  - /api/human-assist (GET, PUT com adminNumber, PUT sem adminNumber → 400)
  - /api/agents/test-node (200 com response real, 400 sem prompt)
  - /api/tts/preview (Neural voice, alloy→FranciscaNeural mapping)
  - /api/easy-manager/wizard (PUT envelope correto, GET reflete save)
  - /api/settings/easy-wizard-partial (Cadastrar Grupo)
  - /api/rag/documents/{id} DELETE (cria + deleta)
  - Regressões: /api/settings, /api/agents, /api/rag/all-documents, /api/crm/promises, /api/rag/gaps

- `deploy/_test_fix_front_1.cjs` — 25/25 (regressão FIX-FRONT-1)
- `deploy/_test_bloco1_4.cjs` — todos os endpoints Bloco 1+4 funcionais (RAG pending, central, forms)

Deploy em beta: `hermes-call:beta v0.2.1`, build 20260723-1206, container healthy.

## O que ainda é "feature em construção" (botões disabled honestos)

1. **Shadow Mode** (AgentTrainerPanel) — comparar v_atual vs v_nova em produção sem afetar clientes
2. **Stress Test** (AgentChatTest) — worker de carga + métricas de rate-limit
3. **Simular Cliente Grosseiro** (EasyAgentWizard) — injetar mensagem no chat de teste

Esses 3 estão com `disabled` + tooltip explicativo. Nenhum vai te enganar com
toast verde mentiroso.

## Como promover

Se Haylla validar no beta:
```bash
cd D:/hipercool-refactor
node deploy/promote-stable.js
```

Se der problema:
```bash
node deploy/rollback.js
```

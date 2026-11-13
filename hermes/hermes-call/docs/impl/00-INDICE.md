# Plano de Implementação Backend — Índice Mestre

> **Como este plano foi feito (2026-07-21):** os 4 docs de spec (BACKEND_MASTER_PLAN,
> BACKEND_ROUTING_SPECS, backend_features_blueprint, API_MODULOS) descrevem a INTENÇÃO de
> produto, mas estão **desatualizados** — muita coisa foi implementada, renomeada ou movida
> sem atualizar o doc. Por isso cada item abaixo foi **verificado no CÓDIGO** (fonte da
> verdade: `cmd/server/httpapi.go` tem 370 rotas reais; ver `docs/_MAPA_BACKEND_EXISTENTE.md`
> e `docs/_MAPA_FRONTEND_GAPS.md`).

## ⛔ Agente de FRONTEND: leia [LEIA-ANTES-DE-CRIAR-TELA.md](LEIA-ANTES-DE-CRIAR-TELA.md) ANTES de mexer em qualquer tela
Toda tela nova/alterada tem que vir com o "pedido de backend" pronto (contrato + exemplo +
schema + passo a passo), no padrão dos docs 01-05. Botão que só dá `toast` é dívida, não entrega.

## Regra de ouro pra quem for implementar
1. **O código manda, não o doc.** Antes de criar qualquer rota/tabela, faça
   `grep` em `cmd/server/httpapi.go` (rotas) e nos `*_store.go` (tabelas). Se já existe, NÃO recrie.
2. **Migrations são aditivas** (`ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS`) —
   é o que garante o rollback. Ver VERSIONING.md.
3. **Não compila no PC de dev** (sem Go/gcc/MLow). Valide no CI ou revisão; build real é na VPS
   via `node deploy/deploy-beta.js` (ver docs/DEPLOY.md — cuidado com o ban de fail2ban).
4. Uma rota nova SEMPRE é registrada em `cmd/server/httpapi.go`.

---

## ✅ JÁ FEITO E FUNCIONANDO (NÃO reimplementar — confirmado no código)
Estas features os docs às vezes listam como "a fazer", mas já existem e têm handler real:

| Área | Rotas/arquivos reais | Status |
|---|---|---|
| RAG por agente | `/api/rag/documents\|search\|ingest-conversations` (rag_api.go, rag_store.go, pgvector) | ✅ |
| Chat de teste / Juiz / Wargame | `/api/agents/{id}/test\|evaluate\|wargame` (agent_wargame.go) | ✅ |
| Gerar/Refinar agente | `/api/agents/generate\|refine` (agent_generate.go) | ✅ |
| Treinador (jobs/prompts) | `/api/training/estimate\|jobs\|prompts\|prompts/{id}/activate` (training_api.go) | ✅ |
| Follow-up (cadenciador) | `/api/followup/*` — campaigns/steps/contacts/rules/sequences (followup_*.go) | ✅ (3 modelos coexistem — ver 04) |
| Agenda | `/api/agenda/*` (agenda_api.go) | ✅ |
| Catálogo/Vitrine | `/api/catalog/*` (catalog_api.go) | ✅ |
| Billing (Asaas) | `/api/billing/*` (billing_api.go) | ✅ |
| Captação de leads | `/api/leads/capture\|export` (lead_capture.go) | ✅ |
| Scheduled calls | `/api/scheduled_calls/*` (scheduled_calls_*.go) | ✅ |
| CRM board/etapas | `/api/crm/board\|stages\|move` (crm_api.go) | ✅ (etapas de desfecho corrigidas hoje) |
| Dashboard/Analytics/Audit | `/api/dashboard`, `/api/analytics` (13 rotas), `/api/audit-log` | ✅ (front não consome tudo — ver EASY-WINS) |
| Dual-agent settings | `/api/settings/manager\|attendant` | ✅ (só settings, não orquestração) |
| Meet Bot | `/api/meet/turn` | ✅ (falta mic virtual no host) |

---

## ❌ O QUE REALMENTE FALTA (verificado: NÃO existe no código)

Ordenado por **ROI da campanha** (pedido da dona). Cada um tem um doc próprio:

| # | Área | Doc | Por que falta / evidência no código |
|---|---|---|---|
| 1 | **EASY-WINS do front** (ligar telas prontas a endpoints que já existem) | [01-easy-wins-frontend.md](01-easy-wins-frontend.md) | Baixo esforço, alto impacto visual. Dashboard usa dados fixos; AgentTrainerPanel tem botões `disabled`. Backend já existe. |
| 2 | **Worker assíncrono + Promessas (Accountability)** | [02-worker-promessas.md](02-worker-promessas.md) | `grep asynq/river/queue` = nada. `agent_promises` não existe. É base pra #3 e auto-evolução RAG. |
| 3 | **Wizard "Gestor Fácil" (EasyManagerWizard)** | [03-wizard-gestor.md](03-wizard-gestor.md) | `/api/easy-wizard*` = **0 rotas**. `manager_profiles`/`is_manager` não existe. Front manda payload que ninguém recebe. |
| 4 | **Roteamento por níveis (1/2/3) + Orquestrador executor** | [04-roteamento-orquestrador.md](04-roteamento-orquestrador.md) | `logic_type`/`priority`/`ai_trigger`/`single_agent_mode` = nada. `orchestration_flows` só guarda o desenho do canvas; não há motor que execute o fluxo. |
| 5 | **KnowledgeGaps + fill-gap + auto-evolução RAG (shadowing)** | [05-knowledge-gaps-rag.md](05-knowledge-gaps-rag.md) | `knowledge_gap`/`fill-gap`/`shadow_mode` = nada. Depende do worker (#2). |
| 6 | **Extrator "Garimpo WhatsApp"** | [07-garimpo-whatsapp.md](07-garimpo-whatsapp.md) | `/api/whatsapp/chats` = **0 rotas**. Frontend concluído e consumindo mock. Depende da ligação com a engine (Baileys/Evolution API). |
> Consolidação pendente (dívida técnica a resolver junto, ver docs 02 e 04):
> - **3 modelos de follow-up** coexistem (fu_campaigns/fu_steps, followup_rules, followup_sequences) — decidir 1.
> - **Dupla implementação de sessions/messages** (cmd/server/sessionstore.go vs internal/sessions/store.go) — confirmar fonte da verdade antes de mexer em sessão/mensagem.
> - **contact_leads sobrecarregado** (CRM + jornada/lead_journey).
> - **api_keys vs hermes_api_keys** — o segundo pode ser legado morto.
> - **Analytics em 3 fontes** (internal/analytics, panel_analytics.go, crm_analytics.go) — padronizar.

---

## Projetos GitHub reaproveitáveis (recomendação)
> Web indisponível nesta sessão; recomendações por conhecimento estabelecido. Confirmar
> licença/manutenção antes de adotar.

- **Worker/fila (item #2):** `riverqueue/river` (fila Postgres-nativa em Go, enfileiramento
  transacional, cron/periódico, retries) — encaixa perfeito porque o projeto JÁ usa Postgres
  (pgx). Alternativa: `hibiken/asynq` (requer Redis — adiciona infra). **Preferir River** pra
  não subir Redis. Não é obrigatório uma lib: um cron simples em goroutine (padrão já usado em
  campaign_scheduler.go e scheduled_calls_cron.go) resolve o MVP das promessas.
- **Roteamento/orquestração multi-agente (item #4):** inspiração em `openai/swarm` (padrão de
  handoff/transfer_to_agent) — mas implementar nativo em Go (o projeto já tem transfer_to_agent
  na ligação). Não importar Python.
- **RAG (item #5):** já resolvido com pgvector nativo; não trocar por Pinecone/Qdrant (decisão
  firme da dona: sem infra externa).

## Sequência sugerida de execução
1º **01 (easy-wins)** — rápido, dá resultado visível já. →
2º **02 (worker+promessas)** — destrava #3 e #5. →
3º **03 (wizard gestor)** — fecha o maior buraco de UX (front manda payload no vazio). →
4º **04 (roteamento/orquestrador)** — feature grande, mais arriscada. →
5º **05 (knowledge-gaps)** — depende do worker.

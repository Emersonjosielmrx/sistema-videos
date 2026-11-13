# 02 — Worker assíncrono + Gestor de Promessas (Accountability)

**Esforço:** médio. **Impacto:** alto (destrava auto-evolução RAG e alertas do gestor).
**Verificado no código:** NÃO existe fila (`grep asynq/river/queue` = nada) nem tabela
`agent_promises`. `promise_text` em `scheduled_calls_api.go` é OUTRA coisa (texto da promessa
de retorno numa ligação agendada) — não confundir.

## Decisão de infra (importante)
O projeto já roda **crons em goroutine** (`campaign_scheduler.go`, `scheduled_calls_cron.go`,
tick de 1 min do follow-up). NÃO subir Redis. Duas opções:
- **MVP (recomendado):** um cron em goroutine que varre uma tabela `agent_promises` a cada
  N min — mesmo padrão dos crons existentes. Zero infra nova.
- **Robusto (depois):** biblioteca `riverqueue/river` (fila Postgres-nativa em Go, o projeto
  já usa pgx). Só adotar se o volume justificar.

Comece pelo MVP.

## Passo 1 — Migration da tabela
Em um arquivo store novo `cmd/server/promises_store.go` (espelhe o estilo de `crm_store.go`):
```sql
CREATE TABLE IF NOT EXISTS agent_promises (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  lead_jid TEXT NOT NULL,
  agent_id TEXT,
  description TEXT NOT NULL,
  deadline_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | fulfilled | overdue
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);
```
Registrar a criação no init do store (padrão dos outros `New*Store`).

## Passo 2 — Extração de promessas (pós-sessão)
- **Gatilho:** quando uma ligação/conversa encerra. Ponto real: em `broadcast.go` onde
  hoje se chama `recordLeadJourney` no `completed` (linhas ~1986 e ~2100) e no autoreply
  ao fechar thread. Ali já existe a transcrição (`reply`).
- **Ação:** chamar um LLM leve (usar o cliente de IA do dono, mesmo padrão de `agent_wargame.go`)
  com few-shot: "Extraia promessas que o atendente fez (ex.: 'te mando o orçamento amanhã').
  Retorne JSON `[{description, deadline_at}]` ou `[]`." Salvar cada uma em `agent_promises`.
- **Melhor**: enfileirar essa extração (não bloquear o fim da ligação) — no MVP, um
  `go func(){...}()` já resolve.

## Passo 3 — Cron de varredura
Novo `cmd/server/promises_cron.go` (espelhe `scheduled_calls_cron.go`):
- A cada 30 min: marca `status='overdue'` onde `deadline_at < now() AND status='pending'`.
- Para cada overdue novo: notifica o dono (usar `notifyOwner` do TelegramBot, já existe) e
  registra no painel do gestor.

## Passo 4 — Rotas de leitura (pro painel/CRM)
Registrar em `httpapi.go` (área CRM):
- `GET /api/crm/promises?status=` → lista promessas do tenant.
- `PUT /api/crm/promises/{id}` → `{status}` (marcar fulfilled manualmente).
Handler novo em `promises_api.go` (padrão de `crm_api.go`).

## Passo 5 — Frontend
- `CRMPage.tsx` aba `promises` já existe no front (ver mapa). Ligar ao `GET /api/crm/promises`.

## Verificação
- Rodar uma ligação de teste onde a IA promete algo → conferir linha em `agent_promises`.
- Forçar `deadline_at` no passado → o cron marca overdue e o dono recebe aviso no Telegram.
- Aba Promessas do CRM lista os registros reais.

## Trade-offs
- Extração custa tokens: usar LLM barato (Groq/Gemini) e só em conversas que fecharam.
- Não bloquear o fim da ligação com a extração (async).

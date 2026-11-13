# Treino de Agentes de Atendimento — Endpoints (para o frontend)

Backend novo que treina um **agente de atendimento** a partir das conversas reais do
**número de WhatsApp já conectado**. Lê as mensagens, classifica quais conversas são de
atendimento (vs pessoais, via LLM), e destila **um system prompt versionado**.

Todos os endpoints:
- Exigem autenticação (cookie/sessão de usuário, igual ao resto do `/api/*`).
- São escopados por dono — cada usuário só vê os próprios jobs/prompts.
- Usam JSON.

Sugestão de UI: **2 sub-abas em "Funcionários IA"**
1. **Treinar** — escolher agente + nº de conversas → botão *Estimar custo* → botão *Treinar* + barra de progresso (polling).
2. **Prompts gerados** — lista de versões → *Ver* / *Ativar*.

---

## 1. Estimar custo (antes de treinar)
`POST /api/training/estimate`

Conta as conversas candidatas do número conectado e estima tokens/custo **sem** rodar a
destilação. A 1ª rodada inclui o custo de classificar conversas ainda não vistas.

**Body:**
```json
{ "agent_id": "uuid-do-agente", "conv_limit": 20 }
```
`conv_limit` opcional (default 20, máx 200).

**Resposta 200:**
```json
{
  "conversations": 18,
  "to_classify": 18,
  "est_tokens_in": 42000,
  "est_tokens_out": 6000,
  "est_cost_usd": 0.216,
  "note": "estimativa aproximada; a 1ª rodada inclui o custo de classificar conversas novas"
}
```
**Erros:** 400 `{"error":"nenhum número de WhatsApp conectado"}`.

---

## 2. Iniciar treino
`POST /api/training/jobs`

Cria um job e dispara o treino em background. Retorna na hora — acompanhe por polling (nº 4).

**Body:**
```json
{ "agent_id": "uuid-do-agente", "conv_limit": 20, "max_cost_usd": 5.0 }
```
- `conv_limit` — quantas conversas ler (cap de volume). Default 20, máx 200.
- `max_cost_usd` — teto de gasto por execução; o treino **auto-pausa** se estourar. Default 5.0.

**Resposta 200:**
```json
{ "job_id": "uuid-do-job", "status": "running" }
```
**Erros:** 400 (agent_id faltando / sem número conectado), 404 (agente não encontrado).

---

## 3. Listar jobs
`GET /api/training/jobs?agent_id=uuid` (o `agent_id` é opcional; sem ele lista todos)

**Resposta 200:** array de jobs (mesmo shape do nº 4).

---

## 4. Status de um job (polling)
`GET /api/training/jobs/{id}`

**Resposta 200:**
```json
{
  "id": "uuid-do-job",
  "agent_id": "uuid-do-agente",
  "status": "running",
  "conv_limit": 20,
  "max_cost_usd": 5.0,
  "cost_usd": 0.42,
  "processed": 12,
  "total": 18,
  "error": "",
  "created_at": "2026-07-16T23:00:00Z",
  "finished_at": null
}
```
`status`: `running` | `paused` | `done` | `aborted` | `error`.
- `done` → prompt gerado (ver nº 6).
- `aborted` → cancelado pelo usuário **ou** auto-pausa por custo (veja `error`).
- `error` → falhou (veja `error`).

Sugestão: fazer polling a cada ~2s enquanto `status == "running"`; usar `processed`/`total`
pra barra de progresso e mostrar `cost_usd` correndo.

---

## 5. Cancelar treino
`POST /api/training/jobs/{id}/cancel`

**Resposta 200:** `{ "cancelled": true }` (`false` se o job já tinha terminado).

---

## 6. Listar prompts gerados
`GET /api/training/prompts?agent_id=uuid` (`agent_id` obrigatório)

**Resposta 200:**
```json
[
  { "id": "uuid", "agent_id": "uuid", "job_id": "uuid", "version": 2, "is_active": true,  "created_at": "..." },
  { "id": "uuid", "agent_id": "uuid", "job_id": "uuid", "version": 1, "is_active": false, "created_at": "..." }
]
```
(Não traz o corpo — use o nº 7 pra abrir uma versão.)

---

## 7. Ver o corpo de um prompt
`GET /api/training/prompts/{id}`

**Resposta 200:**
```json
{ "id": "uuid", "agent_id": "uuid", "version": 2, "body": "## Persona\n...", "is_active": true, "created_at": "..." }
```
O `body` é Markdown com as seções: **Persona / Tom de Voz / Regras de Conduta / Exemplos
Few-Shot / Anti-padrões**.

---

## 8. Ativar um prompt
`POST /api/training/prompts/{id}/activate`

Marca a versão como ativa **e grava no `system_prompt` do agente** (`agent_profiles`). A
partir daí o agente passa a usar o prompt treinado.

**Resposta 200:**
```json
{ "activated": true, "agent_id": "uuid", "version": 2 }
```

---

## Fluxo típico no painel
1. Usuário escolhe um agente e um `conv_limit` → **Estimar** (nº 1) mostra custo previsto.
2. Confirma → **Treinar** (nº 2) devolve `job_id`.
3. Barra de progresso via polling (nº 4) até `done`.
4. Aba "Prompts gerados" (nº 6) lista as versões; **Ver** (nº 7) abre o texto.
5. **Ativar** (nº 8) coloca o prompt no agente.

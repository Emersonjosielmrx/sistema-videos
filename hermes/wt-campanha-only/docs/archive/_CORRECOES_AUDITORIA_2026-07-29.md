# Correções da Auditoria — Hermes Call (2026-07-29)

> Sessão de auditoria estática + correção de bugs reais (não cosméticos). Todo o
> batch **compila limpo** (`go build ./...` EXIT 0). O único erro de `go vet` é
> pré-existente e num arquivo de teste que NÃO foi tocado
> (`cmd/server/sessionmanager_test.go:33` — assinatura desatualizada de `newSessionManager`).
>
> **DEPLOY + VALIDAÇÃO FEITOS (2026-07-29 17:xx):** commitado (4 commits), deploy no
> **beta** OK (`/api/version` = `v0.3.5`, container healthy). Validado ao vivo contra
> `hermescall.opus-sem-limites.com.br`:
> - **#R9** ✅ start_voz recebe **403** em `/api/easy-manager/wizard` e `PUT /api/settings/manager`;
>   `/api/settings` geral segue **200**; start_texto recebe **200** nas rotas do Gestor.
> - **#R6** ✅ id não-UUID → **404/400/200-vazio**, nunca 500. Caso feliz: id UUID real do
>   próprio tenant ainda dá **200** (o cast não quebrou match legítimo).
> - **Pattern 3** ✅ `score:-1`→400 (`"score não pode ser negativo"`), `payment_amount:-1`→400,
>   `price:-1`/`1e12`→400, `delay_minutes:-5`→400; bordas válidas (0) → 200.
> - `test_plans_e2e.sh`: 56 ok, 2 "falhas" que são **bugs do próprio script** (rotas-sonda
>   GET `/api/calls/recent` e `/api/meet/sessions` NÃO existem no backend → 404 pra
>   qualquer plano; corrigir o script). Todos os bloqueios 403 de plano corretos.
>
> **PENDENTE ainda:** Prioridade 1 do plano de testes (idempotência #J3 / recuperação #M2
> em modo corrida) precisa QA local com Postgres — não dá pra manipular ticker em produção.
> Rollback disponível: `node deploy/rollback.js`. Promover: `node deploy/promote-stable.js`.

---

## APLICADOS (DB-only / fronteira — seguros, espelham padrões já validados no repo)

### #R6 (lote) — UUID cast crash: `id=$N` → `id::text=$N`
- **Sintoma:** rota com `id` inválido na URL (não-UUID) retornava **500** (Postgres
  aborta o parse do UUID) em vez de 404/lista vazia.
- **Fix:** cast `id::text=$N` em todas as queries que comparam a PK `id` (UUID) com
  parâmetro vindo da URL. Aplicado via sed seguro (` id=$` com espaço antes só casa
  a coluna PK, não `product_id`/`agent_id`/etc). **12 tabelas confirmadas `id UUID`.**
- **Arquivos:** projects_store, crm_store, rag_store, training_store, agenda_store,
  catalog_store, followup_store, scheduled_calls_store. (mesma classe do #R6 já
  deployado em v0.3.4)

### Pattern 3 — validação de range em inputs de fronteira (API)
- **followup_api.go** (`CreateStep`): `delay_minutes`/`order` negativos rejeitados
  (400). Motivo: `delay_minutes` negativo empurra `next_execution` pro passado →
  step dispara fora de ordem na varredura.
- **agenda_api.go** (create appointment): `payment_amount` negativo rejeitado (400).
- **features_api.go** (`handleSetLead`): `score` negativo rejeitado (400). Motivo:
  filtro de busca usa `score >= ScoreMin` (default 0) → score negativo tornava o
  lead **invisível** em toda busca.
- **NÃO validado (inócuo):** `handlePutRateLimit` — `NewRateLimiter` já clampa
  `<= 0` pros defaults (10 msg / 60s), então valor ruim salvo é inofensivo.

### Bloco L (encoding) — truncamento em rune boundary
- **monitor.go** (`send` e o alerta de erro): `text[:N]`/`detail[:N]` por byte podia
  cortar UTF-8 no meio de um acento → Telegram rejeita UTF-8 inválido e o alerta de
  monitoramento sumia silenciosamente. Trocado por `[]rune(...)[:N]`.
- **Resto do Bloco L: limpo.** Todos os outros truncamentos são guardados por
  `if len(x) > N` (sem risco de panic) e são strings internas (contexto de LLM),
  não vão pra APIs que validam encoding. Lógica de telefone é ASCII+guardada.

### #R9 (NOVO) — bypass de plano: Funcionário Gestor acessível por start_voz
- **Sintoma:** o middleware (`authmw.go:159`) só bloqueia rota que `moduleForPath`
  mapeia. As rotas do Gestor (`/api/easy-manager/*`, `PUT /api/settings/manager`)
  **não estavam mapeadas** → um cliente **start_voz** (que não tem a aba
  `manager_chat`) acessava o Funcionário Gestor chamando a API direto. Mesma classe
  do P0-2 já corrigido.
- **Fix:** `plan_features.go` `moduleForPath` agora mapeia essas 3 rotas → `tabManager`.
  As 3 rotas de Gestor existentes ficam cobertas.
- **Verificado:** follow-up NÃO tem esse problema (vive sob a aba CRM, liberada a
  todos os planos).

### #J3 / #M — reenvio de follow-up por corrida (idempotência)
- **Sintoma:** `followup_cron.go` fazia read-then-write **sem claim atômico**: o
  goroutine de boot (20s) e o ticker (1min) podiam pegar o mesmo contato/etapa e
  **enviar a mesma mensagem 2×**. Além disso, crash entre `sendAndMark` e
  `AdvanceContact` deixava o contato `active` no mesmo step → **reenvio a cada tick**.
- **Fix:** novo `ClaimDue` (UPDATE ... WHERE status='active' AND current_step=$N AND
  next_execution<=now(), empurra +5min) — **espelha o `MarkDispatched` já validado**.
  `AdvanceContact` ganhou guard `AND current_step=$old` contra dupla-progressão.
  Crash mid-send agora só reexecuta em 5min (reenvio isolado, não loop por tick).

### #M2 — resume de campanha furando o anti-ban
- **Sintoma:** `resumeCampaigns` (boot) chamava `OpenCampaigns(kind)` que filtrava só
  por `kind`, **não por mode**. Campanhas `paced`/`multiline` eram retomadas com
  `go runCampaign` (dispara TODOS os pendentes de uma vez), **furando janela de
  horário / meta diária / teto anti-ban por linha** — e concorrendo com o scheduler
  (`DueCampaigns`), que já as cadencia. Risco: **burst de disparo → ban** + duplicação.
- **Fix:** `OpenCampaigns` agora exclui `mode IN ('paced','multiline')` (elas são
  retomadas exclusivamente pelo scheduler). Só `immediate` é retomada no boot.
  Serve aos dois callers (call e message).

---

## BILLING — FIX PREPARADO (commit a1c7397, NÃO DEPLOYADO — aguarda dona)

### #J1 [ALTA] — assinatura duplicada: CORRIGIDO no código
- `handleBillingSubscribe` agora consulta `SubscriptionStatus` antes de criar: se já há
  assinatura Asaas viva, **reusa** (retorna `reused:true`) em vez de criar outra. Se o
  Asaas está fora, NÃO cria às cegas (evita duplicar por indisponibilidade transitória).

### #J5 [MÉDIA] — webhook sem dedupe: CORRIGIDO no código (parcial)
- Nova tabela `billing_webhook_events` (PK `event_id`) + `MarkWebhookEvent` atômico
  (INSERT ON CONFLICT DO NOTHING). Reentrega/duplicata do webhook é ignorada.
- **LIMITAÇÃO:** não trata evento FORA DE ORDEM (REFUNDED antes de CONFIRMED). Precisaria
  comparar timestamp do evento. Fica pra decisão da dona.
- **AÇÃO DA DONA:** configurar o webhook no painel Asaas (URL + token). Ver seção no chat.

---

## ESCALADO — dispatch real (mensagem/ligação = dinheiro + risco de ban; tradeoff de negócio)

> NÃO auto-corrigidos: mexer no resume de dispatch tem tradeoff (excluir estado do
> resume = envio interrompido genuíno nunca reintenta). Precisa decisão + QA com Postgres.

### #B4 [MÉDIA] — mass-message pode reenviar 1 msg no resume pós-crash
- `massmsg.go`: contato fica `queued`, só vira `sent` DEPOIS do `SendMessage` (l.194→~216).
  Crash nessa janela deixa `queued`; `resumeMessageJobs`→`PendingNumbers` não exclui
  `queued` → **reenvia pra quem já recebeu**. Fix seria claim `sending` antes do envio
  (como o `ClaimDue` do follow-up). Janela pequena, mas real.

### #C1/Q4 [MÉDIA] — resume de campanha immediate re-disca número em 'ringing'
- `PendingNumbers` (store.go:298) não exclui `ringing`; `resumeCampaigns` (immediate)
  re-disca direto (não passa pelo `ClaimNumber` atômico). Número que caiu em 'ringing'
  no crash é **rediscado**. (paced/multiline já não são retomadas — mas aí o 'ringing'
  fica órfão, ver #C2.) Tradeoff: excluir 'ringing' do resume evita rediscar, mas perde
  o retry de uma ligação genuinamente interrompida. Decisão de negócio.

### #C2 [MÉDIA] — sem reaper de estados presos
- Não há job que devolva linhas presas em `ringing`/`dispatched` a um estado retryável
  após timeout. `call_watchdog.go` só aborta chamada in-memory (grava `call_stuck`), não
  reseta o DB. Número preso em 'ringing' fica órfão pra sempre. Sugestão: cron que, após
  N min, marca 'ringing' órfão como 'failed' (ou 'queued' pra retry controlado).

### #B6 [BAIXA] — double-submit cria linha duplicada (catalog/followup/agenda)
- Só `agent_profiles` tem `UNIQUE(user_id,name)` + upsert. Catalog product, followup
  campaign e agenda appointment **não têm** unique key → 2 POST idênticos = 2 linhas.
  Sugestão: unique constraint onde fizer sentido, ou idempotency key no create.

### #B5 / scheduled_calls — SAFE (confirmado)
- `MarkDispatched` segue atômico (`WHERE id::text=$1 AND status='pending'` + rows-affected);
  o cron respeita o `ok`. O #R6 (id::text) não quebrou o claim.

---

## ESCALAR PARA A DONA (billing legado — contexto do #J1/#J5 acima)

> Regra de isolamento: billing de produção é intocável sem autorização. Estes exigem
> teste contra o Asaas (impossível aqui) e decisão de negócio.

### #J1 [ALTA] — double-submit de assinatura cria assinatura duplicada no Asaas
- **billing_api.go:104** (`handleBillingSubscribe`): reusa o *customer* se já existe,
  mas `CreateSubscription` **não checa `AsaasSubID`**. Dois POST rápidos (duplo-clique
  / retry) criam **2 assinaturas MONTHLY vivas**. O `Upsert` guarda só o 2º subID; a
  1ª vira órfã mas **continua cobrando o cliente todo mês**, invisível ao app.
- **Impacto:** cliente cobrado 2× R$199/399/mês, uma cobrança não-rastreável.
- **Correção sugerida (a validar):** se `b.AsaasSubID != ""` e a assinatura existente
  ainda está viva (consultar `SubscriptionStatus`), reusar/retornar ela em vez de
  criar outra; ou guarda de idempotência por (user, plano) na janela de N segundos.
  Precisa decidir o comportamento de troca de plano (não há rota de change/cancel hoje).

### #J5 [MÉDIA] — webhook Asaas sem dedupe nem guarda de ordem
- **billing_api.go:220-235**: sem chave de evento processado → `PAYMENT_CONFIRMED` +
  `PAYMENT_RECEIVED` do mesmo pagamento notificam a dona 2×. Pior: entrega fora de
  ordem (ex.: `REFUNDED` antes de um `CONFIRMED` re-emitido) sobrescreve status sem
  checar timestamp do evento → pode reativar/cancelar conta errado. A escrita de
  status em si é idempotente (sem double-charge aqui).
- **Correção sugerida (a validar):** tabela de eventos processados (dedupe por
  event id) + comparar timestamp do evento antes de sobrescrever status.

---

## PENDÊNCIAS
- **Deploy beta + smoke test** do batch acumulado (precisa VPS + commit + aprovação).
- **#R8** (limites de quantidade por plano não são enforced) — aguarda decisão da dona.
- **go vet**: corrigir `sessionmanager_test.go:33` (assinatura de `newSessionManager`
  desatualizada) — pré-existente, fora do escopo desta auditoria.

# PLANO DE TESTE MASTER — Hermes Call v0.3.5

> Plano mais completo possível. Objetivo: cobrir **TUDO**, com destaque para **o que
> nunca foi testado ao vivo**. Cada seção marca `[JÁ COBERTO]` (por script existente)
> ou `[LACUNA]` (nunca rodou). As LACUNAS são a prioridade.
>
> **Base beta:** `https://hermescall.opus-sem-limites.com.br` (channel=beta, v0.3.5).
> **QA local:** `:8095` quando houver docker+Postgres (necessário pras seções de corrida).
>
> **Cobertura atual (o que já existe):**
> - `test_plans_e2e.sh` — gating de plano (5 planos, abas + 1 rota 200/403 cada).
> - `tests/e2e/02-security.spec.ts` — IDOR cross-tenant, auth bypass, cupom, webhook
>   Asaas sem token, SQLi não derruba, path traversal, rate-limit login.
> - `tests/e2e/01-smoke`, `03-campaign-flow`, `04-button-walker`, `05-settings-walker`.
> - `tests/stress/01-volume.spec.ts`.
>
> **ZONA PROIBIDA (imutável):** não disparar ligação/campanha/mensagem real; não tocar
> `internal/voip/*`; dados de teste com prefixo `qa035-`, limpar depois; produção intocável.
>
> **Legenda severidade:** 🔴 crítico (perda de dado / segurança / 500) · 🟠 médio ·
> 🟡 baixo. **Legenda status esperado:** cada caso diz o HTTP/efeito esperado.

---

# BLOCO A — Regressão dos fixes v0.3.5  [PARCIAL: validado por HTTP no beta hoje]

## A0 — resumo do que JÁ foi validado ao vivo (2026-07-29)
- ✅ #R9 gestor 403 (start_voz) / 200 (start_texto); settings geral 200.
- ✅ #R6 id não-UUID → 404/400, nunca 500; UUID legítimo → 200.
- ✅ Pattern 3: score/payment/price/delay negativos → 400; bordas (0) → 200.

## A1 — #R6 UUID cast, cobertura EXAUSTIVA  [LACUNA: só testei ~5 rotas]
Para **CADA** rota abaixo, com token válido, id **não-UUID** (`lixo`, `123-abc`, `' OR 1=1`):
esperado 400/404/2xx-vazio, **NUNCA 500**. E id UUID **legítimo do próprio tenant** → 2xx.

| Store | Rotas a cobrir |
|---|---|
| catalog | GET/PUT/DELETE `/api/catalog/products/{id}`, `/api/catalog/images/{id}`, reorder |
| followup | PUT/DELETE `/api/followup/campaigns/{id}`, `/steps/{id}`, `/rules/{id}`, `/sequences/{id}` |
| agenda | GET/PUT/DELETE `/api/agenda/appointments/{id}`, `/professionals/{id}`, `/blocks/{id}`, `/waitlist/{id}` |
| crm | leads by id, `/api/crm/*/{id}` |
| training | `/api/training/{id}` (todas as 8) |
| rag | `/api/rag/{id}` |
| projects | `/api/projects/{id}` |
| scheduled | `/api/scheduled/{id}` |
| keys/credentials | DELETE `/api/keys/{id}`, `/api/credentials/{id}` ✅ (já testado) |
| contact-lists | `/api/contact-lists/{id}` |

**Método:** loop de curl (adaptar `test_plans_e2e.sh`). 🔴 se algum 500.

## A2 — #R9 bypass de plano, cobertura de TODOS os módulos restritos  [LACUNA parcial]
`moduleForPath` mapeia: calls, meeting-ai, catalog, agenda, chat, agents, campaigns, manager.
Para cada plano, cruzar aba-permitida × rota-do-módulo:

| Plano | Deve **200** | Deve **403** (plan_forbidden) |
|---|---|---|
| start_voz | `/api/calls/*`, `/api/crm/*` | `/api/easy-manager/wizard` ✅, `/api/chat/*`, `/api/agent-profiles`, `/api/catalog/*`, `/api/agenda/*`, `/api/meet/*` |
| start_texto | chat, agents, manager ✅ | `/api/calls/*`, `/api/catalog/*`, `/api/agenda/*`, `/api/meet/*` |
| pro | tudo menos meet | `/api/meet/*` |
| scale/trial | tudo | — |

**Atenção à borda:** `/api/catalog/public*` deve ser **200 SEM token** (vitrine) mesmo
pra quem não tem a aba. `/api/agenda/asaas-webhook` idem (público). Confirmar que o gate
NÃO bloqueia esses.

## A3 — Pattern 3, todas as bordas  [LACUNA parcial]
- followup step: `delay_minutes` = -1→400, 0→200, MAX_INT→? (checar overflow no `time.Duration`).
- catalog: `price`/`cost` = -0.01→400, 0→200, 1e9→200(borda), 1e9+1→400.
- lead score: -1→400, 0→200, valor gigante (2^31)→? (checar int overflow).
- agenda payment_amount: -1→400, 0→200.
- **NÃO validado (documentar):** rate-limit `WindowSeconds<=0` é clampado no runtime (inócuo).

## A4 — agentprofiles.List NULL-safe  [LACUNA: não testei ao vivo]
- Criar agent SEM áudio (não setar audio_id/trigger/offer).
- `GET /api/agent-profiles` → lista **contém** o agente. Criar 2º agente COM áudio →
  ambos aparecem. 🔴 se a lista voltar vazia/500.

## A5 — encoding monitor rune-boundary  [LACUNA: só leitura de código]
- Não há gatilho HTTP direto. Validação: inspeção + build. (Opcional QA: forçar alerta
  com string > 4000 chars terminando em acento e ver se o Telegram recebe.)

---

# BLOCO B — Idempotência (o mais valioso; NUNCA testado ao vivo)  [LACUNA TOTAL]

> **Requer QA local com Postgres** (manipular ticker/estado). Em produção só leitura.

## B1 — 🔴 #J3 follow-up NÃO reenvia a mesma etapa
- **Corrida:** enrolar 1 contato de teste, delay 0. Disparar `runFollowupTick` 2× em
  paralelo. Esperado: exatamente **1** linha 'sent' em `fu_message_log` pra (contato,step).
  A 2ª chamada perde `ClaimDue` → pula.
- **Pós-claim:** após `ClaimDue`, `SELECT next_execution` do contato deve estar **+5min**.
  Confirmar que o próximo tick de 1min NÃO o repega.
- **Guard current_step:** chamar `AdvanceContact(d)` 2× com o mesmo `d` → só a 1ª avança
  (2ª é no-op por `WHERE current_step=$old`).
- **Boot × ticker:** simular o goroutine de boot (20s) e o ticker juntos → sem envio duplo.

## B2 — 🔴 #J1 billing double-subscribe  [FIX PREPARADO — testar após deploy do billing]
- Fix (commit a1c7397): reusa assinatura viva em vez de criar outra.
- **Teste em SANDBOX Asaas (NUNCA produção):** 2 POST `/api/billing/subscribe` rápidos →
  contar assinaturas criadas. Esperado pós-fix: **1** (2ª retorna `reused:true`).
- **Borda:** Asaas fora do ar → NÃO cria às cegas (não duplica por indisponibilidade).

## B3 — 🟠 #J5 webhook Asaas dedupe  [FIX PREPARADO — testar após deploy do billing]
- Fix (commit a1c7397): tabela `billing_webhook_events` + dedupe por `event_id`.
- **Teste:** enviar 2× o mesmo evento (mesmo `id`) → 2ª é ignorada (dona notificada 1×).
  Verificar linha única em `billing_webhook_events`.
- **LIMITAÇÃO conhecida (não corrigida):** evento FORA DE ORDEM (REFUNDED antes de
  CONFIRMED) ainda sobrescreve status sem checar timestamp. Testar e documentar o
  comportamento; decisão da dona se vale o guard de ordem.
- **Pré-requisito:** webhook configurado no painel Asaas (URL `/api/billing/webhook` +
  header `asaas-access-token` = `HERMES_ASAAS_WEBHOOK_TOKEN`).

## B4 — 🟠 mass-message reenvia no resume  [CONFIRMADO POR LEITURA — bug aberto]
- `massmsg.go`: contato fica `queued` e só vira `sent` DEPOIS do `SendMessage` (l.194).
  `PendingNumbers` (store.go:298) não exclui `queued` → resume reenvia pra quem já recebeu.
- **Teste (QA, número próprio ou stub):** enrolar 2 contatos, matar o processo logo após
  o 1º `SendMessage` retornar (antes do UpsertResult). No boot, confirmar se reenvia.
  Esperado hoje: reenvia (bug). Pós-fix (claim 'sending'): não reenvia.
- **NÃO disparar real** pra número de terceiro.

## B5 — scheduled_calls (referência limpa)  [CONFIRMADO SAFE]
- `MarkDispatched` (scheduled_calls_store.go:254) segue atômico `WHERE id::text=$1 AND
  status='pending'` + rows-affected; cron respeita o `ok` (l.124). #R6 não quebrou.
- **Teste:** chamar MarkDispatched 2× no mesmo id → 2ª retorna false. (unit test ideal.)

## B6 — 🟠 double-submit cria duplicata  [CONFIRMADO POR LEITURA]
- Sem unique key: catalog product, followup campaign, agenda appointment → 2 POST = 2 linhas.
- COM guard: agent-profile (`UNIQUE(user_id,name)` + upsert) → idempotente.
- **Teste:** 2 POST idênticos rápidos em cada create; contar linhas. Documentar quais
  precisam de unique/idempotency key (decisão da dona).

---

# BLOCO C — Recuperação / crash-consistency  [LACUNA TOTAL]

## C1 — 🔴 #M2 resume de campanha NÃO fura anti-ban  [validar]
- QA: inserir campanha `paced` e `multiline` abertas (finished_at NULL), sem disparar.
- Chamar `OpenCampaigns(ctx,"call")` → **não** retorna paced/multiline (só immediate).
- Regressão: campanha `immediate` aberta AINDA é retomada.
- Chamar `OpenCampaigns(ctx,"message")` → mesma exclusão.

## C2 — 🟠 reaper de estados presos  [CONFIRMADO AUSENTE POR LEITURA]
- Não existe job que resete `ringing`/`dispatched` pra retryável após timeout.
  `call_watchdog.go` só aborta chamada in-memory (grava `call_stuck`), não toca o DB.
- **Consequência:** número preso em 'ringing' (paced/multiline, que não são retomados)
  fica órfão pra sempre. Immediate re-disca (ver C4).
- **Teste (QA):** marcar um campaign_result em 'ringing' e deixar; confirmar que nada
  o move. Sugestão de fix: cron que após N min marca 'ringing' órfão como 'failed'.

## C4 — 🟠 resume immediate re-disca 'ringing'  [CONFIRMADO POR LEITURA — bug aberto]
- `PendingNumbers` não exclui `ringing`; `resumeCampaigns` immediate re-disca sem passar
  pelo `ClaimNumber` atômico → número mid-'ringing' no crash é rediscado (duplicado).
- **Tradeoff de negócio:** excluir 'ringing' do resume evita rediscar mas perde retry de
  ligação genuinamente interrompida. Decisão da dona antes de corrigir.
- **Teste (QA):** campanha immediate, matar processo com 1 número em 'ringing', bootar →
  confirmar se re-disca. NÃO com número real de terceiro.

## C3 — 🟠 sessões WhatsApp restauradas no boot  [LACUNA]
- Log do deploy mostrou "sessions restored count=6". Validar: após restart, sessão
  pareada volta a operar (status via `/api/sessions/{id}`), sem duplicar conexão.

---

# BLOCO D — Cross-tenant / segurança  [PARCIAL: SEC-1 cobre IDOR básico]

## D1 — IDOR exaustivo em TODOS os stores tocados pelo #R6  [LACUNA: SEC-1 testa só 1-2]
- Conta A cria: produto, lead, campanha followup, step, agendamento, profissional,
  bloco, apikey, credential, projeto, sequência, item de treino, rag doc, contact-list.
- Conta B tenta GET/PUT/DELETE por **id de A** → 404/403, nunca 200 nem 500.
- **Ponto crítico do #R6:** confirmar que toda query com `id::text=$N` **manteve** o
  `AND user_id=$M`. Grep de sanidade: nenhuma query id::text perdeu o filtro de dono.

## D2 — auth  [JÁ COBERTO: SEC-2/3/8]
- Revalidar: sem token→401, token forjado→401, brute-force login→bloqueio.

## D3 — rotas públicas não vazam dado autenticado  [LACUNA]
- `/api/catalog/public?owner=<id-de-A>` → só leitura da vitrine, sem campos internos
  (custo, stock interno, telefone do dono). Confirmar payload público mínimo.
- `/api/demo/voice`, `/api/demo/clip` → rate-limit por IP funciona (não é DoS grátis).

## D4 — injeção  [JÁ COBERTO: SEC-6/7]
- Revalidar SQLi/path-traversal nos novos handlers (catalog price, human-assist).

---

# BLOCO E — Feature nova HumanAssist (Ponto Eletrônico SOS)  [LACUNA TOTAL]

## E1 — round-trip persistência
- `PUT /api/settings/human-assist` {enabled,channel,admin_number,stall_message,auto_learn}.
- `GET /api/settings` → bloco `human_assist` com os MESMOS valores.
- `channel` inválido → normaliza "whatsapp"; `channel:"call"` preserva.

## E2 — cross-tenant
- Conta B não lê config de A. (Invalidação de cache: `invalidateUserSettings` após PUT.)

## E3 — comportamento (leitura + QA)
- Quando a IA "não sabe", dispara o canal escolhido? `auto_learn` injeta no RAG?
  (Requer fluxo de chat com LLM — bloqueado por quota Gemini; documentar.)

---

# BLOCO F — Cobertura por módulo (varredura de rota × handler)  [PARCIAL]

> Para cada módulo: (a) toda rota da UI existe no backend (não é fantasma → 404);
> (b) toda rota do backend é usada pela UI (não é órfã); (c) chave JSON front↔struct
> Go bate (bug clássico `system_msg` vs `system_message`).

| Módulo | Rotas | Status cobertura |
|---|---|---|
| /api/sessions (102) | conectar, qr, webhook, proxy, chatwoot | [LACUNA] a maior superfície; button-walker toca UI mas não valida payloads |
| /api/settings (26) | 05-settings-walker carrega abas | [PARCIAL] falta round-trip de cada save |
| /api/followup (26) | campaigns/steps/rules/sequences/contacts | [LACUNA] só #R6/#J3 tocados |
| /api/catalog (24) | products/images/public/reorder/stock | [PARCIAL] price validado; falta stock/reorder/public |
| /api/contacts (21) | leads/extras/tags/import | [LACUNA] |
| /api/agenda (17) | appointments/professionals/blocks/waitlist/webhook | [LACUNA] só #R6 |
| /api/analytics (13) | dashboards | [LACUNA] validar não-500 com conta vazia |
| /api/agents+agent-profiles (13) | CRUD + NULL-safe | [PARCIAL] A4 |
| /api/training (8), /api/rag (5) | base de conhecimento | [LACUNA] |
| /api/billing (5) | subscribe/check/coupon/webhook | [PARCIAL] cupom ok; #J1/#J5 lacuna |
| /api/2fa (4), /api/security (5), /api/access-list (5) | segurança conta | [LACUNA] |
| /api/tts (4), /api/audios (4), /api/recordings (4) | mídia | [LACUNA] não-500 |
| /api/n8n (2), /api/orchestration (2), /api/projects (4) | integrações | [LACUNA] |

**Método sugerido:** gerar do `httpapi.go` a lista das 386 rotas, cruzar com
`tests/api_calls.txt` (rotas que a UI chama) e `tests/orphans.json` — marcar
fantasmas (UI→backend inexistente) e órfãs (backend sem UI).

---

# BLOCO G — Robustez de entrada (fuzz leve por handler)  [LACUNA]

Para cada POST/PUT com body JSON:
- body vazio `{}` → não 500 (400 ou default).
- body malformado (não-JSON) → 400, não 500.
- campo string gigante (1MB) → rejeitado ou truncado, não estoura.
- tipos trocados (string onde espera int) → 400, não 500.
- UTF-8 / emoji / RTL em nomes → persiste e volta íntegro (relaciona com fix encoding).
- números: negativo, zero, MAX_INT, NaN/Infinity no JSON → 400.

---

# BLOCO H — Não-funcional  [PARCIAL: stress/01-volume existe]

- **H1 latência:** cada GET de lista responde < 2s com conta vazia e < 5s com 1k registros.
- **H2 volume:** [JÁ COBERTO parcial] importar 1k contatos, listar paginado.
- **H3 concorrência:** 20 requests paralelos no mesmo endpoint de leitura → sem erro/deadlock.
- **H4 memória:** monitorar container beta sob button-walker (sem leak óbvio).

---

# ORDEM DE EXECUÇÃO
1. **Smoke** (version, landing, login, `test_plans_e2e.sh`) — confirma beta de pé.
2. **Bloco A** (regressão dos fixes) — rápido, HTTP, alta prioridade.
3. **Bloco D** (cross-tenant) — segurança.
4. **Bloco B + C** (idempotência/recuperação) — **o mais valioso e não-testado**; precisa QA+Postgres.
5. **Bloco E** (HumanAssist), **F** (varredura módulos), **G** (fuzz), **H** (não-funcional).

# BLOQUEIOS CONHECIDOS
- **Postgres/docker ausente nesta máquina** → Blocos B1/B5/C1 (modo corrida) precisam QA local.
- **Quota Gemini (429 nas ~90 chaves)** → simulação RAG/LLM e E3 bloqueados.
- **Asaas produção** → B2/B3 só em sandbox ou leitura de código.

# PENDÊNCIAS DE LIMPEZA
- Contas `qa035.*` criadas no banco do beta (inócuas, trial). Limpeza real:
  `DELETE FROM users WHERE email LIKE 'qa035.%'` no Postgres da VPS — requer confirmação.
- Corrigir `test_plans_e2e.sh`: rotas-sonda `/api/calls/recent` e `/api/meet/sessions`
  (GET) não existem → trocar por rotas reais (`POST /api/calls/{id}/bridge`, `/api/meet/turn`).

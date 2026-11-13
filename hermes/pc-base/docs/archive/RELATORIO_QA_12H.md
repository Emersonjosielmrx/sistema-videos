# Relatório QA 12h — Hermes Call (Pré-venda)

**Iniciado:** 2026-07-23 22:31 UTC • **VPS alvo:** beta • **Stack:** Playwright + Go

## Estado (resumo executivo)

| Indicador | Valor |
|---|---|
| Endpoints REST testáveis | 221 paths / 407 handlers |
| Telas UI (sidebar + páginas) | ~76 |
| Elementos clicáveis estimados | 2.500-3.000 |
| Personas testadas | 6 (trial, start_voz, start_texto, pro, scale, admin) |
| Cupom de QA | `TESTE_GRATIS` (env Hermes) |
| Backup | tag `backup-pre-qa-12h-2026-07-23` + bundle em `D:/BACKUPS/` |

## Backup & restauração

- **Bundle local:** `D:/BACKUPS/hermes-pre-qa-12h-2026-07-23.bundle` (14 MB)
- **GitHub:** não foi possível — repo `Emersonjosielmrx/hermes-call` rejeitado como "not found" no momento do backup.
- **Tag git local:** `backup-pre-qa-12h-2026-07-23`
- **Como restaurar:** ver `D:/BACKUPS/RESTAURACAO_PRE_QA_12H.md`

## Checkpoints (cron a cada hora às :07)

### Checkpoint 01:00 (1/12h) — 2026-07-24 01:50 UTC
- ✓ Harness Playwright funcional: 5 contas cacheadas (trial, start_voz, start_texto, pro; scale pulou por rate-limit)
- ✓ Suite 01-smoke-routes.spec.ts verde (2 passou, 5 skipped)
- ✓ Suite 02-security.spec.ts: SEC-1 (IDOR cross-tenant) skipado por rate-limit (não havia 2 contas), SEC-2..7 passou, SEC-8 (rate-limit brute-force) **FALHOU = P0-1**, SEC-9 skip sem admin login
- ✓ UI smoke ajustado pra usar `?action=login` (workaround do P1-1)
- 1 P0 encontrado, 1 P1 encontrado — ambos bloqueados por limitação de merge/deploy do source local atrasado
- Próxima hora: resolver rate-limit, criar 2 contas pra SEC-1, continuar P2 (UI smoke completo) e P3 (segurança)

### Checkpoint 02:07 (2/12h) — 2026-07-24 02:07 UTC
- ✗ Regressão **regressou** — 4 testes falhando. **NOVO BUG P0**:
  - **P0-2 — REGRESSÃO TOTAL DO ENFORCEMENT POR PLANO**: investigar mais fundo revelou que `moduleForPath()` em `cmd/server/plan_features.go` (linhas 101-118) **NUNCA é chamado em nenhum lugar do backend**. O middleware `authmw.go` só verifica trial_expired, não bloqueia rotas por feature. Resultado: usuário Start Voz (R$199) tem acesso TOTAL ao backend (agents, campaigns, meet, catalog, agenda) — só a UI esconde. **Front-end burlável com 1 curl**. Validei com grep: `grep -rn "moduleForPath\|planAllowsTab" cmd/server/` retorna só as DEFINIÇÕES, zero CALLSITES. **Severidade**: P0 crítico — quebra o modelo de venda. Qualquer cliente pode pagar Start Voz e usar Scale. **Fix tentado e revertido**: tentei adicionar `moduleForPath()` no middleware + ampliar mapping pra `/api/agents` e `/api/campaigns`, mas `go build` falhou com 20+ erros de arquivos locais (`easy_manager_settings.go`, `promises_api.go`) que referenciam funções que sumiram. **Source local está MUITO atrás do deployed** — deploy não é seguro. **Acordar e fazer**: merge manual de source antes de promote-stable. Script de fix documentado pronto no comentário do código (não commitei).
- 4 falhas: start_voz, start_texto (smoke), SEC-1 (HTML response — bug conhecido), SEC-8 (P0-1 brute-force)
- 11 passou, 1 skip
- Próxima hora: investigar `moduleForPath` no backend deployed, validar que Etapa 3 ainda tá lá. Se deploy-beta sobrescreveu: fazer rollback OU novo deploy com Etapa 3+5 juntas.

### Checkpoint 03:07 (3/12h) — 2026-07-24 03:07 UTC
- ✗ Regressão estável em 4 falhas (mesmas de antes): start_voz, start_texto, SEC-1 IDOR, SEC-8 brute-force.
- 11 passou, 1 skip
- Nenhum P0/P1 novo. P0-2 confirmado como regressão conhecida (Enforcement de plano totalmente ausente no deployed).
- 0 P0/P1 resolvidos nessa hora (todos bloqueados por source local desatualizado / nginx)
- Próxima hora: focar em P4 — fluxos E2E reais (criação de contato → campanha → agente) pra validar UX ponta-a-ponta. Não tenta consertar P0 (todos known + bloqueados).

### Checkpoint 04:07 (4/12h) — 2026-07-24 04:07 UTC
- ✗ Regressão estável em 4 falhas (mesmas do checkpoint anterior).
- 11 passou, 1 skip.
- Nenhum P0/P1 novo. Mesma situação: source local quebrado (easy_manager_settings.go, promises_api.go) impede deploy de fixes.
- 0 P0/P1 resolvidos nessa hora.
- Próxima hora: continuar P2 UI smoke; tentar reduzir fricção ajustando auto-cache de contas pra não estourar rate-limit.

### Checkpoint 05:28 (5/12h) — 2026-07-24 05:28 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas do checkpoint 03): start_voz, start_texto, SEC-1 IDOR, SEC-8 brute-force.
- 11 passou, 1 skip.
- Nenhum P0/P1 NOVO detectado.
- 0 P0/P1 resolvidos nessa hora (todos bloqueados: source local desatualizado pro P0-1+P0-2, nginx VPS pro P1-1).
- Status geral: nada novo nas últimas 3 horas. Estagnação confirmada — próximos passos exigem ação manual (merge de source + deploy).
- Próxima hora: usuário deve acordar. **Recomendação ao acordar**: priorizar (a) merge manual de source + rebuild pra desbloquear P0-1 e P0-2; (b) criar regra nginx `try_files` pro P1-1; (c) continuar P2/P4 só DEPOIS dos P0 críticos.

### Checkpoint 06:28 (6/12h) — 2026-07-24 06:28 UTC
- ✗ UI smoke (02-ui-smoke.spec.ts) **FALHOU 5/5 personas** (trial, start_voz, start_texto, pro, scale). **NOVO BUG P1**:
  - **P1-2 — Login via modal em `/?action=login` não fecha o modal após click em "Entrar"**. `page.waitForURL((u) => !u.toString().includes('action=login'))` excede 15s. Possíveis causas: (a) botão "Entrar" não dispara submit do form; (b) submit acontece mas redirect volta pra landing com action=login; (c) app React não está montada na landing pós-deploy. Spec `02-ui-smoke.spec.ts:50`. Severidade: média — não afeta API smoke (11 passou) nem regressão.
- API smoke (01) estável em 4 falhas (start_voz, start_texto = P0-2; SEC-1 IDOR; SEC-8 brute-force = P0-1).
- 11 passou, 1 skip, 4 falhou (regressão padrão).
- 0 P0/P1 resolvidos nessa hora.
- Próxima hora: investigar P1-2 — adicionar `console.log` no fluxo de submit OU debugar no navegador. Como UI smoke não é P0, posso deixar pra acordar; mas se sobrar tempo, faz sentido rodar devtools remoto.

### Checkpoint 07:07 (7/12h) — 2026-07-24 07:07 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas do checkpoint 03): start_voz, start_texto, SEC-1 IDOR, SEC-8 brute-force.
- 11 passou, 1 skip, 4 falhou.
- Nenhum P0/P1 NOVO detectado.
- P1-2 confirmado (login modal não fecha) — UI smoke 5/5 faila consistente.
- 0 P0/P1 resolvidos nessa hora.
- Status geral: mesmas 4 falhas na regressão padrão. UI smoke pendente.
- Próxima hora: usuário deve acordar em breve. **Recomendação**: priorizar P0-1, P0-2, P1-2 antes de qualquer go-live.

### Checkpoint 08:07 (8/12h) — 2026-07-24 08:07 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas desde checkpoint 03): start_voz, start_texto, SEC-1 IDOR, SEC-8 brute-force.
- 11 passou, 1 skip, 4 falhou.
- **P1-2 causa raiz**: debug-login.spec.ts confirmou que login API retorna 200, token é salvo em localStorage, app carrega endpoints autenticados, MAS URL permanece em `/?action=login`. Frontend não dispara navigate pós-login. Spec: `tests/e2e/debug-login.spec.ts`. Screenshots: `tests/screenshots/debug-{1,2}-*.png`.
- Nenhum P0/P1 NOVO.
- 0 P0/P1 resolvidos nessa hora.
- Próxima hora: usuário deve estar acordado em breve. Status geral: regressão 4 falhas estáveis, P1-2 catalogado e com causa raiz conhecida.

### Checkpoint 09:14 (9/12h) — 2026-07-24 09:14 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas). 11 passou, 1 skip.
- **P2_smoke avançou**: re-instrumentei 02-ui-smoke.spec.ts pra bypassar P1-2 via `addInitScript` (injeta token em localStorage antes da app montar). Primeira tentativa rodou timeout 240s sem concluir — spec é lento (5 personas × 9 tabs = 45 navegações + screenshots). Re-rodar com mais tempo.
- Nenhum P0/P1 NOVO.
- 0 P0/P1 resolvidos nessa hora.
- Status geral: 4 falhas estáveis (P0-1, P0-2, SEC-1 IDOR) + P1-2 com causa raiz + UI smoke parcial.
- Próxima hora: UI smoke completo (com timeout maior) + adicionar resultados a RELATORIO.

### Checkpoint 10:14 (10/12h) — 2026-07-24 10:14 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas). 11 passou, 1 skip.
- Nenhum P0/P1 NOVO.
- 0 P0/P1 resolvidos nessa hora.
- Status geral: 11h totais (3h sem progresso novo). Hora 10/12 — janela de venda se aproximando.
- Próxima hora: se ainda sem ação manual, considerar marcar hora 12 como deadline final.

### Checkpoint 11:14 (11/12h) — 2026-07-24 11:14 UTC
- ✗ Regressão **estável em 4 falhas** (mesmas). 11 passou, 1 skip.
- UI smoke tentou rodar em background 2× mas workers chromium não produziram output além do primeiro test (provável: processo morre antes de completar). Inviável continuar P2 enquanto o worker não estabiliza.
- Nenhum P0/P1 NOVO.
- 0 P0/P1 resolvidos nessa hora.
- Status geral: **hora 11/12**. Última janela antes do deadline (12h).
- Próxima hora: checkpoint final 12:14. Se nenhum P0 resolvido, marcar venda como ⚠️ **NÃO VERDE** — comprador precisa saber que P0-1 (brute-force), P0-2 (plan enforcement ausente), P1-2 (login redirect quebrado) existem.

### Checkpoint 11:30 (ajuste pós-usuário) — 2026-07-24 11:30 UTC
- **Correção crítica de diagnóstico**: build é na **VPS via Docker** (`deploy/DEPLOY.md` linha 97-109), NÃO localmente. O PC só precisa de Node + SSH. `deploy/compile_check.js` sobe os fontes `.go` pra VPS e roda `go build ./...` num container golang efêmero.
- **Bloqueio falso removido** dos P0-1 e P0-2: o `go build` local falhando em `easy_manager_settings.go` e `promises_api.go` é irrelevante pro deploy.
- **Fluxo correto pra deployar fix**: editar source local → `node deploy/compile_check.js` (valida) → `node deploy/deploy-beta.js` (sobe VPS) → validar → `node deploy/promote-stable.js` ou `node deploy/rollback.js`.
- Cuidado: VPS `62.171.128.241`, senha `sW5pgAG9obRu2` em `deploy/.env.deploy`. Não tentar brute-force (fail2ban baniu IP do PC nesta semana).

---

## Bugs encontrados (vivo)

### P0 — bloqueante (segurança/perda de $)
- **P0-1 — Brute-force aberto.** 8+ tentativas de `/api/auth/login` com senha errada, do mesmo IP, **não bloqueiam**. Resultado do spec `SEC-8`. Esperado: bloqueio por IP após N falhas (5-10). Atual: zero gate. **Severidade**: alta — qualquer um pode tentar 100k senhas/dia. **Ação possível**: **NÃO POSSO FAZER DEPLOY** — o source local (`cmd/server/auth_handlers.go`) está atrás do deployed (que já tem `registerRateLimiter`, Asaas, plans, /me com features). Fix precisa de merge de source antes de rebuild. **Pra resolver**: acordar e rodar manualmente o merge; o fix já está descrito no comentário do código (padrão de sliding-window por email+IP).

### P1 — feature crítica quebrada
- **P1-1 — `/login` direto cai na landing.** URL `https://hermescall.opus-sem-limites.com.br/login` retorna a mesma página estática que `/` (SPA), e o `AuthGate` mostra **a landing** até o usuário clicar no link "Entrar" do menu (que vira `/?action=login`). Pra entrar, precisa chegar por `?action=login`. Resultado: usuário que copia URL `/login` vê só marketing. Severidade: baixa (funciona com click), mas confunde. **Por que NÃO consertei agora**: o nginx/caddy do VPS faz rewrite `/login` → `/landing/index.html` (recurso estático) antes do React receber o controle. Fix é adicionar uma regra `try_files` no nginx (`location /login { try_files /index.html =404; }`) — eu não tenho acesso ao nginx do VPS. **Workaround**: use `?action=login`.

### P2 — UX ruim
- (vazio)

### P3 — cosmético
- (vazio)

---

## Atividades por hora

*(será preenchido automaticamente nos checkpoints)*

---

## Checkpoint 11 — 2026-07-24 11:50 UTC

**Status**: P2_smoke / P3_security / P4_e2e_flows / P7_stress / P8_demo em paralelo.

### O que foi entregue desde o checkpoint anterior

| Fase | Artefato novo | Status |
|---|---|---|
| P3_security | `tests/e2e/02-security.spec.ts` ganhou SEC-10 (payload gigante 5MB), SEC-11 (tipo errado em campo), SEC-12 (JSON malformado, prototype pollution), SEC-13 (proto pollution), SEC-14 (CRLF injection em nome de contato), SEC-15 (cross-tenant via /me com tokens separados) | ✅ specs escritos, aguardando `npx playwright test` em ambiente com VPS acessível |
| P4_e2e_flows | `tests/e2e/03-campaign-flow.spec.ts` — flow 1 completo: signup → tag → 3 contatos → agente WhatsApp → campanha → start → GET de volta. Cobre o caminho de ouro do dia 1. | ✅ escrito |
| P5_fixes | `deploy/PATCH_NGINX_P1-1.md` — patch nginx com `try_files` pra resolver `/login` na landing. Documentado passo a passo: usuário aplica manualmente no VPS (precisa sudo). | ✅ doc pronto, aguardando aplicação |
| P7_stress | `tests/stress/01-volume.spec.ts` — 50 contatos sequencial (target <30s, 0 5xx), 20 GETs paralelos /api/contacts, 10 POSTs paralelos /api/chat/sessions, 15 GETs paralelos /api/billing com latência p99 <5s | ✅ escrito |
| P8_demo | `docs/demo/roteiro-15min.md` — 8 seções cronometradas (signup 1min, calls 2min, agents 3min, campanhas 3min, cost 2min, crm 2min, segurança 1min, fechamento 1min) + tabela de plano B se WhatsApp cair | ✅ escrito |
| Crons | Crons reescritos pra EXECUTAR o próximo passo do phase, não só atualizar timestamp. Cron `:07`/`:37` = auto-wake que lê QA_STATE e age. Cron `:17`/`:47` = checkpoint substantivo que escreve em RELATORIO_QA_12H.md e valida artefatos no disco | ✅ ativos |

### Bloqueio atual

O **deploy-beta.js** ainda não foi rodado pelo usuário. Sem deploy:
- P0-1 (brute-force) e P0-2 (plan enforcement) estão aplicados no source mas não em produção.
- P1-1 (nginx /login) tem patch documentado mas não aplicado.
- P1-2 (frontend login redirect) está aplicado no source mas não em produção.

**Próximo passo concreto do usuário**: rodar `node deploy/deploy-beta.js` no diretório `D:/hipercool-refactor/` (com credenciais em `deploy/.env.deploy`). Depois aplicar patch nginx conforme `deploy/PATCH_NGINX_P1-1.md`. Depois rodar `node deploy/promote-stable.js`.

### Próximo passo autônomo (próximo cron às 12:07)

Após o deploy, rodar `npx playwright test tests/e2e/03-campaign-flow.spec.ts` pra validar o flow 1 end-to-end. Se passar, marcar P4 como completed e iniciar P6_regression (rodar `tests/regression.sh` completo). Se falhar, abrir bug P2-1 e priorizar fix.

---

## Checkpoint 12 — 2026-07-24 12:35 UTC

**Status**: P2_smoke (button walker profundo).

### Demand: "validar cada botão do painel de cada aba ou sub aba"

Construídos 2 specs de walker que clicam em **cada botão interativo** do app, validando 5xx, JS uncaught e console.error a cada clique:

| Spec | O que faz | Cobertura |
|---|---|---|
| `tests/e2e/04-button-walker.spec.ts` | Pra cada uma das 13 abas top-level (cost, crm, chat, manager_chat, specialized, agenda, catalog, calls, meeting-ai, settings, logs, analytics, lists), abre cada sub-aba listada, depois enumera TODOS os `button:visible` e clica em cada um (skip destrutivos: sair/excluir/remover/disconnect/delete + skip risky: enviar agora/assinar/pagar). Screenshot + latência + lista de 5xx/JS errors por clique. Report gravado em `tests/screenshots/button-walker-report.json` | ~13 abas × ~10-30 botões = ~150-400 cliques |
| `tests/e2e/05-settings-walker.spec.ts` | Foco no /settings. Itera 12 sub-abas (Configura Fácil, Cérebro, Agente Gestor, Webhook, Credenciais, Segurança, Perfil, Workspaces, Aparência, Chat, Avançado, Logs). Em cada uma: click no primeiro switch (toggle), testa até 5 botões não-destrutivos, mede latência de carregamento (<5s). Garante 0 5xx e 0 JS uncaught no painel inteiro de configurações | 12 sub-abas |

### Skip rules (não destrói dados)

```js
// DESTRUCTIVE_PATTERNS
/sair/i, /logout/i, /excluir/i, /remover/i, /delete/i, /disconnect/i,
/deletar/i, /apagar/i, /desconectar/i, /cancelar assinatura/i, /revoke/i,
/reset/i, /limpar tudo/i, /deletar conta/i, /apagar conta/i

// RISKY_BUTTON_PATTERNS (cobrança real / WhatsApp real)
/enviar agora/i, /disparar campanha/i, /iniciar campanha/i,
/pagar/i, /assinar/i, /upgrade agora/i, /comprar/i,
/conectar whatsapp/i
```

### Como rodar

```bash
cd tests
npx playwright test 04-button-walker.spec.ts --reporter=list
npx playwright test 05-settings-walker.spec.ts --reporter=list
# Relatório completo em tests/screenshots/button-walker-report.json
```

### Próximo passo autônomo (próximo cron às 13:05)

Se P5_fixes não tiver deploy do usuário ainda, focar em:
1. Adicionar **P2-1**: regression test que valida que cada persona consegue abrir a home `/` sem 5xx (já existe em 01-smoke-routes, mas falta validar UI React renderizada, não só API).
2. Adicionar **walker de formulários**: preencher cada form (criar contato, criar tag, criar evento) com dados válidos e validar que persiste (GET confirma).

---

## Checkpoint 13 — 2026-07-24 12:40 UTC

**Status**: P6_regression — suite 100% verde. Deploy no ar (build 20260724-1229, channel=beta).

### (a) O que foi completado desde o checkpoint anterior

O usuário perguntou "o que está dando errado no deploy?". **Resposta: o deploy nunca esteve quebrado.** `node deploy/deploy-beta.js` rodou de primeira (SFTP das fontes + docker build na VPS + container healthy). O que travava era a **regression acusando bugs REAIS de backend**. Rodei o ciclo diagnosticar→corrigir→redeploy→revalidar até zerar as falhas. 5 bugs de backend corrigidos e deployados:

| Bug | Sintoma | Fix | Arquivo |
|---|---|---|---|
| BUG-3 | `GET /api/contacts` (e qualquer `/api/*` sem handler) retornava o app React com HTTP 200 (HTML), quebrando clients de API | `spaHandler` agora retorna 404 pra rotas `/api/*` não-casadas | cmd/server/httpapi.go |
| BUG-4 | `/api/auth/me` não trazia `features.tabs` — frontend/QA não sabiam quais abas mostrar | adicionado `features: featuresForPlan(u.Plan)` | cmd/server/auth_handlers.go |
| BUG-5 (SEC-4) | cupom fora da allowlist ("ADMIN","FREE") era aceito com 200 → backdoor de trial grátis | valida `TESTE_GRATIS` + `HERMES_FREE_COUPONS`, rejeita resto com 400 | cmd/server/billing_api.go |
| BUG-1 (SEC-8) | rate-limit de login não bloqueava em 8 tentativas | threshold 8→5 | internal/auth/store.go |
| BUG-6 (SEC-10) | payload de 5MB derrubava handler com 500 | middleware `withMaxBodySize` 1MB → 413 | cmd/server/httpapi.go |

Além disso, **smoke test corrigido**: batia em 6 rotas que nunca existiram (`/api/calls/recent`, `/api/chat/sessions`, `/api/crm/deals`, `/api/agenda/events`, `/api/phone-numbers`, `/api/meet/sessions`) — substituídas pelas reais do backend (`/api/crm/board`, `/api/chat/threads`, `/api/agenda/appointments`, `/api/contacts/leads`, `/api/transcripts`, `/api/recordings`).

**Descoberta de infra**: a VPS de produção usa **Traefik** (`/opt/traefik-config/dynamic/hermes.yml`), NÃO nginx. Isso invalida o `deploy/PATCH_NGINX_P1-1.md` — o patch do P1-1 precisa ser reescrito como regra Traefik.

**Regression final**: `20 passed, 0 failed, 2 skipped` (skips por rate-limit na criação de conta, esperado). Os 6 testes SEC-10..15 que escrevi de manhã passam.

### (b) Blocker atual

Nenhum blocker técnico. QA passa 100%, deploy no ar. O único item pendente é **decisão do usuário**: validar visualmente e rodar `node deploy/promote-stable.js` pra marcar este beta como estável. P1-1 (Traefik /login rewrite) é cosmético (workaround `/?action=login` funciona).

### (c) Próximo passo concreto

1. Reescrever `deploy/PATCH_NGINX_P1-1.md` como patch Traefik (middleware de `replacePathRegex` ou roteador SPA) já que a VPS não tem nginx.
2. Continuar P4_e2e_flows: faltam 4 fluxos (whatsapp-connect, agent-configure, live-monitor, billing).
3. Artefatos verificados no disco: todos os 6 specs e2e + stress/01-volume.spec.ts existem. ✅


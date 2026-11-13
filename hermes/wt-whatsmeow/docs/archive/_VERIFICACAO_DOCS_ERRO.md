# Verificação de veracidade dos docs de erro (vs fonte atual + golden)

> Ciclo noturno 2026-07-26 ~02:55. A dona pediu: os docs de erro antigos foram
> feitos na versão ERRADA (contaminada) — verificar quais bugs são REAIS na
> v0.2.1 antes de "recorrigir". Legenda:
> - **JÁ-CORRIGIDO**: fix presente no fonte local (marcador `FIX Px-xxx` ou lógica confirmada). Não retrabalhar.
> - **REAL-PENDENTE**: bug ainda existe, precisa correção.
> - **FALSO-POSITIVO / OBSOLETO**: não se aplica à v0.2.1 ou já resolvido de outra forma.
> - **PRECISA-DONA**: só validável ao vivo.

## Bugs de backend do QA_STATE.json (5) — TODOS JÁ-CORRIGIDOS ✅
Confirmado lendo o fonte Go local (que gera o binário da v0.2.1):

| ID | Sintoma | Status | Evidência no fonte |
|----|---------|--------|--------------------|
| BUG-3 QA | `/api/*` sem handler devolvia HTML 200 | **JÁ-CORRIGIDO** | httpapi.go:584 `HasPrefix(path,"/api/")` → `http.NotFound` |
| BUG-4 QA | `/auth/me` sem `features.tabs` | **JÁ-CORRIGIDO** | auth_handlers.go:127 `"features": featuresForPlan(u.Plan)` |
| BUG-5 QA (SEC-4) | cupom fora da allowlist aceito (backdoor) | **JÁ-CORRIGIDO** | billing_api.go:169 allowlist `TESTE_GRATIS` + `HERMES_FREE_COUPONS` |
| BUG-1 QA (SEC-8) | rate-limit login não travava | **JÁ-CORRIGIDO** | auth/store.go:49 `loginMaxAttempts (5)` janela 10min |
| BUG-6 QA (SEC-10) | payload 5MB → 500 | **JÁ-CORRIGIDO** | httpapi.go:572 `withMaxBodySize(handler, 1<<20)` → 413 |

## Bugs P0/P1/P2 dos docs (_ACHADOS_NOTURNOS / _CORRECOES_LOG / RELATORIO_QA_12H)
Todos os 20 IDs (P0-001..010, P1-001..007, P2-001..003) verificados. Todos têm fix no fonte:

| ID | Descrição | Status | Evidência |
|----|-----------|--------|-----------|
| P0-001 | AuthGate bypass (portas 5173/5174) | **JÁ-CORRIGIDO** | AuthGate.tsx:12 "FIX P0-001 ... bypass REMOVIDO" |
| P0-002 | senha mínima 6 chars | **JÁ-CORRIGIDO** | marcador `FIX P0-002` no fonte |
| P0-003 | valida formato email | **JÁ-CORRIGIDO** | marcador `FIX P0-003` |
| P0-004 | sanitiza strings do front | **JÁ-CORRIGIDO** | marcador `FIX P0-004` |
| P0-005 | transcripts delete | **JÁ-CORRIGIDO** | marcador `FIX P0-005` |
| P0-006 | JWT in URL | **JÁ-CORRIGIDO** | marcador `FIX P0-006` |
| P0-007 | SpecializedAgents persistTrigger (só ~11 campos) | **JÁ-CORRIGIDO** | SpecializedAgents.tsx:113 "FIX P0-007" |
| P0-008 | dashboard skeleton | **JÁ-CORRIGIDO** | marcador `FIX P0-008` |
| P0-009 | recordings/transcripts sem case no App.tsx | **JÁ-CORRIGIDO** | App.tsx:140-141 ambos roteados |
| P0-010 | rate-limit semantics | **JÁ-CORRIGIDO** | marcador `FIX P0-010` |
| P1-001 | 45 silenciadores de catch | **JÁ-CORRIGIDO** | lib/log.ts criado |
| P1-002 | ErrorBoundary leak | **JÁ-CORRIGIDO** | marcador `FIX P1-002` |
| P1-003 | EmptyState sem retry | **JÁ-CORRIGIDO** | EmptyState.tsx tem retry |
| P1-004 | register 409 | **JÁ-CORRIGIDO** | marcador `FIX P1-004` |
| P1-005/006 | refresh/logout | **JÁ-CORRIGIDO** | marcador `FIX P1-005/006` |
| P1-007 | RecordingsPage false-success delete | **JÁ-CORRIGIDO** | P1_007_NOTE.ts: auditado, delete real |
| P2-001 | onboarding done per-user | **JÁ-CORRIGIDO** | SetupWizard.tsx `isOnboardingDone` |
| P2-002 | silent catch | **JÁ-CORRIGIDO** | marcador `FIX P2-002` |
| P2-003 | textos i18n hardcoded | **RELACIONADO À RECONSTRUÇÃO** | é a própria regressão de 178 strings UI já mapeada em `_PLANO_RECONSTRUCAO_v0.2.1.md` |

## Conclusão desta verificação
**Nenhum dos bugs documentados (backend QA + 20 P-bugs) precisa de retrabalho** — todos já
estão corrigidos no fonte local que gera a v0.2.1. Confirma a suspeita da dona: os docs
refletem trabalho JÁ FEITO, não pendências. O único item "vivo" é P2-003 (textos
hardcoded), que coincide com a reconstrução de UI em andamento (regressões do golden).

**Foco real do trabalho** portanto NÃO são os docs antigos, e sim:
1. Regressões de UI vs golden (178 strings — billing, vozes, funil, RAG, copilot, listas).
2. Os 7 BUGs NOVOS achados pela dona ao vivo na v0.2.1 (ver `_BUGS_v0.2.1_A_CORRIGIR.md`) — esses SIM são reais e alguns pendentes.

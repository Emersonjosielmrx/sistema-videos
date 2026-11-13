# PLANO DE CORREÇÕES — Hermes Call
## Para: agente humano de manhã / auditor
## Estado: 🚧 PRONTO PARA EXECUÇÃO (não iniciado)

**Data de criação:** 2026-07-25 ~10:30
**Última edição:** 2026-07-25 ~10:30
**Working dir:** `d:\hipercool-refactor`

---

## 0. COMO USAR ESTE DOCUMENTO

Cada bug está listado com:
- **O QUÊ** — descrição do bug
- **ONDE** — `arquivo:linha`
- **POR QUÊ** — causa raiz
- **COMO REPRODUZIR** — passos
- **COMO REVERTER** — `git tag + checkout` ou patch
- **CORREÇÃO PROPOSTA** — código antes/depois
- **CHECKLIST** — passos para aplicar
- **PRIORIDADE** — 🔴 P0 / 🟠 P1 / 🟡 P2

### REGRA DE OURO ANTES DE CADA CORREÇÃO

```bash
# 1. SEMPRE criar tag pre-fix
git tag pre-fix-<NOME>-$(date +%Y%m%d-%H%M%S)

# 2. Aplicar correção

# 3. SEMPRE criar tag post-fix
git tag post-fix-<NOME>-$(date +%Y%m%d-%H%M%S)

# 4. SEMPRE documentar no log
# 5. SEMPRE testar (build + smoke)

# SE DER RUIM:
git checkout pre-fix-<NOME>-<timestamp>  # volta tudo
```

---

## 1. BUGS CRÍTICOS (P0) — corrigir primeiro

### P0-001: AuthGate BYPASSA auth nas portas 5173/5174
- **Onde:** `client/src/AuthGate.tsx:13-17`
- **Por quê:** Comentário "TEMPORARY BYPASS FOR TESTING DASHBOARD WITHOUT BACKEND" — qualquer proxy/CDN que reescreva pra uma dessas portas BURLA o login.
- **Como reproduzir:** Acessar app em `http://localhost:5173` → entra direto no dashboard, sem token.
- **Severidade:** 🔴 CRÍTICA — bypass de auth em produção possível.

**CORREÇÃO PROPOSTA:**
```typescript
// ANTES (AuthGate.tsx)
useEffect(() => {
  if (window.location.port === "5173" || window.location.port === "5174") {
    // TEMPORARY BYPASS FOR TESTING DASHBOARD WITHOUT BACKEND ON PORT 5173 or 5174
    setState("ok");
    return;
  }
  checkAuth().then((result) => { ... });
});

// DEPOIS
useEffect(() => {
  // Bypass REMOVIDO por P0-001: bypass expunha auth em prod.
  // Devs devem rodar `npm run dev` (porta 5173) com backend local ou mock JWT.
  checkAuth().then((result) => { ... });
});
```

**Reverter:**
```bash
git tag pre-fix-p0-001-$(date +%Y%m%d-%H%M%S)
# ... aplicar correção
git tag post-fix-p0-001-$(date +%Y%m%d-%H%M%S)
# SE RUIM: git checkout pre-fix-p0-001-20260725-XXXXXX
```

**Checklist:**
- [ ] tag pre-fix criada
- [ ] código alterado
- [ ] `npm run build` no client OK
- [ ] tag post-fix criada
- [ ] testar fluxo: sem token → tela de login
- [ ] testar fluxo: com token → entra no dashboard
- [ ] testar em prod: `https://hermescall.opus-sem-limites.com.br` → exige token

---

### P0-002: Register aceita SENHA de 3 chars
- **Onde:** `cmd/server/auth_handlers.go:14-45` + `internal/auth/store.go:66-110`
- **Por quê:** Front impõe min 6 (RegisterScreen.tsx:70), mas backend NÃO valida. `Register` só checa `password == ""`.
- **Como reproduzir:** `curl -X POST .../api/auth/register -d '{"email":"x","password":"123","name":"X","plan":"basic"}'` → HTTP 201.
- **Severidade:** 🔴 ALTA — bypass do frontend (mobile, curl) permite senhas fracas.

**CORREÇÃO PROPOSTA:**
```go
// internal/auth/store.go
func (s *Store) Register(ctx context.Context, email, password, name, whatsapp, company, plan string) (*User, error) {
  email = strings.ToLower(strings.TrimSpace(email))
  if email == "" {
    return nil, fmt.Errorf("email is required")
  }
  // P0-002: senha mínima 6 chars (espelha RegisterScreen.tsx:70)
  if len(password) < 6 {
    return nil, fmt.Errorf("password must be at least 6 characters")
  }
  if name == "" {
    return nil, fmt.Errorf("name is required")
  }
  // ... resto
}
```

**Reverter:** mesmo padrão de tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `go build ./...` no cmd/server OK
- [ ] tag post-fix
- [ ] curl com password="123" → 400/409
- [ ] curl com password="<SEGREDO_REMOVIDO>" → 201
- [ ] cleanup user `qanight-short@naoexiste.com` do banco

---

### P0-003: Register aceita email INVÁLIDO
- **Onde:** `cmd/server/auth_handlers.go:14-45` + `internal/auth/store.go:66-110`
- **Por quê:** Backend só checa `email == ""`. Aceita "not-an-email", "qanight-injection@x.com'" (aspa), etc.
- **Como reproduzir:** `curl -X POST -d '{"email":"not-an-email","password":"<SEGREDO_REMOVIDO>","name":"X","plan":"basic"}'` → HTTP 201.
- **Severidade:** 🔴 ALTA — emails inválidos no banco quebram envio de notificações/promoções.

**CORREÇÃO PROPOSTA:**
```go
import "net/mail"

// internal/auth/store.go
func (s *Store) Register(...) (*User, error) {
  email = strings.ToLower(strings.TrimSpace(email))
  if email == "" {
    return nil, fmt.Errorf("email is required")
  }
  // P0-003: validar formato do email
  if _, err := mail.ParseAddress(email); err != nil {
    return nil, fmt.Errorf("email is invalid")
  }
  // ... resto
}
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `go build` OK
- [ ] tag post-fix
- [ ] curl email "not-an-email" → 400
- [ ] curl email "test@x.com" → 201
- [ ] cleanup users inválidos (`not-an-email`, `qanight-injection@x.com'`)

---

### P0-004: Register armazena XSS em `company`
- **Onde:** `cmd/server/auth_handlers.go:14-45` + `internal/auth/store.go:66-110`
- **Por quê:** `company = "<script>alert(1)</script>"` aceito e devolvido na resposta.
- **Como reproduzir:** `curl -X POST -d '{"email":"x","password":"<SEGREDO_REMOVIDO>","name":"X","company":"<script>alert(1)</script>"}'` → HTTP 201.
- **Severidade:** 🔴 ALTA — XSS armazenado quebra se admin panel renderiza user.company sem escape.

**CORREÇÃO PROPOSTA:**
```go
import "html"

// internal/auth/store.go
func sanitizeString(s string, maxLen int) string {
  s = strings.TrimSpace(s)
  // P0-004: remover HTML tags perigosos
  s = html.EscapeString(s)
  if len(s) > maxLen {
    s = s[:maxLen]
  }
  return s
}

func (s *Store) Register(...) (*User, error) {
  // ...
  company = sanitizeString(company, 500)
  // ... idem para name (máx 200), whatsapp (máx 50)
}
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `go build` OK
- [ ] tag post-fix
- [ ] curl com `<script>` → 400 ou sanitize
- [ ] cleanup user `qanight-tax@x.com`

---

### P0-005: deleteSelected de Transcripts é FALSE-SUCESSO
- **Onde:** `client/src/pages/TranscriptsPage.tsx:51-58`
- **Por quê:** `// TODO: implement real deletion endpoint` antes de `toast.success(...)`. Remove da UI mas não persiste.
- **Como reproduzir:** Selecionar transcrições → "Apagar" → confirmar → toast verde + some da tela.
- **Severidade:** 🔴 CRÍTICA — usuário pensa que apagou, mas só escondeu.

**OPÇÃO A (esconder botão):**
```typescript
// client/src/pages/TranscriptsPage.tsx:51-58
// REMOVER toda a função deleteSelected
// REMOVER o botão <Button variant="destructive" ... onClick={deleteSelected}> (linha 112-115)
// Manter apenas Export CSV
```

**OPÇÃO B (implementar endpoint DELETE):**
```go
// cmd/server/transcripts.go (NOVO)
func (s *server) handleDeleteTranscript(w http.ResponseWriter, r *http.Request) {
  u := userFromCtx(r)
  if u == nil { /* 401 */ }
  id := r.PathValue("id")
  _, err := s.db.ExecContext(r.Context(),
    `DELETE FROM call_transcripts WHERE id=$1 AND user_id=$2`, id, u.ID)
  if err != nil { /* 500 */ }
  writeJSON(w, 200, map[string]any{"ok": true})
}
```
```typescript
// client/src/pages/TranscriptsPage.tsx
const deleteSelected = async () => {
  if (!selectedIds.length) return;
  if (!confirm(`Apagar ${selectedIds.length} ligações?`)) return;
  try {
    for (const id of selectedIds) {
      await apiDelete(`/api/transcripts/${id}`);
    }
    toast.success(`${selectedIds.length} registros apagados.`);
    setList(prev => prev.filter(t => !selectedIds.includes(t.id)));
    setSelectedIds([]);
  } catch (e: any) {
    toast.error(`Erro ao apagar: ${e.message}`);
  }
};
```

**Recomendação:** OPÇÃO A (esconder botão) é mais segura — não força deploy de backend.

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] Escolher Opção A ou B
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `npm run build` no client OK (ou `go build` se B)
- [ ] tag post-fix
- [ ] testar: botão some (A) ou apaga real (B)

---

### P0-006: JWT em URL em event-stream.ts:36, LogsPage:40, RecordingsPage:18
- **Onde:** `client/src/lib/event-stream.ts:36`, `client/src/pages/LogsPage.tsx:40`, `client/src/pages/RecordingsPage.tsx:18`
- **Por quê:** Token aparece em proxy logs, Intercom, analytics, Sentry.
- **Severidade:** 🔴 ALTA — info leak.

**CORREÇÃO PROPOSTA:**
- **EventSource não suporta headers customizados** (limitação do browser). Solução real: usar **cookie httpOnly** para SSE, OU **polling + fetch** com Auth header.
- **Workaround imediato:** adicionar replace de token na URL via `?apiKey=` mas LOGAR warning se visível em `console.warn`.

**Opção A (curto prazo, FÁCIL):**
```typescript
// client/src/lib/event-stream.ts:36
// ANTES: const url = `${getApiBase()}/api/events?clientId=${...}&apiKey=${...}`;
// DEPOIS: NÃO colocar apiKey em URL. Backend valida por cookie httpOnly OU connection origin.
const url = `${getApiBase()}/api/events?clientId=${encodeURIComponent(clientId)}`;
```

**Mas isso exige backend suporte.** Confirmar antes.

**Opção B (logging):**
```typescript
// client/src/lib/event-stream.ts
console.warn("[SECURITY] JWT in URL — visible to proxies. Use httpOnly cookie instead.");
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] Escolher A (refactor) ou B (feedback)
- [ ] tag pre-fix
- [ ] código alterado
- [ ] tag post-fix
- [ ] testar: token não aparece em URL

---

### P0-007: Salvar gatilho de agente APAGA perfil inteiro
- **Onde:** `client/src/components/specialized/SpecializedAgents.tsx:112-125` + `cmd/server/agentprofiles.go:282-303`
- **Por quê:** UPSERT `ON CONFLICT DO UPDATE SET <todos 35 campos> = EXCLUDED.*` zera campos não enviados.
- **Severidade:** 🔴 CRÍTICA — destruição de dados em massa.

**CORREÇÃO PROPOSTA:**
```typescript
// SpecializedAgents.tsx:112-125
// ANTES: persistTrigger envia só ~10 campos
// DEPOIS: envia spread ...agent completo
const persistTrigger = async (trigger: string) => {
  const all = { ...currentAgent, trigger }; // P0-007: spread pra não apagar
  return apiPut(`/api/agent-profiles/${currentAgent.id}`, all);
};
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `npm run build` OK
- [ ] tag post-fix
- [ ] testar: salvar gatilho NÃO apaga voz/prompts

---

### P0-008: Dashboard skeleton infinito
- **Onde:** `client/src/pages/DashboardPage.tsx:149,162`
- **Por quê:** `fetchDashboard().catch(() => {})` — `data` fica null → `<Skeleton>` pra sempre.
- **Severidade:** 🟠 MÉDIA — UX ruim mas não destrutivo.

**CORREÇÃO PROPOSTA:**
```typescript
// DashboardPage.tsx:149
// ANTES: fetchDashboard(...)..catch(() => {});
// DEPOIS:
// fetchDashboard().then(setData).catch((e) => {
//   setError(e.message);
//   setData(null); // importante
// });
// E no render: if (error) return <ErrorState msg={error} onRetry={...} />;
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] tag post-fix
- [ ] testar: 500 simulado → mostra erro, não skeleton

---

### P0-009: view "recordings"/"transcripts" no union mas SEM case no App.tsx
- **Onde:** `client/src/types/navigation.ts:4` + `client/src/App.tsx:114-167`
- **Por quê:** Se usuário clicar em item que seta view="recordings", cai em `EmptyState`.
- **Severidade:** 🔴 CRÍTICA — UX quebra.

**CORREÇÃO PROPOSTA:**
```typescript
// client/src/App.tsx:114-167
// ADICIONAR cases:
if (view === "recordings") return <RecordingsPage />;
if (view === "transcripts") return <TranscriptsPage />;
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] Verificar se RecordingsPage e TranscriptsPage existem
- [ ] tag pre-fix
- [ ] código alterado
- [ ] tag post-fix
- [ ] testar: navegação → recordings/transcripts abrem

---

### P0-010: Rate Limit bidirecional salva semântica trocada
- **Onde:** `cmd/server/features_api.go:854-862`
- **Por quê:** `MaxMessages → MaxReqPerHour` e `WindowSeconds → MaxReqPerMin`. Banco grava trocado.
- **Severidade:** 🔴 ALTA — proteção fica errada.

**CORREÇÃO PROPOSTA:**
```go
// features_api.go:858
// ANTES: cfg.MaxReqPerHour = body.MaxMessages; cfg.MaxReqPerMin = body.WindowSeconds;
// DEPOIS: usar campos semânticos corretos
type RateLimitSettings struct {
  MaxMessagesPerHour int `json:"max_messages_per_hour"`
  MaxMessagesPerMin  int `json:"max_messages_per_min"`
  // ...
}
```

**Reverter:** tags pre/post-fix.

**Checklist:**
- [ ] tag pre-fix
- [ ] código alterado
- [ ] `go build` OK
- [ ] tag post-fix
- [ ] testar: PUT /api/settings/rate-limit → banco grava correto

---

## 2. BUGS MÉDIOS (P1) — corrigir após P0

### P1-001: EventStream.onerror = () => {}
- **Onde:** `client/src/lib/event-stream.ts:44`
- **Correção:** adicionar reconexão com backoff.
```typescript
// event-stream.ts
this.#es.onerror = (e) => {
  console.warn("[eventStream] connection error, reconnecting in 5s");
  this.#es?.close();
  setTimeout(() => this.connect(lastClientId), 5000);
};
```

### P1-002: ErrorBoundary info leak
- **Onde:** `client/src/components/ErrorBoundary.tsx:34`
- **Correção:** mostrar mensagem genérica + botão "Copiar detalhes".
```typescript
// ErrorBoundary.tsx
<pre className="...hidden">{error.stack}</pre>  // hidden by default
<Button onClick={() => navigator.clipboard.writeText(error.stack)}>Copiar detalhes</Button>
```

### P1-003: EmptyState sem botão de retry
- **Onde:** `client/src/components/shared/EmptyState.tsx`
- **Correção:** adicionar prop `onRetry`.

### P1-004: `register` retorna 409 em "email is required"
- **Onde:** `cmd/server/auth_handlers.go:30-36`
- **Correção:** separar 400 (validation) de 409 (conflict).
```go
code := http.StatusInternalServerError
if strings.Contains(err.Error(), "required") {
  code = http.StatusBadRequest  // 400, não 409
} else if strings.Contains(err.Error(), "already registered") {
  code = http.StatusConflict
}
```

### P1-005: `/api/auth/refresh` exige token
- **Onde:** sem handler (rota fantasma)
- **Correção:** criar handler público:
```go
// cmd/server/auth_handlers.go
func (s *server) handleAuthRefresh(w http.ResponseWriter, r *http.Request) {
  // recebe refresh_token (oposto do access) OU usa Authorization
  // retorna novo token
}
```

### P1-006: `/api/auth/logout` exige token
- **Onde:** sem handler
- **Correção:** criar handler que invalida session.
```go
// cmd/server/auth_handlers.go
func (s *server) handleAuthLogout(w http.ResponseWriter, r *http.Request) {
  u := userFromCtx(r)
  if u != nil {
    s.users.Logout(r.Context(), u.ID)
  }
  writeJSON(w, 200, map[string]any{"ok": true})
}
```

### P1-007: deleteRecording / EasyWizard / outros false-success
- **Onde:** vários — ver `_ACHADOS_NOTURNOS.md` Rodada 16, 18, 19
- **Correção:** padrão: NÃO mostrar toast.success antes do await.

---

## 3. BUGS BAIXOS (P2) — corrigir por último

### P2-001: Onboarding done em localStorage (per-user-agnostic)
- **Onde:** `client/src/components/onboarding/SetupWizard.tsx:6-9`
- **Correção:** incluir user.id na key.
```typescript
const DONE_KEY = (userId: string) => `hermes.onboarding.done.${userId}`;
```

### P2-002: getUser() sem try/catch
- **Onde:** `client/src/lib/auth.ts:5-8`
- **Correção:**
```typescript
export const getUser = (): any => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
};
```

### P2-003: Various texts i18n hardcoded
- **Onde:** LoginScreen.tsx, RegisterScreen.tsx
- **Correção:** mover pra i18n key.

---

## 4. LIMPEZA DE DADOS

### Usuários de teste para deletar (DB)
```sql
DELETE FROM users WHERE email IN (
  'qanight-short@naoexiste.com',
  'not-an-email',
  'qanight-injection@x.com''',
  'qanight-plan@x.com',
  'qanight-tax@x.com',
  'qaNIGHT-ratelimit@x.com'
);
```

Nota: `qanight-injection@x.com'` tem aspas — escape correto no SQL.

---

## 5. CHECKLIST GERAL DE EXECUÇÃO

### Antes de qualquer correção
- [ ] `git status` clean
- [ ] `git tag pre-fix-<NOME>-<timestamp>` criado
- [ ] Backup local se modificação grande

### Durante a correção
- [ ] Editar arquivos
- [ ] `npm run build` no client (se TS)
- [ ] `go build ./...` no cmd/server (se Go)
- [ ] Atualizar `_CORRECOES_LOG.md` (criar)

### Depois da correção
- [ ] `git tag post-fix-<NOME>-<timestamp>`
- [ ] Smoke test manual: rodar app, clicar no fluxo alterado
- [ ] Curl: testar endpoint alterado (200/201 para happy path, 4xx para edge)
- [ ] Documentar reversão

### Se DER ERRADO durante a correção
- [ ] `git checkout pre-fix-<NOME>-<timestamp>`
- [ ] `git checkout main`
- [ ] Investigar causa raiz
- [ ] Tentar de novo

---

## 6. SCRIPT AUXILIAR (deixar no fim do doc)

```bash
#!/bin/bash
# fix.sh — aplica uma correção com backup automático
# USO: ./fix.sh "p0-001-authgate-bypass" "Descrição da correção"

set -e
NAME=$1
DESC=$2
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

cd /d/hipercool-refactor

echo "🛡️  Criando tag pre-fix: pre-fix-$NAME-$TIMESTAMP"
git tag pre-fix-$NAME-$TIMESTAMP

echo "📝 $DESC"
echo "✏️  Faça as edições no código agora."

# Wait for user
read -p "Pressione ENTER quando terminar de editar..."

echo "🔨 Rodando build..."
(cd client && npm run build 2>&1 | tail -5) || echo "Build falhou — reverta!"
(cd cmd/server && go build ./... 2>&1 | tail -5) || echo "Build Go falhou — reverta!"

echo "🏷️  Criando tag post-fix: post-fix-$NAME-$TIMESTAMP"
git tag post-fix-$NAME-$TIMESTAMP

echo "✅ Correção $NAME registrada."
echo "Rollback: git checkout pre-fix-$NAME-$TIMESTAMP"
```

---

## 7. STATUS DE EXECUÇÃO

| Bug | Status | Data | Quem | Tag |
|---|---|---|---|---|
| P0-001 | ⏳ pendente | — | — | — |
| P0-002 | ⏳ pendente | — | — | — |
| P0-003 | ⏳ pendente | — | — | — |
| P0-004 | ⏳ pendente | — | — | — |
| P0-005 | ⏳ pendente | — | — | — |
| P0-006 | ⏳ pendente | — | — | — |
| P0-007 | ⏳ pendente | — | — | — |
| P0-008 | ⏳ pendente | — | — | — |
| P0-009 | ⏳ pendente | — | — | — |
| P0-010 | ⏳ pendente | — | — | — |
| P1-001 | ⏳ pendente | — | — | — |
| ... | ... | ... | ... | ... |

(A ser preenchido pelo agente executor de correções.)

---

## 8. NOTAS FINAIS

- **Backup 23/07 PRESERVADO** — `backup-pre-qa-12h-2026-07-23` (tag) + `landing_HERMES_BACKUP_2026-07-23_DEPLOY.tar.gz`.
- **Backup NOVO 25/07 criado** — `backup-pre-correcoes-2026-07-25` (tag) + `_BACKUP_SOURCE_2026-07-25_PRE-CORRECOES.tar.gz`.
- **Cron PAUSADA** — ID `c0a8152c` deletada.
- **Working dir:** `d:\hipercool-refactor` (código) — não `d:\hipercool-videos` (vazio).
- **Total de bugs NOVOS:** ~314 (24 rodadas).
- **Total de CRÍTICOS (🔴):** ~20.
- **Total de MÉDIOS (🟠):** ~154.
- **Total de BAIXOS (🟡):** ~140.

---

**FIM DO PLANO DE CORREÇÕES — 2026-07-25 ~10:30**

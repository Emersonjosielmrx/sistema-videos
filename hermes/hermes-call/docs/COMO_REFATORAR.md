# COMO REFATORAR — Plano de modularização do Hermes Call v3

**Estado atual:** 1 package `main` (cmd/server/) com 108 arquivos, ~22.000 linhas. Frontend separado em `client/`. Internals já em `internal/voice`, `internal/voip`, `internal/wa`.

**Meta:** quebrar `cmd/server/` em pacotes `internal/<domínio>/` mantendo o entry point (`cmd/server/main.go` + `server.go`) fino.

**Regra de ouro:** NÃO MUDE COMPORTAMENTO ENQUANTO REFATORA. Cada passo deve compilar, rodar, e ter o mesmo output que antes. Se mudar comportamento, faça em commit separado DEPOIS.

---

## Fase 0 — Setup (já feito)

- ✅ `docs/ARCHITECTURE.md` com mapa dos 108 arquivos
- ✅ `docs/COMO_DEBUGAR.md` com troubleshooting
- ✅ Comentários inline em `authmw.go`, `sessionstore.go`
- ⏳ Próximos comentários: `auth.go`, `sessionmanager.go`, `session.go`, `settings.go`, `settingsapi.go`, `httpapi.go`, `telegram.go`, `broadcast.go` (esses dois últimos são os maiores)

**Sugestão:** faça os comentários de todos antes de mover arquivos. Vai dar contexto de quem chama quem.

---

## Fase 1 — Pacotes pequenos, sem dependência circular

### 1.1 `internal/auth`

**Origem:** `cmd/server/auth.go` (385 linhas), `authmw.go` (95), `apikeys.go` (143), `sessions_security.go` (163).

**Plano:**

```
internal/auth/
├── README.md             # O que é, contratos, exemplos
├── types.go              # type User, ctxKey, userCtxKey
├── jwt.go                # jwtSecret, generateJWT, parseJWT, TrialExpired
├── store.go              # userStore + newUserStore (cria tabela users)
├── apikey.go             # APIKeyStore + NewAPIKeyStore (cria tabela api_keys)
├── loginsession.go       # sessions_security.go (renomeado)
├── middleware.go         # withUserAuth, userFromCtx
├── handlers.go           # handleAuthRegister, handleAuthLogin, handleAuthMe
└── seed.go               # seedAdmin (cria admin@hermescall.com no boot se não existe)
```

**Problema principal:** `User` é usado em praticamente todos os outros arquivos. Tem 2 opções:

- **Opção A:** Mover `User` para `internal/auth` e importar de lá. Todos os outros pacotes passam a importar `internal/auth`. Funciona, mas cria dependência de alto nível.
- **Opção B:** Deixar `type User` em `internal/model/` ou similar e fazer `internal/auth` trabalhar com ele. Mais limpo a longo prazo.

**Sugestão:** comece com A e migre pra B depois. Não otimize prematuramente.

**Cuidados:**

- O `userFromCtx(r)` retorna `*auth.User`. Os handlers antigos vão precisar trocar `*User` por `*auth.User`.
- `authmw_test.go` (se houver) precisa atualizar o caminho.
- O package `internal/auth` não pode importar `main`. Senão ciclo.

### 1.2 `internal/sessions`

**Origem:** `cmd/server/sessionmanager.go` (289), `sessionstore.go` (95), `session.go` (692), `sessions_security.go` (163) [vai pro auth].

**Plano:**

```
internal/sessions/
├── README.md
├── store.go              # sessionStore + tabela
├── session.go            # type Session (whatsmeow wrapper)
├── manager.go            # SessionManager (in-memory map + Restore)
├── handlers.go           # httpapi.go handlers relacionados a /api/sessions/*
├── pairing.go            # QR, pair code, passkey
├── messaging.go          # envio de mensagens (texto, image, audio, etc)
├── calling.go            # chamadas VoIP
├── recording.go          # gravação de chamadas
└── events.go             # bridge/broker integration
```

**Problema principal:** `Session` referencia coisas de todo lugar. Vai precisar de interfaces.

**Interfaces sugeridas:**

```go
// em internal/sessions/ports.go
type UserFromContext interface {
    userFromCtx(r *http.Request) *auth.User  // callback
}

type EventEmitter interface {
    EmitSessionList(userID string, sessions []SessionInfo)
}

type Logger interface {
    Info(msg string, args ...any)
    Error(msg string, args ...any)
    Warn(msg string, args ...any)
}
```

E o `SessionManager` recebe via construtor. Evita importar `main`.

### 1.3 `internal/settings`

**Origem:** `cmd/server/settings.go` (565), `settingsapi.go` (375), `features_api.go` (603).

**Plano:**

```
internal/settings/
├── store.go              # settingsStore, PK (key, user_id)
├── handlers.go           # /api/settings/*
├── features.go           # schedule, IP whitelist, rate limit
└── envfallback.go        # applyUserEnvFallbacks (somente se user não tem config)
```

### 1.4 `internal/billing`

**Origem:** `cmd/server/ai_cost.go` (~150), `cost_api.go` (~150).

```
internal/billing/
├── store.go              # ai_cost table, Record/Summary/Reset
└── handlers.go           # /api/ai-cost
```

### 1.5 `internal/analytics`

**Origem:** `cmd/server/dashboard.go`, `dashboard_analytics.go`.

### 1.6 `internal/whatsapp_campaigns`

**Origem:** `cmd/server/campaigns.go` (347), `campaigns_api.go`, `broadcast.go` (869), `massmsg.go`, `masscall.go`.

**Esse é o mais crítico** — broadcast.go tem 869 linhas e provavelmente tem o bug que o usuário reportou de "disparo sem feedback".

### 1.7 `internal/whatsapp_messaging`

**Origem:** `messaging.go` (308), `chatting.go` (295), `conversation.go` (~120).

### 1.8 `internal/telegram`

**Origem:** `telegram.go` (1860), `telegram_buttons.go` (~120).

**Esse é o monstro. Considere quebrar em:**

```
internal/telegram/
├── bot.go                # type Bot, NewBot, Start, Stop
├── commands.go           # todos os handlers de comando (/campanha, /start, etc)
├── callbacks.go          # handlers de callback de botão inline
├── sendmsg.go            # envio de mensagem pro chat_id
├── store.go              # persistência de tokens por user (se houver)
└── ratelimit.go          # evita flood
```

---

## Fase 2 — Decoupling

Depois que os pacotes `internal/*` existirem:

1. `cmd/server/server.go` passa a ser só wiring: NewServer importa e conecta os pacotes.
2. `cmd/server/httpapi.go` só tem a função `routes()` que monta os mux.
3. Cada handler HTTP vira um método do pacote correspondente.

---

## Fase 3 — Testes

Cada `internal/<domínio>/` deve ter:

- `store_test.go` — testa SQL CRUD contra Postgres real (use o docker de testes)
- `handler_test.go` — usa `httptest.NewRecorder` + token JWT de fixture

Helpers:

```go
// internal/testutil/auth.go
func NewTestUser(t *testing.T) (*auth.User, string) {
    // cria user, gera JWT, retorna
}
```

---

## Fase 4 — NÃO FAÇA

- Não mova arquivos `.go` entre pastas sem atualizar TODOS os imports ao mesmo tempo.
- Não renomeie funções públicas sem grep `-r` antes.
- Não mude assinatura de `*server.X(...)` sem mudar todas as chamadas.
- Não quebre o que funciona. Cada passo é um commit isolado.

---

## Fase 5 — Validar

A cada passo:

1. `go build -tags mlow -o /tmp/wacalls ./cmd/server` (deve compilar).
2. Deploy.
3. Login admin + janela anônima + register novo → confirmar lista de sessões vazia.
4. Disparar campanha → confirmar feedback no Telegram.
5. Trocar dark mode → confirmar fundo preto sem flash.

Só avance quando o anterior estiver verde.

---

## Anexo — Comandos úteis pra refator

```bash
# Ver quem importa um package
cd /d/callagente
grep -rn '"github.com/foo/bar"' cmd/ internal/

# Ver quem chama uma função
grep -rn "s\.sessions\.Create\|m\.sessions\.Create" cmd/ internal/

# Ver estrutura de tipos e interfaces
go doc -all ./cmd/server | head -200
```

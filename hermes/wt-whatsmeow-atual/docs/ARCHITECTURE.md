# ARCHITECTURE — Hermes Call v3 Backend

**Stack:** Go 1.26 + PostgreSQL 16 + whatsmeow (WhatsApp) + React 18/Vite (frontend)
**Total:** ~22.000 linhas Go em 108 arquivos, todos no package `main` (cmd/server/)
**Problema conhecido:** package único dificulta modularização. Ver `docs/COMO_REFATORAR.md` (próximo agente).

---

## 1. Visão geral de fluxo

```
[Navegador]
  └─ JWT (localStorage "token") ou API Key (header X-API-Key)
     └─ fetch /api/*
        └─ Traefik (TLS, https://hermes3.inovareinteligenciaartificial.com)
           └─ Docker service hermes_call_v3_hermes-call-v3
              └─ cmd/server (Go) → [com authmw.go valida JWT/APIKey]
                 ├─ cmd/server/handlers/* (httpapi.go + cada *_api.go)
                 ├─ internal/voice (TTS/STT/vad)
                 ├─ internal/voip (WebRTC + signaling + media)
                 └─ internal/wa (whatsmeow wrapper)
                    └─ Postgres (namespace = hermescall)
                       ├─ hermescall_main (dados: users, sessions, settings, campaigns...)
                       └─ hermescall_<session-id> (1 DB por sessão WhatsApp, estilo WAHA)
```

---

## 2. Mapa dos 108 arquivos (cmd/server/)

### 2.1 Entry point e infra

| Arquivo | LOC | Responsabilidade |
|---------|-----|------------------|
| `main.go` | 120 | Entry point. Flags, env, start do HTTP, Restore de sessões no boot. |
| `server.go` | 366 | `type server` (struct gigante com todos os stores), `NewServer`, `routes()`. |
| `db.go` | ~150 | Conexão Postgres, criação dos DBs por namespace. |
| `cron.go` | ~100 | Jobs periódicos (daily retries, improve analyzer). |
| `logstream.go` | 215 | Buffer de logs em memória que o frontend lê via SSE. |
| `stream_helpers.go` | ~80 | Helpers de SSE/streaming. |
| `broker.go` | 322 | `type Broker` — hub de eventos SSE por usuário (`emitSessionList`, etc). |

### 2.2 Autenticação e multi-tenant (CRÍTICO)

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `auth.go` | 385 | `type User`, `userStore`, register/login/JWT/bcrypt. Seed do admin. | ✅ |
| `authmw.go` | 95 | Middleware `withUserAuth`, `userFromCtx`, fallback de API Key. | ✅ |
| `apikeys.go` | 143 | `APIKeyStore` (hk_... keys, hash SHA-256). | ✅ |
| `sessions_security.go` | 163 | Login sessions (cookies/JWT), revoke. | ✅ |
| `passkey.go` | ~120 | WebAuthn/passkey extension. | ✅ |
| `twofa.go` | ~80 | 2FA TOTP. | ✅ |
| `accesslist.go` | ~80 | IP allowlist. | ✅ |
| `adminlist.go` | ~80 | Admin user list. | ✅ |
| `auditlog.go` | ~100 | Audit log de ações sensíveis. | ✅ |
| `privacy.go` | ~80 | LGPD, export/delete conta. | ✅ |

### 2.3 Sessões WhatsApp (CRÍTICO)

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `sessionmanager.go` | 289 | `type SessionManager` — gerencia sessões em memória (`m.sessions map`). `Restore`, `Create`, `Delete`, `infos(userID)`. | ✅ |
| `sessionstore.go` | 95 | `sessionStore` — SQL CRUD de `sessions` table. **Filtros `WHERE user_id = $1`.** | ✅ |
| `session.go` | 692 | `type Session` — uma sessão WhatsApp. Pairing, envio de msg, chamada, gravação. | ✅ |
| `whatsapp.go` | ~200 | Helpers de whatsmeow (Client, eventos, JID). | ✅ |
| `wahacompat.go` | ~80 | Compat WAHA API. | ✅ |
| `messaging.go` | 308 | Envio de mensagens (texto, imagem, áudio, vídeo, doc, location, contact, poll, link-preview). | ✅ |
| `chatting.go` | 295 | Chat em tempo real, receipts, mark-seen, typing. | ✅ |
| `conversation.go` | ~120 | Histórico de conversas. | ✅ |
| `presence.go` | ~80 | Online/offline. | ✅ |
| `reaction.go` | ~60 | Reações a mensagens. | ✅ |
| `poll.go` + `pollvote.go` | ~150 | Enquetes. | ✅ |
| `viewonce.go` | ~150 | View-once messages. | ✅ |
| `recorder.go` | 214 | Grava chamadas VoIP. | ✅ |
| `recording.go` | 239 | Reproduz gravações. | ✅ |
| `callrecording.go` | 245 | Tabela `call_recordings`, listagem, transcrição, IA summary. | ✅ |
| `callregistry.go` | ~180 | Registro de chamadas VoIP ativas. | ✅ |
| `callrouting.go` | ~150 | Roteamento de chamadas. | ✅ |
| `callclient.go` | ~150 | Cliente SIP/RTP. | ✅ |
| `call_intel.go` | ~200 | Call intelligence (analytics de chamada). | ✅ |
| `bridge.go` | ~150 | Bridge entre WhatsApp e VoIP. | ✅ |

### 2.4 Mensageria em massa (campaigns)

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `campaigns.go` | 347 | `type Campaign`, `campaignStore`. Persiste em `campaigns` table. CRUD. | ✅ |
| `campaigns_api.go` | ~150 | Endpoints `/api/campaigns/*`. | ✅ |
| `broadcast.go` | 869 | `type Broadcaster` — engine de envio em massa. LÊ listas, FAZ fila, ENVIA. **AQUI está o bug que usuário reportou de "disparo sem feedback".** | ✅ |
| `massmsg.go` | ~200 | Massa de mensagens (single-session, sem campaign). | ✅ |
| `masscall.go` | 280 | Massa de chamadas. | ✅ |
| `confirm_send.go` | ~80 | Confirmação dupla antes de enviar. | ✅ |
| `daily_retries` | ~80 | Retry diário de campanhas. | ✅ |

### 2.5 Settings e config (CRÍTICO para multi-tenant)

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `settings.go` | 565 | `type settingsStore`, PK `(key, user_id)`, env fallbacks. | ✅ |
| `settingsapi.go` | 375 | `/api/settings/*` handlers. | ✅ |
| `features_api.go` | 603 | Schedule, IP whitelist, rate limit. | ✅ |
| `ipwhitelist.go` | ~100 | IP whitelist per-user. | ✅ |
| `ratelimit.go` | ~100 | Rate limit per-user. | ✅ |
| `schedule.go` | ~100 | Horário de funcionamento. | ✅ |
| `proxy.go` | ~100 | Proxy per-session. | ✅ |
| `channels.go` | ~100 | Canais de atendimento. | ✅ |
| `chatwoot.go` | 1135 | Integração Chatwoot (per-session config). | ✅ |
| `webhook.go` | ~200 | Webhook per-session. | ✅ |
| `webhook_queue.go` | ~100 | Fila de webhooks. | ✅ |

### 2.6 Telegram (BUG REPORTADO)

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `telegram.go` | **1860** | Bot Telegram completo. Token, chat IDs autorizados, comandos, envio. **AQUI também tem o bot que monitora comandos /campanha, /disparo.** | ⚠️ PARCIAL |
| `telegram_buttons.go` | ~120 | Botões inline do Telegram. | ⚠️ |

**Problema do bug do usuário:** o `telegram.go` carrega `HERMES_TELEGRAM_TOKEN` da env **UMA VEZ no boot**, e o bot conversa com QUALQUER chat_id que esteja no campo "IDs autorizados" do admin. Quando o user novo dispara via Telegram, o bot usa o token global. Mas o feedback de "disparo iniciado / falhou" — onde está? Procurar `func (b *Bot) handleCommand` e ver se há `b.api.SendMessage` com o status.

### 2.7 IA e billing

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `aiagent.go` | 814 | AI agent por sessão (config Anthropic/Gemini). | ✅ |
| `aiagent_actions.go` | 536 | Actions do agent (transferir, encerrar, etc). | ✅ |
| `ai_cost.go` | ~150 | `ai_cost` table, `Record`/`Summary`/`Reset` por user. | ✅ |
| `cost_api.go` | ~150 | `/api/ai-cost` endpoints. | ✅ |
| `meet_agent.go` | ~200 | Integração meet.com agent. | ✅ |
| `agentprofiles.go` | ~100 | Perfis de agente. | ✅ |
| `models_api.go` | ~150 | Listagem de modelos. | ✅ |
| `tts_api.go` | ~80 | Text-to-Speech. | ✅ |
| `voice_helpers.go` | ~80 | Helpers de voz. | ✅ |
| `voiceservice.go` | ~200 | Serviço de voz agregado. | ✅ |
| `intel_log.go` | ~80 | Log de inteligência. | ✅ |
| `improve_analyzer.go` | ~150 | Analisa logs e sugere melhorias. | ✅ |

### 2.8 Dashboard / analytics

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `dashboard.go` | ~150 | `/api/dashboard` métricas gerais. | ✅ |
| `dashboard_analytics.go` | 248 | Analytics agregados (mensagens/dia, top contatos, response time). | ✅ |
| `event.go` + `eventrsvp.go` | ~400 | Eventos, RSVP. | ✅ |
| `audio_library.go` | 215 | Biblioteca de áudios. | ✅ |

### 2.9 Contatos e CRM

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `contacts.go` | 337 | CRUD de contatos. | ✅ |
| `contact.go` | ~150 | Model de contato. | ✅ |
| `contact_extras.go` | 409 | Custom fields, notes, tags, leads. | ✅ |
| `contact_lists.go` | ~120 | Listas de contatos. | ✅ |
| `messagestore.go` | ~150 | Cache de mensagens. | ✅ |
| `chats.go` | ~120 | Lista de chats. | ✅ |
| `autoreply.go` | ~150 | Auto-resposta. | ✅ |
| `catalog.go` | ~150 | Catálogo de produtos. | ✅ |
| `business.go` | ~100 | WhatsApp Business. | ✅ |
| `groupadmin.go` | ~120 | Admin de grupos. | ✅ |
| `groupevents.go` | ~120 | Eventos em grupo. | ✅ |
| `groups.go` | 372 | CRUD de grupos. | ✅ |

### 2.10 External API / pagamento

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `external_api.go` | ~200 | API externa `/api/external/*` (webhook inbound, agent call). | ✅ |
| `payment.go` | ~150 | Pagamentos / assinatura. | ✅ |
| `recording.go` | 239 | Endpoint de áudio gravado. | ✅ |

### 2.11 Console chat / debug

| Arquivo | LOC | Responsabilidade | Multi-tenant? |
|---------|-----|------------------|---------------|
| `console_chat.go` | 211 | Console de chat pra debug. | ✅ |
| `console_chat_page.go` | ~150 | HTML do console. | ✅ |

### 2.12 _test.go (24 arquivos de teste)

`db_test.go`, `event_test.go`, `sessionmanager_test.go`, etc. Roda com `go test ./...`.

---

## 3. Schema do banco principal (`hermescall_main`)

```sql
-- Core
users            (id UUID PK, email UNIQUE, password hash, plan, active, ...)
sessions         (id PK, name, jid, user_id UUID FK, webhook, chatwoot, recording, proxy, created_at)
settings         (key, user_id UUID, value JSONB, updated_at)  -- PK (key, user_id)
login_sessions   (token_hash PK, user_id, expires_at, ...)
api_keys         (id PK, user_id FK, name, key_hash, prefix, active, last_used, ...)

-- Messaging
messages         (id, session_id, chat_jid, ts, body, ...)
conversations    (user_id, session_id, chat_jid, role, content, ts)
contacts         (id PK, user_id FK, jid, name, ...)
contact_lists    (id PK, user_id FK, name, ...)
contact_tag_assignments, contact_custom_fields, contact_notes, contact_leads

-- Campaigns / massa
campaigns        (id PK, user_id FK, session_id, kind, name, total, audio_ms, config, ...)
campaign_results (campaign_id FK, contact_jid, status, attempts, last_error, ...)

-- Billing / IA
ai_cost          (user_id, lane, model, in_tok, out_tok, cost_brl, ts)  -- PK inclui user_id

-- Recordings
call_recordings  (id, user_id, session_id, call_id, remote_jid, direction, duration_sec, file_path, transcription, ai_summary)
audio_library    (id, user_id, name, file_path, ...)

-- CRM
events, event_rsvp
polls, poll_votes
catalog
```

---

## 4. Fluxo de autenticação (importante!)

```
request
  ↓
withUserAuth (authmw.go)
  ↓
  1. Path é /api/auth/login ou /register? → passa direto
  2. Path é /api/chatwoot/webhook? → passa direto
  3. Não-API (static)? → passa direto
  4. Authorization: Bearer <jwt>?
     → parseJWT(jwtSecret) → sub = user_id
     → users.getByID(ctx, sub)
  5. Senão X-API-Key / ?apiKey=
     → se começa com "ey", tenta parseJWT
     → se começa com "hk_", apiKeys.GetUserByKeyHash
     → senão users.getByAPIKey (tabela api_keys, hash sha256)
  6. user == nil → 401
  7. user.TrialExpired() && plan == "trial" && 1h passou → 403
  8. ctx com user → handler
```

`userFromCtx(r)` é o que cada handler usa para obter o user atual.

**Garantias multi-tenant:**
- `sessions` table: PK `id`, coluna `user_id UUID`. Queries: `WHERE user_id = $1`.
- `settings` table: PK `(key, user_id)`. Sem user_id = órfão (invisível).
- `ai_cost`: PK inclui `user_id`. `Record(userID, ...)`, `Summary(userID)`, `Reset(userID)`.
- `users` table: SEM `user_id` (é a tabela mestra).
- `messages`, `contacts`, `campaigns`: FK pra `user_id` direta.

---

## 5. Pontos críticos (onde foi feita a refatoração multi-tenant)

1. **`authmw.go`** — removido bypass `WACALLS_API_KEY` que devolvia admin global.
2. **`sessionstore.go`** — `setJID/setWebhook/setChatwoot/setRecording/setProxy/delete` agora exigem `user_id`. `OR user_id IS NULL` foi substituído por `COALESCE(user_id, $3::uuid)`.
3. **`settings.go`** — PK migrada de `(key)` pra `(key, user_id)`. Linhas legadas vinculadas ao admin via `UPDATE settings SET user_id = $1 WHERE user_id IS NULL`.
4. **`ai_cost.go`** — `Record`/`Summary`/`Reset` filtram por `userID`.
5. **`conversation.go`** — removido `OR user_id IS NULL` de `GetHistoryByUser`/`ClearHistoryByUser`.
6. **`dashboard_analytics.go`** — agregado filtra por `user_id = $1` direto.
7. **`httpapi.go`** — `sessionByID` checa `sess.userID != u.ID` → 404 se não bate.
8. **`external_api.go`** — `/api/agent/call/hangup/status` filtram por `userFromCtx`.

---

## 6. Como rodar / debugar

```bash
# Build local
cd /d/callagente
docker build -t inovare/hermes-call-v3:latest .

# Deploy pra VPS
python _build_and_deploy.py
# (o script usa paramiko pra SFTP + SSH)

# Conectar no Postgres
ssh root@209.145.60.53
CN=$(docker ps -q --filter name=hermes_call_v3_pg_v3 | head -1)
docker exec $CN psql -U hermescall -d hermescall_main

# Ver logs do app
CN=$(docker ps -q --filter name=hermes_call_v3_hermes-call-v3 | head -1)
docker logs --tail 100 $CN
```

---

## 7. Sistema de Agentes (Jul 2026)

### 7.1 Hierarquia

- **Agente Gerenciador** (`manager agent`): o cérebro principal, usado pela dona para
  comandar o sistema via texto. Opera em 3 canais com memória compartilhada (mesmo
  `consoleChatJID` = `console:<userID>:<thread>`):
  - **Telegram** — funciona (via `telegram.go`)
  - **WhatsApp self-chat** — BUG: `autoreply.go` ignora `IsFromMe`, nunca respondeu
  - **Chat web** — IMPLEMENTADO: `GET /api/console/threads`, `GET /api/console/messages`,
    `POST /api/console/send`, `POST /api/console/clear` (`console_chat.go`)

- **Agentes Especializados** (`attendant`): atendentes por tag/produto/campanha. Cada
  um tem `system_prompt` próprio. Criados via aba "Agentes Especializados" no painel.

- **Agente de Ligação** (`call_ai`): usado durante chamadas VoIP (rótulo/greeting,
  decisões de rota, summary pós-ligação).

### 7.2 Memória compartilhada

O `ConversationStore` em Postgres persiste o histórico. A chave é `chat_jid`:

| Canal | JID pattern |
|-------|-------------|
| Telegram | `telegram:<userID>:<thread>` |
| WhatsApp | `wa:<userID>:<thread>` |
| Console/Web | `console:<userID>:<thread>` |

Para o agente gerenciador, todas as threads convergem no mesmo `consoleChatJID`
quando o canal é Telegram/WhatsApp e o thread é "geral". Assim a dona troca de
canal sem perder o histórico.

### 7.3 API endpoints de chat console

```
GET  /api/console/threads          → lista salas (agente base + perfis)
GET  /api/console/messages?thread= → histórico (100 msgs)
POST /api/console/send  {thread, text} → resposta do agente + memória
POST /api/console/clear {thread}     → limpa histórico
POST /api/console/audio?thread=&voice=1 → STT → agente → TTS (opcional)
```

### 7.4 Fluxo de uma mensagem (console/web)

```
handleConsoleSend
  → consoleReply(userID, thread, text)
     → getUserAgent(userID, "manager")         // agente base
     → conversations.GetHistoryByUser           // últimos 20 msgs
     → conversations.AddMessage (user role)    // persiste
     → agent.ProcessMessageWithHistory          // LLM
     → conversations.AddMessage (assistant)    // persiste resposta
  → {reply, at}
```

### 7.5 Multi-agente por thread

Se `thread != "geral"` e existe `AgentProfile` correspondente, o agente é clonado
com o `system_prompt` do perfil. Isso permite ter agentes especializados por
produto/campanha acessíveis via thread separada.

### 7.6 Voz (pipeline completo)

```
STT (Whisper) → Agente LLM → TTS (Edge-TTS / ElevenLabs / OpenAI)
```

- STT: `internal/voice/stt.go`
- TTS: `internal/voice/tts.go`
- Voice service agregado: `voiceservice.go`
- Endpoint console audio: `handleConsoleAudio` (`console_chat.go`)
- Durante ligação: `bridge.go` + `call_intel.go`

## 8. Variáveis de ambiente importantes

```
WACALLS_PG_URL          postgres://hermescall:<removido — ver cofre/VPS>@pg_v3:5432/postgres
WACALLS_PG_NAMESPACE    hermescall  (gera hermescall_main + hermescall_<id>)
HERMES_JWT_SECRET       <removido — ver cofre/VPS>
HERMES_ADMIN_EMAIL      admin@hermescall.com  (seeded on first boot)
HERMES_ADMIN_PASSWORD   <removido — ver cofre/VPS>
HERMES_TELEGRAM_TOKEN   <removido — ver cofre/VPS>  (GLOBAL, não per-user)
HERMES_AI_API_KEY       <removido — ver cofre/VPS>
HERMES_AI_BASE_URL      https://claudeopus.inovareinteligenciaartificial.com
HERMES_AI_MODEL         kr/claude-haiku-4.5
HERMES_AI_PROVIDER      anthropic
WACALLS_MAX_CALLS       8 (limite concorrência por sessão)
```

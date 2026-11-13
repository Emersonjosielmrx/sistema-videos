# Sistema de Agentes — Hermes Call

Documentação do sistema de agentes de IA do Hermes Call. three agentes em
contextos diferentes: o **Agente Gerenciador** (comando do sistema), os
**Agentes Especializados** (atendentes por produto/tag) e o **Agente de
Ligação** (durante chamadas VoIP).

---

## 1. Agente Gerenciador

O "cérebro" central. A dona conversa com ele para controlar todo o sistema:
disparar campanhas, buscar contatos, consultar métricas, criar listas, modificar
configurações, etc.

### 1.1 Canais de acesso

| Canal | Status | Endpoint / Handler |
|-------|--------|-------------------|
| Telegram | Funcionando | `telegram.go` (bot commands + chat) |
| WhatsApp self-chat | Implementado (BUG `IsFromMe`) | `autoreply.go` → `aiOwnerReply` |
| Chat web (painel) | IMPLEMENTADO (Jul 2026) | `console_chat.go` + `ManagerChat.tsx` |

Todos os canais usam a **mesma memória** (mesmo `consoleChatJID`), então a dona
pode trocar de Telegram para WhatsApp para chat web sem perder o histórico.

### 1.2 Configuração

O Agente Gerenciador é configurado na aba **"3. Agente Gerenciador"** do painel
(Configurações). Ele usa a config de IA padrão (`settings.ai`) como base.

```typescript
// settings.ts — campos relevantes
interface AllSettings {
  ai: AISettings;       // provider, model, api_key, system_message, ...
  manager?: AgentConfig; // override por usuário (provider, model, system_msg)
  agent_chat: AgentChatSettings; // enabled, mode (private/group), owner_message_enabled, ...
}
```

O prompt do sistema (system message) é o que define o comportamento do agente.
Ele recebe ferramentas de leitura/escrita no WhatsApp, campanhas, contatos, etc.

### 1.3 Ferramentas disponíveis

As ferramentas ficam em `aiagent_actions.go`. Principais:

| Ferramenta | O que faz |
|------------|-----------|
| `read_chat` | Lê últimas N mensagens com um contato |
| `send_message` | Envia mensagem de texto (com confirmação) |
| `send_audio` | Envia áudio (MP3/OGG) |
| `make_call` | Inicia ligação VoIP |
| `end_call` | Encerra ligação ativa |
| `list_campaigns` | Lista campanhas existentes |
| `start_campaign` | Dispara uma campanha |
| `search_contacts` | Busca contatos por nome/número |
| `list_contacts` | Lista contatos (com limite) |
| `create_contact` | Cria novo contato |
| `update_contact` | Atualiza dados/tags de contato |
| `get_session_status` | Status da sessão WhatsApp |
| `broadcast_message` | Dispara mensagem em massa |
| `get_dashboard` | Métricas gerais (chamadas, mensagens, etc.) |
| `get_campaign_status` | Status de uma campanha |

Todas passam por confirmação antes de executar ações irreversíveis (envio de
mensagem, ligação). A confirmação é feita via contexto no `ctxWithConfirmKey`.

### 1.4 Memória e histórico

O histórico de conversa é persistido em Postgres (`conversations` table).

```
JID = "console:<userID>:<thread>"  // thread = "geral" ou id do perfil
```

- `GET /api/console/messages?thread=geral` — recupera últimos 100 mensagens
- `POST /api/console/send {thread, text}` — envia e persiste (user + assistant)
- `POST /api/console/clear {thread}` — limpa histórico

### 1.5 Configurando o WhatsApp self-chat

O diagnóstico do `autoreply.go` explica o bug: `IsFromMe` sempre ignora a mensagem.
A correção (`aiOwnerReply`) está implementada mas depende de `cfg.OwnerMessageEnabled`.

```typescript
// AgentChatSettings — campo adicionado
interface AgentChatSettings {
  // ... campos existentes ...
  owner_message_enabled: boolean; // habilita resposta no self-chat
}
```

Para ativar:
1. Vá em Configurações → Agente Gerenciador
2. Habilite "Responder no meu WhatsApp" (owner_message_enabled)
3. Abra o WhatsApp no número da sessão e envie uma mensagem para si mesmo
   (ou no grupo criado pelo sistema)
4. A resposta virá com tag `[Hermes]`

---

## 2. Agentes Especializados (Perfis de Agente)

Criados na aba **"4. Agentes Especializados"** do painel. Cada perfil tem seu
próprio `system_prompt` e pode ser acionado por:

- **Campanha de ligação** — ao discar, o agente daquele perfil atende
- **Auto-resposta** — respondendo a mensagens de clientes por tag/etapa
- **Thread separada** — acessível no chat web (`ManagerChat`) ao selecionar a sala

### 2.1 Modelo de dados

```go
// agentprofiles.go
type AgentProfile struct {
    ID             string // UUID, gerado automaticamente
    Name           string // nome amigável (único por usuário)
    Product        string // descrição do produto
    SystemPrompt   string // roteiro/prompt do agente
    InitialContext string // contexto injetado no início (ex.: abertura do áudio)
    Voice          string // voz TTS (ex.: "pt-BR-FranciscaNeural")
    TTSDefault     string // texto inicial (vira áudio se não vier outro)
    WakeWord       string // palavra de ativação (modo wake)
    MeetMode       string // "wake" (sóm com wake word) ou "auto" (sempre responde)
}
```

### 2.2 Criar via API

```bash
# via endpoint de settings (ManagerAgentSettings no frontend)
PUT /api/settings
{
  "key": "agent_profile_<name>",
  "value": { "name": "...", "system_prompt": "...", "product": "...", ... }
}
```

### 2.3 Perfis seedados

Ao boot, o sistema cria o perfil "Vendas Hermes Call" com um roteiro de vendas
por telefone pré-definido. Isso pode ser customizado ou desabilitado.

---

## 3. Agente de Ligação (Call AI)

Usado durante chamadas VoIP entrantes e efetuadas. Configurado na aba
**"2. IA da Ligação"**.

| Campo | Descrição |
|-------|-----------|
| `enabled` | Liga/desliga o agente de voz |
| `provider` | Provedor de IA (anthropic, openai, gemini) |
| `model` | Modelo específico |
| `api_key` | Chave da API |
| `api_base_url` | URL base customizada (opcional) |
| `system_message` | Prompt do agente (instruções de atendimento) |

O agente de ligação usa o pipeline de voz:
```
cliente fala → STT (Whisper) → agente LLM → TTS (Edge-TTS) → cliente ouve
```

Ver `bridge.go` + `call_intel.go` + `voiceservice.go`.

---

## 4. Configuração de IA (providers)

### 4.1 Providers suportados

| Provider | Valor do `provider` | Notes |
|----------|---------------------|-------|
| Anthropic | `anthropic` | Usa `api_base_url` como proxy (se houver) |
| OpenAI | `openai` | GPT-4, GPT-4o, etc. |
| Groq | `openai` + `api_base_url: https://api.groq.com` | Inferência rápida |
| Gemini | `gemini` | Google AI Studio |
| Proxy custom | qualquer + `api_base_url` | Para routers como OneProxy |

### 4.2 Busca de modelos

O painel tem um botão "Buscar modelos" que faz `GET /api/models` no backend,
que por sua vez consulta a API do provider. Isso evita que a dona digite
nomes de modelo manualmente.

```bash
GET /api/models?provider=anthropic
GET /api/models?provider=openai
# etc.
```

---

## 5. Billing e custos

Cada uso de IA é registrado em `ai_cost` table (por `user_id`, `lane`, `model`,
`in_tok`, `out_tok`, `cost_brl`).

```bash
# Endpoints de custo
GET  /api/ai-cost              → resumo geral
GET  /api/ai-cost/summary     → por modelo / período
POST /api/ai-cost/reset        → limpa histórico (usuário)
```

Lanes:
- `main` — chat/telegram/console (Agente Gerenciador)
- `call` — IA durante ligações (Call AI)
- `attendant` — auto-resposta de clientes

---

## 6. Integração OpenClaw

Se o usuário já tem um **OpenClaw** próprio, a config fica na aba do Agente
Gerenciador:

```typescript
interface OpenClawConfig {
  enabled: boolean;
  url: string;       // URL do servidor OpenClaw
  api_key: string;   // Bearer token
}
```

Quando habilitada, o `aiAutoReply` prefere o OpenClaw ao agente local:

```go
// autoreply.go:206
if cfg.OpenClaw.Enabled && cfg.OpenClaw.URL != "" {
    reply, err = callOpenClaw(ctx, cfg.OpenClaw, text, senderName)
    // fallback para agente local se falhar
}
```

O mesmo vale para o Agente Gerenciador — se configurado, pode ser usado
como cérebro externo para todo o sistema.

---

## 7. Escalabilidade e multi-tenant

Cada agente é instanciado por `userID`. Não há agente global compartilhado —
todas as queries de DB passam `WHERE user_id = $1`.

O `getUserAgent` busca a config do usuário logado:

```go
// aiagent.go
func (s *server) getUserAgent(ctx context.Context, userID, role string) *AIAgent
// role = "manager" | "attendant" | "call"
```

Se o usuário não tem config específica, usa os defaults de ambiente
(`HERMES_AI_API_KEY`, `HERMES_AI_MODEL`, etc.).

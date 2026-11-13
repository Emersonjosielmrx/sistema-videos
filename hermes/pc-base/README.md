# Inovare Hermes Call

Sistema de ligações WhatsApp com agente IA integrado. Baseado no protocolo WhatsApp nativo (whatsmeow + codec MLow), permite fazer e receber chamadas de voz diretamente do navegador ou via API programática.

## Funcionalidades

- **Ligações WhatsApp** — Faz e recebe chamadas de voz nativas via WebRTC
- **Multi-sessão** — Múltiplos números WhatsApp simultâneos
- **Telegram Bot** — Comandar ligações pelo Telegram (@InovareHermesCallBot)
- **Agente IA nativo** — LLM integrado (Claude/OpenAI/Groq) que pode operar chamadas autonomamente
- **API de agente externo** — Endpoint REST para qualquer Hermes/OpenClaw externo se conectar
- **Webhook** — Notificações em tempo real (SSE + webhook HTTP)
- **Painel web** — Interface React para gerenciar sessões e chamadas

## Como roda

- **Produção:** binário Go via systemd na VPS, publicado só com `bash ops/publicar.sh`
  (ver [`CLAUDE.md`](CLAUDE.md) §6 e [`docs/VERSOES.md`](docs/VERSOES.md)).
- **VPS de teste / experimentar:** imagem Docker `fabricadeautomacoesia/hermes-call`
  (`bash ops/publicar-teste.sh`). Exemplo mínimo:

```bash
docker run -d --name hermes-call --restart=always \
  -e WACALLS_PG_URL="postgres://user:pass@host:5432/postgres?sslmode=disable" \
  -e HERMES_JWT_SECRET="<32+ caracteres aleatórios>" \
  -e HERMES_ADMIN_EMAIL="voce@exemplo.com" \
  -e HERMES_ADMIN_PASSWORD="<senha forte>" \
  -p 8080:8080 \
  fabricadeautomacoesia/hermes-call:<versão>
```

> Versão/canal em execução: `curl -s http://127.0.0.1:8080/api/version`.

## Variáveis de Ambiente

**Todas** as configurações (cerca de 100), com o que cada uma faz e o valor padrão, estão no
catálogo [`.env.example`](.env.example), separadas por grupo. O teste
`cmd/server/env_catalog_test.go` falha se alguém criar uma variável sem documentar lá.

Obrigatórias (sem elas o servidor não sobe): `WACALLS_PG_URL`, `HERMES_JWT_SECRET` (32+
caracteres) e, num banco novo, `HERMES_ADMIN_EMAIL` + `HERMES_ADMIN_PASSWORD`. Chaves de IA,
voz e Telegram podem ser configuradas por conta no painel.

## API

### Rotas principais
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/sessions` | Listar sessões |
| POST | `/api/sessions` | Criar sessão |
| POST | `/api/sessions/{sid}/calls` | Iniciar ligação |
| DELETE | `/api/sessions/{sid}/calls/{id}` | Encerrar ligação |
| GET | `/api/events` | Stream SSE de eventos |

### API do Agente Externo (Hermes/OpenClaw)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/agent/connect` | Info de conexão + snippet |
| GET | `/api/agent/status` | Status do sistema |
| POST | `/api/agent/call` | Fazer ligação `{"phone":"5511..."}` |
| POST | `/api/agent/hangup` | Encerrar ligação `{"call_id":"..."}` |

### Autenticação
Header `X-API-Key` ou query param `?apiKey=` em todas as rotas `/api/*`.

## Conectar Agente Externo (Hermes/OpenClaw)

Acesse `GET /api/agent/connect` para obter o snippet de configuração. Cole no seu agente:

```json
{
  "base_url": "https://calls.seudominio.com",
  "api_key": "<SEGREDO_REMOVIDO>",
  "type": "inovare-hermes-call"
}
```

O agente externo pode então:
1. `GET /api/agent/status` — verificar conexão
2. `POST /api/agent/call` — fazer ligação
3. `POST /api/agent/hangup` — desligar
4. `GET /api/events` — receber eventos em tempo real

## Telegram Bot

Comandos disponíveis:
- `/ligar 5511999999999` — Faz ligação
- `/desligar <callId>` — Encerra ligação
- `/sessoes` — Lista sessões conectadas
- `/status` — Status do sistema
- Mensagem livre → processada pelo agente IA

## Licença

AGPL-3.0 (fork do AstraCalls/WaCalls)

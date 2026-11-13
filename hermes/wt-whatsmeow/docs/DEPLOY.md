# DEPLOY — Hermes Call v3 (refactor)

Como fazer build e deploy na VPS. Um comando resolve tudo.

## TL;DR — deploy de um comando

```bash
cd deploy
node deploy.js            # backend (compila no VPS) + frontend + restart + valida
node deploy.js --back-only   # só o binário Go
node deploy.js --front-only  # só o frontend
```

No fim ele imprime `/api/version`, o HTTP da raiz (200 = UI ok) e quantas
sessões restauraram. Se o serviço não subir, o script sai com erro.

---

## Infra atual (VPS 62.171.128.241 — "opus-sem-limites")

| Peça | Onde | Observação |
|---|---|---|
| **App** | systemd `hermes-call.service` em `/opt/hermes-call/` | binário + `dist/` (frontend). Reinicia sozinho, sobrevive reboot |
| **Porta interna** | `127.0.0.1:8080` | não exposta direto; Traefik faz o proxy |
| **Proxy/TLS** | Traefik (container `traefik`, `--network host`) | Let's Encrypt automático, config em `/opt/traefik-config/` |
| **Banco** | PostgreSQL local (systemd), banco `wacalls_main` | user `hermes_call_v3test`. 1 banco por sessão: `wacalls_<sessionid>` |
| **Domínio** | `hermescall.opus-sem-limites.com.br` → 62.171.128.241 | wildcard `*.opus-sem-limites.com.br` |
| **Fontes Go** | `/opt/hipercool-refactor/` | o build roda aqui, dentro do container `golang:1.26-bookworm` |

**Por que compilar no VPS:** o PC de dev não tem Go. O VPS tem a imagem
`golang:1.26-bookworm`, então o `deploy.js` monta o binário lá dentro
(isolado e reproduzível). O frontend (vite) é buildado no PC porque precisa
de `node_modules`.

**Login inicial:** `admin@hermescall.com` / `changeme`.

---

## Setup inicial da VPS (feito 1x — só repetir em VPS nova)

### 1. PostgreSQL
```bash
apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql
service postgresql start
su - postgres -c "psql -c \"CREATE USER hermes_call_v3test WITH PASSWORD 'hermes_call_v3test' CREATEDB;\""
su - postgres -c "psql -c \"CREATE DATABASE wacalls_main OWNER hermes_call_v3test;\""
```
> O user PRECISA de `CREATEDB` — o app cria um banco por sessão WhatsApp
> (`wacalls_<id>`). Sem isso o boot falha com "permission denied to create database".

### 2. systemd unit (`/etc/systemd/system/hermes-call.service`)
```ini
[Unit]
Description=Hermes Call v3 (WhatsApp VoIP)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
WorkingDirectory=/opt/hermes-call
Environment=WACALLS_PG_URL=postgres://hermes_call_v3test:<removido — ver cofre/VPS>@localhost:5432/wacalls_main?sslmode=disable
Environment=PORT=8080
ExecStart=/opt/hermes-call/hermes-call -static /opt/hermes-call/dist
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload && systemctl enable --now hermes-call
```
> O `deploy.js` reescreve essa unit a cada deploy, então não precisa mexer à mão.

### 3. Traefik (proxy + TLS)
Container standalone com `--network host` e file provider:
- `/opt/traefik-config/traefik.yml` — entrypoints web/websecure + resolver `le` (Let's Encrypt HTTP challenge) + file provider apontando pra `/etc/traefik/dynamic`
- `/opt/traefik-config/dynamic/hermes.yml` — router `Host(hermescall.opus-sem-limites.com.br)` → `http://127.0.0.1:8080/`, tls certResolver `le`

```bash
docker run -d --name traefik --restart=always --network host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /opt/traefik-config/traefik.yml:/etc/traefik/traefik.yml:ro \
  -v /opt/traefik-config/dynamic:/etc/traefik/dynamic:ro \
  -v /opt/traefik-config/letsencrypt:/letsencrypt \
  traefik:v2.10
```
> O DNS do subdomínio precisa apontar pra VPS ANTES — senão o Let's Encrypt
> falha com NXDOMAIN. Com o wildcard `*` já resolve.

---

## Migrar dados de outra VPS (banco novo vazio)

O Hermes guarda dados em **múltiplos bancos**: `wacalls_main` (users,
sessions, mensagens) + um banco `wacalls_<sessionid>` por número WhatsApp
(contém as credenciais `whatsmeow_*`). Pra copiar tudo:

```bash
# Na VPS antiga (só leitura — não afeta produção):
docker exec <pg> pg_dump -U <user> -d wacalls_main --no-owner --no-privileges -f /tmp/main.sql
docker exec <pg> pg_dump -U <user> -d wacalls_<sid> --no-owner --no-privileges -f /tmp/sess.sql

# Na VPS nova: parar o serviço ANTES de inserir as sessions
systemctl stop hermes-call
# restaurar wacalls_main + cada wacalls_<sid>, ajustar owner p/ hermes_call_v3test
# reinserir as linhas da tabela sessions (senão o Restore apaga sessão sem device)
systemctl start hermes-call   # deve logar "sessions restored count=N"
```
> **Cuidado:** o `Restore()` no boot APAGA qualquer sessão cuja `jid` não tenha
> um device DB correspondente. Por isso restaure os bancos `wacalls_<sid>`
> ANTES de reinserir as linhas em `sessions`.

---

## Isolamento multi-tenant (importante)

Cada usuário logado vê SÓ os próprios dados. Camadas:
- `authmw.go` — middleware injeta `*auth.User` no contexto (`userFromCtx`). Rotas públicas: `/api/auth/login`, `/api/auth/register`, `/api/version`.
- `cmd/server/sessionstore.go` — `list(userID)` filtra `WHERE user_id=$1`; sessões órfãs (`user_id NULL`) são invisíveis até alguém reivindicar.
- `httpapi.go:sessionByID` — retorna 404 (não 403) se a sessão não é do usuário.
- `sessionmanager.go:Restore` — emite `session-list` **por usuário** no boot. **Não use `emitSessionList("")`** — isso vaza a lista global via SSE (conta nova via os números da conta principal).

Teste rápido de isolamento:
```bash
# registrar conta nova → GET /api/sessions deve retornar {"sessions":[]}
# admin → deve continuar vendo os números dele
```

---

## Padrão de nomenclatura (tags e imagens)

> Regras completas em [`deploy/DEPLOY.md` → "Padrão de nomenclatura"](../deploy/DEPLOY.md).
> Resumo rápido abaixo.

- **Git tags**: sempre `vX.Y.Z` (semver). Nunca nomes descritivos como `VERSAO-BOA`.
- **Docker VPS**: só 3 tags — `:beta`, `:stable`, `:stable-prev`. Nada mais.
- **Docker Hub**: `:vX.Y.Z` (fixa), `:stable`/`:latest` (move), `:next`/`:beta` (move).
- **VERSION**: arquivo na raiz, `X.Y.Z` sem `v`. Bumpar antes do deploy.
- **Limpeza**: `node deploy/cleanup-docker.js` remove imagens antigas da VPS.

## Troubleshooting

| Sintoma | Causa / Fix |
|---|---|
| Raiz dá 404 | frontend não foi servido — confira `-static /opt/hermes-call/dist` e que o `dist/` existe |
| `permission denied to create database` | user do PG sem `CREATEDB` → `ALTER USER hermes_call_v3test CREATEDB;` |
| `sessions restored count=0` mas tem sessões no banco | falta o banco `wacalls_<sid>` (device store) → restaurar o dump por-sessão |
| Let's Encrypt NXDOMAIN | DNS do subdomínio não aponta pra VPS ainda |
| build "missing go.sum entry" | rode `go mod tidy` (o `deploy.js` já faz isso) |
| `/api/version` dá 401 | rota não está na whitelist do `authmw.go` |
| deploy diz OK mas rodou código velho | binário antigo não foi removido antes do build (o `deploy.js` corrige removendo antes) |

## Comandos úteis (VPS)
```bash
systemctl status hermes-call
journalctl -u hermes-call -f            # logs ao vivo
journalctl -u hermes-call -n 50         # últimas 50 linhas
curl -s http://127.0.0.1:8080/api/version
```

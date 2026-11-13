# Contribuindo — Hermes Call

Guia rápido de como mexer no projeto sem quebrar produção.

## Stack

- **Backend:** Go 1.26 (pacote `main` em `cmd/server/`, libs em `internal/`).
- **Frontend:** React + TypeScript + Vite + Tailwind (`client/`).
- **Banco:** PostgreSQL (um `wacalls_main` + um `wacalls_<sessionid>` por número).
- **Áudio da ligação:** codec MLow (`libopus_mlow.so`, compilado no Dockerfile, cgo).

Arquitetura detalhada: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Ambiente

O PC de dev normalmente **não tem Go nem Docker** — o build de imagem roda na VPS
(ou no CI). Dá pra trabalhar assim:

- **Frontend:** `cd client && npm ci && npm run build` (ou `npm run dev`).
- **Backend:** se tiver Go, `make build` / `make test`. Senão, confie no CI.

Atalhos em [`Makefile`](Makefile) (`make help`).

## Fluxo de trabalho

1. Crie uma branch a partir de `main`.
2. Faça a mudança pequena e focada. Siga o estilo do arquivo vizinho.
3. Valide localmente o que der: `make ci` (vet + test + build do front).
4. Abra PR. O **CI** (`.github/workflows/ci.yml`) roda build/test Go + build do front.
5. Ao mergear e cortar release, siga [`VERSIONING.md`](VERSIONING.md).

## Regras de versão (resumo)

- Cada melhoria sobe **+1 ponto** (o MINOR) e o projeto fica **sempre abaixo de v1.0**
  (série `v0.x`): `v0.1.0` → `v0.2.0` → … Detalhes em [`VERSIONING.md`](VERSIONING.md).
- Toda mudança relevante entra no [`CHANGELOG.md`](CHANGELOG.md).
- **Migrações de banco devem ser aditivas** (`ADD COLUMN IF NOT EXISTS`,
  `CREATE TABLE IF NOT EXISTS`) — é o que permite o rollback voltar pra estável.

## Deploy

Nunca faça deploy direto sem preservar a estável. Use o fluxo beta → validação →
promote/rollback descrito em [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

## Segurança

- **Nunca** commite segredos. Credenciais ficam em `deploy/.env.deploy` (gitignored).
- Não cole tokens em PR/issue/chat. Rotacione PATs periodicamente.
- Serviços expostos sem auth devem ser sinalizados no PR.

# 🚀 DEPLOY — Reconstrução no ar (2026-07-26)

> A reconstrução (branch reconstrucao-v0.2.1) foi deployada em PRODUÇÃO por cima
> da golden, com autorização explícita da dona nesta sessão. Rollback = 1 comando.

## ⏪ COMO REVERTER (se algo estiver errado)

```bash
cd D:\hermes-call
node deploy/rollback.js
```

Isso volta pro `hermes-call:stable`, que está fixado na **golden exata** (`21c83411cfd1`,
digest `sha256:e9076d201c63fce053d5ff9bead7275ed590f58815bc6516e765bcc177042c13`).
Redundância: `hermes-call:golden-restore-point` aponta pra mesma golden.
Também no Docker Hub: `fabricadeautomacoesia/hermes-call:v0.2.1` (e backup-pre-asaas).

## O que está no ar agora

- **Container:** `hermes-call:beta` — Up (healthy), sem erro/panic no boot.
- **Version:** `{"build":"20260726-1558","channel":"beta","version":"v0.2.0"}`
- **Bundle front NOVO:** `index-BFHuVbG3.js` (reconstrução; golden era index-BYgTiieN.js).
- **Paridade:** ~68% literal / ~90% funcional vs golden (billing, cadastro, vozes, CRM/funil,
  listas, campanha, telefonia, RAG/copilot restaurados). Divergências deliberadas
  documentadas em `_GOLDEN_v0.2.1/_DIVERGENCIAS_DELIBERADAS.md`.

## Validação técnica pós-deploy (2026-07-26 ~16:00)

- Container healthy, HTTP server :8080 ok, root UI 200.
- Endpoints novos respondem (401 = protegido/existe): /api/billing, /billing/subscribe,
  /tts/preview, /analytics/crm/kpis, /projects, /sessions. Nenhum 404/500.
- Asaas: 3 envs presentes (API_KEY, API_URL, WEBHOOK_TOKEN).
- Sessões WhatsApp: 5 restauradas (conexões preservadas).

## ⚠ PENDENTE — validação no browser (clicando)

Type-check + build + healthcheck passaram, mas isso NÃO garante comportamento de UI.
FALTA a dona (ou eu, com browser) validar clicando: billing (gerar cobrança), cadastro
(fluxo plano/cupom/CPF), vozes (preview), CRM (funil/kanban), reconexão WhatsApp.
Se algo estiver quebrado → `node deploy/rollback.js`.

## Se validar OK → promover

```bash
node deploy/promote-stable.js   # marca este beta como nova :stable
```
ATENÇÃO: só promover DEPOIS de validar no browser. Enquanto não promover, a :stable
segue apontando pra golden (rollback seguro).

## Imagens de restauração na VPS

| Tag | Image ID | O que é |
|---|---|---|
| `hermes-call:stable` | 21c83411cfd1 | **golden** (alvo do rollback) |
| `hermes-call:golden-restore-point` | 21c83411cfd1 | golden (redundância) |
| `fabricadeautomacoesia/hermes-call:v0.2.1` | 21c83411cfd1 | golden (Docker Hub) |
| `hermes-call:beta` | 3bec15f18ac6 | **reconstrução (no ar agora)** |
| `hermes-call:stable-prev-20260726` | da254c00b298 | :stable antiga (preservada) |

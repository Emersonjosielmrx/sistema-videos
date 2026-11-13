# 🔒 BACKUP — Operação "adicionar envs Asaas" (2026-07-26)

> Registro de segurança criado ANTES de recriar o container `hermes-call`.
> Regra da Haylla: guardar a imagem atual com todos os detalhes (nome, digest,
> onde está) pra podermos VOLTAR a qualquer momento se a mudança der errado.

## Por que essa operação existe

O container `hermes-call` em produção estava rodando a imagem golden CORRETA,
mas **sem as 3 variáveis de ambiente do Asaas**. Resultado: `/api/billing`
retornava **HTTP 401** (billing quebrado). A imagem está certa; faltavam só as envs.

Solução: recriar o container (mesma imagem golden) adicionando as envs Asaas.
Nenhuma alteração na imagem — só nas envs passadas no `docker run`.

## Estado ANTES da operação (capturado por _inspect_readonly.js)

- **VPS:** `62.171.128.241` (opus-sem-limites) — ESTA é a VPS do Hermes Call.
  ⚠️ Os rótulos do `.env.deploy` chamam `.241` de "BUILD" e `.53` de "PROD",
  mas isso é LEGADO ENGANOSO. O Hermes Call roda em `.241`. **NÃO mexer na `.53`.**
- **Container:** `hermes-call` — estava `Up 12 hours (healthy)`
- **Imagem:** `fabricadeautomacoesia/hermes-call:v0.2.1`
- **Digest (imutável):** `sha256:e9076d201c63fce053d5ff9bead7275ed590f58815bc6516e765bcc177042c13`
- **Image ID local:** `sha256:21c83411cfd1e3e297c3229d288e0d230a0d9f00b145af273a806f89feccc276`
- **Version API:** `{"build":"20260723-2224","channel":"beta","version":"v0.2.1"}`
- **Envs que TINHA:** só `HERMES_TELEGRAM_TOKEN`, `PORT`, `WACALLS_PG_URL`
- **Envs que FALTAVAM:** `HERMES_ASAAS_API_KEY`, `HERMES_ASAAS_API_URL`, `HERMES_ASAAS_WEBHOOK_TOKEN`
- **billing:** HTTP 401 (quebrado por falta das envs)

## Backups criados ANTES de recriar (3 camadas)

### 1. Snapshot local do container em execução
- **Tag:** `hermes-call:snapshot-pre-asaas-20260726-0857`
- **Image ID:** `sha256:56173657fa2eed72e71210e91caac5edeea9c04df9966c27f5032397f1d9d27d`
- **Onde:** local na VPS `.241` (`docker images`)
- **O que é:** `docker commit` do container exatamente como estava rodando agora.

### 2. Tag de backup no Docker Hub (nuvem, imutável)
- **Tag:** `fabricadeautomacoesia/hermes-call:backup-pre-asaas-20260726-0857`
- **Digest:** `sha256:e9076d201c63fce053d5ff9bead7275ed590f58815bc6516e765bcc177042c13` (= golden)
- **Onde:** Docker Hub, conta `fabricadeautomacoesia` (push confirmado 2026-07-26).

### 3. Golden já preservada de antes (não tocada)
- `fabricadeautomacoesia/hermes-call:v0.2.1` / `:stable` / `:latest` / `:GOLDEN-ultima-funcional-20260723`
  (todas mesmo digest `e9076d20...`)
- Cópia local: `D:\hermes-call\_GOLDEN_v0.2.1\` (binário + dist + MANIFEST)

## COMO VOLTAR (rollback) se a recriação der errado

Na VPS `62.171.128.241` (user root, pass no `deploy/.env.deploy`):

```bash
# Opção A — voltar ao container idêntico ao de antes (SEM envs Asaas, billing 401):
docker rm -f hermes-call
docker run -d --name hermes-call --restart=always --network host \
  -e 'WACALLS_PG_URL=postgres://hermes_call_v3test:<removido — ver cofre/VPS>@localhost:5432/wacalls_main?sslmode=disable' \
  -e 'PORT=8080' \
  -e 'HERMES_TELEGRAM_TOKEN=<ver deploy/.env.deploy>' \
  fabricadeautomacoesia/hermes-call:v0.2.1

# Opção B — restaurar o snapshot exato do container de antes:
docker rm -f hermes-call
docker run -d --name hermes-call --restart=always --network host \
  hermes-call:snapshot-pre-asaas-20260726-0857

# Opção C — puxar a imagem do Docker Hub de novo (se sumir da VPS):
docker pull fabricadeautomacoesia/hermes-call:v0.2.1
# ou o backup nomeado:
docker pull fabricadeautomacoesia/hermes-call:backup-pre-asaas-20260726-0857
```

## Operação executada (recriação com envs Asaas) — CONCLUÍDA

- **Data/hora:** 2026-07-26 ~12:02 UTC
- **Script:** `deploy/_recreate_with_asaas.js`
- **Imagem usada:** `fabricadeautomacoesia/hermes-call:v0.2.1` (a MESMA golden — só muda env)
- **Envs adicionadas:** `HERMES_ASAAS_API_KEY`, `HERMES_ASAAS_API_URL`, `HERMES_ASAAS_WEBHOOK_TOKEN`
  (valores lidos do `deploy/.env.deploy`)
- **Método:** as envs que já rodavam foram lidas do próprio container e preservadas
  (`WACALLS_PG_URL`, `PORT`, `HERMES_TELEGRAM_TOKEN`); só as 3 do Asaas foram somadas.
- **Novo container ID:** `56a2be9cd5c4...`
- **Status pós-operação:** `Up (healthy)`, version `20260723-2224 / v0.2.1` (inalterada)

### Resultado da validação

- Envs Asaas confirmadas dentro do container: as 3 presentes.
  - `HERMES_ASAAS_API_URL = https://api.asaas.com/v3`
  - `HERMES_ASAAS_API_KEY` = 167 chars (presente)
- Logs de boot: **sem erros de Asaas/billing** (subiu limpo).
- `/api/billing` → HTTP **401** — MAS isso é o **middleware de auth**, não erro de config:
  `/api/health` também dá 401 e `/api/version` (público) dá 200. Endpoints de billing
  exigem login, comportamento esperado. A config do Asaas está aplicada.
- ⚠️ Validação de ponta-a-ponta do billing (criar cobrança/plano) precisa de request
  AUTENTICADO no browser — não dá pra confirmar via curl sem sessão. Config OK; falta
  o teste funcional logado (dona + browser).

### Confirmação anti-perda (regra cumprida)

Antes de derrubar o container, foram criadas 3 camadas de backup (ver acima):
snapshot local `hermes-call:snapshot-pre-asaas-20260726-0857`, tag Docker Hub
`backup-pre-asaas-20260726-0857`, e a golden intacta. Rollback documentado na seção
"COMO VOLTAR". Nenhuma imagem foi sobrescrita; o digest golden `e9076d20...` segue íntegro.

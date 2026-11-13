# Backlog de DX — Hermes Call

> ## ⚠️ DOCUMENTO DE JULHO — conferido em 06/10/2026: **não é lista de pendência**
>
> Foi escrito quando a produção rodava em Docker (`deploy/*.js`). Hoje a publicação é por `ops/` e a maior
> parte disto já existe de outro jeito:
> - "status da produção sem abrir SSH" → `bash ops/status.sh`;
> - "`.env.example` de runtime" → existe na raiz, com teste que falha se faltar variável (`TestEnvCatalog`);
> - "smoke test pós-deploy" → o `ops/publicar.sh` confere versão, linhas e erros e volta sozinho se falhar;
> - "pega-ratão" → `docs/REGRESSOES_LIGACAO.md` e `docs/PENDENCIAS_BUGS.md`.
>
> O resto (make doctor, seed local, Dependabot, template de PR, badges) é conforto de programador: **não fazer
> sem a dona pedir**. Dependabot em especial abriria pedidos automáticos que ninguém revisa.

Melhorias de **developer/deploy experience** que deixam o trabalho neste projeto mais
fácil e seguro. Não são features de produto. Rastreável: marque `[x]` ao concluir e
registre no `CHANGELOG.md` se afetar o fluxo de release.

Legenda de esforço: **P** pequeno (~1 sessão) · **M** médio · **G** grande.
Prioridade: 🔴 alta · 🟡 média · 🟢 baixa.

---

## 🔴 Alta prioridade

- [ ] **`make doctor` — auto-diagnóstico de ambiente** · P
  - Script (`deploy/doctor.js` + alvo no Makefile) que ao abrir a pasta checa:
    Node/Go/Docker presentes?, `deploy/.env.deploy` existe?, `git remote` = repo certo?,
    versão local (`VERSION`) e o que está no ar (`curl /api/version` na VPS).
  - **Pronto quando:** `make doctor` imprime um relatório verde/vermelho e sai 0/1.

- [ ] **`deploy/status.js` — status de produção sem abrir SSH** · P
  - SSH na `62.171.128.241` e imprime: container `hermes-call` up?, `/api/version`,
    últimas 10 linhas de log, imagens `hermes-call:*` presentes (stable/beta/versões).
  - **Pronto quando:** `node deploy/status.js` mostra tudo isso e nunca escreve segredo.

- [ ] **`.env.example` de runtime (raiz do app)** · P
  - Documentar TODAS as env vars do app (`WACALLS_*`, `HERMES_*`, `PORT`) num único
    lugar; hoje estão espalhadas entre README/docs/scripts. Sem valores reais.
  - **Pronto quando:** existe `.env.example` versionado e o README aponta pra ele.

- [ ] **Smoke test pós-deploy** · M
  - Script que após subir valida: login (`/api/auth/login`), `/api/version` (versão/canal
    esperados) e 1 endpoint autenticado. Falha o deploy se algo quebrar.
  - **Pronto quando:** `deploy-beta.js` chama o smoke test no fim e aborta em falha.

## 🟡 Média prioridade

- [ ] **Seed de ambiente local (docker compose + dados)** · M
  - Subir Postgres + app + usuário de teste localmente sem depender da VPS, pra testar
    o fluxo real (o `docker-compose.yml` já sobe Postgres+app; falta o seed do usuário).
  - **Pronto quando:** `docker compose up` + um comando de seed dá login pronto.

- [ ] **CI: cache + lint** · P
  - Adicionar `golangci-lint` ao `ci.yml` (config `.golangci.yml` já existe) e garantir
    cache de módulos Go/npm (já parcialmente feito).
  - **Pronto quando:** o job de lint roda no PR e o tempo de CI cai com cache.

- [ ] **Template de PR + CODEOWNERS** · P
  - `.github/pull_request_template.md` (checklist: CHANGELOG atualizado?, migração
    aditiva?, testado?) e `CODEOWNERS` pra revisão.
  - **Pronto quando:** abrir PR mostra o checklist automaticamente.

- [ ] **Dependabot / Renovate** · P
  - Atualização automática de deps Go/npm via PR; o CI valida antes do merge.
  - **Pronto quando:** `.github/dependabot.yml` ativo e gerando PRs.

## 🟢 Baixa prioridade

- [ ] **`docs/SINTOMA_CAUSA_FIX.md`** · P (contínuo)
  - Registrar "pega-ratão" recorrentes (sintoma → causa → fix), no espírito do que o
    projeto hipercool usa. Cresce com o tempo.
  - **Pronto quando:** existe e tem ao menos os casos já conhecidos (EOF do gateway,
    `sessions restored count=0`, permission denied CREATEDB — ver `docs/DEPLOY.md`).

- [ ] **Limpeza das tags git de checkpoint** · P
  - Remover as ~13 tags que não seguem `vX.Y.Z` (comandos documentados em `VERSIONING.md`).
  - **Pronto quando:** `git tag` só lista `vX.Y.Z` (+ eventuais releases).

- [ ] **Badge de CI + versão no README** · P
  - Badge do workflow de CI e da última versão/tag no topo do README.
  - **Pronto quando:** README mostra status do CI e versão atual.

---

## Como usar este arquivo

- Ao pegar um item, mova o foco pra ele e marque `[x]` quando o "Pronto quando" bater.
- Item que muda o fluxo de release/deploy → também registrar no `CHANGELOG.md`.
- Novas ideias de DX entram aqui (não no `CLAUDE.md`, que fica só com o essencial +
  um ponteiro pra este backlog).

# Versionamento — Hermes Call

Como versionamos, o que entra em cada bump, e como cortar/reverter uma release.
O histórico de mudanças fica em [`CHANGELOG.md`](CHANGELOG.md). O procedimento
operacional (com credenciais) fica em [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

## Regra permanente: sempre abaixo de v1.0, +1 ponto por melhoria

**REGRA FIXA (não mudar):** a cada melhoria/entrega, incrementa-se **apenas um ponto**
na versão, e o projeto **permanece sempre abaixo de v1.0** (série `v0.x`). Ou seja:
sobe-se o **MINOR** a cada melhoria (`v0.1.0` → `v0.2.0` → `v0.3.0` → … → `v0.9.0` →
`v0.10.0` → `v0.11.0` …). O primeiro número **fica em `0` para sempre** — nunca chega
em `v1.0.0`. Não há salto de MAJOR.

- **1 melhoria = +1 no MINOR** (o "ponto"): `v0.N.0` → `v0.(N+1).0`.
- **PATCH** (`v0.N.1`, `v0.N.2`…) fica opcional só para hotfix pontual da mesma leva,
  sem melhoria nova. Se preferir simplicidade, pode usar só o MINOR.
- Passar de `v0.9.0` vai para `v0.10.0` (dez, não "um zero") e segue: `v0.11.0`,
  `v0.12.0`… sem limite. O `0.` inicial é permanente.

Fonte única da versão: arquivo **`VERSION`** na raiz (ex.: `0.1.0`). O binário
expõe em `GET /api/version` → `{ version, channel, build }`.

### Como isso muda a semântica de mudança

Como não existe MAJOR neste projeto, mudanças que normalmente seriam "quebra
incompatível" continuam subindo só +1 no MINOR — mas **precisam** ser sinalizadas
no CHANGELOG com **⚠️ Breaking changes** e o passo de migração. A regra do rollback
(migração aditiva) continua valendo e fica ainda mais importante.

### Canais

- **beta** — leva nova em validação em produção. A imagem estável anterior fica
  guardada como `hermes-call:stable` e pode ser restaurada num comando.
- **stable** — versão promovida após validação (`deploy/promote-stable.js`).

`appVersion`/`appChannel` vivem em `cmd/server/main.go` e podem ser sobrescritos no
build via `-ldflags "-X main.appVersion=... -X main.appChannel=..."`.

### Stack de tags no Docker Hub (`fabricadeautomacoesia/hermes-call`)

Toda release publica **uma tag fixa imutável** + **tags móveis** conforme o canal.
Assim quem for atualizar escolhe entre "estável", "próxima (beta)" ou uma versão fixa.

| Tag | Move? | Aponta para | Quem usa |
|---|---|---|---|
| `:vX.Y.Z` | ❌ imutável | aquela versão exata (estável) | pin / rollback determinístico |
| `:vX.Y.Z-beta.N` | ❌ imutável | aquele pré-lançamento exato | pin de um beta específico |
| `:stable` | ✅ | última estável | produção (alias de latest) |
| `:latest` | ✅ | **última ESTÁVEL** (nunca beta) | produção (default do `docker pull`) |
| `:next` | ✅ | próxima em validação (beta) | quem quer testar antes |
| `:beta` | ✅ | idem `:next` (alias) | quem quer testar antes |

Regras:
- **`:latest` só aponta pra estável.** Um release beta **nunca** mexe em `:latest`.
- A tag fixa (`:vX.Y.Z[-beta.N]`) nunca é sobrescrita — é o ponto de pin/rollback.
- `release.js` monta essa stack automaticamente pelo canal (`--channel` ou sufixo
  `-beta`/`-rc`/`-alpha` na versão).

Como puxar:
```bash
docker pull fabricadeautomacoesia/hermes-call:latest    # produção estável
docker pull fabricadeautomacoesia/hermes-call:next      # próxima (beta), pra testar
docker pull fabricadeautomacoesia/hermes-call:v0.2.0    # uma versão exata (pin)
```

## Fluxo de release

1. **Feche o escopo** e atualize o `CHANGELOG.md`: adicione uma seção no topo com a
   nova versão (Novidades / Correções / Migrações de banco). Data no formato AAAA-MM-DD.
2. **Bump da versão**: edite `VERSION` (ou passe `--version` no release.js) e, se o
   canal mudou, ajuste `appChannel` em `cmd/server/main.go`.
3. **Corte a release** (tag Git + imagem Docker Hub). Escolha o canal:
   ```bash
   # pré-lançamento pra validar (canal beta → tags :next + :beta, NÃO mexe em :latest)
   node deploy/release.js --version 0.2.0-beta.1

   # release estável (canal stable → tags :stable + :latest)
   node deploy/release.js --version 0.2.0
   ```
   Cria a tag Git correspondente, faz push pro GitHub e builda/pusha a stack de tags
   do canal no Docker Hub (ver "Stack de tags" acima). O canal é inferido do sufixo
   `-beta`/`-rc`/`-alpha`, ou force com `--channel beta|stable`.
4. **Deploy beta na VPS** (preserva a estável):
   ```bash
   node deploy/deploy-beta.js
   ```
5. **Valide** em https://hermescall.opus-sem-limites.com.br
   (`/api/version` deve mostrar `channel=beta` e a versão nova).
6. **Promova ou reverta**:
   ```bash
   node deploy/promote-stable.js   # aprovado → vira nova estável
   node deploy/rollback.js         # deu ruim → volta pra estável anterior
   ```

## O que documentar a cada versão (CHANGELOG)

Para cada release, registre sob a seção da versão:

- **✨ Novidades** — features e endpoints novos (o "o quê" e o "por quê" curto).
- **🐛 Correções** — bugs corrigidos (sintoma → causa, quando ajudar).
- **⚙️ Migrações de banco** — toda alteração de schema, marcando se é aditiva
  (segura p/ rollback) ou destrutiva (exige MAJOR + plano de migração).
- **⚠️ Breaking changes** — se houver, no topo, com o passo de migração.

Regra de ouro do rollback: **migrações devem ser aditivas** sempre que possível
(`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`), pra que a versão estável
continue lendo o banco após um `rollback.js`. Mudança destrutiva vira MAJOR e precisa
de plano de migração/reversão explícito no CHANGELOG.

## Regra prática

- Cada melhoria/entrega → **+1 no MINOR** (`v0.1.0` → `v0.2.0` → `v0.3.0` …).
  Este é o caso padrão: quase toda release é uma melhoria e sobe um ponto.
- Hotfix pontual da mesma leva, sem melhoria nova → PATCH opcional (`v0.2.0` → `v0.2.1`).
- Quebra de compatibilidade / schema destrutivo → **continua +1 no MINOR** (não vira
  v1.0.0), mas marque **⚠️ Breaking changes** no CHANGELOG com o passo de migração.
- O primeiro número é **`0` para sempre** — o projeto nunca sai da série `v0.x`.

## Roadmap de versões (planejado)

O que fazer e em que ordem está no plano em vigor: [`docs/PLANO_MES_OUTUBRO_2026.md`](docs/PLANO_MES_OUTUBRO_2026.md).
Ao iniciar uma nova versão, puxe de lá os itens prontos e registre-os no CHANGELOG quando entrarem.
(O roadmap de julho foi para `docs/archive/ROADMAP_MELHORIAS_2026-07.md`.)

## Limpeza das tags antigas de checkpoint (opcional, uma vez)

O repositório tem tags antigas de checkpoint (ex.: `crm-ui-20260716`,
`fix-gate-loop-20260716`, `v3.2-stable-call-intel`) que **não** seguem a convenção
`vX.Y.Z`. Elas são ruído no histórico. Se quiser limpar (revise a lista antes —
destrutivo no remoto):

```bash
# lista as tags que NÃO são vX.Y.Z (as candidatas a remover)
git tag | grep -vE '^v[0-9]+\.[0-9]+\.[0-9]+'

# remove uma tag local + no remoto (confira o nome antes!)
git tag -d <tag>
git push origin :refs/tags/<tag>
```

> Não removi automaticamente: apagar tag no remoto é destrutivo. Mantenha só as
> `vX.Y.Z` daqui pra frente.
